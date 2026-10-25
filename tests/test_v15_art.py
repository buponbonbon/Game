"""Authored animation cells are real distinct artwork, bounded and transparent."""

import hashlib, json, unittest
from pathlib import Path
from game.content import HEROES, ENEMIES
from tests.test_assets import decode_png

ROOT = Path(__file__).resolve().parents[1] / "web/assets"


class MotionArtTests(unittest.TestCase):
    def test_all_actors_have_native_action_sequences_and_reactions(self):
        atlas = json.loads((ROOT / "motion/motion.json").read_text())
        self.assertEqual(set(atlas), set(HEROES) | set(ENEMIES) | {"altar"})
        count = 0
        for id, meta in atlas.items():
            source = ROOT / "motion" / (id + ".png")
            self.assertEqual(
                hashlib.sha256(source.read_bytes()).hexdigest(), meta["sha256"]
            )
            w, h, rows = decode_png(source)
            self.assertEqual((w, h), (meta["width"], meta["height"]))
            self.assertGreaterEqual(meta["cell_h"], 200)
            self.assertGreaterEqual(meta["cell_w"], 200)
            states = meta["states"]
            self.assertEqual(len(states["attack"]), 4)
            self.assertEqual(len(states["skill"]), 4)
            self.assertEqual(len(states["hurt"]), 1)
            self.assertEqual(len(states["death"]), 2)
            self.assertEqual(
                len(states["ultimate"] if id in HEROES else states["walk"]), 4
            )
            for name, frames in states.items():
                hashes = []
                for f in frames:
                    self.assertTrue(0 <= f["x"] < f["x"] + f["w"] <= w)
                    self.assertTrue(0 <= f["y"] < f["y"] + f["h"] <= h)
                    self.assertTrue(0 <= f["dx"] < meta["cell_w"])
                    self.assertTrue(0 <= f["dy"] < meta["cell_h"])
                    pixels = b"".join(
                        row[f["x"] * 4 : (f["x"] + f["w"]) * 4]
                        for row in rows[f["y"] : f["y"] + f["h"]]
                    )
                    alpha = pixels[3::4]
                    self.assertIn(0, alpha)
                    self.assertGreater(sum(v > 180 for v in alpha), 250, (id, name))
                    hashes.append(hashlib.sha256(pixels).hexdigest())
                    count += 1
                if len(frames) >= 2:
                    self.assertGreaterEqual(
                        len(set(hashes)), min(3, len(frames)), (id, name)
                    )
        self.assertEqual(count, 336)

    def test_objective_props_are_separate_complete_cutouts(self):
        w, h, rows = decode_png(ROOT / "objectives.png")
        meta = json.loads((ROOT / "objectives.json").read_text())
        self.assertEqual(set(meta), {"caravan", "beacon", "oath"})
        last = 0
        for name, item in meta.items():
            self.assertGreaterEqual(item["x"], last)
            self.assertLessEqual(item["x"] + item["w"], w)
            self.assertLessEqual(item["y"] + item["h"], h)
            self.assertGreater(item["w"], 400)
            self.assertGreater(item["h"], 500)
            last = item["x"] + item["w"]


if __name__ == "__main__":
    unittest.main()
