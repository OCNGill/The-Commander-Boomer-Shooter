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
