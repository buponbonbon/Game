"""Economy migration, atomic purchases and battle-bound growth/rewards."""

import copy
import http.client
import json
import threading
import unittest
from game import estate
from game.content import HEROES, STAGES
from game.engine import Battle, ticks, HZ
from game.server import create_server


def profile(stones=500, insight=20):
    return estate.normalize_profile(
        dict(version=1, completed=[], stones=stones, insight=insight, upgrades={})
    )


def outcome(**overrides):
    return dict(
        dict(
            status="victory",
            stage="wharf-1",
            region="wharf",
            mode="campaign",
            time=180,
            gate=3,
            wave=12,
            wave_count=12,
            kills=20,
            metrics={
                "kills_by_type": {"tide": 20},
                "roles_used": ["Economy", "Damage", "Control"],
            },
        ),
        **overrides
    )


class EstateTests(unittest.TestCase):
    def action(self, p, action, **data):
        return estate.act(p, action, **data)["profile"]

    def test_v1_migration_preserves_wallet_talents_and_progress_and_grants_starter_once(
        self,
    ):
        raw = dict(
            version=1,
            completed=["wharf-1", "wharf-3"],
            stones=75,
            insight=4,
            upgrades={"sword": "A"},
            settings={"music": 0.3},
        )
        p = estate.normalize_profile(raw)
        self.assertEqual(p["version"], 2)
        self.assertEqual(p["stones"], 75)
        self.assertEqual(p["upgrades"], raw["upgrades"])
        self.assertEqual(p["completed"], raw["completed"])
        self.assertEqual(p["settings"], raw["settings"])
        p = self.action(p, "plant", plot=0, crop="qi_grass")
        self.assertEqual(p["estate"]["bag"]["seeds"]["qi_grass"], 2)
        reloaded = estate.normalize_profile(p)
        self.assertEqual(reloaded["estate"]["bag"]["seeds"]["qi_grass"], 2)
        self.assertEqual(reloaded["save_id"], p["save_id"])

    def test_failed_transaction_does_not_mutate_input(self):
        p = profile(0)
        before = copy.deepcopy(p)
        for action, data in [
            ("buy", dict(item="seed:soul_lingzhi", quantity=1)),
            ("expand", {}),
            ("craft", dict(recipe="spirit_tea")),
            ("harvest", dict(plot=0)),
        ]:
            with self.assertRaises(estate.EconomyError):
                estate.act(p, action, **data)
            self.assertEqual(p, before)

    def test_growth_once_per_outcome_not_by_visits_or_early_losses(self):
        p = self.action(profile(), "plant", plot=0, crop="river_lotus")
        for _ in range(3):
            p = self.action(p, "inspect")
        self.assertEqual(p["estate"]["garden"]["plots"][0]["growth"], 0)
        p = estate.settle(p, "loss-early", outcome(status="defeat", time=50, wave=6))[
            "profile"
        ]
        self.assertEqual(p["estate"]["garden"]["plots"][0]["growth"], 0)
        p = estate.settle(p, "loss-earned", outcome(status="defeat", time=80, wave=6))[
            "profile"
        ]
        self.assertEqual(p["estate"]["garden"]["plots"][0]["growth"], 1)
        twice = estate.settle(
            p, "loss-earned", outcome(status="defeat", time=80, wave=6)
        )
        self.assertTrue(twice["duplicate"])
        self.assertEqual(twice["profile"], p)
        p = estate.settle(p, "win", outcome())["profile"]
        self.assertEqual(p["estate"]["garden"]["plots"][0]["growth"], 2)

    def test_watering_fertilizer_and_research_yield_and_seed_return(self):
        p = profile()
        p = self.action(p, "crop_research", crop="river_lotus")
        p = self.action(p, "crop_research", crop="river_lotus")
        p = self.action(p, "plant", plot=0, crop="river_lotus")
        p = self.action(p, "water", plot=0)
        p = self.action(p, "fertilize", plot=0)
        p = estate.settle(p, "grow", outcome())["profile"]
        a = estate.view(p)["plots"][0]
        self.assertEqual(a["need"], 1)
        self.assertEqual(a["yield"], 6)
        p = self.action(p, "harvest", plot=0)
        self.assertEqual(p["estate"]["bag"]["produce"]["river_lotus"], 6)
        # Starting one seed was spent, a victory grants one, mastery returns one.
        self.assertEqual(p["estate"]["bag"]["seeds"]["river_lotus"], 2)

    def test_expand_locks_and_irrigation(self):
        p = profile()
        with self.assertRaises(estate.EconomyError):
            self.action(p, "plant", plot=3, crop="qi_grass")
        p = self.action(p, "expand")
        p = self.action(p, "expand")
        self.assertEqual(p["estate"]["garden"]["size"], 9)
        self.assertEqual(p["stones"], 320)
        p = self.action(p, "irrigation")
        p = self.action(p, "irrigation")
        p = self.action(p, "plant", plot=8, crop="qi_grass")
        self.assertTrue(p["estate"]["garden"]["plots"][8]["watered"])
        self.assertEqual(estate.view(p)["plots"][8]["yield"], 4)
        with self.assertRaises(estate.EconomyError):
            self.action(p, "expand")

    def test_trade_prices_do_not_form_buy_sell_profit_loop(self):
        from game.estate_content import CROPS

        for c in CROPS.values():
            self.assertLess(c["sell_price"], c["seed_price"])
        p = profile()
        p = self.action(p, "buy", item="seed:qi_grass", quantity=5)
        self.assertEqual(p["stones"], 490)
        for bad in (0, 100, True, 1.1):
            with self.assertRaises(estate.EconomyError):
                self.action(p, "buy", item="fertilizer", quantity=bad)

    def test_crafting_and_one_equipped_preparation(self):
        p = profile()
        p["estate"]["bag"]["produce"] = {
            "qi_grass": 6,
            "river_lotus": 2,
            "azure_bamboo": 2,
        }
        p = self.action(p, "craft", recipe="spirit_tea", quantity=2)
        self.assertEqual(p["stones"], 496)
        self.assertEqual(p["estate"]["bag"]["produce"]["qi_grass"], 0)
        p = self.action(p, "equip", item="spirit_tea")
        p2, item = estate.prepare(p)
        self.assertEqual(item, "spirit_tea")
        self.assertEqual(p2["estate"]["bag"]["pills"]["spirit_tea"], 1)
        self.assertEqual(p["estate"]["bag"]["pills"]["spirit_tea"], 2)
        with self.assertRaises(estate.EconomyError):
            self.action(p, "craft", recipe="purifying_dew")
        p = self.action(p, "learn_recipe", recipe="purifying_dew")
        p = self.action(p, "craft", recipe="purifying_dew")
        p = self.action(p, "equip", item="purifying_dew")
        self.assertEqual(p["estate"]["equipped"], "purifying_dew")

    def test_commissions_research_and_achievements_only_claim_once(self):
        p = profile()
        p = estate.settle(p, "one", outcome())["profile"]
        p = estate.settle(p, "two", outcome())["profile"]
        p = estate.settle(p, "three", outcome())["profile"]
        for c in list(p["estate"]["contracts"]["entries"]):
            p = self.action(p, "contract_claim", id=c["id"])
            with self.assertRaises(estate.EconomyError):
                self.action(p, "contract_claim", id=c["id"])
        p = self.action(p, "contracts_rotate")
        self.assertEqual(p["estate"]["contracts"]["cycle"], 1)
        p = self.action(p, "monster_claim", enemy="tide", tier=2)
        self.assertEqual(p["insight"], 22)
        with self.assertRaises(estate.EconomyError):
            self.action(p, "monster_claim", enemy="tide", tier=2)
        p = self.action(p, "achievement_claim", id="first_victory")
        with self.assertRaises(estate.EconomyError):
            self.action(p, "achievement_claim", id="first_victory")

    def test_talent_paths_respec_refunds_paid_nodes_and_legacy_cost(self):
        p = profile()
        p = self.action(p, "buy_talent", hero="sword", branch="A", rank=1)
        p = self.action(p, "buy_talent", hero="sword", branch="A", rank=2)
        self.assertEqual(p["stones"], 450)
        with self.assertRaises(estate.EconomyError):
            self.action(p, "buy_talent", hero="sword", branch="B", rank=3)
        p = self.action(p, "respec", hero="sword")
        self.assertEqual(p["stones"], 500)
        self.assertNotIn("sword", p["upgrades"])
        p["upgrades"]["sword"] = "A"
        p = self.action(p, "respec", hero="sword")
        self.assertEqual(p["stones"], 525)

    def test_legacy_advance_respec_does_not_refund_unpaid_nodes(self):
        p = profile()
        p["upgrades"]["sword"] = "A"
        p = self.action(p, "buy_talent", hero="sword", branch="A", rank=4)
        self.assertEqual(p["estate"]["talent_paid"]["sword"], 95)
        p = self.action(p, "respec", hero="sword")
        self.assertEqual(p["stones"], 535)

    def test_nursery_rewards_and_no_campaign_clear_or_stone_inflation(self):
        p = profile()
        p = estate.settle(
            p,
            "nursery",
            outcome(
                stage="garden-defense",
                mode="nursery",
                nursery_beds=[{"hp": 2}, {"hp": 1}, {"hp": 1}],
                gate=4,
            ),
        )["profile"]
        self.assertEqual(p["completed"], [])
        self.assertEqual(p["stones"], 500)
        self.assertEqual(p["estate"]["bag"]["seeds"]["soul_lingzhi"], 2)
        self.assertEqual(p["estate"]["stats"]["nursery_perfect"], 1)

    def test_existing_clears_count_for_first_victory_and_nursery_is_not_a_region_rite(
        self,
    ):
        p = estate.normalize_profile(
            dict(version=1, completed=["wharf-1"], upgrades={})
        )
        first = next(
            a for a in estate.view(p)["achievements"] if a["id"] == "first_victory"
        )
        self.assertEqual(first["progress"], 1)
        p = estate.settle(
            p,
            "shelter",
            outcome(
                mode="nursery",
                stage="garden-defense",
                nursery_beds=[{"hp": 2}] * 3,
                metrics={"rituals_used": 1},
            ),
        )["profile"]
        self.assertEqual(p["estate"]["stats"].get("ritual_regions", 0), 0)

    def test_normalizer_handles_malformed_optional_inventory(self):
        for broken in (
            {"garden": {"plots": [{"crop": []}]}},
            {"blueprints": [[]]},
            {"cosmetics": {"owned": None, "active": 4}},
            {"claimed_achievements": None},
            {"contracts": {"entries": [{"id": []}]}},
        ):
            p = estate.normalize_profile({"estate": broken})
            self.assertEqual(p["estate"]["garden"]["size"], 3)


class PreparationAndNurseryTests(unittest.TestCase):
    def place(self, b, lane=2, kind="sword", col=2):
        b.qi = 320
        b.cards[kind] = 0
        self.assertTrue(
            b.command(dict(action="place", hero=kind, lane=lane, col=col))["ok"]
        )
        return list(b.heroes.values())[-1]

    def test_tea_only_first_three_valid_summons(self):
        b = Battle("wharf-1")
        b.apply_preparation("spirit_tea")
        self.assertFalse(
            b.command(dict(action="place", hero="sword", lane=0, col=0))["ok"]
        )
        for i in range(4):
            h = self.place(b, lane=i)
            self.assertEqual(
                h["mana"], h["data"]["mana_initial"] + (10 if i < 3 else 0)
            )
        self.assertTrue(b.preparation["used"])
        self.assertEqual(len(b.metrics["roles_used"]), 1)
        with self.assertRaises(ValueError):
            b.apply_preparation("soul_ward")

    def test_dew_region_triggers_and_soul_ward_once(self):
        b = Battle("wharf-2")
        b.apply_preparation("purifying_dew")
        b.tick = ticks(28)
        b._preparation_tick()
        self.assertTrue(b.preparation["used"])
        self.assertEqual(b._hazard()["phase"], "CALM")
        self.assertEqual(b._calm_until - b.tick, ticks(8))
        b = Battle("terrace-1")
        b.apply_preparation("purifying_dew")
        h = self.place(b, lane=b.nodes[0]["lane"], col=b.nodes[0]["col"])
        h["mana"] = 0
        b.nodes[0]["corrupted"] = True
        b._preparation_tick()
        self.assertFalse(b.nodes[0]["corrupted"])
        self.assertEqual(h["mana"], 15)
        self.assertEqual(b.metrics["nodes_purified"], 1)
        b = Battle("tomb-1")
        b.apply_preparation("purifying_dew")
        h = self.place(b, lane=1)
        b.tick = ticks(19)
        b._preparation_tick()
        self.assertEqual(b._mana_regen(h), h["data"]["mana_regen"])
        b = Battle("tomb-1")
        b.apply_preparation("soul_ward")
        h = self.place(b)
        h["curse_until"] = ticks(8)
        b._preparation_tick()
        self.assertEqual(h["curse_until"], 0)
        self.assertTrue(b.preparation["used"])
        h["curse_until"] = ticks(8)
        b._preparation_tick()
        self.assertGreater(h["curse_until"], 0)

    def test_nursery_active_lanes_and_independent_bed_breaches(self):
        b = Battle("garden-defense")
        self.assertEqual(len(STAGES), 9)
        self.assertFalse(
            b.command(dict(action="place", hero="sword", lane=0, col=2))["ok"]
        )
        self.place(b)
        b.defenses[1]["status"] = "spent"
        for _ in range(3):
            e = b._spawn("tide", 1, 0.4)
            b._enemy_tick(e)
        self.assertEqual(b.nursery_beds[0]["hp"], 0)
        self.assertEqual(b.gate, 4)
        b.defenses[2]["status"] = "spent"
        b.defenses[3]["status"] = "spent"
        for lane in [2, 2, 3, 3]:
            b._enemy_tick(b._spawn("tide", lane, 0.4))
        b.advance(1 / HZ)
        self.assertEqual(b.status, "defeat")

    def test_nursery_shelter_is_a_paid_timed_shield(self):
        b = Battle("garden-defense")
        h = self.place(b)
        b.qi = 100
        self.assertTrue(b.command(dict(action="ritual"))["ok"])
        self.assertEqual(b.qi, 65)
        self.assertEqual(h["shield"], 35)
        self.assertEqual(h["shield_until"], ticks(6))
        self.assertFalse(b.command(dict(action="ritual"))["ok"])
        self.assertEqual(b.qi, 65)

    def test_kills_and_node_purification_metrics_are_real_events(self):
        b = Battle("terrace-1")
        e = b._spawn("tide", 2, 5)
        b._kill(e, None)
        b._kill(e, None)
        self.assertEqual(b.metrics["kills_by_type"], {"tide": 1})
        n = b.nodes[0]
        self.place(b, lane=n["lane"], col=n["col"])
        n["corrupted"] = True
        for i in range(1, 5):
            b.tick = ticks(i)
            b._mechanic_tick()
        self.assertEqual(b.metrics["nodes_purified"], 1)


class EconomyHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self, path, data):
        c = http.client.HTTPConnection("127.0.0.1", self.port)
        c.request("POST", path, json.dumps(data), {"Content-Type": "application/json"})
        r = c.getresponse()
        out = json.loads(r.read())
        c.close()
        return r.status, out

    def test_only_actual_finished_server_battle_can_award_and_lost_receipt_replays(
        self,
    ):
        p = profile()
        code, out = self.post(
            "/api/battle", dict(stage="wharf-1", profile=p, paused=True)
        )
        self.assertEqual(code, 201)
        bid = out["battle_id"]
        code, _ = self.post(
            "/api/estate",
            dict(action="claim_battle", profile=p, battle_id=bid, state=outcome()),
        )
        self.assertEqual(code, 400)
        record = self.server.store.get(bid)
        with record.lock:
            record.battle.status = "victory"
            record.battle._wave_index = 12
        code, first = self.post(
            "/api/estate", dict(action="claim_battle", profile=p, battle_id=bid)
        )
        self.assertEqual(code, 200)
        self.assertEqual(len(first["profile"]["completed"]), 1)
        self.assertEqual(
            first["outcome"]["stones"], STAGES["wharf-1"]["reward"]["stones"]
        )
        self.assertTrue(first["outcome"]["garden_grew"])
        _, retry = self.post(
            "/api/estate", dict(action="claim_battle", profile=p, battle_id=bid)
        )
        self.assertEqual(first, retry)
        new = self.action_buy(first["profile"])
        _, duplicate = self.post(
            "/api/estate", dict(action="claim_battle", profile=new, battle_id=bid)
        )
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(duplicate["profile"]["stones"], new["stones"])

    def action_buy(self, p):
        return self.post(
            "/api/estate", dict(action="buy", profile=p, item="fertilizer")
        )[1]["profile"]

    def test_failed_battle_creation_does_not_consume_client_inventory(self):
        p = profile()
        p["estate"]["bag"]["pills"]["spirit_tea"] = 1
        p["estate"]["equipped"] = "spirit_tea"
        before = copy.deepcopy(p)
        code, _ = self.post("/api/battle", dict(stage="missing", profile=p))
        self.assertEqual(code, 400)
        self.assertEqual(p, before)
        code, out = self.post(
            "/api/battle", dict(stage="garden-defense", profile=p, paused=True)
        )
        self.assertEqual(code, 201)
        self.assertEqual(out["profile"]["estate"]["bag"]["pills"]["spirit_tea"], 0)
        self.assertEqual(out["state"]["preparation"]["id"], "spirit_tea")
        self.assertIsNone(out["profile"]["estate"]["equipped"])


if __name__ == "__main__":
    unittest.main()
