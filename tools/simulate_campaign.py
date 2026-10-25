#!/usr/bin/env python3
"""Replay the verified nine-stage policy using legal player commands only.

This is one reproducible authored-wave policy, not a statistical balance study.
Run from any directory: python /path/to/Game/tools/simulate_campaign.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from game.content import HEROES, STAGES, TRIALS
from game.engine import Battle


def can_cast(hero, state):
    ultimate = hero["stats"]["ultimate"]
    return (
        hero["resonance"] >= 100
        and hero["mana"] >= ultimate["mana_cost"]
        and state["qi"] >= ultimate["qi_cost"]
        and hero["ultimate_cd"] <= 0
    )


def play_stage(stage_id, seed, upgrades, realm, tactics=None, preparation=None):
    """Build economy, cover incoming lanes, then add fire and use charged arts."""
    late_tomb = stage_id in ("tomb-2", "tomb-3", "trial-oath")
    from game.nursery import NURSERY

    content = (
        NURSERY
        if stage_id == "garden-defense"
        else TRIALS[stage_id] if stage_id in TRIALS else STAGES[stage_id]
    )
    battle = Battle(stage_id, seed=seed, upgrades=dict(upgrades), realm=realm)
    if preparation:
        battle.apply_preparation(preparation)
    battle.command({"action": "auto_ultimate", "enabled": True})
    actions = []

    def place(kind, lane, col):
        if any(
            t.get("blocked") and t["lane"] == lane and t["col"] == col
            for t in battle.snapshot()["hazard"]["tiles"]
        ):
            return False
        result = battle.command(
            {"action": "place", "hero": kind, "lane": lane, "col": col}
        )
        if result["ok"]:
            actions.append(
                {"time": round(battle.time, 3), "hero": kind, "lane": lane, "col": col}
            )
        return result["ok"]

    tactics = tactics or {}
    safe_terrace = stage_id in ("terrace-1", "terrace-3")
    economy_lane = tactics.get(
        "economy_lane", {"terrace-1": 4, "terrace-3": 0}.get(stage_id, 2)
    )
    gatherer_limit = tactics.get(
        "gatherer_limit", 3 if late_tomb or stage_id == "terrace-3" else 2
    )
    economy_window = tactics.get(
        "economy_window", 32 if late_tomb else 110 if safe_terrace else 24
    )
    economy_order = tactics.get(
        "economy_order", (0, 1, 3, 2, 4) if safe_terrace else (1, 3, 2, 0, 4)
    )
    add_tank = tactics.get("add_tank", safe_terrace)
    place("gatherer", economy_lane, 1)
    place("sword", 2, 2)
    for _ in range(3_500 if stage_id == "tomb-3" else 2_500):
        state = battle.snapshot()
        elapsed, heroes, enemies = state["time"], state["heroes"], state["enemies"]
        occupied = {(hero["lane"], hero["col"]) for hero in heroes}
        defended = {
            hero["lane"]
            for hero in heroes
            if hero["type"] in ("sword", "fire", "frost", "lightning")
        }
        gatherers = sum(hero["type"] == "gatherer" for hero in heroes)
        if (
            stage_id.startswith("tomb-")
            and tactics.get("healer")
            and elapsed >= 90
            and not any(h["type"] == "herbalist" for h in heroes)
            and state["qi"] >= 125
            and state["cards"]["herbalist"] <= 0
            and (2, 5) not in occupied
        ):
            place("herbalist", 2, 5)
            battle.advance(0.2)
            continue
        if stage_id == "trial-oath":
            if any(e["type"] == "boneemperor" for e in enemies):
                for unit in list(battle.heroes.values()):
                    if unit["type"] == "gatherer":
                        battle.command(dict(action="sell", unit=unit["id"]))
            support = (
                ("herbalist", 2, 4)
                if elapsed >= 90 and not any(h["type"] == "herbalist" for h in heroes)
                else (
                    ("formation", 2, 5)
                    if elapsed >= 150
                    and not any(h["type"] == "formation" for h in heroes)
                    else (
                        ("frost", 2, 3)
                        if elapsed >= 175
                        and not any(h["type"] == "frost" for h in heroes)
                        else None
                    )
                )
            )
            if (
                support
                and state["qi"] >= HEROES[support[0]]["cost"]
                and state["cards"][support[0]] <= 0
                and (support[1], support[2]) not in occupied
            ):
                place(*support)
                battle.advance(0.2)
                continue
        if (
            tactics.get("healer", stage_id == "trial-oath")
            and realm >= 1
            and elapsed > 50
            and state["qi"] >= 125
            and state["cards"]["herbalist"] <= 0
            and not any(h["type"] == "herbalist" for h in heroes)
            and any(
                h["hp"] < h["max_hp"] * 0.75 and h["type"] != "gatherer" for h in heroes
            )
        ):
            placed = False
            for lane, col in ((2, 2), (2, 3), (1, 2), (3, 2)):
                if (lane, col) not in occupied and place("herbalist", lane, col):
                    placed = True
                    break
            if placed:
                battle.advance(0.2)
                continue
        if (
            stage_id == "tomb-3"
            and elapsed > 280
            and state["qi"] >= 150
            and state["cards"]["formation"] <= 0
            and (1, 3) not in occupied
        ):
            place("formation", 1, 3)
        elif (
            gatherers < gatherer_limit
            and (gatherers < 2 or late_tomb or elapsed > 60)
            and elapsed < economy_window
            and state["qi"] >= 50
            and state["cards"]["gatherer"] <= 0
        ):
            for lane in economy_order:
                if (lane, 1) not in occupied and place("gatherer", lane, 1):
                    break
        else:
            upcoming = {lane: 999 for lane in range(5)}
            for wave in content["waves"]:
                for spawn in wave["spawns"]:
                    if wave["at"] >= elapsed:
                        upcoming[spawn["lane"]] = min(
                            upcoming[spawn["lane"]], wave["at"] - elapsed
                        )
            for enemy in enemies:
                upcoming[enemy["lane"]] = min(upcoming[enemy["lane"]], -20 + enemy["x"])
            needed = [
                lane
                for lane in sorted(upcoming, key=upcoming.get)
                if lane not in defended and upcoming[lane] < 22
            ]
            if needed and state["qi"] >= 75 and state["cards"]["sword"] <= 0:
                for col in (
                    (3, 2, 4) if late_tomb else (4, 3, 2) if realm else (2, 3, 4)
                ):
                    if (needed[0], col) not in occupied and place(
                        "sword", needed[0], col
                    ):
                        break
            elif not needed:
                pressure = {
                    lane: sum(enemy["hp"] for enemy in enemies if enemy["lane"] == lane)
                    for lane in range(5)
                }
                for lane in sorted(
                    pressure, key=lambda value: (-pressure[value], abs(value - 2))
                ):
                    if pressure[lane] <= 0:
                        continue
                    types = {hero["type"] for hero in heroes if hero["lane"] == lane}
                    kind = (
                        (
                            (
                                "fire"
                                if "fire" not in types
                                else (
                                    "monk"
                                    if "monk" not in types
                                    else (
                                        "lightning"
                                        if "lightning" not in types
                                        else "sword"
                                    )
                                )
                            )
                            if stage_id == "tomb-3"
                            else (
                                "monk"
                                if "monk" not in types
                                else "fire" if "fire" not in types else "sword"
                            )
                        )
                        if late_tomb
                        else (
                            "fire"
                            if "fire" not in types
                            else (
                                "monk" if add_tank and "monk" not in types else "sword"
                            )
                        )
                    )
                    if (
                        state["qi"] >= HEROES[kind]["cost"]
                        and state["cards"][kind] <= 0
                    ):
                        for col in (
                            (6, 7, 8)
                            if kind == "monk"
                            else (4, 5, 2) if late_tomb else (3, 4, 5, 2)
                        ):
                            if (lane, col) not in occupied and place(kind, lane, col):
                                break
                        break
        if late_tomb:
            if (
                (
                    any(
                        t["kind"] == "ROYAL DECREE" and t["ttl"] < 0.3
                        for t in state["telegraphs"]
                    )
                    if stage_id == "trial-oath"
                    else elapsed > 100
                )
                and any(h["hp"] < h["max_hp"] * 0.6 for h in heroes)
                and "tide_pearl" not in state["relics_used"]
            ):
                battle.command({"action": "relic", "id": "tide_pearl"})
            if elapsed > 180 and "wind_compass" not in state["relics_used"]:
                battle.command({"action": "relic", "id": "wind_compass"})
        battle.advance(0.2)
        if battle.status != "playing":
            break
    state = battle.snapshot()
    return {
        "stage": stage_id,
        "seed": seed,
        "realm": realm,
        "policy": (
            "Three Yun, fire/staff/lightning defense, a late formation circuit, automatic arts and timed relics"
            if late_tomb
            else "Two Yun, cover incoming lanes, fire reinforcement and charged arts"
        ),
        "upgrades_at_start": dict(upgrades),
        "status": state["status"],
        "duration": state["time"],
        "gate": state["gate"],
        "nursery_beds": state.get("nursery_beds", []),
        "objective": state.get("objective"),
        "remaining_enemies": [
            {k: e[k] for k in ("type", "hp", "x", "lane")} for e in state["enemies"]
        ],
        "mode": state["mode"],
        "region": state["region"],
        "wave": state["wave"],
        "wave_count": state["wave_count"],
        "preparation": state.get("preparation"),
        "kills": state["kills"],
        "qi_remaining": state["qi"],
        "metrics": state["metrics"],
        "rewards": state["rewards"],
        "placements": actions,
    }


def simulate_campaign(seed=4701):
    upgrades, completed, stages = {}, [], []
    stones = 0
    for stage_id in STAGES:
        realm = (
            3
            if "tomb-3" in completed
            else 2 if "terrace-3" in completed else 1 if "wharf-3" in completed else 0
        )
        result = play_stage(stage_id, seed, upgrades, realm)
        result["stones_before"] = stones
        result["branches_purchased"] = []
        stages.append(result)
        if result["status"] != "victory":
            result["stones_after"] = stones
            break
        completed.append(stage_id)
        stones += result["rewards"]["stones"]
        plan = (
            [("gatherer", "A", r) for r in (1, 2, 3)]
            + [("sword", "A", r) for r in (1, 2, 3)]
            + [("fire", "B", r) for r in (1, 2, 3, 4, 5)]
            + [("monk", "A", r) for r in (1, 2, 3)]
            + [("herbalist", "A", r) for r in (1, 2, 3)]
        )
        for hero, branch, rank in plan:
            current = upgrades.get(hero, {}).get("rank", 0)
            if current >= rank:
                continue
            cost = HEROES[hero]["talents"][branch][rank - 1]["cost"]
            if stones < cost:
                break
            upgrades[hero] = {"branch": branch, "rank": rank}
            stones -= cost
            result["branches_purchased"].append(
                {"hero": hero, "branch": branch, "rank": rank, "cost": cost}
            )
        result["stones_after"] = stones
    return {
        "policy": "Earn and spend real campaign rewards; adapt the formation to armored and spectral encounters",
        "scope": "One seeded legal-play smoke run; not statistical balance validation.",
        "seed": seed,
        "passed": len(completed) == len(STAGES),
        "completed": completed,
        "stones_remaining": stones,
        "stages": stages,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed", type=int, default=4701, help="Battle seed (default: 4701)."
    )
    parser.add_argument(
        "--output", type=Path, help="Also write the JSON report to this file."
    )
    args = parser.parse_args(argv)
    report = simulate_campaign(args.seed)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
