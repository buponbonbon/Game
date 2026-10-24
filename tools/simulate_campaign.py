#!/usr/bin/env python3
"""Replay the verified nine-stage policy using legal player commands only.

This is one reproducible authored-wave policy, not a statistical balance study.
Run from any directory: python /path/to/Game/tools/simulate_campaign.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from game.content import HEROES, STAGES
from game.engine import Battle


def play_stage(stage_id, seed, upgrades, realm):
    """Build economy, cover incoming lanes, then add fire and use charged arts."""
    content = STAGES[stage_id]
    battle = Battle(stage_id, seed=seed, upgrades=dict(upgrades), realm=realm)
    actions = []

    def place(kind, lane, col):
        result = battle.command({"action": "place", "hero": kind, "lane": lane, "col": col})
        if result["ok"]:
            actions.append({"time": round(battle.time, 3), "hero": kind, "lane": lane, "col": col})
        return result["ok"]

    place("gatherer", 2, 1)
    place("sword", 2, 2)
    for _ in range(2_500):
        state = battle.snapshot()
        elapsed, heroes, enemies = state["time"], state["heroes"], state["enemies"]
        occupied = {(hero["lane"], hero["col"]) for hero in heroes}
        defended = {hero["lane"] for hero in heroes if hero["type"] in ("sword", "fire", "frost", "lightning")}
        gatherers = sum(hero["type"] == "gatherer" for hero in heroes)
        if gatherers < 2 and elapsed < 24 and state["qi"] >= 50 and state["cards"]["gatherer"] <= 0:
            for lane in (1, 3, 2, 0, 4):
                if (lane, 1) not in occupied and place("gatherer", lane, 1):
                    break
        else:
            upcoming = {lane: 999 for lane in range(5)}
            for wave in content["waves"]:
                for spawn in wave["spawns"]:
                    if wave["at"] >= elapsed:
                        upcoming[spawn["lane"]] = min(upcoming[spawn["lane"]], wave["at"] - elapsed)
            for enemy in enemies:
                upcoming[enemy["lane"]] = min(upcoming[enemy["lane"]], -20 + enemy["x"])
            needed = [lane for lane in sorted(upcoming, key=upcoming.get) if lane not in defended and upcoming[lane] < 22]
            if needed and state["qi"] >= 75 and state["cards"]["sword"] <= 0:
                for col in (2, 3, 4):
                    if (needed[0], col) not in occupied and place("sword", needed[0], col):
                        break
            elif not needed:
                pressure = {lane: sum(enemy["hp"] for enemy in enemies if enemy["lane"] == lane) for lane in range(5)}
                for lane in sorted(pressure, key=lambda value: (-pressure[value], abs(value - 2))):
                    if pressure[lane] <= 0:
                        continue
                    types = {hero["type"] for hero in heroes if hero["lane"] == lane}
                    kind = "fire" if "fire" not in types else "sword"
                    if state["qi"] >= HEROES[kind]["cost"] and state["cards"][kind] <= 0:
                        for col in (3, 4, 5, 2):
                            if (lane, col) not in occupied and place(kind, lane, col):
                                break
                        break
        for hero in heroes:
            if hero["resonance"] >= 100 and any(enemy["lane"] == hero["lane"] for enemy in enemies):
                battle.command({"action": "ultimate", "unit": hero["id"]})
        battle.advance(0.2)
        if battle.status != "playing":
            break
    state = battle.snapshot()
    return {
        "stage": stage_id, "seed": seed, "realm": realm,
        "policy": "two gatherers, cover authored threats, fire reinforcement, charged ultimates",
        "upgrades_at_start": dict(upgrades), "status": state["status"],
        "duration": state["time"], "gate": state["gate"], "kills": state["kills"],
        "qi_remaining": state["qi"], "metrics": state["metrics"],
        "rewards": state["rewards"], "placements": actions,
    }


def play_final_stage(seed, upgrades, realm):
    """Counter the Emperor with economy, cleanse, formation, lightning and a tank.

    Unlike the earlier encounters, adding only sword/fire damage is insufficient
    against sustained royal decrees. All deployments still wait for actual Qi and
    card cooldowns. The supplied branch upgrades were paid for in earlier stages.
    """
    battle = Battle("tomb-3", seed=seed, upgrades=dict(upgrades), realm=realm)
    plan = [
        (0, "gatherer", 2, 1), (0, "sword", 2, 2),
        (8, "gatherer", 0, 1), (16, "gatherer", 4, 1),
        (18, "sword", 1, 2), (28, "sword", 3, 2),
        (34, "fire", 1, 3), (42, "lightning", 2, 4),
        (50, "herbalist", 3, 3), (58, "formation", 2, 3),
        (66, "monk", 2, 6), (75, "fire", 2, 5), (80, "fire", 4, 3),
    ]
    placements, ultimate_casts = [], []
    for _ in range(2_000):
        state = battle.snapshot()
        elapsed, heroes, enemies = state["time"], state["heroes"], state["enemies"]
        occupied = {(hero["lane"], hero["col"]) for hero in heroes}

        def place(kind, lane, col):
            result = battle.command({"action": "place", "hero": kind, "lane": lane, "col": col})
            if result["ok"]:
                placements.append({"time": elapsed, "hero": kind, "lane": lane, "col": col})
            return result["ok"]

        if plan and plan[0][0] <= elapsed:
            _, kind, lane, col = plan[0]
            if (lane, col) in occupied:
                plan.pop(0)
            elif state["qi"] >= HEROES[kind]["cost"] and state["cards"][kind] <= 0:
                if place(kind, lane, col):
                    plan.pop(0)
        elif not plan:
            # Replace fallen core defenders before adding another damage unit.
            for kind, lane, col in (
                ("herbalist", 3, 3), ("monk", 2, 6), ("lightning", 2, 4),
                ("formation", 2, 3), ("fire", 2, 5), ("fire", 4, 3),
                ("sword", 1, 2), ("sword", 3, 2),
                ("gatherer", 0, 1), ("gatherer", 4, 1),
            ):
                if (lane, col) not in occupied and state["qi"] >= HEROES[kind]["cost"] and state["cards"][kind] <= 0:
                    if place(kind, lane, col):
                        break

        for hero in heroes:
            if hero["resonance"] < 100:
                continue
            kind = hero["type"]
            cast = (
                (kind == "gatherer" and state["qi"] < 900)
                or (kind == "herbalist" and any(ally["hp"] < ally["max_hp"] * 0.8 for ally in heroes))
                or (kind == "formation" and len(heroes) >= 4)
                or any(enemy["lane"] == hero["lane"] for enemy in enemies)
            )
            if cast and battle.command({"action": "ultimate", "unit": hero["id"]})["ok"]:
                ultimate_casts.append({"time": elapsed, "hero": kind, "unit": hero["id"]})
        if state.get("telegraphs") and "tide_pearl" not in state["relics_used"] and any(hero["hp"] < hero["max_hp"] * 0.7 for hero in heroes):
            battle.command({"action": "relic", "id": "tide_pearl"})
        if any(enemy.get("boss") and enemy["phase"] >= 2 for enemy in enemies) and "wind_compass" not in state["relics_used"]:
            battle.command({"action": "relic", "id": "wind_compass"})
        battle.advance(0.2)
        if battle.status != "playing":
            break

    state = battle.snapshot()
    return {
        "stage": "tomb-3", "seed": seed, "realm": realm,
        "policy": "three gatherers; lightning, healer and formation core; frontline monk; role-aware arts and warning-timed relics",
        "upgrades_at_start": dict(upgrades), "status": state["status"],
        "duration": state["time"], "gate": state["gate"], "kills": state["kills"],
        "qi_remaining": state["qi"], "metrics": state["metrics"],
        "rewards": state["rewards"], "placements": placements,
        "ultimate_casts": ultimate_casts, "relics_used": state["relics_used"],
    }


def simulate_campaign(seed=4701):
    upgrades, completed, stages = {}, [], []
    stones = 0
    for stage_id in STAGES:
        realm = 3 if "tomb-3" in completed else 2 if "terrace-3" in completed else 1 if "wharf-3" in completed else 0
        result = play_final_stage(seed, upgrades, realm) if stage_id == "tomb-3" else play_stage(stage_id, seed, upgrades, realm)
        result["stones_before"] = stones
        result["branches_purchased"] = []
        stages.append(result)
        if result["status"] != "victory":
            result["stones_after"] = stones
            break
        completed.append(stage_id)
        stones += result["rewards"]["stones"]
        for hero, branch in (("gatherer", "A"), ("sword", "B"), ("fire", "B"), ("monk", "A"), ("frost", "A"), ("lightning", "B")):
            cost = HEROES[hero]["branches"][branch]["cost"]
            if hero not in upgrades and stones >= cost:
                upgrades[hero] = branch
                stones -= cost
                result["branches_purchased"].append({"hero": hero, "branch": branch, "cost": cost})
                break
        result["stones_after"] = stones
    return {
        "policy": "economy and lane coverage, with a mixed support/defense formation for the final boss",
        "scope": "One seeded legal-play smoke run; not statistical balance validation.",
        "seed": seed, "passed": len(completed) == len(STAGES),
        "completed": completed, "stones_remaining": stones,
        "stages": stages,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=4701, help="Battle seed (default: 4701).")
    parser.add_argument("--output", type=Path, help="Also write the JSON report to this file.")
    args = parser.parse_args(argv)
    report = simulate_campaign(args.seed)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
