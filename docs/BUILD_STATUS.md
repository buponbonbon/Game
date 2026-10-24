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

## Version 1.1 improvements

The existing eight-hero, nine-stage campaign now has 12-21 waves per encounter.
A 12-column field offers nine deployment columns and a reserved guardian column.
Each lane has one automatic rescue sweep; bosses take a phase-safe heavy hit.
The three region strongholds stand visibly behind the formation. VT323 is bundled
with its license and replaces the missing-glyph bitmap renderer. A twelve-entry
monster archive shows combat attributes, named abilities and counterplay.
Eight hero sound palettes and four locally composed themes distinguish characters,
the lobby, wharf, terrace and tomb. Save schema version 1 remains compatible.

## Validation evidence

- All 54 standard-library unit tests pass, including longer encounter playability,
  the new deployment boundary, one-use guardian sweeps, flying/boss interactions,
  paused guardians, archive data and bundled-font licensing.
- The seeded legal campaign policy clears all nine extended stages with all gate
  seals intact. Recorded durations: 183.8, 219.0, 310.133, 263.383, 249.483, 342.867,
  297.917, 287.217 and 390.95 simulation seconds. The opening stage has 31 enemies.
  Reproduce with `python tools/simulate_campaign.py --output report.json`.
  This is one playability policy, not a statistical balance study.
- Actual Chromium input placed a hero in new column 9 and correctly rejected
  column 0 with an explanation. An undefended enemy naturally triggered the
  guardian; its sweep preserved the gate and became spent. Pause froze the clock.
- Browser checks loaded the real local VT323 face, browsed the archive including
  boss attributes, imported an earned version-1 save, dispatched eight distinct
  hero sound palettes and changed between all four music themes. No JavaScript
  errors or external network requests occurred. Audio checks establish event
  dispatch and a running graph, not the perceived mix on every speaker.
- The 1.1 fresh-extraction ZIP smoke check passed with `python -S`, a path with
  spaces and a different working directory: real browser placement, combat kill,
  pause, no external requests and no JavaScript errors. Updated touch checks
  passed for modal settings sliders, new field placement, exact Qi and pause.
  Earlier first-clear reward persistence and version-1 save compatibility are
  retained; the current browser check imported an earned version-1 campaign save.

## Scope and limitations

This is a playable compact adaptation, not full production-document parity.
Boss HP is tuned for local play; encounter wave schedules are extended. Mastery text is tactical
guidance rather than a tracked achievement system. There is no full narrative
cutscene campaign, exhaustive hero-rank tree, New Game+ modifier system, or
long-form recorded soundtrack. Four sprite poses per actor do not constitute
every named animation in the original production brief.

Campaign/settings saves live in the browser. An active battle can reconnect while
the same Python server session exists; restarting the server starts fresh battle
sessions. Save export is needed to transfer progress between browsers/computers.
Chromium was tested here; Windows/macOS launch scripts and other browser engines
were not executed on their native platforms in this Linux environment.
