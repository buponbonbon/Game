# Sanctuary UI research and implementation — 1.7

Research date: 2026-10-26 (Vietnam client date).

The user requested contemporary game UI references, especially Gunny. Searches
were attempted for Gunny Origin and lobby UI. Official Gunny pages at
`https://gunny.zing.vn/`, `https://gunny.vnggames.com/`, Google/Bing results and
Google Play were rejected by this environment's network proxy (403).
A public GitHub repository search succeeded; its unofficial Gunny projects do
not establish the appearance or behavior of the current official game. The
externally hosted screenshot linked by one README was also blocked. No claim is
made that the official current Gunny client was visually inspected.

An accessible web MMORPG reference was inspected instead:

- [Kaetram public repository](https://github.com/Kaetram/Kaetram-Open).
- [Client interface markup](https://github.com/Kaetram/Kaetram-Open/blob/develop/packages/client/components/game.astro): separate quest/reward panels, inventory/quest/settings buttons, ability shortcuts and a dedicated map frame with destination controls.
- [Client interface styles](https://github.com/Kaetram/Kaetram-Open/blob/develop/packages/client/scss/game/_index.scss): separate interface modules for player/profile, quests, map, interaction and zoom.

These were layout/interaction references. The implementation and artwork in this
project are original; no game code or assets were copied from these references.
The chosen layout uses fixed screen-space currency/profile/shortcuts, an
illustrated map and compact contextual NPC labels rather than persistent hover
instruction text. It is not an imitation or recreation of Gunny's UI.

## Why the previous sanctuary felt jerky

The movement loop consumed one grid segment per frame and spent an extra frame
shifting a reached waypoint, resetting its walking phase during that stop. The
new loop spends the frame's full distance budget across route segments, removes
unnecessary grid turns with collision-checked line segments and ties gait phase
to distance traveled. Sprite feet are registered individually from source alpha;
body scale is shared across a character's frames. Eight walking frames per
facing replace the former three walking poses. Standing uses separate directional
idle poses, and NPCs no longer perform slow sliding walk cycles in place.

The view starts at 1.85x zoom, follows position with time-based camera easing and
clamps to the scene edges. Ground clicks use the inverse camera transform.
The HTML/CSS interface stays in screen space. Position-only saves skip hero
preview refresh and are throttled while moving; explicit stops/transitions save.

Browser timing evidence is an observation from this cloud Chromium run, not a
universal performance guarantee. The report also checks every movement step for
collisions, unintended stops and jumps; these checks address the reported jerk
at waypoints directly.
