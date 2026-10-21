# TASK-02 — Per-Enemy Modernization Spec (X-COM Kit)

**Slot:** swarm-w2 · **Engine:** UE 5.8 (`TheCommander.uproject`, `EngineAssociation: 5.8`)
**Source of truth on disk:** `Tools/blender/xcom_enemies.py` (v1), `Tools/blender/xcom_enemies_v2.py` (v2/v3 builder),
`Tools/blender/out_xcom/xcom_manifest.json`, `Tools/blender/out_xcom/XCOM_*.fbx`,
`CommandCenter/briefs/XCOM_ENEMY_DESIGN_BRIEF.md`, `CommandCenter/briefs/XCOM_ENEMY_V2_FIXLIST.md`
**Design locks honoured:** TRUE 3D only (NO sprites) · original *UFO: Enemy Unknown* (1994) roster only ·
zero reload animations ever · pickups are the only health system, no regeneration.

---

## 0. Grounding — what the build scripts actually emit today

Read from the repo, not assumed:

| Fact | Evidence |
|---|---|
| v3 kit is built by `xcom_enemies_v2.py`; v1 `xcom_enemies.py` is superseded but still present and still the path named in the design brief's "BUILD OUTPUT" section | `Tools/blender/xcom_enemies.py:48-52` (usage block names itself), `Tools/blender/xcom_enemies_v2.py:48-51` |
| Each enemy is a **single joined mesh**, origin forced to the world cursor (0,0,0) i.e. **pivot on the floor** | `xcom_enemies_v2.py:220-234` `join_objects()` → `origin_set(type='ORIGIN_CURSOR')` |
| Per-enemy material families are authored by `enemy_materials()` and always create **7** materials: `CHITIN`, `PLATE`, `PLATE_DARK`, `PLATE_OXBLOOD`, `ACCENT_EMISSIVE`, `ACCENT_DIM`, `CHITIN_BONE` | `xcom_enemies_v2.py:316-346` |
| Blender material shading is **fully procedural** — noise→ColorRamp→BaseColor, a second noise→Bump(0.25)→Normal, a third noise→roughness break-up | `xcom_enemies_v2.py:249-313` `procedural_mat()` |
| FBX export: `axis_forward='-Z'`, `axis_up='Y'`, `apply_scale_options='FBX_SCALE_ALL'`, `use_selection=True`, `object_types={'MESH'}` | `xcom_enemies_v2.py:1567-1571` (v1: `xcom_enemies.py:427-431`, identical) |
| The exported FBX carries **no texture references and no external image files** — material names only | binary FBX scan: `Texture`=0, `Video`=0, `LayerElementUV`=2 (a `UVMap` layer exists, unused), `Deformer`=0, `BlendShape`=0, `Model::LOD`=0 for all five |
| The v3 FBX material names are **per-enemy** (`XCOM_Sectoid_CHITIN` …), not the v1 shared names | FBX string dump, §3 below |
| Current v3 polycounts / sizes | `out_xcom/xcom_manifest.json`: Sectoid 5636, Viper 5764, Floater 2732, Muton 5216, Chryssalid 6252 tris; FBX 146.1 / 140.2 / 78.3 / 122.6 / 164.7 KB |
| Current v3 dimensions (Blender metres) | height 1.44 / 2.06 / **0.33** / 2.07 / 1.03; width 0.46 / 0.64 / 2.48 / 1.15 / 0.82 |

### 0.1 CONFLICT TO REPORT (not silently fixed)

`CommandCenter/outputs/ue_import/xcom_ue_import_report.md` and `Content/Enemies/XCOM/*.uasset` describe the **v1** FBX
(tris 2864/3712/1980/2520/2536; heights 197/198.5/114.37/202/93.66 cm; material names `XCOM_Chitin_Mid`,
`XCOM_Armor_Plate`, …). The FBX on disk were **rebuilt at 02:47–02:51 on 2026-10-21** with the v3 builder
(tris 5636/5764/2732/5216/6252; per-enemy material names). The UE content is therefore **one generation stale**:
the imported meshes are the old geometry and the imported materials are named against a scheme the new FBX no
longer uses. A fresh import (TASK-07) will produce **new material assets** and different triangle counts; the old
`XCOM_Chitin_*` / `XCOM_Armor_*` uassets in `Content/Enemies/XCOM/` become orphans and should be deleted by the
owner of `Content/**` (locked for this slot — reported, not edited).

### 0.2 CONFLICT TO REPORT

`xcom_enemies_v2.py` still has `remove_debris` referenced in the import path vocabulary
(`xcom_enemies.py` is clean, but the UE-side `import_xcom_fbx.py:263` sets `remove_debris` defensively because
UE 5.8 removed it — see `ue_import/xcom_ue_import_report.md` "Warnings"). Any **new** import script must use the
same defensive `sset()` pattern and must not assume `remove_debris` exists.

---

## 1. Polycount budget per enemy

**Frame budget rationale.** `Docs/DESIGN.md` locks 144+ FPS. The kit must survive a full 1994-style terror
mission: up to **8 enemies visible at once** (Sectoid waves), each with a reveal light rig.
Working budget: **≤ 40,000 triangles of enemy geometry in a worst-case frame** at LOD mix, and a hard
**≤ 10,000 tris per enemy at LOD0** so a single Muton close-up never becomes the frame cost.

The v3 meshes are all well inside these numbers, so the budget is a **ceiling to enforce**, not a rebuild trigger.
Where the v3 count already sits near the ceiling (Chryssalid 6252, Viper 5764), the LOD1 target is what protects
the frame.

| Enemy | v3 actual tris | **LOD0 ceiling** | **LOD1 target** | **LOD2 target** | Why this number |
|---|---|---|---|---|---|
| **Sectoid** | 5636 | **6,000** | 2,200 (≈37%) | 800 | Smallest frame; 2× per pod is cheap. Cranium/eyes are the read — LOD1 keeps the cranium and eyes, drops finger sub-divisions. |
| **Viper** | 5764 | **6,000** | 2,300 (≈40%) | 850 | Marquee enemy: 45 cm snout + 5 dorsal ribs must survive LOD1 or the silhouette dies. Drop the 6 teeth and the hand digits first. |
| **Floater** | 2732 | **4,000** | 1,400 (≈35%) | 500 | Already the cheapest. Its 2.48 m span is *area*, not tris — it is a lighting cost, not a geometry cost. Keep the wing planform solid at LOD1. |
| **Muton** | 5216 | **7,000** | 2,700 (≈38%) | 1,000 | Widest mass in the kit (1.15 m); pauldrons + two-handed rifle + oxblood chest plate. The chest plate is the focal point — it survives every LOD. |
| **Chryssalid** | 6252 | **7,000** | 2,800 (≈40%) | 1,050 | Most expensive (4 digitigrade legs × 3 segments + 2 scythes). The scythe *edge* blade is the tell — LOD1 keeps both scythes, drops leg segment 2. |
| **Kit total (LOD0)** | 25,600 | **30,000** | 11,400 | 4,200 | 8 concurrent enemies at LOD1 = ~91k tris worst case — comfortably inside a 144 FPS budget on the target node. |

**Enforcement rules.**
1. A rebuild that pushes any enemy over its LOD0 ceiling is a **FAIL**, even if it looks better.
2. Tri count is measured the same way the existing tooling measures it: `sum(len(p.vertices)-2 for p in me.polygons)`
   in Blender (`xcom_enemies_v2.py:237-238`) and `StaticMesh.get_num_triangles(0)` in UE
   (`Tools/python/import_xcom_fbx.py:36-81`). Both numbers must agree.
3. FBX on disk is a single joined mesh per enemy — **LODs are not authored in Blender today**
   (`Model::LOD` = 0 in all five FBX). LOD1/LOD2 are **generated in UE** from LOD0 (see §4.4) or authored as
   separate Blender objects later; the *budget* is the contract either way.
4. No LOD reduction may change the **silhouette** — the v2 manifest records each enemy's canonical silhouette
   string (`XCOM_Sectoid` → "small + gaunt, oversized smooth cranium…") and that string is the acceptance test
   for every LOD.

---

## 2. Texture approach and resolution

### 2.1 The honest state: procedural in Blender, and Blender's procedural is invisible to UE

The v2 builder's entire surface story is **procedural node graphs** (`procedural_mat()`,
`xcom_enemies_v2.py:249-313`) — the fixlist demanded it: *"Every material gets a procedural detail pass (no
external textures needed)"* (`XCOM_ENEMY_V2_FIXLIST.md` §F). But **FBX does not carry Blender's node graph.**
The binary FBX scan shows `Texture`=0 / `Video`=0: the export carries the Principled scalars and nothing else.
Every one of those noise→ramp→bump chains is dropped at the FBX boundary.

**Therefore, in UE today, all five enemies render as flat-coloured primitives.** This is the single largest
gap between the Blender art and the shipped look, and it is the thing TASK-02 must close.

### 2.2 Recommended approach: **procedural re-authored in UE as Material Instance Constants** (primary), with an
optional 1024 baked set for the hero close-up

| Decision | Recommendation | Rationale |
|---|---|---|
| Chitin / Plate / Bone / Oxblood detail | **Procedural, authored in the UE master material.** Mirror the Blender node graph 1:1: `Noise` (scale 7 for chitin / 5.5 for plate / 20 for bone) → `ColorRamp` (0.32/0.70 positions, ±mottle) → `BaseColor`; a second `Noise` (×4.5) → `Bump` (strength 0.20 chitin / 0.16 plate / 0.26 bone, distance 0.015) → `Normal`; a third `Noise` (×2.0) → `ColorRamp` → `Roughness`. | Zero texture memory, zero streaming hitch, and it is the *same* look the Commander already signed off on in the preview renders. The UE master becomes the single source of truth for the surface story, and each enemy is a MIC that only changes base colour + accent. |
| Baked textures | **One optional 1024×1024 baked set per material family, not per enemy.** Allowed for the hero pass only. | Per-enemy bakes are 5× the memory for near-identical surfaces. Family-level bakes can be shared by all 5 enemies. |
| Panel lines / vents / insignia | **Geometry, not texture.** Already modelled as thin inset boxes (`panel_line()`, `xcom_enemies_v2.py:621-625`; Muton has 3 chest seams + 3 vent slats + 2 insignia bars). | Costs tris, not texels, and reads at any distance and any light angle. Keep it. |
| Accent / emissive | **Pure emissive scalar in UE**, driven by a `Vector` param (colour) + `Scalar` param (strength) on a shared emissive master. | The reveal is the whole design brief. Emissive must be a *parameter*, not a texture, so the spawn rig can drive it. |
| Normal map on the accent | None. | Emissive parts are eyes/visor/coil/venom — a normal map on them fights the bloom. |

### 2.3 Texture resolution table (if the optional baked set is produced)

| Map | Resolution | Format | Applies to | Memory |
|---|---|---|---|---|
| Chitin albedo (mottled) | **1024×1024** | sRGB PNG, BC7 | all 5 enemies (shared) | ~1 MB |
| Chitin normal | **1024×1024** | linear PNG, BC5 | all 5 (shared) | ~0.7 MB |
| Chitin roughness (ORM pack) | **1024×1024** | linear PNG, BC5 (R=ao, G=rough, B=metal) | all 5 (shared) | ~0.7 MB |
| Plate albedo + normal + ORM | **1024×1024** | as above | Sectoid, Viper, Muton, Chryssalid | ~2.4 MB |
| Bone / scythe edge | **512×512** | as above | Viper ribs+teeth, Chryssalid spurs+edge, Sectoid claws | ~0.9 MB |
| Oxblood chest plate | **1024×1024** | as above | **Muton only** (only enemy using it) | ~2.4 MB |
| Accent emissive mask | **512×512** | sRGB, R only | shared, optional | ~0.3 MB |
| **Total (all baked)** | | | | **≈ 8.4 MB** |

**Rule:** if the total baked set exceeds ~10 MB or any single family exceeds 1024×1024, the bake is rejected and
the procedural path stands. The 144 FPS target outranks surface fidelity in the dark.

### 2.4 UV reality

The FBX has a `UVMap` layer but it is the Blender primitive default — the v2 builder never unwraps
(no `bpy.ops.uv.smart_project` anywhere in `xcom_enemies_v2.py`). **Any bake therefore requires a UV pass first**,
which is a change to `Tools/blender/**` (locked for this slot). Procedural-in-UE (the recommended path) needs no UVs
at all, which is a further reason to prefer it. Reported, not edited.

---

## 3. Material breakdown per enemy

### 3.1 What the FBX files actually carry today (verified by string scan of the binary FBX)

| Enemy | Material slots in the v3 FBX | Count |
|---|---|---|
| **XCOM_Sectoid** | `XCOM_Sectoid_CHITIN`, `_PLATE`, `_PLATE_DARK`, `_CHITIN_BONE`, `_ACCENT_EMISSIVE` | **5** |
| **XCOM_Viper** | `XCOM_Viper_CHITIN`, `_PLATE`, `_PLATE_DARK`, `_CHITIN_BONE`, `_ACCENT_EMISSIVE` | **5** |
| **XCOM_Floater** | `XCOM_Floater_CHITIN`, `_PLATE_DARK`, `_CHITIN_BONE`, `_ACCENT_EMISSIVE` | **4** |
| **XCOM_Muton** | `XCOM_Muton_CHITIN`, `_PLATE`, `_PLATE_DARK`, `_PLATE_OXBLOOD`, `_ACCENT_EMISSIVE` | **5** |
| **XCOM_Chryssalid** | `XCOM_Chryssalid_CHITIN`, `_PLATE`, `_PLATE_DARK`, `_CHITIN_BONE`, `_ACCENT_EMISSIVE` | **5** |
| | **Total across kit** | **24 slots** |

The builder always *authors* 7 materials per enemy (`enemy_materials()`), but Blender's FBX exporter only writes
materials that are actually assigned to a face — so `PLATE_OXBLOOD` reaches only the Muton, `PLATE` reaches
nobody on the Floater (its shell is pure chitin), and `ACCENT_DIM` is currently unused on all five.

### 3.2 What each material carries, and what it must carry in UE

| Family | Blender procedural recipe (authoritative) | What it carries on the model | UE master |
|---|---|---|---|
| `CHITIN` | noise 7.0 → ramp 0.32/0.70 (±0.30 mottle) → BaseColor; noise 31.5 → Bump 0.20 → Normal; noise 14.0 → ramp → Roughness ±0.10; rough 0.56, metal 0.04 | All flesh: torsos, limbs, cranium, abdomen, Floater shell + wings, Chryssalid thorax/abdomen/neck, Muton abdomen + limb segments. The base of every silhouette. | `M_XCOM_Chitin_Master` |
| `PLATE` | noise 5.5 → ramp (±0.22) → BaseColor; noise 24.75 → Bump 0.16 → Normal; noise 11.0 → ramp → Roughness ±0.10; rough 0.32, metal 0.62 | Hard shell: Sectoid sternum/shoulder caps/feet, Viper throat/shoulders/feet, Muton helmet/chest/pauldrons/pelvis/feet, Chryssalid feet + scythe blades. | `M_XCOM_Plate_Master` |
| `PLATE_DARK` | noise 9.0 → ramp; rough 0.70, metal 0.30 | Recessed/inset detail only: panel-line seams, Muton visor recess + respirator, Sectoid nasal slit, Floater mouth seam, Chryssalid mouth seam, alien eye *sockets*. The shadow-line colour of the whole kit. | `M_XCOM_PlateDark_Master` |
| `PLATE_OXBLOOD` | noise 10.0 → ramp (±0.35); rough 0.42, metal 0.30 | **Muton only** — the oxblood chest plate (with its 3 seams, 3 vent slats, 2 insignia). The one saturated colour in the kit and the Muton's focal point. | `M_XCOM_Oxblood_Master` |
| `CHITIN_BONE` | noise 20.0 → ramp; rough 0.62, metal 0.0 | Bone only: Sectoid claws, Viper dorsal ribs + teeth, Floater wing ribs, Chryssalid dorsal spurs + mandibles + scythe cutting edge + claws. Never on hands, never on feet. | `M_XCOM_Bone_Master` |
| `ACCENT_EMISSIVE` | noise 16.0, bump 0.12, rough 0.22, emissive colour + strength | The reveal: Sectoid eye lenses, Viper eye lenses + pistol coil, Floater eye lenses + 3 dorsal core segments, Muton visor slit + rifle coil + back core, Chryssalid eye lenses + venom sac. | `M_XCOM_Accent_Master` (emissive, bloom-capable) |
| `ACCENT_DIM` | authored everywhere, **assigned nowhere** | Reserved: dimmed secondary glow for a future "core cooling" state. Ship the material; assign nothing. | `M_XCOM_AccentDim_Master` |

### 3.3 Per-enemy accent colour (from `BUILDERS`, `xcom_enemies_v2.py:1283-1374`) — the only bright colour per enemy

| Enemy | Accent RGB | Strength | Reads as |
|---|---|---|---|
| Sectoid | (0.12, 1.00, 0.40) | 2.5 | acid green eyes |
| Viper | (0.10, 1.00, 0.75) | 2.4 | cyan-green |
| Floater | (0.05, 0.80, 1.00) | 2.6 | cold cyan (the psychic one) |
| Muton | (0.25, 1.00, 0.18) | 2.4 | hard green visor slit |
| Chryssalid | (0.45, 1.00, 0.05) | 2.0 | venom yellow-green |

The per-enemy base-colour triplets (chitin / plate / oxblood / bone) also live in `BUILDERS` and are the values the
UE MICs must reproduce exactly — otherwise the Blender preview and the UE build drift apart, which is exactly the
failure Ebert scored 3.33 for.

### 3.4 Material-instance count in UE

- **7 master materials** (`M_XCOM_*_Master`) in `/Game/Enemies/XCOM/Materials/Masters/`
- **≤ 24 material instances** (one per FBX slot) in `/Game/Enemies/XCOM/Materials/Instances/`,
  named `MI_XCOM_<Enemy>_<FAMILY>` — e.g. `MI_XCOM_Muton_PLATE_OXBLOOD`.
- Instance parameters: `BaseColor` (Vector), `Roughness` (Scalar), `Metallic` (Scalar), `EmissiveColor` (Vector),
  `EmissiveStrength` (Scalar), `NormalStrength` (Scalar). `EmissiveStrength` **must** be exposed so the spawn rig
  can drive the reveal (§4.6).
- **Do not** overwrite the FBX-authored materials. `import_xcom_fbx.py:361-377` already keeps FBX-authored
  material sets and only falls back to a created instance when the FBX carries none; that behaviour is correct and
  must be preserved, with the fallback path now creating the *master-based* MIC instead of an
  `/Engine/BasicShapes/BasicShapeMaterial` instance (the current fallback is a placeholder, not shippable).

---

## 4. UE import settings (per enemy)

### 4.1 Scale

| Setting | Value | Why |
|---|---|---|
| Blender unit | 1.0 = 1 metre; FBX export `apply_scale_options='FBX_SCALE_ALL'` | `xcom_enemies_v2.py:1570` |
| UE import | `FbxImportUI.static_mesh_import_data.convert_scene = True`, **no** `mesh_scale_to_unit` override, import uniform scale **1.0** | The v1 import already proved this maps 1 Blender m → 100 UE cm (1.95 m Sectoid → 197.0 cm in UE, per `ue_import/xcom_ue_import_report.md` "Manifest Cross-Check"). Keep it. |
| Actor scale at spawn | **1.0** for all five | The meshes are already human-scale in metres. Do **not** run the `populate_encounters.py` height-normalisation trick (`target_height()` / `want / extent_z`) on these — that helper exists for the abstract blockout proxies in `Tools/blender/out/`, not for authored characters. |
| Floater Z offset | **+100 cm** at spawn | The v2 builder forces the pivot to the world cursor, so the Floater's *body* sits ~1.05 m above its own origin while its mesh bbox height is only 0.33 m. A spawner that places it at floor level will bury it. This is a property of the current FBX, and it must be handled at spawn (TASK-07), not by re-baking. |

### 4.2 Axis conversion

- Blender exports **Y-up, −Z forward** (`axis_forward='-Z'`, `axis_up='Y'`). UE is Z-up, +X forward.
- Set `convert_scene = True` and let UE apply the conversion. **Do not** additionally set `rotation` or
  `scale` on the import task — the existing import script does not, and the v1 import produced correct upright
  meshes (heights 197/198.5/202 cm for three ~2 m humanoids), so the conversion is already right.
- **Forward vector convention:** Blender's `−Y` is the model's "front" in every build function
  (eyes, snouts, mandibles and the weapon all sit at negative Y). In UE that becomes **−Y as well** after
  `convert_scene` (UE's −Y is also "into the screen" for a default-rotated actor). A spawner that faces an enemy
  at the player with `yaw = atan2(dy, dx)` must account for the model's forward being **−Y**, i.e. add 180° to the
  naive yaw, or the enemy will spawn with its back to the player. This is the most likely silent bug in the
  first in-engine spawn — verify it with one spawn per enemy before the wave system lands.

### 4.3 FBX import options (exactly the set proven to work in UE 5.8)

From `Tools/python/import_xcom_fbx.py:232-267`, which produced a clean 5/5 import
(`[XCOMIMPORT] SUMMARY imported=5 failed=0`):

```
task.filename            = <FBX path>
task.destination_path    = '/Game/Enemies/XCOM'
task.destination_name    = 'XCOM_<Enemy>'      # asset name == FBX stem
task.replace_existing    = True
task.save                = True
task.automated           = True

options.import_mesh            = True
options.import_as_skeletal     = False     # static, no rig in this kit (Deformer=0 in every FBX)
options.import_materials       = True      # keep FBX material slots; re-point them at MICs afterwards
options.import_textures        = False     # there ARE no textures in the FBX (Texture=0)
options.import_animations      = False     # and no animation (BlendShape=0)
options.static_mesh_import_data.combine_meshes          = True   # one joined mesh per enemy
options.static_mesh_import_data.generate_lightmap_u_vs   = False  # no lightmap UVs on a character
options.static_mesh_import_data.auto_generate_collision  = False  # collision is set explicitly, see §4.4
options.static_mesh_import_data.convert_scene            = True   # Y-up/-Z-forward -> Z-up/+X-forward
options.static_mesh_import_data.remove_debris            = (set defensively; REMOVED in UE 5.8)
```

Every one of these must be set through a **defensive setter** (the `sset(obj, prop, val)` helper at
`import_xcom_fbx.py:241-247`) that swallows the exception when the property does not exist in the running build.
Attempt 1 of the real import failed on *every* mesh for exactly this reason
(`'FbxStaticMeshImportData' object has no attribute 'remove_debris'`).

### 4.4 Collision

- **Set to Use Complex as Simple.** The enemies must block the player, and the kit has no authored simple
  collision (no convex hulls, no box). UE 5.8 has **no** `EditorStaticMeshLibrary.set_collision_complex_as_simple`
  helper — the API probe in `import_xcom_fbx.py:195-199` confirms the library only exposes
  `get_collision_complexity`, `add_simple_collisions`, `bulk_set_convex_decomposition_collisions`.
- The **authoritative** write is on the mesh's `BodySetup`:
  ```python
  body = mesh.get_editor_property('body_setup')
  body.set_editor_property('collision_trace_flag',
      unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
  ```
  (`import_xcom_fbx.py:313-325`). The legacy `mesh.collision_complexity` fallback and
  `unreal.CollisionComplexity` are **deprecated on `StaticMesh` in 5.8** and only kept as a last resort.
- **Readback is mandatory**: re-read `body.get_editor_property('collision_trace_flag')` from the *saved* asset in
  a separate UE session and assert `'CTF_USE_COMPLEX_AS_SIMPLE'` is in the string. The v1 run did exactly this
  and all five passed (`ue_import/xcom_ue_import_report.md` "Verification"). `get_collision_complexity()` will
  still report `CTF_USE_DEFAULT` — that is expected and must not be treated as a failure.
- **Performance note:** complex-as-simple on a 5,652-tri Muton is a per-triangle trace. It is acceptable for
  5–8 enemies but is a candidate for the **convex-decomposition upgrade** if profiling ever complains:
  `EditorStaticMeshLibrary.bulk_set_convex_decomposition_collisions` with ~8 convex hulls per enemy.
  Do not do this before a profile says so.

### 4.5 LOD policy (UE side)

The FBX carries **no LODs** (`Model::LOD`=0 in all five), so LOD1/LOD2 must be produced in UE:

| LOD | Source | Screen-size transition | Budget (§1) | Notes |
|---|---|---|---|---|
| LOD0 | the imported mesh | 100% → 60% | per enemy ceiling | Source of truth. |
| LOD1 | UE-generated (Decimate / `StaticMeshEditorSubsystem` LOD build) | 60% → 30% | 2,200–2,800 tris | Must preserve the silhouette string from the manifest. **Verify by render, not by tri count.** |
| LOD2 | UE-generated | 30% → 15% | 500–1,050 tris | |
| LOD3 | UE-generated | 15% → 0% | ≤ 300 tris | Optional; a degenerate mesh is acceptable. **A billboard/sprite LOD is forbidden** — the design lock is TRUE 3D, NO sprites, and a billboard LOD would also break the reveal lighting. |

- Use `StaticMeshEditorSubsystem` LOD generation in the import script rather than a manual editor step, so the
  whole kit is reproducible headless. If the 5.8 Python API does not expose a working LOD-build call, the
  **fallback is explicit**: import only LOD0 and author LOD1/LOD2 as separate joined meshes in
  `Tools/blender/xcom_enemies_v2.py` (a change to a locked path — report, do not perform) and import them as
  `_LOD1` / `_LOD2` assets, then wire the LOD array. Do not silently ship a single-LOD kit.
- LOD transitions must be identical across the five so the transition never pops one enemy in isolation.

### 4.6 Material instances, emissive, and the reveal rig

- On import, keep the FBX material slots and **replace each with the matching MIC** from §3.4
  (`StaticMesh.set_material(i, mat)` — the proven call at `import_xcom_fbx.py:171-188`).
- The **accent emissive** must be a real emissive material with `EmissiveStrength` exposed, because the whole
  point of the kit is the 1994 "lit out of darkness" reveal. The Blender rig values
  (`CommandCenter/outputs/lighting/rig_params.json`) are the reference:
  `reveal_key` SPOT (0.62, 0.78, 1.0), `reveal_rim` SPOT (0.20, 1.00, 0.42), `reveal_under` SPOT (0.45, 0.90, 1.00),
  world background 0.10, per-enemy wattages 133/187/4/208/24.
- **Project bloom is off**: `Config/DefaultEngine.ini:19` sets `r.DefaultFeature.Bloom=False`. The Blender preview
  bloomed via the compositor Glare node (threshold 0.85); UE will **not** bloom by default. The spec therefore
  requires a **Post Process Volume with Bloom enabled** (or `r.DefaultFeature.Bloom=True` in the project settings)
  around the play space, otherwise the emissive eyes/cores read as flat bright polygons and the entire reveal
  design fails. This is a project-settings change — **reported, not edited** (`Config/` is locked for this slot).
- The reveal **light rig** itself is a UE-side spawn concern (TASK-07 §6), not an import concern: the FBX carries
  no lights.

### 4.7 Per-enemy import settings summary table

| Setting | Sectoid | Viper | Floater | Muton | Chryssalid |
|---|---|---|---|---|---|
| Asset name | `XCOM_Sectoid` | `XCOM_Viper` | `XCOM_Floater` | `XCOM_Muton` | `XCOM_Chryssalid` |
| Dest path | `/Game/Enemies/XCOM` | ← | ← | ← | ← |
| Import as | Static (skeletal=False) | ← | ← | ← | ← |
| Uniform scale | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| Actor scale at spawn | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| Spawn Z offset | 0 | 0 | **+100 cm** | 0 | 0 |
| Collision | ComplexAsSimple | ← | ← (hovering: no floor contact) | ← | ← |
| LOD0 ceiling | 6,000 | 6,000 | 4,000 | 7,000 | 7,000 |
| Material slots | 5 | 5 | 4 | 5 | 5 |
| Accent | (0.12,1.00,0.40) @2.5 | (0.10,1.00,0.75) @2.4 | (0.05,0.80,1.00) @2.6 | (0.25,1.00,0.18) @2.4 | (0.45,1.00,0.05) @2.0 |
| Baked textures allowed | chitin+plate+bone 1024 | chitin+plate+bone 1024 | chitin+bone 1024 | chitin+plate+oxblood+bone 1024 | chitin+plate+bone 1024 |
| Reveal rig | key+rim+under | key+rim+under | key+rim+under | key+rim+under | key+rim+under |

---

## 5. Acceptance criteria (TASK-02)

1. Every enemy is inside its §1 LOD0 ceiling, measured by the same formula as the existing tooling, and the
   number is written into the build manifest alongside the current one.
2. Every FBX carries its §3.1 material slots, and every one of them is mapped to a MIC in UE with the §3.3 base
   colours and accent values reproduced exactly.
3. No enemy renders as a flat untextured primitive in UE — the procedural master materials carry the Blender
   noise→ramp→bump chain.
4. All five import at scale 1.0, upright (Z-up), collision = `CTF_USE_COMPLEX_AS_SIMPLE`, confirmed by readback
   from the saved asset.
5. LOD1/LOD2 exist for all five and preserve each enemy's canonical silhouette string.
6. The Floater spawns clear of the floor (+100 cm) and no enemy spawns facing away from the player.
7. A post-process volume provides bloom, or the reveal is documented as un-bloomed with the reason.
8. **No sprites, no billboard LODs, no reload animations, no health regeneration** anywhere in the pipeline.
