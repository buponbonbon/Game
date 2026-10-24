# Build status — version 1.2

Download/extract the repository and run `python run.py`. Python 3.10+ and a modern
browser are the runtime requirements. No pip/npm installation, account, remote
API or runtime asset download is required. Windows also has `play.bat`.

The supplied production document is a design reference. The user chose a Python
localhost browser game; the authoritative 60 Hz combat/server uses Python's
standard library and the client uses canvas and browser audio APIs.

## Implemented in this update

- Eight heroes and nine encounters retained; 12–21 waves per encounter, five lanes,
  twelve columns, deployment in 1–9 and a reserved one-use guardian column.
- Per-unit mana and regeneration, automatic-skill costs/toggle, and atomic ultimate
  checks for mana, Qi, 100 Dao and a personal cooldown. Shared Qi cap 320, maximum
  three Yuns with diminishing orb yields and a finite economy ultimate.
- Shared effective-stat data for combat and previews. The field manual lists
  scaling, current power, costs, cooldowns, target counts and precise geometry.
  Hover overlays cycle basic/skill/ultimate ranges; pause-menu access covers all
  eight cultivators and twelve monster types.
- Two exclusive five-node talent paths per hero, two special milestones per path,
  real stat/effect changes and smaller repeat-clear rewards. Legacy A/B upgrades
  remain usable as rank-3 paths. Talents apply when a new battle starts.
- Three encounter phases, increasing elite presence, small captains and enemy HP
  scaling by 5% multiplicatively per campaign stage. Boss phase gates use matching
  integer thresholds, fixing a rounding softlock exposed by scaled HP.
- Region-specific tide penalties, corruptible/purifiable ley nodes, wind, grave
  mist, curses and resurrection altars. Each region has a 35-Qi/30s ritual and a
  different emergency artifact with its own effects. The region guide states
  timings, radii, buffs and counterplay.
- Native 64×64 hero action sheets with separate idle/attack/skill/ultimate frames;
  denser 1024×576 region backgrounds, distinct defended architecture and 48×48
  region-specific rescue devices. Water/wind/mist and the lobby animate.
- Sixteen bundled English synthetic voice clips, captions, a Voice volume slider,
  music ducking and battle-transition cancellation. Eight character SFX palettes.
- Ten original Chinese-inspired instrumental loops: lobby and three increasingly
  intense arrangements per region, with guqin/guzheng/pipa/dizi/percussion timbres.
- Existing local VT323, save slots, IndexedDB mirror, import/export, pause, speed,
  keyboard, mouse and touch controls remain supported.

## Verification

- All **79** standard-library tests passed: rules, geometry, mana transaction
  failures, Qi cap, diminishing economy, talent milestones, old saves, scaled
  boss phases, nodes/rituals, HTTP previews/validation and reproducible assets.
- The legal seeded campaign policy cleared **9/9** encounters using only earned
  stone rewards and legal costs/cooldowns; no failed commands. Durations were
  189.517, 224.650, 333.783, 287.500, 258.250, 368.233, 316.600, 413.983, 525.467
  simulation seconds. All nine stages retained three gate seals. Reproduce with `python tools/simulate_campaign.py --output report.json`.
  This is one playability policy, not a statistical balance study.
- Chromium exercised lobby, talents, the hero/enemy manual, range controls,
  mana inspection, pause, region guide and settings without JavaScript errors or
  external requests. All eight English summon voices played; a legally charged
  Yun ultimate played its English line. Actual wave progression changed wharf
  music through setup/pressure/onslaught. All 36 bundled audio files decoded.
- A fresh source ZIP launched with `python -S` from a path containing spaces
  and a different working directory. Canvas input placed Yun/Shen, spent exactly
  125 Qi, defeated an enemy and paused combat without external requests or errors.
- Landscape touch checks confirmed paid talent purchase, exclusive branches,
  effective preview matching deployed HP, reload persistence, the Voice slider
  and a frozen battle clock while browsing skills.
- See `docs/ART_AUDIO.md` for asset sizes, authoring dependencies and attribution;
  none of the optional audio-authoring tools is required to launch the game.

## Practical limits

This is a compact adaptation, not full parity with the production brief. It has
no narrative cutscene campaign, New Game+ system or tracked mastery achievement
system. Current talent trees implement two five-node paths, not an unlimited hero
rank system. Voice dialogue is synthetic; music uses synthesized timbres rather
than acoustic recordings. Enemies retain four-frame sprites; the expanded action
sheets in this update focus on cultivators.

Browser storage holds campaign progress/settings. Restarting Python does not
retain active battle sessions; export a save to transfer campaign progress.
Keep the same browser and localhost port to retain its save origin. Linux
Chromium was exercised here; native Windows/macOS launchers and other browser
engines were not executed in this environment.
