# Build status — version 1.5

Run `python run.py` or Windows `play.bat`. Python 3.10+ and a modern browser are
still the only runtime requirements; art, font and audio are bundled offline.

## Changes

- 336 authored animation frames across eight cultivators and thirteen enemy/altar
  identities. Separate windup/strike/recovery, skill/ultimate, recoil and death
  artwork; enemy walk cycles. Playback follows simulation time and attack windup.
  Idle is one frame; these are compact image-generated animation sheets, not a
  full hand-animated production. Native source PNGs are preserved unchanged.
- Clear/Cinematic effects, Smart/All HP/mana bars and Compact/Full/Off damage text.
  Battlefield dimming, reduced rescue-device size, bounded damage labels and
  precise circle/segment/lane threat countdowns improve crowded-field reading.
  Sheets load lazily and decode to bounded-size bitmaps; VFX composite separately.
- Elite Guard/Mender/Striker cooperation with exact visible ranges, capped
  protection/healing, interruptible channels and lower support-role HP budgets.
  Ordinary enemies and bosses receive no squad buffs. Pause includes objective,
  death and animation clocks; cosmetic recoil adds no movement stun.
- Three optional trials on existing maps: escort a jade caravan, defend twin
  beacons, challenge the Bone Court and preserve honor for medals. Zero honor
  still permits a Bronze victory. No campaign progression requires medals.
  New objective props, illustrated briefings, persistent best medals and rewards.
- Fertilizer costs 2 stones; Tea adds 20 Dao to its existing 10 MP for three
  summons, without waiving ultimate costs. Estate Ledger records 32 recent
  transactions/outcomes; ready crops appear in the lobby. V1/V2 saves migrate
  without regranting supplies or losing the existing wallet/talents/settings.

## Verification

- **136 standard-library tests passed**, including source-frame integrity,
  regeneration/preservation, squad caps/interrupts, objective fairness, pause,
  recoil, medals, transactions and previous combat/server/save regressions.
  `python3 -S -m unittest discover -s tests -v`.
- The earned-budget campaign policy cleared **9/9** with no preparations and no
  invalid commands. Eight encounters kept three seals, the final kept two.
  Evidence: `validation/CAMPAIGN_1_5.json`.
- A separate integrated estate/campaign policy also cleared **9/9**, harvested
  17 plots, crafted all three formulas, expanded to six plots and retained 566
  stones/20 Insight. It used Tea during the Wharf and banked Dew/Ward for later;
  those two effects are covered separately by engine and browser checks.
  No injected currency/free talents. Evidence: `validation/PROGRESSION_1_5.json`.
  Reproduce: `python3 -S tools/playtest_progression.py --output report.json`.
- All three trials cleared using normal commands and region-appropriate earned
  talents. The Oath policy includes healing, formation support, retiring fragile
  Yun and a timed relic; Bronze remains available after honor is exhausted.
  Evidence: `validation/TRIALS_1_5.json`.
- Chromium rendered all four attack/skill frames for all 21 identities, all hero
  ultimate sequences, enemy walks and two-frame deaths. It verified pause,
  shaped/countdown warnings, clarity options, local journal, Gold reward and
  persistent medals. Desktop/landscape touch had no JS errors or external calls.
  Terminal and pose snapshots are controlled UI fixtures, not balance wins.
  Evidence: `validation/COMBAT_BROWSER_1_5.json`.
- Estate UI regression covered actual canvas planting/watering/fertilizer,
  upgrades/trades, harvest/crafting/equipping, preparation consumption, cosmetics,
  commissions/achievements/research, legacy respec and dropped-receipt recovery.
  Evidence: `validation/ESTATE_BROWSER_1_5.json`.
- A fresh ZIP was extracted into a directory containing spaces and launched
  from another working directory with `python -S`. Catalog/estate, real canvas
  planting, paused entry, deployment for 125 Qi, Auto and pause passed.
  Evidence: `validation/RELEASE_SMOKE_1_5.json`.

These are reproducible scripted policies and fixtures, not a player study or an
exhaustive balance analysis. Other builds can perform differently. Human feedback
is still needed for long-term economy pacing, animation style and clarity.

Saves remain local/editable, not cloud synced. Collect a finished outcome before
restarting Python; active battles/receipts do not survive server restarts. Keep
same browser/port or export/import Chronicles. Native Windows/macOS and other
browser engines were not executed here. Audio is unchanged: synthetic English
voices and Chinese-inspired synthesized music. Optional trials reuse region art
and encounter music families; there are still eight heroes/nine campaign stages.
