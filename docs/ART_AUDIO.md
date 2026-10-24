# Art and audio — version 1.2

## Raster art

The included assets are original integer-grid artwork. Regenerate them with
`python tools/generate_assets.py`, using Python's standard library only.
`tools/generate_cultivators.py` authors the higher-resolution hero action sheets,
region-specific rescue devices and map detail. This is optional authoring work;
all game-ready images are already committed.

| Asset | Native pixels | Contents |
| --- | --- | --- |
| title.png | 384 × 216 | Mountain-gate backdrop for the animated lobby |
| wharf.png | 1024 × 576 | Lantern palace, timber river deck, red lanterns and water detail |
| terrace.png | 1024 × 576 | Jade sky pavilion, pale stone, floating roofs and cloud terraces |
| tomb.png | 1024 × 576 | Bronze ancestral crypt, dark stone, funerary ornament and braziers |
| cultivators.png | 768 × 2048 | Eight native 64×64 heroes, four separate action states |
| guardians.png | 288 × 144 | Three native 48×48 devices, six frames each |
| sprites.png | 128 × 672 | Legacy portraits and four-frame enemies, bosses and altar |
| icons.png | 128 × 32 | Resource/action/status icons |

Each hero has idle (6), basic-attack (8), skill (10) and ultimate (12) authored
frames. `cultivators.json` maps state rows, frame counts and FPS. The runtime
chooses a state from actual simulation actions, anchored to its simulation start
time; pausing freezes the pose. Economy/healing/aura heroes use their support
activity rather than dealing a cosmetic basic attack. The generic attack sheet
is retained for each hero, including support poses.

`guardians.json` maps the Jade River Ark, Heaven Sword Array and Soul-Sealing
Bell. They have visibly different boat, flying-blade and bronze-bell designs.
Each sweeps its lane once. Region art puts a distinct defended building behind
the heroes. Water, wind, ley-node corruption and grave mist add runtime motion.

The logical board is 512×288 with five 32-pixel lanes, twelve columns and a 3×
backing canvas. Nearest-neighbor rendering retains raster edges. VT323 is bundled
under SIL OFL in `web/assets/fonts`; neither fonts nor images use a CDN.
Asset tests decode PNG chunks, check atlas coverage/transparency/action diversity,
and reproduce every generated file byte-for-byte with no external packages.

## Music

Ten original looped scores are bundled as OGG and MP3 for local decoding:
one lobby score, plus setup/pressure/onslaught arrangements for each region.
They use pentatonic melodies, damped and slightly inharmonic string partials,
pitch bends, transient plucks, breath/vibrato and percussion. The intended timbres
are guqin, guzheng, pipa, dizi, Chinese drums and gong. These are synthesized
instrumental arrangements, not recordings of acoustic instruments or performers.
No commercial song or recording was sampled.

Each region has its own melody, root, tempo and color. Setup is sparse; pressure
adds pipa and drums; onslaught adds rapid figures and gong accents. The encounter
phase comes from actual wave progression. Local buffers crossfade over 1.1s.
Music pauses with battle pause and a hidden document. Victory/defeat cues use
short pentatonic, plucked partials rather than the previous major-scale fanfares.

`tools/generate_music.py` optionally regenerates scores with NumPy, soundfile and
ffmpeg. Its generation dependencies are not game runtime dependencies. The
`music.json` manifest records filenames, tempos, durations and instruments.

## English character dialogue

Sixteen original English lines are bundled in `audio/voices`: one summon line
and one short ultimate line per cultivator. Each character uses a distinct
synthetic voice. Playback follows authoritative deployment/ultimate events, is
queued with ultimate priority and captions, ducks music, and stops obsolete
queued dialogue when changing battles. No voice service or synthesis runs while
playing. Master, Music, SFX and Voice have separate volume controls.

The optional authoring script `tools/generate_voices.py` uses Kokoro-82M v1.0
(Apache-2.0 model) with kokoro-onnx 0.6.1 (MIT), soundfile 0.13.1, ONNX Runtime
and ffmpeg. Model files are explicit local inputs and verified by SHA-256; model
weights are not distributed in this game. Attribution is in each audio folder's
NOTICE. These are fictional character lines, not actor performances or a claim
of real-person imitation.

## Effects and verification

Eight distinct SFX palettes remain tied to actual attacks/skills: jade chimes,
bamboo slash, flame, frost glass, stone/staff, lightning, healing and formation.
An output compressor and per-character throttling limit stacking. Audio starts
after the first user interaction, following browser autoplay rules.

Chromium decoded all 16 voice files and all 20 music encodings, played all eight
summon voices and a legally charged Yun ultimate, and crossed the actual setup,
pressure and onslaught phases. These checks verify local decoding and event
routing; the perceived mix still depends on speakers/headphones and preference.

The artwork and musical patterns are original repository assets. This remains a
compact procedural-art game; the higher resolution and generated dialogue are
not a claim of a full premium illustration, animation or voice-acting pipeline.
