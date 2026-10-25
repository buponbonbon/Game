# VAN DAO: IMMORTAL WAR

A local browser lane-defense game with a Python combat simulation and original
pixel-art assets. Download the repository, extract it, and start playing with one
command. No npm, pip installation, account, or Internet connection is required
to play.

[Hướng dẫn tiếng Việt](README_VI.md)

## Start the game

Install **Python 3.10 or newer** if it is not already on your computer. On Windows,
enable **Add Python to PATH** in the Python installer.

1. On GitHub, choose **Code → Download ZIP**, then extract the entire ZIP.
2. Open a terminal in the extracted folder and run:

   ```bash
   python run.py
   ```

   On macOS/Linux, use `python3 run.py` if the command is named `python3`.
   On Windows, you can also double-click **play.bat**.

3. Your browser opens automatically. Keep the terminal open while playing.
   Press **Ctrl+C** in the terminal to stop the game server.

Do not open `web/index.html` directly or start a generic static-file server: the
Python server also runs the combat simulation. If the browser does not open,
open the local address printed in the terminal.

For a different port or a server without automatic browser launch:

```bash
python run.py --port 9000 --no-browser
```

## How to play

- Choose a hero card, then choose an empty deployment tile. Keys **1–8** select
  cards; **Escape** cancels a selection.
- Enemies advance from the right. Protect the gate's three seals.
- The field has 12 columns: deploy in columns 1–9. Column 0 holds a guardian
  artifact that automatically sweeps its lane once; it deals a phase-safe heavy
  hit to bosses. Spent artifacts never recharge within that battle.
- Start with **Little Daoist Yun** and **Shen Zhu** in the middle lane. Yun
  generates Qi; Shen Zhu fires swords. Prepare the lanes above and below when
  the wave warnings appear.
- Qi pays for deployment, region rituals and part of each ultimate. A card must finish its cooldown before it can be used
  again. Clicking a deployed hero opens its inspection controls.
- **Space** pauses/resumes. Use the speed and sound controls in the game UI.
- Mouse and touch are supported. A landscape browser window gives the best view.

Campaign progress and settings are saved in this browser. Use the in-game save
export before clearing browser data or changing computers. Keep using the same
local server port to keep the same browser save origin.

## What is included

The campaign adapts the supplied design into nine extended encounters across
Glass Lantern Wharf, Azure Spirit Terraces, and the Ten-Thousand-Bone Mausoleum.
The roster contains eight distinct heroes, unlockable upgrade branches, three
bosses, map hazards, relics, and authored enemy waves. This is a playable compact
adaptation, rather than a claim that every detail of the production document is
implemented. See [build status](docs/BUILD_STATUS.md) for verified coverage and
limitations and [balance reference](docs/BALANCE_REFERENCE.md) for content data.

## Version 1.7: close camera and a new sanctuary interface

The courtyard opens at **1.85× zoom** and scrolls with your character. Use the
+ / − controls to choose 1.45–2.4×. The profile, currency icons, illustrated
minimap and facility dock stay fixed on screen. Nearby NPC labels replace the
old “Click to approach” hover text.

- **M / MAP:** open a dedicated illustrated parchment map; select a landmark,
  then Travel Here to walk there, or Open Facility for immediate access.
- The screen-space HTML/CSS interface has icon buttons, clear focus/disabled
  states, currency tooltips, NPC conversation panels and a commission journal.
- Each of three avatars has **eight walking frames per direction**, separate
  directional idle poses and registered feet. Walking follows distance traveled;
  routes no longer pause at every grid waypoint or restart the gait there.
- WASD/arrows, Shift, E/Enter, saves, quests and existing facilities still work.
  Position-only saves avoid refreshing combat previews. Art stays bundled offline.

See [UI references and movement diagnosis](docs/UI_REFERENCE_1_7.md) for the
accessible research sources and the official Gunny sites blocked by the network.

## Version 1.6: Celestial Sanctuary

The main screen is now an interactive HD-2D sect courtyard: a native
1672×941 painted environment, detailed character cutouts, four-direction walking,
water reflections, drifting petals and warm light. The hub uses smooth rendering
and system fonts; combat keeps its existing pixel presentation. “32/64-bit” is
not used as a visual quality claim.

- Walk with WASD/arrows, hold Shift to run, click the ground or an NPC, and press
  E/Enter to speak. MAP or Tab/M lists eight destinations with automatic routes.
  Collision keeps the player away from buildings, planted beds, cliffs and water.
- NPCs link to Campaign, Talents, Bestiary, Alchemy, Garden, Merchant, Commissions
  and Trials. The bottom bar also opens these systems immediately.
- Commissions show objectives/progress/rewards and can be pinned. Progress still
  counts automatically; following a commission adds no new grind or reward source.
- Avatar selects Shen Zhu or Yun; Mu Qing becomes available after Wharf III.
  Appearance is cosmetic. Position, appearance and followed commission persist in
  the existing save slots/export. Ambient motion can be disabled in Avatar, and
  defaults to the browser's reduced-motion preference for new saves.
- Owned lantern canopy, jade chimes and ward banner appear in the courtyard.
  Existing saves migrate without losing currency, inventory or learned talents.

Runtime is still Python's standard library and a browser. All hub images are
bundled; no new account or runtime dependency is needed.

## Version 1.5: animated combat and regional trials

- **336 authored animation frames:** all eight cultivators and thirteen enemy/altar
  identities have separate attack, cast, recoil and death artwork; enemies also
  have four-frame walk cycles. Hero ultimates use four frames. Frames follow the
  simulation clock, pause with combat and use the real attack windup. Idle uses
  a single pose. New sheets load on demand and decode to bounded-size bitmaps.
- **Clearer combat:** dimmed battlefield, smaller rescue devices, smart HP/mana
  bars, compact damage text and reduced particle opacity. Choose Clear/Cinematic,
  Smart/All bars and Compact/Full/Off damage text under Settings → Battle Visuals.
  Danger circles/segments/lanes now show the actual affected area and countdown.
- **Elite squads:** Guards protect nearby elites; Menders channel limited healing
  that damage/freeze can interrupt. Support roles trade some HP for their utility.
  Read exact rules from Squad Tactics in the pause menu or Regional Trials.
- **Three optional trials on existing maps:** escort the Lantern Caravan, protect
  Twin Jade Beacons, or challenge the Bone Court with honor seals. Medals never
  gate campaign progression; best medals persist. First wins grant 20 stones and
  1 Insight, repeats 6 stones and a regional seed. The Oath's ward reduces incoming
  hero damage by 25%; losing all honor seals still permits a Bronze victory.
- **Economy:** fertilizer costs 2 stones. Spirit Tea gives the first three summons
  +10 MP and +20 Dao without waiving ultimate costs. The estate's Ledger shows
  recent harvests, spending and battle rewards. The lobby calls out ready crops.

Version-1/2 saves remain compatible. No new hero or campaign map is required.
The authored animation PNGs and new objective props are bundled offline.

## Version 1.4: the Sect Estate

Open **Sect Estate / Linh Dien** from the lobby. Spirit Stones remain the main
persistent currency; Insight unlocks herbal research/formulas. Battle Qi remains
separate and cannot be converted to permanent currency.

- **Garden:** three starting plots, expandable to six/nine; four illustrated crops
  grow after 1–3 completed battles. Water/fertilizer improve yield. Two research
  levels per crop improve yield, then shorten growth and return a seed. Nothing
  withers while away. Victory grows crops once; a defeat qualifies after half the
  waves **and** 60 seconds. Quitting does not grow crops.
- **Alchemy:** Spirit Tea, Five-Element Dew and Soul-Ward Elixir. Brew harvested
  ingredients for a small stone fee, then equip **one preparation per battle**.
  One dose is spent on successful battle entry; its effect activates automatically.
  Formula panels state costs, triggers, duration and exact affected cells.
- **Merchant:** buy seeds/fertilizer, sell spare produce, purchase and toggle three
  cosmetic decorations for the lobby, garden and stronghold.
- **Missions / Goals / Research:** three rotating commissions (no daily timer),
  eight achievements and three bestiary milestones per enemy. Claim rewards here;
  the Monster Archive links directly to research. All inventory is in the save.
- **Nursery Defense:** a separate six-wave, three-lane seed run. Each bed has two
  health; damage stays in its own lane. More surviving beds give more seed types.
  Three illustrated briefing pages explain the mode. Garden Shelter grants every
  living cultivator a 35-point shield for 6s (35 Qi, 30s cooldown).
- **Talent reset:** reset a cultivator in the Cultivation Hall and recover the
  stones actually paid. First reset is free; later resets deduct a 10-stone fee.
  Legacy branch purchases keep their original 35-stone basis.
- **New actor art:** redesigned detailed RPG-style cutouts for all eight
  cultivators and twelve enemies plus the altar. Four hero poses and three enemy
  poses combine with runtime breathing/lunging/casting and existing skill effects.
  New garden scenery and sixteen botany stages are bundled offline.

Version-1 saves migrate automatically to version 2 without losing progression,
wallet, settings or talents. Starter seeds/fertilizer are granted once. Completed
battle receipts prevent duplicate rewards; a lost HTTP response can be retried.
Keep the same browser/localhost port or use Chronicles export/import.

## Version 1.3 improvements

- Nine individual encounter themes, each with setup/pressure/onslaught music:
  **28 bundled arrangements** including the lobby. Actual crowd size and elite/boss
  pressure can intensify music before the next wave phase; a six-second release
  prevents constant switching. Chinese-inspired guqin/guzheng/pipa/dizi remain the style.
- Every final wave attacks **all five lanes**, with **35–51 authored enemies**.
  Swarm troops mix with elites, captains and bosses. Swarm HP/ATK is lighter than
  normal troops so mass attacks reward area damage without simply multiplying durability.
- **A:ON / A:OFF** beside Speed toggles smart automatic ultimates; **A** is its
  keyboard shortcut. It uses normal mana, Qi, Dao and cooldowns, checks ultimate
  range, saves costly attacks for a useful target and heals/buffs allies who benefit.
- Sixteen newly directed **English synthetic voice** takes use expressive phrases,
  pauses, changing pace and energy. Separate Voice volume and music ducking remain.
- Learned talents are green/gold with a tick. Unlearned nodes are grey; the next
  available node has a jade border. Locked nodes remain readable when selected.
- Individual casting effects distinguish all eight heroes: spirit wells, flying
  blades, fire lotuses, ice crystals, mountain shockwaves, thunder, healing leaves
  and formation circuits. Hits no longer erase a skill/ultimate pose, and stale
  HTTP responses cannot rewind the cast animation or Auto preference.
- Every encounter opens an illustrated three-page region briefing while the
  simulation is paused at tick zero. Read terrain, counters and the rescue device,
  then choose **Enter Battle**. Reopen it from **?** or the pause menu.
- New high-resolution **16-bit RPG style** scenes use distinct river-palace,
  floating-jade-observatory and underground-bronze-mausoleum designs. Three ornate
  artifact cutouts have different silhouettes and runtime motion.

The roster stays eight heroes and nine encounters. Version-1 saves remain
compatible. Qi remains capped at 320 with at most three Yuns. Mana, precise skill
ranges and two exclusive five-node talent paths remain in effect.
Stop the old Python process before launching the update on the same browser/port.

## Development

The runtime uses only Python's standard library and browser APIs. The generated
PNG assets are already included; asset generation is not a startup requirement.

```bash
python -m unittest discover -s tests -v
python tools/simulate_campaign.py --output dist/balance-report.json
python tools/generate_assets.py
python tools/package_release.py
```

The package command writes `dist/VAN_DAO_Immortal_War.zip`, excluding local virtual
environments, caches, and Git metadata. Python owns the fixed-step combat rules;
the canvas client owns rendering, input, audio, and browser save storage.
