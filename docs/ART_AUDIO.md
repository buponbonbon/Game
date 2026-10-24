# Art and audio

## Shipped raster artwork

The game ships its original artwork in `web/assets`; it never downloads sprites,
fonts, backgrounds or sound libraries at runtime. `tools/generate_assets.py`
authors the images directly on integer pixel grids with Python's standard
library, then writes RGBA PNGs using `struct` and `zlib`. No image package, asset
marketplace, stock illustration, proprietary character, emoji is used for artwork. VT323 is bundled separately from the Google Fonts
repository under the SIL Open Font License; see `web/assets/fonts/OFL.txt`.

Regenerate the committed images with:

```bash
python tools/generate_assets.py
```

The generator is deterministic. `tests/test_assets.py` regenerates every image
in a temporary directory and compares its bytes with the shipped asset. The
tests also check PNG chunk checksums, actual decompression, complete backgrounds,
sprite transparency, atlas bounds, coverage of every content ID and four distinct
frames per actor.

| File | Native size | Purpose |
| --- | --- | --- |
| `title.png` | 384 × 216 | Mountain gate, lanterns and a solitary sword cultivator |
| `wharf.png` | 512 × 288 | Lantern-lit timber deck above the river |
| `terrace.png` | 512 × 288 | Mossy stone terrace, mountain clouds and wind banners |
| `tomb.png` | 512 × 288 | Moonlit mausoleum with spirit braziers and bone fragments |
| `sprites.png` | 128 × 672 | Eight heroes, nine ordinary enemies, three bosses and a soul altar |
| `icons.png` | 128 × 32 | Sixteen small resource, action and status emblems |

Each actor occupies one 32-pixel-high row and has four 32 × 32 frames. The direct
ID mapping in `sprites.json` provides `x`, `y`, `w`, `h` and `frames`; advance the
source x-coordinate by `frame * w`. Feet rest near row 29. Heroes face right and
invaders face left. Weapon poses, breathing, steps and lunges distinguish the
frames; these are compact four-frame animations rather than separate extensive
idle, attack, skill and death sheets.

The board occupies x = 92–475 and y = 60–219 at the 512 × 288 logical
resolution. Twelve columns and five lanes use 32-pixel tiles. Columns 1–9 permit
deployment, column 0 visibly contains guardian artifacts, and the two rightmost
columns provide enemy approach space. Region-specific palaces and shrines occupy
the space behind the guardians. Drawing uses nearest-neighbor sprites and a 3x
backing canvas, with locally loaded VT323 text for legibility and full punctuation.

The palette uses dark ink outlines, muted jade, weathered gold, warm lantern red,
ice blue and violet. Each environment uses stepped color bands and small raster
clusters. The wharf's horizontal plank grain, the terrace's mossy cracks and the
tomb's desaturated stone distinguish the three arenas while leaving combat
silhouettes readable.

## Synthesized sound

The browser's `AudioContext` generates original audio locally after the first
pointer or keyboard interaction. No audio files, remote audio service or external
JavaScript library are required. An audio context starts or resumes in response
to input so normal browser autoplay rules remain in effect.

The implemented audio has three gain stages: Master, Music and SFX. Settings let
the player adjust their volumes. SFX use short sine, triangle, square or sawtooth
oscillator tones with attack/decay envelopes. Separate cues cover selection,
confirmation, placement, Qi, hit, kill, death, error, skill, ultimate and upgrade;
victory and defeat use short note sequences. Repeated hits are rate-limited to
avoid stacking a sound on every rendered frame.

Four separate 32-note scores cover the lobby, wharf, terrace and tomb. They have
distinct melody, tempo, root and instrumentation, with bass, pad and percussion
layers; bosses add rhythmic accents. Scheduling and synthesis remain entirely
local. Music pauses with battle pause or a hidden document.

Each hero has a distinct pitched/noise palette: jade chimes, bamboo slashes, flame
bursts, glassy frost, low stone/staff impacts, electric transients, healing notes
and formation bells. Simulation events carry stable actor IDs, so character SFX
are tied to real attacks/skills rather than decorative particles. Placement and
Ultimates use the same character identity. Per-character throttling limits clutter.

Automated checks can establish that the audio context starts and events dispatch
without browser errors. They do not establish perceived musical quality, speaker
output, loudness on every device or accessibility for a particular listener.
Check the Master, Music and SFX sliders on the intended speakers or headphones
when evaluating the mix.

## Scope and ownership

The artwork and synthesized patterns were authored for this repository. No
existing game's characters, exact level art, sound recordings or interface
illustrations were copied. This release is a compact playable adaptation of the
design reference; its small atlases and oscillator sound system should not be
represented as a full premium art-and-audio production pipeline.
