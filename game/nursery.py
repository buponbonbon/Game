"""A short three-lane seed run; separate from the nine campaign encounters."""

NURSERY = dict(
    id="garden-defense",
    name="Nursery Defense",
    region="wharf",
    index=0,
    chapter=0,
    mode="nursery",
    gate=6,
    boss=None,
    next=None,
    tutorial=False,
    description="Defend three herb beds. Each can withstand two breaches; protect more beds for better seed rewards.",
    mechanic="Three Nursery Beds",
    duration=170,
    duration_label="2-3 min",
    stronghold="Herbal Pavilion",
    hp_multiplier=1.0,
    music_theme="wharf_1",
    reward={"stones": 0, "insight": 0},
    guardian={
        "name": "Seed-Ward Lantern",
        "description": "Each active lane sweeps once.",
    },
    ritual={
        "name": "Garden Shelter",
        "description": "35 Qi / 30s cooldown: all living cultivators receive a 35-point shield for 6 seconds.",
    },
    phases=[
        dict(id="setup", name="Plant the Defense", end_wave=2),
        dict(id="pressure", name="Raiding Party", end_wave=4),
        dict(id="onslaught", name="The Last Harvest", end_wave=6),
    ],
    waves=[
        dict(
            at=at,
            spawns=[
                dict(
                    type=kind,
                    lane=lane,
                    count=count,
                    gap=gap,
                    swarm=count >= 4,
                    elite_count=elite,
                )
                for lane in lanes
            ],
        )
        for at, kind, lanes, count, gap, elite in [
            (10, "tide", [2], 2, 2, 0),
            (28, "tide", [1, 3], 2, 2, 0),
            (49, "lantern", [1, 2, 3], 2, 1.8, 0),
            (72, "drowned", [1, 2, 3], 2, 1.8, 0),
            (96, "tide", [1, 2, 3], 4, 0.8, 0),
            (122, "drowned", [1, 2, 3], 5, 0.55, 1),
        ]
    ],
    final_assault_count=15,
    water_lanes=[],
    blocked_tiles=[],
    nodes=[],
    mist_lanes=[],
    altars=[],
)
NURSERY["enemy_count"] = sum(s["count"] for w in NURSERY["waves"] for s in w["spawns"])
