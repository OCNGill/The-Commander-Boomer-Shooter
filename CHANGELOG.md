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
