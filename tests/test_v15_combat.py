"""Counterplay budgets, objective fairness, animation clocks and portable economy."""

import copy, json, unittest
from game.engine import Battle, HZ, STEP, ticks
from game.content import HEROES, ENEMIES, STAGES, TRIALS, catalog
from game import estate
from game.estate_content import FERTILIZER_PRICE


class SquadTests(unittest.TestCase):
    def setup_group(self):
        b = Battle("terrace-1")
        guard = b._spawn("hound", 2, 5, rank="elite")
        ally = b._spawn("tide", 2, 5.7, rank="elite")
        ally["data"]["armor"] = 0
        ally["data"]["resistances"] = {}
        ally["hp"] = ally["max_hp"] = 1000
        return b, guard, ally

    def test_guard_mitigation_capped_nonstacking_and_breakable(self):
        b, g, a = self.setup_group()
        self.assertEqual(b._hurt_enemy(a, 100, "Physical"), 97)
        second = b._spawn("drowned", 2, 5.4, rank="elite")
        self.assertEqual(b._hurt_enemy(a, 100, "Physical"), 97)
        self.assertEqual(b._hurt_enemy(a, 100, "True"), 100)
        b._stun(g, 2)
        b._stun(second, 2)
        self.assertEqual(b._hurt_enemy(a, 100, "Physical"), 100)

    def test_guard_only_covers_elites_in_exact_radius_and_never_bosses(self):
        b, g, a = self.setup_group()
        a["x"] = 6.26
        self.assertIsNone(b._squad_guard(a))
        a["x"] = 6.25
        self.assertEqual(b._squad_guard(a)["id"], g["id"])
        normal = b._spawn("tide", 2, 5.2)
        boss = b._spawn("mountainlord", 2, 5.2)
        self.assertIsNone(b._squad_guard(normal))
        self.assertIsNone(b._squad_guard(boss))
        self.assertIsNone(b._squad_guard(g))

    def mending(self):
        b = Battle("wharf-2")
        m = b._spawn("lantern", 2, 5, rank="elite")
        m["next_mend"] = 0
        a = b._spawn("tide", 2, 5.6, rank="elite")
        a["hp"] -= 40
        b._squad_tick()
        self.assertEqual(m["action"], "mend")
        token = m["squad_token"]
        return b, m, a, token

    def test_mend_has_windup_target_cap_and_resource_budget(self):
        b, m, a, token = self.mending()
        others = []
        for lane in (1, 3):
            e = b._spawn("tide", lane, 5.6, rank="elite")
            e["hp"] -= 40
            others.append(e)
        normal = b._spawn("tide", 2, 5.3)
        normal["hp"] -= 40
        before = normal["hp"]
        total = sum(e["hp"] for e in (a, *others))
        b.tick = HZ
        b._resolve("mend", dict(enemy=m["id"], token=token))
        gained = sum(e["hp"] for e in (a, *others)) - total
        self.assertGreater(gained, 0)
        self.assertLessEqual(gained, 32)
        self.assertEqual(normal["hp"], before)
        self.assertEqual(sum(e["max_hp"] - e["hp"] < 40 for e in (a, *others)), 2)
        self.assertEqual(m["next_mend"], ticks(8))

    def test_damage_or_freeze_interrupts_heal_and_dead_caster_cannot_resolve(self):
        for interrupt in ("hit", "freeze", "death"):
            b, m, a, token = self.mending()
            before = a["hp"]
            if interrupt == "hit":
                b._hurt_enemy(m, 1, "True")
            elif interrupt == "freeze":
                b._stun(m, 2)
            else:
                b._kill(m, None)
            b.tick = HZ
            b._resolve("mend", dict(enemy=m["id"], token=token))
            self.assertEqual(a["hp"], before, interrupt)

    def test_visual_recoil_does_not_add_a_movement_stun(self):
        b = Battle("wharf-1")
        e = b._spawn("tide", 2, 8)
        b.tick = 100
        b._hurt_enemy(e, 1, "True")
        x = e["x"]
        b._enemy_tick(e)
        self.assertLess(e["x"], x)
        self.assertEqual(e["action_until"], 0)
        self.assertEqual(e["hurt_at"], 100)

    def test_role_durability_pays_for_support_utility(self):
        b = Battle("wharf-1")
        normal = b._spawn("hound", 2)
        guard = b._spawn("hound", 2, rank="elite")
        self.assertLess(guard["max_hp"], round(normal["max_hp"] * 1.25))
        self.assertGreater(guard["max_hp"], normal["max_hp"])


class TrialAndMotionClockTests(unittest.TestCase):
    def fighter(self, b, lane=2, col=2):
        b.qi = 320
        b.cards["sword"] = 0
        self.assertTrue(
            b.command(dict(action="place", hero="sword", lane=lane, col=col))["ok"]
        )
        return list(b.heroes.values())[-1]

    def test_trials_are_separate_and_objective_rules_are_public(self):
        c = catalog()
        self.assertEqual(len(c["stages"]), 9)
        self.assertEqual(len(c["trials"]), 3)
        self.assertEqual(len(HEROES), 8)
        for id in TRIALS:
            self.assertEqual(Battle(id).snapshot()["mode"], "trial")

    def test_caravan_moves_with_fighter_and_does_not_progress_while_paused(self):
        b = Battle("trial-caravan")
        cart = b.objective["objects"][0]
        start = cart["x"]
        b._objective_tick()
        self.assertEqual(cart["x"], start)
        self.fighter(b)
        b._objective_tick()
        self.assertGreater(cart["x"], start)
        b.command(dict(action="pause", paused=True))
        before = b.snapshot()
        b.advance(10)
        self.assertEqual(b.snapshot(), before)

    def test_raider_damage_is_capped_guardable_and_frozen_raiders_do_not_damage(self):
        b = Battle("trial-caravan")
        cart = b.objective["objects"][0]
        enemies = [b._spawn("tide", 2, cart["x"] + 0.3) for _ in range(5)]
        b.tick = HZ
        b._objective_tick()
        self.assertEqual(cart["hp"], cart["max_hp"] - 24)
        self.fighter(b)
        b.tick = 2 * HZ
        before = cart["hp"]
        b._objective_tick()
        self.assertEqual(before - cart["hp"], 12)
        for e in enemies:
            b._stun(e, 3)
        b.tick += HZ
        before = cart["hp"]
        b._objective_tick()
        self.assertEqual(cart["hp"], before)

    def test_either_beacon_can_fail_without_damaging_other_beacon(self):
        b = Battle("trial-beacons")
        one, two = b.objective["objects"]
        one["hp"] = 1
        b._spawn("tide", one["lane"], one["x"])
        b.tick = HZ
        b._objective_tick()
        self.assertTrue(b.objective["failed"])
        self.assertEqual(two["hp"], two["max_hp"])
        self.assertEqual(b.gate, 0)

    def test_oath_seals_score_losses_without_an_abrupt_near_victory_failure(self):
        b = Battle("trial-oath")
        limit = b.stage["loss_limit"]
        b.metrics["deaths"] = limit
        b._objective_tick()
        self.assertFalse(b.objective["failed"])
        b.metrics["deaths"] = limit + 1
        b._objective_tick()
        self.assertFalse(b.objective["failed"])
        self.assertEqual(b.objective["remaining"], 0)

    def test_remains_are_bounded_simulation_clocked_and_do_not_count_as_living_enemies(
        self,
    ):
        b = Battle("wharf-1")
        e = b._spawn("tide", 2, 8)
        b._kill(e, None)
        self.assertNotIn(e["id"], b.enemies)
        self.assertEqual(b.snapshot()["remains"][0]["age"], 0)
        b.command(dict(action="pause", paused=True))
        before = b.snapshot()
        b.advance(5)
        self.assertEqual(b.snapshot(), before)
        b.command(dict(action="pause", paused=False))
        b.advance(1)
        self.assertFalse(b.snapshot()["remains"])

    def test_telegraph_exposes_actual_geometry_and_countdown(self):
        b = Battle("terrace-1")
        b._tell("SPORE CLOUD", [2], 1, x=5)
        b._tell("SHOULDER RUSH", [1], 1.1, x=6)
        b._tell("ROYAL DECREE", [0, 3], 1.8)
        rows = b.snapshot()["telegraphs"]
        self.assertEqual([r["shape"] for r in rows], ["circle", "segment", "lanes"])
        self.assertEqual(rows[0]["radius"], 1.2)
        self.assertEqual(rows[1]["radius"], 0.75)
        self.assertEqual(rows[2]["duration"], 1.8)

    def test_basic_enemy_attack_exposes_start_and_recovery(self):
        b = Battle("wharf-1")
        h = self.fighter(b)
        b.tick = 100
        e = b._spawn("tide", 2, h["x"] + 0.5)
        b._enemy_tick(e)
        enemy_id = e["id"]
        s = next(row for row in b.snapshot()["enemies"] if row["id"] == enemy_id)
        self.assertEqual(s["action"], "attack")
        self.assertEqual(s["action_started"], 100 / HZ)
        self.assertGreater(s["action_until"], s["action_started"])


class Economy15Tests(unittest.TestCase):
    def profile(self):
        return estate.normalize_profile(
            dict(version=2, completed=[], upgrades={}, stones=100, insight=0)
        )

    def test_journal_is_bounded_preserved_and_records_real_transaction_deltas(self):
        p = self.profile()
        p = estate.act(p, "buy", item="fertilizer")["profile"]
        row = p["estate"]["journal"][-1]
        self.assertEqual(row["stones"], -FERTILIZER_PRICE)
        self.assertEqual(p["stones"], 100 - FERTILIZER_PRICE)
        for _ in range(36):
            p = estate.act(p, "buy", item="seed:qi_grass")["profile"]
        p = estate.normalize_profile(p)
        self.assertEqual(len(p["estate"]["journal"]), 32)
        before = copy.deepcopy(p)
        with self.assertRaises(estate.EconomyError):
            estate.act(p, "buy", item="seed:soul_lingzhi", quantity=99)
        self.assertEqual(p, before)

    def test_tea_adds_limited_dao_without_waiving_ultimate_requirements(self):
        b = Battle("wharf-1")
        b.apply_preparation("spirit_tea")
        for lane in range(4):
            b.qi = 320
            b.cards["sword"] = 0
            b.command(dict(action="place", hero="sword", lane=lane, col=2))
        units = list(b.heroes.values())
        self.assertEqual([h["resonance"] for h in units], [20, 20, 20, 0])
        self.assertFalse(b.command(dict(action="ultimate", unit=units[0]["id"]))["ok"])
        self.assertEqual(b.metrics["preparation_dao"], 60)

    def test_trial_medals_do_not_unlock_campaign_and_reward_first_win_once(self):
        p = self.profile()
        b = Battle("trial-caravan")
        b.status = "victory"
        b.tick = ticks(200)
        b._wave_index = 6
        b.objective["objects"][0]["arrived"] = True
        first = estate.settle(p, "trial1", b.snapshot())
        p = first["profile"]
        self.assertEqual(p["completed"], [])
        self.assertEqual(first["outcome"]["medal"], 3)
        self.assertEqual(first["outcome"]["stones"], 20)
        second = estate.settle(p, "trial2", b.snapshot())
        self.assertEqual(second["outcome"]["stones"], 6)
        self.assertEqual(second["outcome"]["insight"], 0)
        duplicate = estate.settle(second["profile"], "trial2", b.snapshot())
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(
            duplicate["profile"]["estate"]["trial_wins"]["trial-caravan"], 2
        )

    def test_oath_silver_threshold_matches_the_published_medal_rule(self):
        p = self.profile()
        b = Battle("trial-oath")
        b.status = "victory"
        b.metrics["deaths"] = 3
        self.assertEqual(
            estate.settle(p, "oath-silver", b.snapshot())["outcome"]["medal"], 2
        )
        b.metrics["deaths"] = 4
        self.assertEqual(
            estate.settle(p, "oath-bronze", b.snapshot())["outcome"]["medal"], 1
        )

    def test_medal_never_downgrades_and_v2_fields_survive_migration(self):
        p = self.profile()
        p["estate"]["trial_medals"] = {"trial-beacons": 3}
        p["estate"]["trial_wins"] = {"trial-beacons": 1}
        p["settings"] = {"clarity": True, "damageText": "off"}
        result = estate.normalize_profile(p)
        self.assertEqual(result["estate"]["trial_medals"]["trial-beacons"], 3)
        self.assertEqual(result["settings"], p["settings"])
        self.assertEqual(result["estate"]["bag"]["seeds"], p["estate"]["bag"]["seeds"])

        battle = Battle("trial-beacons")
        battle.status = "victory"
        battle.metrics["deaths"] = 4
        run = estate.settle(p, "bronze-after-gold", battle.snapshot())
        self.assertEqual(run["profile"]["estate"]["trial_medals"]["trial-beacons"], 3)
        self.assertEqual(run["outcome"]["medal"], 1)


if __name__ == "__main__":
    unittest.main()
