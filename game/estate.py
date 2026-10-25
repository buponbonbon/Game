"""Pure, transactional profile economy. Browser saves remain portable/offline."""

from copy import deepcopy
import math, uuid
from .content import HEROES, ENEMIES, STAGES
from .estate_content import CROPS, RECIPES, DECORATIONS, CONTRACTS, ACHIEVEMENTS
from .rules import validate_upgrades


class EconomyError(ValueError):
    pass


def sequence(value):
    return value if isinstance(value, list) else []


def member(value, mapping):
    return isinstance(value, str) and value in mapping


def number(v, default=0, maximum=999999):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        return default
    return min(maximum, max(0, int(v)))


def realm(p):
    return (
        3
        if "tomb-3" in p["completed"]
        else (
            2
            if "terrace-3" in p["completed"]
            else 1 if "wharf-3" in p["completed"] else 0
        )
    )


def new_estate():
    return dict(
        garden={
            "size": 3,
            "irrigation": 0,
            "plots": [
                dict(crop=None, growth=0, watered=False, fertilized=False)
                for _ in range(9)
            ],
        },
        bag={
            "seeds": {
                "qi_grass": 3,
                "river_lotus": 1,
                "azure_bamboo": 1,
                "soul_lingzhi": 1,
            },
            "produce": {},
            "pills": {},
            "fertilizer": 3,
        },
        talent_paid={},
        crop_research={},
        blueprints=["spirit_tea"],
        equipped=None,
        cosmetics={"owned": [], "active": []},
        contracts={"cycle": 0, "entries": []},
        claimed_achievements=[],
        monsters={},
        monster_claims={},
        ledger=[],
        stats={},
    )


def normalize_profile(raw):
    if not isinstance(raw, dict):
        raise EconomyError("A save profile is required.")
    p = {k: deepcopy(raw[k]) for k in ("best", "settings", "updated") if k in raw}
    p.update(
        version=2,
        save_id=(
            raw.get("save_id")
            if isinstance(raw.get("save_id"), str) and 1 <= len(raw["save_id"]) <= 64
            else uuid.uuid4().hex
        ),
        stones=number(raw.get("stones")),
        insight=number(raw.get("insight")),
        completed=(
            list(
                dict.fromkeys(
                    x
                    for x in raw.get("completed", [])
                    if isinstance(x, str) and x in STAGES
                )
            )
            if isinstance(raw.get("completed", []), list)
            else []
        ),
        upgrades=validate_upgrades(raw.get("upgrades", {})),
    )
    if not isinstance(p.get("best"), dict):
        p["best"] = {}
    if not isinstance(p.get("settings"), dict):
        p["settings"] = {}
    e = new_estate()
    old = raw.get("estate")
    if isinstance(old, dict):
        g = old.get("garden", {})
        g = g if isinstance(g, dict) else {}
        size = number(g.get("size"), 3, 9)
        e["garden"]["size"] = size if size in (3, 6, 9) else 3
        e["garden"]["irrigation"] = number(g.get("irrigation"), 0, 2)
        for i, plot in enumerate(
            g.get("plots", [])[:9] if isinstance(g.get("plots"), list) else []
        ):
            if (
                i >= e["garden"]["size"]
                or not isinstance(plot, dict)
                or not member(plot.get("crop"), CROPS)
            ):
                continue
            e["garden"]["plots"][i] = dict(
                crop=plot["crop"],
                growth=number(plot.get("growth"), 0, 3),
                watered=plot.get("watered") is True,
                fertilized=plot.get("fertilized") is True,
            )
        bag = old.get("bag", {})
        bag = bag if isinstance(bag, dict) else {}
        for category, keys in (
            ("seeds", CROPS),
            ("produce", CROPS),
            ("pills", RECIPES),
        ):
            data = bag.get(category, {})
            data = data if isinstance(data, dict) else {}
            e["bag"][category] = {k: number(data.get(k), 0, 9999) for k in keys}
        e["bag"]["fertilizer"] = number(bag.get("fertilizer"), 0, 9999)
        data = old.get("crop_research", {})
        data = data if isinstance(data, dict) else {}
        e["crop_research"] = {k: number(data.get(k), 0, 2) for k in CROPS}
        e["blueprints"] = (
            list(
                dict.fromkeys(
                    ["spirit_tea"]
                    + [k for k in old.get("blueprints", []) if member(k, RECIPES)]
                )
            )
            if isinstance(old.get("blueprints", []), list)
            else ["spirit_tea"]
        )
        e["equipped"] = (
            old.get("equipped")
            if isinstance(old.get("equipped"), str) and old["equipped"] in RECIPES
            else None
        )
        cosmetics = old.get("cosmetics", {})
        cosmetics = cosmetics if isinstance(cosmetics, dict) else {}
        e["cosmetics"]["owned"] = [
            k for k in DECORATIONS if k in sequence(cosmetics.get("owned"))
        ]
        e["cosmetics"]["active"] = [
            k for k in e["cosmetics"]["owned"] if k in sequence(cosmetics.get("active"))
        ]
        e["claimed_achievements"] = [
            a["id"]
            for a in ACHIEVEMENTS
            if a["id"] in sequence(old.get("claimed_achievements"))
        ]
        for key, allowed in (("monsters", ENEMIES), ("stats", None)):
            values = old.get(key, {})
            values = values if isinstance(values, dict) else {}
            e[key] = {
                k: number(v)
                for k, v in values.items()
                if isinstance(k, str) and (allowed is None or k in allowed)
            }
        claims = old.get("monster_claims", {})
        claims = claims if isinstance(claims, dict) else {}
        e["monster_claims"] = {
            k: [tier for tier in (0, 1, 2) if tier in v]
            for k, v in claims.items()
            if k in ENEMIES and isinstance(v, list)
        }
        e["ledger"] = (
            list(
                dict.fromkeys(
                    x
                    for x in old.get("ledger", [])
                    if isinstance(x, str) and len(x) <= 80
                )
            )[-512:]
            if isinstance(old.get("ledger", []), list)
            else []
        )
        con = old.get("contracts", {})
        con = con if isinstance(con, dict) else {}
        e["contracts"]["cycle"] = number(con.get("cycle"))
        definitions = {x["id"]: x for x in CONTRACTS}
        entries = con.get("entries", [])
        if isinstance(entries, list):
            seen = set()
            for c in entries[:3]:
                if (
                    isinstance(c, dict)
                    and member(c.get("id"), definitions)
                    and c["id"] not in seen
                ):
                    seen.add(c["id"])
                    e["contracts"]["entries"].append(
                        dict(
                            id=c["id"],
                            progress=number(c.get("progress")),
                            claimed=c.get("claimed") is True,
                        )
                    )
    paid = old.get("talent_paid", {}) if isinstance(old, dict) else {}
    paid = paid if isinstance(paid, dict) else {}
    for key, upgrade in p["upgrades"].items():
        maximum = (
            35
            if isinstance(upgrade, str)
            else sum(
                n["cost"]
                for n in HEROES[key]["talents"][upgrade["branch"]][: upgrade["rank"]]
            )
        )
        e["talent_paid"][key] = number(paid.get(key), maximum, maximum)
    if not isinstance(old, dict):
        e["stats"]["wins"] = len(p["completed"])
    p["estate"] = e
    if len(e["contracts"]["entries"]) != 3:
        _rotate(p, initial=True)
    return p


def _rotate(p, initial=False):
    e = p["estate"]
    con = e["contracts"]
    if not initial:
        if not all(c["claimed"] for c in con["entries"]):
            raise EconomyError("Claim all three commissions before taking a new set.")
        con["cycle"] += 1
    available = [c for c in CONTRACTS if c["min_realm"] <= realm(p)]
    offset = con["cycle"] * 3 % len(available)
    ordered = available[offset:] + available[:offset]
    con["entries"] = [dict(id=c["id"], progress=0, claimed=False) for c in ordered[:3]]


def _progress(p, kind, amount=1):
    definitions = {c["id"]: c for c in CONTRACTS}
    for c in p["estate"]["contracts"]["entries"]:
        if definitions[c["id"]]["kind"] == kind and not c["claimed"]:
            c["progress"] = min(definitions[c["id"]]["target"], c["progress"] + amount)


def _give(p, reward):
    p["stones"] = min(999999, p["stones"] + number(reward.get("stones")))
    p["insight"] = min(999999, p["insight"] + number(reward.get("insight")))
    for category in ("seeds", "produce", "pills"):
        for key, qty in reward.get(category, {}).items():
            p["estate"]["bag"][category][key] = min(
                9999, p["estate"]["bag"][category].get(key, 0) + qty
            )
    p["estate"]["bag"]["fertilizer"] = min(
        9999, p["estate"]["bag"]["fertilizer"] + number(reward.get("fertilizer"))
    )


def _spend(p, stones=0, insight=0):
    if p["stones"] < stones:
        raise EconomyError(f'Need {stones-p["stones"]} more Spirit Stones.')
    if p["insight"] < insight:
        raise EconomyError(f'Need {insight-p["insight"]} more Insight.')
    p["stones"] -= stones
    p["insight"] -= insight


def requirement(p, crop):
    return max(
        1, CROPS[crop]["growth"] - (p["estate"]["crop_research"].get(crop, 0) >= 2)
    )


def harvest_yield(p, plot):
    return (
        CROPS[plot["crop"]]["yield_amount"]
        + (1 + int(p["estate"]["garden"]["irrigation"] >= 2) if plot["watered"] else 0)
        + int(plot["fertilized"])
        + int(p["estate"]["crop_research"].get(plot["crop"], 0) >= 1)
    )


def _plot(p, index):
    if (
        isinstance(index, bool)
        or not isinstance(index, int)
        or not 0 <= index < p["estate"]["garden"]["size"]
    ):
        raise EconomyError("Choose an unlocked plot.")
    return p["estate"]["garden"]["plots"][index]


def _grow(p):
    for plot in p["estate"]["garden"]["plots"][: p["estate"]["garden"]["size"]]:
        if plot["crop"]:
            plot["growth"] = min(requirement(p, plot["crop"]), plot["growth"] + 1)
            if p["estate"]["garden"]["irrigation"] >= 1:
                plot["watered"] = True


def _achievement_progress(p, a):
    e = p["estate"]
    key = a["stat"]
    return (
        len(p["completed"])
        if key == "campaign"
        else (
            e["garden"]["size"]
            if key == "garden_size"
            else (
                sum(bool(v) for v in e["monster_claims"].values())
                if key == "studied"
                else e["stats"].get(key, 0)
            )
        )
    )


def view(p):
    e = p["estate"]
    defs = {c["id"]: c for c in CONTRACTS}
    return dict(
        crops=list(CROPS.values()),
        recipes=list(RECIPES.values()),
        decorations=list(DECORATIONS.values()),
        contracts=[{**defs[c["id"]], **c} for c in e["contracts"]["entries"]],
        achievements=[
            {
                **a,
                "progress": min(a["target"], _achievement_progress(p, a)),
                "claimed": a["id"] in e["claimed_achievements"],
            }
            for a in ACHIEVEMENTS
        ],
        plots=[
            {
                **plot,
                "need": requirement(p, plot["crop"]) if plot["crop"] else 0,
                "yield": harvest_yield(p, plot) if plot["crop"] else 0,
            }
            for plot in e["garden"]["plots"]
        ],
        research={
            id: dict(
                kills=e["monsters"].get(id, 0),
                thresholds=[1, 3, 5] if enemy["boss"] else [3, 10, 25],
                claimed=e["monster_claims"].get(id, []),
            )
            for id, enemy in ENEMIES.items()
        },
        expand_cost=(
            60
            if e["garden"]["size"] == 3
            else 120 if e["garden"]["size"] == 6 else None
        ),
        irrigation_cost=[40, 90, None][e["garden"]["irrigation"]],
        respec_fee=0 if e["stats"].get("respecs", 0) == 0 else 10,
    )


def act(raw, action, **data):
    p = normalize_profile(raw)
    e = p["estate"]
    notice = ""
    if action == "inspect":
        pass
    elif action == "plant":
        plot = _plot(p, data.get("plot"))
        crop = data.get("crop")
        if not isinstance(crop, str) or crop not in CROPS:
            raise EconomyError("Choose a seed type.")
        if plot["crop"]:
            raise EconomyError("Harvest or clear this plot first.")
        if e["bag"]["seeds"].get(crop, 0) < 1:
            raise EconomyError("Buy or earn a seed first.")
        e["bag"]["seeds"][crop] -= 1
        plot.update(
            crop=crop,
            growth=0,
            watered=e["garden"]["irrigation"] >= 2,
            fertilized=False,
        )
        notice = CROPS[crop]["name"] + " planted."
    elif action == "water":
        plot = _plot(p, data.get("plot"))
        if not plot["crop"]:
            raise EconomyError("Plant a seed first.")
        if plot["watered"]:
            raise EconomyError("This crop is already watered.")
        plot["watered"] = True
        notice = "Watered: better harvest yield."
    elif action == "fertilize":
        plot = _plot(p, data.get("plot"))
        if not plot["crop"]:
            raise EconomyError("Plant a seed first.")
        if plot["fertilized"]:
            raise EconomyError("Fertilizer has already been applied.")
        if not e["bag"]["fertilizer"]:
            raise EconomyError("Earn or buy fertilizer first.")
        e["bag"]["fertilizer"] -= 1
        plot["fertilized"] = True
        notice = "Fertilized: +1 harvest yield."
    elif action == "clear":
        plot = _plot(p, data.get("plot"))
        if not plot["crop"]:
            raise EconomyError("This plot is empty.")
        plot.update(crop=None, growth=0, watered=False, fertilized=False)
        notice = "Plot cleared. The planted seed was spent."
    elif action == "harvest":
        plot = _plot(p, data.get("plot"))
        if not plot["crop"] or plot["growth"] < requirement(p, plot["crop"]):
            raise EconomyError("This crop needs more completed battles.")
        crop = plot["crop"]
        amount = harvest_yield(p, plot)
        _give(p, {"produce": {crop: amount}})
        if e["crop_research"].get(crop, 0) >= 2:
            _give(p, {"seeds": {crop: 1}})
        e["stats"]["harvests"] = e["stats"].get("harvests", 0) + 1
        _progress(p, "harvests")
        plot.update(crop=None, growth=0, watered=False, fertilized=False)
        notice = f'Harvested {amount} {CROPS[crop]["name"]}.'
    elif action == "expand":
        if e["garden"]["size"] >= 9:
            raise EconomyError("All nine plots are already open.")
        _spend(p, 60 if e["garden"]["size"] == 3 else 120)
        e["garden"]["size"] += 3
        notice = "Three more plots opened."
    elif action == "irrigation":
        level = e["garden"]["irrigation"]
        if level >= 2:
            raise EconomyError("Irrigation is fully upgraded.")
        _spend(p, [40, 90][level])
        e["garden"]["irrigation"] += 1
        notice = "Irrigation upgraded."
    elif action in ("buy", "sell"):
        item = data.get("item")
        qty = data.get("quantity", 1)
        if isinstance(qty, bool) or not isinstance(qty, int) or not 1 <= qty <= 99:
            raise EconomyError("Quantity must be 1–99.")
        if action == "buy" and item == "fertilizer":
            _spend(p, 5 * qty)
            _give(p, {"fertilizer": qty})
            notice = f"Bought {qty} fertilizer."
        elif (
            isinstance(item, str)
            and item.startswith("seed:")
            and item[5:] in CROPS
            and action == "buy"
        ):
            crop = item[5:]
            _spend(p, CROPS[crop]["seed_price"] * qty)
            _give(p, {"seeds": {crop: qty}})
            notice = f"Bought {qty} seeds."
        elif (
            isinstance(item, str)
            and item.startswith("produce:")
            and item[8:] in CROPS
            and action == "sell"
        ):
            crop = item[8:]
            if e["bag"]["produce"].get(crop, 0) < qty:
                raise EconomyError("Not enough harvested produce.")
            e["bag"]["produce"][crop] -= qty
            value = CROPS[crop]["sell_price"] * qty
            _give(p, {"stones": value})
            notice = f"Sold {qty} for {value} Spirit Stones."
        elif (
            action == "buy"
            and isinstance(item, str)
            and item.startswith("decor:")
            and item[6:] in DECORATIONS
        ):
            key = item[6:]
            if qty != 1 or key in e["cosmetics"]["owned"]:
                raise EconomyError("This decoration is already owned.")
            _spend(p, DECORATIONS[key]["price"])
            e["cosmetics"]["owned"].append(key)
            e["cosmetics"]["active"].append(key)
            notice = "Decoration purchased and displayed."
        else:
            raise EconomyError("Choose a valid merchant item.")
    elif action == "decorate":
        key = data.get("item")
        if key not in e["cosmetics"]["owned"]:
            raise EconomyError("Buy this decoration first.")
        if key in e["cosmetics"]["active"]:
            e["cosmetics"]["active"].remove(key)
        else:
            e["cosmetics"]["active"].append(key)
        notice = "Decoration display changed."
    elif action == "crop_research":
        crop = data.get("crop")
        if not isinstance(crop, str) or crop not in CROPS:
            raise EconomyError("Choose a crop to study.")
        level = e["crop_research"].get(crop, 0)
        if level >= 2:
            raise EconomyError("This crop is fully researched.")
        _spend(p, insight=[1, 2][level])
        e["crop_research"][crop] = level + 1
        notice = "Crop research advanced."
    elif action == "learn_recipe":
        key = data.get("recipe")
        if not isinstance(key, str) or key not in RECIPES:
            raise EconomyError("Choose a formula.")
        if key in e["blueprints"]:
            raise EconomyError("This formula is already known.")
        _spend(p, insight=RECIPES[key]["insight_cost"])
        e["blueprints"].append(key)
        notice = "Formula researched."
    elif action == "craft":
        key = data.get("recipe")
        qty = data.get("quantity", 1)
        if key not in e["blueprints"]:
            raise EconomyError("Research this formula first.")
        if isinstance(qty, bool) or not isinstance(qty, int) or not 1 <= qty <= 10:
            raise EconomyError("Craft 1–10 doses at a time.")
        recipe = RECIPES[key]
        for crop, n in recipe["ingredients"].items():
            if e["bag"]["produce"].get(crop, 0) < n * qty:
                raise EconomyError("More harvested ingredients are needed.")
        _spend(p, recipe["fee"] * qty)
        for crop, n in recipe["ingredients"].items():
            e["bag"]["produce"][crop] -= n * qty
        _give(p, {"pills": {key: qty}})
        e["stats"]["crafted"] = e["stats"].get("crafted", 0) + qty
        _progress(p, "crafted", qty)
        notice = f'Crafted {qty} {recipe["name"]}.'
    elif action == "equip":
        key = data.get("item")
        if key is not None and (
            not isinstance(key, str)
            or key not in RECIPES
            or e["bag"]["pills"].get(key, 0) < 1
        ):
            raise EconomyError("Craft or own a dose before equipping it.")
        e["equipped"] = key
        notice = (
            "Preparation selected for the next battle."
            if key
            else "Preparation slot cleared."
        )
    elif action == "contract_claim":
        key = data.get("id")
        entry = next((c for c in e["contracts"]["entries"] if c["id"] == key), None)
        definition = next((c for c in CONTRACTS if c["id"] == key), None)
        if not entry or entry["claimed"] or entry["progress"] < definition["target"]:
            raise EconomyError("This commission is not ready to claim.")
        entry["claimed"] = True
        _give(p, definition["reward"])
        notice = "Commission reward claimed."
    elif action == "contracts_rotate":
        _rotate(p)
        notice = "Three new commissions posted."
    elif action == "achievement_claim":
        key = data.get("id")
        a = next((a for a in ACHIEVEMENTS if a["id"] == key), None)
        if (
            not a
            or key in e["claimed_achievements"]
            or _achievement_progress(p, a) < a["target"]
        ):
            raise EconomyError("This achievement is not ready to claim.")
        e["claimed_achievements"].append(key)
        _give(p, a["reward"])
        notice = "Achievement reward claimed."
    elif action == "monster_claim":
        key = data.get("enemy")
        tier = data.get("tier")
        if (
            not isinstance(key, str)
            or key not in ENEMIES
            or isinstance(tier, bool)
            or not isinstance(tier, int)
            or tier not in (0, 1, 2)
        ):
            raise EconomyError("Choose an enemy research milestone.")
        needed = ([1, 3, 5] if ENEMIES[key]["boss"] else [3, 10, 25])[tier]
        if e["monsters"].get(key, 0) < needed or tier in e["monster_claims"].get(
            key, []
        ):
            raise EconomyError("This research reward is not available.")
        e["monster_claims"].setdefault(key, []).append(tier)
        _give(
            p,
            {
                "stones": ([10, 15, 25] if ENEMIES[key]["boss"] else [5, 10, 15])[tier],
                "insight": int(tier == 2 or ENEMIES[key]["boss"] and tier == 1),
            },
        )
        notice = "Bestiary research reward claimed."
    elif action == "respec":
        key = data.get("hero")
        if not isinstance(key, str) or key not in HEROES or key not in p["upgrades"]:
            raise EconomyError("Choose a cultivator with learned talents.")
        upgrade = p["upgrades"][key]
        spent = e["talent_paid"][key]
        fee = 0 if e["stats"].get("respecs", 0) == 0 else 10
        if spent <= 0:
            raise EconomyError("No learned nodes to reset.")
        del p["upgrades"][key]
        e["talent_paid"].pop(key, None)
        _give(p, {"stones": max(0, spent - fee)})
        e["stats"]["respecs"] = e["stats"].get("respecs", 0) + 1
        notice = f"Talents reset: {max(0,spent-fee)} stones returned (fee {fee})."
    elif action == "buy_talent":
        key = data.get("hero")
        branch = data.get("branch")
        rank = data.get("rank")
        if (
            not isinstance(key, str)
            or key not in HEROES
            or branch not in ("A", "B")
            or isinstance(rank, bool)
            or not isinstance(rank, int)
            or not 1 <= rank <= 5
        ):
            raise EconomyError("Choose a valid talent node.")
        if realm(p) < HEROES[key]["unlock_chapter"]:
            raise EconomyError("This cultivator is not unlocked.")
        current = p["upgrades"].get(key, {})
        current = (
            {"branch": current, "rank": 3} if isinstance(current, str) else current
        )
        if current and current["branch"] != branch:
            raise EconomyError("Reset the current path before changing branches.")
        if rank != current.get("rank", 0) + 1:
            raise EconomyError("Learn the preceding node first.")
        cost = HEROES[key]["talents"][branch][rank - 1]["cost"]
        _spend(p, cost)
        e["talent_paid"][key] = e["talent_paid"].get(key, 0) + cost
        p["upgrades"][key] = {"branch": branch, "rank": rank}
        notice = "Talent awakened."
    else:
        raise EconomyError("Unknown estate action.")
    return dict(ok=True, profile=p, catalogue=view(p), notice=notice)


def prepare(raw):
    p = normalize_profile(raw)
    key = p["estate"]["equipped"]
    if key:
        if p["estate"]["bag"]["pills"].get(key, 0) < 1:
            raise EconomyError(
                "The equipped preparation is out of stock. Craft a dose or clear the slot."
            )
        p["estate"]["bag"]["pills"][key] -= 1
        if not p["estate"]["bag"]["pills"][key]:
            p["estate"]["equipped"] = None
    return p, key


def settle(raw, battle_id, state):
    p = normalize_profile(raw)
    e = p["estate"]
    if battle_id in e["ledger"]:
        return dict(
            ok=True,
            profile=p,
            catalogue=view(p),
            notice="This battle is already recorded.",
            duplicate=True,
        )
    if state.get("status") not in ("victory", "defeat"):
        raise EconomyError("Finish the battle before collecting its outcome.")
    e["ledger"].append(battle_id)
    e["ledger"] = e["ledger"][-512:]
    won = state["status"] == "victory"
    nursery = state.get("mode") == "nursery"
    m = state.get("metrics", {})
    growth = (
        won
        or state.get("wave", 0) >= math.ceil(state.get("wave_count", 1) / 2)
        and state.get("time", 0) >= 60
    )
    before_stones, before_insight = p["stones"], p["insight"]
    before_seeds = deepcopy(e["bag"]["seeds"])
    before_fertilizer = e["bag"]["fertilizer"]
    if growth:
        _grow(p)
    kills = m.get("kills_by_type", {})
    total = 0
    for key, count in kills.items():
        if key in ENEMIES:
            n = number(count)
            e["monsters"][key] = e["monsters"].get(key, 0) + n
            total += n
    _progress(p, "kills", total)
    stats = e["stats"]
    stats["battles"] = stats.get("battles", 0) + 1
    nodes = number(m.get("nodes_purified"))
    rituals = number(m.get("rituals_used"))
    _progress(p, "nodes", nodes)
    if not nursery:
        _progress(p, "rituals", rituals)
    if rituals and not nursery:
        marker = "ritual_" + state.get("region", "wharf")
        stats[marker] = 1
        stats["ritual_regions"] = sum(
            stats.get("ritual_" + r, 0) > 0 for r in ("wharf", "terrace", "tomb")
        )
    if won:
        stats["wins"] = stats.get("wins", 0) + 1
        roles = len(m.get("roles_used", []))
        stats["max_roles"] = max(stats.get("max_roles", 0), roles)
        if roles >= 3:
            _progress(p, "diverse")
        if nursery:
            beds = sum(b["hp"] > 0 for b in state.get("nursery_beds", []))
            loot = {"seeds": {"qi_grass": max(1, beds)}}
            if beds >= 2:
                loot["seeds"]["river_lotus"] = 1
                loot["fertilizer"] = 1
            if beds == 3:
                loot["seeds"].update(azure_bamboo=1, soul_lingzhi=1)
                stats["nursery_perfect"] = stats.get("nursery_perfect", 0) + 1
            _give(p, loot)
            _progress(p, "nursery")
            notice = (
                f"Nursery defended: {beds} beds survived. Seeds and supplies awarded."
            )
        else:
            stage = STAGES[state["stage"]]
            first = state["stage"] not in p["completed"]
            reward = stage["reward"]
            if first:
                p["completed"].append(state["stage"])
                _give(
                    p, {"stones": reward["stones"], "insight": reward.get("insight", 0)}
                )
            else:
                _give(p, {"stones": max(10, math.floor(reward["stones"] * 0.25))})
            # One seed after every successful encounter; region determines its use.
            seed = {
                "wharf": "river_lotus",
                "terrace": "azure_bamboo",
                "tomb": "soul_lingzhi",
            }[state["region"]]
            _give(p, {"seeds": {seed: 1}})
            if stats["wins"] % 3 == 0:
                _give(p, {"fertilizer": 1})
            old = p["best"].get(state["stage"])
            if (
                not isinstance(old, dict)
                or not isinstance(old.get("time"), (int, float))
                or state["time"] < old["time"]
            ):
                p["best"][state["stage"]] = {
                    k: state.get(k, 0) for k in ("time", "gate", "kills")
                }
            notice = "Victory recorded: stones, seeds and garden growth awarded."
        if state.get("gate", 0) >= (6 if nursery else 3):
            _progress(p, "perfect")
    else:
        notice = (
            "Battle recorded. Garden growth earned."
            if growth
            else "Battle recorded. Reach half the waves and 60 seconds, or win, to grow crops."
        )
    return dict(
        ok=True,
        profile=p,
        catalogue=view(p),
        notice=notice,
        duplicate=False,
        outcome=dict(
            stones=p["stones"] - before_stones,
            insight=p["insight"] - before_insight,
            seeds={
                k: n - before_seeds.get(k, 0)
                for k, n in e["bag"]["seeds"].items()
                if n > before_seeds.get(k, 0)
            },
            fertilizer=e["bag"]["fertilizer"] - before_fertilizer,
            garden_grew=growth,
            beds=(
                sum(b["hp"] > 0 for b in state.get("nursery_beds", []))
                if nursery
                else None
            ),
        ),
    )
