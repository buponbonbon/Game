"""Optional objectives on existing regional maps; no campaign unlocks depend on them."""

from copy import deepcopy


def build_trials(stages):
    specs = [
        (
            "trial-caravan",
            "wharf-2",
            "Lantern Caravan",
            "wharf-3",
            "escort",
            "Escort the jade caravan to column 8. A fighter within radius 1.5 lets it advance; after the raiders are cleared it moves freely. Raiders within radius 0.9 drain 12 HP/s each, capped at 24; a nearby fighter halves this damage. Losing the caravan ends the trial.",
            [
                ("tide", 2, 2),
                ("lantern", 1, 2),
                ("drowned", 3, 3),
                ("tide", 2, 4),
                ("lantern", 2, 4),
                ("drowned", 2, 5),
            ],
        ),
        (
            "trial-beacons",
            "terrace-1",
            "Twin Jade Beacons",
            "terrace-1",
            "beacons",
            "Keep both jade beacons alive at row 2/column 3 and row 4/column 3. Raiders within radius 0.9 drain 12 HP/s each, capped at 24 per beacon. A fighter within radius 1.5 halves this damage. Losing either beacon ends the trial.",
            [
                ("tide", 1, 2),
                ("hound", 3, 2),
                ("lantern", 1, 2),
                ("rottenwood", 3, 2),
                ("hound", 1, 3),
                ("drainer", 3, 4),
            ],
        ),
        (
            "trial-oath",
            "tomb-2",
            "Oath of the Bone Court",
            "tomb-2",
            "oath",
            "Court ward reduces all incoming hero damage by 25%. Defeat the Bone-Crown Emperor and its raiders with ten honor seals. Each cultivator death breaks one seal. Empty seals still allow a Bronze victory; Silver needs at most three deaths and Gold needs none. This optional court has no resurrection altars. All normal mana, Qi and ultimate costs apply.",
            [
                ("soul", 2, 2),
                ("swordcorpse", 1, 2),
                ("rottenwood", 3, 2),
                ("drainer", 2, 3),
                ("soul", 1, 4),
                ("swordcorpse", 3, 4),
            ],
        ),
    ]
    result = {}
    for id, base, name, unlock, kind, description, packs in specs:
        s = deepcopy(stages[base])
        s.update(
            id=id,
            name=name,
            mode="trial",
            unlock=unlock,
            next=None,
            boss=None,
            objective_kind=kind,
            description=description,
            chapter=0,
            duration=240,
            duration_label="3-5 min",
            reward={"stones": 20, "insight": 1},
            hp_multiplier=1.0,
            altars=[],
            starting_qi=220 if kind == "oath" else 175,
        )
        if kind == "oath":
            packs = packs[:-1] + [("soul", 4, 3), ("swordcorpse", 0, 3)] + packs[-1:]
        waves = []
        for i, (enemy, lane, count) in enumerate(packs):
            spawns = [
                dict(
                    type=enemy, lane=lane, count=count, gap=1.1, elite_count=int(i >= 3)
                )
            ]
            if i >= 2:
                spawns.append(
                    dict(
                        type="lantern" if i % 2 == 0 else "hound",
                        lane=lane,
                        count=1,
                        gap=1,
                        elite_count=1,
                    )
                )
            if i == len(packs) - 1:
                spawns.extend(
                    dict(
                        type="soul" if kind == "oath" else "tide",
                        lane=ln,
                        count=4,
                        gap=0.65,
                        swarm=True,
                    )
                    for ln in range(5)
                )
                if kind == "oath":
                    spawns.append(dict(type="boneemperor", lane=2, count=1, gap=1))
            waves.append(
                dict(at=12 + i * (26 if kind == "oath" else 23), spawns=spawns)
            )
        s.update(
            waves=waves,
            phases=[
                dict(id="setup", name="Prepare the Guard", end_wave=2),
                dict(id="pressure", name="Coordinated Raiders", end_wave=4),
                dict(id="onslaught", name="Final Stand", end_wave=len(waves)),
            ],
            final_assault_count=sum(x["count"] for x in waves[-1]["spawns"]),
        )
        s["loss_limit"] = 10 if kind == "oath" else None
        if kind == "oath":
            s["duration_label"] = "5-8 min"
        s["incoming_damage_multiplier"] = 0.75 if kind == "oath" else 1
        s["enemy_count"] = sum(x["count"] for w in waves for x in w["spawns"])
        s["medals"] = dict(
            bronze="Win the trial.",
            silver="Win with gate intact, at most one cultivator death and objective health at least 70%.",
            gold="Win with gate intact, no cultivator deaths and objective health at least 90%.",
        )
        if kind == "oath":
            s["medals"][
                "silver"
            ] = "Win with gate intact and at most three cultivator deaths."
        result[id] = s
    return result


SQUAD_ROLES = {
    "guard": dict(
        name="Guard",
        radius=1.25,
        description="Elite Hounds/Drowned protect nearby elite non-boss, non-guard enemies within radius 1.25: 15% less non-True damage, capped at 3 prevented damage per hit. Does not stack. Guard has 12% less HP than its standard elite profile. Freeze or defeat the guard to break the link.",
    ),
    "mender": dict(
        name="Mender",
        radius=1.5,
        description="Elite Lanterns/Rottenwood channel for 1s, then heal at most two other elite non-boss allies inside radius 1.5 for 4% max HP, capped at 16 each. Cooldown 8s. Mender has 10% less HP than its standard elite profile. Any damage or freeze interrupts the channel.",
    ),
    "striker": dict(
        name="Striker",
        radius=0,
        description="Other elite raiders use their existing attack and special skill. Remove the guard or mender first; the squad adds no extra attack multiplier.",
    ),
}
