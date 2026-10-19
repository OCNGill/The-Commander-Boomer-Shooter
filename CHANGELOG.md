# CHANGELOG — The Commander Boomer Shooter

*"For we are his workmanship, created in Christ Jesus for good works, which God prepared beforehand, that we should walk in them."* — Ephesians 2:10

---

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
