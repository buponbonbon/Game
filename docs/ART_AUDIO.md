# Art and audio

## Shipped raster artwork

The game ships its original artwork in `web/assets`; it never downloads sprites,
fonts, backgrounds or sound libraries at runtime. `tools/generate_assets.py`
authors the images directly on integer pixel grids with Python's standard
library, then writes RGBA PNGs using `struct` and `zlib`. No image package, asset
marketplace, stock illustration, proprietary character, emoji or external font
is used.

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
| `wharf.png` | 384 × 216 | Lantern-lit timber deck above the river |
| `terrace.png` | 384 × 216 | Mossy stone terrace, mountain clouds and wind banners |
| `tomb.png` | 384 × 216 | Moonlit mausoleum with spirit braziers and bone fragments |
| `sprites.png` | 128 × 672 | Eight heroes, nine ordinary enemies, three bosses and a soul altar |
| `icons.png` | 128 × 32 | Sixteen small resource, action and status emblems |

Each actor occupies one 32-pixel-high row and has four 32 × 32 frames. The direct
ID mapping in `sprites.json` provides `x`, `y`, `w`, `h` and `frames`; advance the
source x-coordinate by `frame * w`. Feet rest near row 29. Heroes face right and
invaders face left. Weapon poses, breathing, steps and lunges distinguish the
frames; these are compact four-frame animations rather than separate extensive
idle, attack, skill and death sheets.

The board occupies x = 44–349 and y = 49–173 at the internal 384 × 216 resolution.
Its nine columns use 34-pixel tiles, and its five lanes use 25-pixel tiles. The
browser draws the scene with image smoothing disabled, an embedded 5 × 7 bitmap
alphabet and pixel-sized interface details. It provides a fit display and an
integer-scale option. Large bosses are enlarged with nearest-neighbor sampling.

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

Each region has a different eight-note musical pattern with a slower supporting
tone. The browser schedules the pattern locally; the music pauses while battle
is paused or the document is hidden. These are compact synthesized loops and
feedback tones, not the long, fully arranged soundtrack or complete per-hero
sound inventory described in the production brief.

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
