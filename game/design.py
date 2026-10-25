"""Version 1.2 content contracts: costs, exact grid geometry and talent trees."""

from math import hypot

MANA = {
    "gatherer": (110, 60, 2.8, 8, 85, 25, 60),
    "sword": (100, 60, 3.0, 16, 65, 20, 35),
    "fire": (130, 80, 3.2, 24, 95, 35, 50),
    "frost": (120, 70, 3.2, 18, 80, 25, 45),
    "monk": (90, 60, 2.8, 14, 70, 20, 45),
    "lightning": (140, 80, 3.5, 24, 100, 40, 55),
    "herbalist": (130, 85, 3.8, 16, 90, 25, 50),
    "formation": (150, 90, 3.4, 22, 110, 35, 60),
}
# Scope is measured between tile centers; circles are Euclidean, not vague squares.
GEOMETRY = {
    "gatherer": (("self", 0, 1), ("self", 0, 1), ("self", 0, 1)),
    "sword": (("line", 5.5, 1), ("line", 3.5, 3), ("lane", 12, 3)),
    "fire": (("line", 4.8, 1), ("line", 4.8, 1), ("lane", 12, 3)),
    "frost": (("line", 5, 1), ("circle", 2, 1), ("lane", 12, 99)),
    "monk": (("line", 1, 1), ("line", 1.25, 99), ("lane", 12, 99)),
    "lightning": (("line", 5.2, 3), ("line", 5.2, 3), ("lane", 12, 5)),
    "herbalist": (("circle", 3, 1), ("circle", 3, 1), ("field", 12, 99)),
    "formation": (("circle", 1.5, 99), ("circle", 2.5, 3), ("circle", 2, 99)),
}
SPECIALS = {
    "gatherer": (
        (
            "Shared Breath",
            "Orb collection restores 4 mana to each ally within radius 1.5 (3x3 cells).",
            {"shared_breath": 4},
        ),
        (
            "Celestial Treasury",
            "While Yun lives, shared Qi capacity rises by 40; it still cannot overflow.",
            {"treasury_cap": 40},
        ),
    ),
    "sword": (
        (
            "Verdant Torrent",
            "Every third landed basic sword restores 6 mana.",
            {"third_mana": 6},
        ),
        (
            "Wind Through Bamboo",
            "Deal 12% more damage while above half mana.",
            {"high_mana_damage": 0.12},
        ),
    ),
    "fire": (
        (
            "Undying Cinder",
            "Basic Ember burn lasts 5s instead of 3s; same-source burn does not stack.",
            {"burn_duration": 5},
        ),
        (
            "Lotus Sanctuary",
            "Furnace splash radius becomes 1.15, reaching immediately adjacent lanes.",
            {"skill_radius": 1.15},
        ),
    ),
    "frost": (
        (
            "Winter Without End",
            "Frost freeze durations increase 25%; boss reductions still apply.",
            {"cc_duration": 1.25},
        ),
        (
            "Twin Mirrors",
            "Ice Mirror shields the two lowest-HP allies inside its radius-2 circle.",
            {"shield_targets": 2},
        ),
    ),
    "monk": (
        (
            "Golden Core Body",
            "Take 5% less damage from every type after armor.",
            {"talent_reduction": 0.05},
        ),
        (
            "Earth Dragon Echo",
            "Staff skill reaches adjacent lanes inside the forward radius-1.25 arc.",
            {"staff_arc": True},
        ),
    ),
    "lightning": (
        (
            "Endless Sky",
            "Chain jumps reach radius 1.75 instead of 1.25.",
            {"chain_range": 1.75},
        ),
        (
            "Tribulation Siphon",
            "Consuming three Conductive marks restores 5 mana.",
            {"conductive_mana": 5},
        ),
    ),
    "herbalist": (
        (
            "Spring Everlasting",
            "Garden also heals a second injured ally for 70% power inside radius 3.",
            {"heal_targets": 2},
        ),
        (
            "Jade Rain",
            "Clear-Pulse fallback shield becomes 70, within the same radius-3 circle.",
            {"cleanse_shield": 70},
        ),
    ),
    "formation": (
        (
            "Living Array",
            "Passive formation radius becomes 2 (13 tile centers), instead of 1.5 (3x3).",
            {"aura_range": 2},
        ),
        (
            "Dao Confluence",
            "Circuit also restores 8 mana to its three chosen allies within radius 2.5.",
            {"circuit_mana": 8},
        ),
    ),
}
from .performances import PERFORMANCES, lines

VOICELINES = {hero: lines(hero) for hero in PERFORMANCES}


def geometry(shape, radius, targets):
    if shape in ("circle", "front_circle"):
        offsets = [
            [dx, dy]
            for dy in range(-5, 6)
            for dx in range(-12, 13)
            if hypot(dx, dy) <= radius and (shape != "front_circle" or dx >= 0)
        ]
        label = f'{"Forward circle" if shape=="front_circle" else "Circle"} radius {radius}: {len(offsets)} tile centers, clipped at board edges.'
    elif shape == "field":
        offsets = []
        label = "All 5 lanes and all deployment cells."
    elif shape == "self":
        offsets = [[0, 0]]
        label = "This hero cell only."
    else:
        offsets = [[dx, 0] for dx in range(1, 13) if dx <= radius]
        label = "This lane only, " + (
            f"forward reach {radius} tiles."
            if shape == "line"
            else "all enemies in the lane."
        )
    return dict(
        shape=shape, radius=radius, targets=targets, offsets=offsets, description=label
    )


def enrich(heroes, enemies, stages, regions):
    heroes["gatherer"].update(orb_interval=10.0, orb_value=20)
    heroes["gatherer"]["branches"]["A"]["stats"] = {"orb_interval": 8.0}
    heroes["gatherer"]["branches"]["A"][
        "description"
    ] = "Generate one 20-Qi orb every 8s instead of 10s."
    heroes["gatherer"]["branches"]["B"]["stats"] = {"orb_value": 24}
    heroes["gatherer"]["branches"]["B"][
        "description"
    ] = "Orb value increases from 20 to 24; 10s interval remains."
    for id, h in heroes.items():
        maximum, initial, regen, skill_cost, ult_cost, qi_cost, ult_cd = MANA[id]
        h.update(
            mana_max=maximum,
            mana_initial=initial,
            mana_regen=regen,
            passive_mana=8 if id == "gatherer" else 6 if id == "herbalist" else 0,
        )
        basic, skill, ult = GEOMETRY[id]
        h["basic"] = {
            "name": (
                "Herb Garden"
                if id == "herbalist"
                else (
                    "Linked Meridian"
                    if id == "formation"
                    else "Gathering Breath" if id == "gatherer" else "Basic attack"
                )
            ),
            "geometry": geometry(*basic),
            "cooldown": h.get("heal_interval", h["interval"]),
            "mana_cost": h["passive_mana"],
            "scaling": (
                "100% ATK"
                if h["damage"]
                else (
                    "20 Qi / 10s; diminishing returns"
                    if id == "gatherer"
                    else (
                        "16% max HP heal"
                        if id == "herbalist"
                        else "+8% ally attack speed"
                    )
                )
            ),
        }
        h["skill"].update(
            mana_cost=0 if id == "gatherer" else skill_cost, geometry=geometry(*skill)
        )
        if id == "gatherer":
            h["skill"].update(
                name="Frugal Practice",
                description="First three orbs gain +5 Qi if a Formation Adept stands within radius 1.5 (3x3 cells).",
                cooldown=0,
                geometry=geometry("circle", 1.5, 1),
            )
        h["ultimate"].update(
            mana_cost=ult_cost,
            qi_cost=qi_cost,
            cooldown=ult_cd,
            resonance_cost=100,
            geometry=geometry(*ult),
        )
        h["voice"] = {"summon": VOICELINES[id][0], "ultimate": VOICELINES[id][1]}
        h["talents"] = {}
        for branch in ("A", "B"):
            special = SPECIALS[id][0 if branch == "A" else 1]
            h["talents"][branch] = [
                {
                    "id": branch + "1",
                    "rank": 1,
                    "cost": 20,
                    "kind": "stat",
                    "name": "Rooted Body" if branch == "A" else "Deep Reservoir",
                    "description": "+6% max HP." if branch == "A" else "+10 max mana.",
                },
                {
                    "id": branch + "2",
                    "rank": 2,
                    "cost": 30,
                    "kind": "stat",
                    "name": "Tempered Art" if branch == "A" else "Returning Breath",
                    "description": (
                        "+5% ATK and healing power."
                        if branch == "A"
                        else "+12% mana regeneration."
                    ),
                },
                {
                    "id": branch + "3",
                    "rank": 3,
                    "cost": 45,
                    "kind": "special",
                    "name": h["branches"][branch]["name"],
                    "description": h["branches"][branch]["description"],
                },
                {
                    "id": branch + "4",
                    "rank": 4,
                    "cost": 60,
                    "kind": "stat",
                    "name": (
                        "Cultivated Vessel" if branch == "A" else "Flowing Meridian"
                    ),
                    "description": (
                        "+4% HP and +8% mana regeneration."
                        if branch == "A"
                        else "Automatic skill cooldown -8%."
                    ),
                },
                {
                    "id": branch + "5",
                    "rank": 5,
                    "cost": 90,
                    "kind": "special",
                    "name": special[0],
                    "description": special[1],
                    "stats": special[2],
                },
            ]
    ranges = {
        "tide": ("self", 0, 1),
        "lantern": ("circle", 1.5, 99),
        "drowned": ("self", 0, 1),
        "hound": ("line", 1.5, 1),
        "yaksha": ("line", 12, 1),
        "drainer": ("field", 12, 1),
        "soul": ("line", 0.8, 1),
        "rottenwood": ("circle", 1.2, 99),
        "swordcorpse": ("self", 0, 1),
        "riverlord": ("lane", 12, 99),
        "mountainlord": ("lane", 12, 99),
        "boneemperor": ("lane", 12, 99),
    }
    descriptions = {
        "drowned": "At high tide, fades during the last 2.4s of each 7s cycle. Fire/lightning or reveal can still target it. Melee silences its one target for 0.65s.",
        "lantern": "Shield all enemies within radius 1.5 (3x3 cell centers) for 25. Death burst radius 0.8, 30 Spirit damage.",
        "hound": "Telegraph 1.1s, then rush 1.5 cells left. Stops at the first hero crossed.",
        "yaksha": "Flies through blockers 4.5s per 7s cycle; dives at a support in its current lane only.",
        "drainer": "Channels 1s, then drains up to 30 shared Qi from any position on the board. Any damaging hit interrupts.",
        "soul": "Phases for the last 1.6s of each 5.5s cycle. A melee hit curses its one target; 3 stacks slow attacks 20% for 8s.",
        "rottenwood": "Warns 1s, then creates a radius-1.2 spore circle: 10 Wood damage/s for 3s, attack speed -15%.",
        "swordcorpse": "Absorbs light projectiles for 1s; each absorbed blade adds 14 to its next same-lane melee hit.",
        "riverlord": "Warns 1.8s; hits its lane and the lane immediately below for 55+22xphase Water damage.",
        "mountainlord": "Warns 2s; hits both lanes with the most heroes for 60+20xphase Physical damage. Plates take hits separately.",
        "boneemperor": "Warns 1.8s; marks 1/2/3 consecutive lanes by phase for 50+25xphase Spirit damage. Three altars resurrect souls after 6s.",
    }
    for id, e in enemies.items():
        e["basic_geometry"] = geometry("line", e["range"], 1)
        e["abilities"][0].update(
            geometry=geometry(*ranges[id]),
            cooldown=e.get("ability_interval", 0),
            windup=(
                2
                if id == "mountainlord"
                else (
                    1.8
                    if e.get("boss")
                    else (
                        1.1
                        if id == "hound"
                        else 1 if id in ("drainer", "rottenwood") else 0
                    )
                )
            ),
        )
        if id in descriptions:
            e["abilities"][0]["description"] = descriptions[id]
        e["basic_geometry"][
            "description"
        ] = f"This lane only, reach {e['range']} tiles to the left; one target."
        if e["abilities"][0]["geometry"]["shape"] == "self":
            e["abilities"][0]["geometry"][
                "description"
            ] = "This enemy only; no area damage."
        elif e["abilities"][0]["geometry"]["shape"] == "line":
            e["abilities"][0]["geometry"][
                "description"
            ] = f"This lane only, to the left, reach {e['abilities'][0]['geometry']['radius']} tiles."
    for id, description in {
        "riverlord": "Two full lanes: the boss lane and the lane immediately below (wraps at the bottom).",
        "mountainlord": "Two full lanes with the most allied heroes; ties prefer the lower lane. Telegraph lasts 2s.",
        "boneemperor": "One, two or three consecutive full lanes by boss phase; the exact lanes are marked 1.8s before impact.",
    }.items():
        enemies[id]["abilities"][0]["geometry"].update(
            shape="lanes", description=description
        )
    for s in stages.values():
        s["hp_multiplier"] = round(1.05 ** s["index"], 5)
        s["elite_multiplier"] = 1.25
        n = len(s["waves"])
        s["phases"] = [
            {
                "id": "setup",
                "name": "Quiet Before the Storm",
                "start_wave": 1,
                "end_wave": max(3, n // 3),
            },
            {
                "id": "pressure",
                "name": "Corruption Rises",
                "start_wave": max(3, n // 3) + 1,
                "end_wave": max(6, n * 2 // 3),
            },
            {
                "id": "onslaught",
                "name": "Heaven-Shaking Assault",
                "start_wave": max(6, n * 2 // 3) + 1,
                "end_wave": n,
            },
        ]
        for i, w in enumerate(s["waves"]):
            phase = (
                "setup"
                if i < s["phases"][0]["end_wave"]
                else "pressure" if i < s["phases"][1]["end_wave"] else "onslaught"
            )
            w["phase"] = phase
            for j, spawn in enumerate(w["spawns"]):
                if enemies[spawn["type"]]["boss"]:
                    continue
                # Rank placement is authored and deterministic, never tied to rendering.
                spawn["elite_count"] = (
                    0
                    if phase == "setup"
                    else min(
                        spawn["count"],
                        1 if phase == "pressure" else max(1, (spawn["count"] + 1) // 2),
                    )
                )
                spawn["captain"] = (
                    phase == "onslaught" and i == n - 1 and j == 0 and not s["boss"]
                )
        s["guardian"] = {
            "wharf": "Jade River Ark",
            "terrace": "Heaven Sword Array",
            "tomb": "Soul-Sealing Bell",
        }[s["region"]]
        s["ritual"] = {
            "wharf": {
                "name": "Calm the River",
                "description": "Spend 35 Qi to calm high tide for 12s. Flood tiles become safe.",
            },
            "terrace": {
                "name": "Purify the Ley",
                "description": "Spend 35 Qi to purify all 3 nodes, lock wind 10s, and restore 15 mana near nodes.",
            },
            "tomb": {
                "name": "Soul Mirror",
                "description": "Spend 35 Qi to reveal ghosts, prevent resurrection 6s, and cleanse allied curses.",
            },
        }[s["region"]]
        s["ritual"].update(cost=35, cooldown=30)

        # A coordinated final assault reaches all five lanes within 0.6 seconds.
        local = s["index"] % 3
        common = {"wharf": "tide", "terrace": "tide", "tomb": "soul"}[s["region"]]
        support = {
            "wharf": "lantern" if local != 1 else "drowned",
            "terrace": "yaksha",
            "tomb": "swordcorpse",
        }[s["region"]]
        final = s["waves"][-1]
        leaders = [spawn for spawn in final["spawns"] if enemies[spawn["type"]]["boss"]]
        surge = []
        for lane in range(5):
            surge.append(
                dict(
                    type=common,
                    swarm=True,
                    lane=lane,
                    count=6 + local,
                    gap=0.48,
                    delay=lane * 0.15,
                    elite_count=1 if local < 2 else 2,
                    captain=not s["boss"] and lane == 2,
                )
            )
            # Heavy tomb corpses reinforce alternating lanes; souls fill the rest.
            kind = common if s["region"] == "tomb" and lane % 2 == 0 else support
            surge.append(
                dict(
                    type=kind,
                    swarm=kind == common,
                    lane=lane,
                    count=1 + int(local == 2),
                    gap=0.9,
                    delay=lane * 0.15 + 0.3,
                    elite_count=0,
                    captain=False,
                )
            )
        final.update(spawns=leaders + surge, phase="onslaught", all_lanes=True)
        s["final_assault_count"] = sum(x["count"] for x in final["spawns"])
        s["enemy_count"] = sum(x["count"] for w in s["waves"] for x in w["spawns"])
        s["music_theme"] = s["id"].replace("-", "_")
