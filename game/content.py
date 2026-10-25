"""Authored content for VAN DAO: Immortal War.

The campaign is a compact, locally playable adaptation of the supplied design
brief. Combat values are intentionally calibrated for short browser encounters.
All data is JSON serializable and shared by the Python simulation and canvas UI.
"""
from copy import deepcopy

VERSION = "1.6.0"

REGIONS = [
    {"id": "wharf", "name": "Glass Lantern Wharf", "subtitle": "The river remembers", "chapter": 1, "color": "#58c8bd", "description": "Protect a lantern-lit town as the corrupted river rises.", "mechanic": "Tide Cycle", "intro": "Keeper, the lanterns are going dark. Gather Spirit Qi and hold the river gate.", "outro": "The River Lord was bound to a broken seal. Its last breath points toward the Azure Terraces."},
    {"id": "terrace", "name": "Azure Spirit Terraces", "subtitle": "Where the ley-lines fracture", "chapter": 2, "color": "#a9d782", "description": "Capture jade ley nodes and withstand the mountain wind.", "mechanic": "Ley Nodes & Wind", "intro": "The mountain gardens have fallen silent. Let the old ley nodes strengthen your formation.", "outro": "Behind the mountain armor lies a corrupted core. The final ley-line descends into the imperial tomb."},
    {"id": "tomb", "name": "Ten-Thousand-Bone Mausoleum", "subtitle": "No emperor reigns forever", "chapter": 3, "color": "#b9a4db", "description": "Pierce the grave mist and end the Bone-Crown Emperor's court.", "mechanic": "Mist & Resurrection", "intro": "A nameless court waits beneath the earth. Break its seals before the dead can rise again.", "outro": "The crown is broken. The river, mountain and ancient gate breathe as one again."},
]


def _hero(id, name, title, role, color, cost, hp, armor, damage, damage_type, interval, windup, range, projectile_speed, cooldown, description, skill, ultimate, branches, unlock="start", **extra):
    data = dict(id=id, name=name, title=title, role=role, color=color, cost=cost, hp=hp, armor=armor, damage=damage, damage_type=damage_type, interval=interval, windup=windup, range=range, projectile_speed=projectile_speed, cooldown=cooldown, unlock=unlock, unlock_chapter=0 if unlock == "start" else (1 if unlock == "wharf-3" else 2), description=description, skill=skill, ultimate=ultimate, branches=branches, resistances={})
    data.update(extra)
    return data


def _branch(name, description, **stats):
    return {"name": name, "description": description, "cost": 35, "stats": stats}


HEROES = {
    "gatherer": _hero(
        "gatherer", "Little Daoist Yun", "Qi Gatherer", "economy", "#63d59d", 50, 170, 0, 0, "spirit", 8.0, 0, 0, 0, 8.0,
        "A jade-gourd disciple who generates 25 Spirit Qi every 8 seconds. Protect him behind your fighters.",
        {"name": "Gathering Breath", "description": "Produce a 25-Qi spirit orb every 8 seconds; orbs collect automatically.", "cooldown": 8.0},
        {"name": "Spirit Well", "description": "Generate 60 Qi over 6 seconds while the well survives.", "duration": 6, "qi": 60},
        {"A": _branch("Steady Breath", "Gather every 6.5 seconds instead of 8.", orb_interval=6.5), "B": _branch("Jade Vessel", "Each spirit orb is worth 30 Qi instead of 25.", orb_value=30)},
        orb_interval=8.0, orb_value=25, resistances={"spirit": -0.10}),
    "sword": _hero(
        "sword", "Shen Zhu", "Bamboo Sword Cultivator", "damage", "#a4ead9", 75, 260, 2, 36, "sword", 1.35, .35, 5.5, 7.0, 7.0,
        "Reliable ranged lane damage. Every third landed sword deals bonus damage; his crescent cuts through a crowd.",
        {"name": "Crosswind Cut", "description": "A 48-damage crescent pierces up to three nearby enemies.", "cooldown": 8.0, "damage": 48, "range": 3.5, "pierce": 3},
        {"name": "Ten Thousand Bamboo Blades", "description": "Send ten 22-damage blades through the selected lane.", "damage": 22, "hits": 10},
        {"A": _branch("Piercing Bamboo", "Basic blades pierce a second enemy, but deal 32 damage.", damage=32, pierce=2), "B": _branch("Quick Draw", "Attack every 1.10 seconds; third-hit bonus becomes 15%.", interval=1.10, third_hit_bonus=.15)},
        pierce=1, third_hit_bonus=.25),
    "fire": _hero(
        "fire", "Hong Lian", "Fire Lotus Immortal", "damage", "#f28b78", 125, 230, 0, 52, "fire", 2.0, .65, 4.8, 5.0, 12.0,
        "Lotus embers burst on impact, damaging clustered enemies. Repeated hits ignite a lingering burn.",
        {"name": "Blooming Furnace", "description": "A 70-damage lotus bloom scorches nearby enemies.", "cooldown": 10.0, "damage": 70, "radius": .9},
        {"name": "Crimson Lotus Cataclysm", "description": "Mark three advanced enemies, then erupt for 150 Fire damage.", "damage": 150, "radius": 1.1, "targets": 3},
        {"A": _branch("Ashen Lotus", "Burn deals 14 damage a tick, but basic embers deal 48.", damage=48, burn_damage=14), "B": _branch("Many-Petal Bloom", "Larger explosions deal 70% damage to secondary targets.", splash_radius=.75, splash_factor=.70)},
        splash_radius=.55, splash_factor=.60, burn_damage=10, burn_duration=3.0),
    "frost": _hero(
        "frost", "Bing Ruo", "Frost Talisman Adept", "control", "#92ddec", 100, 245, 1, 22, "ice", 1.55, .40, 5.0, 6.0, 10.0,
        "Cold seals slow enemies. Accumulated frost briefly freezes common foes; Ice Mirror shields a wounded ally.",
        {"name": "Ice Mirror", "description": "Shield a nearby wounded ally for 70 damage, lasting 4 seconds.", "cooldown": 9.0, "shield": 70, "duration": 4.0},
        {"name": "Thousand-Year Frost", "description": "Deal 85 Ice damage and freeze the lane; bosses resist the freeze.", "damage": 85, "freeze": 1.75},
        {"A": _branch("Deep Winter", "Freeze with two frost stacks, but ordinary slow falls to 15%.", frost_stacks=2, slow=.15), "B": _branch("Frost Mirror", "Ice Mirror absorbs 95 damage for 3 seconds.", shield_amount=95, shield_duration=3.0)},
        unlock="wharf-3", slow=.20, frost_stacks=3, shield_amount=70, shield_duration=4.0),
    "monk": _hero(
        "monk", "Jin Shan", "Diamond Guardian Monk", "tank", "#e6b75c", 100, 900, 12, 44, "physical", 1.45, .45, 1.0, 0, 11.0,
        "A bronze-robed guardian who blocks the lane, absorbs punishment and knocks ordinary enemies backward.",
        {"name": "Earth-Shaking Staff", "description": "Slam for 60 damage and push enemies 0.35 tiles backward.", "cooldown": 7.5, "damage": 60, "range": 1.25, "knockback": .35},
        {"name": "Mountain Holds the Sky", "description": "Gain a 450-point shield and send a 90-damage shockwave along the lane.", "shield": 450, "duration": 5.0, "damage": 90},
        {"A": _branch("Iron Sutra", "Gain 1,080 HP and 14 armor, but attack damage falls to 38.", hp=1080, armor=14, damage=38), "B": _branch("Resonant Staff", "Deal 52 basic damage and knock enemies back 0.45 tiles.", damage=52, knockback=.45)},
        knockback=.35, physical_reduction=.10),
    "lightning": _hero(
        "lightning", "Lei Xun", "Lightning Sword Wanderer", "damage", "#b8a3f2", 175, 300, 2, 30, "lightning", 1.65, .30, 5.2, 16.0, 14.0,
        "Purple arcs chain between enemies. Conductive marks crack armor and punish flying threats.",
        {"name": "Thunder Step", "description": "Strike a flying or conductive target for 80 damage, chaining 35 to two others.", "cooldown": 8.0, "damage": 80, "chain_damage": 35},
        {"name": "Nine Heavens Thunderfall", "description": "Strike up to five enemies for 125 Lightning damage each.", "damage": 125, "targets": 5},
        {"A": _branch("Forked Sky", "Chain to four targets; final arc deals 35% damage.", chains=4, last_chain_factor=.35), "B": _branch("Armor-Cracking Thunder", "Conductive marks remove 5 armor; bonus damage falls to 18.", armor_break=5, conductive_damage=18)},
        unlock="terrace-3", chains=3, last_chain_factor=.45, armor_break=3, conductive_damage=24),
    "herbalist": _hero(
        "herbalist", "Mu Qing", "Spirit Herbalist", "support", "#a4cb7a", 125, 280, 1, 0, "wood", 6.0, .2, 3.0, 0, 12.0,
        "Heals the most wounded nearby ally every six seconds. Clear-Pulse removes harmful effects or grants a shield.",
        {"name": "Clear-Pulse Incantation", "description": "Cleanse a nearby ally and heal 35 HP, or grant a 45-point shield.", "cooldown": 10.0, "heal": 35, "shield": 45},
        {"name": "Rain of Green Heaven", "description": "Heal every ally for 120 HP, cleanse one effect and grant a 65-point shield.", "heal": 120, "shield": 65, "duration": 3.0},
        {"A": _branch("Long-Life Medicine", "Heal 58 HP every 6.8 seconds.", heal_amount=58, heal_interval=6.8), "B": _branch("Purifying Leaves", "Cleanse two effects; fallback shields last 4 seconds.", cleanse_count=2, shield_duration=4.0)},
        unlock="wharf-3", heal_amount=45, heal_interval=6.0, heal_range=3.0, cleanse_count=1, shield_duration=3.0),
    "formation": _hero(
        "formation", "Zhen Luo", "Eight-Trigram Formation Adept", "support", "#7dc7b6", 150, 320, 3, 0, "spirit", 9.0, .3, 1.5, 0, 13.0,
        "A bronze-compass master whose formation increases nearby attack speed and feeds allies' Ultimate gauges.",
        {"name": "Qi Circuit", "description": "Grant 20 Resonance to up to three connected allies.", "cooldown": 9.0, "resonance": 20, "range": 2.5, "targets": 3},
        {"name": "Grand Eight-Trigram Array", "description": "For six seconds, nearby allies gain attack speed, damage and protection.", "duration": 6.0, "radius": 2.0, "attack_speed": .18, "damage_bonus": .12, "reduction": .10},
        {"A": _branch("Swift Array", "Aura attack speed rises to 12%; role-diversity protection is lost.", attack_speed_buff=.12, diversity_reduction=0), "B": _branch("Deep Circuit", "Qi Circuit grants 25 Resonance with an 11-second cooldown.", circuit_resonance=25, circuit_cooldown=11.0)},
        unlock="terrace-3", aura_range=1.5, attack_speed_buff=.08, diversity_reduction=.03, circuit_resonance=20, circuit_cooldown=9.0),
}


def _enemy(id, name, role, hp, armor, damage, damage_type, interval, windup, speed, description, **extra):
    data = dict(id=id, name=name, role=role, hp=hp, armor=armor, damage=damage, damage_type=damage_type, interval=interval, windup=windup, speed=speed, range=.8, resistances={}, description=description, boss=False, shield=0, qi_drop=0)
    data.update(extra)
    return data


ENEMIES = {
    "tide": _enemy("tide", "Tide Miao", "swarm", 95, 0, 18, "physical", 1.6, .35, .70, "A quick waterbound runner. Low health, dangerous in packs.", resistances={"ice": -.10}, water=True),
    "lantern": _enemy("lantern", "Lantern Demon", "support", 140, 1, 12, "spirit", 1.8, .45, .40, "Its murk lantern grants nearby enemies shields. Bursts on defeat.", range=1.0, qi_drop=15, ability_interval=6.0, shield_amount=25),
    "drowned": _enemy("drowned", "Drowned Corpse", "ambusher", 230, 3, 36, "water", 2.0, .6, .32, "A river corpse that submerges and rises to grab its defender.", water=True, ability_interval=7.0),
    "hound": _enemy("hound", "Ironback Mountain Hound", "armored", 520, 18, 70, "physical", 2.4, .9, .22, "Stone plates absorb the first hits. Rushes across unguarded ground.", shield=260, qi_drop=20, ability_interval=10.0),
    "yaksha": _enemy("yaksha", "Windwing Yaksha", "flying", 180, 2, 32, "physical", 1.65, .4, .55, "A winged raider that dives toward vulnerable backline allies.", flying=True, resistances={"physical": .15}, ability_interval=7.0),
    "drainer": _enemy("drainer", "Qi-Draining Adept", "ranged", 210, 3, 18, "spirit", 2.1, .75, .30, "Channels a visible siphon that steals Qi. Interrupt it before the pulse.", range=3.5, ability_interval=8.0, qi_drop=20),
    "soul": _enemy("soul", "Faceless Soul", "spectral", 190, 0, 28, "spirit", 1.9, .65, .37, "Fades through grave mist and curses allies with each touch.", spectral=True, ability_interval=5.5),
    "rottenwood": _enemy("rottenwood", "Rottenwood Corpse", "regenerator", 440, 7, 42, "wood", 2.2, .8, .18, "Regenerates when left unhurt. Keep steady damage on it to interrupt recovery.", ability_interval=9.0, resistances={"fire": -.15}),
    "swordcorpse": _enemy("swordcorpse", "Sword-Swallowing Ancient Corpse", "counter", 620, 11, 58, "spirit", 2.6, .9, .20, "Its glowing chest absorbs small blades, then returns stored power.", ability_interval=6.0),
    "riverlord": _enemy("riverlord", "Crimson-Scale River Lord", "boss", 1800, 8, 110, "water", 4.0, 1.0, .10, "A crimson river dragon whose waterbound summons and sweeping tides grow fiercer through three phases.", boss=True, range=1.3, resistances={"water": .25, "fire": -.10, "ice": .10, "lightning": -.05}, cc_reduction=.75, slow_effectiveness=.5, phase_names=["River Claim", "Flooded Court", "Crimson Deluge"], ability_interval=11.0, qi_drop=100),
    "mountainlord": _enemy("mountainlord", "Ironback Mountain Lord", "boss", 2400, 14, 140, "physical", 4.8, 1.1, .09, "Three granite plates conceal a corrupted core. Marked lane tremors punish crowded formations.", boss=True, range=1.4, shield=540, plates=3, plate_hp=180, resistances={"physical": .10, "lightning": -.20}, cc_reduction=.75, slow_effectiveness=.5, phase_names=["Guarded Advance", "Broken Mountain", "Core of the Mountain"], ability_interval=12.0, qi_drop=125),
    "boneemperor": _enemy("boneemperor", "Bone-Crown Emperor", "boss", 3000, 10, 115, "spirit", 4.2, .9, .085, "The dead court obeys its crown. Break the seal altars and survive the final royal decree.", boss=True, range=2.5, resistances={"spirit": -.10, "physical": .15, "ice": .10}, cc_reduction=.85, slow_effectiveness=.4, phase_names=["Court of the Nameless", "Ten-Thousand Souls", "Crown of Extinction"], ability_interval=12.0, qi_drop=150),
}


ENEMY_ABILITIES = {'tide': ('Tidal Rush', 'Moves 15% faster during high tide.', 'Frost slows its sprint.'), 'lantern': ('Murk Lantern', 'Grants nearby enemies 25 shield every 6s; bursts after death.', 'Burn down the support before the pack arrives.'), 'drowned': ('Submerge', 'Becomes hidden during the high-tide phase.', 'Fire and lightning can strike submerged targets.'), 'hound': ('Shoulder Rush', 'After a 1.1s tell, rushes 1.5 tiles if no nearby blocker. Starts with 260 shield.', 'Place a guardian ahead of mixed damage.'), 'yaksha': ('Winged Dive', 'Flies over blockers for 4.5s in each 7s cycle, then hunts support.', 'Lightning prioritizes flying targets.'), 'drainer': ('Qi Siphon', 'Channels for 1s, then steals Qi. Interrupt the channel.', 'Stun it or kill it before the pulse.'), 'soul': ('Faceless Fade', 'Phases near the end of each 5.5s cycle. Spirit hits curse heroes.', 'Fire, lightning or the soul bell pierce its fade.'), 'rottenwood': ('Spore Cloud', 'A warned spore patch damages and slows allies. Recovers 30 HP while unhurt.', 'Keep dealing damage; spread supports out.'), 'swordcorpse': ('Sword Swallow', 'Absorbs light swords for 1s and returns their energy in its next blow.', 'Use fire, lightning or a monk staff.'), 'riverlord': ('Tidal Sweep', 'Marks two lanes, then sweeps for increasing Water damage. Three HP phases summon waterbound enemies.', 'Shield the marked lanes and preserve sustained damage.'), 'mountainlord': ('Granite Plates', 'Three plates absorb hits without spillover. Warned tremors target crowded lanes.', 'Mix lightning damage with tanks and healing.'), 'boneemperor': ('Royal Decree', 'Marks up to three lanes. Seal altars resurrect souls and grant boss shields.', 'Destroy the three altars; bring healing and formation support.')}
for _enemy_id, (_ability_name, _ability_text, _counter) in ENEMY_ABILITIES.items():
    ENEMIES[_enemy_id]["abilities"] = [{"name": _ability_name, "description": _ability_text}]
    ENEMIES[_enemy_id]["counterplay"] = _counter


def _spawn(type, lane, count=1, gap=.8):
    return dict(type=type, lane=lane, count=count, gap=gap)


def _wave(at, *spawns):
    return dict(at=at, spawns=list(spawns))


def _stage(id, name, region, index, description, mechanic, waves, duration, reward, boss=None, mastery=None, **extra):
    data = dict(id=id, name=name, region=region, index=index, chapter=index // 3 + 1, number=index % 3 + 1, description=description, mechanic=mechanic, waves=waves, duration=duration, reward=reward, boss=boss, gate=3, mastery=mastery or ["Win without a gate breach", "Finish with three different hero roles"], next=None)
    data.update(extra)
    return data


STAGES = {
    "wharf-1": _stage("wharf-1", "Lanterns Going Dark", "wharf", 0,
        "Place Yun behind Shen Zhu in the middle lane. Prepare the lanes above and below as the next waves arrive.", "Tide Cycle",
        [_wave(8, _spawn("tide", 2)), _wave(21, _spawn("tide", 1)), _wave(38, _spawn("tide", 3)), _wave(47, _spawn("tide", 2, 2, 1.4)), _wave(60, _spawn("tide", 1), _spawn("tide", 3))],
        76, {"stones": 45, "insight": 1}, mastery=["Keep all three gate seals", "Gather 100 Qi from Yun"], tutorial=True, water_lanes=[1, 3]),
    "wharf-2": _stage("wharf-2", "The Drowned Ferry", "wharf", 1,
        "The ferry is broken. Lanterns shield the drowned while swift runners test the outer lanes.", "Tide Cycle",
        [_wave(8, _spawn("tide", 2)), _wave(20, _spawn("lantern", 1)), _wave(31, _spawn("drowned", 3)), _wave(42, _spawn("tide", 0, 2, 1.5)), _wave(52, _spawn("tide", 4, 2, 1.5)), _wave(63, _spawn("drowned", 2), _spawn("tide", 2)), _wave(75, _spawn("lantern", 1), _spawn("tide", 3, 2))],
        96, {"stones": 55, "insight": 1}, water_lanes=[1, 3], blocked_tiles=[{"lane": 2, "col": 5}], bridge_opens=42),
    "wharf-3": _stage("wharf-3", "River King's Claim", "wharf", 2,
        "The Crimson-Scale River Lord claims the gate. Shelter your formation from the marked tide sweep.", "Tide Cycle",
        [_wave(10, _spawn("tide", 2)), _wave(22, _spawn("drowned", 1)), _wave(34, _spawn("lantern", 3), _spawn("tide", 3)), _wave(42, _spawn("riverlord", 2)), _wave(54, _spawn("tide", 1, 2)), _wave(67, _spawn("tide", 3, 2))],
        112, {"stones": 90, "insight": 2, "relic": "tide_pearl", "material": "Tide Jade", "unlocks": ["frost", "herbalist"]}, boss="riverlord", water_lanes=[1, 3], mastery=["Defeat all three River Lord phases", "Keep at least two gate seals"]),
    "terrace-1": _stage("terrace-1", "Broken Ley Garden", "terrace", 3,
        "Build beside the jade ley nodes. Fire and sustained damage can crack the mountain hounds' stone plates.", "Ley Nodes & Wind",
        [_wave(8, _spawn("tide", 2)), _wave(20, _spawn("hound", 2)), _wave(34, _spawn("tide", 1), _spawn("rottenwood", 3)), _wave(48, _spawn("hound", 1)), _wave(62, _spawn("rottenwood", 2), _spawn("tide", 4)), _wave(76, _spawn("hound", 3), _spawn("tide", 0))],
        112, {"stones": 65, "insight": 1}, nodes=[{"lane": 1, "col": 3}, {"lane": 2, "col": 2}, {"lane": 3, "col": 4}], mastery=["Deploy beside all three ley nodes", "Win with two damage types"]),
    "terrace-2": _stage("terrace-2", "Wings Above the Terrace", "terrace", 4,
        "Winged yaksha dive toward your support. The Qi-Draining Adept's siphon must be answered before it finishes.", "Ley Nodes & Wind",
        [_wave(8, _spawn("tide", 2)), _wave(18, _spawn("yaksha", 2)), _wave(30, _spawn("drainer", 1)), _wave(42, _spawn("hound", 3), _spawn("tide", 3)), _wave(54, _spawn("yaksha", 0), _spawn("yaksha", 4)), _wave(66, _spawn("drainer", 2), _spawn("yaksha", 1)), _wave(78, _spawn("rottenwood", 3), _spawn("yaksha", 2)), _wave(90, _spawn("hound", 1), _spawn("drainer", 4))],
        120, {"stones": 75, "insight": 1}, nodes=[{"lane": 1, "col": 3}, {"lane": 2, "col": 2}, {"lane": 3, "col": 4}]),
    "terrace-3": _stage("terrace-3", "Heart of the Mountain", "terrace", 5,
        "Break the Mountain Lord's three plates and protect the marked lanes when its granite core awakens.", "Ley Nodes & Wind",
        [_wave(10, _spawn("tide", 2)), _wave(23, _spawn("hound", 1)), _wave(35, _spawn("yaksha", 3)), _wave(44, _spawn("mountainlord", 2)), _wave(59, _spawn("drainer", 1)), _wave(75, _spawn("yaksha", 3, 2))],
        128, {"stones": 110, "insight": 2, "relic": "wind_compass", "material": "Azure Ley Shard", "unlocks": ["lightning", "formation"]}, boss="mountainlord", nodes=[{"lane": 1, "col": 3}, {"lane": 2, "col": 2}, {"lane": 3, "col": 4}], mastery=["Break all three armor plates", "Lose no more than one hero"]),
    "tomb-1": _stage("tomb-1", "The Unmarked Gate", "tomb", 6,
        "Souls emerge from the grave mist. Fire blooms, lightning and the reveal shrine can catch them between phases.", "Mist & Resurrection",
        [_wave(8, _spawn("tide", 2)), _wave(20, _spawn("soul", 1)), _wave(32, _spawn("soul", 3, 2)), _wave(44, _spawn("rottenwood", 2), _spawn("soul", 2)), _wave(56, _spawn("soul", 0), _spawn("soul", 4)), _wave(72, _spawn("swordcorpse", 1), _spawn("soul", 3, 2))],
        108, {"stones": 85, "insight": 1}, mist_lanes=[1, 3], mastery=["Reveal and defeat six Faceless Souls", "Win without three Curse stacks"]),
    "tomb-2": _stage("tomb-2", "The Coffin Corridor", "tomb", 7,
        "Ancient corpses swallow light blades. Use fire, frost or a guardian's staff while the spectral chest is open.", "Mist & Resurrection",
        [_wave(8, _spawn("soul", 2)), _wave(20, _spawn("swordcorpse", 2)), _wave(32, _spawn("rottenwood", 1), _spawn("soul", 1)), _wave(44, _spawn("swordcorpse", 3)), _wave(56, _spawn("soul", 0, 2)), _wave(68, _spawn("drainer", 4), _spawn("soul", 4)), _wave(80, _spawn("swordcorpse", 1), _spawn("soul", 3)), _wave(92, _spawn("swordcorpse", 2), _spawn("rottenwood", 3))],
        126, {"stones": 95, "insight": 1}, mist_lanes=[0, 2, 4]),
    "tomb-3": _stage("tomb-3", "The Bone-Crown Emperor", "tomb", 8,
        "Destroy the court's seal altars, survive its royal decrees, and restore the world's broken ley-lines.", "Mist & Resurrection",
        [_wave(10, _spawn("soul", 2)), _wave(23, _spawn("swordcorpse", 1)), _wave(35, _spawn("rottenwood", 3)), _wave(46, _spawn("boneemperor", 2)), _wave(62, _spawn("soul", 1)), _wave(78, _spawn("soul", 3))],
        140, {"stones": 160, "insight": 3, "relic": "soul_bell", "material": "Mausoleum Seal Fragment", "campaign_complete": True}, boss="boneemperor", mist_lanes=[1, 3], altars=[{"lane": 1, "x": 7.0}, {"lane": 2, "x": 7.5}, {"lane": 3, "x": 7.0}], mastery=["Destroy every seal altar", "Defeat all three emperor phases"]),
}

# Reinforcement chapters extend the existing campaign; no stages or heroes are added.
for _stage_data in STAGES.values():
    _tutorial = _stage_data.get("tutorial", False)
    _boss = _stage_data.get("boss")
    _waves = [deepcopy(w) for w in _stage_data["waves"] if not any(ENEMIES[s["type"]]["boss"] for s in w["spawns"])]
    _target = 12 if _tutorial else 14 + _stage_data["chapter"] * 2
    _pool = {"wharf": ["tide", "lantern", "drowned"], "terrace": ["tide", "hound", "yaksha", "drainer", "rottenwood"], "tomb": ["soul", "swordcorpse", "rottenwood", "drainer"]}[_stage_data["region"]]
    while len(_waves) < _target:
        _n = len(_waves)
        _at = _waves[-1]["at"] + (17 if _tutorial else 15)
        _lane = [2, 1, 3][_n % 3] if _tutorial else (_n * 2 + _stage_data["index"]) % 5
        _type = "tide" if _tutorial else _pool[_n % len(_pool)]
        _pack = (3 + int(_n >= 9)) if _tutorial else (2 + int(_n >= 10))
        _spawns = [_spawn(_type, _lane, _pack, 1.6)]
        if not _tutorial and _n % 3 == 0:
            _spawns.append(_spawn(_pool[(_n + 1) % len(_pool)], (_lane + 2) % 5, 2, 2))
        _waves.append(_wave(_at, *_spawns))
    if _boss:
        _waves.append(_wave(_waves[-1]["at"] + 22, _spawn(_boss, 2)))
    _stage_data["waves"] = _waves
    _stage_data["duration"] = _waves[-1]["at"] + (100 if _boss else 35)
    _stage_data["columns"] = 12
    _stage_data["deployment_columns"] = list(range(1, 10))
    _stage_data["stronghold"] = {"wharf": "Lantern Palace", "terrace": "Azure Sky Pavilion", "tomb": "Ancestral Spirit Shrine"}[_stage_data["region"]]
    _stage_data["enemy_count"] = sum(s["count"] for w in _waves for s in w["spawns"])
    _stage_data["duration_label"] = "3-4 min" if _tutorial else ("5-7 min" if _boss else "4-5 min")

_stage_ids = list(STAGES)
for _index, _id in enumerate(_stage_ids[:-1]):
    STAGES[_id]["next"] = _stage_ids[_index + 1]

RELICS = {
    "tide_pearl": {"id": "tide_pearl", "name": "Jade Tide Pearl", "color": "#7ce1d8", "unlock": "wharf-3", "description": "Once per battle, grant every living hero a 120-point shield for 5 seconds.", "effect": "shield", "shield": 120, "duration": 5.0},
    "wind_compass": {"id": "wind_compass", "name": "Eight-Trigram Wind Compass", "color": "#e4cb80", "unlock": "terrace-3", "description": "Once per battle, grant all heroes 35 Resonance and haste for 8 seconds.", "effect": "haste", "resonance": 35, "duration": 8.0},
    "soul_bell": {"id": "soul_bell", "name": "Soul-Sealing Bronze Bell", "color": "#b9b0e6", "unlock": "tomb-3", "description": "Once per battle, reveal and interrupt enemies, block resurrection and cleanse allied curses.", "effect": "reveal", "duration": 6.0},
}


from .design import enrich

enrich(HEROES, ENEMIES, STAGES, REGIONS)

from .trials import build_trials, SQUAD_ROLES
TRIALS = build_trials(STAGES)


def catalog():
    """Return detached public content data; callers cannot mutate the rules."""
    from .nursery import NURSERY
    from .sanctuary import SANCTUARY
    return deepcopy({"hub": SANCTUARY, "trials": list(TRIALS.values()), "squad_roles": SQUAD_ROLES, "side_modes": [NURSERY], "version": VERSION, "regions": REGIONS, "heroes": list(HEROES.values()), "enemies": list(ENEMIES.values()), "stages": list(STAGES.values()), "relics": list(RELICS.values()), "title": "VAN DAO: IMMORTAL WAR", "tagline": "Guard the last immortal gate.", "rules": {"lanes": 5, "columns": 12, "deployment_columns": list(range(1, 10)), "lane_wards": 1, "starting_qi": 150, "passive_qi": 30, "passive_interval": 12, "qi_cap": 320, "gate": 3, "simulation_hz": 60}})
