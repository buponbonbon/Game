"""Shared, testable effective hero stats and tile geometry."""

from copy import deepcopy
from .content import HEROES
from .design import geometry


def progress(value):
    if isinstance(value, str):
        return value, 3, True
    if isinstance(value, dict):
        return value.get("branch"), value.get("rank", 0), False
    return None, 0, False


def hero_data(id, upgrade=None):
    h = deepcopy(HEROES[id])
    branch, rank, legacy = progress(upgrade)
    if (
        branch not in ("A", "B")
        or not isinstance(rank, int)
        or isinstance(rank, bool)
        or not 0 <= rank <= 5
    ):
        branch, rank = None, 0
    if rank >= 3:
        h.update(
            {
                k: v
                for k, v in h["branches"][branch]["stats"].items()
                if isinstance(v, (int, float, bool))
            }
        )
    power = 1.0
    if not legacy and rank:
        if branch == "A":
            h["hp"] = round(h["hp"] * 1.06)
            if rank >= 2:
                h["damage"] *= 1.05
                power *= 1.05
            if rank >= 4:
                h["hp"] = round(h["hp"] * 1.04)
                h["mana_regen"] *= 1.08
        else:
            h["mana_max"] += 10
            if rank >= 2:
                h["mana_regen"] *= 1.12
            if rank >= 4:
                h["skill"]["cooldown"] *= 0.92
                if "circuit_cooldown" in h:
                    h["circuit_cooldown"] *= 0.92
    if rank >= 5:
        h.update(h["talents"][branch][4]["stats"])
    h.update(
        branch=branch if rank >= 3 else None,
        talent_branch=branch,
        talent_rank=rank,
        healing_multiplier=power,
    )
    h["damage"] = round(h["damage"], 2)
    skill = h["skill"]
    ult = h["ultimate"]
    atk = h["damage"]
    hp = h["hp"]
    formulas = {
        "gatherer": (
            0,
            "20 Qi / 10s before talent and duplicate modifiers",
            48,
            "4 pulses x 12 Qi",
        ),
        "sword": (
            round(atk * 4 / 3),
            "133% ATK per target",
            round(atk * 22 / 36),
            "61.1% ATK per blade x 10",
        ),
        "fire": (
            round(atk * 70 / 52),
            "134.6% ATK; secondary targets 60%",
            round(atk * 150 / 52),
            "288.5% ATK per marked explosion",
        ),
        "frost": (
            round(hp * h.get("shield_amount", 70) / 245),
            f"{100*h.get('shield_amount',70)/245:.1f}% max HP shield",
            round(atk * 85 / 22),
            "386.4% ATK per lane target",
        ),
        "monk": (
            round(atk * 60 / 44),
            "136.4% ATK per target",
            round(atk * 90 / 44),
            "204.5% ATK; shield 50% max HP",
        ),
        "lightning": (
            round(atk * 80 / 30),
            "266.7% ATK primary / 116.7% ATK chain",
            round(atk * 125 / 30),
            "416.7% ATK to up to 5 targets",
        ),
        "herbalist": (
            round(hp * 0.125 * power),
            "12.5% max HP cleanse-heal",
            round(hp * 120 / 280 * power),
            "42.9% max HP team heal + 65 shield",
        ),
        "formation": (
            h.get("circuit_resonance", 20),
            "Fixed Resonance pulse; no damage",
            0,
            "+18% attack speed, +12% damage, -10% incoming damage",
        ),
    }
    sp, ss, up, us = formulas[id]
    skill.update(power=sp, scaling=ss)
    ult.update(power=up, scaling=us)
    skill["cooldown"] = h.get("circuit_cooldown", skill["cooldown"])
    if id == "formation":
        h["basic"]["geometry"] = geometry("circle", h.get("aura_range", 1.5), 99)
    if id == "monk" and h.get("staff_arc"):
        skill["geometry"] = geometry("front_circle", 1.25, 99)
    if id == "fire":
        skill["splash_radius"] = h.get("skill_radius", 0.9)
    skill["targets"] = h.get("shield_targets", skill["geometry"]["targets"])
    if id == "herbalist":
        h["heal_amount"] = round(hp * h.get("heal_amount", 45) / 280 * power)
    if id == "gatherer":
        h["basic"]["cooldown"] = h["orb_interval"]
    if id == "formation":
        h["basic"][
            "scaling"
        ] = f"+{round(h['attack_speed_buff']*100)}% ally attack speed"
    descriptions = {
        "gatherer": (
            f"First 3 orbs gain +5 Qi if a Formation Adept is within radius 1.5 (3x3 centers).",
            "Four pulses of 12 Qi, 1.5s apart: 48 total before the shared cap. Remaining pulses stop if Yun dies.",
        ),
        "sword": (
            f"Hit up to 3 enemies ahead in this lane within 3.5 tiles for {sp} Sword damage; interrupt non-bosses for 0.3s.",
            f"10 blades of {up} Sword damage are distributed among up to 3 living enemies in this lane over 1.2s.",
        ),
        "fire": (
            f"Requires 2 targets in primary range. Deal {sp} Fire damage in radius {h.get('skill_radius',.9)} around impact; secondary enemies take {round(h.get('splash_factor',.6)*100)}%. Burn 8/s for {h.get('burn_duration',3)}s.",
            f"Mark the 3 most advanced enemies in this lane. After 0.8s each point explodes in radius 1.1 for {up} Fire damage; scorched circles deal 8/s for 4s.",
        ),
        "frost": (
            f"Shield the {h.get('shield_targets',1)} lowest-HP injured allies in a radius-2 circle (13 centers), absorbing {sp} for {h.get('shield_duration',4)}s.",
            f"Hit every enemy in this lane for {up} Ice damage; freeze {round(1.75*h.get('cc_duration',1),2)}s. Bosses receive a 25% slow for 2s instead.",
        ),
        "monk": (
            f"Hit eligible enemies in {'a forward radius-1.25 circle, including adjacent lanes' if h.get('staff_arc') else 'this lane up to 1.25 tiles ahead'} for {sp}; push normal enemies {h.get('knockback',.35)} tiles.",
            f"Shield self for {round(hp*.5)} (50% max HP), 5s. Hit every enemy in this lane for {up} Physical damage; taunt 2.5s.",
        ),
        "lightning": (
            f"Hit a flying/conductive primary target for {sp}, otherwise {round(atk*55/30)}. Chain {round(atk*35/30)} to 2 enemies within radius 1.5 of it.",
            f"After 0.6s, strike up to 5 enemies in this lane for {up} Lightning damage each; add 2 Conductive stacks.",
        ),
        "herbalist": (
            f"Choose lowest-HP ally in a radius-3 circle (29 centers). Cleanse curse and heal {sp}, or shield for {h.get('cleanse_shield',45)} for {h.get('shield_duration',3)}s.",
            f"Heal every living ally on the 5-lane board for {up}; cleanse curse and add 65 shield for 3s. Cannot revive or repair the gate.",
        ),
        "formation": (
            f"Choose 3 other allies inside radius 2.5 (21 centers), highest Dao first. Grant {h.get('circuit_resonance',20)} Dao"
            + (f" and {h.get('circuit_mana')} mana" if h.get("circuit_mana") else "")
            + " each.",
            "For 6s, allies inside radius 2 (13 centers) gain 18% attack speed, 12% damage and 10% damage reduction. Does not stack with another Grand Array.",
        ),
    }
    skill["description"], ult["description"] = descriptions[id]
    if id == "gatherer":
        h["description"] = (
            "Economy support: up to three gatherers. Their respective orb values are 100% / 80% / 60%. Shared Qi capacity is 320 before Treasury talent."
        )
        h["basic"][
            "scaling"
        ] = f"{h['orb_value']} Qi / {h['orb_interval']}s before duplicate modifiers"
    if id == "herbalist":
        h["basic"]["geometry"] = geometry("circle", 3, h.get("heal_targets", 1))
        h["basic"]["geometry"]["exclude_self"] = True
        h["basic"]["geometry"]["offsets"].remove([0, 0])
        h["basic"]["geometry"][
            "description"
        ] = "Circle radius 3: 28 other tile centers; this hero cannot heal herself."
        h["basic"][
            "scaling"
        ] = f"Heal {h['heal_amount']} (+15 with Herb charge), no self-heal"
    if id == "lightning":
        h["basic"]["scaling"] = (
            f"100% / 70% / 45% ATK"
            + (" / 35%" if h.get("chains", 3) == 4 else "")
            + f"; chain radius {h.get('chain_range',1.25)}"
        )
    h["basic"]["description"] = {
        "gatherer": f"Generate {h.get('orb_value',20)} Qi every {h.get('orb_interval',10)}s for 8 mana; duplicate Yuns yield 100/80/60%. Maximum 3. Shared cap 320 before Treasury; orbs auto-collect after 1.2s.",
        "sword": f"Launch a blade down this lane up to {h['range']} tiles. Every third landed attack gains {15 if h.get('branch')=='B' else 25}% damage. "
        + ("Pierces 2 enemies." if h.get("pierce") else "Hits 1 enemy."),
        "fire": f"Hit the first enemy in this lane, radius-{h.get('splash_radius',.55)} splash at {round(h.get('splash_factor',.6)*100)}% power. Every fourth hit burns for {h.get('burn_damage',14 if h.get('branch')=='A' else 10)}/s for {h.get('burn_duration',3)}s; same-source burn refreshes.",
        "frost": f"Hit one enemy in this lane; slow {15 if h.get('branch')=='A' else 20}% for 2s. Every third hit adds a Frost stack; {2 if h.get('branch')=='A' else 3} stacks freeze {round(1.1*h.get('cc_duration',1),2)}s. Bosses are slowed instead.",
        "monk": "Strike one enemy ahead in this lane within 1 tile. This hero blocks ordinary ground enemies; flying Yaksha pass over him.",
        "lightning": f"Chain up to {h.get('chains',3)} enemies, radius {h.get('chain_range',1.25)} between jumps, including adjacent lanes. Each hit adds Conductive; 3 marks add {h.get('conductive_damage',24)} damage and break {h.get('armor_break',3)} armor for 3s.",
        "herbalist": f"Heal the lowest-HP other ally within radius 3 for {h.get('heal_amount',45)}, spending 6 mana. If no ally is injured, store up to 2 Herb charges; a charge adds 15 healing. "
        + (
            "Second ally receives 70% base healing."
            if h.get("heal_targets", 1) > 1
            else "One ally per pulse."
        ),
        "formation": f"Continuous aura: +{round(h.get('attack_speed_buff',.08)*100)}% attack speed inside radius {h.get('aura_range',1.5)}. Does not stack. "
        + (
            "No role-diversity protection."
            if h.get("branch") == "A"
            else "Three distinct roles inside radius 1.5 add 3% damage reduction."
        ),
    }[id]
    if id == "herbalist" and h.get("cleanse_count", 1) > 1:
        h["skill"][
            "description"
        ] = f"Lowest-HP ally within radius 3: remove curse plus one spore/disable effect and heal {sp}. With no debuff, grant {h.get('cleanse_shield',45)} shield for {h.get('shield_duration',3)}s."
    return h


def validate_upgrades(upgrades):
    if not isinstance(upgrades, dict) or len(upgrades) > 8:
        raise ValueError("Upgrades must map at most eight heroes to talent paths.")
    for id, value in upgrades.items():
        if not isinstance(id, str) or id not in HEROES:
            raise ValueError("Unknown cultivator in talent data.")
        if isinstance(value, str):
            if value not in ("A", "B"):
                raise ValueError("Talent branch must be A or B.")
        elif isinstance(value, dict):
            rank = value.get("rank")
            branch = value.get("branch")
            if (
                branch not in ("A", "B")
                or isinstance(rank, bool)
                or not isinstance(rank, int)
                or not 0 <= rank <= 5
            ):
                raise ValueError("Talent rank must be 0-5 on branch A or B.")
        else:
            raise ValueError("Invalid talent selection.")
    return deepcopy(upgrades)
