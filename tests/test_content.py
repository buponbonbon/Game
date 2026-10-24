"""Validate authored campaign relationships before a player can encounter them."""
import unittest

from game.content import ENEMIES, HEROES, REGIONS, RELICS, STAGES, catalog


class ContentTests(unittest.TestCase):
    def test_campaign_chain_visits_every_stage_once(self):
        current = min(STAGES.values(), key=lambda stage: stage["index"])["id"]
        seen = []
        while current is not None:
            self.assertNotIn(current, seen, "Campaign progression contains a cycle")
            self.assertIn(current, STAGES)
            seen.append(current)
            current = STAGES[current]["next"]
        self.assertEqual(set(seen), set(STAGES))
        self.assertEqual([STAGES[id]["index"] for id in seen], list(range(9)))

    def test_regions_have_three_stages_and_a_final_boss(self):
        for region in REGIONS:
            stages = sorted((stage for stage in STAGES.values() if stage["region"] == region["id"]), key=lambda stage: stage["index"])
            self.assertEqual([stage["number"] for stage in stages], [1, 2, 3])
            self.assertTrue(all(stage["chapter"] == region["chapter"] for stage in stages))
            self.assertIsNone(stages[0]["boss"])
            self.assertIsNone(stages[1]["boss"])
            self.assertTrue(ENEMIES[stages[2]["boss"]]["boss"])

    def test_wave_scripts_are_ordered_and_reference_legal_spawns(self):
        for stage in STAGES.values():
            with self.subTest(stage=stage["id"]):
                previous_at = -1
                bosses = []
                self.assertGreater(len(stage["waves"]), 0)
                for wave in stage["waves"]:
                    self.assertGreater(wave["at"], previous_at)
                    previous_at = wave["at"]
                    self.assertGreater(len(wave["spawns"]), 0)
                    for spawn in wave["spawns"]:
                        self.assertIn(spawn["type"], ENEMIES)
                        self.assertIn(spawn["lane"], range(5))
                        self.assertIsInstance(spawn["count"], int)
                        self.assertGreaterEqual(spawn["count"], 1)
                        self.assertGreaterEqual(spawn["gap"], 0)
                        if ENEMIES[spawn["type"]]["boss"]:
                            bosses.extend([spawn["type"]] * spawn["count"])
                self.assertLess(stage["waves"][-1]["at"], stage["duration"])
                self.assertEqual(bosses, [stage["boss"]] if stage["boss"] else [])

    def test_all_unlocks_are_reachable_and_rewarded(self):
        for hero in HEROES.values():
            unlock = hero["unlock"]
            if unlock == "start":
                continue
            self.assertIn(unlock, STAGES)
            self.assertIn(hero["id"], STAGES[unlock]["reward"]["unlocks"])
            self.assertLess(STAGES[unlock]["index"], len(STAGES) - 1)
        for relic in RELICS.values():
            self.assertIn(relic["unlock"], STAGES)
            self.assertEqual(STAGES[relic["unlock"]]["reward"]["relic"], relic["id"])
        for stage in STAGES.values():
            reward = stage["reward"]
            self.assertGreater(reward["stones"], 0)
            self.assertGreater(reward["insight"], 0)
            if "relic" in reward:
                self.assertIn(reward["relic"], RELICS)
            for hero in reward.get("unlocks", []):
                self.assertIn(hero, HEROES)

    def test_tutorial_has_budget_for_new_lanes_before_their_first_spawn(self):
        """One gatherer plus one sword must finance each additional taught lane."""
        stage = STAGES["wharf-1"]
        gatherer, sword = HEROES["gatherer"], HEROES["sword"]
        income = 150 - gatherer["cost"]
        known_lanes = set()
        spent = 0
        for wave in stage["waves"]:
            available = income + int(wave["at"] // gatherer["orb_interval"]) * gatherer["orb_value"] + int(wave["at"] // 12) * catalog()["rules"]["passive_qi"] - int(wave["at"] // 24)
            for spawn in wave["spawns"]:
                lane = spawn["lane"]
                if lane not in known_lanes:
                    known_lanes.add(lane)
                    spent += sword["cost"]
                    self.assertGreaterEqual(available, spent, f"Cannot finance lane {lane + 1} by {wave['at']}s")
        self.assertLessEqual(len(known_lanes), 3, "Tutorial introduces too many lanes before economy is learned")

    def test_hero_branches_and_defenses_are_well_formed(self):
        self.assertEqual(len(HEROES), 8)
        for hero in HEROES.values():
            self.assertGreater(hero["hp"], 0)
            self.assertGreater(hero["cost"], 0)
            self.assertGreater(hero["cooldown"], 0)
            self.assertEqual(set(hero["branches"]), {"A", "B"})
            for branch in hero["branches"].values():
                self.assertGreater(branch["cost"], 0)
                self.assertTrue(branch["stats"])
        for enemy in ENEMIES.values():
            self.assertGreater(enemy["hp"], 0)
            self.assertGreater(enemy["speed"], 0)
            self.assertGreaterEqual(enemy["armor"], 0)
            for resistance in enemy["resistances"].values():
                self.assertGreaterEqual(resistance, -.5)
                self.assertLessEqual(resistance, .8)

    def test_catalog_returns_detached_data(self):
        first = catalog()
        first["heroes"][0]["cost"] = -1
        first["stages"][0]["reward"]["stones"] = -1
        self.assertGreater(catalog()["heroes"][0]["cost"], 0)
        self.assertGreater(catalog()["stages"][0]["reward"]["stones"], 0)


if __name__ == "__main__":
    unittest.main()
