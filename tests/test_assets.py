"""Validate the shipped raster assets without a third-party image decoder."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from game.content import ENEMIES, HEROES, STAGES

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "web" / "assets"


def decode_png(path):
    """Read and validate our noninterlaced 8-bit RGBA production PNGs."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Invalid PNG signature: {path.name}")
    offset, compressed, chunks = 8, bytearray(), []
    width = height = None
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("Truncated PNG chunk")
        length = struct.unpack("!I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        body = data[offset + 8:offset + 8 + length]
        expected = struct.unpack("!I", data[offset + 8 + length:offset + 12 + length])[0]
        if zlib.crc32(kind + body) & 0xffffffff != expected:
            raise ValueError(f"PNG checksum mismatch: {kind!r}")
        chunks.append(kind)
        if kind == b"IHDR":
            width, height, depth, mode, compression, filtering, interlace = struct.unpack("!2I5B", body)
            if (depth, mode, compression, filtering, interlace) != (8, 6, 0, 0, 0):
                raise ValueError("Expected noninterlaced 8-bit RGBA PNG")
        elif kind == b"IDAT":
            compressed.extend(body)
        elif kind == b"IEND":
            if body:
                raise ValueError("IEND must be empty")
        offset += length + 12
    if not chunks or chunks[0] != b"IHDR" or chunks[-1] != b"IEND" or b"IDAT" not in chunks:
        raise ValueError("PNG required chunks missing or misordered")
    scan = zlib.decompress(compressed)
    stride = width * 4
    if len(scan) != (stride + 1) * height:
        raise ValueError("Decoded PNG length does not match dimensions")
    rows = []
    for y in range(height):
        start = y * (stride + 1)
        filtering = scan[start]
        row = bytearray(scan[start + 1:start + stride + 1])
        previous = rows[-1] if rows else bytes(stride)
        for x in range(stride):
            left, above = (row[x - 4] if x >= 4 else 0), previous[x]
            upper_left = previous[x - 4] if x >= 4 else 0
            if filtering == 0:
                predictor = 0
            elif filtering == 1:
                predictor = left
            elif filtering == 2:
                predictor = above
            elif filtering == 3:
                predictor = (left + above) // 2
            elif filtering == 4:
                p = left + above - upper_left
                distances = abs(p - left), abs(p - above), abs(p - upper_left)
                predictor = (left, above, upper_left)[distances.index(min(distances))]
            else:
                raise ValueError("Unsupported PNG row filter")
            row[x] = (row[x] + predictor) & 255
        rows.append(bytes(row))
    return width, height, rows


class AssetTests(unittest.TestCase):
    def test_backgrounds_are_complete_native_rasters(self):
        regions = {stage["region"] for stage in STAGES.values()}
        self.assertEqual(regions, {"wharf", "terrace", "tomb"})
        for name in sorted(regions | {"title"}):
            with self.subTest(background=name):
                width, height, rows = decode_png(ASSETS / f"{name}.png")
                self.assertEqual((width, height), (384, 216))
                self.assertTrue(all(row[x] == 255 for row in rows for x in range(3, width * 4, 4)))
                palette = {row[x:x + 4] for row in rows for x in range(0, width * 4, 4)}
                self.assertGreaterEqual(len(palette), 20)

    def test_all_content_has_bounded_animated_sprites(self):
        width, height, rows = decode_png(ASSETS / "sprites.png")
        sprites = json.loads((ASSETS / "sprites.json").read_text())
        ids = set(HEROES) | set(ENEMIES) | {"altar"}
        self.assertTrue(ids <= set(sprites))
        for name in sorted(ids):
            with self.subTest(entity=name):
                item = sprites[name]
                self.assertEqual((item["w"], item["h"], item["frames"]), (32, 32, 4))
                self.assertGreaterEqual(item["x"], 0)
                self.assertGreaterEqual(item["y"], 0)
                self.assertLessEqual(item["x"] + item["w"] * item["frames"], width)
                self.assertLessEqual(item["y"] + item["h"], height)
                frames = []
                for frame in range(item["frames"]):
                    x = item["x"] + frame * item["w"]
                    pixels = b"".join(row[x * 4:(x + item["w"]) * 4] for row in rows[item["y"]:item["y"] + item["h"]])
                    self.assertIn(0, pixels[3::4], "Sprites need a transparent silhouette")
                    self.assertIn(255, pixels[3::4], "Sprite must contain visible artwork")
                    frames.append(pixels)
                self.assertEqual(len(set(frames)), 4, "Animation must not contain cloned frames")
        for alias, key in {"miao": "tide", "river_lord": "riverlord", "mountain_lord": "mountainlord", "bone_emperor": "boneemperor"}.items():
            self.assertEqual(sprites[alias], sprites[key])

    def test_ui_icon_atlas_bounds_and_content(self):
        width, height, rows = decode_png(ASSETS / "icons.png")
        icons = json.loads((ASSETS / "icons.json").read_text())
        self.assertTrue({"qi", "gate", "stones", "relic", "shield", "heal", "fire", "ice"} <= set(icons))
        for name, item in icons.items():
            with self.subTest(icon=name):
                self.assertLessEqual(item["x"] + item["w"], width)
                self.assertLessEqual(item["y"] + item["h"], height)
                alpha = [row[x * 4 + 3] for row in rows[item["y"]:item["y"] + item["h"]] for x in range(item["x"], item["x"] + item["w"])]
                self.assertIn(255, alpha)

    def test_assets_reproduce_exactly_without_external_packages(self):
        spec = importlib.util.spec_from_file_location("van_dao_asset_generator", ROOT / "tools" / "generate_assets.py")
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        with tempfile.TemporaryDirectory(prefix="van-dao-art-") as folder:
            generator.OUT = Path(folder)
            generator.main()
            for path in Path(folder).iterdir():
                with self.subTest(asset=path.name):
                    self.assertEqual(path.read_bytes(), (ASSETS / path.name).read_bytes())


if __name__ == "__main__":
    unittest.main()
