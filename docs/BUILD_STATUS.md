# Build status — version 1.8

Run `python run.py` or Windows `play.bat`. Python 3.10+ and a modern browser are
still the only runtime requirements; art, font and audio are bundled offline.

## 1.8 changes

- Illustrated three-region journey map replaces the campaign card list. Nine
  authored encounter stories provide witnesses, motives, 27 introduction pages,
  18 optional responses and nine aftermaths. Next Stage opens the next story.
- Six original visitor NPCs join the eight cultivators; free conversation topics,
  progress/choice-aware greetings, three optional keepsake favors and a persistent
  journal. Ten environmental discoveries use actual walking/inspection and local
  foliage/water/chime reactions. Story actions grant no wallet/combat rewards.
- Garden is a walkable 2D workyard: nine physical beds, crop stages, wet and wild
  soil, character/tool interaction poses, foliage/butterflies and NPCs. Selecting
  a bed opens a compact inspector; actions walk to an approach point before using
  the existing Python transaction. Seed/growth/yield/preparation rules unchanged.
- Three avatars now have eight facings: 192 walking frames, 24 standing poses and
  48 greeting/inspection/water/gather frames. Foot registration, acceleration,
  short stopping movement, breathing and footfall effects improve presentation.
  Original PNGs remain unchanged. Source variants are explicit in atlas metadata.
- Bounded story state migrates into existing V1/V2 saves; wallet, inventory,
  learned talents, settings and campaign progression are preserved. Keyboard and
  touch scrolling support the longer journal. Runtime is still stdlib/browser.

## 1.8 verification

- **150 stdlib tests passed**. Fifteen affected story/save/source/preservation
  checks also passed after final directional idle registration. New checks cover
  invalid/locked story actions, idempotent discoveries, real favor prerequisites,
  portable bounded state, no currency/completion from reading and authored assets.
- Chromium reached all six visitors and inspected real environment objects,
  selected a saved branch, planted/watered/fertilized a physical bed, expanded to
  six beds, upgraded irrigation and used the existing Ledger. Four water action
  frames were observed during an actual transaction.
- The live first-encounter record won through the existing legal taught deployment
  policy with zero invalid commands and three gate seals. Its normal settlement
  grew the crop and unlocked only Wharf II. Next Stage opened Tao's story; the
  completed first chapter showed its aftermath. The crop yielded the advertised
  four produce; gardener/courier favors and save reload passed.
- Explicit completed-campaign fixtures verified all nine aftermaths and revisit
  actions. 960x540 touch read/closed story, physically scrolled the long journal
  and planted a bed. No JS errors/external requests. These later story fixtures
  are UI checks, not extra campaign balance wins.
  Evidence: `validation/EXPLORATION_BROWSER_1_8.json`.
- Chromium rendered all **192** walking, **24** directional standing and **48**
  interaction poses. The measured steady hub draw work in this run averaged about
  5.2ms; this is not a hardware-independent FPS guarantee.
  Evidence: `validation/EXPLORATION_ART_1_8.json`.
- Keyboard PageDown scrolled the journal, Enter advanced narrative and Tab stayed
  in the dialogue. Long touch scrolling was exercised separately above.
  Evidence: `validation/EXPLORATION_FOCUS_1_8.json`.
- Fresh ZIP extracted to a directory with spaces and launched using `python -S`
  from another cwd: actual bed selection/planting, story-led entry, tick-zero
  briefing, 125-Qi deployment, Auto and pause passed without external requests.
  Evidence: `validation/RELEASE_SMOKE_1_8.json`.
- The mature nine-bed garden overview is an explicit art fixture, not an extra
  progression run. Actual planting, battle growth and four-yield harvest are
  covered by the live-record browser check above. Combat rules were unchanged;
  full nine-stage balance policies were not rerun for this presentation update.

Previous release evidence below is historical. Saves remain local/editable;
active battles do not survive Python restarts. Native Windows/macOS and other
browser engines were not executed here. Dialogue is text; existing synthetic
English voices and Chinese-inspired music remain bundled.

## 1.7 changes

- Screen-space HTML/CSS sanctuary HUD: avatar/profile, illustrated currency icons,
  facility dock, persistent quest card, contextual NPC labels and modern dialogue
  panels. Removes the old hover instruction; focus/disabled controls stay usable.
- Default 1.85x close camera, time-based following and 1.45–2.4x zoom controls.
  Source-cropped scene rendering and inverse camera mapping for ground input.
  Dedicated parchment map with landmark selection, travel/direct-open actions,
  player location and an overview minimap showing the camera's visible area.
- 96 new walking frames across three avatars/four directions plus twelve retained
  directional idle poses. Feet registered from source alpha; gait phase follows
  distance. Collision-safe route simplification and full distance consumption at
  waypoints remove one-frame stops. NPCs no longer slide in place while walking.
- Position saves are throttled while moving and skip combat preview refresh.
  Save compatibility, existing facilities and combat parameters stay unchanged.
- Research sources and proxy-blocked official Gunny pages are documented in
  `UI_REFERENCE_1_7.md`. No official Gunny client inspection is claimed.

## 1.7 verification

- **142 stdlib tests passed**. After idle/icon source registration, affected
  sanctuary integrity and generator-preservation checks also passed.
- Chromium checked all **64** facility pairs across 14,949 movement steps:
  no unintended waypoint stops, collision violations or jumps. Real map travel
  rendered all eight walk frames and moved the camera with the HUD fixed.
- All eight NPC/facility links, commission tracking/claim, disabled repeat claims,
  appearance/ambient settings, zoom, save reload, existing settings/garden and
  campaign briefing/deployment/Auto/pause passed. 960x540 touch map buttons stayed
  visible and reached/opened the garden. No JS errors or external requests.
  Evidence: `validation/SANCTUARY_BROWSER_1_7.json`.
- In this headless Chromium run, median/p95 requestAnimationFrame interval was
  16.7ms and measured hub draw work averaged 2.383ms. These are local observations,
  not a performance guarantee for other devices or browsers.

- Final art/input checks rendered eight distinct frames for every direction of
  all three avatars, loaded twelve idle poses and nine authored dock icons/two
  currency illustrations. Inverse-camera ground clicks and modal keyboard
  navigation passed. Evidence: `validation/SANCTUARY_ART_INPUT_1_7.json`.
- Fresh ZIP extracted into a directory with spaces and launched from another cwd
  with `python -S`: close camera/art HUD, actual UI/garden planting, tick-zero
  campaign briefing, 125-Qi deployment, Auto and pause passed. No JS errors or
  external requests. Evidence: `validation/RELEASE_SMOKE_1_7.json`.

The sections below are historical verification for earlier releases. Combat
balance policies were not rerun for this sanctuary presentation update.

## 1.6 changes

- Interactive HD-2D Celestial Sanctuary replaces the old main lobby: native
  painted scene, eight NPC destinations, separate buildings, detailed cutouts,
  three four-direction avatar sheets, animated water/light/petals and owned props.
- WASD/arrows/Shift, ground/NPC clicks, E/Enter dialogue and Tab/M directory.
  Collision-safe routes and immediate bottom-bar access to existing systems.
- NPC commission page shows objectives, progress and rewards; one commission can
  be pinned. Following does not gate automatic progress or introduce extra income.
- Cosmetic appearances, validated position, discoveries and followed commission
  persist inside existing V2 saves. Mu Qing appearance unlocks after Wharf III.
  Currency, inventory and talents migrate intact; avatar choice changes no stats.
- Smooth hub rendering, readable system fonts, optional ambient motion respecting
  reduced-motion preference for new saves. Runtime remains Python stdlib/browser.

## 1.6 verification

- **142 stdlib tests passed** with `python3 -S -m unittest discover -s tests -q`.
  Includes six sanctuary checks for migration, atomic cosmetic actions, locked
  avatars, invalid imports, commission rewards/tracking, connected approaches and
  source-frame integrity; previous engine/server/economy/assets checks also pass.
- Chromium exercised all eight NPC routes and system links using actual canvas
  input; 64 facility pairs additionally reached their target by deterministic
  stepping. Keyboard movement, Enter dialogue, commission claim/pin, position and
  appearance persistence, reduced motion, legacy settings/garden, campaign
  briefing/deployment/Auto/pause and landscape touch passed. No JS errors or
  external requests. Fixture begins with a cleared campaign/one ready commission.
  Evidence: `validation/SANCTUARY_BROWSER_1_6.json`.
- Fresh portable ZIP extracted to a path with spaces, launched with `python -S`
  from another cwd: hub load, garden planting, tick-zero campaign briefing,
  deployment for 125 Qi, Auto and pause passed without external calls.
  Evidence: `validation/RELEASE_SMOKE_1_6.json`.

Combat parameters are unchanged in 1.6. The following 1.5 policy results remain
historical baseline evidence; the full balance simulations were not rerun for
this hub-only update.

## 1.5 combat and estate changes

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

## 1.5 baseline verification

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
