"""Detailed 64px cultivator state sheets and region-exclusive emergency artifacts."""

import json, math


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
    guardians = Raster(48 * 6, 48 * 3)
    metadata = {}
    for row, region in enumerate(["wharf", "terrace", "tomb"]):
        for frame in range(6):
            r = Raster(48, 48)
            shift = round(math.sin(frame * math.tau / 6) * 2)
            if region == "wharf":
                r.poly(
                    [(3, 30), (11, 36), (36, 36), (44, 25), (38, 25), (33, 29)],
                    "356b72",
                )
                r.line(7, 31, 36, 31, "b3d5ac", 2)
                r.line(12, 37, 34, 37, "538c9b")
                r.line(23, 28, 23, 7, "c9b27d", 2)
                r.poly([(25, 9), (36, 22), (25, 22)], "97cfbc")
                r.line(26, 11, 30, 19, "e6e4bb")
                r.poly([(35, 27), (39, 19), (44, 21), (45, 25), (40, 27)], "6cbcb5")
                r.pixel(42, 22, "f9ce83")
                for n in range(3):
                    r.line(6 + n * 12, 40 + shift, 13 + n * 12, 40 + shift, "70bfc3")
            elif region == "terrace":
                r.ellipse(9, 32, 29, 7, "968052")
                r.ellipse(12, 33, 23, 4, "4e9990")
                for n in range(3):
                    x = 13 + n * 11
                    y = 6 + (shift if n == 1 else -shift)
                    r.line(x, y, x, y + 23, "d9efd4", 3)
                    r.line(x - 1, y + 2, x - 1, y + 18, "78c2b8")
                    r.line(x - 5, y + 22, x + 5, y + 22, "d0ad69", 2)
                    r.rect(x - 1, y + 24, 2, 5, "9b875d")
                r.pixel(5, 19 + frame, "c5e5c3")
                r.pixel(43, 16 - frame, "e9d394")
            else:
                r.line(22, 5, 26, 5, "d3b275", 2)
                r.line(22, 5, 20, 11, "a88b60", 2)
                r.line(26, 5, 28, 11, "a88b60", 2)
                r.poly(
                    [
                        (17, 11),
                        (30, 11),
                        (33, 29),
                        (37, 33),
                        (37, 36),
                        (10, 36),
                        (10, 33),
                        (14, 29),
                    ],
                    "7f7056",
                )
                r.poly([(18, 14), (28, 14), (31, 31), (16, 31)], "bba171")
                r.rect(19, 17, 8, 2, "4a7774")
                r.line(18, 22, 27, 22, "4d807d", 2)
                r.line(23, 17, 23, 28, "5ca6a0")
                r.ellipse(10, 33, 28, 6, "527674")
                r.ellipse(14, 35, 20, 3, "203e4b")
                r.rect(23, 35, 2, 7, "c2be87")
                r.rect(21 + shift, 41, 6, 2, "9bd4bc")
            guardians.blit(r, frame * 48, row * 48)
        metadata[region] = {"x": 0, "y": row * 48, "w": 48, "h": 48, "frames": 6}
    guardians.save(out / "guardians.png")
    (out / "guardians.json").write_text(json.dumps(metadata, indent=2) + "\n")


def detail_map(m, base, kind):
    # Remodel the stronghold before adding native 2x ornamentation.
    r = base
    R = m.Raster
    if kind == "wharf":
        for y in (95, 134, 173):
            for x in (7, 72):
                m.lantern(r, x, y, size=1)
        for x in range(17, 70, 8):
            r.line(x, 93, x, 213, "805749")
            r.pixel(x + 2, 115, "c89358")
        r.rect(30, 190, 27, 4, "a2674b")
        r.line(44, 186, 44, 218, "d2ad76", 2)
        for y in range(226, 242, 4):
            r.line(0, y, 20, y, "5d9292")
    elif kind == "terrace":
        r.rect(5, 91, 76, 130, "ced3b6")
        r.rect(13, 99, 60, 119, "3a726a")
        for x in (14, 62):
            r.rect(x, 91, 8, 132, "dce0c3")
            r.line(x + 2, 94, x + 2, 218, "9bad98")
        for y, width in [(62, 82), (49, 58), (37, 36)]:
            x = 43 - width // 2
            r.poly(
                [
                    (x, y + 12),
                    (x + 7, y + 7),
                    (43, y),
                    (x + width - 7, y + 7),
                    (x + width, y + 12),
                ],
                "386d67",
            )
            r.line(x + 2, y + 12, x + width - 2, y + 12, "d4c88c")
        r.rect(30, 157, 26, 61, "244a50")
        r.ellipse(32, 175, 21, 24, "70b7a0")
        r.ellipse(38, 181, 9, 12, "d8ddb4")
        r.poly([(2, 222), (85, 222), (71, 242), (49, 250), (21, 239)], "3e5f5b")
        for x in (6, 76):
            r.line(x, 101, x + 8, 129, "8eb29c")
            r.poly([(x, 100), (x + 10, 102), (x + 9, 125), (x + 2, 121)], "79b89c")
    else:
        r.rect(5, 79, 78, 142, "425b60")
        r.rect(11, 86, 66, 134, "947951")
        r.rect(16, 91, 56, 127, "354d55")
        for x in (17, 46):
            r.rect(x, 96, 24, 118, "58746a")
            r.rect(x + 2, 99, 20, 110, "355358")
            for y in (104, 135, 166, 196):
                r.line(x + 3, y, x + 19, y, "b49b69")
                r.line(x + 3, y, x + 3, y + 18, "a28b60")
                r.line(x + 19, y, x + 19, y + 18, "a28b60")
            r.ellipse(x + 7, 150, 9, 9, "b59d73")
            r.ellipse(x + 9, 152, 5, 5, "29434b")
        r.poly([(0, 78), (7, 67), (44, 58), (80, 67), (88, 78)], "213b49")
        r.line(3, 79, 85, 79, "a58d62", 2)
        for x in (6, 77):
            for y in (98, 144, 190):
                m.flame(r, x, y, "4c9796", "b9dfb8")
        r.rect(40, 84, 7, 8, "b3a274")
        r.line(43, 86, 43, 90, "416a6a")
    hi = enlarged(r, R)
    # New, non-upscaled microdetail: roof tiles, masonry, cloth edges and runic inlays.
    for lane in range(5):
        for col in range(12):
            x = 184 + col * 64
            y = 120 + lane * 64
            for n in range(4):
                xx = x + 6 + n * 14
                yy = y + 5 + (n * 11 + col * 3 + lane * 7) % 43
                hi.pixel(
                    xx,
                    yy,
                    (
                        "897654"
                        if kind == "wharf"
                        else "7a9690" if kind == "terrace" else "607d80"
                    ),
                )
                hi.line(
                    xx,
                    yy + 1,
                    xx + 5,
                    yy + 1,
                    "415a59" if kind != "wharf" else "4d453b",
                )
            if col == 0:
                for n in range(8):
                    a = n * math.tau / 8
                    hi.pixel(
                        round(x + 32 + 17 * math.cos(a)),
                        round(y + 32 + 17 * math.sin(a)),
                        "b5ac78",
                    )
    for y in range(178, 433, 7):
        for x in (24, 142):
            hi.line(x, y, x + 7, y, "c4b689" if kind != "tomb" else "76978a")
    for x in range(8, 170, 7):
        hi.pixel(x, 155, "d8bd80")
        hi.pixel(x + 1, 158, "7d907b")
    return hi
