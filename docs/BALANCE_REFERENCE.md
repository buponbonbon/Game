# VAN DAO 1.2 balance reference

Python is authoritative. Base content is in `game/content.py`, version-1.2
contracts in `game/design.py`, and talent-adjusted previews in `game/rules.py`.
The in-game field manual uses these same effective stats, including live units.

## Economy and combat

Five lanes, twelve columns; deploy in columns 1–9. Column 0 holds the emergency
artifact. Three breaches lose the gate; a boss breach consumes all three seals.
Start with 150 Qi, or 175 after the River Lord. Passive Qi is 30/12s, increasing
to 32 after the Mountain Lord. Capacity is 320. Every 24s, upkeep costs
`ceil(living heroes / 6)` Qi. Pause freezes all simulation clocks.

Yun spends 8 mana to make a 20-Qi orb each 10s. At most three Yuns may coexist;
their orb yields are 100%, 80%, 60% by deployment order. A-rank-3 reduces the
interval to 8s; B-rank-3 raises raw value to 24. Orbs collect automatically after
1.2s. The first three orbs gain +5 with a Formation Adept within radius 1.5.
Yun's ultimate costs 85 mana, 25 Qi and 100 Dao; four surviving-owner pulses
produce 48 Qi total, a net gain of 23 before the cap, on a 60s cooldown.

Positive damage subtracts armor, then resistance, with minimum positive damage
of 1. Hero skill powers scale from effective ATK or HP; the manual lists the
formula and current rounded power. Mana and Dao belong to each unit; Qi is shared.
Automatic skills spend mana only when they successfully find an eligible effect.
AUTO OFF reserves mana while basic attacks/passives and regeneration continue.
An ultimate checks all resources and its cooldown before spending anything.

## Base hero costs

Ultimate columns below omit the common requirement of 100 Dao. Card cooldown,
attack interval and skill cooldown are separate clocks. The manual exposes all.

| Cultivator | Deploy Qi | Initial / max MP | MP/s | Skill MP / CD | Ultimate MP / Qi / CD |
| --- | ---: | --- | ---: | --- | --- |
| Little Daoist Yun | 50 | 60 / 110 | 2.8 | 0 / 0s | 85 / 25 / 60s |
| Shen Zhu | 75 | 60 / 100 | 3.0 | 16 / 8.0s | 65 / 20 / 35s |
| Hong Lian | 125 | 80 / 130 | 3.2 | 24 / 10.0s | 95 / 35 / 50s |
| Bing Ruo | 100 | 70 / 120 | 3.2 | 18 / 9.0s | 80 / 25 / 45s |
| Jin Shan | 100 | 60 / 90 | 2.8 | 14 / 7.5s | 70 / 20 / 45s |
| Lei Xun | 175 | 80 / 140 | 3.5 | 24 / 8.0s | 100 / 40 / 55s |
| Mu Qing | 125 | 85 / 130 | 3.8 | 16 / 10.0s | 90 / 25 / 50s |
| Zhen Luo | 150 | 90 / 150 | 3.4 | 22 / 9.0s | 110 / 35 / 60s |

Yun's Frugal Practice is passive, with no additional cost. His orb costs 8 MP.
Mu Qing's Herb Garden costs 6 MP per successful healing pulse. Formation's basic
aura is continuous; it has no per-pulse mana fee. Skills and ultimates are distinct
from their basic/passive activities.

## Exact geometry

Circles use Euclidean distance between tile centers and clip at board boundaries:
radius 1.5 = 9 centers (3×3), radius 2 = 13, radius 2.5 = 21, radius 3 = 29.
Mu Qing's basic excludes her own center, leaving 28 possible other cells. Lines
follow the caster's lane; hero attacks face right, enemy melee faces left.
The hover **Range** button cycles basic/skill/ultimate. Secondary splash and chain
radii are written explicitly in the field manual. Boss warnings mark the actual
multi-lane impact; the manual states lane selection and windup.

## Talent paths

Each hero chooses one exclusive A/B path, five nodes each. Costs are 20, 30, 45,
60, 90 stones. Nodes 1/2/4 give minor stats; nodes 3/5 are unique special talents.
A gives HP, ATK/healing power, then HP/mana regeneration. B gives max mana, mana
regeneration, then automatic-skill cooldown reduction. Four specials are available
per hero across both paths. These are alternatives, not four simultaneous buffs.

| Hero | A special milestones | B special milestones |
| --- | --- | --- |
| Little Daoist Yun | Steady Breath → Shared Breath | Jade Vessel → Celestial Treasury |
| Shen Zhu | Piercing Bamboo → Verdant Torrent | Quick Draw → Wind Through Bamboo |
| Hong Lian | Ashen Lotus → Undying Cinder | Many-Petal Bloom → Lotus Sanctuary |
| Bing Ruo | Deep Winter → Winter Without End | Frost Mirror → Twin Mirrors |
| Jin Shan | Iron Sutra → Golden Core Body | Resonant Staff → Earth Dragon Echo |
| Lei Xun | Forked Sky → Endless Sky | Armor-Cracking Thunder → Tribulation Siphon |
| Mu Qing | Long-Life Medicine → Spring Everlasting | Purifying Leaves → Jade Rain |
| Zhen Luo | Swift Array → Living Array | Deep Circuit → Dao Confluence |

Talents apply to newly started battles. Legacy A/B saves keep their old branch
stats and count as rank 3; a subsequent purchase adopts the full new path stats.
First clears grant authored stone rewards; repeat clears grant
`max(10, floor(first-clear stones × 0.25))`. Each browser battle applies its
result once. Local saves are editable single-player data, not a competitive ledger.

## Escalation

Enemy HP grows multiplicatively by 5% after each campaign stage:
`round(base HP × 1.05 ** stage_index × rank multiplier)`.
Elite rank: 1.25× HP, +2 armor, 1.10× ATK. Captain: 1.50× HP, +3 armor,
1.15× ATK and +10% movement speed to other enemies within radius 1.5. Captains
appear in the last wave of non-boss encounters. Elite lantern shields increase
from 25 to 35. Rank labels are visible above invaders.

The first third of waves is setup, with ordinary enemies; the middle third adds
one elite per pack; the final third increases elite share to about half each pack.
Bosses retain mandatory 70%/35% HP phase gates and brief phase protection;
rounding uses the same integer thresholds for damage clamping and transitions.

| Encounter | Waves | Authored spawns* | HP multiplier |
| --- | ---: | ---: | ---: |
| wharf-1 | 12 | 31 | 1.0000 |
| wharf-2 | 16 | 42 | 1.0500 |
| wharf-3 | 17 | 45 | 1.1025 |
| terrace-1 | 18 | 49 | 1.1576 |
| terrace-2 | 18 | 47 | 1.2155 |
| terrace-3 | 19 | 49 | 1.2763 |
| tomb-1 | 20 | 59 | 1.3401 |
| tomb-2 | 20 | 55 | 1.4071 |
| tomb-3 | 21 | 56 | 1.4775 |

*Boss summons and altar resurrection can add enemies beyond the authored count.
Completion requires clearing enemies; a wave timer alone never awards victory.

## Region counterplay

| Region | Terrain | Paid ritual (35 Qi / 30s) | One-use emergency device |
| --- | --- | --- | --- |
| Glass Lantern Wharf | 48s tide cycle; marked columns 3–4 lose 15% attack speed while rising/high; high tide blocks placement and deals 15 Water damage/6s. Tide Miao gain 15% speed. | Calm the River: suppress flooding for 12s. | Jade River Ark: purge ordinary invaders, 35% boss HP subject to phase gates, slow boss 40% for 4s. |
| Azure Spirit Terraces | Healthy nodes buff heroes on/orthogonally beside them: +12% attack speed, +20% mana regeneration. A Drainer within radius 1 corrupts a node after 2s; corrupted nodes heal enemies within radius 2 for 3% HP/8s. Without a Drainer, an adjacent hero purifies after 3s. Wind changes projectile travel every 20s. | Purify the Ley: purify all nodes, lock wind 10s, restore 15 MP to heroes on/beside nodes. | Heaven Sword Array: purge ordinary invaders, 40% phase-safe boss HP, grant 80 shield/5s to allies passed. |
| Ten-Thousand-Bone Mausoleum | Mist is last 6s/24s: marked lanes lose 30% mana regeneration and ordinary target reach is 2.8 tiles. Fire/lightning or reveal pierce ghost fades. Three curse stacks slow attacks 20% for 8s. Final-stage altars resurrect souls after 6s and enable boss shields. | Soul Mirror: reveal, prevent resurrection 6s and cleanse allied curses. | Soul-Sealing Bell: purge without resurrection; reveal during sweep and 6s afterward. |

Each lane's device activates automatically once, moves with simulation time and
never recharges during that battle. Boss hits respect mandatory phases. Relics
remain separately unlocked, once-per-battle items.

## Reproduction

`python -m unittest discover -s tests -v` checks rules, API, content and assets.
`python tools/simulate_campaign.py --output report.json` plays the campaign using
legal costs/cooldowns and buys talent nodes only from preceding victory rewards.
This is one reproducible policy, not statistical balance validation or a claim
that all formations work equally well.
