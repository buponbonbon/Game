"""Narrative progression is bounded, portable and independent of battle rewards."""

import copy, hashlib, json, unittest
from pathlib import Path
from game import estate
from game.content import STAGES, catalog
from game.world_story import CHAPTERS, SIDE_NPCS, OBSERVATIONS, FAVORS, normalize_story

ROOT = Path(__file__).resolve().parents[1]


class WorldStoryTests(unittest.TestCase):
    def profile(self):
        return estate.normalize_profile(
            estate.normalize_profile(
                dict(
                    version=2,
                    completed=[],
                    stones=73,
                    insight=4,
                    upgrades={"sword": {"branch": "A", "rank": 1}},
                )
            )
        )

    def test_chapters_cover_existing_stages_with_distinct_motives_and_choices(self):
        self.assertEqual([c["id"] for c in CHAPTERS], list(STAGES))
        self.assertEqual(len(SIDE_NPCS), 6)
        self.assertEqual(len({c["title"] for c in CHAPTERS}), 9)
        for c in CHAPTERS:
            self.assertEqual(c["region"], STAGES[c["id"]]["region"])
            self.assertEqual(len(c["pages"]), 3)
            self.assertEqual(len(c["choices"]), 2)
            self.assertGreater(len(c["reason"]), 40)
            self.assertGreater(len(c["aftermath"]), 100)
        self.assertEqual(len(catalog()["stages"]), 9)
        self.assertEqual(len(catalog()["heroes"]), 8)

    def test_legacy_saves_add_empty_story_without_loss_or_second_starter_grant(self):
        p = self.profile()
        p["estate"].pop("story")
        p["estate"]["bag"]["seeds"]["qi_grass"] = 1
        q = estate.normalize_profile(p)
        self.assertEqual(q["stones"], 73)
        self.assertEqual(q["insight"], 4)
        self.assertEqual(q["upgrades"], p["upgrades"])
        self.assertEqual(q["estate"]["bag"], p["estate"]["bag"])
        self.assertEqual(q["estate"]["story"]["choices"], {})
        self.assertEqual(estate.normalize_profile(q), q)

    def test_reading_and_choices_cannot_complete_or_unlock_encounters_or_mint_currency(
        self,
    ):
        p = self.profile()
        before = copy.deepcopy(p)
        for c in CHAPTERS:
            if c["id"] != "wharf-1":
                p["completed"].append(CHAPTERS[CHAPTERS.index(c) - 1]["id"])
            progress = list(p["completed"])
            wallet = (p["stones"], p["insight"])
            inventory = copy.deepcopy(p["estate"]["bag"])
            p = estate.act(p, "story_seen", chapter=c["id"])["profile"]
            p = estate.act(
                p, "story_choice", chapter=c["id"], choice=c["choices"][0]["id"]
            )["profile"]
            self.assertEqual(p["completed"], progress)
            self.assertEqual((p["stones"], p["insight"]), wallet)
            self.assertEqual(p["estate"]["bag"], inventory)
        self.assertNotIn("tomb-3", p["completed"])
        self.assertEqual(p["upgrades"], before["upgrades"])

    def test_locked_chapter_and_invalid_choice_are_atomic(self):
        p = self.profile()
        before = copy.deepcopy(p)
        for action, data in [
            ("story_choice", dict(chapter="tomb-3", choice="council")),
            ("story_seen", dict(chapter="terrace-1")),
            ("story_choice", dict(chapter="wharf-1", choice="council")),
            ("story_observe", dict(id="unknown")),
            ("story_met", dict(npc=["mei"])),
        ]:
            with self.assertRaises(estate.EconomyError):
                estate.act(p, action, **data)
            self.assertEqual(p, before)

    def test_discoveries_and_people_are_unique_and_repeatable_without_rewards(self):
        p = self.profile()
        wallet = p["stones"]
        bag = copy.deepcopy(p["estate"]["bag"])
        for _ in range(3):
            for o in OBSERVATIONS:
                p = estate.act(p, "story_observe", id=o["id"])["profile"]
            for n in SIDE_NPCS:
                p = estate.act(p, "story_met", npc=n["id"])["profile"]
        self.assertEqual(len(p["estate"]["story"]["observations"]), 10)
        self.assertEqual(len(p["estate"]["story"]["met"]), 6)
        self.assertEqual(p["stones"], wallet)
        self.assertEqual(p["estate"]["bag"], bag)

    def test_favors_check_real_progress_and_cannot_be_claimed_twice(self):
        p = self.profile()
        for f in FAVORS:
            with self.assertRaises(estate.EconomyError):
                estate.act(p, "story_favor", id=f["id"])
        for o in OBSERVATIONS[:3]:
            p = estate.act(p, "story_observe", id=o["id"])["profile"]
        p = estate.act(p, "story_favor", id="courier")["profile"]
        self.assertIn("courier", p["estate"]["story"]["favors"])
        with self.assertRaises(estate.EconomyError):
            estate.act(p, "story_favor", id="courier")
        p["estate"]["stats"]["harvests"] = 1
        p = estate.act(p, "story_favor", id="gardener")["profile"]
        p["completed"] = ["wharf-3"]
        p = estate.act(p, "story_favor", id="river")["profile"]
        self.assertEqual(
            set(p["estate"]["story"]["favors"]), {"courier", "gardener", "river"}
        )
        self.assertEqual(p["stones"], 73)
        self.assertEqual(p["insight"], 4)

    def test_import_sanitization_bounds_story_records(self):
        s = normalize_story(
            dict(
                choices={"wharf-1": "families", "tomb-3": "hacked", "bad": "evil"},
                seen=["wharf-1"] * 1000 + ["bad"],
                observations=["grass"] * 1000 + ["bad"],
                met=["ren", {}],
                favors=["courier", "bad"],
            )
        )
        self.assertEqual(s["choices"], {"wharf-1": "families"})
        self.assertEqual(s["seen"], ["wharf-1"])
        self.assertEqual(s["observations"], ["grass"])
        self.assertEqual(s["met"], ["ren"])
        self.assertEqual(s["favors"], ["courier"])

    def test_exploration_pngs_and_registered_sequences_are_intact(self):
        folder = ROOT / "web/assets/exploration"
        art = json.loads((folder / "exploration.json").read_text())
        for name, s in art["sources"].items():
            self.assertEqual(
                hashlib.sha256((folder / (name + ".png")).read_bytes()).hexdigest(),
                s["sha256"],
            )
        self.assertEqual(len(art["npcs"]), 6)
        self.assertEqual(len(art["props"]), 12)
        for actor in art["actions"].values():
            self.assertEqual(
                set(actor["states"]), {"greet", "inspect", "water", "gather"}
            )
            for frames in actor["states"].values():
                self.assertEqual(len(frames), 4)
                for f in frames:
                    self.assertLessEqual(f["x"] + f["w"], actor["width"])
                    self.assertLessEqual(f["y"] + f["h"], actor["height"])
