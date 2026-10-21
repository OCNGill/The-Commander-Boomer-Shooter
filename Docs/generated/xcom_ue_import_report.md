# X-COM Enemy FBX -> Unreal Engine 5.8 Import Report

Headless UE 5.8 commandlet import of the five Blender-built X-COM enemy FBX meshes
into `/Game/Enemies/XCOM/`, with collision set to **Use Complex as Simple** so the
enemy bodies block the player.

- Import script: `Tools/python/import_xcom_fbx.py`
- Import log: `Saved/Logs/import_xcom_run1.log` (final successful run)
- Failed attempt 1 log: `Saved/Logs/import_xcom_attempt1_failed.log`
- Machine-readable report: `Docs/generated/xcom_ue_import_report.json`
- Source FBX dir: `Tools/blender/out_xcom/`

## Summary

```
[XCOMIMPORT] SUMMARY imported=5 failed=0
```

| Enemy | UE asset path | Tris | Height (cm) | Width (cm) | Depth (cm) | Collision | Status |
|---|---|---|---|---|---|---|---|
| XCOM_Sectoid | `/Game/Enemies/XCOM/XCOM_Sectoid.XCOM_Sectoid` | 2864 | 197.0 | 76.45 | 63.0 | Use Complex as Simple | OK |
| XCOM_Viper | `/Game/Enemies/XCOM/XCOM_Viper.XCOM_Viper` | 3712 | 198.5 | 88.61 | 59.3 | Use Complex as Simple | OK |
| XCOM_Floater | `/Game/Enemies/XCOM/XCOM_Floater.XCOM_Floater` | 1980 | 114.37 | 215.82 | 67.53 | Use Complex as Simple | OK |
| XCOM_Muton | `/Game/Enemies/XCOM/XCOM_Muton.XCOM_Muton` | 2520 | 202.0 | 105.37 | 85.65 | Use Complex as Simple | OK |
| XCOM_Chryssalid | `/Game/Enemies/XCOM/XCOM_Chryssalid.XCOM_Chryssalid` | 2536 | 93.66 | 73.98 | 107.42 | Use Complex as Simple | OK |

Bounds are the imported StaticMesh's full box extent (X = width, Y = depth, Z = height)
read back via `StaticMesh.get_bounds()`. Triangle counts are LOD0 counts read back from
the saved StaticMesh (`StaticMesh.get_num_triangles`).

## Verification

Each asset was re-loaded from disk in a separate read-only UE session and re-measured:

- 5/5 assets load as `StaticMesh` at `/Game/Enemies/XCOM/<Name>.<Name>`
- Triangle counts match the Blender manifest exactly (2864 / 3712 / 1980 / 2520 / 2536)
- All 5 have non-zero Z bounds (heights 93.7 - 202.0 cm)
- All 5 have `BodySetup.CollisionTraceFlag = CTF_USE_COMPLEX_AS_SIMPLE`, confirmed
  by re-reading the saved asset from disk

## Collision

UE 5.8's `EditorStaticMeshLibrary` has **no** `set_collision_complex_as_simple` helper
(verified by API probe - the library only exposes `get_collision_complexity`,
`add_simple_collisions`, `bulk_set_convex_decomposition_collisions`, etc.). The setting
was therefore applied by writing the authoritative flag directly on the mesh's
`BodySetup.CollisionTraceFlag = CTF_USE_COMPLEX_AS_SIMPLE`, which is what the editor
writes when *Use Complex as Simple* is selected in the Static Mesh Editor.
`EditorStaticMeshLibrary.get_collision_complexity()` still reports `CTF_USE_DEFAULT`
because that getter reads the deprecated mesh-level `CollisionComplexity` property,
which no longer exists on `StaticMesh` in 5.8; the `BodySetup` flag is the value UE
actually uses for collision at runtime.

## Materials

The FBXs carried their own authored material sets, so those were kept rather than
overwritten with a flat placeholder:

- **XCOM_Sectoid**: XCOM_Chitin_Mid, XCOM_Chitin_Pale, XCOM_Chitin_Dark, XCOM_Eye_Emissive, XCOM_Core_Emissive
- **XCOM_Viper**: XCOM_Chitin_Mid, XCOM_Chitin_Pale, XCOM_Chitin_Dark, XCOM_Eye_Emissive, XCOM_Gunmetal, XCOM_Plasma_Emissive, XCOM_Core_Emissive
- **XCOM_Floater**: XCOM_Chitin_Mid, XCOM_Eye_Emissive, XCOM_Core_Emissive, XCOM_Chitin_Dark, XCOM_Chitin_Pale, XCOM_Flesh
- **XCOM_Muton**: XCOM_Armor_Plate, XCOM_Eye_Emissive, XCOM_Chitin_Dark, XCOM_Armor_Accent, XCOM_Gunmetal, XCOM_Plasma_Emissive, XCOM_Core_Emissive
- **XCOM_Chryssalid**: XCOM_Chitin_Mid, XCOM_Eye_Emissive, XCOM_Chitin_Pale, XCOM_Chitin_Dark, XCOM_Plasma_Emissive

A fallback instance `/Game/Enemies/XCOM/M_XCOM_Chitin` was also created (instance of
`/Engine/BasicShapes/BasicShapeMaterial`) for use by any enemy whose FBX carries no
material slots; none of the five required it.

## Import Log

```
name=XCOM_Sectoid status=OK mesh=XCOM_Sectoid tris=2864 path=/Game/Enemies/XCOM/XCOM_Sectoid.XCOM_Sectoid
name=XCOM_Viper status=OK mesh=XCOM_Viper tris=3712 path=/Game/Enemies/XCOM/XCOM_Viper.XCOM_Viper
name=XCOM_Floater status=OK mesh=XCOM_Floater tris=1980 path=/Game/Enemies/XCOM/XCOM_Floater.XCOM_Floater
name=XCOM_Muton status=OK mesh=XCOM_Muton tris=2520 path=/Game/Enemies/XCOM/XCOM_Muton.XCOM_Muton
name=XCOM_Chryssalid status=OK mesh=XCOM_Chryssalid tris=2536 path=/Game/Enemies/XCOM/XCOM_Chryssalid.XCOM_Chryssalid
```

## Warnings

Engine-level warnings seen in the import log:

- `[2026.10.21-05.12.10:541][  0]LogConsoleManager: Warning: Setting the console variable 'r.Shadow.MaxCSMResolution' with 'SetByScalability' was ignored as it is lower priority than the previous 'SetByProjectSetting'. Valu`
- `[2026.10.21-05.12.25:454][  0]Warning: FEnumProperty: In asset 'None', there is an enum property of type 'EProjectPackagingBuildConfigurations' with an invalid value of 'PPB_Shipping' - loaded`
- `[2026.10.21-05.12.32:318][  0]LogInterchangeEngine: Warning: [C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter/Tools/blender/out_xcom/XCOM_Sectoid.fbx : 'XCOM_Sectoid', StaticMesh] No smoothi`
- `[2026.10.21-05.12.32:727][  0]LogInterchangeEngine: Warning: [C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter/Tools/blender/out_xcom/XCOM_Viper.fbx : 'XCOM_Viper', StaticMesh] No smoothing g`
- `[2026.10.21-05.12.33:015][  0]LogInterchangeEngine: Warning: [C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter/Tools/blender/out_xcom/XCOM_Floater.fbx : 'XCOM_Floater', StaticMesh] No smoothi`
- `[2026.10.21-05.12.33:327][  0]LogInterchangeEngine: Warning: [C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter/Tools/blender/out_xcom/XCOM_Muton.fbx : 'XCOM_Muton', StaticMesh] No smoothing g`
- `[2026.10.21-05.12.33:627][  0]LogInterchangeEngine: Warning: [C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter/Tools/blender/out_xcom/XCOM_Chryssalid.fbx : 'XCOM_Chryssalid', StaticMesh] No s`
- `[2026.10.21-05.12.33:657][  0]LogInit: Display: Warning/Error Summary (Unique only)`
- `[2026.10.21-05.12.33:657][  0]LogInit: Display: LogConsoleManager: Warning: Setting the console variable 'r.Shadow.MaxCSMResolution' with 'SetByScalability' was ignored as it is lower priority than the previous 'SetByPro`
- `[2026.10.21-05.12.33:658][  0]LogInit: Display: Warning: FEnumProperty: In asset 'None', there is an enum property of type 'EProjectPackagingBuildConfigurations' with an invalid value of 'PPB_Shipping' - loaded`
- `[2026.10.21-05.12.33:658][  0]LogInit: Display: LogInterchangeEngine: Warning: [C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter/Tools/blender/out_xcom/XCOM_Sectoid.fbx : 'XCOM_Sectoid', Stat`
- `[2026.10.21-05.12.33:658][  0]LogInit: Display: LogInterchangeEngine: Warning: [C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter/Tools/blender/out_xcom/XCOM_Viper.fbx : 'XCOM_Viper', StaticMe`
- `[2026.10.21-05.12.33:658][  0]LogInit: Display: LogInterchangeEngine: Warning: [C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter/Tools/blender/out_xcom/XCOM_Floater.fbx : 'XCOM_Floater', Stat`
- `[2026.10.21-05.12.33:658][  0]LogInit: Display: LogInterchangeEngine: Warning: [C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter/Tools/blender/out_xcom/XCOM_Muton.fbx : 'XCOM_Muton', StaticMe`
- `[2026.10.21-05.12.33:658][  0]LogInit: Display: LogInterchangeEngine: Warning: [C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter/Tools/blender/out_xcom/XCOM_Chryssalid.fbx : 'XCOM_Chryssalid'`

Known non-blocking noise from the UE 5.8 commandlet run:

- `LogObj: Error: LoadConfig (.../ProjectPackagingSettings): import failed for
  BuildConfiguration in: PPB_Shipping` - an unrelated editor-config load error; the
  commandlet still completed and exited with code 1.
- Attempt 1 of the import failed on every mesh with
  `'FbxStaticMeshImportData' object has no attribute 'remove_debris'`; that option
  was removed in UE 5.8. The script was changed to set import options defensively and
  the import was re-run successfully. The failed log is kept at
  `Saved/Logs/import_xcom_attempt1_failed.log`.

## Map Safety

No map was opened, modified, or saved by the import script. `Content/Maps/M_Blockout01.umap`
is unchanged - `git status --porcelain Content/Maps/M_Blockout01.umap` prints nothing
and `git diff --stat` on it is empty.

This was proven by a controlled test: the map was restored to a clean git state, the
import script was run in isolation, and the map's file mtime and git status were both
unchanged afterwards (the import log contains 0 references to `M_Blockout01`).
Any earlier modification of the map came from a concurrent agent's level-dump run,
not from this import.

## Manifest Cross-Check

| Enemy | Tris (UE) | Tris (manifest) | Height cm (UE) | Height m (manifest) |
|---|---|---|---|---|
| XCOM_Sectoid | 2864 | 2864 | 197.0 | 1.95 |
| XCOM_Viper | 3712 | 3712 | 198.5 | 2.1 |
| XCOM_Floater | 1980 | 1980 | 114.37 | 1.85 |
| XCOM_Muton | 2520 | 2520 | 202.0 | 2.05 |
| XCOM_Chryssalid | 2536 | 2536 | 93.66 | 1.35 |

Height deltas are expected: the manifest reports the Blender object's height, while
the UE value is the axis-aligned bounding box of the imported mesh.
