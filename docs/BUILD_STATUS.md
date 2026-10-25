# Build status — version 1.3

Download/extract the repository and run `python run.py`. Python 3.10+ and a modern
browser are the only runtime requirements. No pip/npm installation, account,
remote API or online asset download is required. Windows also has `play.bat`.

## Changes for this release

- All nine encounters now have different melodies and three tension arrangements;
  28 local instrumental scores including the lobby. Actual crowd/elite/boss pressure
  can intensify music independently of the authored wave phase.
- Final assaults reach all five lanes with 35–51 authored spawns. Lighter swarm
  troops mix with elites/captains/bosses. A 15s HUD warning prepares the player.
- Global smart Auto Ultimate beside Speed (key A): normal resource/cooldown rules,
  actual ultimate ranges, useful target selection, healing and formation/economy
  conditions. The setting persists and can change while paused.
- Sixteen newly directed English synthetic performances with phrase-level pacing,
  pauses and changing energy; a bounded voice queue and a revised music/voice mix.
- Learned talents have green/gold styling and a tick; unlearned nodes are grey,
  with a jade border on the next available node. Locked nodes remain readable.
- Individual skill/ultimate choreography for all eight cultivators. Casting poses
  survive incoming hits; monotonic tick/command revisions prevent late HTTP
  responses erasing new effects, settings or simulation progress.
- Three illustrated briefing pages on each entry, including actual marked cells,
  mechanic diagrams and rescue artifacts. The server starts the battle paused at
  tick zero. Enter Battle resumes; ? and the pause menu reopen the briefing.
- Three new high-resolution 16-bit RPG style scenes with distinct architecture:
  river timber residence, floating jade observatory and subterranean bronze tomb.
  Detailed dragon-boat, sword-armillary and bell-arch artifacts have separate
  cutouts, silhouettes and runtime motion.
- Existing eight-hero/nine-stage roster, exact skill manual, mana, capped Qi,
  talent branches, local VT323, browser saves and import/export remain supported.

## Verification

- **94 standard-library tests passed.** Coverage includes coordinated five-lane
  spawn timing/counts, Auto costs/range/usefulness/pause/shared-Qi limits, crowd
  music hysteresis, emotional take metadata, unique musical families, cast-pose
  preservation, snapshot revisions, paused creation, RGB/RGBA art validation and
  the earlier combat/content/server/talent rules.
- A legal seeded campaign policy cleared **9/9** using earned stone rewards,
  normal costs/cooldowns and the actual Auto command. No invalid commands. First
  eight encounters retained three seals; the last retained two. Peak concurrent
  enemy counts ranged from 24 to 57. Durations in simulation seconds:
  197.117, 231.000, 341.117, 283.583, 261.350, 363.600, 306.233, 308.350, 517.767.
  Evidence: `docs/validation/CAMPAIGN_1_3.json`; reproduce with
  `python tools/simulate_campaign.py --output report.json`.
  This is one reproducible policy, not statistical balance validation.
- Chromium rendered all eight actual Auto Ultimate events in isolated combat
  fixtures. It sampled different learned/locked talent pixels and checked paid
  purchase/branch rules. All **72 audio encodings** decoded successfully.
- Actual client starts loaded all nine encounter music families, all three briefing
  pages, tick-zero pause and landscape touch. Auto persisted across reloads.
  A crowded fixture escalated music during setup. A deliberately delayed old
  snapshot did not erase the new Auto setting or casting effects. These browser
  checks had no JavaScript errors or external requests.
- Fresh-release launcher smoke passed with `python -S`, an extracted path
  containing spaces and a different working directory. Real canvas input opened
  the briefing at tick zero, deployed units for exactly 125 Qi, enabled Auto,
  defeated an enemy and froze on pause without JavaScript errors or external requests.

## Practical limits

This is a compact adaptation of the supplied production reference. There is no
full cutscene campaign or New Game+ system. Voices remain synthetic; emotional
quality and musical taste require listening feedback. Music uses synthesized
Chinese-inspired timbres, not recorded acoustic performers. Scene/artifact
paintings are retained image-generated inputs; the Python art command reproduces
procedural actors and preserves those inputs rather than recreating paintings.

Browser storage retains campaign/settings. Restarting Python starts new battle
sessions. Keep the same browser/localhost port or export/import a save to transfer
progress. Linux Chromium and landscape touch were exercised here; native
Windows/macOS launchers and other browser engines were not run on those systems.
