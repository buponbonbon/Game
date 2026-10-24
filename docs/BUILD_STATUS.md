# Build status

## Playable release

Download/extract the repository and run `python run.py`. Python 3.10+ is the only
runtime prerequisite. The standard-library server opens a local browser and runs
the combat simulation; the included canvas client renders the game. No package
installation, account, remote API, or runtime asset download is needed.

The user explicitly chose Python and local browser play. This architecture
replaces the earlier Pygbag/CDN onboarding experiment, avoiding an online
WebAssembly prerequisite. The uploaded production document was used as a design
reference, not as existing executable code.

## Implemented

- Deterministic 60 Hz Python combat: resource costs, deployment cooldowns,
  blocking/movement, attack windups, traveling projectiles, shared damage math,
  shields, healing, status effects, death, gate breaches and terminal rewards.
- Eight heroes with distinct economy/damage/control/tank/support behavior,
  autonomous skills, charged player Ultimates, and exclusive upgrade branches.
- Nine authored encounters across three regions, nine common enemy archetypes,
  three bosses with mandatory phases and visible danger warnings, and three
  one-use relics. Tide tiles, a timed ferry opening, ley-node bonuses, grave mist
  and destructible resurrection altars affect combat.
- Original native raster pixel art: four backgrounds, 21 animated actors and
  a UI icon atlas. Procedural Web Audio music/cues, volume controls and reduced
  shake setting are included.
- Mouse, keyboard and touch input; pause/speed controls; campaign and cultivation
  screens; three local save slots, IndexedDB mirror, export/import and reset
  confirmation. Campaign rewards are granted only on the first clear.
- One-command launcher, optional Windows batch launcher, safe local HTTP API,
  source-archive packager and reproducible asset generator.

## Validation evidence

- All 47 standard-library unit tests passed. The suite covers combat, campaign opening/loss/retry,
  content consistency, asset decoding/CRC/reproduction, and local HTTP behavior.
- The taught tutorial opening cleared in 64 simulation seconds with all three
  gate seals and seven enemy kills. A legal seeded policy cleared all nine
  stages using unlocks and upgrades paid from earlier rewards. The final stage
  required a mixed healing/formation/tank/damage team: 83.6 seconds, three altars
  destroyed and all gate seals intact. Reproduce this one-policy playability
  check with `python tools/simulate_campaign.py --output report.json`; it is not
  a statistical balance study or a guarantee that every team wins.
- Actual Chromium browser play cleared the tutorial through canvas controls,
  including resource deduction, invalid-placement feedback, pause, 1.5x speed,
  combat, victory and next-stage unlock. First-clear 45 stones survived reload
  and did not repeat on subsequent polls. Audio context started after input.
- Touch browser checks covered placement, pause, landscape/portrait layout,
  settings persistence, three-slot switching, and save export/import. Observed
  no JavaScript errors, failed requests, or requests outside the local server.
- A freshly extracted release ZIP launched with `python -S` (no site packages),
  from a path containing spaces and a different working directory. Browser
  controls deployed two heroes for exactly 125 Qi, defeated an enemy and paused
  the authoritative simulation. The archive's CRC passed and it excluded Git
  metadata, virtual environments and caches. No external requests or JavaScript
  errors occurred in that release check.

## Scope and limitations

This is a playable compact adaptation, not full production-document parity.
Encounters and boss HP are shortened for local play. Mastery text is tactical
guidance rather than a tracked achievement system. There is no full narrative
cutscene campaign, exhaustive hero-rank tree, New Game+ modifier system, or
long-form recorded soundtrack. Four sprite poses per actor do not constitute
every named animation in the original production brief.

Campaign/settings saves live in the browser. An active battle can reconnect while
the same Python server session exists; restarting the server starts fresh battle
sessions. Save export is needed to transfer progress between browsers/computers.
Chromium was tested here; Windows/macOS launch scripts and other browser engines
were not executed on their native platforms in this Linux environment.
