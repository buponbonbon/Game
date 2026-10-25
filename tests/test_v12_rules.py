"""Version 1.2 contracts: real resource costs, geometry and regional counterplay."""

import copy
import json
import math
from pathlib import Path
import unittest

from game.content import HEROES, STAGES, ENEMIES
from game.design import geometry
from game.engine import Battle, HZ, ticks
from game.rules import hero_data, validate_upgrades

ASSETS = Path(__file__).resolve().parents[1] / "web" / "assets"


class ExpandedRulesTests(unittest.TestCase):
    def place(self, battle, kind="sword", lane=2, col=2):
        battle.qi = 320
        battle.cards[kind] = 0
        result = battle.command(dict(action="place", hero=kind, lane=lane, col=col))
        self.assertTrue(result["ok"], result)
        return list(battle.heroes.values())[-1]

    def test_each_tree_has_two_paths_and_four_distinct_specials(self):
        for id, h in HEROES.items():
            with self.subTest(hero=id):
                special = []
                for path in ("A", "B"):
                    self.assertEqual(
                        [n["rank"] for n in h["talents"][path]], list(range(1, 6))
                    )
                    self.assertEqual(
                        [n["cost"] for n in h["talents"][path]], [20, 30, 45, 60, 90]
                    )
                    special += [
                        n["name"] for n in h["talents"][path] if n["kind"] == "special"
                    ]
                self.assertEqual(len(set(special)), 4)

    def test_talent_milestones_change_effective_stats_without_mutating_catalog(self):
        before = copy.deepcopy(HEROES)
        base = hero_data("gatherer")
        rank2 = hero_data("gatherer", dict(branch="A", rank=2))
        rank3 = hero_data("gatherer", dict(branch="A", rank=3))
        rank5 = hero_data("gatherer", dict(branch="A", rank=5))
        self.assertGreater(rank2["hp"], base["hp"])
        self.assertEqual(rank2["orb_interval"], 10)
        self.assertEqual(rank3["orb_interval"], 8)
        self.assertEqual(rank5["shared_breath"], 4)
        self.assertEqual(HEROES, before)
        self.assertGreater(
            hero_data("sword", dict(branch="B", rank=4))["mana_regen"],
            HEROES["sword"]["mana_regen"],
        )

        self.assertAlmostEqual(
            hero_data("sword", {"branch": "B", "rank": 4})["skill"]["cooldown"],
            HEROES["sword"]["skill"]["cooldown"] * 0.92,
        )
        self.assertAlmostEqual(
            hero_data("formation", {"branch": "B", "rank": 4})["skill"]["cooldown"],
            11 * 0.92,
        )

    def test_legacy_branches_keep_their_effect_and_can_advance_to_new_nodes(self):
        old = hero_data("sword", "A")
        self.assertEqual(old["damage"], 32)
        self.assertEqual(old["pierce"], 2)
        self.assertEqual(old["talent_rank"], 3)
        self.assertGreater(
            hero_data("sword", dict(branch="A", rank=4))["hp"], old["hp"]
        )

    def test_invalid_paths_cannot_reach_combat(self):
        for value in (
            None,
            [],
            {"unknown": "A"},
            {"sword": "C"},
            {"sword": {"branch": "A", "rank": True}},
            {"sword": {"branch": "B", "rank": 6}},
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_upgrades(value)
        self.assertEqual(
            validate_upgrades({"sword": {"branch": "B", "rank": 5}})["sword"]["rank"], 5
        )

    def test_circle_geometry_uses_exact_centers_and_self_exclusion(self):
        for radius, count in ((1.5, 9), (2, 13), (2.5, 21), (3, 29)):
            g = geometry("circle", radius, 99)
            self.assertEqual(len(g["offsets"]), count)
            self.assertTrue(all(math.hypot(x, y) <= radius for x, y in g["offsets"]))
        healer = hero_data("herbalist")["basic"]["geometry"]
        self.assertNotIn([0, 0], healer["offsets"])
        self.assertEqual(len(healer["offsets"]), 28)

    def test_all_heroes_expose_costs_and_authoritative_scaling(self):
        for id in HEROES:
            h = hero_data(id)
            self.assertGreaterEqual(h["mana_max"], h["mana_initial"])
            self.assertGreater(h["mana_regen"], 0)
            for ability in ("basic", "skill", "ultimate"):
                self.assertIn("geometry", h[ability])
                self.assertIn("scaling", h[ability])
                self.assertIn("mana_cost", h[ability])
            self.assertGreater(h["ultimate"]["mana_cost"], h["skill"]["mana_cost"])
            self.assertGreater(h["ultimate"]["qi_cost"], 0)
            self.assertGreater(h["ultimate"]["cooldown"], 0)

    def test_ultimate_rejections_are_atomic_then_exactly_spend_all_resources(self):
        b = Battle("wharf-1")
        h = self.place(b)
        h["resonance"] = 100
        h["mana"] = 64
        b.qi = 200
        for mana, qi, ready in ((64, 200, 0), (90, 19, 0), (90, 200, 100)):
            h["mana"] = mana
            b.qi = qi
            h["ultimate_ready"] = ready
            before = (
                h["mana"],
                b.qi,
                h["resonance"],
                h["ultimate_ready"],
                len(b.pending),
            )
            self.assertFalse(b.command(dict(action="ultimate", unit=h["id"]))["ok"])
            self.assertEqual(
                before,
                (h["mana"], b.qi, h["resonance"], h["ultimate_ready"], len(b.pending)),
            )
        h["mana"] = 90
        b.qi = 200
        h["ultimate_ready"] = 0
        self.assertTrue(b.command(dict(action="ultimate", unit=h["id"]))["ok"])
        self.assertEqual((h["mana"], b.qi, h["resonance"]), (25, 180, 0))
        self.assertEqual(h["ultimate_ready"], ticks(35))
        self.assertEqual(h["action"], "ultimate")

    def test_autoskill_reserves_mana_when_disabled_and_spends_only_on_cast(self):
        b = Battle("wharf-1")
        h = self.place(b)
        b.tick = ticks(10)
        h["mana"] = 50
        h["next_skill"] = 0
        h["next_attack"] = ticks(100)
        b._hero_tick(h)
        self.assertGreater(h["mana"], 50)  # no eligible enemy, no cost
        b._spawn("tide", 2, 5)
        b.command(dict(action="auto_skill", unit=h["id"], enabled=False))
        before = h["mana"]
        b._hero_tick(h)
        self.assertGreater(h["mana"], before)
        b.command(dict(action="auto_skill", unit=h["id"], enabled=True))
        before = h["mana"]
        b._hero_tick(h)
        self.assertAlmostEqual(h["mana"], before + 3 / HZ - 16)
        self.assertGreater(h["next_skill"], b.tick)

    def test_three_gatherers_have_diminishing_values_and_fourth_is_rejected(self):
        b = Battle("wharf-1")
        heroes = [self.place(b, "gatherer", lane, 1) for lane in (0, 2, 4)]
        b.tick = ticks(10)
        for h in heroes:
            b._hero_tick(h)
        self.assertEqual([o["value"] for o in b.orbs.values()], [20, 16, 12])
        b.qi = 320
        b.cards["gatherer"] = 0
        self.assertFalse(
            b.command(dict(action="place", hero="gatherer", lane=1, col=1))["ok"]
        )
        self.assertEqual(b.qi, 320)

    def test_qi_cannot_overflow_and_treasury_disappears_with_its_owner(self):
        b = Battle("wharf-1", upgrades={"gatherer": {"branch": "B", "rank": 5}})
        h = self.place(b, "gatherer", 0, 1)
        self.assertEqual(b._qi_cap(), 360)
        b._add_qi(10000, "fixture")
        self.assertEqual(b.qi, 360)
        b.heroes.pop(h["id"])
        b.advance(1 / HZ)
        self.assertEqual(b.qi, 320)
        b._add_qi(10000, "fixture")
        self.assertEqual(b.qi, 320)

    def test_pause_freezes_mana_and_cooldowns_but_allows_auto_preference(self):
        b = Battle("wharf-1")
        h = self.place(b)
        b.command(dict(action="pause", paused=True))
        self.assertTrue(
            b.command(dict(action="auto_skill", unit=h["id"], enabled=False))["ok"]
        )
        before = b.snapshot()
        b.advance(30)
        self.assertEqual(before, b.snapshot())
        self.assertFalse(b.command(dict(action="ritual"))["ok"])

    def test_regional_mana_modifiers_match_live_snapshot(self):
        b = Battle("terrace-1", realm=1)
        h = self.place(b, col=2)
        self.assertAlmostEqual(b.snapshot()["heroes"][0]["mana_regen"], 3.6)
        for n in b.nodes:
            n["corrupted"] = True
        self.assertAlmostEqual(b.snapshot()["heroes"][0]["mana_regen"], 3)
        b = Battle("tomb-1", realm=2)
        lane = b.stage["mist_lanes"][0]
        h = self.place(b, lane=lane)
        b.tick = ticks(19)
        self.assertAlmostEqual(b.snapshot()["heroes"][0]["mana_regen"], 2.1)

    def test_ritual_is_paid_once_then_cools_down_and_calms_real_tide(self):
        b = Battle("wharf-2")
        b.tick = ticks(30)
        self.assertEqual(b._hazard()["phase"], "HIGH TIDE")
        before = b.qi
        self.assertTrue(b.command(dict(action="ritual"))["ok"])
        self.assertEqual(b.qi, before - 35)
        self.assertEqual(b._hazard()["phase"], "CALM")
        self.assertTrue(
            any(t["col"] == 5 and t["blocked"] for t in b._hazard()["tiles"])
        )
        self.assertFalse(any(t["type"] == "water" for t in b._hazard()["tiles"]))
        self.assertEqual(b.snapshot()["ritual_cd"], 30)
        self.assertFalse(b.command(dict(action="ritual"))["ok"])
        self.assertEqual(b.qi, before - 35)

    def test_drainer_corrupts_node_and_neighbor_purifies_it(self):
        b = Battle("terrace-1", realm=1)
        node = b.nodes[0]
        e = b._spawn("drainer", node["lane"], node["col"] + 0.5)
        for second in (1, 2):
            b.tick = ticks(second)
            b._mechanic_tick()
        self.assertTrue(node["corrupted"])
        b.enemies.pop(e["id"])
        h = self.place(b, lane=node["lane"], col=node["col"])
        for second in (3, 4, 5):
            b.tick = ticks(second)
            b._mechanic_tick()
        self.assertFalse(node["corrupted"])
        node["corrupted"] = True
        h["mana"] = 10
        b.command(dict(action="ritual"))
        self.assertFalse(node["corrupted"])
        self.assertEqual(h["mana"], 25)

    def test_stage_hp_grows_five_percent_and_elites_arrive_after_setup(self):
        for index, (id, s) in enumerate(STAGES.items()):
            self.assertAlmostEqual(s["hp_multiplier"], 1.05**index, places=4)
            self.assertEqual(
                [p["id"] for p in s["phases"]], ["setup", "pressure", "onslaught"]
            )
            ranks = {p: 0 for p in ("setup", "pressure", "onslaught")}
            for wave in s["waves"]:
                ranks[wave["phase"]] += sum(
                    x.get("elite_count", 0) for x in wave["spawns"]
                )
            self.assertEqual(ranks["setup"], 0)
            self.assertGreater(ranks["onslaught"], ranks["pressure"])
        b = Battle("wharf-2")
        normal = b._spawn("tide", 1)
        elite = b._spawn("tide", 1, rank="elite")
        self.assertGreater(elite["max_hp"], normal["max_hp"])
        self.assertEqual(elite["data"]["armor"], normal["data"]["armor"] + 2)

    def test_fractional_scaled_boss_hp_cannot_softlock_at_phase_boundary(self):
        for stage, enemy in (
            ("wharf-3", "riverlord"),
            ("terrace-3", "mountainlord"),
            ("tomb-3", "boneemperor"),
        ):
            b = Battle(stage, realm=2)
            boss = b._spawn(enemy, 2)
            boss["shield"] = 0
            boss["data"]["plate_hp"] = 0
            b._hurt_enemy(boss, 100000, "True")
            self.assertEqual(boss["phase"], 2)
            self.assertEqual(boss["hp"], math.ceil(boss["max_hp"] * 0.7))
            b.tick += ticks(2)
            b._hurt_enemy(boss, 100000, "True")
            self.assertEqual(boss["phase"], 3)

    def test_crosswind_cannot_hit_enemies_outside_its_documented_3_5_tiles(self):
        b = Battle("wharf-1")
        h = self.place(b)
        near = b._spawn("tide", 2, 5)
        far = b._spawn("tide", 2, 7)
        b._skill(h)
        self.assertLess(near["hp"], near["max_hp"])
        self.assertEqual(far["hp"], far["max_hp"])

    def test_staff_arc_is_circular_and_lightning_chains_cross_adjacent_lanes(self):
        b = Battle("terrace-1", realm=2, upgrades={"monk": {"branch": "B", "rank": 5}})
        h = self.place(b, "monk")
        near = b._spawn("tide", 1, 3)
        far = b._spawn("tide", 0, 3)
        b._skill(h)
        self.assertLess(near["hp"], near["max_hp"])
        self.assertEqual(far["hp"], far["max_hp"])
        h = self.place(b, "lightning", lane=4)
        primary = b._spawn("tide", 4, 5)
        adjacent = b._spawn("tide", 3, 5)
        b._skill(h)
        self.assertLess(adjacent["hp"], adjacent["max_hp"])

    def test_monster_abilities_have_exact_geometry_and_bosses_warn_multiple_lanes(self):
        for e in ENEMIES.values():
            self.assertIn("basic_geometry", e)
            for ability in e["abilities"]:
                self.assertIn("geometry", ability)
            if e["boss"]:
                self.assertEqual(e["abilities"][0]["geometry"]["shape"], "lanes")

    def test_marked_ultimates_resolve_safely_if_caster_dies_during_windup(self):
        for kind in ("fire", "lightning"):
            with self.subTest(hero=kind):
                b = Battle("terrace-1", realm=2)
                h = self.place(b, kind)
                e = b._spawn("rottenwood", 2, 5)
                b._ultimate(h)
                b.heroes.pop(h["id"])
                b.advance(1.2)
                self.assertLess(e["hp"], e["max_hp"])
                self.assertEqual(b.status, "playing")

    def test_purifying_leaves_cleanses_two_distinct_debuffs(self):
        b = Battle(
            "terrace-1", realm=2, upgrades={"herbalist": {"branch": "B", "rank": 3}}
        )
        target = self.place(b)
        target.update(
            hp=100, curse=2, curse_until=600, spore_until=600, disabled_until=600
        )
        h = self.place(b, "herbalist", lane=1)
        self.assertTrue(b._skill(h))
        self.assertEqual(
            (target["curse"], target["curse_until"], target["spore_until"]), (0, 0, 0)
        )
        self.assertEqual(target["disabled_until"], 600)
        self.assertGreater(target["hp"], 100)

    def test_bundled_english_dialogue_and_progressive_local_music_are_complete(self):
        voice = json.loads((ASSETS / "audio/voices/voices.json").read_text())
        self.assertEqual(voice["language"], "en")
        self.assertEqual(set(voice["characters"]), set(HEROES))
        for id, lines in voice["characters"].items():
            self.assertEqual(set(lines), {"summon", "ultimate"})
            for kind, line in lines.items():
                self.assertEqual(line["text"], HEROES[id]["voice"][kind])
                self.assertGreater(line["duration"], 0.5)
                self.assertGreater(
                    (ASSETS / "audio/voices" / line["file"]).stat().st_size, 1000
                )
        tracks = json.loads((ASSETS / "audio/music/music.json").read_text())["tracks"]
        self.assertEqual(len(tracks), 28)
        for region in (stage.replace("-", "_") for stage in STAGES):
            tempos = [
                tracks[region + "_" + phase]["bpm"]
                for phase in ("setup", "pressure", "onslaught")
            ]
            self.assertEqual(tempos, sorted(set(tempos)))
        for track in tracks.values():
            self.assertGreater(track["duration"], 20)
            for format in ("ogg", "mp3"):
                self.assertGreater(
                    (ASSETS / "audio/music" / track[format]).stat().st_size, 10000
                )


if __name__ == "__main__":
    unittest.main()
