# VAN DAO balance reference

This is a compact campaign adaptation of the supplied VAN DAO design brief.
It contains nine authored encounters, eight heroes and twelve enemy archetypes.
The large-production brief is a reference, not a claim that every proposed
system, asset or exact balance target is implemented. Content values live in
`game/content.py`; the Python simulation remains the authority for combat.

## Shared battle rules

- Five lanes, nine columns. Heroes deploy in columns 1–6; enemies approach from
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

| Stage | Encounter budget | Main question | Suggested counterplay |
| --- | ---: | --- | --- |
| Lanterns Going Dark | 76 s | Build an economy while learning three lanes | Start Yun at middle column 1 and Shen Zhu at middle column 3. Add a sword in lane 2 around 12 s and lane 4 around 24 s. |
| The Drowned Ferry | 96 s | Support shields and pressure on the outer lanes | Add lanes gradually; concentrated Fire bursts help remove lantern-backed groups. |
| River King's Claim | 112 s | Hold a boss lane through the tide | Protect sustained damage with Jin Shan; watch marked lane attacks and charge Ultimates. |
| Broken Ley Garden | 112 s | Break armor without losing tempo | Build beside ley nodes; sustained Fire and mixed damage are better than isolated weak hits. |
| Wings Above the Terrace | 120 s | Defend backline economy from flight and siphons | Use control and prioritize the draining channel; do not leave support units exposed. |
| Heart of the Mountain | 128 s | Break plates and survive marked impacts | Maintain damage through the armor phase and avoid over-investing in one vulnerable cluster. |
| The Unmarked Gate | 108 s | Catch spectral enemies through mist | Area damage and Lightning retain value where ordinary blades lose targets. |
| The Coffin Corridor | 126 s | Counter projectile absorption | Use the Monk's staff, Fire, and control rather than relying solely on light swords. |
| The Bone-Crown Emperor | 140 s | End the court's resurrection loop | Remove seal support, preserve shields for decrees, and keep damage ready through phase transitions. |

Lane numbers in this table are one-based, top to bottom. Simulation data uses
zero-based lanes. The first encounter intentionally uses only the middle three
lanes. Its first enemies arrive at 8, 21 and 34 seconds, leaving enough time to
finance additional swords through passive recovery and Yun's orbs.

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
