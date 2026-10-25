#!/usr/bin/env python3
"""Create the game's original raster artwork using only Python's standard library.

Procedural fallback sprites/icons use an integer grid. Authored RPG scenes,
actor pose sheets and botany are retained PNG inputs copied without alteration.
No third-party packages are required for this preservation/generation command.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import random
import struct
import zlib

OUT = Path(__file__).resolve().parents[1] / "web" / "assets"


def color(value):
    if isinstance(value, str):
        value = value.lstrip("#")
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    return tuple(value) if len(value) == 4 else tuple(value) + (255,)


class Raster:
    def __init__(self, width, height, fill=(0, 0, 0, 0)):
        self.w, self.h = width, height
        self.data = bytearray(color(fill) * (width * height))

    def pixel(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            start = (y * self.w + x) * 4
            self.data[start:start + 4] = bytes(color(c))

    def rect(self, x, y, w, h, c):
        for yy in range(int(y), int(y + h)):
            for xx in range(int(x), int(x + w)):
                self.pixel(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, width=1):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = 1 if x0 < x1 else -1, 1 if y0 < y1 else -1
        error = dx + dy
        while True:
            self.rect(x0, y0, width, width, c)
            if x0 == x1 and y0 == y1:
                break
            twice = 2 * error
            if twice >= dy:
                error += dy
                x0 += sx
            if twice <= dx:
                error += dx
                y0 += sy

    def poly(self, points, c):
        low = max(0, min(p[1] for p in points))
        high = min(self.h - 1, max(p[1] for p in points))
        for yy in range(low, high + 1):
            intersections = []
            for p1, p2 in zip(points, points[1:] + points[:1]):
                if p1[1] == p2[1]:
                    continue
                if min(p1[1], p2[1]) <= yy < max(p1[1], p2[1]):
                    intersections.append(int(p1[0] + (yy - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])))
            intersections.sort()
            for x0, x1 in zip(intersections[::2], intersections[1::2]):
                self.rect(x0, yy, x1 - x0 + 1, 1, c)

    def ellipse(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if ((xx + .5 - x - w / 2) / (w / 2)) ** 2 + ((yy + .5 - y - h / 2) / (h / 2)) ** 2 <= 1:
                    self.pixel(xx, yy, c)

    def blit(self, other, x, y):
        for yy in range(other.h):
            for xx in range(other.w):
                offset = (yy * other.w + xx) * 4
                c = other.data[offset:offset + 4]
                if c[3]:
                    dx, dy = x + xx, y + yy
                    if c[3] < 255 and 0 <= dx < self.w and 0 <= dy < self.h:
                        pos = (dy * self.w + dx) * 4
                        d = self.data[pos:pos + 4]
                        if d[3]:
                            alpha = c[3] + d[3] * (255 - c[3]) / 255
                            mixed = [round((c[k] * c[3] + d[k] * d[3] * (255 - c[3]) / 255) / alpha) for k in range(3)]
                            c = mixed + [round(alpha)]
                    self.pixel(dx, dy, c)

    def save(self, path):
        def chunk(kind, body):
            return struct.pack("!I", len(body)) + kind + body + struct.pack("!I", zlib.crc32(kind + body) & 0xffffffff)
        scan = b"".join(b"\0" + self.data[y * self.w * 4:(y + 1) * self.w * 4] for y in range(self.h))
        result = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack("!2I5B", self.w, self.h, 8, 6, 0, 0, 0))
        result += chunk(b"IDAT", zlib.compress(scan, 9)) + chunk(b"IEND", b"")
        path.write_bytes(result)


INK = "111a2b"
GOLD = "e8ba65"
LIGHT = "f8e7bd"


def cloud(r, x, y, scale=1, c="29465a"):
    for dx, dy, w, h in [(0, 4, 26, 4), (5, 1, 14, 5), (15, 3, 20, 4), (28, 5, 9, 2)]:
        r.rect(x + dx * scale, y + dy * scale, w * scale, h * scale, c)


def mountain(r, x, peak, width, bottom, c, highlight=None):
    points = [(x, bottom), (x + width // 5, peak + 19), (x + width // 3, peak + 12),
              (x + width // 2, peak), (x + width * 3 // 5, peak + 8),
              (x + width * 4 // 5, peak + 24), (x + width, bottom)]
    r.poly(points, c)
    if highlight:
        r.poly([(x + width // 2, peak), (x + width // 2 + 4, peak + 11),
                (x + width * 3 // 5, peak + 8), (x + width * 4 // 5, peak + 24),
                (x + width // 2 + 6, peak + 15), (x + width // 3, peak + 12)], highlight)


def temple(r, x, y, width=42, c="182e40", light="705647"):
    h = width // 3
    r.rect(x + 8, y + h // 2, width - 16, h, c)
    r.poly([(x, y + h // 2), (x + 8, y + h // 3), (x + width // 2, y),
            (x + width - 8, y + h // 3), (x + width, y + h // 2), (x + width - 2, y + h // 2 + 2),
            (x + 2, y + h // 2 + 2)], c)
    r.line(x + 4, y + h // 2, x + width - 4, y + h // 2, light)
    for xx in range(x + 13, x + width - 8, 8):
        r.rect(xx, y + h // 2 + 3, 2, max(3, h // 2), light)
    r.rect(x + width // 2 - 3, y + h // 2 + 4, 6, h - 3, INK)


def lantern(r, x, y, c="cc7054", size=1):
    r.line(x + 3 * size, y - 7 * size, x + 3 * size, y, "9f8d69")
    r.rect(x + size, y, 5 * size, size, "503d38")
    r.rect(x, y + size, 7 * size, 7 * size, "592f38")
    r.rect(x + size, y + size, 5 * size, 6 * size, c)
    r.rect(x + 3 * size, y + 2 * size, size, 4 * size, "f5d991")
    r.rect(x + size, y + 8 * size, 5 * size, size, "503d38")
    r.line(x + 3 * size, y + 9 * size, x + 3 * size, y + 12 * size, c)


def stars(r, rng, c="94bbc3", number=45):
    for _ in range(number):
        x, y = rng.randrange(384), rng.randrange(3, 64)
        r.pixel(x, y, c)
        if rng.random() < .12:
            r.pixel(x - 1, y, c)
            r.pixel(x + 1, y, c)


def board(r, kind, rng):
    x, y, w, h = 44, 49, 306, 125
    palettes = {"wharf": ("695241", "614b3c", "81664a", "493e35"),
                "terrace": ("54716b", "4d6762", "6a8071", "354f4d"),
                "tomb": ("384957", "35434e", "4b5b61", "23333f")}
    a, b, hi, seam = palettes[kind]
    r.rect(x - 3, y - 4, w + 6, h + 8, INK)
    r.rect(x - 2, y - 3, w + 4, 3, hi)
    for row in range(5):
        for col in range(9):
            xx, yy = x + col * 34, y + row * 25
            r.rect(xx, yy, 34, 25, a if (row + col) % 2 else b)
            r.line(xx, yy + 24, xx + 33, yy + 24, seam)
            r.line(xx + 33, yy, xx + 33, yy + 24, seam)
            if kind == "wharf":
                for offset in (5, 12, 19):
                    r.line(xx + 1, yy + offset, xx + 31, yy + offset, seam)
                    r.line(xx + 4, yy + offset + 1, xx + rng.randrange(10, 25), yy + offset + 1, hi)
                r.pixel(xx + 2, yy + 2, "a18b65")
                r.pixel(xx + 30, yy + 21, "282e30")
            else:
                for _ in range(5):
                    px, py = xx + rng.randrange(3, 31), yy + rng.randrange(3, 22)
                    r.rect(px, py, rng.randrange(1, 4), 1, hi)
                if (row + col) % 3 == 0:
                    r.line(xx + 23, yy + 3, xx + 20, yy + 9, seam)
                    r.line(xx + 20, yy + 9, xx + 24, yy + 13, seam)
                    r.rect(xx + 2, yy + 19, 5, 2, "425e50" if kind == "terrace" else "314c4b")
    r.rect(x - 3, y + h + 1, w + 6, 3, seam)


def wharf():
    r, rng = Raster(384, 216, "142c40"), random.Random(11)
    for y, h, c in [(0, 15, "15283d"), (15, 18, "1b3448"), (33, 25, "234656"), (58, 158, "254a52")]:
        r.rect(0, y, 384, h, c)
    stars(r, rng)
    r.ellipse(286, 9, 20, 20, "d4c99c")
    r.ellipse(281, 5, 19, 21, "1b3448")
    mountain(r, -20, 27, 180, 79, "273d4c")
    mountain(r, 174, 20, 246, 80, "263b4c")
    temple(r, 31, 24, 50, "162f3f", "6a6957")
    temple(r, 318, 28, 46, "162b3d", "667064")
    for i in range(22):
        x, y = rng.randrange(384), rng.randrange(60, 216)
        r.rect(x, y, rng.randrange(5, 30), 1, "41635d")
    for y in (80, 119, 176, 193):
        r.rect(0, y, 384, 1, "1c3b48")
    for x in (9, 32, 356, 376):
        r.rect(x, 45, 5, 143, "253b3c")
        r.rect(x, 44, 6, 3, "8d7858")
        r.rect(x + 1, 50, 1, 125, "567164")
    board(r, "wharf", rng)
    for x in (17, 355):
        r.line(x, 28, x + 12, 30, "9d8a67")
        lantern(r, x + 3, 35, size=1)
        lantern(r, x + 3, 143, size=1)
    for x in (2, 365):
        for yy in (185, 197):
            r.line(x, yy + 12, x + 6, yy - 3, "507765")
            r.line(x + 4, yy + 8, x + 11, yy, "63916f")
    for x in range(55, 340, 21):
        r.rect(x, 181, 5, 12, "233942")
        r.rect(x, 194, 5, 2, "46625c")
    return r


def terrace():
    r, rng = Raster(384, 216, "294c5b"), random.Random(21)
    r.rect(0, 0, 384, 22, "315f6a")
    r.rect(0, 22, 384, 29, "427980")
    mountain(r, -30, 12, 155, 115, "427178", "5d8d89")
    mountain(r, 87, -13, 140, 109, "3b656d", "638b83")
    mountain(r, 231, 13, 190, 120, "365b63", "527b73")
    mountain(r, 0, 61, 111, 217, "234451", "325b5c")
    mountain(r, 274, 54, 139, 216, "244552", "365f5d")
    for x, y, scale in [(-10, 28, 2), (111, 33, 1), (245, 17, 2), (175, 186, 2)]:
        cloud(r, x, y, scale, "73998c")
    temple(r, 212, 15, 49, "273d4a", "b09b72")
    r.line(183, 40, 283, 40, "6c8d79")
    board(r, "terrace", rng)
    for x in (16, 357):
        r.rect(x, 63, 6, 103, "1d3541")
        r.rect(x, 61, 10, 5, "84937a")
        r.rect(x + 2, 66, 2, 89, "527263")
        r.line(x + 3, 69, x + 17, 69, "9c9e78")
        r.poly([(x + 6, 71), (x + 18, 71), (x + 15, 94), (x + 6, 91)], "4b8d7a")
        r.rect(x + 9, 74, 3, 11, "afc89b")
    r.poly([(41, 177), (352, 177), (332, 192), (319, 192), (310, 211), (270, 207),
            (233, 216), (119, 216), (86, 204), (62, 200)], "203e49")
    for x in range(49, 347, 8):
        y = rng.randrange(178, 207)
        r.rect(x, y, rng.randrange(2, 7), rng.randrange(3, 12), "315653")
        if rng.random() < .6:
            r.rect(x, 177, rng.randrange(3, 8), 3, "5d8470")
    for x, y in [(10, 188), (362, 182)]:
        r.line(x + 6, y + 27, x + 8, y, "394e48", 2)
        for yy in range(y, y + 23, 6):
            r.ellipse(x - 2, yy, 20, 8, "316854")
            r.rect(x, yy + 2, 12, 2, "4d9070")
    return r


def flame(r, x, y, c1="3daba7", c2="9bdfc2"):
    r.poly([(x, y + 12), (x - 4, y + 6), (x, y), (x + 2, y + 5), (x + 4, y + 2), (x + 5, y + 10)], c1)
    r.rect(x, y + 6, 2, 5, c2)


def tomb():
    r, rng = Raster(384, 216, "111d31"), random.Random(31)
    r.rect(0, 22, 384, 32, "1a2b3e")
    r.rect(0, 54, 384, 162, "1b2b39")
    stars(r, rng, "63939c", 67)
    r.ellipse(163, -8, 42, 42, "9bb9ab")
    r.ellipse(170, -3, 6, 5, "6d918d")
    r.rect(181, 19, 8, 2, "769b91")
    mountain(r, -12, 20, 179, 81, "17283a")
    mountain(r, 200, 15, 208, 84, "16283a")
    for xx in (24, 94, 278, 352):
        temple(r, xx - 14, 25, 28, "112235", "354e5b")
        r.rect(xx - 5, 34, 10, 22, "132334")
    board(r, "tomb", rng)
    for x in (14, 360):
        for y in (61, 128):
            r.rect(x + 2, y + 17, 10, 20, "1c2a39")
            r.rect(x, y + 15, 14, 4, "5a6e6d")
            r.rect(x + 4, y + 23, 6, 1, "71877a")
            flame(r, x + 6, y + 2)
    for x in range(48, 348, 30):
        y = rng.randrange(184, 204)
        r.ellipse(x, y, 10, 8, "71847c")
        r.rect(x + 1, y + 3, 3, 3, "172b38")
        r.rect(x + 6, y + 3, 3, 3, "172b38")
        r.pixel(x + 5, y + 6, "1c3540")
        r.rect(x + 2, y + 7, 6, 3, "596e6b")
    for x, y in [(56, 192), (168, 201), (289, 188)]:
        cloud(r, x, y, 2, "29474f")
    return r


def title():
    r, rng = Raster(384, 216, "111d30"), random.Random(41)
    for y, h, c in [(0, 27, "17293d"), (27, 27, "234254"), (54, 37, "30596a"),
                     (91, 58, "3b6b73"), (149, 67, "2d555a")]:
        r.rect(0, y, 384, h, c)
    stars(r, rng, "8ea9a4", 80)
    r.ellipse(292, 16, 31, 31, "dbd2a8")
    r.ellipse(289, 11, 29, 29, "17293d")
    mountain(r, -36, 54, 182, 163, "244252", "315b63")
    mountain(r, 72, 39, 146, 166, "2c5362", "407379")
    mountain(r, 171, 27, 163, 166, "254957", "3a6b70")
    mountain(r, 296, 63, 138, 170, "234551", "3d6867")
    for x, y, scale in [(13, 104, 2), (134, 117, 2), (285, 77, 1), (-20, 143, 2)]:
        cloud(r, x, y, scale, "56817d")
    r.poly([(0, 164), (36, 155), (88, 160), (119, 145), (169, 155), (196, 146), (253, 162),
            (302, 147), (384, 158), (384, 216), (0, 216)], "18343d")
    r.poly([(214, 216), (250, 148), (277, 148), (306, 216)], "647c6c")
    for y in range(159, 216, 8):
        width = int((y - 148) * 1.15 + 26)
        r.rect(264 - width // 2, y, width, 2, "364e4e")
    # Carved mountain gate: broken jade stone with a warm interior lantern.
    r.rect(231, 107, 10, 62, "172d36")
    r.rect(287, 107, 10, 62, "172d36")
    r.rect(233, 111, 5, 54, "81917a")
    r.rect(289, 111, 5, 54, "81917a")
    r.rect(228, 106, 72, 8, "a2a184")
    r.rect(230, 109, 68, 3, "50675e")
    r.poly([(219, 106), (234, 98), (263, 85), (294, 98), (309, 106), (306, 109), (222, 109)], "172a36")
    r.line(224, 105, 305, 105, "c4a775", 2)
    r.line(232, 101, 296, 101, "52746c")
    r.rect(253, 101, 22, 7, "553f36")
    for x in (257, 264, 270):
        r.rect(x, 102, 2, 4, "d4b578")
    lantern(r, 244, 119, size=1)
    lantern(r, 276, 119, size=1)
    for x, y in [(326, 149), (352, 165), (20, 180), (52, 190)]:
        r.line(x, y, x + 3, y + 27, "111f2b", 2)
        for k in range(4):
            r.poly([(x - 13, y + k * 6 + 4), (x, y + k * 5 - 4), (x + 16, y + k * 6 + 5)], "193a3e")
            r.line(x - 8, y + k * 6 + 3, x + 11, y + k * 6 + 3, "2e514b")
    # A solitary sword cultivator watches the gate. The quiet left-center sky
    # remains open for the title and menu; foreground pixels anchor the scene.
    r.ellipse(249, 172, 29, 5, "1b363a")
    r.blit(hero("sword", 0), 246, 142)
    r.line(273, 178, 288, 178, "3c675f")
    r.line(235, 180, 257, 180, "3c675f")
    for x, y in [(344, 193), (357, 200)]:
        r.poly([(x - 5, y), (x, y - 5), (x + 6, y), (x + 2, y + 3)], "9d6772")
        r.rect(x - 1, y - 2, 3, 3, "e6b88a")
        r.line(x - 8, y + 4, x + 10, y + 4, "4c8173")
    return r


def shadow(r):
    r.ellipse(6, 27, 21, 4, (8, 19, 29, 120))


def spark(r, x, y, c):
    r.rect(x - 1, y, 3, 1, c)
    r.rect(x, y - 1, 1, 3, c)


def hero(kind, frame):
    r = Raster(32, 32)
    shadow(r)
    bob = (0, -1, 0, 0)[frame]
    palettes = {
        "gatherer": ("3e7865", "70ad7a", "c0d3a1", "263e40"),
        "sword": ("426d75", "79a8a0", "e6e3bd", "213543"),
        "fire": ("9a3e4b", "de6c62", "f6c08a", "4c2d40"),
        "frost": ("527e9d", "90bfd2", "e0e9dc", "273e61"),
        "monk": ("8b633b", "cb9553", "e6c77e", "4b3f35"),
        "lightning": ("504875", "8b71af", "ced6dd", "292c50"),
        "herbalist": ("3e6c4b", "719967", "c2ca8d", "253f3b"),
        "formation": ("2e676a", "589691", "bca674", "213a48"),
    }
    dark, mid, light, edge = palettes[kind]
    # Silhouette: feet and a diagonally folded robe.
    if kind == "monk":
        r.poly([(10, 13 + bob), (20, 12 + bob), (25, 26), (22, 29), (8, 29), (6, 25)], INK)
        r.poly([(11, 13 + bob), (20, 14 + bob), (23, 26), (10, 27), (8, 23)], dark)
        r.poly([(11, 14 + bob), (15, 14 + bob), (19, 26), (10, 26)], mid)
        r.rect(11, 17 + bob, 8, 2, light)
    else:
        r.poly([(12, 13 + bob), (19, 13 + bob), (23, 26), (21, 29), (8, 28), (9, 23)], INK)
        r.poly([(12, 14 + bob), (19, 14 + bob), (21, 26), (10, 27)], dark)
        r.poly([(13, 14 + bob), (16, 15 + bob), (17, 26), (11, 26)], mid)
        r.poly([(12, 14 + bob), (14, 14 + bob), (18, 22 + bob), (16, 23 + bob)], light)
        r.rect(10, 21, 11, 2, edge)
        r.rect(14, 21, 3, 1, GOLD)
    r.rect(10, 28, 4, 2, "172534")
    r.rect(18, 28, 4, 2, "172534")
    # Neck, hair silhouette and face in profile.
    r.rect(14, 11 + bob, 4, 4, "c99774")
    r.ellipse(11, 4 + bob, 10, 10, INK)
    hair = "b6c7ce" if kind in ("frost", "lightning") else "20303c"
    r.ellipse(12, 5 + bob, 8, 8, "deb58c")
    if kind != "monk":
        r.rect(11, 5 + bob, 8, 4, hair)
        r.rect(11, 8 + bob, 2, 5, hair)
        r.rect(13, 2 + bob, 4, 4, INK)
        r.rect(14, 2 + bob, 3, 3, hair)
        r.rect(13, 5 + bob, 6, 1, light)
    else:
        r.rect(13, 5 + bob, 5, 1, "edcea0")
        r.pixel(15, 8 + bob, "b28361")
    r.pixel(18, 9 + bob, INK)
    r.pixel(19, 11 + bob, "bb815f")
    attack = frame in (2, 3)
    hand_x = 23 if attack else 21
    r.poly([(18, 15 + bob), (21, 15 + bob), (hand_x + 1, 20 + bob), (hand_x - 3, 21 + bob), (17, 18 + bob)], dark)
    r.rect(hand_x - 1, 17 + bob, 3, 3, "deb58c")
    if kind == "gatherer":
        r.rect(10, 17 + bob, 2, 5, light)
        r.ellipse(21, 17 + bob, 7, 9, "244b45")
        r.ellipse(22, 18 + bob, 5, 6, "7caa69")
        r.rect(23, 15 + bob, 3, 4, "b5c88d")
        r.rect(24, 19 + bob, 1, 3, "e7d99c")
        for x, y in [(6, 12 + frame % 2), (26, 8 + frame % 3), (6, 23)]:
            spark(r, x, y, "83c99c")
    elif kind in ("sword", "lightning"):
        blade = "b7ded4" if kind == "sword" else "dccaf3"
        if attack:
            r.line(21, 18 + bob, 30, 10 + bob, INK, 2)
            r.line(22, 18 + bob, 30, 10 + bob, blade)
            r.line(20, 17 + bob, 24, 21 + bob, GOLD)
            r.line(23, 5 + bob, 29, 9 + bob, light)
            r.line(29, 10 + bob, 30, 14 + bob, light)
        else:
            r.line(24, 24, 27, 8 + bob, INK, 2)
            r.line(25, 23, 28, 7 + bob, blade)
            r.line(22, 21, 28, 22, GOLD)
        if kind == "lightning":
            r.line(6, 11, 9, 7, "a58bda")
            r.line(9, 7, 7, 15, "a58bda")
            r.line(7, 15, 10, 12, "eee2ef")
            spark(r, 29, 26 - frame, "b7a0e3")
        else:
            r.line(5, 12 + frame, 9, 9 + frame, "81b083")
            r.pixel(7, 11 + frame, "c6d9a5")
    elif kind == "fire":
        r.rect(9, 8 + bob, 4, 3, "c65e60")
        r.pixel(10, 7 + bob, GOLD)
        flame(r, 25, 7 + bob if attack else 11 + bob, "e1844f", "ffe0a2")
        r.pixel(7, 21 + frame % 2, "d96a5a")
        r.pixel(28, 24 - frame % 2, "f2ae68")
    elif kind == "frost":
        for xx, yy in [(6, 14 - frame % 2), (25, 6 + frame % 2)]:
            r.rect(xx, yy, 4, 7, "263950")
            r.rect(xx + 1, yy, 3, 6, "c3dece")
            r.rect(xx + 2, yy + 2, 1, 3, "4e82a4")
        spark(r, 26, 21, "a3e2de")
        r.rect(12, 3 + bob, 7, 1, "e3f2df")
    elif kind == "monk":
        r.line(25, 7, 25, 29, INK, 3)
        r.line(26, 7, 26, 28, "a69672")
        r.rect(23, 6, 7, 3, "b6b391")
        r.rect(24, 5, 5, 1, "e0d1a0")
        for x, y in [(10, 15), (11, 18), (13, 20), (16, 20), (18, 18)]:
            r.rect(x, y + bob, 2, 2, "4a3b34")
            r.pixel(x, y + bob, "bea173")
        if attack:
            r.line(23, 25, 30, 25, "d9b677")
    elif kind == "herbalist":
        r.line(25, 8, 25, 29, INK, 2)
        r.line(26, 8, 26, 28, "8a7951")
        r.ellipse(22, 6, 8, 5, "688c56")
        r.rect(24, 7, 5, 1, "c1cd90")
        r.rect(7, 20, 7, 6, "735c42")
        r.rect(8, 20, 5, 2, "bb9c66")
        r.line(10, 14, 14, 23, "a69467")
        spark(r, 6, 9 + frame, "93be79")
    elif kind == "formation":
        r.poly([(8, 7 + bob), (16, 2 + bob), (23, 7 + bob)], "203b48")
        r.line(10, 7 + bob, 22, 7 + bob, "b19c6c")
        r.ellipse(21, 16 + bob, 8, 8, "c6a85f")
        r.ellipse(22, 17 + bob, 6, 6, "365e62")
        r.rect(24, 18 + bob, 2, 4, "d4bd7d")
        for x, y in [(4, 14), (26, 6), (6, 24)]:
            r.rect(x, y + frame % 2, 4, 4, "b89d62")
            r.rect(x + 1, y + 1 + frame % 2, 2, 2, "28474d")
    if frame == 3:
        follow_through = Raster(32, 32)
        follow_through.blit(r, 1, 0)
        return follow_through
    return r


def enemy(kind, frame):
    r = Raster(32, 32)
    shadow(r)
    bob = (0, -1, 0, 1)[frame]
    leg = frame % 2
    if kind in ("tide", "hound"):
        heavy = kind == "hound"
        shell = "727e72" if heavy else "3c7777"
        mid = "a5a27b" if heavy else "71b3a0"
        r.ellipse(8, 12 + bob, 21, 14, INK)
        r.ellipse(10, 13 + bob, 17, 11, shell)
        r.ellipse(4, 15 + bob, 12, 11, INK)
        r.rect(3, 19 + bob, 11, 6, shell)
        r.rect(1, 21 + bob, 6, 3, "324d54")
        r.poly([(7, 17 + bob), (7, 9 + bob), (13, 17 + bob)], INK)
        r.rect(8, 13 + bob, 2, 4, mid)
        r.pixel(6, 20 + bob, "f7c374")
        r.rect(4, 24 + bob, 3, 1, "e7dbad")
        for xx in (9, 20):
            r.rect(xx + leg, 23 + bob, 4, 6 - bob, INK)
            r.rect(xx + leg, 24 + bob, 3, 3, shell)
        r.line(27, 17 + bob, 30, 11 + bob, shell, 2)
        if heavy:
            for xx in (13, 18, 23):
                r.poly([(xx - 2, 17 + bob), (xx, 10 + bob), (xx + 4, 15 + bob), (xx + 2, 20 + bob)], mid)
                r.pixel(xx, 13 + bob, LIGHT)
        else:
            r.rect(12, 15 + bob, 10, 2, mid)
            r.rect(13, 18 + bob, 3, 2, "98c9b4")
    elif kind == "lantern":
        r.line(17, 4 + bob, 17, 7 + bob, GOLD)
        r.rect(10, 6 + bob, 13, 3, "63454b")
        r.ellipse(7, 8 + bob, 19, 18, INK)
        r.ellipse(8, 9 + bob, 17, 16, "bb5d62")
        r.rect(11, 10 + bob, 3, 13, "e99573")
        r.rect(19, 10 + bob, 3, 13, "8b414f")
        r.rect(9, 14 + bob, 5, 3, "272740")
        r.rect(18, 14 + bob, 5, 3, "272740")
        r.pixel(10, 15 + bob, "ffe0a4")
        r.pixel(19, 15 + bob, "ffe0a4")
        r.rect(14, 20 + bob, 4, 2, INK)
        r.rect(12, 24 + bob, 10, 2, "63454b")
        r.line(15, 26 + bob, 12 + frame, 30, "b77569")
        r.line(20, 26 + bob, 23 - frame, 30, "b77569")
    elif kind == "drowned":
        r.poly([(13, 11 + bob), (22, 12 + bob), (25, 26), (20, 28), (9, 26)], INK)
        r.poly([(13, 12 + bob), (21, 13 + bob), (22, 25), (11, 25)], "416b6d")
        r.rect(13, 18 + bob, 6, 2, "739180")
        r.rect(11, 26, 4, 4, "193540")
        r.rect(20, 26, 3, 4, "193540")
        r.ellipse(9, 4 + bob, 13, 13, INK)
        r.ellipse(10, 6 + bob, 10, 10, "70938a")
        r.rect(10, 6 + bob, 12, 4, "294d58")
        r.rect(10, 11 + bob, 3, 2, "bde3bf")
        r.rect(15, 11 + bob, 3, 2, "142b38")
        r.rect(11, 14 + bob, 5, 1, "314a4d")
        r.rect(5, 16 + bob, 10, 4, "365457")
        r.rect(3, 17 + bob, 5, 3, "8ba895")
        r.line(23, 10 + bob, 24, 24, "5f8772")
    elif kind == "yaksha":
        wing_y = 5 if frame % 2 else 10
        r.poly([(15, 14), (6, wing_y), (0, wing_y - 3), (4, 18), (11, 21)], INK)
        r.poly([(17, 14), (26, wing_y), (31, wing_y - 2), (28, 20), (21, 21)], INK)
        r.poly([(13, 14), (5, wing_y + 2), (7, 18), (12, 19)], "6b5988")
        r.poly([(20, 14), (28, wing_y + 2), (26, 18), (21, 19)], "7c6498")
        r.ellipse(11, 8 + bob, 11, 15, "806d91")
        r.ellipse(11, 6 + bob, 10, 10, INK)
        r.rect(12, 8 + bob, 8, 7, "a88fa2")
        r.poly([(12, 8 + bob), (10, 3 + bob), (15, 7 + bob)], "d7bf9c")
        r.poly([(18, 8 + bob), (21, 3 + bob), (20, 10 + bob)], "d7bf9c")
        r.pixel(12, 11 + bob, "e4e1b5")
        r.line(13, 22 + bob, 10, 27 + bob, "b0a38e", 2)
        r.line(20, 22 + bob, 21, 27 + bob, "b0a38e", 2)
    elif kind in ("drainer", "soul"):
        soul = kind == "soul"
        dark, mid, light = ("436b79", "81b9bd", "d1ded0") if soul else ("413750", "74607f", "c49d9c")
        r.poly([(12, 11 + bob), (22, 11 + bob), (26, 25 + bob), (22, 28 + bob),
                (17, 25 + bob), (11, 29 + bob), (7, 24 + bob)], INK)
        r.poly([(13, 12 + bob), (21, 12 + bob), (23, 25 + bob), (17, 23 + bob), (10, 26 + bob)], dark)
        r.poly([(14, 12 + bob), (17, 13 + bob), (15, 23 + bob), (11, 25 + bob)], mid)
        r.ellipse(10, 4 + bob, 14, 14, INK)
        r.ellipse(11, 5 + bob, 12, 12, mid)
        r.ellipse(12, 7 + bob, 8, 9, dark)
        if soul:
            r.rect(12, 8 + bob, 7, 7, light)
            r.rect(13, 13 + bob, 4, 1, "83b4b8")
            spark(r, 5, 13 + frame, "82bec1")
            r.rect(22, 30 - frame, 3, 1, "60929d")
        else:
            r.pixel(13, 10 + bob, "e9c5ad")
            r.pixel(17, 10 + bob, "e9c5ad")
            r.line(6, 12 + bob, 6, 29, "a48b74", 2)
            r.ellipse(2, 10 + bob, 8, 8, "9c677b")
            r.ellipse(4, 12 + bob, 4, 4, "e1af9b")
    elif kind == "rottenwood":
        r.poly([(10, 6 + bob), (22, 7 + bob), (26, 25), (20, 28), (9, 27), (6, 20)], INK)
        r.poly([(11, 7 + bob), (21, 8 + bob), (23, 25), (10, 25)], "63594b")
        r.rect(11, 9 + bob, 3, 14, "8a7656")
        r.rect(18, 10 + bob, 2, 14, "3e4941")
        r.rect(10, 13 + bob, 4, 2, "a8c48c")
        r.rect(18, 13 + bob, 4, 2, "a8c48c")
        r.rect(14, 18 + bob, 5, 3, "263d3e")
        for x, y in [(6, 17), (26, 14), (15, 7)]:
            r.line(x, y + 5, x - 4, y - 4, "817051", 2)
            r.rect(x - 5, y - 6, 5, 3, "638265")
        r.line(11, 25, 6 + leg, 29, "70634c", 3)
        r.line(21, 25, 25 - leg, 29, "70634c", 3)
    elif kind == "swordcorpse":
        r.poly([(12, 10 + bob), (24, 11 + bob), (27, 25), (20, 29), (9, 27)], INK)
        r.poly([(12, 12 + bob), (23, 13 + bob), (24, 25), (11, 26)], "5b6570")
        r.rect(12, 18 + bob, 11, 3, "a3a48d")
        r.rect(17, 14 + bob, 4, 11, "303d4b")
        r.ellipse(11, 3 + bob, 12, 12, INK)
        r.rect(12, 6 + bob, 9, 7, "91a49c")
        r.rect(11, 4 + bob, 13, 4, "47495a")
        r.rect(12, 9 + bob, 3, 2, "d4dfb7")
        r.rect(19, 9 + bob, 2, 2, "d4dfb7")
        r.rect(12, 13 + bob, 8, 2, "2d3846")
        r.line(5, 27, 8, 7 + bob, "192b3c", 3)
        r.line(6, 25, 9, 6 + bob, "b1c1bc", 2)
        r.line(3, 23, 11, 24, "9f8f68", 2)
        r.rect(12, 27, 4, 3, "243544")
        r.rect(21, 27, 4, 3, "243544")
    elif kind == "riverlord":
        r.poly([(29, 26), (23, 30), (14, 26), (11, 18), (4, 16), (3, 8), (12, 3), (20, 5), (22, 14)], INK)
        r.poly([(28, 25), (23, 27), (17, 24), (14, 15), (6, 14), (5, 9), (12, 5), (19, 6), (20, 15)], "9f4e54")
        r.poly([(9, 15), (14, 14), (16, 23), (23, 26), (22, 28), (15, 26)], "d8a06c")
        r.rect(4, 10, 11, 4, "c57260")
        r.pixel(8, 9, "ffe0a2")
        r.poly([(13, 6), (14, 1), (17, 5)], "d7bd88")
        r.poly([(7, 7), (4, 3), (11, 5)], "d7bd88")
        for xx, yy in [(18, 11), (20, 17), (22, 22)]:
            r.line(xx - 3, yy, xx, yy - 2, "dc8a69")
        r.line(5, 14, 0, 18, "d9be8a")
        if frame % 2:
            spark(r, 29, 9, "79c2bd")
            r.line(1, 26, 10, 26, "4d9b9f")
    elif kind == "mountainlord":
        r.ellipse(5, 9 + bob, 25, 20, INK)
        r.ellipse(7, 10 + bob, 22, 17, "787356")
        r.ellipse(2, 10 + bob, 19, 16, "4a5650")
        r.rect(1, 17 + bob, 14, 8, "a09b71")
        r.rect(0, 19 + bob, 4, 4, "536257")
        r.pixel(5, 16 + bob, "ffcf85")
        r.poly([(7, 12 + bob), (6, 4 + bob), (13, 11 + bob)], "d5c69a")
        r.poly([(15, 12 + bob), (21, 4 + bob), (20, 14 + bob)], "d5c69a")
        for x in (15, 21, 26):
            r.poly([(x - 2, 15 + bob), (x, 6 + bob), (x + 4, 12 + bob), (x + 3, 19 + bob)], "aba77b")
            r.pixel(x, 9 + bob, "e9dba7")
        r.rect(6 + leg, 25, 6, 5, "2e3e3e")
        r.rect(22 - leg, 25, 6, 5, "2e3e3e")
        r.rect(13, 25, 9, 3, "b09d6c")
    elif kind == "altar":
        r.rect(4, 25, 24, 5, INK)
        r.rect(5, 25, 22, 3, "657c75")
        r.rect(7, 21, 18, 5, "314f53")
        r.rect(8, 21, 16, 2, "a1a37e")
        r.rect(10, 14, 12, 8, "486862")
        r.rect(11, 15, 2, 6, "8b9c7c")
        r.rect(19, 15, 2, 6, "213d49")
        r.rect(8, 12, 16, 3, "b2aa7d")
        r.rect(7, 11, 18, 2, "263d47")
        r.rect(5, 9, 3, 12, "8b916f")
        r.rect(24, 9, 3, 12, "8b916f")
        r.rect(4, 8, 5, 3, "c6bd8d")
        r.rect(23, 8, 5, 3, "c6bd8d")
        flame(r, 15, 0 + frame % 2, "5d9ea7", "c4e2bd")
        spark(r, 6 + frame, 3 + frame % 3, "739e9f")
        r.rect(14, 16, 4, 4, "b9bb8e")
        r.rect(15, 17, 2, 2, "416964")
    elif kind == "boneemperor":
        r.poly([(12, 11), (22, 11), (29, 29), (24, 28), (19, 30), (10, 29), (6, 27)], INK)
        r.poly([(12, 13), (22, 13), (26, 27), (20, 28), (10, 27)], "5a4a70")
        r.poly([(14, 12), (18, 13), (20, 28), (13, 27)], "9b7c9a")
        r.rect(12, 20, 10, 2, "d5bd8b")
        r.ellipse(11, 4 + bob, 12, 11, INK)
        r.ellipse(12, 5 + bob, 10, 9, "d0d1b4")
        r.rect(12, 9 + bob, 3, 2, "334f5c")
        r.rect(18, 9 + bob, 3, 2, "334f5c")
        r.pixel(13, 9 + bob, "95d6c4")
        r.pixel(19, 9 + bob, "95d6c4")
        r.rect(15, 13 + bob, 4, 1, "384354")
        r.rect(10, 4 + bob, 14, 2, "bdac7b")
        for xx, yy in [(10, 1), (15, 0), (21, 1)]:
            r.rect(xx, yy + bob, 3, 5 - yy, "d8c594")
            r.pixel(xx + 1, yy + bob, "9dd1bd")
        r.line(5, 9, 5, 29, "817894", 2)
        flame(r, 5, 1, "7f9ec3", "c4dfd3")
        spark(r, 28, 10 + frame, "a49ac3")
    if frame >= 2:
        lunge = Raster(32, 32)
        lunge.blit(r, -1 if frame == 2 else 1, 0)
        return lunge
    return r


def icons():
    ids = ["qi", "gate", "stones", "insight", "pause", "speed", "sound", "muted", "relic", "sword", "shield", "heal", "fire", "ice", "lightning", "skull"]
    atlas = Raster(128, 32)
    info = {}
    for index, name in enumerate(ids):
        r = Raster(16, 16)
        if name == "qi":
            r.ellipse(3, 3, 10, 11, "78553a")
            r.ellipse(4, 4, 8, 9, "e4b75d")
            r.rect(6, 3, 4, 2, "f4d991")
            r.rect(7, 6, 2, 5, "fff0b8")
            r.pixel(4, 2, "9ec399")
            r.pixel(11, 1, "9ec399")
        elif name == "gate":
            r.rect(2, 5, 3, 9, "77968c")
            r.rect(11, 5, 3, 9, "77968c")
            r.poly([(0, 5), (8, 1), (15, 5)], "c0bc8c")
            r.rect(1, 5, 14, 2, "d7ca93")
            r.rect(6, 8, 4, 6, "b97f57")
        elif name == "stones":
            r.poly([(3, 8), (7, 3), (12, 4), (15, 9), (11, 14), (5, 13)], "405e6e")
            r.poly([(3, 8), (7, 3), (10, 7), (8, 12), (5, 13)], "89b6b3")
            r.poly([(10, 7), (12, 4), (15, 9), (11, 14), (8, 12)], "639290")
        elif name == "insight":
            r.rect(3, 2, 10, 12, "5b6058")
            r.rect(4, 3, 8, 10, "d5c58a")
            r.rect(6, 4, 4, 1, "786c51")
            r.rect(6, 7, 4, 1, "786c51")
            r.rect(6, 10, 3, 1, "786c51")
        elif name == "pause":
            r.rect(4, 3, 3, 10, "d8dcbe")
            r.rect(10, 3, 3, 10, "d8dcbe")
        elif name == "speed":
            r.poly([(2, 3), (8, 8), (2, 13)], "d8dcbe")
            r.poly([(8, 3), (14, 8), (8, 13)], "d8dcbe")
        elif name in ("sound", "muted"):
            r.rect(2, 6, 4, 5, "a6b8aa")
            r.poly([(5, 6), (9, 3), (9, 14), (5, 11)], "d8dcbe")
            if name == "sound":
                r.line(12, 5, 14, 7, "95b8ad")
                r.line(14, 7, 14, 10, "95b8ad")
                r.line(14, 10, 12, 12, "95b8ad")
            else:
                r.line(11, 6, 15, 11, "cb7b70")
                r.line(15, 6, 11, 11, "cb7b70")
        elif name == "relic":
            r.ellipse(2, 2, 12, 12, "7e6b49")
            r.ellipse(3, 3, 10, 10, "d5bb78")
            r.ellipse(5, 5, 6, 6, "3c7777")
            r.rect(7, 6, 2, 4, "a8d0b8")
        elif name == "sword":
            r.line(4, 12, 12, 3, "1a2b38", 3)
            r.line(5, 11, 13, 2, "d3dfc8", 2)
            r.line(3, 10, 7, 14, "d5b778", 2)
        elif name == "shield":
            r.poly([(2, 3), (8, 1), (14, 3), (13, 10), (8, 15), (3, 10)], "b6ac79")
            r.poly([(4, 4), (8, 3), (12, 4), (11, 9), (8, 12), (5, 9)], "4e7d7c")
            r.rect(7, 4, 2, 7, "97ba9c")
        elif name == "heal":
            r.rect(6, 2, 4, 12, "8fc48a")
            r.rect(2, 6, 12, 4, "8fc48a")
            r.rect(7, 3, 2, 8, "c3deb0")
        elif name == "fire":
            flame(r, 7, 1, "c76c50", "f2d08b")
        elif name == "ice":
            r.line(8, 1, 8, 15, "abd5d7")
            r.line(2, 4, 14, 12, "abd5d7")
            r.line(2, 12, 14, 4, "abd5d7")
            r.rect(6, 6, 5, 5, "d7ede0")
        elif name == "lightning":
            r.poly([(8, 1), (3, 9), (7, 9), (5, 15), (13, 6), (9, 6), (12, 1)], "c0a3e6")
        else:
            r.ellipse(3, 2, 11, 10, "c1c7ad")
            r.rect(4, 6, 3, 3, "2e4953")
            r.rect(10, 6, 3, 3, "2e4953")
            r.rect(5, 10, 7, 4, "9ba68f")
            for xx in (6, 9):
                r.rect(xx, 12, 1, 3, "3b555a")
        x, y = index % 8 * 16, index // 8 * 16
        atlas.blit(r, x, y)
        info[name] = {"x": x, "y": y, "w": 16, "h": 16}
    atlas.save(OUT / "icons.png")
    (OUT / "icons.json").write_text(json.dumps(info, indent=2) + "\n")


def expanded_region(kind, original):
    """Twelve-column courtyards with a visible, region-specific stronghold."""
    r = Raster(512, 288, "152735")
    for y in range(288):
        for x in range(512):
            sx, sy = min(383, x * 384 // 512), min(215, y * 216 // 288)
            offset = (sy * original.w + sx) * 4
            r.pixel(x, y, original.data[offset:offset + 4])
    rng = random.Random({"wharf": 101, "terrace": 102, "tomb": 103}[kind])
    stone, hi, seam = {"wharf": ("645344", "947956", "403b35"), "terrace": ("4f7067", "86a186", "2b494b"), "tomb": ("354854", "607378", "1f303b")}[kind]
    r.rect(89, 56, 390, 168, "101c28")
    r.rect(91, 58, 386, 164, hi)
    for lane in range(5):
        for col in range(12):
            xx, yy = 92 + col * 32, 60 + lane * 32
            r.rect(xx, yy, 31, 31, stone)
            r.line(xx, yy + 31, xx + 31, yy + 31, seam)
            r.line(xx + 31, yy, xx + 31, yy + 31, seam)
            if kind == "wharf":
                for dy in (6, 14, 22):
                    r.line(xx + 1, yy + dy, xx + 30, yy + dy, seam)
                    r.line(xx + 4, yy + dy + 1, xx + rng.randrange(10, 28), yy + dy + 1, hi)
            else:
                for _ in range(4):
                    r.rect(xx + rng.randrange(3, 26), yy + rng.randrange(3, 27), 3, 1, hi)
                r.line(xx + 26, yy + 2, xx + 23, yy + 8, seam)
            if col == 0:
                r.rect(xx + 4, yy + 7, 24, 18, "233d48")
                r.line(xx + 5, yy + 25, xx + 27, yy + 25, "aa976c")
    # The sanctuary is visibly behind the five defense seals, not scenery at spawn.
    r.rect(2, 51, 84, 181, "142633")
    r.rect(7, 61, 72, 161, "425951" if kind != "tomb" else "303d4a")
    r.rect(15, 67, 56, 147, "263c42")
    for x in (14, 65):
        r.rect(x, 63, 7, 159, "96855d")
        r.rect(x + 2, 65, 2, 153, "d1b379")
    for y in (74, 111, 148):
        r.rect(25, y, 33, 22, "20303d")
        for x in (28, 41, 54):
            r.rect(x, y + 3, 2, 15, "c38b53" if kind == "wharf" else "78bcb3")
        r.rect(24, y + 23, 37, 3, "897856")
    for y, width in ((78, 88), (67, 64), (56, 40)):
        x = 44 - width // 2
        r.poly([(x, y + 13), (x + 7, y + 8), (44, y), (x + width - 7, y + 8), (x + width, y + 13)], "172936")
        r.line(x + 2, y + 13, x + width - 2, y + 13, "bea575")
        r.rect(43, y + 2, 3, 3, "dcc688")
    r.rect(27, 183, 34, 39, "121e2d")
    r.rect(29, 186, 30, 33, "395a5b")
    for y in range(222, 239, 3):
        r.rect(13 - (y - 222) // 3, y, 65 + (y - 222) // 3 * 2, 2, hi)
    if kind == "wharf":
        lantern(r, 6, 87); lantern(r, 72, 87)
        r.rect(31, 190, 24, 2, "c8a76c")
        r.rect(42, 183, 2, 32, "b19066")
    elif kind == "terrace":
        for y in (85, 121, 157):
            r.poly([(4, y), (12, y), (12, y + 22), (8, y + 18), (4, y + 22)], "559a7b")
        r.ellipse(34, 193, 20, 20, "66aaa0")
        r.ellipse(38, 197, 12, 12, "bed9b0")
    else:
        for y in (83, 121, 158):
            flame(r, 8, y, "4e979c", "b1e0cb")
        r.poly([(34, 212), (34, 193), (44, 187), (54, 193), (54, 212)], "83948b")
        r.rect(40, 197, 8, 11, "2e5460")
    return r


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    import importlib.util, shutil

    spec = importlib.util.spec_from_file_location(
        "van_dao_cultivator_art", Path(__file__).with_name("generate_cultivators.py")
    )
    detail = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(detail)

    # Supply the current generator module even when a test imports it under an alias.
    class Art:
        pass

    art = Art()
    for name in ("Raster", "hero", "lantern", "flame"):
        setattr(art, name, globals()[name])
    # High-resolution scene paintings are retained authoring inputs, never replaced
    # by the earlier recolored tile courtyards when regenerating procedural actors.
    retained=Path(__file__).resolve().parents[1]/'web/assets'
    for name in ('wharf.png','terrace.png','tomb.png','scenes.json','garden.png','crops.png','crops.json','actors.json','actors_manifest.json','objectives.png','objectives.json','heroes_idle.png','heroes_attack.png','heroes_skill.png','heroes_ultimate.png','enemies_idle.png','enemies_attack.png','enemies_skill.png'):
        source=retained/name;target=OUT/name
        if source.resolve()!=target.resolve():shutil.copyfile(source,target)
    if (retained/'motion').is_dir() and (OUT/'motion').resolve()!=(retained/'motion').resolve():
        shutil.copytree(retained/'motion',OUT/'motion',dirs_exist_ok=True)
    title().save(OUT/'title.png')
    hero_ids = [
        "gatherer",
        "sword",
        "fire",
        "frost",
        "monk",
        "lightning",
        "herbalist",
        "formation",
    ]
    enemy_ids = [
        "tide",
        "lantern",
        "drowned",
        "hound",
        "yaksha",
        "drainer",
        "soul",
        "rottenwood",
        "swordcorpse",
        "riverlord",
        "mountainlord",
        "boneemperor",
        "altar",
    ]
    atlas, info = Raster(128, 32 * (len(hero_ids) + len(enemy_ids))), {}
    for row, kind in enumerate(hero_ids + enemy_ids):
        for frame in range(4):
            image = hero(kind, frame) if kind in hero_ids else enemy(kind, frame)
            atlas.blit(image, frame * 32, row * 32)
        info[kind] = {"x": 0, "y": row * 32, "w": 32, "h": 32, "frames": 4}
    for alias, key in {
        "miao": "tide",
        "river_lord": "riverlord",
        "mountain_lord": "mountainlord",
        "bone_emperor": "boneemperor",
    }.items():
        info[alias] = info[key]
    atlas.save(OUT / "sprites.png")
    (OUT / "sprites.json").write_text(json.dumps(info, indent=2) + "\n")
    icons()
    detail.generate(art, OUT)
    (OUT / "ART_LICENSE.txt").write_text(
        "VAN DAO raster assets: retained image-generated RPG scenes, artifacts, actors and botany; procedural fallback sprites and icons.\nArtwork is original. VT323 is separately bundled under its SIL Open Font License.\nSee the repository license for redistribution terms.\n"
    )
    print(f"Generated original pixel artwork in {OUT}")


if __name__ == "__main__":
    main()
