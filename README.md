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

## Version 1.2 improvements

- Per-hero mana, automatic-skill costs, ultimate mana/Qi/Dao costs and cooldowns.
  Qi is capped at 320; three Yun maximum, with 100%/80%/60% orb yields. Toggle
  AUTO OFF in a hero's inspection controls to reserve mana for their ultimate.
- Hover a deployed hero or card for its range. **Range** cycles basic, skill and
  ultimate geometry. **Menu → Cultivator / Enemy Skills** pauses the battle and
  opens exact costs, scaling, target counts and affected cells.
- Two exclusive five-node talent paths per hero. Each path has two special
  milestones, giving four distinct special talents per hero. Victories on cleared
  stages award a smaller, repeatable Spirit Stone reward for further cultivation.
- Native 64-pixel hero action sheets: idle, attack, skill and ultimate poses.
  Richer region art and three different one-use emergency artifacts guard the gates.
- Sixteen bundled **English** summon/ultimate voice clips, subtitles, a Voice
  slider and music ducking. Dialogue uses synthetic character voices.
- Ten original Chinese-inspired instrumental loops: lobby, then setup/pressure/
  onslaught arrangements per region, with guqin/guzheng/pipa/dizi timbres.
- Three battle phases, more late elites, captains and 5% multiplicative enemy HP
  progression per stage. Each region has a paid ritual and distinct counterplay.
- Animated lobby, local VT323, expanded Monster Archive and in-battle field manual.

The roster remains eight heroes and nine stages. Existing version-1 saves remain
compatible. Old A/B upgrades retain their original branch effects and count as
rank 3; buying a later node adopts the full new path stats. Stop the old Python
server, extract the update and restart on the same browser/port to retain progress.

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
