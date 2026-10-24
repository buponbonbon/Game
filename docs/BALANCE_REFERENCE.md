# VAN DAO balance reference

This is a compact campaign adaptation of the supplied VAN DAO design brief.
It contains nine authored encounters, eight heroes and twelve enemy archetypes.
The large-production brief is a reference, not a claim that every proposed
system, asset or exact balance target is implemented. Content values live in
`game/content.py`; the Python simulation remains the authority for combat.

## Shared battle rules

- Five lanes, twelve columns. Heroes deploy in columns 1–9; enemies approach from
  the right. Three breaches break the gate.
- Begin with 150 Spirit Qi. Passive recovery gives 25 Qi every 12 active seconds.
  Yun adds 25 Qi every 8 seconds. The resource cap is 999.
- Ordinary positive damage subtracts armor, then applies the target's resistance,
  retaining the central combat function's minimum positive damage rule.
- Pause stops simulation time. Speed changes affect simulated time rather than
  creating a second source of damage or resources.
- Stage durations below are encounter budgets, not guaranteed completion times.
  A surviving final enemy must still be defeated; a timer alone is not a victory.
- Current boss HP is 1,800 / 2,400 / 3,000 rather than the brief's long-form
  8,400 / 10,500 / 12,800. This keeps local browser battles manageable.

## Hero roster

| Hero | Role | Cost | HP / armor | Basic attack | Card cooldown |
| --- | --- | ---: | --- | --- | ---: |
| Little Daoist Yun | Economy | 50 | 170 / 0 | 25 Qi every 8 s | 8 s |
| Shen Zhu | Sword damage | 75 | 260 / 2 | 36 every 1.35 s | 7 s |
| Hong Lian | Fire area damage | 125 | 230 / 0 | 52 every 2 s | 12 s |
| Jin Shan | Melee tank | 100 | 900 / 12 | 44 every 1.45 s | 11 s |
| Bing Ruo | Ice control | 100 | 245 / 1 | 22 every 1.55 s | 10 s |
| Mu Qing | Healing support | 125 | 280 / 1 | Heal 45 every 6 s | 12 s |
| Lei Xun | Chained lightning | 175 | 300 / 2 | 30 every 1.65 s | 14 s |
| Zhen Luo | Formation support | 150 | 320 / 3 | Nearby attack-speed aura | 13 s |

Yun, Shen Zhu, Hong Lian and Jin Shan are available at the start. Bing Ruo and
Mu Qing unlock after the River Lord; Lei Xun and Zhen Luo unlock after the
Mountain Lord. Each hero has two mutually exclusive branch definitions. A
branch costs 35 Spirit Stones. Branches trade an advantage for a drawback where
appropriate: for example, Shen Zhu can pierce two enemies at reduced damage or
attack faster with a smaller third-hit bonus.

Support heroes occupy real tiles and cost Qi. Buying economy at the expense of
all damage is dangerous; putting every fighter in one lane leaves the gate open.
Place melee protection ahead of ranged damage and economy behind the front.

## Authored encounters and tactical openings

| Stage | Waves | Scripted enemies | Encounter budget |
| --- | ---: | ---: | ---: |
| Lanterns Going Dark | 12 | 31 | 214 s |
| The Drowned Ferry | 16 | 42 | 245 s |
| River King's Claim | 17 | 45 | 354 s |
| Broken Ley Garden | 18 | 49 | 291 s |
| Wings Above the Terrace | 18 | 47 | 275 s |
| Heart of the Mountain | 19 | 49 | 392 s |
| The Unmarked Gate | 20 | 59 | 317 s |
| The Coffin Corridor | 20 | 55 | 307 s |
| The Bone-Crown Emperor | 21 | 56 | 425 s |

Lane numbers in this table are one-based, top to bottom. Simulation data uses
zero-based lanes. The first encounter intentionally uses only the middle three
lanes. Its first enemies arrive at 8, 21 and 34 seconds, leaving enough time to
finance additional swords through passive recovery and Yun's orbs.

Each lane has one guardian seal. An approaching enemy triggers its automatic
sweep: ordinary enemies are purged, including flying enemies; bosses take one
phase-safe heavy hit and are pushed away from the gate. It never recharges, and
pause stops its movement. Once spent, later breaches damage the gate normally.

## Regions and campaign rewards

- **Glass Lantern Wharf:** low, rising and high tide. The region rewards Jade
  Tide Pearl, Tide Jade and the frost/healer roster unlocks.
- **Azure Spirit Terraces:** ley nodes and changing wind. The region rewards the
  Eight-Trigram Wind Compass, Azure Ley Shard and lightning/formation unlocks.
- **Ten-Thousand-Bone Mausoleum:** mist, curses and seal support. The final
  region rewards Soul-Sealing Bronze Bell and concludes the nine-stage campaign.

Relics have finite once-per-battle effects. The compact Pearl grants shields;
the Compass grants Resonance/haste; the Bell reveals, interrupts and cleanses.
These are deliberate compact adaptations of the larger brief's relic rules.

## Validation scope

`tests/test_content.py` checks campaign reachability, region progression, legal
wave references, boss placement, unlock/reward consistency, tutorial resource
budget and detached public catalog data. Combat and browser tests are separate;
content validation alone does not establish that an encounter is beatable or
that the user interface behaves correctly.
