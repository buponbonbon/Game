"""Combat tests exercise the authoritative Python rules, without a browser."""
import copy
import math
import unittest

from game.content import HEROES
from game.engine import Battle, HZ, damage_amount


class CombatTests(unittest.TestCase):
    def place(self, battle, hero="sword", lane=2, col=2):
        result = battle.command({"action": "place", "hero": hero, "lane": lane, "col": col})
        self.assertTrue(result["ok"], result)
        return next(h for h in reversed(list(battle.heroes.values())) if h["type"] == hero)

    def test_placement_spends_exact_cost_and_starts_only_its_card_cooldown(self):
        battle = Battle("wharf-1")
        self.place(battle)
        self.assertEqual(battle.qi, 150 - HEROES["sword"]["cost"])
        self.assertEqual(battle.cards["sword"], round(HEROES["sword"]["cooldown"] * HZ))
        self.assertEqual(battle.cards["gatherer"], 0)

    def test_invalid_placement_cannot_spend_qi_or_reset_card(self):
        battle = Battle("wharf-1")
        self.place(battle)
        before = (battle.qi, copy.deepcopy(battle.cards), len(battle.heroes))
        result = battle.command({"action": "place", "hero": "gatherer", "lane": 2, "col": 2})
        self.assertFalse(result["ok"])
        self.assertIn("occupied", result["message"])
        self.assertEqual(before, (battle.qi, battle.cards, len(battle.heroes)))
        for lane, col in [(-1, 2), (5, 2), (2, 0), (2, 7), (True, 2), (2.5, 2)]:
            self.assertFalse(battle.command({"action": "place", "hero": "gatherer", "lane": lane, "col": col})["ok"])

    def test_insufficient_qi_and_locked_heroes_are_rejected(self):
        battle = Battle("wharf-1")
        self.place(battle, "fire")
        self.assertFalse(battle.command({"action": "place", "hero": "sword", "lane": 1, "col": 2})["ok"])
        self.assertFalse(battle.command({"action": "place", "hero": "lightning", "lane": 1, "col": 2})["ok"])
        self.assertEqual(battle.qi, 25)

    def test_pause_freezes_wave_projectile_and_resource_clocks(self):
        battle = Battle("wharf-1")
        self.place(battle, "gatherer")
        battle.advance(7.9)
        battle.command({"action": "pause", "paused": True})
        before = battle.snapshot()
        battle.advance(90)
        self.assertEqual(before, battle.snapshot())
        battle.command({"action": "pause", "paused": False})
        battle.advance(.2)
        self.assertEqual(len(battle.enemies), 1)
        self.assertEqual(len(battle.orbs), 1)

    def test_fixed_step_results_do_not_depend_on_request_chunk_size(self):
        first, second = Battle("wharf-1", 417), Battle("wharf-1", 417)
        for battle in (first, second):
            self.place(battle, "gatherer", col=1)
            self.place(battle, "sword")
        first.advance(18)
        for _ in range(180):
            second.advance(.1)
        self.assertEqual(first.snapshot(), second.snapshot())

    def test_projectile_travels_before_applying_damage(self):
        battle = Battle("wharf-1")
        self.place(battle)
        enemy = battle._spawn("tide", 2, 5.5)
        battle.advance(.85)
        self.assertEqual(enemy["hp"], enemy["max_hp"])
        self.assertGreater(len(battle.projectiles), 0)
        battle.advance(1)
        self.assertLess(enemy["hp"], enemy["max_hp"])
        self.assertGreater(battle.metrics["damage"]["sword"], 0)

    def test_damage_formula_resistance_clamps_zero_and_true_damage(self):
        self.assertEqual(damage_amount(0, 100), 0)
        self.assertEqual(damage_amount(50, 10, .2), 32)
        self.assertEqual(damage_amount(50, 999), 1)
        self.assertEqual(damage_amount(50, 999, .8, True), 50)
        self.assertEqual(damage_amount(100, 0, 8), 20)
        battle = Battle("wharf-1")
        enemy = battle._spawn("tide", 2)
        self.assertEqual(battle._hurt_enemy(enemy, 20, "ice"), 22)

    def test_gatherer_produces_finite_qi_and_he_cannot_attack(self):
        battle = Battle("wharf-1")
        self.place(battle, "gatherer", lane=0, col=1)
        battle.advance(9.3)
        self.assertEqual(battle.qi, 125)
        self.assertEqual(battle.metrics["qi"]["gatherer"], 25)
        self.assertEqual(battle.metrics["damage"], {})

    def test_branch_modifies_only_selected_branch(self):
        battle = Battle("wharf-1", upgrades={"gatherer": "A"})
        gatherer = self.place(battle, "gatherer")
        self.assertEqual(gatherer["data"]["orb_interval"], 6.5)
        self.assertEqual(gatherer["data"]["orb_value"], 25)
        self.assertEqual(HEROES["gatherer"]["orb_interval"], 8)

    def test_ultimate_spends_charge_and_cannot_self_fund(self):
        battle = Battle("wharf-1")
        hero = self.place(battle)
        self.assertFalse(battle.command({"action": "ultimate", "unit": hero["id"]})["ok"])
        hero["resonance"] = 100
        enemy = battle._spawn("hound", 2, 5)
        battle.command({"action": "ultimate", "unit": hero["id"]})
        self.assertEqual(hero["resonance"], 0)
        battle.advance(.4)
        self.assertLess(enemy["shield"], 260)
        self.assertEqual(hero["resonance"], 0)

    def test_boss_cannot_skip_mandatory_phases_even_with_lethal_hit(self):
        battle = Battle("wharf-3")
        boss = battle._spawn("riverlord", 2)
        battle._hurt_enemy(boss, 100000, "True")
        self.assertEqual(boss["phase"], 2)
        self.assertEqual(boss["hp"], math.ceil(boss["max_hp"] * .7))
        battle._hurt_enemy(boss, 100000, "True")
        self.assertEqual(boss["phase"], 2)
        battle.advance(1.4)
        battle._hurt_enemy(boss, 100000, "True")
        self.assertEqual(boss["phase"], 3)
        battle.advance(1.4)
        battle._hurt_enemy(boss, 100000, "True")
        self.assertNotIn(boss["id"], battle.enemies)

    def test_mountain_plate_break_does_not_spill_into_next_plate_or_body(self):
        battle = Battle("terrace-3", realm=1)
        boss = battle._spawn("mountainlord", 2)
        hp = boss["hp"]
        battle._hurt_enemy(boss, 10000, "Sword")
        self.assertEqual(boss["shield"], 360)
        self.assertEqual(boss["hp"], hp)
        self.assertEqual(boss["data"]["armor"], 10)
        self.assertEqual(battle.metrics["plates_broken"], 1)

    def test_repeated_freeze_has_diminishing_returns_and_boss_remains_mobile(self):
        battle = Battle("wharf-1")
        enemy = battle._spawn("tide", 2)
        durations = []
        for _ in range(5):
            enemy["frozen_until"] = 0
            battle._stun(enemy, 1)
            durations.append(enemy["frozen_until"] - battle.tick)
        self.assertEqual(durations, [60, 45, 30, 15, 0])
        boss = battle._spawn("riverlord", 2)
        battle._stun(boss, 10)
        self.assertEqual(boss["frozen_until"], 0)
        self.assertGreater(boss["slow_power"], 0)

    def test_ferry_bridge_opens_from_authored_stage_time(self):
        battle = Battle("wharf-2")
        result = battle.command({"action": "place", "hero": "sword", "lane": 2, "col": 5})
        self.assertFalse(result["ok"])
        battle.tick = 42 * HZ
        result = battle.command({"action": "place", "hero": "sword", "lane": 2, "col": 5})
        self.assertTrue(result["ok"], result)

    def test_stage_nodes_and_water_lanes_match_authored_content(self):
        battle = Battle("wharf-1")
        battle.tick = 30 * HZ
        self.assertEqual({tile["lane"] for tile in battle._hazard()["tiles"]}, {1, 3})
        battle = Battle("terrace-1", realm=1)
        self.assertEqual(len(battle._hazard()["tiles"]), 3)
        hero = self.place(battle, col=2)
        self.assertGreater(battle._buffs(hero)[0], 1)

    def test_altars_control_resurrection_and_are_targetable(self):
        battle = Battle("tomb-3", realm=2)
        self.assertEqual(len([e for e in battle.enemies.values() if e["type"] == "altar"]), 3)
        soul = battle._spawn("soul", 1, 7)
        battle._hurt_enemy(soul, 1000, "True")
        self.assertTrue(any(p[2] == "resurrect" for p in battle.pending))
        for altar in list(battle.enemies.values()):
            if altar["type"] == "altar":
                battle._hurt_enemy(altar, 1000, "True")
        battle.advance(6.1)
        self.assertFalse(any(e["type"] == "soul" for e in battle.enemies.values()))
        self.assertEqual(battle.metrics["altars_destroyed"], 3)

    def test_relics_are_one_use_and_match_catalog_effects(self):
        battle = Battle("tomb-1", realm=3)
        hero = self.place(battle)
        hero["curse"] = 2
        result = battle.command({"action": "relic", "id": "tide_pearl"})
        self.assertTrue(result["ok"])
        self.assertEqual(hero["shield"], 120)
        self.assertEqual(hero["shield_until"] - battle.tick, 5 * HZ)
        self.assertFalse(battle.command({"action": "relic", "id": "tide_pearl"})["ok"])
        battle.command({"action": "relic", "id": "wind_compass"})
        self.assertEqual(hero["resonance"], 35)
        self.assertGreater(battle._buffs(hero)[0], 1)
        battle.command({"action": "relic", "id": "soul_bell"})
        self.assertEqual(hero["curse"], 0)
        self.assertGreater(battle._reveal_until, battle.tick)

    def test_first_stage_is_winnable_with_legal_economy_and_three_lanes(self):
        battle = Battle("wharf-1", seed=47)
        self.place(battle, "gatherer", col=1)
        self.place(battle)
        battle.advance(12)
        self.place(battle, lane=1)
        battle.advance(13.2)
        self.place(battle, lane=3)
        battle.advance(60)
        self.assertEqual(battle.status, "victory")
        self.assertEqual(battle.gate, 3)
        self.assertEqual(battle.kills, 7)
        self.assertGreater(battle.snapshot()["rewards"]["stones"], 0)

    def test_terminal_rewards_cannot_repeat_and_terminal_clock_stops(self):
        battle = Battle("wharf-1")
        battle._spawn_queue = []
        battle.advance(1 / HZ)
        self.assertEqual(battle.status, "victory")
        before = battle.snapshot()
        battle.advance(100)
        self.assertEqual(before, battle.snapshot())
        self.assertFalse(battle.command({"action": "place", "hero": "sword", "lane": 2, "col": 2})["ok"])

    def test_invalid_time_cannot_poison_simulation(self):
        battle = Battle("wharf-1")
        for dt in (-1, float("nan"), float("inf"), "1"):
            with self.assertRaises(ValueError):
                battle.advance(dt)
        self.assertEqual(battle.tick, 0)

    def test_malformed_commands_fail_without_exception_or_spending(self):
        battle = Battle("wharf-1")
        commands = [None, [], {"action": "place", "hero": []},
                    {"action": "place", "hero": {}}, {"action": "ultimate", "unit": {}},
                    {"action": "collect", "orb": float("inf")}, {"action": "speed", "value": "fast"}]
        for command in commands:
            self.assertFalse(battle.command(command)["ok"])
        self.assertEqual(battle.qi, 150)
        self.assertEqual(battle.heroes, {})

    def test_fire_area_branch_and_lightning_armor_branch_are_functional(self):
        battle = Battle("wharf-1", upgrades={"fire": "B"})
        hero = self.place(battle, "fire")
        target = battle._spawn("tide", 2, 5)
        battle._resolve("hero_attack", {"hero": hero["id"], "target": target["id"]})
        projectile = next(iter(battle.projectiles.values()))
        self.assertEqual(projectile["radius"], .75)
        self.assertEqual(projectile["splash_factor"], .70)
        battle = Battle("terrace-1", realm=2, upgrades={"lightning": "B"})
        hero = self.place(battle, "lightning")
        target = battle._spawn("hound", 2, 5)
        target["conductive"] = 3
        battle._resolve("hero_attack", {"hero": hero["id"], "target": target["id"]})
        self.assertEqual(target["armor_break"], 5)
        self.assertEqual(target["conductive"], 1)

    def test_healing_caps_and_formation_branch_grants_real_resonance(self):
        battle = Battle("tomb-1", realm=2, upgrades={"formation": "B"})
        battle.qi = 999
        sword = self.place(battle, "sword", col=2)
        formation = self.place(battle, "formation", col=1)
        sword["hp"] = sword["max_hp"] - 10
        battle._heal(sword, 120)
        self.assertEqual(sword["hp"], sword["max_hp"])
        self.assertEqual(battle.metrics["healing"], 10)
        self.assertTrue(battle._skill(formation))
        self.assertEqual(sword["resonance"], 25)
        self.assertEqual(formation["data"]["circuit_cooldown"], 11)

    def test_gate_never_goes_negative_and_defeat_stops_simulation(self):
        battle = Battle("wharf-3")
        battle.gate = 1
        battle._spawn("riverlord", 2, .5001)
        battle._spawn("tide", 1, .5001)
        battle.advance(1 / HZ)
        self.assertEqual(battle.gate, 0)
        self.assertEqual(battle.status, "defeat")
        self.assertEqual(battle.metrics["breaches"], 1)
        tick = battle.tick
        battle.advance(10)
        self.assertEqual(battle.tick, tick)


if __name__ == "__main__":
    unittest.main()
