# Build status — version 1.4

Download/extract the repository and run `python run.py` (Windows: `play.bat`).
Python 3.10+ and a modern browser are the only runtime requirements. No package
installation, account, remote API or online asset download is needed.

## Changes in 1.4

The lobby's Sect Estate adds a persistent economy using existing Spirit Stones,
Insight for research, and harvested ingredients. Battle Qi stays separate.

- Three starting plots, expansions to six/nine, four crops, watering/fertilizer,
  two irrigation upgrades and two research tiers per crop. Growth is earned by
  completed battles: victory, or a loss reaching half the waves and 60 seconds.
  No offline timer or withering; leaving early never grows crops.
- Three alchemy formulas with exact triggers/costs/ranges. Equip one preparation;
  successful battle creation spends one dose. The last dose automatically clears
  the slot. Tea supports the first three summons; Dew counters a regional hazard;
  Soul Ward automatically cleanses a full curse and reveals ghosts.
- Seed/fertilizer/produce merchant, three purchasable/toggleable decorations,
  three rotating commissions, eight achievements and twelve enemy research tracks.
  Research includes separate boss thresholds and one-time stone/Insight rewards.
- Six-wave Nursery Defense: three active lanes, independent two-health herb beds,
  seed rewards according to surviving beds, illustrated briefing and paid timed
  Garden Shelter shields. This is separate from the nine campaign encounters.
- Talent resets refund the amount actually paid, including the legacy 35-stone
  purchase basis; first reset free, later fee 10 deducted from the refund.
- Version-1 saves migrate to version 2, preserving wallet, campaign, settings,
  best results and talents. Starter supplies appear once. Terminal results are
  settled from server state. Save ledgers/live receipts prevent duplicate rewards
  and recover lost outcome responses. New results display loot and crop growth.
- Redesigned authored actor sheets: eight cultivators, twelve enemies and altar,
  71 distinct action poses with runtime motion and existing actor-specific VFX.
  New garden painting and sixteen crop stages. Retained source images are bundled;
  asset regeneration preserves them and reproduces procedural fallbacks/icons.

Prior 1.3 features remain: nine encounter themes × three adaptive arrangements
plus lobby music, five-lane final assaults, smart Auto Ultimate, exact range/skill
manuals, two talent paths, directed English synthetic voices, VT323 and distinct
region scenes/rescue artifacts.

## Verification

- **115 standard-library tests passed.** These cover existing combat/server/content
  behavior and new migration, transactional spending, crop yield/growth, preparation
  triggers, independent beds, real outcome settlement, lost-response receipts,
  one-time claims, talent refund accounting and native art integrity/bounds.
  Run `python3 -S -m unittest discover -s tests -v`.
- The earned-budget legal campaign policy still cleared **9/9** with no invalid
  commands and no preparations. Eight stages retained three seals; the final
  retained two. Evidence: `validation/CAMPAIGN_1_4.json`. Reproduce with
  `python3 -S tools/simulate_campaign.py --output report.json`.
- Nursery Defense cleared without talents/preparations at seeds 1, 42 and 4701,
  retaining all three beds (six health), in 166.017 simulation seconds. Each run
  used normal costs/cooldowns and zero invalid commands. Authored waves are largely
  deterministic, so these are smoke runs, not independent statistical trials.
  Evidence: `validation/NURSERY_1_4.json`.
- Chromium exercised real canvas purchases, planting/watering/fertilizer,
  research, harvests, brewing/equipping, dose consumption, decorations, milestones,
  achievements, commissions and legacy respec/new talent purchase. A deliberately
  dropped outcome response recovered the same receipt without duplicate growth.
  Reload retained fields/inventory without regranting supplies. Desktop and
  landscape touch rendered without JavaScript errors or external requests.
  Terminal snapshots and actor galleries used controlled server fixtures;
  they are UI/settlement checks, not additional balance wins.
  Evidence: `validation/ESTATE_BROWSER_1_4.json`.
- A fresh packaged release was extracted into a path containing spaces and
  launched from another working directory with `python -S`. Internal HTTP and
  actual canvas smoke verified catalog/estate, tick-zero briefing, deployment,
  normal Qi spending, Auto and pause. No asset network service was required.
  Evidence: `validation/RELEASE_SMOKE_1_4.json`.

## Practical limits

Saves remain local and editable. Active battles and uncollected receipts do not
survive a Python server restart; collect results first. Keep the same browser and
localhost port, or export/import Chronicles to transfer progress. Progress is not
cloud synced. Native Windows/macOS launchers and other browser engines were not
executed here; Linux Chromium and landscape touch were exercised.

New actor art uses authored pose cutouts plus runtime transforms/effects, not
new frame-by-frame hand animation. The nursery reuses the first Wharf music
family with its existing adaptive arrangements. Voices remain synthetic and music
uses synthesized Chinese-inspired timbres. Art/music taste and long-term economy
pacing still benefit from player feedback; the seeded policies are not an
exhaustive balance study. There is no full cinematic campaign or New Game+.
