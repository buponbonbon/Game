"""Retained actor poses/botany must be real, distinct transparent source cutouts."""

import hashlib
import json
from pathlib import Path
import unittest
from game.content import HEROES, ENEMIES
from tests.test_assets import decode_png

ROOT = Path(__file__).resolve().parents[1] / "web/assets"


class EstateArtTests(unittest.TestCase):
    def test_source_checksums_dimensions_and_cutout_bounds(self):
        manifest = json.loads((ROOT / "actors_manifest.json").read_text())["assets"]
        actors = json.loads((ROOT / "actors.json").read_text())
        crops = json.loads((ROOT / "crops.json").read_text())
        self.assertEqual(set(actors), set(HEROES) | set(ENEMIES) | {"altar"})
        decoded = {}
        for name, meta in manifest.items():
            p = ROOT / (name + ".png")
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), meta["sha256"])
            w, h, rows = decode_png(p)
            self.assertEqual((w, h), (meta["width"], meta["height"]))
            self.assertGreater(w, 1000)
            self.assertGreater(h, 900)
            decoded[name] = (w, h, rows)
        hashes = []
        for actor, states in actors.items():
            expected = (
                {"idle", "attack", "skill", "ultimate"}
                if actor in HEROES
                else {"idle", "attack", "skill"}
            )
            self.assertEqual(set(states), expected)
            poses = []
            for state, a in states.items():
                w, h, rows = decoded[a["image"]]
                self.assertGreaterEqual(a["x"], 0)
                self.assertGreaterEqual(a["y"], 0)
                self.assertLessEqual(a["x"] + a["w"], w)
                self.assertLessEqual(a["y"] + a["h"], h)
                self.assertGreater(a["w"], 150)
                self.assertGreater(a["h"], 150)
                pixels = b"".join(
                    row[a["x"] * 4 : (a["x"] + a["w"]) * 4]
                    for row in rows[a["y"] : a["y"] + a["h"]]
                )
                alpha = pixels[3::4]
                self.assertIn(0, alpha)
                self.assertGreater(sum(v > 200 for v in alpha), 10000)
                poses.append(hashlib.sha256(pixels).hexdigest())
            self.assertEqual(len(set(poses)), len(poses), actor)
            hashes.extend(poses)
        self.assertEqual(len(set(hashes)), len(hashes))
        self.assertEqual(len(crops), 4)
        w, h, rows = decoded["crops"]
        for frames in crops.values():
            self.assertEqual(len(frames), 4)
            for a in frames:
                self.assertTrue(0 <= a["x"] < a["x"] + a["w"] <= w)
                self.assertTrue(0 <= a["y"] < a["y"] + a["h"] <= h)


if __name__ == "__main__":
    unittest.main()
