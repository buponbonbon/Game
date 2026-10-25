"""Deterministic, fixed-step lane-defense simulation.

Rendering is deliberately outside this module: browser pixels never apply damage.
All times are integer simulation ticks, including attack windups and projectiles.
"""

from __future__ import annotations

import copy
import heapq
import math
import random
from collections import deque

from .content import ENEMIES, HEROES, RELICS, STAGES
from .rules import hero_data

HZ = 60
STEP = 1 / HZ


def ticks(seconds):
    return max(1, round(float(seconds) * HZ))


def damage_amount(raw, armor=0, resistance=0, true=False):
    """One shared damage formula; zero damage cannot generate a phantom hit."""
    if raw <= 0:
        return 0
    if true:
        return max(1, math.floor(raw))
    resistance = max(-0.5, min(0.8, resistance))
    return max(1, math.floor(max(1, raw - max(0, armor)) * (1 - resistance) + 1e-9))


class Battle:
    def __init__(self, stage_id, seed=1, upgrades=None, realm=0):
        if not isinstance(stage_id, str) or stage_id not in STAGES:
            raise ValueError("Unknown stage")
        self.stage = copy.deepcopy(STAGES[stage_id])
        self.stage_id = stage_id
        self.region = self.stage.get("region", "wharf")
        self.seed = int(seed)
        self.rng = random.Random(self.seed)
        self.realm = max(0, min(3, int(realm)))
        self.upgrades = upgrades if isinstance(upgrades, dict) else {}
        self.status = "playing"
        self.tick = 0
        self.command_revision = 0
        self.paused = False
        self.speed = 1.0
        self.auto_ultimate = False
        self._next_auto_ultimate = 0
        self._music_level = 0
        self._music_fall_at = 0
        self._accumulator = 0.0
        self.qi = 175 if self.realm >= 1 else 150
        self.gate = int(self.stage.get("gate", 3))
        self.kills = 0
        self.defenses = [
            {"lane": lane, "status": "ready", "x": 0.5, "hit": set()}
            for lane in range(5)
        ]
        self.heroes = {}
        self.enemies = {}
        self.projectiles = {}
        self.orbs = {}
        self.effects = []
        self.zones = []
        self.telegraphs = []
        self.events = deque(maxlen=80)
        self.cards = {key: 0 for key in HEROES}
        self.pending = []
        self._sequence = 0
        self._entity = 0
        self._wave_index = 0
        self._spawn_queue = []
        self._rel_used = set()
        self._wind_lock = 0
        self._haste_until = 0
        self._tide_forced = 0
        self._reveal_until = 0
        self._calm_until = 0
        self.ritual_until = 0
        self.nodes = [
            {**node, "corrupted": False, "channel": 0, "purify": 0}
            for node in self.stage.get("nodes", [])
        ]
        self._rewards = {}
        self._rewarded = False
        self.metrics = {
            "damage": {},
            "healing": 0,
            "altars_destroyed": 0,
            "plates_broken": 0,
            "qi": {"starting": self.qi},
            "spent": 0,
            "deaths": 0,
            "breaches": 0,
            "invalid": 0,
        }
        self._waves = sorted(
            self.stage.get("waves", []), key=lambda w: w.get("at", w.get("time", 0))
        )
        for wave_index, wave in enumerate(self._waves):
            at = wave.get("at", wave.get("time", 0))
            for spawn in wave.get("spawns", wave.get("enemies", [])):
                for n in range(max(1, min(20, int(spawn.get("count", 1))))):
                    self._spawn_queue.append(
                        (
                            ticks(
                                at
                                + spawn.get("delay", 0)
                                + n * spawn.get("gap", spawn.get("interval", 0.6))
                            ),
                            wave_index,
                            spawn["type"],
                            int(spawn.get("lane", 2)),
                            (
                                "captain"
                                if spawn.get("captain") and n == 0
                                else (
                                    "elite"
                                    if n < spawn.get("elite_count", 0)
                                    else "swarm" if spawn.get("swarm") else "normal"
                                )
                            ),
                        )
                    )
        self._spawn_queue.sort()
        self._spawn_index = 0
        for altar in self.stage.get("altars", []):
            self._spawn("altar", altar["lane"], altar["x"])
        self._event("start", self.stage.get("name", stage_id))

    @property
    def time(self):
        return self.tick / HZ

    def _id(self):
        self._entity += 1
        return self._entity

    def _event(self, kind, text, x=None, lane=None, actor=None):
        self._sequence += 1
        event = {
            "seq": self._sequence,
            "kind": kind,
            "text": text,
            "time": round(self.time, 3),
        }
        if x is not None:
            event.update(x=x, lane=lane)
        if actor is not None:
            event["actor"] = actor
        self.events.append(event)

    def _effect(self, kind, x, lane, text="", duration=0.65):
        self.effects.append(
            {
                "id": self._id(),
                "kind": kind,
                "x": x,
                "lane": lane,
                "text": str(text),
                "until": self.tick + ticks(duration),
                "born": self.tick,
            }
        )
        self.effects = self.effects[-100:]

    def _schedule(self, delay, kind, **data):
        self._sequence += 1
        heapq.heappush(
            self.pending, (self.tick + ticks(delay), self._sequence, kind, data)
        )

    def _add_qi(self, amount, source):
        actual = max(0, min(self._qi_cap() - self.qi, max(0, amount)))
        self.qi += actual
        self.metrics["qi"][source] = self.metrics["qi"].get(source, 0) + actual
        return actual

    def _hero_data(self, hero_id):
        return hero_data(hero_id, self.upgrades.get(hero_id))

    def _auto_ultimate_tick(self):
        if not self.auto_ultimate or self.tick < self._next_auto_ultimate:
            return
        for h in sorted(
            self.heroes.values(),
            key=lambda h: (
                {"herbalist": 0, "formation": 2, "gatherer": 3}.get(h["type"], 1),
                h["id"],
            ),
        ):
            u = h["data"]["ultimate"]
            if (
                h["resonance"] < 100
                or h["mana"] < u["mana_cost"]
                or self.qi < u["qi_cost"]
                or h["ultimate_ready"] > self.tick
                or h["disabled_until"] > self.tick
            ):
                continue
            kind = h["type"]
            if kind == "gatherer":
                benefits = self.qi <= self._qi_cap() - 48
            elif kind == "herbalist":
                benefits = any(
                    a["hp"] < a["max_hp"] * 0.85
                    or a.get("curse", 0)
                    or a.get("curse_until", 0) > self.tick
                    for a in self.heroes.values()
                )
            elif kind == "formation":
                allies = [
                    a
                    for a in self.heroes.values()
                    if a["id"] != h["id"] and self._near(a, h, 2)
                ]
                benefits = (
                    bool(allies)
                    and any(
                        e["type"] != "altar" and e["x"] < 10
                        for e in self.enemies.values()
                    )
                    and not any(
                        a["type"] == "formation"
                        and a["array_until"] > self.tick
                        and self._near(a, h, 2)
                        for a in self.heroes.values()
                    )
                )
            else:
                scope = u["geometry"]
                shape = scope["shape"]
                radius = scope["radius"]
                eligible = [
                    e
                    for e in self.enemies.values()
                    if (
                        (shape == "lane" and e["lane"] == h["lane"])
                        or shape == "field"
                        or (shape == "circle" and self._near(e, h, radius))
                        or (
                            shape == "line"
                            and e["lane"] == h["lane"]
                            and -0.3 <= e["x"] - h["x"] <= radius
                        )
                    )
                ]
                # Save expensive arts for a pack, a durable target or immediate danger.
                power = u.get("power", 0) * (
                    10
                    if kind == "sword"
                    else 2 if kind == "fire" else 3 if kind == "lightning" else 1
                )
                benefits = bool(eligible) and (
                    len(eligible) >= 2
                    or any(
                        e["data"].get("boss") or e["x"] <= h["x"] + 1.5
                        for e in eligible
                    )
                    or sum(e["hp"] + e["shield"] for e in eligible) >= power * 0.8
                )
            if benefits and self.command(dict(action="ultimate", unit=h["id"]))["ok"]:
                self._next_auto_ultimate = self.tick + ticks(0.22)
                return

    def _music_tick(self):
        phases = {"setup": 0, "pressure": 1, "onslaught": 2}
        base = phases[self._encounter()["id"]]
        living = [e for e in self.enemies.values() if e["type"] != "altar"]
        self.metrics["peak_enemies"] = max(
            self.metrics.get("peak_enemies", 0), len(living)
        )
        elites = sum(e.get("rank") in ("elite", "captain") for e in living)
        peak = (
            len(living) >= 10
            or elites >= 4
            or any(e["data"].get("boss") and e["x"] < 9 for e in living)
        )
        desired = max(base, 2 if peak else 1 if len(living) >= 5 or elites >= 2 else 0)
        if desired >= self._music_level:
            self._music_level = desired
            self._music_fall_at = self.tick + ticks(6)
        elif self.tick >= self._music_fall_at:
            self._music_level = desired

    def _qi_cap(self):
        return 320 + max(
            (h["data"].get("treasury_cap", 0) for h in self.heroes.values()), default=0
        )

    def _mana(self, hero, amount):
        hero["mana"] = min(hero["data"]["mana_max"], max(0, hero["mana"] + amount))

    def _unlock(self, hero_id):
        data = HEROES[hero_id]
        explicit = data.get("unlock_realm", data.get("unlock_level"))
        if explicit is not None:
            return int(explicit)
        return (
            1
            if hero_id in ("frost", "herbalist")
            else 2 if hero_id in ("lightning", "formation") else 0
        )

    def _response(self, ok, message):
        if not ok:
            self.metrics["invalid"] += 1
        return {"ok": ok, "message": message}

    def command(self, command):
        self.command_revision += 1
        if not isinstance(command, dict):
            return self._response(False, "Invalid command.")
        action = command.get("action")
        if self.status != "playing":
            return self._response(False, "This battle has ended.")
        if action == "pause":
            self.paused = bool(command.get("paused", not self.paused))
            return self._response(
                True, "Battle paused." if self.paused else "Battle resumed."
            )
        if action == "speed":
            try:
                speed = float(command.get("value", 1))
            except (ValueError, TypeError):
                return self._response(False, "Invalid battle speed.")
            if speed not in (1, 1.5, 2):
                return self._response(False, "Choose 1x, 1.5x or 2x.")
            self.speed = speed
            return self._response(True, f"Battle speed {speed:g}x.")
        if action == "auto_ultimate":
            enabled = command.get("enabled", not self.auto_ultimate)
            if not isinstance(enabled, bool):
                return self._response(False, "Auto ultimate must be on or off.")
            self.auto_ultimate = enabled
            self._event(
                "auto_ultimate",
                "Auto ultimates " + ("enabled." if enabled else "disabled."),
            )
            return self._response(
                True, "Auto ultimates " + ("enabled." if enabled else "disabled.")
            )
        if action == "ritual":
            if self.paused:
                return self._response(
                    False, "Resume the battle before invoking a ritual."
                )
            if self.tick < self.ritual_until:
                return self._response(False, "The region ritual is cooling down.")
            if self.qi < 35:
                return self._response(False, "Region ritual needs 35 Qi.")
            self.qi -= 35
            self.metrics["spent"] += 35
            self.ritual_until = self.tick + ticks(30)
            if self.region == "wharf":
                self._calm_until = self.tick + ticks(12)
            elif self.region == "terrace":
                for node in self.nodes:
                    node.update(corrupted=False, channel=0, purify=0)
                self._wind_lock = self.tick + ticks(10)
                for h in self.heroes.values():
                    if any(
                        math.hypot(h["lane"] - n["lane"], h["col"] - n["col"]) <= 1
                        for n in self.nodes
                    ):
                        self._mana(h, 15)
            else:
                self._reveal_until = self.tick + ticks(6)
                for h in self.heroes.values():
                    h["curse"] = 0
                    h["curse_until"] = 0
            self._event("ritual", self.stage["ritual"]["name"] + " invoked.")
            return self._response(True, "Region ritual invoked.")
        if action == "auto_skill":
            try:
                unit = self.heroes.get(int(command.get("unit", -1)))
            except (ValueError, TypeError, OverflowError):
                unit = None
            if not unit:
                return self._response(False, "Select a living cultivator.")
            unit["auto_skill"] = bool(command.get("enabled", not unit["auto_skill"]))
            return self._response(
                True,
                (
                    "Automatic skill enabled."
                    if unit["auto_skill"]
                    else "Mana reserved for ultimate."
                ),
            )
        if self.paused and action not in ("pause", "speed"):
            return self._response(
                False, "Resume the battle before issuing combat actions."
            )
        if action == "place":
            hero_id = command.get("hero")
            lane, col = command.get("lane"), command.get("col")
            if not isinstance(hero_id, str) or hero_id not in HEROES:
                return self._response(False, "Choose a hero card.")
            if (
                not isinstance(lane, int)
                or not isinstance(col, int)
                or isinstance(lane, bool)
                or isinstance(col, bool)
            ):
                return self._response(False, "Choose a valid battlefield tile.")
            if not 0 <= lane < 5 or not 1 <= col <= 9:
                return self._response(
                    False,
                    "Column 0 holds a one-use guardian seal. Deploy in columns 1-9.",
                )
            if self.realm < self._unlock(hero_id):
                return self._response(False, "This hero is not unlocked yet.")
            if any(h["lane"] == lane and h["col"] == col for h in self.heroes.values()):
                return self._response(False, "Tile occupied.")
            if any(
                t["lane"] == lane and t["col"] == col and t.get("blocked")
                for t in self._hazard()["tiles"]
            ):
                return self._response(
                    False, "This tile is sealed by the current hazard."
                )
            if (
                hero_id == "gatherer"
                and sum(h["type"] == "gatherer" for h in self.heroes.values()) >= 3
            ):
                return self._response(
                    False, "Only three Qi Gatherers may channel at once."
                )
            data = self._hero_data(hero_id)
            if self.cards[hero_id] > self.tick:
                return self._response(False, "That card is cooling down.")
            if self.qi < data["cost"]:
                return self._response(
                    False, f"Need {math.ceil(data['cost'] - self.qi)} more Qi."
                )
            self.qi -= data["cost"]
            self.metrics["spent"] += data["cost"]
            unit_id = self._id()
            unit = {
                "id": unit_id,
                "type": hero_id,
                "lane": lane,
                "col": col,
                "x": col + 0.5,
                "hp": data["hp"],
                "max_hp": data["hp"],
                "shield": 0,
                "shield_until": 0,
                "resonance": 0,
                "mana": data["mana_initial"],
                "auto_skill": True,
                "ultimate_ready": 0,
                "action_started": self.tick,
                "data": data,
                "born": self.tick,
                "next_attack": self.tick + ticks(0.5),
                "next_skill": self.tick
                + ticks(
                    data.get(
                        "circuit_cooldown", data.get("skill", {}).get("cooldown", 9)
                    )
                ),
                "next_passive": self.tick
                + ticks(
                    data.get("orb_interval", 8)
                    if hero_id == "gatherer"
                    else data.get("heal_interval", 6)
                ),
                "hits": 0,
                "hurt_hits": 0,
                "orb_count": 0,
                "herb": 0,
                "action": "deploy",
                "action_until": self.tick + ticks(0.5),
                "disabled_until": 0,
                "array_until": 0,
                "curse": 0,
            }
            unit["public_stats"] = copy.deepcopy(
                {k: v for k, v in data.items() if k not in ("talents", "branches")}
            )
            self.heroes[unit_id] = unit
            self.cards[hero_id] = self.tick + ticks(data.get("cooldown", 8))
            self._effect("deploy", unit["x"], lane, duration=0.8)
            self._event(
                "place",
                f"{data.get('name', hero_id)} deployed.",
                unit["x"],
                lane,
                actor=hero_id,
            )
            return self._response(True, f"{data.get('name', hero_id)} deployed.")
        if action in ("ultimate", "sell"):
            try:
                unit = self.heroes.get(int(command.get("unit", -1)))
            except (ValueError, TypeError, OverflowError):
                unit = None
            if not unit:
                return self._response(False, "Select a living friendly unit.")
            if action == "sell":
                refund = math.floor(
                    unit["data"]["cost"] * 0.5 * unit["hp"] / unit["max_hp"]
                )
                self._add_qi(refund, "recall")
                del self.heroes[unit["id"]]
                self._effect("recall", unit["x"], unit["lane"], f"+{refund}")
                return self._response(True, f"Hero recalled. +{refund} Qi.")
            if unit["resonance"] < 100:
                return self._response(
                    False,
                    f"Ultimate needs {100 - math.floor(unit['resonance'])} more Resonance.",
                )
            ultimate = unit["data"]["ultimate"]
            if unit["ultimate_ready"] > self.tick:
                return self._response(False, "Ultimate art is cooling down.")
            if unit["mana"] < ultimate["mana_cost"]:
                return self._response(
                    False,
                    f"Ultimate needs {math.ceil(ultimate['mana_cost']-unit['mana'])} more mana.",
                )
            if self.qi < ultimate["qi_cost"]:
                return self._response(
                    False, f"Ultimate needs {ultimate['qi_cost']} shared Qi."
                )
            unit["resonance"] = 0
            self._mana(unit, -ultimate["mana_cost"])
            self.qi -= ultimate["qi_cost"]
            self.metrics["spent"] += ultimate["qi_cost"]
            unit["ultimate_ready"] = self.tick + ticks(ultimate["cooldown"])
            self._ultimate(unit)
            return self._response(True, "Ultimate art unleashed!")
        if action == "collect":
            try:
                orb = self.orbs.get(int(command.get("orb", -1)))
            except (ValueError, TypeError, OverflowError):
                orb = None
            if not orb:
                return self._response(False, "That Qi mote has already been collected.")
            self._collect(orb)
            return self._response(True, "Qi collected.")
        if action == "relic":
            relic = command.get("id", command.get("relic"))
            relic_ids = ["tide_pearl", "wind_compass", "soul_bell"]
            if relic is None:
                try:
                    relic = relic_ids[int(command.get("slot", 0))]
                except (ValueError, TypeError, IndexError):
                    relic = None
            if relic not in relic_ids or self.realm < relic_ids.index(relic) + 1:
                return self._response(False, "That relic has not been unlocked.")
            if relic in self._rel_used:
                return self._response(
                    False, "This relic was already used in this battle."
                )
            self._rel_used.add(relic)
            if relic == "tide_pearl":
                for hero in self.heroes.values():
                    self._shield(hero, 120, 5)
            elif relic == "wind_compass":
                self._haste_until = self.tick + ticks(8)
                for hero in self.heroes.values():
                    self._resonance(hero, 35)
            else:
                self._reveal_until = self.tick + ticks(6)
                for hero in self.heroes.values():
                    hero["curse"] = 0
                    hero["curse_until"] = 0
                for enemy in list(self.enemies.values()):
                    self._stun(enemy, 1.2)
                    if not enemy["data"].get("boss"):
                        enemy["channel_token"] += 1
            self._event(
                "relic", f"{RELICS.get(relic, {}).get('name', relic)} activated."
            )
            return self._response(True, "Relic activated.")
        return self._response(False, "Unknown action.")

    def advance(self, dt):
        if not isinstance(dt, (int, float)) or not math.isfinite(dt) or dt < 0:
            raise ValueError("dt must be a finite nonnegative number")
        if self.paused or self.status != "playing":
            return
        self._accumulator += dt * self.speed
        count = min(18000, int((self._accumulator + 1e-10) * HZ))
        self._accumulator -= count * STEP
        for _ in range(count):
            if self.status != "playing":
                self._accumulator = 0
                break
            self._step()

    def _step(self):
        self.tick += 1
        if self.tick % ticks(12) == 0:
            amount = 32 if self.realm >= 2 else 30
            self._add_qi(amount, "passive")
            self._event("qi", f"Ley-line pulse: +{amount} Qi")
        if self.tick % ticks(24) == 0:
            upkeep = min(self.qi, math.ceil(len(self.heroes) / 6))
            self.qi -= upkeep
            self.metrics["spent"] += upkeep
        self.qi = min(self.qi, self._qi_cap())
        self._mechanic_tick()
        while (
            self._spawn_index < len(self._spawn_queue)
            and self._spawn_queue[self._spawn_index][0] <= self.tick
        ):
            _, wave, enemy_type, lane, rank = self._spawn_queue[self._spawn_index]
            self._spawn_index += 1
            self._wave_index = max(self._wave_index, wave + 1)
            self._spawn(enemy_type, lane, rank=rank)
        while self.pending and self.pending[0][0] <= self.tick:
            _, _, kind, data = heapq.heappop(self.pending)
            self._resolve(kind, data)
        for orb in list(self.orbs.values()):
            if self.tick - orb["born"] >= ticks(1.2):
                self._collect(orb)
        self.effects = [
            effect for effect in self.effects if effect["until"] > self.tick
        ]
        self.telegraphs = [
            tell for tell in self.telegraphs if tell["until"] > self.tick
        ]
        self._update_zones()
        self._auto_ultimate_tick()
        for hero in list(self.heroes.values()):
            self._hero_tick(hero)
        for enemy in list(self.enemies.values()):
            if self.gate <= 0:
                break
            if enemy["id"] in self.enemies:
                self._enemy_tick(enemy)
        self._defense_tick()
        if self.gate > 0:
            self._projectile_tick()
        if self.tick % ticks(6) == 0 and self._hazard()["phase"] == "HIGH TIDE":
            for hero in list(self.heroes.values()):
                if hero["lane"] in self.stage.get("water_lanes", [0, 4]) and hero[
                    "col"
                ] in (3, 4):
                    self._hurt_hero(hero, 15, "Water")
        self._music_tick()
        if self.gate <= 0:
            self.status = "defeat"
            self._event(
                "defeat",
                "The immortal gate has fallen. Rebuild your formation and try again.",
            )
        elif (
            self._spawn_index >= len(self._spawn_queue)
            and not self.enemies
            and not any(item[2] == "spawn" for item in self.pending)
        ):
            self.status = "victory"
            if not self._rewarded:
                reward = copy.deepcopy(
                    self.stage.get("reward", self.stage.get("rewards", {}))
                )
                if not isinstance(reward, dict):
                    reward = {"stones": 80}
                reward.setdefault("stones", 70 + self.stage.get("index", 0) * 15)
                reward.setdefault("insight", 1)
                reward.update(
                    stage=self.stage_id,
                    kills=self.kills,
                    replay_stones=max(10, math.floor(reward["stones"] * 0.25)),
                )
                self._rewards = reward
                self._rewarded = True
                self._event("victory", "The gate endures. Victory!")

    def _spawn(self, enemy_type, lane, x=11.8, rank="normal"):
        if enemy_type not in ENEMIES and enemy_type != "altar":
            self._event("warning", f"Unknown enemy definition: {enemy_type}")
            return
        data = (
            copy.deepcopy(ENEMIES[enemy_type])
            if enemy_type in ENEMIES
            else {
                "id": "altar",
                "name": "Soul-Seal Altar",
                "hp": 420,
                "armor": 8,
                "damage": 0,
                "speed": 0,
                "range": 0,
                "boss": False,
                "resistances": {"lightning": -0.25, "spirit": -0.25},
            }
        )
        scale = self.stage.get("hp_multiplier", 1) * (
            1.5
            if rank == "captain"
            else 1.25 if rank == "elite" else 0.8 if rank == "swarm" else 1
        )
        data["hp"] = round(data["hp"] * scale)
        if rank == "swarm":
            data["damage"] = round(data.get("damage", 0) * 0.85)
        if rank in ("elite", "captain"):
            data["armor"] += 3 if rank == "captain" else 2
            data["damage"] = round(
                data.get("damage", 0) * (1.15 if rank == "captain" else 1.10)
            )
        enemy_id = self._id()
        enemy = {
            "id": enemy_id,
            "type": enemy_type,
            "rank": rank,
            "lane": max(0, min(4, int(lane))),
            "x": x,
            "hp": data["hp"],
            "max_hp": data["hp"],
            "shield": data.get("shield", data.get("plate", 0)),
            "shield_until": 0,
            "data": data,
            "born": self.tick,
            "next_attack": self.tick,
            "next_skill": self.tick
            + ticks(data.get("ability_interval", 6 if enemy_type == "lantern" else 8)),
            "next_boss": self.tick + ticks(9),
            "slow_until": 0,
            "slow_power": 0,
            "frozen_until": 0,
            "burn_until": 0,
            "burn_next": 0,
            "burn_damage": 0,
            "burn_owner": 0,
            "frost": 0,
            "conductive": 0,
            "conductive_until": 0,
            "armor_break_until": 0,
            "action": "walk",
            "action_until": 0,
            "phase": 1,
            "invulnerable_until": 0,
            "last_hit": self.tick,
            "regen_ticks": 0,
            "channel_token": 0,
            "cc_last": -10000,
            "cc_count": 0,
            "absorbed": 0,
            "absorb_until": 0,
            "resurrected": False,
            "damage_owners": {},
            "flight_until": 0,
            "next_edict": self.tick + ticks(15),
        }
        self.enemies[enemy_id] = enemy
        if data.get("boss"):
            self._event(
                "boss", data.get("name", enemy_type) + " approaches!", x, enemy["lane"]
            )
            self._effect("boss", x, enemy["lane"], "BOSS", 2)
        return enemy

    def _near(self, a, b, radius):
        return math.hypot(a["x"] - b["x"], a["lane"] - b["lane"]) <= radius

    def _targets(self, hero, radius=None, all_lanes=False):
        data = hero["data"]
        radius = data.get("range", 5) if radius is None else radius
        result = []
        for enemy in self.enemies.values():
            if all_lanes and not self._near(hero, enemy, radius):
                continue
            if not all_lanes and enemy["lane"] != hero["lane"]:
                continue
            if enemy["x"] < hero["x"] - 0.3 or enemy["x"] - hero["x"] > radius:
                continue
            if self._hidden(enemy) and hero["type"] not in ("fire", "lightning"):
                continue
            if (
                self.region == "tomb"
                and self._hazard()["phase"] == "GRAVE MIST"
                and enemy["lane"] in self.stage.get("mist_lanes", [1, 3])
                and enemy["x"] - hero["x"] > 2.8
                and hero["type"] not in ("fire", "lightning")
                and self._reveal_until <= self.tick
            ):
                continue
            result.append(enemy)
        if hero["type"] == "lightning":
            result.sort(key=lambda e: (e["type"] != "yaksha", e["x"], e["id"]))
        else:
            result.sort(key=lambda e: (e["x"], e["id"]))
        return result

    def _hidden(self, enemy):
        if self._reveal_until > self.tick:
            return False
        if enemy["type"] == "soul":
            return (self.tick - enemy["born"]) % ticks(5.5) > ticks(3.9)
        if enemy["type"] == "drowned" and self._hazard()["phase"] == "HIGH TIDE":
            return (self.tick - enemy["born"]) % ticks(7) > ticks(4.6)
        return False

    def _buffs(self, hero):
        attack_speed, damage, reduction = 1.0, 1.0, 0.0
        formations = [
            unit
            for unit in self.heroes.values()
            if unit["type"] == "formation"
            and self._near(hero, unit, unit["data"].get("aura_range", 1.5))
        ]
        if formations:
            attack_speed += max(
                unit["data"].get("attack_speed_buff", 0.08) for unit in formations
            )
            roles = {
                unit["data"].get("role")
                for unit in self.heroes.values()
                if self._near(unit, formations[0], 1.5)
            }
            if len(roles) >= 3 and formations[0]["data"].get("branch") != "A":
                reduction = 0.03
        for unit in self.heroes.values():
            if (
                unit["type"] == "formation"
                and unit["array_until"] > self.tick
                and self._near(hero, unit, 2)
            ):
                attack_speed += 0.18
                damage += 0.12
                reduction = max(reduction, 0.1)
                break
        if self.region == "terrace" and any(
            math.hypot(node["lane"] - hero["lane"], node["col"] - hero["col"]) <= 1
            for node in self.nodes
            if not node["corrupted"]
        ):
            attack_speed += 0.12
        if self._haste_until > self.tick:
            attack_speed += 0.2
        if hero.get("curse_until", 0) > self.tick:
            attack_speed *= 0.8
        if hero.get("spore_until", 0) > self.tick:
            attack_speed *= 0.85
        if (
            self.region == "wharf"
            and self._hazard()["phase"] in ("HIGH TIDE", "RISING")
            and hero["lane"] in self.stage.get("water_lanes", [])
            and hero["col"] in (3, 4)
        ):
            attack_speed *= 0.85
        if hero["mana"] >= hero["data"]["mana_max"] * 0.5:
            damage += hero["data"].get("high_mana_damage", 0)
        reduction += hero["data"].get("talent_reduction", 0)
        return attack_speed, damage, min(0.65, reduction)

    def _mana_regen(self, hero):
        regen = hero["data"]["mana_regen"]
        if self.region == "terrace" and any(
            not n["corrupted"]
            and math.hypot(n["lane"] - hero["lane"], n["col"] - hero["col"]) <= 1
            for n in self.nodes
        ):
            regen *= 1.2
        if (
            self.region == "tomb"
            and self._hazard()["phase"] == "GRAVE MIST"
            and hero["lane"] in self.stage.get("mist_lanes", [])
        ):
            regen *= 0.7
        return regen

    def _hero_tick(self, hero):
        self._mana(hero, self._mana_regen(hero) * STEP)
        if hero["shield_until"] and hero["shield_until"] <= self.tick:
            hero["shield"] = 0
        if hero["action"] in ("ultimate", "skill") and hero["action_until"] > self.tick:
            return
        if hero["action_until"] <= self.tick:
            hero["action"] = "idle"
        if hero["disabled_until"] > self.tick or self.tick - hero["born"] < ticks(0.5):
            return
        hero_type, data = hero["type"], hero["data"]
        if (
            hero_type == "gatherer"
            and hero["next_passive"] <= self.tick
            and hero["mana"] >= data["passive_mana"]
        ):
            self._mana(hero, -data["passive_mana"])
            gatherers = sorted(
                (h for h in self.heroes.values() if h["type"] == "gatherer"),
                key=lambda h: h["id"],
            )
            order = next(i for i, h in enumerate(gatherers) if h["id"] == hero["id"])
            value = round(data.get("orb_value", 20) * (1, 0.8, 0.6)[min(order, 2)])
            if data.get("shared_breath"):
                for ally in self.heroes.values():
                    if self._near(hero, ally, 1.5):
                        self._mana(ally, data["shared_breath"])
            if hero["orb_count"] < 3 and any(
                unit["type"] == "formation" and self._near(hero, unit, 1.5)
                for unit in self.heroes.values()
            ):
                value += 5
            hero["orb_count"] += 1
            hero["next_passive"] = self.tick + ticks(data.get("orb_interval", 8))
            orb = {
                "id": self._id(),
                "x": hero["x"],
                "lane": hero["lane"],
                "value": value,
                "born": self.tick,
            }
            self.orbs[orb["id"]] = orb
            hero["action"] = "skill"
            hero["action_started"] = self.tick
            hero["action_until"] = self.tick + ticks(0.5)
            self._resonance(hero, 12)
            self._effect("qi", hero["x"], hero["lane"], f"+{value}")
            self._event("hero_skill", "", hero["x"], hero["lane"], actor="gatherer")
        if (
            hero_type == "herbalist"
            and hero["next_passive"] <= self.tick
            and hero["mana"] >= data["passive_mana"]
        ):
            allies = [
                ally
                for ally in self.heroes.values()
                if ally["id"] != hero["id"]
                and self._near(hero, ally, 3)
                and ally["hp"] < ally["max_hp"]
            ]
            if allies:
                ally = min(allies, key=lambda h: (h["hp"] / h["max_hp"], h["id"]))
                self._mana(hero, -data["passive_mana"])
                self._heal(
                    ally, data.get("heal_amount", 45) + (15 if hero["herb"] else 0)
                )
                if data.get("heal_targets", 1) > 1:
                    others = sorted(
                        (a for a in allies if a["id"] != ally["id"]),
                        key=lambda a: a["hp"] / a["max_hp"],
                    )
                    if others:
                        self._heal(others[0], round(data.get("heal_amount", 45) * 0.7))
                hero["herb"] = max(0, hero["herb"] - 1)
                self._resonance(hero, 15)
                hero["action_started"] = self.tick
                hero["action"] = "skill"
                hero["action_until"] = self.tick + ticks(0.5)
            else:
                hero["herb"] = min(2, hero["herb"] + 1)
            hero["next_passive"] = self.tick + ticks(data.get("heal_interval", 6))
        if (
            hero["auto_skill"]
            and hero["next_skill"] <= self.tick
            and hero["mana"] >= data["skill"]["mana_cost"]
        ):
            if self._skill(hero):
                self._mana(hero, -data["skill"]["mana_cost"])
                self._event("hero_skill", "", hero["x"], hero["lane"], actor=hero_type)
                hero["next_skill"] = self.tick + ticks(
                    data.get(
                        "circuit_cooldown", data.get("skill", {}).get("cooldown", 9)
                    )
                )
        if hero["action"] in ("skill", "ultimate") and hero["action_until"] > self.tick:
            return
        if data.get("damage", 0) <= 0 or hero["next_attack"] > self.tick:
            return
        targets = self._targets(hero)
        if not targets:
            return
        target = targets[0]
        speed, multiplier, _ = self._buffs(hero)
        hero["next_attack"] = self.tick + ticks(data.get("interval", 1.5) / speed)
        hero["action_started"] = self.tick
        hero["action"] = "attack"
        self._event("hero_attack", "", hero["x"], hero["lane"], actor=hero_type)
        hero["action_until"] = self.tick + ticks(data.get("windup", 0.3) + 0.25)
        self._schedule(
            data.get("windup", 0.3),
            "hero_attack",
            hero=hero["id"],
            target=target["id"],
            multiplier=multiplier,
        )

    def _skill(self, hero):
        kind, data = hero["type"], hero["data"]
        targets = self._targets(
            hero,
            radius=max(data["range"], 1.25) if kind == "monk" else None,
            all_lanes=bool(data.get("staff_arc")),
        )
        if kind == "sword":
            targets = [e for e in targets if e["x"] - hero["x"] <= 3.5]
        if kind == "sword" and targets:
            for enemy in targets[:3]:
                self._hurt_enemy(enemy, data["skill"]["power"], "Sword", hero)
                self._stun(enemy, 0.3)
            self._effect("sword", hero["x"] + 1, hero["lane"], "CROSSWIND")
        elif kind == "fire" and len(targets) >= 2:
            self._launch(
                hero,
                targets[0],
                data["skill"]["power"],
                "Fire",
                radius=data.get("skill_radius", 0.9),
                burn=8,
            )
        elif kind == "frost":
            allies = [
                a
                for a in self.heroes.values()
                if self._near(a, hero, 2) and a["hp"] < a["max_hp"]
            ]
            if not allies:
                return False
            ally = min(allies, key=lambda h: (h["hp"] / h["max_hp"], h["id"]))
            for ally in sorted(allies, key=lambda h: h["hp"] / h["max_hp"])[
                : data.get("shield_targets", 1)
            ]:
                self._shield(
                    ally, data["skill"]["power"], data.get("shield_duration", 4)
                )
        elif kind == "monk" and targets and targets[0]["x"] - hero["x"] < 1.3:
            for enemy in list(targets):
                if enemy["x"] - hero["x"] <= 1.3:
                    self._hurt_enemy(enemy, data["skill"]["power"], "Physical", hero)
                    if not enemy["data"].get("boss"):
                        enemy["x"] = min(12.1, enemy["x"] + data.get("knockback", 0.35))
            self._effect("slam", hero["x"] + 0.6, hero["lane"], "EARTH SHAKE")
        elif kind == "lightning" and targets:
            target = targets[0]
            self._hurt_enemy(
                target,
                (
                    data["skill"]["power"]
                    if target["type"] == "yaksha" or target["conductive"] >= 2
                    else round(data["damage"] * 55 / 30)
                ),
                "Lightning",
                hero,
            )
            chained = sorted(
                (
                    e
                    for e in self.enemies.values()
                    if e["id"] != target["id"] and self._near(target, e, 1.5)
                ),
                key=lambda e: (e["x"], e["id"]),
            )
            for other in chained[:2]:
                self._hurt_enemy(
                    other, round(data["damage"] * 35 / 30), "Lightning", hero
                )
            self._effect("lightning", target["x"], target["lane"])
        elif kind == "herbalist":
            allies = [a for a in self.heroes.values() if self._near(a, hero, 3)]
            if not allies:
                return False
            ally = min(allies, key=lambda h: (h["hp"] / h["max_hp"], h["id"]))
            debuffs = (
                ["curse"]
                if ally.get("curse", 0) or ally.get("curse_until", 0) > self.tick
                else []
            )
            if data.get("cleanse_count", 1) > 1:
                debuffs += [
                    name
                    for name in ("spore_until", "disabled_until")
                    if ally.get(name, 0) > self.tick
                ]
            if debuffs:
                for name in debuffs[: data.get("cleanse_count", 1)]:
                    if name == "curse":
                        ally["curse"] = 0
                        ally["curse_until"] = 0
                    else:
                        ally[name] = 0
                self._heal(ally, data["skill"]["power"])
            else:
                self._shield(
                    ally, data.get("cleanse_shield", 45), data.get("shield_duration", 3)
                )
            self._resonance(hero, 10)
        elif kind == "formation":
            allies = [
                a
                for a in self.heroes.values()
                if a["id"] != hero["id"] and self._near(a, hero, 2.5)
            ]
            if not allies:
                return False
            allies.sort(key=lambda h: (-h["resonance"], h["hp"] / h["max_hp"], h["id"]))
            for ally in allies[:3]:
                self._resonance(ally, data.get("circuit_resonance", 20))
                self._mana(ally, data.get("circuit_mana", 0))
                self._effect("aura", ally["x"], ally["lane"], "+DAO")
            self._resonance(hero, 12)
        else:
            return False
        hero["action_started"] = self.tick
        hero["action"] = "skill"
        hero["action_until"] = self.tick + ticks(0.5)
        return True

    def _ultimate(self, hero):
        kind = hero["type"]
        hero["action_started"] = self.tick
        hero["action"] = "ultimate"
        hero["action_until"] = self.tick + ticks(1.2)
        self._event(
            "ultimate",
            hero["data"].get("name", kind) + " unleashes an ultimate!",
            hero["x"],
            hero["lane"],
            actor=kind,
        )
        self._effect("ultimate", hero["x"], hero["lane"], "ULTIMATE", 1.4)
        targets = sorted(
            (enemy for enemy in self.enemies.values() if enemy["lane"] == hero["lane"]),
            key=lambda e: (e["x"], e["id"]),
        )
        if kind == "gatherer":
            for number in range(1, 5):
                self._schedule(number * 1.5, "well", hero=hero["id"])
        elif kind == "sword":
            for number in range(10):
                self._schedule(
                    0.1 + number * 0.12, "blade", hero=hero["id"], lane=hero["lane"]
                )
        elif kind == "fire":
            for target in targets[:3]:
                self._tell("fire", [target["lane"]], 0.8, x=target["x"])
                self._schedule(
                    0.8,
                    "eruption",
                    hero=hero["id"],
                    x=target["x"],
                    lane=target["lane"],
                    power=hero["data"]["ultimate"]["power"],
                )
        elif kind == "frost":
            for target in targets:
                self._hurt_enemy(
                    target,
                    hero["data"]["ultimate"]["power"],
                    "Ice",
                    hero,
                    ultimate=True,
                )
                self._stun(target, 1.75 * hero["data"].get("cc_duration", 1))
            self._effect("freeze", 4.8, hero["lane"], "THOUSAND YEAR FROST", 1.2)
        elif kind == "monk":
            self._shield(hero, round(hero["max_hp"] * 0.5), 5)
            hero["taunt_until"] = self.tick + ticks(2.5)
            for target in targets:
                self._hurt_enemy(
                    target,
                    hero["data"]["ultimate"]["power"],
                    "Physical",
                    hero,
                    ultimate=True,
                )
        elif kind == "lightning":
            for target in targets[:5]:
                self._tell("lightning", [target["lane"]], 0.6, x=target["x"])
                self._schedule(
                    0.6,
                    "thunder",
                    hero=hero["id"],
                    target=target["id"],
                    power=hero["data"]["ultimate"]["power"],
                )
        elif kind == "herbalist":
            for ally in self.heroes.values():
                self._heal(ally, hero["data"]["ultimate"]["power"])
                ally["curse"] = 0
                ally["curse_until"] = 0
                self._shield(ally, 65, 3)
        elif kind == "formation":
            hero["array_until"] = self.tick + ticks(6)
            self._effect("array", hero["x"], hero["lane"], "GRAND ARRAY", 6)

    def _resonance(self, hero, amount):
        hero["resonance"] = min(100, hero["resonance"] + amount)

    def _shield(self, unit, amount, duration):
        unit["shield"] = max(unit["shield"], amount)
        unit["shield_until"] = self.tick + ticks(duration)
        self._effect("shield", unit["x"], unit["lane"], f"+{amount}")

    def _heal(self, hero, amount):
        actual = min(hero["max_hp"] - hero["hp"], amount)
        hero["hp"] += actual
        self.metrics["healing"] += actual
        if actual:
            self._effect("heal", hero["x"], hero["lane"], f"+{math.floor(actual)}")

    def _collect(self, orb):
        if orb["id"] not in self.orbs:
            return
        del self.orbs[orb["id"]]
        self._add_qi(orb["value"], "gatherer")
        self._event("collect", f"+{orb['value']} Qi", orb["x"], orb["lane"])

    def _slow(self, enemy, power, duration):
        if enemy["data"].get("boss"):
            power *= 0.5
        cap = 0.4 if enemy["type"] == "yaksha" else 0.7
        enemy["slow_power"] = min(cap, max(enemy["slow_power"], power))
        enemy["slow_until"] = max(enemy["slow_until"], self.tick + ticks(duration))

    def _stun(self, enemy, duration):
        if enemy["id"] not in self.enemies:
            return
        if enemy["type"] == "altar":
            return
        if self.tick - enemy["cc_last"] >= ticks(6):
            enemy["cc_count"] = 0
        multipliers = (1, 0.75, 0.5, 0.25, 0)
        duration *= multipliers[min(4, enemy["cc_count"])]
        enemy["cc_count"] += 1
        enemy["cc_last"] = self.tick
        if enemy["data"].get("boss"):
            self._slow(enemy, 0.25, 2)
            return
        if enemy["type"] == "yaksha":
            duration *= 0.5
        if duration > 0:
            enemy["frozen_until"] = max(
                enemy["frozen_until"], self.tick + ticks(duration)
            )
            enemy["channel_token"] += 1
            self._effect(
                "freeze", enemy["x"], enemy["lane"], duration=min(1.5, duration)
            )

    def _burn(self, enemy, amount, duration, owner):
        enemy["burn_damage"] = amount
        enemy["burn_until"] = self.tick + ticks(duration)
        enemy["burn_owner"] = owner["id"] if owner else 0
        if enemy["burn_next"] <= self.tick:
            enemy["burn_next"] = self.tick + HZ

    def _hurt_enemy(self, enemy, raw, damage_type, owner=None, ultimate=False):
        if enemy["id"] not in self.enemies or enemy["invulnerable_until"] > self.tick:
            return 0
        data = enemy["data"]
        damage_type = damage_type.title()
        armor = data.get("armor", 0) - (
            enemy.get("armor_break", 3) if enemy["armor_break_until"] > self.tick else 0
        )
        if enemy["type"] in ("hound", "mountainlord") and enemy["shield"] > 0:
            armor = 10
        resistance = data.get("resistances", data.get("resistance", {}))
        if not isinstance(resistance, dict):
            resistance = {}
        resist = resistance.get(damage_type, resistance.get(damage_type.lower(), 0))
        if abs(resist) > 1:
            resist /= 100
        amount = damage_amount(raw, armor, resist, damage_type == "True")
        if self._hidden(enemy):
            amount = max(1, math.floor(amount * 0.6))
        if enemy["type"] == "mountainlord" and enemy["shield"] > 0:
            segment = data.get("plate_hp", 180)
            amount = min(amount, enemy["shield"] % segment or segment)
        shield_before = enemy["shield"]
        shield_damage = min(enemy["shield"], amount)
        enemy["shield"] -= shield_damage
        amount -= shield_damage
        if enemy["type"] in ("hound", "mountainlord") and shield_before > 0:
            segment = data.get("plate_hp", shield_before)
            if math.ceil(enemy["shield"] / segment) < math.ceil(
                shield_before / segment
            ):
                self.metrics["plates_broken"] += 1
                self._effect(
                    "armor_break", enemy["x"], enemy["lane"], "ARMOR BROKEN", 1
                )
                if enemy["type"] == "mountainlord":
                    data["armor"] = max(2, data.get("armor", 14) - 4)
                else:
                    enemy["frozen_until"] = self.tick + ticks(1.1)
        if data.get("boss") and enemy["phase"] < 3:
            threshold = 0.7 if enemy["phase"] == 1 else 0.35
            amount = min(
                amount, max(0, enemy["hp"] - math.ceil(enemy["max_hp"] * threshold))
            )
        else:
            amount = min(amount, max(0, enemy["hp"]))
        enemy["hp"] -= amount
        enemy["last_hit"] = self.tick
        enemy["regen_ticks"] = 0
        if enemy["action"] == "channel":
            enemy["channel_token"] += 1
            enemy["action"] = "hurt"
            self._event(
                "interrupt", "Drain channel interrupted!", enemy["x"], enemy["lane"]
            )
        total = amount + shield_damage
        self._effect("damage", enemy["x"], enemy["lane"], str(math.floor(total)), 0.5)
        if owner:
            key = owner["type"]
            self.metrics["damage"][key] = self.metrics["damage"].get(key, 0) + total
            enemy["damage_owners"][owner["id"]] = self.tick
            if not ultimate:
                self._resonance(owner, 8)
        if data.get("boss"):
            self._boss_phase(enemy)
        if enemy["hp"] <= 0:
            self._kill(enemy, owner)
        return total

    def _hurt_hero(self, hero, raw, damage_type="Physical"):
        if hero["id"] not in self.heroes or self.tick - hero["born"] < ticks(0.25):
            return
        _, _, reduction = self._buffs(hero)
        damage_type = damage_type.title()
        if hero["type"] == "monk" and damage_type == "Physical":
            reduction = 1 - (1 - reduction) * 0.9
        resistance = hero["data"].get("resistances", {}).get(damage_type.lower(), 0)
        reduction = 1 - (1 - reduction) * (1 - resistance)
        amount = damage_amount(
            raw, hero["data"].get("armor", 0), reduction, damage_type == "True"
        )
        absorbed = min(hero["shield"], amount)
        hero["shield"] -= absorbed
        hero["hp"] -= amount - absorbed
        hero["hurt_hits"] += 1
        self._resonance(hero, 4)
        if (
            hero["action"] not in ("ultimate", "skill")
            or hero["action_until"] <= self.tick
        ):
            hero["action"] = "hurt"
            hero["action_until"] = self.tick + ticks(0.2)
        self._effect("hurt", hero["x"], hero["lane"], str(amount), 0.4)
        if hero["type"] == "monk" and hero["hurt_hits"] % 4 == 0:
            self._shield(hero, 35, 3)
        if hero["hp"] <= 0:
            del self.heroes[hero["id"]]
            self.metrics["deaths"] += 1
            self._event(
                "death",
                hero["data"].get("name", hero["type"]) + " has fallen.",
                hero["x"],
                hero["lane"],
            )
            self._effect("death", hero["x"], hero["lane"], duration=0.7)

    def _kill(self, enemy, owner):
        if enemy["id"] not in self.enemies:
            return
        del self.enemies[enemy["id"]]
        self.kills += 1
        for unit_id, hit_at in list(enemy["damage_owners"].items())[:3]:
            if self.tick - hit_at <= ticks(3) and unit_id in self.heroes:
                self._resonance(self.heroes[unit_id], 10)
        if owner and owner["id"] in self.heroes:
            self._resonance(owner, 5)
        self._effect("kill", enemy["x"], enemy["lane"], duration=0.7)
        if enemy["type"] == "altar":
            self.metrics["altars_destroyed"] += 1
            self._event(
                "altar",
                "A soul-seal altar is destroyed. The dead lose their anchor.",
                enemy["x"],
                enemy["lane"],
            )
        if enemy["type"] == "lantern":
            self._schedule(0.65, "lantern_burst", x=enemy["x"], lane=enemy["lane"])
            if self.stage.get("index", 0) >= 1:
                self._add_qi(15, "enemy_drop")
        elif enemy["type"] in ("hound", "drainer"):
            self._add_qi(20, "enemy_drop")
        if enemy["data"].get("boss"):
            self._event(
                "boss_defeat", enemy["data"].get("name", enemy["type"]) + " defeated."
            )
            self._spawn_index = len(self._spawn_queue)
            self.pending = [
                entry
                for entry in self.pending
                if entry[2] not in ("spawn", "resurrect")
            ]
            heapq.heapify(self.pending)
            for other in list(self.enemies.values()):
                if not other["data"].get("boss"):
                    del self.enemies[other["id"]]
                    self._effect("flee", other["x"], other["lane"], duration=0.7)
        elif (
            self.region == "tomb"
            and enemy["type"] in ("soul", "swordcorpse")
            and not enemy.get("resurrected")
            and self._reveal_until <= self.tick
            and any(e["type"] == "altar" for e in self.enemies.values())
        ):
            self._schedule(
                6, "resurrect", type=enemy["type"], lane=enemy["lane"], x=enemy["x"]
            )

    def _launch(self, hero, target, damage, kind, radius=0, burn=0, pierce=1):
        projectile_id = self._id()
        self.projectiles[projectile_id] = {
            "id": projectile_id,
            "owner": hero["id"],
            "target": target["id"],
            "type": hero["type"],
            "kind": kind.title(),
            "lane": hero["lane"],
            "x": hero["x"] + 0.3,
            "start": hero["x"],
            "speed": hero["data"].get("projectile_speed", 6),
            "damage": damage,
            "radius": radius,
            "splash_factor": hero["data"].get("splash_factor", 0.6),
            "burn": burn,
            "pierce": pierce,
            "hit": [],
            "range": hero["data"].get("range", 5.5),
        }

    def _projectile_tick(self):
        for projectile in list(self.projectiles.values()):
            old = projectile["x"]
            wind = 1.0
            if self.region == "terrace":
                wind = (
                    1.15
                    if self._wind_lock > self.tick
                    else 1.2 if (self.tick // ticks(20)) % 2 == 0 else 0.8
                )
            projectile["x"] += max(1, projectile["speed"]) * STEP * wind
            owner = self.heroes.get(projectile["owner"])
            candidates = sorted(
                [
                    e
                    for e in self.enemies.values()
                    if e["lane"] == projectile["lane"]
                    and e["id"] not in projectile["hit"]
                    and old - 0.3 <= e["x"] <= projectile["x"] + 0.2
                ],
                key=lambda e: e["x"],
            )
            for enemy in candidates:
                if self._hidden(enemy) and projectile["kind"] not in (
                    "Fire",
                    "Lightning",
                ):
                    continue
                if (
                    enemy["type"] == "swordcorpse"
                    and enemy["absorb_until"] > self.tick
                    and enemy["absorbed"] < 3
                    and not projectile["radius"]
                ):
                    enemy["absorbed"] += 1
                    enemy["hp"] = min(enemy["max_hp"], enemy["hp"] + 15)
                    self._effect("absorb", enemy["x"], enemy["lane"], "ABSORBED")
                    projectile["pierce"] = 0
                    break
                projectile["hit"].append(enemy["id"])
                if projectile["radius"]:
                    targets = [
                        target
                        for target in self.enemies.values()
                        if self._near(target, enemy, projectile["radius"])
                    ]
                    for target in targets:
                        self._hurt_enemy(
                            target,
                            projectile["damage"]
                            * (
                                1
                                if target["id"] == enemy["id"]
                                else projectile["splash_factor"]
                            ),
                            projectile["kind"],
                            owner,
                        )
                        if target["id"] in self.enemies and projectile["burn"]:
                            self._burn(
                                target,
                                projectile["burn"],
                                owner["data"].get("burn_duration", 3) if owner else 3,
                                owner,
                            )
                    self._effect("fire", enemy["x"], enemy["lane"], duration=0.6)
                else:
                    self._hurt_enemy(
                        enemy, projectile["damage"], projectile["kind"], owner
                    )
                    if owner and enemy["id"] in self.enemies:
                        self._hit_passive(owner, enemy)
                if owner:
                    owner["hits"] += 1
                projectile["pierce"] -= 1
                if projectile["pierce"] <= 0:
                    break
            if (
                projectile["pierce"] <= 0
                or projectile["x"] > 12.4
                or projectile["x"] - projectile["start"] > projectile["range"]
            ):
                self.projectiles.pop(projectile["id"], None)

    def _hit_passive(self, owner, target):
        if owner["type"] == "sword" and (owner["hits"] + 1) % 3 == 0:
            self._mana(owner, owner["data"].get("third_mana", 0))
        if owner["type"] == "frost":
            self._slow(target, 0.15 if owner["data"].get("branch") == "A" else 0.2, 2)
            if (owner["hits"] + 1) % 3 == 0:
                target["frost"] += 1
                required = 2 if owner["data"].get("branch") == "A" else 3
                if target["frost"] >= required:
                    self._stun(target, 1.1 * owner["data"].get("cc_duration", 1))
                    target["frost"] = 0

    def _resolve(self, kind, data):
        hero = self.heroes.get(data.get("hero"))
        if kind == "hero_attack":
            target = self.enemies.get(data["target"])
            if not hero or not target or hero["disabled_until"] > self.tick:
                return
            hero_data = hero["data"]
            damage = hero_data.get("damage", 0) * data.get("multiplier", 1)
            if hero["type"] == "sword" and (hero["hits"] + 1) % 3 == 0:
                damage *= 1.15 if hero_data.get("branch") == "B" else 1.25
            if hero["type"] == "monk":
                if abs(target["x"] - hero["x"]) <= hero_data.get("range", 1) + 0.2:
                    self._hurt_enemy(target, damage, "Physical", hero)
                    hero["hits"] += 1
                    self._effect("melee", target["x"], target["lane"])
            elif hero["type"] == "lightning":
                chain = [target]
                for enemy in sorted(
                    self.enemies.values(),
                    key=lambda e: (abs(e["x"] - target["x"]), e["id"]),
                ):
                    if enemy["id"] != target["id"] and self._near(
                        chain[-1], enemy, hero_data.get("chain_range", 1.25)
                    ):
                        chain.append(enemy)
                    if len(chain) >= hero_data.get("chains", 3):
                        break
                factors = (1, 0.7, 0.45, 0.35)
                for index, enemy in enumerate(chain):
                    bonus = (
                        hero_data.get("conductive_damage", 24)
                        if enemy["conductive"] >= 3
                        else 0
                    )
                    if bonus:
                        self._mana(hero, hero_data.get("conductive_mana", 0))
                        enemy["conductive"] = 0
                        enemy["armor_break_until"] = self.tick + ticks(3)
                        enemy["armor_break"] = hero_data.get("armor_break", 3)
                    enemy["conductive"] = min(3, enemy["conductive"] + 1)
                    enemy["conductive_until"] = self.tick + ticks(5)
                    self._hurt_enemy(
                        enemy, damage * factors[index] + bonus, "Lightning", hero
                    )
                    self._effect("lightning", enemy["x"], enemy["lane"])
                hero["hits"] += 1
            else:
                self._launch(
                    hero,
                    target,
                    damage,
                    hero_data.get("damage_type", "Sword"),
                    radius=(
                        hero_data.get("splash_radius", 0.55)
                        if hero["type"] == "fire"
                        else 0
                    ),
                    burn=(
                        hero_data.get(
                            "burn_damage", 14 if hero_data.get("branch") == "A" else 10
                        )
                        if hero["type"] == "fire" and (hero["hits"] + 1) % 4 == 0
                        else 0
                    ),
                    pierce=hero_data.get(
                        "pierce",
                        (
                            2
                            if hero["type"] == "sword"
                            and hero_data.get("branch") == "A"
                            else 1
                        ),
                    ),
                )
        elif kind == "enemy_hit":
            enemy, target = self.enemies.get(data["enemy"]), self.heroes.get(
                data["target"]
            )
            if not enemy or not target or enemy["frozen_until"] > self.tick:
                return
            if (
                target["lane"] == enemy["lane"]
                and abs(enemy["x"] - target["x"])
                <= enemy["data"].get("range", 0.8) + 0.35
            ):
                self._hurt_hero(
                    target, data["damage"], enemy["data"].get("damage_type", "Physical")
                )
                if (
                    enemy["type"] in ("soul", "boneemperor")
                    and target["id"] in self.heroes
                ):
                    target["curse"] += 1
                    if target["curse"] >= 3:
                        target["curse"] = 0
                        target["curse_until"] = self.tick + ticks(8)
                if enemy["type"] == "drowned" and target["id"] in self.heroes:
                    target["disabled_until"] = self.tick + ticks(0.65)
        elif kind == "drain":
            enemy = self.enemies.get(data["enemy"])
            if (
                enemy
                and enemy["channel_token"] == data["token"]
                and enemy["frozen_until"] <= self.tick
            ):
                amount = min(30, self.qi)
                self.qi -= amount
                enemy["shield"] = min(60, enemy["shield"] + amount)
                self._event(
                    "drain", f"Qi Adept stole {amount} Qi!", enemy["x"], enemy["lane"]
                )
        elif kind == "lantern_burst":
            for target in list(self.heroes.values()):
                if self._near(target, data, 0.8):
                    self._hurt_hero(target, 30, "Spirit")
            for target in list(self.enemies.values()):
                if self._near(target, data, 0.8):
                    self._hurt_enemy(target, 30, "Spirit")
            self._effect("fire", data["x"], data["lane"], duration=0.8)
        elif kind == "well" and hero:
            self._add_qi(12, "ultimate")
            self._effect("qi", hero["x"], hero["lane"], "+12")
        elif kind == "blade" and hero:
            targets = sorted(
                (e for e in self.enemies.values() if e["lane"] == data["lane"]),
                key=lambda e: (e["x"], e["id"]),
            )
            if targets:
                self._hurt_enemy(
                    targets[(self.tick // ticks(0.12)) % min(3, len(targets))],
                    hero["data"]["ultimate"]["power"],
                    "Sword",
                    hero,
                    ultimate=True,
                )
        elif kind == "eruption":
            for target in list(self.enemies.values()):
                if self._near(target, data, 1.1):
                    self._hurt_enemy(
                        target,
                        data.get(
                            "power", hero["data"]["ultimate"]["power"] if hero else 0
                        ),
                        "Fire",
                        hero,
                        ultimate=True,
                    )
            self.zones.append(
                {
                    "x": data["x"],
                    "lane": data["lane"],
                    "radius": 1.1,
                    "damage": 8,
                    "until": self.tick + ticks(4),
                    "next": self.tick + HZ,
                    "owner": data.get("hero"),
                }
            )
            self._effect("eruption", data["x"], data["lane"], duration=1.2)
        elif kind == "thunder":
            target = self.enemies.get(data["target"])
            if target:
                self._hurt_enemy(
                    target,
                    data.get("power", hero["data"]["ultimate"]["power"] if hero else 0),
                    "Lightning",
                    hero,
                    ultimate=True,
                )
                target["conductive"] = min(3, target["conductive"] + 2)
                self._effect("lightning", target["x"], target["lane"], duration=0.9)
        elif kind == "boss_hit":
            boss = self.enemies.get(data["enemy"])
            if not boss:
                return
            for target in list(self.heroes.values()):
                if target["lane"] in data["lanes"] and (
                    data.get("x") is None or abs(target["x"] - data["x"]) < 0.9
                ):
                    self._hurt_hero(
                        target, data["damage"], data.get("damage_type", "Spirit")
                    )
                    self._effect("slam", target["x"], target["lane"], duration=0.7)
            if boss["type"] == "riverlord":
                self._spawn("tide", (boss["lane"] + 1) % 5)
            elif boss["type"] == "boneemperor" and boss["phase"] >= 2:
                self._spawn("soul", (boss["lane"] + 2) % 5)
        elif kind == "spawn":
            if data.get("source") is None or data["source"] in self.enemies:
                self._spawn(data["type"], data["lane"])
        elif kind == "resurrect":
            if self._reveal_until > self.tick or not any(
                e["type"] == "altar" for e in self.enemies.values()
            ):
                return
            enemy = self._spawn(data["type"], data["lane"], max(1, data["x"]))
            if enemy:
                enemy["hp"] = math.ceil(enemy["max_hp"] * 0.35)
                enemy["resurrected"] = True
                self._effect("resurrect", enemy["x"], enemy["lane"], "RISEN", 1)
        elif kind == "break_altar":
            altar = self.enemies.get(data["altar"])
            if altar:
                self._kill(altar, None)
        elif kind == "hound_rush":
            enemy = self.enemies.get(data["enemy"])
            if enemy and enemy["frozen_until"] <= self.tick:
                end = max(0.6, enemy["x"] - 1.5)
                blockers = [
                    h
                    for h in self.heroes.values()
                    if h["lane"] == enemy["lane"] and end <= h["x"] <= enemy["x"]
                ]
                if blockers:
                    target = max(blockers, key=lambda h: h["x"])
                    enemy["x"] = target["x"] + 0.7
                    self._hurt_hero(target, 90, "Physical")
                else:
                    enemy["x"] = end
                self._effect("rush", enemy["x"], enemy["lane"], "RUSH")
        elif kind == "spore":
            if data["enemy"] in self.enemies:
                self.zones.append(
                    {
                        "x": data["x"],
                        "lane": data["lane"],
                        "radius": 1.2,
                        "damage": 10,
                        "until": self.tick + ticks(3.1),
                        "next": self.tick + HZ,
                        "side": "heroes",
                    }
                )
                self._effect("spore", data["x"], data["lane"], "SPORES", 3)

    def _update_zones(self):
        for zone in list(self.zones):
            if zone["until"] <= self.tick:
                self.zones.remove(zone)
                continue
            if zone["next"] <= self.tick:
                zone["next"] = self.tick + HZ
                if zone.get("side") == "heroes":
                    for hero in list(self.heroes.values()):
                        if self._near(hero, zone, zone["radius"]):
                            self._hurt_hero(hero, zone["damage"], "Wood")
                            hero["spore_until"] = self.tick + ticks(1.1)
                    continue
                for enemy in list(self.enemies.values()):
                    if self._near(enemy, zone, zone["radius"]):
                        self._hurt_enemy(
                            enemy,
                            zone["damage"],
                            "Fire",
                            self.heroes.get(zone["owner"]),
                            ultimate=True,
                        )

    def _enemy_tick(self, enemy):
        data, kind = enemy["data"], enemy["type"]
        if enemy["shield_until"] and enemy["shield_until"] <= self.tick:
            enemy["shield"] = 0
        if enemy["slow_until"] <= self.tick:
            enemy["slow_power"] = 0
        if enemy["conductive_until"] <= self.tick:
            enemy["conductive"] = 0
        if enemy["burn_until"] > self.tick and enemy["burn_next"] <= self.tick:
            enemy["burn_next"] += HZ
            self._hurt_enemy(
                enemy,
                enemy["burn_damage"],
                "Fire",
                self.heroes.get(enemy["burn_owner"]),
                ultimate=True,
            )
            if enemy["id"] not in self.enemies:
                return
        if enemy["frozen_until"] > self.tick or enemy["invulnerable_until"] > self.tick:
            return
        if kind == "altar":
            return
        if enemy["action_until"] <= self.tick:
            enemy["action"] = "walk"
        if data.get("boss"):
            if (
                kind == "boneemperor"
                and enemy["phase"] >= 2
                and enemy["next_edict"] <= self.tick
                and any(e["type"] == "altar" for e in self.enemies.values())
            ):
                enemy["shield"] = min(
                    enemy["max_hp"] * 0.06, enemy["shield"] + enemy["max_hp"] * 0.03
                )
                enemy["next_edict"] = self.tick + ticks(15)
            if enemy["next_boss"] <= self.tick:
                self._boss_skill(enemy)
                enemy["next_boss"] = self.tick + ticks(11 - enemy["phase"])
        elif enemy["next_skill"] <= self.tick:
            enemy["next_skill"] = self.tick + ticks(
                data.get(
                    "ability_interval", 6 if kind in ("lantern", "swordcorpse") else 8
                )
            )
            if kind == "lantern":
                for other in self.enemies.values():
                    if self._near(enemy, other, 1.5) and other["shield"] <= 0:
                        self._shield(
                            other,
                            data.get("shield_amount", 25)
                            + (10 if enemy.get("rank") in ("elite", "captain") else 0),
                            6,
                        )
            elif kind == "drainer" and self.qi >= 30:
                enemy["channel_token"] += 1
                enemy["action"] = "channel"
                enemy["action_until"] = self.tick + ticks(1)
                self._schedule(
                    1, "drain", enemy=enemy["id"], token=enemy["channel_token"]
                )
                self._effect("drain", enemy["x"], enemy["lane"], "DRAIN", 1)
            elif kind == "swordcorpse":
                enemy["absorbed"] = 0
                enemy["absorb_until"] = self.tick + ticks(1)
                self._effect("absorb", enemy["x"], enemy["lane"], "SWALLOW", 1)
            elif kind == "hound":
                blockers = [
                    hero
                    for hero in self.heroes.values()
                    if hero["lane"] == enemy["lane"] and 0 < enemy["x"] - hero["x"] < 2
                ]
                if not blockers:
                    enemy["action"] = "ability"
                    enemy["action_until"] = self.tick + ticks(1.1)
                    self._tell(
                        "SHOULDER RUSH", [enemy["lane"]], 1.1, x=enemy["x"] - 0.75
                    )
                    self._schedule(1.1, "hound_rush", enemy=enemy["id"])
            elif kind == "rottenwood":
                enemy["action"] = "ability"
                enemy["action_until"] = self.tick + HZ
                self._tell("SPORE CLOUD", [enemy["lane"]], 1, x=enemy["x"])
                self._schedule(
                    1, "spore", enemy=enemy["id"], x=enemy["x"], lane=enemy["lane"]
                )
        if (
            kind == "rottenwood"
            and self.tick - enemy["last_hit"] > ticks(3)
            and enemy["regen_ticks"] < 5
        ):
            if self.tick % HZ == 0:
                enemy["hp"] = min(enemy["max_hp"], enemy["hp"] + 30)
                enemy["regen_ticks"] += 1
                self._effect("heal", enemy["x"], enemy["lane"], "+30")
            return
        flying = kind == "yaksha" and (self.tick - enemy["born"]) % ticks(7) < ticks(
            4.5
        )
        allies = [
            hero
            for hero in self.heroes.values()
            if hero["lane"] == enemy["lane"]
            and self.tick - hero["born"] >= ticks(0.25)
            and hero["x"] <= enemy["x"] + 0.25
        ]
        allies.sort(key=lambda hero: (-hero["x"], hero["id"]))
        target = allies[0] if allies else None
        if flying:
            target = None
        elif kind == "yaksha":
            support = [
                hero
                for hero in allies
                if hero["data"].get("role") in ("economy", "support")
            ]
            if support:
                target = support[0]
        attack_range = data.get("range", 0.8)
        if target and enemy["x"] - target["x"] <= attack_range:
            if enemy["next_attack"] <= self.tick and enemy["action_until"] <= self.tick:
                enemy["action"] = "attack"
                windup = data.get("windup", 0.6)
                enemy["action_until"] = self.tick + ticks(windup + 0.15)
                enemy["next_attack"] = self.tick + ticks(data.get("interval", 2))
                damage = data.get("damage", data.get("attack", 24))
                if kind == "swordcorpse" and enemy["absorbed"]:
                    damage += 14 * enemy["absorbed"]
                    enemy["absorbed"] = 0
                self._schedule(
                    windup,
                    "enemy_hit",
                    enemy=enemy["id"],
                    target=target["id"],
                    damage=damage,
                )
            return
        if enemy["action"] == "channel" or enemy["action_until"] > self.tick:
            return
        speed = data.get("speed", 0.35) * (1 - enemy["slow_power"])
        if kind == "tide" and self._hazard()["phase"] == "HIGH TIDE":
            speed *= 1.15
        if any(
            e.get("rank") == "captain"
            and e["id"] != enemy["id"]
            and self._near(e, enemy, 1.5)
            for e in self.enemies.values()
        ):
            speed *= 1.1
        enemy["x"] -= speed * STEP
        ward = self.defenses[enemy["lane"]]
        if enemy["x"] <= 1.0 and ward["status"] == "ready":
            ward.update(status="sweeping", x=0.5)
            self._event(
                "guardian",
                "Guardian seal awakened! This lane has no second rescue.",
                0.5,
                enemy["lane"],
            )
        if enemy["x"] <= 0.5 and ward["status"] == "sweeping":
            return
        if enemy["x"] <= 0.5:
            self.gate = max(0, self.gate - (3 if data.get("boss") else 1))
            self.metrics["breaches"] += 1
            self.enemies.pop(enemy["id"], None)
            self._event(
                "breach", "An enemy breached the immortal gate!", 0.5, enemy["lane"]
            )
            self._effect("breach", 0.5, enemy["lane"], "BREACH", 1)

    def _defense_tick(self):
        """Each lane's guardian sweeps once. Bosses take a single phase-safe hit."""
        for ward in self.defenses:
            if ward["status"] != "sweeping":
                continue
            ward["x"] += 8 * STEP
            for enemy in list(self.enemies.values()):
                if (
                    enemy["lane"] != ward["lane"]
                    or enemy["id"] in ward["hit"]
                    or enemy["x"] > ward["x"] + 0.5
                ):
                    continue
                ward["hit"].add(enemy["id"])
                if enemy["data"].get("boss"):
                    self._hurt_enemy(
                        enemy,
                        enemy["max_hp"] * (0.4 if self.region == "terrace" else 0.35),
                        "True",
                        ultimate=True,
                    )
                    if self.region == "wharf":
                        self._slow(enemy, 0.4, 4)
                    enemy["x"] = max(2.0, enemy["x"])
                else:
                    enemy["resurrected"] = True
                    self._kill(enemy, None)
                self._effect("guardian", ward["x"], ward["lane"], duration=0.35)
            if self.region == "tomb":
                self._reveal_until = max(self._reveal_until, self.tick + ticks(6))
            if self.region == "terrace":
                for h in self.heroes.values():
                    if h["lane"] == ward["lane"] and abs(h["x"] - ward["x"]) < 0.2:
                        self._shield(h, 80, 5)
            if ward["x"] > 12.5:
                ward["status"] = "spent"

    def _boss_phase(self, boss):
        threshold = 0.7 if boss["phase"] == 1 else 0.35 if boss["phase"] == 2 else 0
        if threshold and boss["hp"] <= math.ceil(boss["max_hp"] * threshold):
            boss["hp"] = max(boss["hp"], math.ceil(boss["max_hp"] * threshold))
            boss["phase"] += 1
            boss["invulnerable_until"] = self.tick + ticks(1.3)
            boss["action"] = "phase"
            boss["action_until"] = boss["invulnerable_until"]
            boss["next_boss"] = boss["invulnerable_until"] + ticks(1)
            self._event(
                "phase",
                f"{boss['data'].get('name', boss['type'])}: PHASE {boss['phase']}",
                boss["x"],
                boss["lane"],
            )
            self._effect(
                "phase", boss["x"], boss["lane"], f"PHASE {boss['phase']}", 1.4
            )
            if boss["type"] == "riverlord":
                self._tide_forced = self.tick + ticks(12)
                self._schedule(
                    1.5,
                    "spawn",
                    type="tide",
                    lane=(boss["lane"] + 1) % 5,
                    source=boss["id"],
                )
            elif boss["type"] == "mountainlord":
                boss["shield"] = 0
                boss["data"]["armor"] = max(2, boss["data"].get("armor", 10) - 4)
            elif boss["type"] == "boneemperor":
                self._schedule(
                    1.5,
                    "spawn",
                    type="soul",
                    lane=(boss["lane"] + 2) % 5,
                    source=boss["id"],
                )
                if boss["phase"] == 3:
                    altars = [e for e in self.enemies.values() if e["type"] == "altar"]
                    if altars:
                        altar = min(
                            altars, key=lambda a: (abs(a["x"] - boss["x"]), a["id"])
                        )
                        self._schedule(1.7, "break_altar", altar=altar["id"])

    def _tell(self, kind, lanes, delay, x=None):
        tell = {
            "id": self._id(),
            "kind": kind,
            "lanes": list(lanes),
            "until": self.tick + ticks(delay),
            "x": x,
        }
        self.telegraphs.append(tell)
        return tell

    def _boss_skill(self, boss):
        phase = boss["phase"]
        if boss["type"] == "riverlord":
            lanes, name, delay, amount, damage_type = (
                [boss["lane"], (boss["lane"] + 1) % 5],
                "TIDAL SWEEP",
                1.8,
                55 + phase * 22,
                "Water",
            )
        elif boss["type"] == "mountainlord":
            counts = [
                (sum(1 for h in self.heroes.values() if h["lane"] == lane), lane)
                for lane in range(5)
            ]
            lanes = [lane for _, lane in sorted(counts, reverse=True)[:2]]
            name, delay, amount, damage_type = (
                "MOUNTAIN TREMOR",
                2,
                60 + phase * 20,
                "Physical",
            )
        else:
            start = self.rng.randrange(5)
            lanes = [(start + offset) % 5 for offset in range(min(phase, 3))]
            name, delay, amount, damage_type = (
                "ROYAL DECREE",
                1.8,
                50 + phase * 25,
                "Spirit",
            )
        self._tell(name, lanes, delay)
        self._schedule(
            delay,
            "boss_hit",
            enemy=boss["id"],
            lanes=lanes,
            damage=amount,
            damage_type=damage_type,
        )
        boss["action"] = "ability"
        boss["action_until"] = self.tick + ticks(delay)
        self._event(
            "warning", name + " — shield the marked lanes!", boss["x"], boss["lane"]
        )

    def _encounter(self):
        phase = next(
            (
                p
                for p in self.stage.get("phases", [])
                if self._wave_index <= p["end_wave"]
            ),
            self.stage["phases"][-1],
        )
        return {**phase, "hp_multiplier": self.stage["hp_multiplier"]}

    def _mechanic_tick(self):
        if self.tick % HZ or self.region != "terrace":
            return
        for node in self.nodes:
            invaders = [
                e
                for e in self.enemies.values()
                if e["type"] == "drainer"
                and math.hypot(e["lane"] - node["lane"], e["x"] - (node["col"] + 0.5))
                <= 1
            ]
            allies = [
                h
                for h in self.heroes.values()
                if math.hypot(h["lane"] - node["lane"], h["col"] - node["col"]) <= 1
            ]
            if invaders:
                node["channel"] += 1
                node["purify"] = 0
                if node["channel"] >= 2:
                    node["corrupted"] = True
            elif allies:
                node["channel"] = 0
                node["purify"] += 1
                if node["purify"] >= 3:
                    node["corrupted"] = False
            else:
                node["channel"] = 0
                node["purify"] = 0
            if node["corrupted"] and self.tick % ticks(8) == 0:
                for e in self.enemies.values():
                    if (
                        math.hypot(
                            e["lane"] - node["lane"], e["x"] - (node["col"] + 0.5)
                        )
                        <= 2
                    ):
                        e["hp"] = min(e["max_hp"], e["hp"] + e["max_hp"] * 0.03)

    def _hazard(self):
        if self.region == "wharf":
            if self._calm_until > self.tick:
                return {
                    "name": "Tide Cycle",
                    "phase": "CALM",
                    "countdown": round((self._calm_until - self.tick) / HZ, 1),
                    "tiles": (
                        [
                            {**tile, "type": "blocked", "blocked": True}
                            for tile in self.stage.get("blocked_tiles", [])
                        ]
                        if self.time < self.stage.get("bridge_opens", 0)
                        else []
                    ),
                    "description": "Ritual suppresses flooding for 12s.",
                }
            cycle = self.time % 48
            if self._tide_forced > self.tick or 28 <= cycle < 40:
                phase, remaining = "HIGH TIDE", (
                    max(0, (self._tide_forced - self.tick) / HZ)
                    if self._tide_forced > self.tick
                    else 40 - cycle
                )
            elif cycle < 20:
                phase, remaining = "LOW TIDE", 20 - cycle
            elif cycle < 28:
                phase, remaining = "RISING", 28 - cycle
            else:
                phase, remaining = "RECEDING", 48 - cycle
            tiles = [
                {
                    "lane": lane,
                    "col": col,
                    "type": "water",
                    "blocked": phase == "HIGH TIDE",
                }
                for lane in self.stage.get("water_lanes", [0, 4])
                for col in (3, 4)
            ]
            if self.time < self.stage.get("bridge_opens", float("inf")):
                tiles.extend(
                    {
                        "lane": tile["lane"],
                        "col": tile["col"],
                        "type": "blocked",
                        "blocked": True,
                    }
                    for tile in self.stage.get("blocked_tiles", [])
                )
            return {
                "name": "Tide Cycle",
                "phase": phase,
                "countdown": round(remaining, 1),
                "tiles": tiles,
                "description": "High tide seals the outer water tiles and harms units standing there.",
            }
        if self.region == "terrace":
            phase = (
                "EAST WIND"
                if self._wind_lock > self.tick or (self.tick // ticks(20)) % 2 == 0
                else "WEST WIND"
            )
            return {
                "name": "Ley Wind",
                "phase": phase,
                "countdown": round(20 - self.time % 20, 1),
                "tiles": [
                    {
                        "lane": node["lane"],
                        "col": node["col"],
                        "type": "leyline",
                        "blocked": False,
                        "corrupted": node["corrupted"],
                    }
                    for node in self.nodes
                ],
                "description": "Standing on or beside a ley node grants 12% attack speed. Wind changes projectile travel.",
            }
        mist = self.time % 24 >= 18
        return {
            "name": "Grave Mist",
            "phase": "GRAVE MIST" if mist else "SEALS DORMANT",
            "countdown": round(24 - self.time % 24 if mist else 18 - self.time % 24, 1),
            "tiles": [
                {"lane": lane, "col": 5, "type": "seal", "blocked": mist}
                for lane in self.stage.get("mist_lanes", [1, 3])
            ],
            "description": "Mist seals outer grave tiles. Soul enemies phase; fire and lightning can still hit them.",
        }

    def snapshot(self):
        heroes = []
        for hero in self.heroes.values():
            heroes.append(
                {
                    key: (
                        round(hero[key], 3)
                        if isinstance(hero[key], float)
                        else hero[key]
                    )
                    for key in (
                        "id",
                        "type",
                        "lane",
                        "col",
                        "x",
                        "hp",
                        "max_hp",
                        "shield",
                        "resonance",
                        "mana",
                        "auto_skill",
                        "action",
                    )
                }
            )
            heroes[-1].update(
                stats=hero["public_stats"],
                mana_max=hero["data"]["mana_max"],
                mana_regen=round(self._mana_regen(hero), 3),
                ultimate_cd=round(max(0, hero["ultimate_ready"] - self.tick) / HZ, 2),
                action_started=hero["action_started"] / HZ,
                action_until=hero["action_until"] / HZ,
                skill_cd=round(max(0, hero["next_skill"] - self.tick) / HZ, 2),
                branch=hero["data"].get("branch"),
                curse=hero["curse"],
                array=max(0, hero["array_until"] - self.tick) / HZ,
            )
        enemies = []
        for enemy in self.enemies.values():
            enemies.append(
                {
                    key: (
                        round(enemy[key], 3)
                        if isinstance(enemy[key], float)
                        else enemy[key]
                    )
                    for key in (
                        "id",
                        "type",
                        "lane",
                        "x",
                        "hp",
                        "max_hp",
                        "shield",
                        "action",
                        "phase",
                        "rank",
                    )
                }
            )
            enemies[-1].update(
                slow=enemy["slow_power"],
                frozen=max(0, enemy["frozen_until"] - self.tick) / HZ,
                burn=max(0, enemy["burn_until"] - self.tick) / HZ,
                hidden=self._hidden(enemy),
                boss=bool(enemy["data"].get("boss")),
                invulnerable=enemy["invulnerable_until"] > self.tick,
                action_until=enemy["action_until"] / HZ,
                conductive=enemy["conductive"],
                plates=(
                    math.ceil(enemy["shield"] / enemy["data"].get("plate_hp", 180))
                    if enemy["type"] == "mountainlord"
                    else None
                ),
            )
        next_wave = None
        if self._spawn_index < len(self._spawn_queue):
            next_wave = max(0, self._spawn_queue[self._spawn_index][0] - self.tick) / HZ
        return {
            "stage": self.stage_id,
            "region": self.region,
            "time": round(self.time, 3),
            "tick": self.tick,
            "status": self.status,
            "paused": self.paused,
            "speed": self.speed,
            "qi": round(self.qi, 2),
            "revision": self.command_revision,
            "auto_ultimate": self.auto_ultimate,
            "music": {
                "theme": self.stage["music_theme"],
                "intensity": ("setup", "pressure", "onslaught")[self._music_level],
                "crowd": sum(e["type"] != "altar" for e in self.enemies.values()),
            },
            "final_assault": {
                "count": self.stage["final_assault_count"],
                "incoming": max(0, round(self._waves[-1]["at"] - self.time, 1)),
                "active": self._wave_index == len(self._waves),
            },
            "qi_cap": self._qi_cap(),
            "ritual_cd": round(max(0, self.ritual_until - self.tick) / HZ, 2),
            "encounter": self._encounter(),
            "nodes": copy.deepcopy(self.nodes),
            "gate": self.gate,
            "kills": self.kills,
            "wave": self._wave_index,
            "wave_count": len(self._waves),
            "next_wave": None if next_wave is None else round(next_wave, 2),
            "seed": self.seed,
            "heroes": heroes,
            "enemies": enemies,
            "columns": 12,
            "deployment_columns": list(range(1, 10)),
            "defenses": [
                {k: v for k, v in ward.items() if k != "hit"} for ward in self.defenses
            ],
            "projectiles": [
                {
                    key: round(value, 3) if isinstance(value, float) else value
                    for key, value in projectile.items()
                    if key not in ("hit",)
                }
                for projectile in self.projectiles.values()
            ],
            "effects": [
                {
                    "id": e["id"],
                    "kind": e["kind"],
                    "x": e["x"],
                    "lane": e["lane"],
                    "text": e["text"],
                    "ttl": round((e["until"] - self.tick) / HZ, 3),
                    "age": round((self.tick - e["born"]) / HZ, 3),
                }
                for e in self.effects
            ],
            "orbs": [
                {
                    "id": orb["id"],
                    "x": orb["x"],
                    "lane": orb["lane"],
                    "value": orb["value"],
                    "age": round((self.tick - orb["born"]) / HZ, 3),
                }
                for orb in self.orbs.values()
            ],
            "cards": {
                key: round(max(0, until - self.tick) / HZ, 2)
                for key, until in self.cards.items()
            },
            "events": list(self.events),
            "hazard": self._hazard(),
            "telegraphs": [
                {
                    "id": tell["id"],
                    "kind": tell["kind"],
                    "lanes": tell["lanes"],
                    "x": tell.get("x"),
                    "ttl": round((tell["until"] - self.tick) / HZ, 3),
                }
                for tell in self.telegraphs
            ],
            "relics_used": sorted(self._rel_used),
            "rewards": copy.deepcopy(self._rewards),
            "metrics": copy.deepcopy(self.metrics),
        }
