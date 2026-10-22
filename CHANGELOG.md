# CHANGELOG — The Commander Boomer Shooter

*"For we are his workmanship, created in Christ Jesus for good works, which God prepared beforehand, that we should walk in them."* — Ephesians 2:10

---

## [2026-10-19c] — Encounter layout + horror lighting in M_Blockout01

### Added
- **18 encounter actors populated into M_Blockout01** (headless commandlet): 9 enemy encounter markers (3 Drones, 2 Zealots, Phantom, Brute in the pit, Golem on the platform, Nor-Easter Titan boss at north wall), 6 pickups/keycards (health+red keycard in pit risk/reward, armor on platform, 2 ammo, green keycard on pillar top), 3 weapon spawns (starter Puckle by PlayerStart, Mayflower mid-arena, Rocket guarded on platform)
- **Horror lighting beats** — 4 point lights (pit red, pillar key-green, boss cold blue, spawn warm) + exponential height fog actor, matching level1_bible.md's HORROR tier
- **Scale normalization** — every mesh auto-scaled to its per-type target height from real mesh bounds (drones 60uu … titan 300uu, pickups 40uu, weapons 60uu)
- **`Tools/python/spawn_probe.py`** — spawn-API diagnostic harness (isolated the spawn failure class in one engine boot)

### Fixed
- `spawn_actor_from_object` returns NULL for EVERY input in this engine build (proven by probe: engine cubes, FBX meshes, both APIs, fresh level) → populate now uses `spawn_actor_from_class(StaticMeshActor)` + `set_static_mesh()` (probe-proven, 18/18)
- `BoxSphereBounds.extent` doesn't exist from python → `box_extent` (half-extents, x2)
- `target_height` rules keyed on asset prefixes (`E_/P_/W_`) while labels use `ENC_/PU_/WP_` — every spawn had silently fallen through to the 100uu default; fixed to real label prefixes
- Actor-list dedup APIs all removed in this 5.8 build (`EditorLevelLibrary.get_all_actors_of_class`, `UnrealEditorSubsystem.get_all_level_actors`, `World.persistent_level` — all AttributeError) → documented pitfall: restore map from git for clean re-runs
- `fog_density` read-only from python → keep component default 0.02

### Verse
> *“So we built the wall... for the people had a mind to work.”* — Nehemiah 4:6
> Chosen because this leg was literally wall-building — placing encounters into the arena map at 2am with the fleet humming is the same unglamorous, wholehearted construction the verse celebrates.

## [2026-10-19e] — Audio + combat tuning docs + actor-listing API recovered

### Added
- **`Docs/generated/sound_design_list.md`** (7.1K) — 6-weapon SFX table (reload explicitly 'none — instant hold-refire per contract'), all-6 enemy vocal/telegraph table, per-beat ambient beds, 3 music cues (foghorn/ship bell/distorted accordion/timpani), gib audio pooling spec, Content/SFX naming convention + file tree
- **`Docs/generated/weapon_stats_table.md`** (5.7K) — tuned per-weapon stats (fire rate, hitscan/projectile, damage, spread, ammo economy), ammo math for full arena clear, TTK-per-enemy table with recommended weapons, boss phase-2 storm note, difficulty scalar knobs
- **`Tools/python/api_inventory_probe.py`** — dir() inventory harness for editor APIs

### Fixed
- **Actor-listing API name recovered** (apilist_run1): `EditorActorSubsystem.get_all_level_actors()` exists and works — my earlier chain called `get_all_actors_of_class` (exists nowhere), `UnrealEditorSubsystem.get_all_level_actors` (wrong class), and `World.persistent_level` (not python-exposed). populate_encounters.py dedup chain now uses the real names; earlier "APIs removed" note corrected
- sound_design_list.md token-cap truncation spliced + completed

### Verse
> *“Praise him with tambourine and dance... with strings and pipe!... with loud clashing cymbals!”* — Psalm 150:5-6
> Chosen because this commit is the audio kit — the sound doc literally specifies the cymbals, and the whole entry is about the orchestra of the thing.

## [2026-10-19d] — Design docs generated on local inference (Main Qwen3.8)

### Added
- **`Docs/generated/level1_bible.md`** (5.9K) — Plymouth Dark beat sheet, encounter rationale, 2 secret designs, verticality metrics, blockout checklist
- **`Docs/generated/blueprint_build_spec.md`** (19.8K) — node-by-node UE 5.8 build spec for tomorrow's editor session: BP_Player (600uu/s movement table), BP_Weapon base + 6 children (zero reload nodes, by contract), BP_Pickup, BP_Enemy + gib pooling, WBP_HUD, GameMode wiring, ordered Build Order Checklist + Definition of Done with acceptance criteria
- Generated entirely on Main's local Qwen3.8-27B (3 inference passes, zero cloud) — truncated passes spliced and completed, generic drift trimmed

### Verse
> *“By wisdom a house is built, and by understanding it is established; by knowledge the rooms are filled with all precious and pleasant riches.”* — Proverbs 24:3-4
> Chosen because these two documents ARE the house's blueprints — the level bible is the understanding, the build spec is the knowledge, and tomorrow's editor session fills the rooms.

## [2026-10-19b] — Blender→FBX→UE leg complete

### Added
- **14 Blender blockout meshes** (portable Blender 4.2.23 LTS, fully headless `-b`) — 3 weapons (Pilgrim Puckle, Mayflower Cannon, Harbor Wreck Rocket), 5 pickups/keycards (health cross, armor shard, ammo box, green+red keycards), 6 enemy proxies (one per weapons_enemies_v1.json enemy) — sources in `Tools/blender/out/`
- **26 UE assets imported headless** — `Tools/python/import_weapons_fbx.py` commandlet: 14 static meshes + 12 materials into `/Game/Weapons`, imported=14 failed=0, zero Python errors (verified against run log)

### Fixed
- `--out` argv parsing in both Blender scripts (flag was consumed as the output path; exports had landed in a stray `--out` directory — relocated and parser corrected)

### Verse
> *“And I am sure of this, that he who began a good work in you will bring it to completion.”* — Philippians 1:6
> Chosen because leg one (map) flowed straight into leg two (assets) with the same pipeline — the "good work started" here is literally the sovereign asset loop completing itself.

## [2026-10-19]

### Added
- **Headless UE 5.8 content pipeline LIVE** — `PythonScriptPlugin` + `EditorScriptingUtilities` enabled in `.uproject`; `Tools/python/blockout_map.py` ran via `UnrealEditor-Cmd -run=pythonscript` and produced **M_Blockout01.umap** (23 actors: arena floor, walls, pillar, 8 cover blocks, platform + ramp, hazard pit ring, PlayerStart, sun) — verified on disk, 11.6 KB
- **Sovereign local-inference content pass** — `Docs/generated/weapons_enemies_v1.json`: 6 escalating weapons (Pilgrim Puckle → Harbor Wreck Rocket) + 6 Plymouth-themed enemies (Barnacle Drone → Nor-Easter Titan), generated on Main's Qwen3.8-27B (no cloud)
- **Blender→FBX→UE pipeline scripts** — `Tools/blender/weapon_blockouts.py` (3 weapon blockout meshes, pure primitives) + `Tools/python/import_weapons_fbx.py` (headless FBX import commandlet)

### Fixed
- Reverted stale 2026-09-30 uncommitted edit to `The_Commander_Boomer_Shooter.md` (said "GoDot" + flipped the no-reload rule — both contradict the locked UE 5.8 design contract); diff preserved as patch in temp before revert

### Verse
> *“But as for you, be strong and not give up, for your work will be rewarded.”* — 2 Chronicles 15:7
> Chosen because this is the first all-night build of the sovereign game pipeline — the grind of tonight (headless commandlets, mirror hunting, plugin forensics) is exactly the "work" this verse promises is not wasted.

## [2026-09-22]

### Added
- **UE 5.8 Blueprint project initialized** — Project structure + design brief (commit cef143e)

### Verse
> *"Whatever you do, work at it with all your heart, as working for the Lord."* — Colossians 3:23
> Chosen because this is the Commander's personal project — every polygon, every blueprint node, is an offering.

## [2026-10-21] X-COM Enemy Pass + Command Center + Aux Vision Repair

- **Aux vision repaired.** `auxiliary.vision` in `%LOCALAPPDATA%\hermes\config.yaml` repointed
  from `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` to
  `minimax/minimax-m3.1-flash:free` (provider `custom:openrouter`) per Commander directive.
  Verified end-to-end: `vision_analyze` on a synthetic probe image returned an accurate
  description (red block upper-left, blue block lower-right). Ebert's eyes work again.
  Backup of the pre-patch config retained as `config.yaml.bak-2026-10-21-*`.
  Scope note: only `auxiliary.vision` was touched. The `delegation`, `providers`, `model.default`,
  and `compression` blocks belong to another lane and were not modified.
- **5 true-3D X-COM enemies built** (`Tools/blender/xcom_enemies.py`, Blender 4.2.23 LTS, headless):
  Sectoid, Viper, Floater, Muton, Chryssalid. Original 1994 *UFO: Enemy Unknown* roster,
  modernized (chitin/armor/plasma materials, emissive eyes + power cores, sane polycount
  1.9k-3.7k tris). Each ships with the "reveal" light rig that reproduces the 1994
  terror-mission reveal - hard cold key, colored alien rim, low under-glow.
  Output: `Tools/blender/out_xcom/` - 5 FBX + 5 lit preview PNGs (720x900) + `xcom_manifest.json`.
- **Command Center live** - `CommandCenter/serve_outputs.py` serves a single dashboard at
  `http://10.0.0.93:8899/` aggregating fleet node status, swarm ledger, task queue, agent
  output slots, renders, Blender kit, UE content inventory, design docs and git state.
- **Swarm harness** - `CommandCenter/SWARM_TASK_QUEUE.md` (8 tasks),
  `CommandCenter/SWARM_LAUNCH_PACKETS.md` (5 ready-to-paste window prompts, 2x HTPC + 3x Main),
  `Tools/blender/blender_turn_htpc.sh` (flock-serialized Blender turns - the HTPC has
  ~5GB free and a second concurrent Blender would OOM the node).
- **Ebert re-armed** with his own rubric (`Agents/Ebert/designs/zero_trust_likert_rubric.md`,
  7 weighted axes, 6.2 pass bar, screenshot-as-evidence, no rounding). Scoring the enemy
  kit and defining the bar for level design, background textures and lighting.

> Psalm 33:6 (ESV) - "By the word of the LORD were the heavens made; and all the host of them
> by the breath of his mouth." Chosen because every asset in this pass is made by command,
> and the swarm only executes what is spoken to it.

## [2026-10-21b] — Arena integrity: poisoned commit, missing floor hole, buried ramp

### Fixed
- **The arena was never actually restored.** Commit `0a2e558` enshrined a REVERTED map:
  the git blob for `Content/Maps/M_Blockout01.umap` is 50,181 bytes / 25 actors, not the
  80,624-byte / 46-actor level. Chain of custody, recovered from the logs: the restore did
  hit disk at 01:12:51 (`[LEVELDUMP] on-disk umap after: 80624 bytes`), and 18 seconds later
  a builder's `git checkout` destroyed it - and the commit then froze the destroyed file.
  **Rule adopted: the blob size inside the commit is now the only proof. A dump reads the
  editor's in-memory world and proves nothing about the file on disk.**
- **The floor had no hole at all.** `BO_Floor` was a single unbroken 40x40m plane at z=0, so
  the pit, its rim, `ENC_Brute_Pit`, `PU_KeyRed_Pit` and `PU_Health_Pit` sat *underneath* the
  floor surface - invisible and unreachable. The renders were cutting the floor open to
  depict a level the map did not contain.
- **The NE ramp was buried in the platform.** `BO_Ramp_NE` at (950,950) sits inside the
  platform footprint (800-1600), so it never reached the floor and the Golem encounter on
  the platform had no approach.
- **`Tools/python/fix_pit_and_ramp.py`** (new): derives the floor surface height `S` from the
  live mesh (plane -> `loc.z`, cube -> `loc.z + scale.z*50`), re-cuts the floor around the pit
  with the same mesh, drops the pit floor 100u below `S`, rebuilds the rim as 200u walls
  (100u proud of the floor), re-places `BO_Ramp_NE` clear of the platform footprint, and
  self-verifies the resulting ramp tilt from the actual transforms.
- **UE 5.8 commandlet pitfall: `-script=` needs FORWARD SLASHES.** With backslashes, `FParse`
  truncated the value at the first backslash run - `C:\Users\Gillsystems Laptop\source` -
  so every script load died with `Could not load Python file`, the run still printed `[DONE]`,
  and the map was never touched. Every historical success in this repo used forward slashes.
  `Tools/python/run_arena_fix.bat` now uses the forward-slash form verbatim, plus a
  pre-flight existence check and a `tasklist | findstr` guard (the guard had been calling
  MSYS `find`, which silently failed).
- **Own-vision pass caught a disqualifying defect before the critic did.** The v2 Floater
  still shipped five legs each ending in a rounded glowing cyan orb - the exact defect
  named in round 1 - and the v2 lighting renders came back with rim 2/7 and under-glow 3/7
  against a rig whose own `verification.json` showed `under_energy` of 1.2W and a face-zone
  `p99_lum` of 1. Both were re-steered with hard numeric acceptance criteria before any
  scoring pass ran.

### Changed
- Level builder permanently hard-stopped from `UnrealEditor-Cmd`, commandlets, populate/apilist
  /dump scripts, git, `Content/Maps/**` and `Docs/generated/level_transforms.json`. Blender-only.
- The map and dump leg is assistant-owned. Builders do not commit.

### Verse
> *"But be doers of the word, and not hearers only, deceiving yourselves."* - James 1:22 (ESV)
> Chosen because this entry is entirely about the difference between hearing a report
> ("[DONE]", "TOTAL=46", "restored") and doing the thing (reading the file, checking the blob).

## [2026-10-21c] — The pit is real: floor cut open, ramp landed on the platform

The arena map said one thing and the renders said another. The renders showed a pit the map did not
contain, and a ramp buried inside the platform it was supposed to reach.

**Root cause (two separate defects, both confirmed against the live map, not against a stale JSON):**
1. `BO_Floor` was a single unbroken 40x40m plane at z=0 with no hole cut in it. The pit, its rim,
   `ENC_Brute_Pit`, `PU_KeyRed_Pit` and `PU_Health_Pit` all sat *under* the floor surface — invisible
   and unreachable. The pit was a drawing, not a place.
2. `BO_Ramp_NE` was at (950, 950) — inside the platform footprint (800..1600) — so it was buried in the
   platform and never reached the floor.

**Fix:** the floor is now four segments (N/S/E/W) around a real hole spanning x[-1525..-875] ×
y[-1525..-1075]; the pit floor sits 100 units below the arena floor at z=-100; the rim walls are 200
units tall (100 proud of the floor) with a 2m entrance gap in the east wall; the pit's three actors
were moved down onto the pit floor; and the ramp was rebuilt from the platform's own measured top
(z=500) and south edge (y=800) so its high end lands exactly on the platform lip and its low end
exactly on the arena floor (pitch 18.4 degrees, roll -18.435).

**Verified, not assumed:** the fix script reads every dimension from the live actors, and the run log
records `ramp roll=-18.4 high end z=500 (want 500) low end z=0 (want 0) ok=True`. The refreshed
transform dump shows 50 actors (floor 4 · wall 4 · cover 8 · pillar 1 · platform 1 · ramp 1 · pit 6 ·
ENC 9 · PU 6 · WP 3 · light 5 · fog 1 · playerstart 1) and the map grew 80,624 -> 86,437 bytes.
The blob size was verified inside the commit, because the last three "restores" of this map were
poisons.

*Proverbs 25:2 (ESV) — "It is the glory of God to conceal a matter: but the honour of kings is to
search out a matter." This mission was the search: three separate map states claimed the same arena,
and only reading the live geometry, not the intent, told us which one was real.*

## [2026-10-21d] — The green keycard is climbable, and the geometry is measured, not guessed

### Added
- **Pillar climb spiral** — 3 ledges (`BO_PillarStep_1/2/3`) spiralling up `BO_Pillar_Center` (top = 600uu) with walking surfaces at 200 / 390 / 580uu. Every rise is 200 / 190 / 190uu against the 250uu jump budget, so the green keycard on the pillar top is reachable. It was never a soft-lock (the bible's alternative reward is 200 health), but it was unjumpable as built.
- **World-space ramp endpoint probe** — `Tools/python/dump_level_transforms.py` now records `rec['ends']`, the two end points of every ramp measured from the live actor (right vector x half-extent x scale), instead of leaving the renderer to guess a roll sign.
- **Location-aware ramp verification** — the arena fix script now requires the platform ramp's high end to land within 150uu of the platform's south edge, not merely at the right height.

### Fixed
- **Renderer builds ramps from engine truth** — `Tools/blender/render_level.py` places each ramp at the midpoint of its measured ends, with the true slope length and a slope-aligned rotation (radians, metres), and draws the new ledges as cover blocks. The previous Euler guess could put a ramp metres from where it stands.
- **Pit exit ramp roll sign** — the first build put the deep end at z=0 and the floor end at z=-100; the script's own measurement caught it and the corrected build gives deep end z=-100 / floor end z=0.
- **Pillar lookup** — the climb step searched for a `BO_Pillar` actor that does not exist (the real actor is `BO_Pillar_Center`), so the ledges were never created and the map save silently no-op'd. The lookup is now a `BO_`-prefixed fuzzy match that cannot grab the keycard actor or its own ledges.

### Verified
- Engine-measured ramp ends in the refreshed dump: `BO_Ramp_NE` high end (1120, 800, 500) — exactly the platform's south edge — low end (1120, -700, 0) on the arena floor. `BO_Ramp_Pit` deep end (-1055, -1300, -100), floor end (-875, -1300, 0).
- The fix log records `ramp roll=-18.4 high end z=500 (want 500) low end z=0 (want 0) high y=800 (want 800) ok=True` and `pillar climb route OK - every rise is within the 2.5m jump`.
- Map grew 87,927 -> 92,202 bytes and now holds 54 actors (3 more than before: the climb ledges).

### Verse
> *"Test everything; hold fast what is good."* — 1 Thessalonians 5:21 (ESV)
> This leg replaced guessed geometry with measured geometry: the engine reports where each ramp actually ends, and the climb ships only because every rise was proven inside the jump budget.

### 2026-10-21e - Cameras re-aimed at the geometry the engine actually built

- The pit and platform frames were still aimed for the old guessed ramp positions. Once both ramps
  were rebuilt from engine-measured end points, the NE ramp's foot sat 15m from where the old
  eye-level camera stood, so the ramp fell out of frame and the platform read as unreachable.
- `CAM_PLAT` now stands behind the ramp's foot and looks up the slope; `CAM_PITRAMP` looks down the
  pit exit ramp from over the rim. Both landings are in frame in both shots.
- `gameplay_06_pitramp.png` is new: the pit exit ramp in close view, solid geometry with visible
  thickness and underside.
- Fixed the `ramp_geo` call site: the helper now returns a rotation, and the old one-line call was
  unpacking that rotation into the material slot, which aborted every gameplay frame with
  "sequence expected at dimension 1, not 'Material'".
- Verified by vision on the fresh renders: the pit is a genuine sunken recess with a flush exit ramp;
  the platform ramp is one continuous slope with both landings visible and no gap; the pit ramp shows
  real thickness with a solid landing at each end. All 9 frames are byte-verified against the copies
  the dashboard serves at `http://10.0.0.93:8899/file/CommandCenter/outputs/level/<name>`.

> *Psalm 119:105 (ESV) - "Your word is a lamp for my feet, a light on my path."* The camera had to be
> re-aimed at the path that was actually built, not the one we assumed.

### 2026-10-21f - Five X-COM enemies rebuilt, imported into UE 5.8, and the triangle claim retracted

- **Enemy v3 is live.** All five X-COM models rebuilt from scratch and published to the dashboard
  (`CommandCenter/outputs/enemy_models/`): hero shot, turnaround, human-scale reference and a
  shape-only silhouette plate per enemy.
- **The Floater's five descending legs with glowing feet are gone.** The body is now one continuous
  swept manta planform from tip to tip, with a low segmented glowing dorsal core and two hair-fine
  filaments trailing off the rear. Verified two ways: a bottom-up orthographic silhouette render shows
  a single smooth planform, and the mesh's lowest vertex is one centred head pod at z = 0.902 - nothing
  hangs below the body.
- **All five FBX are imported into Unreal Engine 5.8** at `/Game/Enemies/XCOM/`, each verified by
  reloading the saved asset from disk in a separate read-only editor session. Collision is
  `Use Complex as Simple` on all five (written straight to `BodySetup.CollisionTraceFlag` - UE 5.8 has
  no `set_collision_complex_as_simple` helper). Import report:
  `Docs/generated/xcom_ue_import_report.json`.
- **Triangle-count reconciliation - a claim is retracted.** A separate audit re-imported each exported
  FBX into Blender and counted triangles on the raw mesh: the FBX files are complete and match the
  Blender build manifest exactly (Sectoid 7308, Viper 5764, Floater 2184, Muton 5216, Chryssalid 6252).
  UE 5.8's import retains only 39-91% of those triangles. The earlier statement that the imported
  counts "match the Blender manifest exactly" was **wrong** and is retracted. The Blender-side export
  is sound; the reduction happens in UE's import pass (degenerate/duplicate removal on geometry
  assembled from joined primitives). **In-engine visual parity against the approved hero renders is
  still unproven** and is the next gate.
- Disclosed limits from the build lane, carried forward deliberately: the contact shadow is a render
  rig (painted occlusion patch + a 700 W near-vertical spot), not baked geometry, so the engine needs
  its own shadow solution; procedural materials do not survive FBX and need texture bakes; LODs,
  collision meshes and import-ready gameplay assets are out of scope for this pass; the Sectoid's lit
  shoulder caps still read as ball joints at 900 px and the Viper's head/neck still shows a seam.

> *Deuteronomy 25:15 (ESV) - "You shall not have in your bag two differing weights."* One honest scale
> for the models and one for the engine: the numbers had to reconcile before anyone signed off.

### 2026-10-21g - The level finally wears its own materials

- **The level was wearing flat paint.** `Tools/blender/render_level.py` built every material as a flat
  Principled base colour with no image texture node anywhere in the file. Six finished procedural
  albedos - concrete, brick, rusted steel, trim sheet, wood planking - were sitting on disk, and the
  gameplay renders used none of them. Ebert caught it as the highest-leverage fix in the project.
- **Now wired.** All five gameplay materials load their albedo and normal map, projected in WORLD space
  with a box projection so a scaled box never stretches its texture, and the flat grade is multiplied
  over the albedo so the level keeps its deliberately dark grade instead of being washed out by the
  texture. One tile per metre instead of one per 4.5 m, so the grain actually resolves on screen.
- **Verified by looking, not by asserting.** The floor now reads as gritty wet concrete in the render
  (vision check on `level_perspective.png`). The mood is unchanged - still a dark tactical arena, deep
  shadows, localised green and pink light.
- **Honest limit, carried forward:** the low cover blocks, walls and platforms still read as flat
  shapes. That is a LIGHTING gap, not a mapping gap - their vertical faces are unlit, and unlit surface
  shows no material. A level fill-light pass is queued for the next level build, deliberately held
  until Ebert's level verdict is issued so the frames it is scoring are not rewritten underneath it.
- Also fixed: the ramp material lost its assignment during the re-grade and the render died on
  `KeyError: 'ramp'` - caught, repaired, and the full nine-frame set re-rendered clean. Cycles samples
  cut 24 -> 12 with denoising on, taking a nine-frame pass from about seven minutes to under three.
- The enemy manifest now records `weapon_visibility` per enemy. The Viper and Muton weapons are real
  geometry in the FBX but do not read in the published hero render - a rig and framing defect, not
  missing geometry. The manifest no longer implies otherwise.

## 2026-10-21 - UE 5.8 API migration + compute relocation to MAIN

- **Fixed all 45 compile errors** that blocked the UE 5.8 build of `TheCommanderGame`:
  - `CommanderLevelFixValues.h` - 18 bare constants were missing type specifiers (`C4430`); every one is now `inline constexpr double`, which also cleared the cascade of undeclared-identifier errors in the subsystem.
  - `CommanderLevelFixSubsystem.cpp` - `GetLocalBounds()` in 5.8 takes `FVector& Min, FVector& Max` by reference instead of returning a box; call updated.
  - `CommanderPlayerController.cpp` - UE 5.8 API migration: `FInputModeGameOnly` exposes only `SetConsumeCaptureMouseDown` (cursor/mouse-lock moved to `UGameViewportClient`); `UInputSettings::AxisMappings`/`ActionMappings` are private, replaced with `GetAxisMappings()`/`GetActionMappings()`; `FInputKeyEventArgs` now requires the `CreateSimulated` factory; `FTimerManager::SetTimer` now takes a leading `FTimerHandle&`.
- **Upscaler plugin scoping corrected** in `TheCommander.uproject`: FSR, DLSS, StreamlineNGXCommon and XeSS now use `PlatformAllowList: ["Win64"]` (was `TargetAllowList`, which silently excluded them from packaged Win64 builds).
- **Compute relocated**: the build was moved off the Ryzen 5 4500U laptop onto the Ryzen 9 5900X at MAIN (12 cores / 24 threads), per the fleet compute-tier order MAIN -> HTPC -> DECK.
- "Test everything; hold fast what is good" (1 Thessalonians 5:21, ESV) - reason: every 5.8 API break had to be caught and verified against the real engine source before shipping a buildable package.

## [2026-10-22] — Doctrine amendment: the shipped runtime is UE5/C++, not Rust

### Changed
- **`Docs/generated/roster_bible.md` §9 and `Docs/generated/roster_bible.json` now describe a UE5 5.8 / C++ ship runtime** — Commander Gill's standing decision (2026-10-22, "nah, stay with C++ then - adjust specs"). The boundary table's logic column is C++ Unreal module code (damage math, AI state machines, encounter scripting, weapon stats, audio scheduling, taunt selection, difficulty scalars, score); the engine column stays UE5/Blender content (meshes, skeletons, materials, lighting, particles, audio assets).
- **`roster_bible.json` is still the ONLY interface** — reworded for a C++ consumer: the C++ runtime reads the numbers verbatim and a build-time generator emits the C++ stat tables from the JSON, so no value is ever re-typed by hand and the two can never drift.
- **`Docs/generated/roster_bible.json` `engine` / `portability` fields updated** — `engine` now reads "Unreal Engine 5.8 + Blender 4.2.23 (authoring); C++ / UE5 runtime (ship)"; `portability.logic` is "pure C++ (UE5 module code)"; `portability.contract` states the C++ runtime reads the numbers verbatim. Bible version bumped 1.1 → 1.2 (JSON `version`, `amended`, `generated`, and the MD header + Amendment 1.2 line).
- **New `Tools/python/gen_roster_bible.py`** — the generator that owns the boundary doctrine and renders both `roster_bible.md` and `roster_bible.json` from it. It is idempotent, refuses to write while any "rust" runtime wording survives, and `python Tools/python/gen_roster_bible.py --check` fails if either generated file drifts from the doctrine.
- **Linux portability note re-pointed at UE's platform-agnostic APIs** — the WAV read path is now `FFileHelper` / `IFileManager` plus a hand-rolled RIFF parser instead of a Rust `std::fs` reader.

### Verse
> *"Plans fail for lack of counsel, but with many advisers they succeed."* — Proverbs 15:22 (ESV)
> Chosen because this leg is the counsel landing: the Commander heard the options and chose C++, and the specs are now adjusted to match that advice instead of the plan failing for want of it.

## [2026-10-22b] — Standalone Win64 build: compiles, cooks, packages, and boots on AMD with FSR

### Added
- **`Tools/ue/package_and_smoke_win64.bat`** — the repeatable sovereign build lane: builds the standalone game target, cooks, stages, packages, archives, and then **boots the shipped `.exe` and checks it survives first frame**. "It compiles" is not "it plays"; this script proves both in one run and reports a machine-readable verdict (`BOOTED` / `FATAL_VIEWPORT` / `FAIL`) plus `FSR=ENGAGED` and `INPUT_AUDIT=OK`.
- **`Docs/generated/ZERO_TRUST_CONFIG_AUDIT.md`** — 9 findings, every one cited to a real file+line or a real engine log captured on MAIN. Verdict: **PASS WITH ONE FIX APPLIED**.

### Fixed
- **CRITICAL — the packaged standalone build died on the first frame.** XeSS Frame Generation (XeFG) hijacked the D3D12 swap chain and failed to create one: `LogXeFGSDK: Error: Failed to create swap chain: 0x887a0022` (`DXGI_ERROR_NOT_CURRENTLY_AVAILABLE`) → `LogXeFGRHI: Error: Failed to create XeFG swap chain, result: -17` → `LogD3D12RHI: Error: hr failed at WindowsD3D12Viewport.cpp:162` → `Fatal error: Failure creating: D3D12Viewport`.
  - **Not an FSR problem and not GPU-specific.** The same run logged `LogFSR: Successfully initialized FSR Upscaling provider using version '4.1.2 *'` — FSR initialised cleanly *before* the crash. XeFG is the Intel vendor path (`libxell.dll` 1.3.2) and it does not own the swap chain in an AMD-first build.
  - **Fix:** `r.XeFG.OverrideSwapChain=0` in `Config/DefaultEngine.ini` (line 114) — the project-level equivalent of the engine's `-XeFGOverrideSwapChainDisabled` switch, but **baked into the shipped `.exe`** so the crash cannot recur on any machine. XeSS *upscaling* (XeSS 3) is a separate module and is unaffected.
  - **Re-verified by re-packaging and re-smoking with no command-line workaround:** `LogConfig: Set CVar [[r.XeFG.OverrideSwapChain:0]]` → `LogXeFGRHI: Display: Override swap chain: 0` → map loads → clean exit.

### Verified (measured on MAIN — Ryzen 9 5900X, RX 7900 XTX, UE 5.8)
- Editor target compile: **218 actions, 108 s, 0 errors / 0 warnings**. Game target compile: **79.57 s**, `Result: Succeeded`.
- Cook: **543 packages**, 0 errors, 1 warning — and that single warning is the per-node device-profile gate *working as designed* (`r.Shadow.MaxCSMResolution` set by `SetByScalability` is correctly outranked by `SetByProjectSetting`).
- Package: **`BUILD SUCCESSFUL`**, `AutomationTool exiting with ExitCode=0`, 1.5 GB archive, 34.85 s `BuildCookRun`.
- Shipped `.exe` boots: `LoadMap: /Game/Maps/M_Blockout01` → `ACommanderGameMode::InitGame map=M_Blockout01 controller=CommanderPlayerController pawn=CommanderCharacter` → `PlayerController ... ready` → `Engine is initialized` → clean exit.
- **FSR is live on AMD: `LogFSR: Successfully initialized FSR Upscaling provider using version '4.1.2 *'`.** The UE plugin stays pinned at 4.1.1; **4.1.2 comes from the Adrenalin driver (26.10.1)** — driver-side, exactly as the FSR research concluded. **No 4.1.2 plugin pin added.**
- **The `-CommanderInputAudit` harness is WORKING, not broken** — it prints map, game mode, controller, pawn, `PlayerInput`, `InputComponent`, `PlayerStart` (`V(Y=-1500.00, Z=100.00)`), pawn location/rotation/velocity, plus all 8 axis and 5 action mappings, live in the packaged build. It fires on the tick *after* map load, so a harness that quits inside the same `ExecCmds` block exits before the audit prints.
- All three upscaler families compile and link: `FFXFSRApi`, `FFXFSRSettings`, `FFXFSRTemporalUpscaling` (FSR) plus the DLSS, XeSS and `StreamlineNGXCommon` modules. FSR primary; DLSS and XeSS retained for compatibility.
- The runtime level-fix subsystem executes correctly **in the packaged build**, not just the editor: 12 changes applied (pit rim × 5, ramp, pillar ledges × 3, cover blocks × 2, keycard beacon).

### Corrected
- The first `BUILD_EXIT=6` was **not** a bad target name — `TheCommanderGameEditor` is a real target (`Source/TheCommanderGameEditor.Target.cs`). The actual cause was `Unable to find plugin 'FSR' (referenced via TheCommander.uproject)`, because `Plugins/` is gitignored and a fresh clone carries no plugin payload. Provision with `python Tools/ue/fetch_upscaler_plugins.py` (SHA-256 verified, 0 downloads from a warm cache). A UBT exit code is not a diagnosis; the message above it is.

## [2026-10-22c] — Validation matrix: MAIN ✅, LAPTOP ✅, STEAM DECK ❌ (wrong artefact)

### Verified
- **MAIN (RX 7900 XTX, D3D12/SM6)** — boots, map loads, FSR 4.1.2 live, 16 input bindings, clean exit. *(unchanged from 2026-10-22b)*
- **LAPTOP (integrated AMD Radeon, no discrete GPU)** — **PASS**. The iGPU reports **Feature Level 12_1 / shader model 6.7** (binding tier 3, wave ops, atomic64), and the RHI makes the correct call: `LogRHI: RHI D3D12 with Feature Level SM6 is supported and will be used.` Map loads, `ACommanderGameMode::InitGame` → player spawned → `PlayerController ready`, FSR swapchain provider registered, DLSS correctly skipped (`kFeatureDLSS_G` — no NVIDIA GPU), **zero fatals**, clean exit. The XeFG fix is not MAIN-specific.

### Known gap (every target)
- **CORRECTED 2026-10-22:** this entry originally claimed the package ships no PSO cache and that
  this cost ~187 s on the laptop. **Both halves were wrong.** UE 5.8 already ships and loads the
  global shader library (8239 unique shaders, confirmed in the log), and the shipped build reaches
  playable — engine initialized, FSR live, input audit complete — in **11.1 s** on the laptop's CPU
  iGPU. The 187 s figure was the whole process lifetime, dominated by teardown after
  `ExecCmds="quit"` fired during init. The new build is **not** faster; the old measurement was
  wrong.

### Steam Deck — verdict
- 1.5 GB package transferred to `/home/deck/AI/TheCommander_Win64`; RDNA 2 Vulkan/RADV live; `Proton 11.0` and `GE-Proton7-28` present; X/Wayland solved (`DISPLAY=:0`, `WAYLAND_DISPLAY=wayland-0`, `XAUTHORITY=/run/user/1000/xauth_iabMRX`).
- **Three blockers, and the third is decisive:** (1) Proton 11.0-100 fails to build a fresh prefix — `Error while copying to ".../drive_c/windows/system32/amdxcffx64.dll": No such file or directory`; (2) the Deck has **~1,360 MB available with 4,866 MB already swapped** (llama-server holds 1.0 GB RSS); (3) **this artefact is D3D12**, and UE5 under Proton means **vkd3d-proton** — an experimental, unsupported path for UE5.
- **Therefore the Windows D3D12 build is not the Steam Deck deliverable.** The Deck needs a **native Linux/Vulkan build** of the same C++ project. That requires the UE 5.8 **Linux** engine (Epic login — a Commander action) and a Linux box with RAM headroom (killing the Deck inference window — a Commander action under window-owns-inference). The Linux cook/package/ship/verify half is fully Hermes-autonomous once those clear.

### Verse
> *"Do not love money or silver or gold or fine clothing or luxury clothing; but pursue righteousness and faithfulness and love, with the accompanying gifts of humility, righteousness, faith, and self-control."* — 1 Timothy 6:11–12 (ESV)
> Chosen because this leg is the discipline of wanting the right thing rather than the impressive thing: a Windows build that runs beautifully on a 7900 XTX and a 4500U iGPU is still the wrong artefact for a Steam Deck, and the honest move is to say so plainly rather than keep polishing a package the target hardware was never going to run. "Pursue righteousness and faithfulness and love" is the discipline of following the mission — Linux/Vulkan on the Deck — instead of the comfortable path.

## [2026-10-22d] — Correction: the "187 s startup" was a measurement error; the build lane now bounds its own smoke test

### Corrected
- **The "~187 s to start, fixed by shipping a PSO cache" claim was wrong, and it was mine.** Both the
  old and the new build load the same cooked global shader library (`Using IoDispatcher for shader
  code library Global. Total 8239 unique shaders`) and both miss exactly **16** PSOs at runtime.
  Measured like for like on the laptop's integrated AMD Radeon:
  - OLD build: launch → engine initialized **10.2 s**
  - NEW build: launch → engine initialized **9.7 s** · → FSR provider 10.3 s · → input audit complete 11.1 s
  - The 187 s was the **whole process lifetime**, dominated by ~3 minutes of **teardown** after
    `ExecCmds="quit"` fired during initialisation — and that quit also meant the input audit never
    printed, so the old run could not be compared on the same metric at all.
- **What the new config actually does:** `r.ShaderPipelineCache.Enabled=1` and
  `bShareMaterialShaderCode=True` make UE 5.8's existing shader-library behaviour **explicit and
  pinned** instead of dependent on an engine default, and `r.ShaderPipelineCache.ReportPSO=1` adds
  the PSO telemetry that made this correction measurable. It is **not** a 9x speedup and is not
  claimed as one.
- **FSR version is driver-dependent, not build-dependent:** the laptop reports provider **3.1.5**
  (older AMD driver), MAIN reports **4.1.2** (Adrenalin 26.10.1). The project supports FSR 3 and
  FSR 4; the number printed at runtime is the driver's, which is correct.

### Fixed
- **`Tools/ue/package_and_smoke_win64.bat` hung on its own smoke test.** The shipped `.exe` does not
  self-exit — the input audit is emitted once and the game keeps running — so the lane blocked
  forever on the process. The smoke step now starts the `.exe`, polls the log for
  `COMMANDER INPUT AUDIT END` (or `Fatal error`) with a **240 s bound**, then stops it. The verdict
  is still read from the log, never from the exit code.
- **The lane will never kill a game the Commander is playing.** If a `TheCommanderGame.exe` instance
  is already running, the smoke step prints `[SKIP]` and exits `RESULT: SKIPPED` without touching it.

### Verified
- MAIN, full lane, HEAD 57524ca: **build exit 0 · package exit 0 · `BUILD SUCCESSFUL` / `ExitCode=0`
  · boot verdict BOOTED · FSR provider ENGAGED · input audit OK · RESULT: PASS · LANE_EXIT=0**.
- Package carries the shader archives: `Save IoStoreShaderCodeArchive 'Global-PCD3D_SM6-PCD3D_SM6'`,
  `Save IoStoreShaderCodeArchive 'TheCommander-PCD3D_SM6-PCD3D_SM6'`, `63.07 MiB for 967 Global shaders`.
- Shipped `.exe` on MAIN: `Loaded Shared Shader Library Global — 8239 unique shaders`,
  `Loaded Shared Shader Library TheCommander — 2113 unique shaders`, `ShaderPipelineCache: Batching
  Resumed`, **no fatals**.
- Shipped `.exe` on the laptop: engine initialized, FSR live, input audit END, **no fatals**, ~10 s
  to playable.

### Verse
> *"The heart of the righteous studies to answer."* — Proverbs 24:23 (ESV)
> Chosen because this leg was exactly a wrong answer that had to be caught: a 187 s startup figure was
> published, then a 20 s figure was published as the fix, and only measuring both logs on the same
> metric showed that the first number measured teardown and the second measured nothing new.
> "Studies to answer" is the discipline of going back to the evidence and answering with what the
> evidence actually says — even when the honest answer retracts two of my own claims.

## [2026-10-22e] — Steam Deck: the game BOOTS under Proton; the blocker is a missing PSO cache, not the build

### The result
- **Correcting my own earlier claim: Proton IS installed on the Deck** — Experimental (11.0-100), 11.0,
  8.0, Hotfix, 7.0, plus **GE-Proton7-28** in `compatibilitytools.d`. My earlier probe looked in the
  wrong path and concluded "Proton not installed". The Deck also already holds the **fixed** build
  (`TheCommanderGame.exe` sha256 `ba51d650993ea82b`, byte-identical to the laptop's).
- **The `Proton 11.0-100` prefix failure is fixable.** `Error while copying to
  ".../drive_c/windows/system32/amdxcffx64.dll"` is a prefix-ordering bug — Proton copies that driver
  DLL before `drive_c/windows/system32` exists. **Pre-creating `pfx/drive_c/windows/system32` and
  `syswow64` before the first run makes the prefix build cleanly** (374 MB, no error).
- **GE-Proton7-28 takes the game to full gameplay state on the Deck:**
  - `RHI D3D12 with Feature Level SM6 is supported and will be used` (vkd3d-proton 2.6.0, build d00d035321c9f81)
  - `LogXeFGRHI: Display: Override swap chain: 0` → **the XeFG crash fix holds on the Deck too**
  - `LogFSR: Successfully initialized FSR Upscaling provider using version '3.1.5'`
  - `LogFFXFI: Successfully initialized FSR FrameInterpolation using version '3.1.6'`
  - `LogLoad: LoadMap: /Game/Maps/M_Blockout01` · `ACommanderGameMode::InitGame` ·
    `CommanderPlayerController ready: pawn=CommanderCharacter playerinput=EnhancedPlayerInput`
  - Full input audit: WASD **and** gamepad axis mappings, Fire / Jump / Dash action bindings,
    pawn at `V(Y=-1500.00, Z=90.15)`
  - DLSS correctly skipped (no NVIDIA); Streamline correctly unsupported for D3D12
- **Then it dies:** `Fatal error: [D3D12Util.cpp:1062] hr failed at D3D12CommandList.cpp:244 with
  error E_INVALIDARG`, ~0.5 s after `Encountered a new graphics PSO: 2110166719 (PSOPrecacheState: Missed)`.

### Root cause — single and precise
- **The package ships no PSO cache.** `Could not open FPipelineCacheFile:
  ../../../TheCommander/Content/PipelineCaches/Windows/TheCommander_PCD3D_SM6.stable.upipelinecache`
  on every target; **no `.upipelinecache` exists anywhere** on MAIN or the laptop.
- **14-15 PSOs are created at runtime on every target — the same set everywhere** (MAIN 15, Deck 13 of
  them before it died): 4026005998, 265281650, 1998208102, 2110166719, 1252366740, 45228890, 3228235678,
  3372292158, 1148996969, 1818476037, 4012981560, 1440837915, 544261722, 3809084492.
- Native D3D12 (MAIN, laptop) creates them fine → the game plays. **vkd3d-proton cannot create them →
  E_INVALIDARG → crash.** A vkd3d-proton capability gap, not a defect in our code.
- **Therefore "ship a PSO cache" was never a no-op.** My `[2026-10-22d]` correction was right about the
  **shader library** (8239 shaders, already cooked, already loaded — that part was genuinely a no-op)
  and wrong to generalise it to the **PSO cache**, which is a *different artifact* and **is** absent.
  On native D3D12 that absence costs 15 runtime compiles; on the Deck's vkd3d it is fatal.

### Proton version matrix (Deck, this build)
| Proton | Result |
|---|---|
| Experimental 11.0-100 | prefix created; D3D12 SM6 up; **Vulkan device lost (`VK_ERROR_DEVICE_LOST`)** ~49 s in |
| **GE-Proton7-28** | **map loaded, player spawned, input audit running → E_INVALIDARG on the first runtime PSO** |
| 11.0 / 8.0 / 7.0 / Hotfix | installed, not yet tried |

### Next leg — one cause, one fix
1. Make the game **exit gracefully** after the input audit so UE writes
   `Saved/PipelineCaches/Windows/TheCommander_PCD3D_SM6.stable.upipelinecache`. A forced kill writes
   nothing, which is why no cache has ever existed here. Small C++ change, rebuild on MAIN.
2. Ship that file in the package at `TheCommander/Content/PipelineCaches/Windows/`.
3. Re-run on the Deck — the 14 PSOs load from cache instead of being created at runtime, so vkd3d
   never has to create them.
4. Fallback if that is not enough: **native Linux/Vulkan build** (still needs the UE 5.8 Linux engine
   = Epic login, the one Commander action I cannot do).

### Verse
> *"Let all things be done decently and in order."* — 1 Corinthians 14:40 (ESV)
> Chosen because this leg was a chain of failures that had to be put in order before anything could be
> trusted: Proton "not installed" (wrong — it was installed, I probed the wrong path), a prefix bug (a
> directory that has to exist before Proton copies a DLL into it), a Vulkan device loss, and then the
> real cause sitting underneath all of it — 14 PSOs that must exist before the game can draw a frame
> on the Deck. Nothing here worked by brute force; it worked because the failures were separated,
> named, and put in order.
