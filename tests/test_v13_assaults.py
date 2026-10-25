"""Player-visible 1.3 behavior: auto casts, coordinated assaults and reactive music."""

import json
from pathlib import Path
import unittest
from game.content import HEROES, STAGES
from game.engine import Battle, HZ, ticks

ASSETS = Path(__file__).resolve().parents[1] / "web/assets"


class AssaultAndAutomationTests(unittest.TestCase):
    def place(self, b, kind="sword", lane=2, col=2):
        b.qi = 320
        b.cards[kind] = 0
        self.assertTrue(
            b.command(dict(action="place", hero=kind, lane=lane, col=col))["ok"]
        )
        return list(b.heroes.values())[-1]

    def charge(self, h):
        h["resonance"] = 100
        h["mana"] = h["data"]["mana_max"]
        h["next_attack"] = ticks(1000)
        h["next_skill"] = ticks(1000)

    def test_auto_attack_waits_for_range_and_pays_normal_costs(self):
        b = Battle("wharf-1")
        h = self.place(b)
        self.charge(h)
        e = b._spawn("rottenwood", 1, 11.8)
        b.command(dict(action="auto_ultimate", enabled=True))
        b.advance(1 / HZ)
        self.assertEqual(h["resonance"], 100)
        e["lane"] = 2
        b.qi = 90
        before = h["mana"]
        b.advance(1 / HZ)
        self.assertEqual(h["resonance"], 0)
        self.assertEqual(b.qi, 70)
        self.assertAlmostEqual(h["mana"], before - 65 + 3 / HZ)
        self.assertGreater(h["ultimate_ready"], b.tick)
        self.assertEqual(sum(e["kind"] == "ultimate" for e in b.events), 1)

    def test_auto_off_and_insufficient_resources_do_not_spend_charge(self):
        b = Battle("wharf-1")
        h = self.place(b)
        self.charge(h)
        b._spawn("tide", 2, 5)
        b.advance(1 / HZ)
        self.assertEqual(h["resonance"], 100)
        b.command(dict(action="auto_ultimate", enabled=True))
        b.qi = 19
        b.advance(0.3)
        self.assertEqual(h["resonance"], 100)
        self.assertEqual(b.qi, 19)
        b.qi = 100
        h["mana"] = 0
        b.advance(0.3)
        self.assertEqual(h["resonance"], 100)
        self.assertEqual(b.metrics["invalid"], 0)

    def test_auto_healer_waits_for_an_injured_ally_then_heals(self):
        b = Battle("terrace-1", realm=2)
        ally = self.place(b)
        h = self.place(b, "herbalist", 1)
        self.charge(h)
        b.command(dict(action="auto_ultimate", enabled=True))
        b.advance(1 / HZ)
        self.assertEqual(h["resonance"], 100)
        ally["hp"] = 100
        b.advance(1 / HZ)
        self.assertEqual(h["resonance"], 0)
        self.assertEqual(ally["hp"], 220)
        self.assertEqual(ally["shield"], 65)

    def test_auto_formation_requires_nearby_allies_and_a_real_threat(self):
        b = Battle("terrace-1", realm=2)
        h = self.place(b, "formation")
        self.charge(h)
        b.command(dict(action="auto_ultimate", enabled=True))
        b.advance(1 / HZ)
        self.assertEqual(h["resonance"], 100)
        ally = self.place(b, col=3)
        b.advance(1 / HZ)
        self.assertEqual(h["resonance"], 100)
        b._spawn("tide", 4, 8)
        b.advance(1 / HZ)
        self.assertEqual(h["resonance"], 0)
        self.assertGreater(h["array_until"], b.tick)
        self.assertGreater(b._buffs(ally)[1], 1)

    def test_auto_economy_does_not_burn_an_ultimate_at_full_qi(self):
        b = Battle("wharf-1")
        h = self.place(b, "gatherer")
        self.charge(h)
        b.qi = 320
        b.command(dict(action="auto_ultimate", enabled=True))
        b.advance(1 / HZ)
        self.assertEqual(h["resonance"], 100)
        b.qi = 200
        b.advance(1 / HZ)
        self.assertEqual(h["resonance"], 0)
        self.assertEqual(b.qi, 175)
        self.assertEqual(sum(x[2] == "well" for x in b.pending), 4)

    def test_two_ready_units_cannot_bypass_shared_qi(self):
        b = Battle("wharf-1")
        units = [self.place(b, lane=i) for i in (1, 2)]
        for h in units:
            self.charge(h)
            b._spawn("rottenwood", h["lane"], 5)
        b.qi = 20
        b.command(dict(action="auto_ultimate", enabled=True))
        b.advance(0.5)
        self.assertEqual(sum(e["kind"] == "ultimate" for e in b.events), 1)
        self.assertEqual(b.qi, 0)
        self.assertEqual(sum(h["resonance"] == 100 for h in units), 1)

    def test_same_tick_command_snapshots_have_monotonic_revisions(self):
        b = Battle("wharf-1")
        before = b.snapshot()
        b.command(dict(action="pause", paused=True))
        paused = b.snapshot()
        b.command(dict(action="auto_ultimate", enabled=True))
        auto = b.snapshot()
        self.assertEqual(before["tick"], auto["tick"])
        self.assertLess(before["revision"], paused["revision"])
        self.assertLess(paused["revision"], auto["revision"])

    def test_paused_preference_does_not_cast_or_advance(self):
        b = Battle("wharf-1")
        h = self.place(b)
        self.charge(h)
        b._spawn("tide", 2, 5)
        b.command(dict(action="pause", paused=True))
        b.command(dict(action="auto_ultimate", enabled=True))
        before = b.snapshot()
        b.advance(90)
        self.assertEqual(before, b.snapshot())
        self.assertTrue(before["auto_ultimate"])
        self.assertFalse(b.command(dict(action="auto_ultimate", enabled="yes"))["ok"])

    def test_being_hit_does_not_erase_ultimate_or_skill_animation(self):
        b = Battle("wharf-1")
        h = self.place(b)
        b._ultimate(h)
        until = h["action_until"]
        started = h["action_started"]
        b._hurt_hero(h, 10)
        self.assertEqual(h["action"], "ultimate")
        self.assertEqual(h["action_until"], until)
        self.assertEqual(h["action_started"], started)
        h["action"] = "skill"
        h["action_until"] = b.tick + ticks(0.5)
        b._hurt_hero(h, 10)
        self.assertEqual(h["action"], "skill")

    def test_crowd_music_escalates_before_wave_phase_and_releases_slowly(self):
        b = Battle("wharf-1")
        for i in range(10):
            b._spawn("tide", i % 5)
        b._music_tick()
        self.assertEqual(b.snapshot()["music"]["intensity"], "onslaught")
        self.assertEqual(b._encounter()["id"], "setup")
        for e in list(b.enemies.values())[5:]:
            b.enemies.pop(e["id"])
        b.tick = ticks(2)
        b._music_tick()
        self.assertEqual(b.snapshot()["music"]["intensity"], "onslaught")
        b.tick = ticks(6) + 1
        b._music_tick()
        self.assertEqual(b.snapshot()["music"]["intensity"], "pressure")

    def test_every_final_wave_has_many_enemies_on_all_five_lanes(self):
        for id, s in STAGES.items():
            with self.subTest(stage=id):
                w = s["waves"][-1]
                counts = {lane: 0 for lane in range(5)}
                for spawn in w["spawns"]:
                    counts[spawn["lane"]] += spawn["count"]
                self.assertTrue(w["all_lanes"])
                self.assertGreaterEqual(min(counts.values()), 7)
                self.assertGreaterEqual(sum(counts.values()), 35)
                b = Battle(id, realm=2)
                b._spawn_queue = [
                    x for x in b._spawn_queue if x[1] == len(s["waves"]) - 1
                ]
                b.tick = ticks(w["at"]) - 1
                b.advance(0.8)
                self.assertEqual({e["lane"] for e in b.enemies.values()}, set(range(5)))
                b.advance(3.4)
                self.assertGreaterEqual(
                    len([e for e in b.enemies.values() if e["type"] != "altar"]), 35
                )

    def test_swarm_numbers_do_not_inherit_elite_stats(self):
        b = Battle("tomb-2", realm=2)
        normal = b._spawn("soul", 2)
        swarm = b._spawn("soul", 2, rank="swarm")
        elite = b._spawn("soul", 2, rank="elite")
        self.assertLess(swarm["max_hp"], normal["max_hp"])
        self.assertLess(swarm["data"]["damage"], normal["data"]["damage"])
        self.assertEqual(swarm["data"]["armor"], normal["data"]["armor"])
        self.assertGreater(elite["max_hp"], normal["max_hp"])

    def test_nine_individual_musical_identities_and_three_arrangements_each(self):
        tracks = json.loads((ASSETS / "audio/music/music.json").read_text())["tracks"]
        self.assertEqual(len(tracks), 28)
        melodies = []
        titles = []
        for stage in STAGES:
            key = stage.replace("-", "_")
            variants = [
                tracks[key + "_" + phase]
                for phase in ("setup", "pressure", "onslaught")
            ]
            melodies.append(tuple(variants[0]["melody"]))
            titles.append(variants[0]["title"])
            self.assertEqual([x["intensity"] for x in variants], [0, 1, 2])
            self.assertEqual(len(set(x["bpm"] for x in variants)), 3)
        self.assertEqual(len(set(melodies)), 9)
        self.assertEqual(len(set(titles)), 9)

    def test_voice_takes_include_deliberate_emotional_pacing_and_energy(self):
        voices = json.loads((ASSETS / "audio/voices/voices.json").read_text())[
            "characters"
        ]
        for hero, lines in voices.items():
            for line in lines.values():
                self.assertTrue(line["direction"])
                self.assertGreaterEqual(len(line["phrases"]), 2)
                self.assertGreater(len({p["pace"] for p in line["phrases"]}), 1)
                self.assertGreater(len({p["energy"] for p in line["phrases"]}), 1)


if __name__ == "__main__":
    unittest.main()
