# Art and audio — version 1.5

## Frame animation (1.5)

`web/assets/motion` holds 21 retained, image-generated transparent 4×4 sheets:
336 source frames. Each hero has idle (1), recoil (1), death (2), attack (4),
skill (4), ultimate (4); enemies/altar have walk (4), attack (4), skill (4),
idle (1), recoil (1), death (2). These are separate source drawings, not copies
of one transformed pose. Idle is a single pose; this is a compact animation set,
not a full studio-authored animation production.

`motion.json` records native dimensions, source SHA-256, frame rectangles and
registration offsets. `tools/register_motion.py` optionally reads alpha
connectivity to exclude detached neighboring-cell fragments, writing metadata
without modifying PNG pixels (Pillow is authoring-only). The stdlib asset
preservation command copies the entire motion directory unchanged.

`web/combat_motion.js` selects frames from simulation time and attack windup;
pausing freezes them. Source images load only when an actor is rendered and are
decoded to a maximum width of 768 pixels. Native detail remains in the repository.
Death remains survive 0.8 simulation seconds and never become combat targets.
The old large portraits/pose atlases remain fallbacks and lobby artwork.

`objectives.png` retains three new props: jade caravan, Azure beacon and Bone
Court tablet; `objectives.json` stores separate source rectangles. Combat VFX use
a separate canvas before being composited at the chosen clarity opacity. Threat
outlines/countdowns remain legible above that layer. Existing music and English
voice assets are unchanged in this release.

## Authored actors and botany (1.4)

The active renderer now uses seven transparent authored actor sheets, with
21 identities and 71 poses: eight cultivators × idle/attack/skill/ultimate;
twelve enemy archetypes plus the altar × idle/attack/skill. Hero sources are
1536×1024; enemy sources are 1506×1044. They are original image-generated RPG
style assets, retained unchanged. `actors.json` crops/anchors them at draw time;
`actors_manifest.json` records dimensions and SHA-256 hashes. These are pose
cutouts with runtime breathing, lunging and casting transforms plus event VFX,
not a new set of hand-drawn frame-by-frame animation sheets.

The new 1672×941 garden has an alchemy pavilion, merchant and soil terrace;
`crops.png` is a transparent 1330×1182 sheet of four crops × four growth stages.
`crops.json` provides source bounds. No image processing or asset download is
needed at startup. The earlier 64×64/32×32 procedural atlases remain fallbacks.

The asset generator preserves/copies **all** authored source PNGs and JSON
metadata; it regenerates only fallback sprites, icons and the title. It cannot
recreate these paintings from a seed. Native sources are larger and more
detailed, while the game keeps its 512×288 logical grid and threefold canvas.

## Scenes and artifacts

The three region scenes are newly image-generated 16-bit RPG style authoring
inputs, retained as committed PNGs. They have distinct composition, materials,
landscape and architecture: a lantern-lit timber river residence; a pale jade
observatory on floating peaks; and an angular bronze necropolis beneath rock.
`web/assets/scenes.json` records native dimensions, SHA-256 and courtyard alignment.
Wharf and Terrace are 1672×941; Tomb is 1672×940. These replace the former 1024×576
procedural recolor family. No image is fetched or generated at runtime.

The transparent 2172×724 artifact sheet contains an ornate dragon skiff, a
nine-sword armillary altar and a bronze bell in a beast-headed ritual arch.
`guardians.json` stores separate bounds. Runtime water trails, levitation and
energy particles animate the cutouts. Their battle behavior remains one rescue
per lane; the illustrated briefing displays their designs and effects.

`python tools/generate_assets.py` regenerates deterministic fallback 64×64 cultivator
state sheets, fallback enemy sprites, icons and the title backdrop, and **preserves/copies**
the authored scene and artifact PNGs. It does not recreate image-generated art
from a random seed. Tests decode RGB/RGBA PNGs, check scene checksums and atlas
bounds/transparency, reproduce procedural assets, and preserve retained art inputs.
VT323 remains bundled under SIL OFL.

## Cast choreography

`web/battle_visuals.js` renders actor-specific skill/ultimate choreography from
actual server events and simulation time. Examples include ten sword trails,
three fire-lotus impacts, a full-lane ice eruption, a mountain/shield shockwave,
lightning strikes, healing-leaf spirals and an eight-direction formation circuit.
The client uses effective support target counts/radii and keeps the animations
frozen while paused. Units enlarge while casting. The server preserves the cast
pose when hit, and tick/command revisions reject late HTTP snapshots that would
otherwise erase a freshly received effect. Visuals do not apply damage.

## Encounter music

Twenty-eight original looped scores are bundled in OGG and MP3: a lobby score
and three arrangements for each of nine individual encounters. The nine melodies,
titles, roots and harmonic routes are distinct. Setup is sparse; pressure adds
pipa/drums; onslaught adds rapid figures and gong accents. The style uses
pentatonic melodies and physically inspired guqin/guzheng/pipa/dizi timbres.
These are synthesized instruments, not acoustic performance recordings.

Python selects intensity from wave phase plus actual battlefield pressure:
five enemies/two elites raise pressure; ten enemies/four elites or a close boss
trigger onslaught. Six seconds of release prevents rapid oscillation. The browser
loads the **encounter** family, crossfades locally over 1.1 seconds, raises the
climax mix, and ducks moderately under speech. Default new-profile music volume
is 38%; existing player volume choices are retained. The buffer cache holds at
most three decoded music tracks. Pause/hidden-document controls remain in effect.

Optional regeneration uses `tools/generate_music.py` with NumPy, soundfile and
ffmpeg. These are authoring dependencies, not game startup requirements.

## Directed English dialogue

`game/performances.py` defines sixteen takes, two per hero, with phrase-level
pace, energy, pauses and delivery direction: nervous hope, quiet resolve,
playful confidence, icy authority, protective warmth, eager bravado, urgent
compassion and a rallying command. The optional Kokoro-82M authoring tool blends
voice timbres, synthesizes phrases separately, builds their energy, and adds
light ultimate ambience. These are synthetic voices, not human actor performances.

All MP3s, subtitles and direction metadata are included in `audio/voices`.
A bounded, expiring queue prevents obsolete lines from accumulating during Auto;
ultimate lines take priority. Voice gain and music ducking are independent.
The model is Apache-2.0; kokoro-onnx is MIT. Notices remain in the audio folders.
No model weights, remote TTS call or synthesis dependency is part of runtime.
`--heroes fire` can regenerate a selected performance while retaining other takes.

## Verification scope

Chromium decoded all **72** audio encodings (56 music + 16 voices), loaded nine
actual encounter families and escalated music during setup in a crowded fixture.
Controlled combat fixtures rendered all eight actual automatic ultimate events;
a delayed HTTP snapshot test preserved the cast and Auto setting. Paid talent
purchases and sampled canvas pixels distinguished learned/available/locked nodes.
Nine illustrated region pages and landscape touch were exercised.

Those checks establish assets, routing and behavior. Musical taste, emotional
voice quality and the mix on individual speakers remain subjective.
