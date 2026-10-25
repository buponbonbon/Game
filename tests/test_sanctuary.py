"""Hub save migration, cosmetic-only actions and navigable facility coverage."""

import copy
import hashlib
import json
from collections import deque
from pathlib import Path
import unittest
from game import estate
from game.content import catalog
from game.sanctuary import SANCTUARY, FACILITIES, walkable, normalize_hub

ROOT = Path(__file__).resolve().parents[1]


class SanctuaryTests(unittest.TestCase):
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

    def test_migration_and_cosmetic_actions_preserve_progress_inventory_and_talents(
        self,
    ):
        p = self.profile()
        before = copy.deepcopy(p)
        for f in FACILITIES:
            p = estate.act(p, "hub_visit", facility=f["id"])["profile"]
        p = estate.act(p, "hub_avatar", avatar="gatherer")["profile"]
        for k in ("completed", "stones", "insight", "upgrades", "save_id"):
            self.assertEqual(p[k], before[k])
        self.assertEqual(p["estate"]["bag"], before["estate"]["bag"])
        self.assertEqual(len(p["estate"]["hub"]["visited"]), 8)
        self.assertEqual(p["estate"]["hub"]["avatar"], "gatherer")
        length = len(p["estate"]["journal"])
        p = estate.act(p, "hub_visit", facility="campaign")["profile"]
        self.assertEqual(len(p["estate"]["journal"]), length)
        self.assertEqual(estate.normalize_profile(p), p)

    def test_locked_avatars_and_unknown_destinations_are_atomic(self):
        p = self.profile()
        before = copy.deepcopy(p)
        for action, data in [
            ("hub_avatar", dict(avatar="herbalist")),
            ("hub_visit", dict(facility="unknown")),
            ("hub_track", dict(id="unknown")),
        ]:
            with self.assertRaises(estate.EconomyError):
                estate.act(p, action, **data)
            self.assertEqual(p, before)
        p["completed"] = ["wharf-1", "wharf-2", "wharf-3"]
        p = estate.act(p, "hub_avatar", avatar="herbalist")["profile"]
        self.assertEqual(p["estate"]["hub"]["avatar"], "herbalist")

    def test_invalid_positions_and_imported_locked_avatar_recover_to_spawn(self):
        for x, y in [
            (256, 150),
            (0, 0),
            (float("nan"), 232),
            (True, 232),
            (10000, 232),
            (170, 140),
        ]:
            h = normalize_hub(
                dict(
                    x=x,
                    y=y,
                    avatar="herbalist",
                    visited=["campaign", "campaign", "bad"],
                )
            )
            self.assertEqual((h["x"], h["y"]), (256, 232))
            self.assertEqual(h["avatar"], "sword")
            self.assertEqual(h["visited"], ["campaign"])
        h = normalize_hub(dict(x=252, y=228, avatar="gatherer"))
        self.assertEqual((h["x"], h["y"]), (252, 228))

    def test_commission_tracking_claim_and_rotation_do_not_duplicate_rewards(self):
        p = self.profile()
        q = p["estate"]["contracts"]["entries"][0]
        qid = q["id"]
        p = estate.act(p, "hub_track", id=qid)["profile"]
        self.assertEqual(p["estate"]["hub"]["tracked"], qid)
        p = estate.act(p, "hub_track", id=None)["profile"]
        self.assertIsNone(p["estate"]["hub"]["tracked"])
        p = estate.act(p, "hub_track", id=qid)["profile"]
        q = p["estate"]["contracts"]["entries"][0]
        q["progress"] = 999
        p = estate.act(p, "contract_claim", id=qid)["profile"]
        self.assertIsNone(p["estate"]["hub"]["tracked"])
        with self.assertRaises(estate.EconomyError):
            estate.act(p, "contract_claim", id=qid)
        for q in p["estate"]["contracts"]["entries"]:
            q.update(progress=999, claimed=True)
        p["estate"]["hub"].update(tracked=qid, tracked_cycle=0)
        p = estate.act(p, "contracts_rotate")["profile"]
        self.assertIsNone(p["estate"]["hub"]["tracked"])

    def test_all_destinations_have_connected_collision_safe_approaches(self):
        nodes = {
            (x, y) for y in range(4, 288, 8) for x in range(4, 512, 8) if walkable(x, y)
        }
        start = min(nodes, key=lambda p: (p[0] - 256) ** 2 + (p[1] - 232) ** 2)
        reached = {start}
        queue = deque([start])
        while queue:
            x, y = queue.popleft()
            for dx, dy in [(8, 0), (-8, 0), (0, 8), (0, -8)]:
                p = (x + dx, y + dy)
                if p in nodes and p not in reached and walkable(x + dx / 2, y + dy / 2):
                    reached.add(p)
                    queue.append(p)
        for f in FACILITIES:
            self.assertTrue(
                any((x - f["x"]) ** 2 + (y - f["y"]) ** 2 < 18**2 for x, y in reached),
                f["id"],
            )
        self.assertFalse(walkable(256, 150))
        self.assertFalse(walkable(170, 140))
        self.assertEqual(catalog()["hub"]["facilities"], FACILITIES)

    def test_authored_sources_and_frame_bounds_are_intact(self):
        folder = ROOT / "web/assets/hub"
        atlas = json.loads((folder / "atlas.json").read_text())
        for name, source in atlas["sources"].items():
            data = (folder / (name + ".png")).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), source["sha256"])
            self.assertGreaterEqual(source["width"], 1500)
        for id, meta in atlas["avatars"].items():
            self.assertEqual(set(meta["states"]), {"north", "south", "east", "west"})
            for frames in meta["states"].values():
                self.assertEqual(len(frames), 4)
                self.assertEqual(len({(f["x"], f["y"]) for f in frames}), 4)
                for f in frames:
                    self.assertGreater(f["w"], 0)
                    self.assertGreater(f["h"], 0)
                    self.assertLessEqual(f["x"] + f["w"], meta["width"])
                    self.assertLessEqual(f["y"] + f["h"], meta["height"])
