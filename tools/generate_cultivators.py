"""Detailed 64px cultivator state sheets and region-exclusive emergency artifacts."""

import json, math, shutil
from pathlib import Path


def enlarged(base, Raster):
    result = Raster(base.w * 2, base.h * 2)
    for y in range(base.h):
        for x in range(base.w):
            n = (y * base.w + x) * 4
            if base.data[n + 3]:
                result.rect(x * 2, y * 2, 2, 2, base.data[n : n + 4])
    return result


def generate(m, out):
    Raster = m.Raster
    ids = [
        "gatherer",
        "sword",
        "fire",
        "frost",
        "monk",
        "lightning",
        "herbalist",
        "formation",
    ]
    colors = {
        "gatherer": "8de0a2",
        "sword": "b8edd9",
        "fire": "ffad74",
        "frost": "b1eefa",
        "monk": "eac576",
        "lightning": "c9b1ff",
        "herbalist": "bae895",
        "formation": "c2c893",
    }
    sheets = Raster(768, 64 * len(ids) * 4)
    info = {}
    states = {"idle": 6, "attack": 8, "skill": 10, "ultimate": 12}
    for index, id in enumerate(ids):
        data = {"w": 64, "h": 64, "states": {}}
        for state_index, (state, count) in enumerate(states.items()):
            row = (index * 4 + state_index) * 64
            data["states"][state] = {
                "x": 0,
                "y": row,
                "frames": count,
                "fps": 6 if state == "idle" else 12,
            }
            for frame in range(count):
                r = enlarged(
                    m.hero(id, 0 if state == "idle" else 2 if state == "attack" else 3),
                    Raster,
                )
                accent = colors[id]
                progress = frame / max(1, count - 1)
                sway = round(math.sin(frame / count * math.tau) * 2)
                # Authored subpixel features go beyond nearest-neighbor enlargement.
                r.line(25, 31, 33, 44, "e4d7b0")
                r.line(26, 33, 31, 42, "a69d83")
                for yy in range(36, 53, 3):
                    r.line(22 + sway, yy, 26 + sway, yy + 2, "65777a")
                    r.line(36, yy, 40, yy + 2, accent)
                for yy in range(33, 52, 5):
                    r.pixel(30, yy, accent)
                    r.pixel(32, yy + 1, "d9c58b")
                r.pixel(37, 17, "1b2330")
                r.pixel(38, 18, "e5b490")
                r.pixel(36, 15, "c49375")
                if state == "idle" and frame == 4:
                    r.line(35, 18, 37, 18, "292f3b")
                else:
                    r.pixel(36, 18, "101827")
                    r.pixel(37, 18, "f1ddbd")
                r.line(28, 7, 31, 6, "e0cf9a")
                r.pixel(32, 8, accent)
                r.line(21, 56, 26, 55, "627477")
                r.line(37, 56, 41, 55, "708184")
                # Embroidered sleeve borders and independent flowing ribbons.
                r.line(38, 32, 45 + sway, 37, "e4d0a2")
                r.line(38, 33, 44 + sway, 39, accent)
                ribbon = round(math.sin(frame / count * math.tau) * 3)
                r.line(20, 43, 15, 48 + ribbon, accent)
                r.line(15, 48 + ribbon, 12, 51 + ribbon, "6d8c89")
                if state == "attack":
                    strength = math.sin(progress * math.pi)
                    angle = -1.4 + strength * 1.9
                    tip = (
                        round(44 + 18 * math.cos(angle)),
                        round(35 + 18 * math.sin(angle)),
                    )
                    if id in ("sword", "lightning", "monk"):
                        r.line(42, 34, *tip, "192433", 3)
                        r.line(43, 34, *tip, accent, 2)
                        r.line(41, 32, 46, 36, "d9b16e", 2)
                        if frame in (3, 4, 5):
                            r.line(
                                tip[0] - 7, tip[1] - 3, tip[0] - 2, tip[1] + 4, "e9ebc6"
                            )
                    else:
                        r.ellipse(
                            45,
                            23,
                            10 + round(strength * 6),
                            10 + round(strength * 6),
                            accent,
                        )
                        r.ellipse(48, 25, 4, 4, "fcf0c8")
                    r.line(20, 51, 17 - sway, 54, accent)
                elif state in ("skill", "ultimate"):
                    radius = 18 if state == "skill" else 26
                    cy = 33 if state == "skill" else 28
                    for n in range(8):
                        angle = n * math.tau / 8 + progress * math.tau
                        x = round(32 + radius * math.cos(angle))
                        y = round(cy + radius * 0.7 * math.sin(angle))
                        r.rect(x - 1, y - 1, 3, 3, accent)
                        if state == "ultimate":
                            r.line(x - 3, y - 3, x + 2, y - 3, "d4bd83")
                            r.pixel(x + 3, y - 2, "fff0be")
                    r.line(42, 35, 45, 20, "d3ad8a", 3)
                    r.line(45, 20, 49, 17, "ead0a3", 2)
                    if state == "ultimate":
                        r.line(18, 39, 15, 21, "d3ad8a", 3)
                        r.line(15, 21, 19, 17, "ead0a3", 2)
                        r.ellipse(24, 2 + frame % 2, 16, 4, accent)
                        for n in range(4):
                            x = 14 + n * 12
                            y = 55 - (frame * 3 + n * 9) % 42
                            r.rect(x, y, 2, 5, accent)
                            r.pixel(x + 1, y - 2, "f9e6b4")
                    if id == "fire":
                        for n in range(5):
                            x = round(
                                32 + 15 * math.cos(n * math.tau / 5 + progress * 2)
                            )
                            y = round(35 + 9 * math.sin(n * math.tau / 5))
                            r.poly(
                                [(x, y - 5), (x + 4, y), (x, y + 4), (x - 3, y)],
                                "e88c70",
                            )
                    elif id == "frost":
                        for n in range(3):
                            x = 10 + n * 19
                            y = 20 + (frame + n) % 3
                            r.rect(x, y, 6, 12, "d3e8d8")
                            r.line(x + 3, y + 2, x + 3, y + 8, "5d9aa7")
                    elif id == "lightning":
                        r.line(10, 18, 16, 12, accent)
                        r.line(16, 12, 12, 25, accent)
                        r.line(12, 25, 21, 20, "f3ead9")
                    elif id == "formation":
                        for n in range(8):
                            x = round(32 + 14 * math.cos(n * math.tau / 8))
                            y = round(35 + 8 * math.sin(n * math.tau / 8))
                            r.rect(x - 2, y, 5, 2, "d2b06e")
                            r.pixel(x, y + 3, accent)
                    elif id == "herbalist":
                        for n in range(4):
                            r.ellipse(
                                8 + n * 14, 12 + (frame + n * 4) % 35, 5, 3, accent
                            )
                else:
                    r.pixel(15 + (frame * 7) % 37, 10 + frame % 3, accent)
                sheets.blit(r, frame * 64, row)
        info[id] = data
    sheets.save(out / "cultivators.png")
    (out / "cultivators.json").write_text(json.dumps(info, indent=2) + "\n")
    retained = Path(__file__).resolve().parents[1] / "web/assets"
    for name in ("guardians.png", "guardians.json"):
        if (out / name).resolve() != (retained / name).resolve():
            shutil.copyfile(retained / name, out / name)
