# TASK-07 — UE5 Import Pipeline Spec (X-COM Enemy FBX Kit)

**Slot:** swarm-w2 · **Target:** Unreal Engine **5.8** (`TheCommander.uproject` → `"EngineAssociation": "5.8"`)
**Proven API baseline:** `Tools/python/import_xcom_fbx.py` (5/5 import, `[XCOMIMPORT] SUMMARY imported=5 failed=0`),
`Tools/python/ensure_base_geometry.py` and `Tools/python/populate_encounters.py` (proven spawn path).
**Design locks:** TRUE 3D only, NO sprites · original 1994 X-COM roster only · zero reload animations ·
pickups are the only health system, no regeneration.

---

## 1. Source-of-truth inventory (what exists today)

| Path | What it is | State |
|---|---|---|
| `Tools/blender/xcom_enemies.py` | v1 builder (5 enemies, flat Principled materials) | superseded, still present |
| `Tools/blender/xcom_enemies_v2.py` | **v2/v3 builder** (per-enemy procedural materials, 7 families, reveal rig) | current source of the FBX on disk |
| `Tools/blender/out_xcom/XCOM_<Enemy>.fbx` | 5 binary FBX, one joined mesh per enemy, Y-up / −Z-forward, `FBX_SCALE_ALL`, no textures, no rig, no LOD | rebuilt 2026-10-21 02:47–02:51 |
| `Tools/blender/out_xcom/xcom_manifest.json` | tris / kb / dims / silhouette / emissive pixel stats | v3 values (5636/5764/2732/5216/6252) |
| `Tools/python/import_xcom_fbx.py` | the working UE 5.8 FBX importer | proven 5/5 |
| `Tools/python/ensure_base_geometry.py` | the **proven spawn path** | `spawn_actor_from_class` + `set_static_mesh` |
| `Tools/python/populate_encounters.py` | encounter/pickup/weapon placement + lighting beats | uses the same proven path |
| `Content/Enemies/XCOM/*.uasset` | 5 static meshes + 11 materials from the **v1** import | **one generation stale** — see §1.1 |
| `CommandCenter/outputs/ue_import/xcom_ue_import_report.md` | the v1 import report (prose + tables) | the model for the new report |

### 1.1 KNOWN STALENESS — must be handled by this pipeline, not ignored

`Content/Enemies/XCOM/XCOM_Sectoid.uasset` etc. were imported at **01:13** from the **v1** FBX (2864 tris,
`XCOM_Chitin_Mid` material family). The FBX were rebuilt at **02:47–02:51** with the v3 builder (5636 tris,
`XCOM_Sectoid_CHITIN` material family). Consequences the pipeline must own:

1. Re-importing **replaces** the mesh assets (same `destination_name`, `replace_existing=True`) — fine.
2. The **v1 material assets** (`XCOM_Chitin_Dark/Mid/Pale`, `XCOM_Armor_Plate`, `XCOM_Armor_Accent`,
   `XCOM_Flesh`, `XCOM_Eye_Emissive`, `XCOM_Core_Emissive`, `XCOM_Plasma_Emissive`, `XCOM_Gunmetal`,
   `M_XCOM_Chitin`) are **orphans** — the new FBX reference a different material scheme. They should be deleted
   by the owner of `Content/**` (locked for this slot — **reported, not edited**).
3. `M_XCOM_Chitin` (an instance of `/Engine/BasicShapes/BasicShapeMaterial`) is a **placeholder** and must not
   remain the fallback for any enemy.

---

## 2. Naming convention

### 2.1 Blender side (source files)

| Element | Pattern | Example |
|---|---|---|
| Enemy FBX | `XCOM_<PascalEnemy>.fbx` | `XCOM_Sectoid.fbx` |
| Blender object / mesh | `XCOM_<PascalEnemy>` | `XCOM_Chryssalid` |
| Blender material | `XCOM_<PascalEnemy>_<FAMILY>` | `XCOM_Muton_PLATE_OXBLOOD` |
| Manifest | `xcom_manifest.json` (one entry per enemy, `name` = asset name) | — |
| Preview renders | `XCOM_<PascalEnemy>.png`, `_turn.png`, `_scale.png`, `_silh.png` | — |

`<PascalEnemy>` ∈ `Sectoid, Viper, Floater, Muton, Chryssalid`.
`<FAMILY>` ∈ `CHITIN, PLATE, PLATE_DARK, PLATE_OXBLOOD, CHITIN_BONE, ACCENT_EMISSIVE, ACCENT_DIM`.

**Rules:** uppercase, no spaces, no dashes, underscores only between words. The FBX stem **must** equal the UE
asset name — the importer derives the destination name from the stem and the report is keyed on it.

### 2.2 UE side (assets)

| Asset | Path | Name pattern | Example |
|---|---|---|---|
| Static mesh (LOD0) | `/Game/Enemies/XCOM` | `XCOM_<PascalEnemy>` | `/Game/Enemies/XCOM/XCOM_Sectoid.XCOM_Sectoid` |
| Master material | `/Game/Enemies/XCOM/Materials/Masters` | `M_XCOM_<FAMILY>_Master` | `M_XCOM_Chitin_Master` |
| Material instance | `/Game/Enemies/XCOM/Materials/Instances` | `MI_XCOM_<PascalEnemy>_<FAMILY>` | `MI_XCOM_Muton_PLATE_OXBLOOD` |
| Texture (optional baked) | `/Game/Enemies/XCOM/Textures` | `T_XCOM_<FAMILY>_<Map>` | `T_XCOM_Chitin_Normal` |
| Blueprint actor (future) | `/Game/Enemies/XCOM/Blueprints` | `BP_XCOM_<PascalEnemy>` | `BP_XCOM_Viper` |
| Spawned actor label | in-level | `XCOM_<PascalEnemy>_<nn>` | `XCOM_Sectoid_03` |

**Why `MI_` / `M_` / `T_` prefixes are new:** the existing v1 import wrote raw FBX material names straight into
`/Game/Enemies/XCOM` (`XCOM_Chitin_Mid.uasset` etc.), so assets, materials and the future baked textures all share
one flat namespace. The new scheme separates them. The migration is additive: masters/instances go into
**subfolders**, so the flat folder keeps only the five mesh assets and can be cleaned in one pass.

### 2.3 Folder/asset path convention (final tree)

```
/Game/Enemies/XCOM/
├── XCOM_Sectoid.uasset        (StaticMesh, LOD0, collision = ComplexAsSimple)
├── XCOM_Viper.uasset
├── XCOM_Floater.uasset
├── XCOM_Muton.uasset
├── XCOM_Chryssalid.uasset
├── Materials/
│   ├── Masters/
│   │   ├── M_XCOM_Chitin_Master.uasset
│   │   ├── M_XCOM_Plate_Master.uasset
│   │   ├── M_XCOM_PlateDark_Master.uasset
│   │   ├── M_XCOM_Oxblood_Master.uasset
│   │   ├── M_XCOM_Bone_Master.uasset
│   │   ├── M_XCOM_Accent_Master.uasset
│   │   └── M_XCOM_AccentDim_Master.uasset
│   └── Instances/
│       ├── MI_XCOM_Sectoid_CHITIN.uasset ... (24 instances total, one per FBX slot)
├── Textures/                  (optional baked set, per TASK-02 §2.3)
└── Blueprints/                (BP_XCOM_<Enemy>, when the AI actor is built)
```

Other kit folders that already exist and must not be disturbed: `/Game/Weapons` (blockout proxies + pickups,
imported by `import_weapons_fbx.py` into the **flat** `/Game/Weapons` with no subfolders — the enemy kit does
**not** apply the subfolder scheme there; consistency is per-kit, not global).

---

## 3. Import pipeline — the five stages

### Stage 0 — preflight (pure Python, no UE)

Read `Tools/blender/out_xcom/xcom_manifest.json` and assert for each of the five enemies:
`tris ≤ LOD0 ceiling` (TASK-02 §1), `fbx` file exists, `height_m > 0`.
Cross-check the FBX binary for: `Texture`=0 and `Video`=0 (so `import_textures=False` is correct),
`Deformer`=0 (so `import_as_skeletal=False` is correct), `Model::LOD`=0 (so LODs must be built in UE).
**Fail the import if the manifest and the FBX disagree** — the v1 import had exactly this class of drift
(manifest tris matched the old FBX, and the on-disk FBX were newer).

### Stage 1 — FBX → StaticMesh (per enemy)

```python
task = unreal.AssetImportTask()
task.filename         = os.path.join(FBX_DIR, name + '.fbx')
task.destination_path = '/Game/Enemies/XCOM'
task.destination_name = name
task.replace_existing = True
task.save             = True
task.automated        = True

options = unreal.FbxImportUI()
def sset(obj, prop, val):          # defensive: property may not exist in this build
    try:
        obj.set_editor_property(prop, val); return True
    except Exception:
        return False

sset(options, 'import_mesh', True)
sset(options, 'import_as_skeletal', False)
sset(options, 'import_materials', True)
sset(options, 'import_textures', False)
sset(options, 'import_animations', False)
smi = options.get_editor_property('static_mesh_import_data')
sset(smi, 'combine_meshes', True)
sset(smi, 'generate_lightmap_u_vs', False)
sset(smi, 'auto_generate_collision', False)
sset(smi, 'convert_scene', True)
sset(smi, 'remove_debris', True)   # REMOVED in UE 5.8 -> sset swallows the failure
sset(options, 'static_mesh_import_data', smi)   # write the mutated struct back
task.options = options
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
```

**Import-option rationale (all proven in the working v1 run):**
- `convert_scene=True` — Blender is Y-up / −Z-forward; UE is Z-up / +X-forward. Without it the enemies land
  on their side. `axis_forward='-Z', axis_up='Y'` is already baked into the FBX export.
- `combine_meshes=True` — each enemy is already one joined mesh; this just guarantees a single StaticMesh.
- `generate_lightmap_u_vs=False` — characters are not lightmapped; the reveal is dynamic.
- `auto_generate_collision=False` — collision is authored explicitly in Stage 3.
- `import_textures=False` — there are no textures in the FBX.
- **Every option goes through `sset`.** Attempt 1 of the real import failed on all five meshes with
  `'FbxStaticMeshImportData' object has no attribute 'remove_debris'`. Never assume a property exists.

After import, resolve the mesh: prefer the `StaticMesh` among `task.imported_object_paths`; fall back to loading
`'%s/%s.%s' % (DEST, name, name)`. Both paths are in `import_xcom_fbx.py:272-296`.

### Stage 2 — materials (masters → instances → re-point slots)

1. **Create the 7 masters** (once, idempotent). Each master is a `unreal.Material` whose graph reproduces the
   Blender procedural chain (TASK-02 §2.2): `Noise→ColorRamp→BaseColor`, `Noise→Bump→Normal`,
   `Noise→ColorRamp→Roughness`, plus `EmissiveColor`/`EmissiveStrength` on the accent masters.
2. **Create ≤ 24 instances**, one per (enemy, FBX slot) pair, named `MI_XCOM_<Enemy>_<FAMILY>`:
   ```python
   f = unreal.MaterialInstanceConstantFactoryNew()
   f.set_editor_property('initial_parent', master)
   asset = tools.create_asset(inst_name, '/Game/Enemies/XCOM/Materials/Instances',
                              unreal.MaterialInstanceConstant, f)
   ```
   then set the vector/scalar parameters (`BaseColor`, `Roughness`, `Metallic`, `EmissiveColor`,
   `EmissiveStrength`, `NormalStrength`) with
   `unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value` /
   `..._scalar_parameter_value`, and finally `unreal.EditorAssetLibrary.save_asset(path)`.
   *(`set_material_instance_vector_parameter_value` is the call already proven at `import_xcom_fbx.py:157`.)*
3. **Re-point the mesh slots** with `mesh.set_material(i, mi)` for each slot index, where `mi` is the instance
   matching the FBX slot's material name. This is the proven call at `import_xcom_fbx.py:171-188`.
   **Keep the FBX-authored material set** — do not blanket-assign one material to every slot. The v1 run got this
   right (`material_note: kept-fbx-authored`) and it is why the v1 report lists a *different* material set per enemy.
4. **The `M_XCOM_Chitin` placeholder must not survive.** The old fallback
   (`ensure_material()` creating an instance of `/Engine/BasicShapes/BasicShapeMaterial`) was a safety net for an
   FBX with no materials; every v3 FBX has materials, so the fallback should now create a **master-based** instance
   or fail loudly. A `BasicShapeMaterial` on an alien is a ship-blocker.

### Stage 3 — collision

```python
body = mesh.get_editor_property('body_setup')
body.set_editor_property('collision_trace_flag',
                         unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
```

- UE 5.8 has **no** `EditorStaticMeshLibrary.set_collision_complex_as_simple` — the API probe in
  `import_xcom_fbx.py:195-199` lists what the library actually offers. `BodySetup.CollisionTraceFlag` is the
  authoritative property; the deprecated `mesh.collision_complexity` and `unreal.CollisionComplexity` are
  last-resort fallbacks only.
- **Readback in the same run:**
  `str(body.get_editor_property('collision_trace_flag'))` must contain `CTF_USE_COMPLEX_AS_SIMPLE`.
- **And readback again in a separate, later UE session from the saved asset on disk** — the v1 report did exactly
  this and all five passed. `EditorStaticMeshLibrary.get_collision_complexity()` will report `CTF_USE_DEFAULT`
  even when the body setup is correct; that is a known false negative, not a failure.

### Stage 4 — LODs

The FBX contains no LODs (`Model::LOD`=0). Build LOD1/LOD2 in UE from LOD0 (TASK-02 §4.5):
targets 2,200–2,800 tris (LOD1) and 500–1,050 tris (LOD2) per enemy, screen transitions 60% and 30%.
**No billboard LOD** — a sprite LOD violates the TRUE-3D lock and would break the reveal lighting.
If the 5.8 Python API cannot build LODs headlessly, the explicit fallback is to author `_LOD1`/`_LOD2` meshes in
Blender (a change to `Tools/blender/**`, which is **locked for this slot — report, do not perform**) and import
them as separate assets.

### Stage 5 — report

Write `Docs/generated/xcom_ue_import_report.json` (machine) and
`CommandCenter/outputs/ue_import/xcom_ue_import_report.md` (human), mirroring the v1 report's structure:
per enemy — asset path, triangle count **and the source of that number**, bounds origin/extent in cm and their
source, height/width/depth in cm, collision status + detail, collision readback, material list + note, status,
error. Plus a `summary` line `imported=N failed=M` and the FBX manifest cross-check table.

Triangle count must be read with the multi-API probe already in the repo
(`tri_count()` at `import_xcom_fbx.py:36-81`): `EditorStaticMeshLibrary.get_number_triangles` →
`mesh.get_num_triangles` → `StaticMeshDescription` → `render_data.get_num_triangles(0)`.

**Report both numbers when they disagree:** the Blender manifest tris and the UE readback tris. The v1 report did
this, and the height deltas it showed (manifest 1.95 m vs UE bbox 197.0 cm) are exactly the kind of delta that
must be explained rather than hidden.

---

## 4. The UE-side spawn script contract

### 4.1 The one non-negotiable rule

**`spawn_actor_from_object` returns NULL for every input in this UE 5.8 build.** This is not a usage error — it
is a property of the engine build, proven by `Tools/python/spawn_probe.py` (which tests subsystem + engine mesh,
subsystem + FBX mesh, `EditorLevelLibrary` variants, and a fresh level as a control) and documented in the
`populate_encounters.py` header comment (`probe_run1`). `blockout_map.py` used it, the base arena silently never
made it into the saved `.umap`, and `ensure_base_geometry.py` had to rebuild 23 actors afterwards (see the
`LEVEL-01` line in `CommandCenter/outputs/LEDGER.md`).

**Every spawn in the new pipeline uses the class-spawn path.**

### 4.2 Proven spawn pattern (copy this shape exactly)

```python
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def spawn_enemy(mesh_path, location, label, yaw=0.0):
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        return None
    a = sub.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(*location),
        unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
    if not a:
        return None
    a.static_mesh_component.set_static_mesh(mesh)   # the assignment IS the spawn
    a.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))  # authored scale, NOT normalised
    a.set_actor_label(label)
    return a
```

Source: `ensure_base_geometry.py:53-75` (`spawn()`), `populate_encounters.py:36-63` (`spawn_mesh()`),
`fix_pit_and_ramp.py:92-96`. `spawn_actor_from_class` + `static_mesh_component.set_static_mesh` is the only
pattern in this repo that has ever produced a saved actor.

### 4.3 The scale trap — do not normalise these meshes

`populate_encounters.py` normalises every spawned mesh to a per-prefix target height
(`target_height()` / `want / extent_z`, e.g. `ENC_` → 180 uu). **That is for the abstract blockout proxies in
`Tools/blender/out/`** (`E_BarnacleDrone`, `E_RockGolem`, …), which are meaningless blobs used as spatial markers.
The X-COM enemies are **authored at true scale** (1.44 / 2.06 / 0.33 / 2.07 / 1.03 m per the manifest). Running
them through `target_height()` would silently rescale a 2.06 m Viper to 1.80 m and a 1.03 m Chryssalid to 1.80 m.
**The enemy spawner must set scale 1.0 and never call `target_height()`.**

### 4.4 The facing trap — Blender −Y is the model's front

Every build function puts the face, snout, mandibles and weapon at **negative Y** in Blender
(`viper_snout` at y = −0.24, `chry_mandible` at y = −0.46, the Viper pistol at y = −0.15). After
`convert_scene=True` that maps to **−Y in UE** as well. A spawner that computes
`yaw = atan2(dy, dx)` toward the player and does nothing else will place the enemy **facing away**.
**The spawner must add 180° to the naive yaw** (or equivalently set the actor rotation to
`yaw = atan2(dy, dx) + 180.0`) so the enemy's face is toward the player. Verify this with one spawn per enemy
before the wave logic is written — a back-turned Sectoid is the exact failure mode of a blind import.

### 4.5 The Floater trap — pivot is on the floor

`join_objects()` forces the origin to the world cursor at (0,0,0) (`xcom_enemies_v2.py:231-233`), so the
Floater's *body* sits ~1.05 m above its own pivot while its mesh bbox height is only 0.33 m. **The Floater must
be spawned at Z + 100 cm** (or its own hover height defined by the wave table) so the shell is above the floor.
The other four are grounded at Z = 0 with feet on the floor (the builder explicitly welds a contact patch under
every foot — `make_shadow_blob` calls in `main()`).

### 4.6 The reveal light rig contract

The 1994 reveal is the design centrepiece: the enemy appears lit out of darkness by a hard cold key, a coloured
alien rim and a low under-glow. The rig is authored in Blender as `reveal_key` / `reveal_rim` / `reveal_under`
(`xcom_enemies_v2.py:720-789`) and its measured parameters live in
`CommandCenter/outputs/lighting/rig_params.json`:

| Light | Type | Colour | Blender energy (per-enemy) | UE spawn contract |
|---|---|---|---|---|
| `reveal_key` | SPOT | (0.62, 0.78, 1.00) | 133.28 W | SPOT, 36° cone, shadow on, aimed at chest (target Z = 0.55 × body height) |
| `reveal_rim` | SPOT | (0.20, 1.00, 0.42) | 186.59 W | SPOT, 45° cone, shadow on, behind-right |
| `reveal_under` | SPOT | (0.45, 0.90, 1.00) | 3.84 W | SPOT, 35° cone, at floor level, shadow off |
| `reveal_pool` | SPOT | (0.52, 0.72, 1.00) | 208.25 W | SPOT, 30° cone, shadow on |
| `reveal_wash` | AREA | (0.45, 0.55, 0.70) | 24.19 W | AREA, size 2.4, shadow off |
| world | — | (0.006, 0.008, 0.012) | strength 0.10 | the level's own dark world / post-process volume |

**Contract:** the rig is spawned **as child actors of the enemy actor** (or as components on the enemy
Blueprint) so that it follows the enemy, and the emitter strength is **driven from the spawn event** — the
brief states the rig is "replicated as point/spot lights on the spawn actor" and the reveal must read even in
total darkness. The `ACCENT_EMISSIVE` material's `EmissiveStrength` is the second half of the reveal and must be
exposed on the material instance so the same event can drive both.

**Blast radius rule:** a reveal rig that lights the whole room destroys the darkness. Each rig light must have a
finite radius/attenuation so only the spawning enemy is lit.

### 4.7 Enemy actor contract (what the wave system will call)

```python
def spawn_xcom_wave(wave_spec) -> list[unreal.Actor]
```
- `wave_spec` = list of `(enemy_name, location, optional_facing_point)`.
- Returns the spawned actors; the caller never touches `static_mesh_component` directly.
- Each actor gets the label `XCOM_<PascalEnemy>_<nn>` (§2.2).
- Each actor gets its reveal rig attached and initialised.
- **No health regeneration, no reload animation, no sprite fallback** anywhere in the contract.

### 4.8 Actor listing / cleanup (proven API)

```python
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = list(sub.get_all_level_actors())     # works
# unreal.EditorLevelLibrary.get_all_level_actors()  # works (fallback)
# get_all_actors_of_class()                     # DOES NOT EXIST on these classes
# world.persistent_level                        # not python-exposed in this 5.8 build
```
(`populate_encounters.py:96-110`.)

Cleanup by label prefix, exactly as `populate_encounters.py` does it: destroy every `StaticMeshActor` whose label
starts with `XCOM_` before re-placing a wave. **Keep the label prefix scheme stable** (`XCOM_`) so cleanup never
deletes a pickup or a blockout proxy (`ENC_`, `PU_`, `WP_`).

### 4.9 Map safety

The import script must **never open, modify or save a map**. `import_xcom_fbx.py:7-8` states this explicitly and
the v1 report proved it: after the import, `git status --porcelain Content/Maps/M_Blockout01.umap` printed
nothing. The new import must keep that property — import assets only, `save_asset` on the mesh and the
materials, `save_dirty_packages` for the packages, **no** `load_map` / `save_map`.

The *spawn* script is the opposite: it may load and save the map, but it must only touch actors whose label
starts with `XCOM_`.

---

## 5. Command-line invocations (the proven forms)

```bash
# import (read-only w.r.t. maps)
UnrealEditor-Cmd.exe TheCommander.uproject -run=pythonscript \
    -script=Tools/python/import_xcom_fbx.py \
    -unattended -nosplash -stdout -FullStdOutLogOutput

# spawn/place (may load+save the map)
UnrealEditor-Cmd.exe TheCommander.uproject -run=pythonscript \
    -script=Tools/python/spawn_xcom_enemies.py \
    -unattended -nosplash -NoSound
```

`-stdout -FullStdOutLogOutput` is required: the import report and the `SUMMARY imported=N failed=M` line are read
from the log, and the v1 attempt-1 failure (`remove_debris`) was only diagnosable from it
(`Saved/Logs/import_xcom_attempt1_failed.log`).

The commandlet exits with code 1 even on success because of an unrelated editor-config load error
(`ProjectPackagingSettings` / `PPB_Shipping`). **Do not treat a non-zero exit code as an import failure** — assert
on the `SUMMARY imported=N failed=M` line instead. (v1: successful import, exit code 1, documented in the report's
Warnings section.)

---

## 6. Acceptance criteria (TASK-07)

1. `xcom_manifest.json` preflight passes for all five enemies (tris under ceiling, FBX present, manifest↔FBX
   consistent) **before** UE is invoked.
2. All five import at `/Game/Enemies/XCOM/XCOM_<Enemy>` as `StaticMesh`, scale 1.0, upright (Z-up), with
   `SUMMARY imported=5 failed=0`.
3. Every FBX material slot is re-pointed to a `MI_XCOM_<Enemy>_<FAMILY>` instance built from the correct master;
   no `BasicShapeMaterial` fallback survives anywhere.
4. All five carry `BodySetup.CollisionTraceFlag == CTF_USE_COMPLEX_AS_SIMPLE`, confirmed by readback **from the
   saved asset in a separate UE session**.
5. LOD1 and LOD2 exist for all five, within the TASK-02 budgets, silhouette preserved, **no billboard LOD**.
6. The report JSON + MD are written, containing the manifest↔UE cross-check table.
7. `Content/Maps/M_Blockout01.umap` is byte-unchanged by the import (`git status --porcelain` empty).
8. Spawn proof: one of each enemy spawned via `spawn_actor_from_class` + `set_static_mesh`, scale 1.0, **facing
   the player** (the 180° correction applied), Floater clear of the floor, each with its reveal rig lit.
9. `Content/**` shows no sprite assets, no reload animations, and no health-regeneration logic.
