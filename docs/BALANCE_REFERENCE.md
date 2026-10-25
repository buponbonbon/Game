# VAN DAO 1.5 balance reference

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

## Escalation and final assaults

Base enemy HP still increases 5% multiplicatively per campaign stage. Elite rank
has 1.25× HP, +2 armor and 1.10× ATK; captain has 1.50× HP, +3 armor, 1.15× ATK
and a radius-1.5 movement aura. Swarm rank uses 0.80× HP and 0.85× ATK with normal
armor. Swarm modifiers are alternatives to elite/captain stats, never stacked.
This lets the finale add bodies while retaining stronger priority targets.

Every final wave attacks five lanes. First spawns across the lanes occur within
0.6s; the full authored pack arrives within about four seconds. Each lane receives
7–10 enemies, plus a boss on boss stages. The HUD gives a 15s all-lane warning.
Boss summons/altar resurrection can add further enemies beyond the authored count.

| Encounter | Waves | Authored spawns | Final assault spawns |
| --- | ---: | ---: | ---: |
| wharf-1 | 12 | 62 | 35 |
| wharf-2 | 16 | 77 | 40 |
| wharf-3 | 17 | 95 | 51 |
| terrace-1 | 18 | 81 | 35 |
| terrace-2 | 18 | 84 | 40 |
| terrace-3 | 19 | 99 | 51 |
| tomb-1 | 20 | 91 | 35 |
| tomb-2 | 20 | 92 | 40 |
| tomb-3 | 21 | 106 | 51 |

Boss HP phases, armor plates and telegraph rules remain in effect. A surviving
boss or enemy must be defeated; a wave timer alone does not award victory.

## Automatic ultimates

The global switch defaults off and is beside Speed; keyboard A toggles it.
The preference persists in the browser. Auto uses the same validated command and
exact costs/cooldowns as manual casting. Offensive arts use their ultimate
geometry. Packs, durable targets, bosses or immediate danger justify expensive
arts; a weak isolated enemy can wait. Heals require injury/curse; formation buffs
require nearby allies and a threat; Yun waits for sufficient Qi headroom.
Casts are spaced by 0.22s and share the real Qi pool. Pause freezes casting;
changing the preference while paused does not spend resources.

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

## Sect economy (1.4)

`game/estate_content.py` defines crops, prices, formulas, commissions and goals;
`game/estate.py` normalizes v1/v2 saves and applies transactions to detached copies.
The API settles outcomes from the actual terminal battle, not a client-supplied
result. A 512-ID save ledger and per-live-battle receipts protect normal retries.
This remains a portable, editable local save, not an online anti-cheat economy.

| Crop | Battles | Base yield | Seed price | Sell per ingredient |
| --- | ---: | ---: | ---: | ---: |
| Qi Grass | 1 | 2 | 2 | 1 |
| River Lotus | 2 | 3 | 4 | 1 |
| Azure Bamboo | 2 | 2 | 5 | 2 |
| Soul Lingzhi | 3 | 2 | 7 | 3 |

Water adds 1 yield (2 at irrigation II). Fertilizer costs 2 stones and adds 1.
Research I costs 1 Insight and adds 1 yield; research II costs 2 Insight, cuts
one growth battle (minimum one) and returns a seed when harvested. Plots expand
3→6 for 60 stones and 6→9 for 120. Irrigation costs 40 then 90; I waters on a
growth event, II waters immediately and improves the water bonus. No real timer,
withering or seed-to-currency shortcut exists.

Tea costs 3 Qi Grass + 2 stones: +10 starting MP (clamped) and +20 Dao for the first three
successful summons. Dew costs 2 Lotus + 2 Bamboo + 3 stones (1 Insight formula):
8s first-tide calm, or purify one corrupted node and +15 MP on its orthogonal
radius-one cross, or 6s immunity to the first grave-mist mana penalty. Soul Ward
costs 2 Lingzhi + 1 Qi Grass + 4 stones (2 Insight formula): at the first active
three-stack curse, cleanse all allied curses and reveal spirits for 5s. Equip
only one; one dose is spent on successful entry even if abandoned or never triggered.

First/replay campaign stone rewards retain prior values. Each campaign victory
adds one regional seed; every third recorded victory when in campaign adds one
fertilizer. Three commissions rotate only after all are claimed. Normal bestiary
thresholds are 3/10/25 kills for 5/10/15 stones (+1 Insight at the last); bosses
1/3/5 kills for 10/15/25 stones (+1 Insight at the last two). Claims are one-time.
Eight achievement definitions and their rewards are visible in the estate.

Nursery Defense is outside STAGES: six waves, 45 enemies, lanes 1/2/3 only,
15 final-wave spawns (including one elite per lane). Each bed has two health;
a ruined bed cannot damage other beds. Each active lane retains a one-use rescue.
One surviving bed grants one Qi seed; two grant two Qi seeds + one Lotus + one
fertilizer; three grant three Qi seeds + Lotus + Bamboo + Lingzhi + fertilizer.
No campaign stones/Insight or campaign clear is awarded by this mode itself;
commissions/achievements/research may still grant their listed rewards.

A talent reset refunds the recorded amount paid: the first is free, later fees
are 10 stones deducted from the refund. Legacy rank-3-equivalent strings count
as the original 35-stone purchase, including when subsequently advanced.

## Elite squads and optional objectives (1.5)

Only elite/captain units gain squad roles; normal enemies and bosses receive no
squad protection/healing. Elite Hounds/Drowned are Guards, with 12% less HP than
the standard elite profile: radius 1.25, 15% final non-True damage prevention,
capped at 3 per hit, nonstacking, excludes other Guards/bosses/altars. Freezing
or defeating the Guard breaks its link. Elite Lanterns/Rottenwood are Menders
(10% less HP): 1s interruptible channel, 8s cooldown, radius 1.5, at most two
other wounded elites, 4% max HP each capped at 16. Any damage or freeze cancels.
Other elites are Strikers and gain no extra multiplier beyond their old rank.
Visual recoil does not stun movement or cancel an ordinary attack.

Trials are separate from STAGES. Caravan and Beacons use six waves; the Bone
Court uses eight waves with its boss at 194s. Caravan: 420 HP, moves toward x=8.5
at 0.065 tiles/s while a damage/tank/control hero is within radius 1.5, or freely
after the final enemies are cleared. Beacons: two 240-HP objects at lanes 1/3,
x=2.5. In either mode, non-frozen raiders within radius 0.9 deal 12 HP/s each,
capped at 24 per object; a nearby fighter halves it. Losing a protected object
fails that trial. Pause freezes objectives as well as combat.

Bone Court: 10 honor seals, one lost per cultivator death. Zero seals does not
fail the encounter. An explicit court ward reduces incoming hero damage by 25%.
Bronze requires a win; Silver also needs an intact gate and at most three losses;
Gold needs intact gate/no losses. Caravan/Beacons Silver additionally require
70% minimum objective health and at most one loss; Gold needs 90% and no losses.
Best medals never downgrade, while the result shows the medal for the actual run.
First wins pay 20 stones/1 Insight; repeats pay 6 stones and a regional seed.
Trials never add campaign clears or unlock mandatory campaign progression.

Fertilizer now costs 2 rather than 5 stones: the old surcharge exceeded the
sale value of its +1 ingredient for every crop. Fertilizer remains a yield choice,
not a required growth timer. Tea adds 20 Dao to its existing 10 initial MP for
three successful summons (60 Dao maximum), because early mana alone often caps
before it creates a useful ultimate opening. Ultimate mana/Qi/Dao/cooldowns and
the shared Qi cap remain unchanged. A bounded 32-entry local journal records
actual spending and rewards; no external telemetry is sent.
