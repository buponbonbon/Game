"""Reproducible legal-play campaign with estate transactions between encounters.

Not telemetry or a player study. One scripted player policy; no injected currency,
free talents or altered enemy stats. Authoring output can be inspected offline.
"""

from pathlib import Path
import sys, json, argparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from game import estate
from game.content import STAGES, HEROES
from game.estate_content import CROPS, RECIPES, FERTILIZER_PRICE
from tools.simulate_campaign import play_stage


def journey(seed=4701):
    p = estate.normalize_profile(
        dict(version=1, completed=[], upgrades={}, stones=0, insight=0)
    )
    runs = []
    actions = []

    def act(action, **data):
        nonlocal p
        try:
            r = estate.act(p, action, **data)
            p = r["profile"]
            actions.append(
                dict(
                    after_battle=len(runs),
                    action=action,
                    details=data,
                    stones=p["stones"],
                    insight=p["insight"],
                )
            )
            return True
        except estate.EconomyError:
            return False

    for i, crop in enumerate(("qi_grass", "river_lotus", "soul_lingzhi")):
        act("plant", plot=i, crop=crop)
        act("water", plot=i)
        act("fertilize", plot=i)
    plan = [
        (h, branch, r)
        for h, branch, ranks in [
            ("gatherer", "A", range(1, 4)),
            ("sword", "A", range(1, 4)),
            ("fire", "B", range(1, 6)),
            ("monk", "A", range(1, 4)),
            ("herbalist", "A", range(1, 4)),
        ]
        for r in ranks
    ]
    for index, stage in enumerate(STAGES.values()):
        prepared, preparation = estate.prepare(p)
        r = play_stage(
            stage["id"],
            seed,
            p["upgrades"],
            estate.realm(p),
            tactics={"healer": False},
            preparation=preparation,
        )
        runs.append(r)
        p = prepared
        if r["status"] == "playing":
            r["policy_timeout"] = True
            break
        state = {**r, "time": r["duration"]}
        result = estate.settle(p, "playtest-" + str(index), state)
        p = result["profile"]
        r["estate_outcome"] = result["outcome"]
        if r["status"] != "victory":
            break
        for i, plot in enumerate(
            estate.view(p)["plots"][: p["estate"]["garden"]["size"]]
        ):
            if plot["crop"] and plot["growth"] >= plot["need"]:
                act("harvest", plot=i)
        for c in estate.view(p)["contracts"]:
            if not c["claimed"] and c["progress"] >= c["target"]:
                act("contract_claim", id=c["id"])
        if all(c["claimed"] for c in p["estate"]["contracts"]["entries"]):
            act("contracts_rotate")
        for a in estate.view(p)["achievements"]:
            if not a["claimed"] and a["progress"] >= a["target"]:
                act("achievement_claim", id=a["id"])
        for enemy, research in estate.view(p)["research"].items():
            for tier, target in enumerate(research["thresholds"]):
                if research["kills"] >= target and tier not in research["claimed"]:
                    act("monster_claim", enemy=enemy, tier=tier)
        # Keep the verified campaign's talent milestones; reserve surplus for
        # the estate instead of automatically spending every stone on combat.
        caps = [
            {"gatherer": 1},
            {"gatherer": 3},
            {"gatherer": 3, "sword": 3},
            {"gatherer": 3, "sword": 3, "fire": 2},
            {"gatherer": 3, "sword": 3, "fire": 3},
            {"gatherer": 3, "sword": 3, "fire": 5},
            {"gatherer": 3, "sword": 3, "fire": 5, "monk": 2, "herbalist": 2},
            {"gatherer": 3, "sword": 3, "fire": 5, "monk": 3, "herbalist": 2},
            {"gatherer": 3, "sword": 3, "fire": 5, "monk": 3, "herbalist": 3},
        ][index]
        for hero, branch, rank in plan:
            if rank > caps.get(hero, 0):
                continue
            current = p["upgrades"].get(hero, {})
            if current.get("rank", 0) >= rank:
                continue
            if not act("buy_talent", hero=hero, branch=branch, rank=rank):
                break
        if index >= 3 and p["stones"] >= 180 and p["estate"]["garden"]["size"] < 6:
            act("expand")
        if p["insight"] >= 1 and not p["estate"]["crop_research"].get("qi_grass"):
            act("crop_research", crop="qi_grass")
        for recipe in ("purifying_dew", "soul_ward"):
            if (
                recipe not in p["estate"]["blueprints"]
                and p["insight"] >= RECIPES[recipe]["insight_cost"]
            ):
                act("learn_recipe", recipe=recipe)
        # Crop variety comes from starter supplies and regional victory seeds.
        preferred = ("azure_bamboo", "qi_grass", "river_lotus", "soul_lingzhi")
        for i, plot in enumerate(
            p["estate"]["garden"]["plots"][: p["estate"]["garden"]["size"]]
        ):
            if plot["crop"]:
                continue
            order = preferred[(index + i) % 4 :] + preferred[: (index + i) % 4]
            for crop in order:
                if p["estate"]["bag"]["seeds"].get(crop, 0) and act(
                    "plant", plot=i, crop=crop
                ):
                    act("water", plot=i)
                    break
        region = stage["region"]
        selection = (
            "soul_ward"
            if region == "tomb"
            else "purifying_dew" if region == "terrace" else "spirit_tea"
        )
        if (
            not p["estate"]["bag"]["pills"].get(selection)
            and p["stones"] >= RECIPES[selection]["fee"] + 5
        ):
            act("craft", recipe=selection)
        if selection == "spirit_tea" and p["estate"]["bag"]["pills"].get(selection):
            act("equip", item=selection)
        else:
            act("equip", item=None)
        r["wallet_after_estate"] = dict(stones=p["stones"], insight=p["insight"])
        r["plots_after_estate"] = p["estate"]["garden"]["size"]
        r["inventory_after_estate"] = p["estate"]["bag"].copy()
    return dict(
        passed=len(runs) == 9 and all(r["status"] == "victory" for r in runs),
        scope="One legal seeded estate/campaign policy, not a player study or exhaustive balance result.",
        seed=seed,
        runs=runs,
        actions=actions,
        final_profile=p,
        fertilizer_unit_price=FERTILIZER_PRICE,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=4701)
    args = parser.parse_args()
    result = journey(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                passed=result["passed"],
                wins=sum(r["status"] == "victory" for r in result["runs"]),
                stones=result["final_profile"]["stones"],
                harvests=result["final_profile"]["estate"]["stats"].get("harvests", 0),
                preparations=[r["preparation"] for r in result["runs"]],
            ),
            indent=2,
        )
    )
    sys.exit(0 if result["passed"] else 1)
