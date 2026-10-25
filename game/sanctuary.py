"""HD sanctuary layout and cosmetic save state; battle rules stay independent."""

from copy import deepcopy
import math

FACILITIES = [
    dict(
        id="campaign",
        name="Grand Hall",
        npc="frost",
        keeper="Bing Ruo",
        title="Keeper of the Gates",
        x=256,
        y=97,
        action="campaign",
        greeting="The mountain is quiet, but the realms still need us. Choose the gate you wish to defend.",
        offer="Open the Campaign",
    ),
    dict(
        id="training",
        name="Bamboo Court",
        npc="sword",
        keeper="Shen Zhu",
        title="Sword Instructor",
        x=120,
        y=113,
        action="roster",
        greeting="A steady stance comes before a brilliant blade. Study your techniques, then choose your own path.",
        offer="Study Talents & Skills",
    ),
    dict(
        id="archive",
        name="Jade Archive",
        npc="formation",
        keeper="Zhen Luo",
        title="Keeper of Records",
        x=408,
        y=110,
        action="archive",
        greeting="Every enemy leaves a pattern. Read it carefully, and even an old defeat becomes a lesson.",
        offer="Read the Bestiary",
    ),
    dict(
        id="alchemy",
        name="Alchemy Pavilion",
        npc="herbalist",
        keeper="Mu Qing",
        title="Sect Alchemist",
        x=112,
        y=178,
        action="Alchemy",
        greeting="The cauldron is ready. Bring me herbs from the fields, and we shall prepare something for your next journey.",
        offer="Brew Preparations",
    ),
    dict(
        id="garden",
        name="Spirit Fields",
        npc="gatherer",
        keeper="Little Daoist Yun",
        title="Garden Apprentice",
        x=171,
        y=207,
        action="Garden",
        greeting="Look! The herbs are coming along. They grow after our expeditions, so there is no need to rush back while you are away.",
        offer="Tend the Garden",
    ),
    dict(
        id="merchant",
        name="Lantern Market",
        npc="fire",
        keeper="Hong Lian",
        title="Lantern Broker",
        x=410,
        y=184,
        action="Merchant",
        greeting="Seeds for tomorrow, a lantern for tonight? A well-kept sect should have a little color in its life.",
        offer="Browse the Market",
    ),
    dict(
        id="missions",
        name="Commission Board",
        npc="monk",
        keeper="Jin Shan",
        title="Keeper of Vows",
        x=183,
        y=165,
        action="missions",
        greeting="A sect grows by the promises it keeps. Take a commission, follow its progress, and return for your reward.",
        offer="Take a Commission",
    ),
    dict(
        id="trials",
        name="Heaven Gate",
        npc="lightning",
        keeper="Lei Xun",
        title="Trial Warden",
        x=405,
        y=232,
        action="trials",
        greeting="Ready for a different kind of challenge? The gate holds trials of escort, protection and honor. Your campaign can wait for you.",
        offer="Enter Regional Trials",
    ),
]
FACILITY_IDS = {f["id"] for f in FACILITIES}
AVATARS = [
    dict(id="sword", name="Shen Zhu", realm=0),
    dict(id="gatherer", name="Little Daoist Yun", realm=0),
    dict(id="herbalist", name="Mu Qing", realm=1),
]
SANCTUARY = dict(
    width=512,
    height=288,
    spawn=dict(x=256, y=232),
    speed=63,
    cell=8,
    facilities=FACILITIES,
    avatars=AVATARS,
    walkways=[
        [
            [219, 91],
            [297, 91],
            [318, 109],
            [355, 122],
            [377, 148],
            [381, 172],
            [354, 192],
            [323, 215],
            [307, 231],
            [204, 231],
            [183, 218],
            [147, 196],
            [127, 174],
            [135, 149],
            [155, 124],
            [200, 106],
        ],
        [[110, 101], [151, 102], [204, 108], [205, 122], [158, 123], [110, 116]],
        [[42, 81], [112, 75], [142, 86], [151, 101], [126, 111], [65, 102]],
        [[330, 108], [370, 100], [414, 89], [430, 103], [385, 125], [352, 138]],
        [[399, 80], [446, 72], [470, 83], [447, 96], [418, 106]],
        [[100, 160], [128, 157], [151, 171], [144, 190], [119, 185], [100, 179]],
        [[25, 155], [77, 145], [110, 160], [113, 174], [84, 177], [41, 168]],
        [[357, 154], [393, 155], [417, 169], [415, 188], [383, 190], [361, 178]],
        [[403, 157], [446, 157], [484, 168], [468, 182], [416, 181]],
        [[132, 189], [169, 183], [195, 207], [190, 229], [162, 229], [143, 214]],
        [
            [43, 204],
            [100, 189],
            [162, 199],
            [176, 219],
            [152, 239],
            [85, 237],
            [47, 224],
        ],
        [
            [315, 210],
            [355, 190],
            [399, 206],
            [422, 222],
            [419, 245],
            [379, 249],
            [352, 227],
        ],
        [[385, 208], [426, 203], [454, 220], [451, 239], [415, 248], [381, 240]],
        [[211, 226], [303, 226], [307, 248], [287, 264], [223, 264], [205, 245]],
    ],
    blockers=[dict(x=148, y=125, w=48, h=30), dict(x=20, y=195, w=111, h=39)],
    fountain=dict(x=256, y=150, rx=39, ry=20),
    style="HD-2D",
)


def inside_polygon(x, y, polygon):
    inside = False
    j = len(polygon) - 1
    for i, (ax, ay) in enumerate(polygon):
        bx, by = polygon[j]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            inside = not inside
        j = i
    return inside


def walkable(x, y, radius=3):
    if (
        not math.isfinite(x)
        or not math.isfinite(y)
        or not 5 < x < 507
        or not 74 < y < 251
    ):
        return False
    for dx, dy in ((0, 0), (radius, 0), (-radius, 0), (0, radius), (0, -radius)):
        if not any(inside_polygon(x + dx, y + dy, p) for p in SANCTUARY["walkways"]):
            return False
    f = SANCTUARY["fountain"]
    if ((x - f["x"]) / (f["rx"] + radius)) ** 2 + (
        (y - f["y"]) / (f["ry"] + radius)
    ) ** 2 < 1:
        return False
    if any(
        b["x"] - radius < x < b["x"] + b["w"] + radius
        and b["y"] - radius < y < b["y"] + b["h"] + radius
        for b in SANCTUARY["blockers"]
    ):
        return False
    return True


def new_hub():
    return dict(
        avatar="sword",
        x=256,
        y=232,
        visited=[],
        tracked=None,
        tracked_cycle=0,
        help_seen=False,
    )


def normalize_hub(raw, realm=0):
    h = new_hub()
    if not isinstance(raw, dict):
        return h
    allowed = {a["id"] for a in AVATARS if a["realm"] <= realm}
    if isinstance(raw.get("avatar"), str) and raw["avatar"] in allowed:
        h["avatar"] = raw["avatar"]
    x, y = raw.get("x"), raw.get("y")
    if all(
        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
        for v in (x, y)
    ) and walkable(x, y):
        h.update(x=round(x, 2), y=round(y, 2))
    h["visited"] = (
        [f["id"] for f in FACILITIES if f["id"] in raw.get("visited", [])]
        if isinstance(raw.get("visited"), list)
        else []
    )
    h["tracked"] = (
        raw.get("tracked")
        if isinstance(raw.get("tracked"), str) and len(raw["tracked"]) <= 40
        else None
    )
    h["tracked_cycle"] = (
        max(0, min(999999, raw.get("tracked_cycle", 0)))
        if isinstance(raw.get("tracked_cycle"), int)
        and not isinstance(raw.get("tracked_cycle"), bool)
        else 0
    )
    h["help_seen"] = raw.get("help_seen") is True
    return h
