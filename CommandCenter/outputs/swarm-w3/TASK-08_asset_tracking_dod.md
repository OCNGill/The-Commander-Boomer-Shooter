# TASK-08 — Asset tracking and Definition of Done

- **Slot:** swarm-w3
- **Lane:** W3 (asset-tracking / DoD lane)
- **Written:** 2026-10-21T07:31:00-04:00
- **Status:** spec only — nothing in `Content/**`, `Tools/**`, `Docs/**` or `Config/**` was edited. No asset was renamed, moved, re-imported or deleted.
- **Companions:** `CommandCenter/outputs/swarm-w3/CLAIM_TASK-08.md`, `CommandCenter/outputs/swarm-w3/LEDGER_LINE.md`

---

## 0. Why this exists

The X-COM enemy kit has **two independent, unlinked truths** on disk right now:

1. A **Blender-side** kit that is current: five FBX, rebuilt 04:24–04:27, with a manifest written at 04:58.
2. A **UE-side** kit that is **stale**: sixteen `.uasset` files written at 01:04–01:13, from an **earlier** build of the FBX, carrying a **different material naming scheme** than the current FBX.

The only artefact that claims to tie them together — the import report — is itself the product of
the *old* build and is therefore a **description of assets that are no longer what it says they
are**. There is no tracker, no freshness check, and no single file that says "this UE asset came
from this FBX, at this hash". The DoD below fixes that.

**This document is a spec, not an implementation.** It defines:

- **§2** the naming spine (Blender side, UE side, in-level) and the rules that make it
  enforceable;
- **§3** the asset-tracking system — what file, what schema, what command, what it reports;
- **§4** the **Definition of Done** — what must exist, where, with what name, and **what
  measurement proves it**;
- **§5** the current state measured against that DoD, with the gaps named;
- **§6** conflicts that are reported and not fixed.

---

## 1. The kit being tracked

Five X-COM enemies. Everything below is measured from disk on **2026-10-21**.

| Enemy | FBX | bytes | triangles | height (m) | width (m) | depth (m) | ground contact | hover (m) | weapon | emissive | face detail |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `XCOM_Sectoid` | `XCOM_Sectoid.fbx` | 191 244 | 7 308 | 1.39 | 0.52 | 0.70 | yes | 0.0 | no | yes | yes |
| `XCOM_Viper` | `XCOM_Viper.fbx` | 143 772 | 5 764 | 2.06 | 0.64 | 0.70 | yes | 0.0 | **yes** | yes | yes |
| `XCOM_Floater` | `XCOM_Floater.fbx` | 67 196 | 2 184 | 0.29 | **2.48** | 1.40 | **no** | **0.9** | no | yes | yes |
| `XCOM_Muton` | `XCOM_Muton.fbx` | 125 644 | 5 216 | 2.07 | 1.15 | 1.09 | yes | 0.0 | **yes** | yes | yes |
| `XCOM_Chryssalid` | `XCOM_Chryssalid.fbx` | 168 668 | 6 252 | 1.03 | 0.82 | 1.62 | yes | 0.0 | no | yes | yes |

Source of truth: `Tools/blender/out_xcom/xcom_manifest.json` (a JSON **list** of five per-enemy
dicts; `name` = asset name, `fbx` = filename, plus `tris`, `height_m`, `width_m`, `length_m`,
`has_ground_contact`, `hover_clearance_m`, `has_emissive`, `has_weapon`, `has_face_detail`,
`emissive_px`, `emissive_green_px`, `emissive_cyan_px`, `fbx_kb`, and the render-audit fields
`bottom5_min/mean/p05/p95`, `contact_probe_px`, `torso_pitch_deg`, `contact_shadow_source`).

### 1.1 FBX integrity (sha256, measured)

| File | sha256 | mtime |
|---|---|---|
| `XCOM_Sectoid.fbx` | `4eda812313b53a7a6ae8b663b23212386ccbcd1615dc88a261d06cbe932f3b56` | 2026-10-21T04:24:27-04:00 |
| `XCOM_Viper.fbx` | `0dabde0e28f16b68a59d9b7421639fd9df6040d8c559b3138696d2949299ed41` | 2026-10-21T04:25:27-04:00 |
| `XCOM_Floater.fbx` | `e90fb732ab604043103014c1bc3bc257681d6d474c79beb267c91cf49bc52dce` | 2026-10-21T04:26:13-04:00 |
| `XCOM_Muton.fbx` | `7fcb1a6a4259f32e2242312b468fac5b3dceef190ecaf629faed78d94d122dbb` | 2026-10-21T04:26:54-04:00 |
| `XCOM_Chryssalid.fbx` | `acc9f5a795fef61a52fc3d3931a0a2e77076e99b6e0d9f486a948b751b6356cf` | 2026-10-21T04:27:47-04:00 |

The manifest itself: `xcom_manifest.json`, 11 014 bytes, sha256 prefix `f21049dbbc2042b6`,
mtime 2026-10-21T04:58:44-04:00 — i.e. the manifest was written **~31 minutes after** the FBX
it describes, so the manifest is newer than the geometry it describes. Good.

---

## 2. The naming spine

This is the spine defined in `CommandCenter/outputs/swarm-w2/TASK-07_ue_import_pipeline.md` §2,
restated here because the tracker has to enforce it.

### 2.1 Blender side (source)

| Element | Pattern | Example |
|---|---|---|
| Enemy FBX | `XCOM_<PascalEnemy>.fbx` | `XCOM_Sectoid.fbx` |
| Blender object / mesh | `XCOM_<PascalEnemy>` | `XCOM_Chryssalid` |
| Blender material | `XCOM_<PascalEnemy>_<FAMILY>` | `XCOM_Muton_PLATE_OXBLOOD` |
| Manifest | `xcom_manifest.json`, one entry per enemy | — |
| Preview renders | `XCOM_<PascalEnemy>.png`, `_turn.png`, `_scale.png`, `_silh.png` | — |

`<PascalEnemy>` ∈ `Sectoid, Viper, Floater, Muton, Chryssalid`.
`<FAMILY>` ∈ `CHITIN, PLATE, PLATE_DARK, PLATE_OXBLOOD, CHITIN_BONE, ACCENT_EMISSIVE, ACCENT_DIM`.

**Enforcement rules:**

- Uppercase, underscores only between words, no spaces, no dashes, no dots in the stem.
- **The FBX stem must equal the UE asset name.** The importer derives the destination name from
  the stem and the report is keyed on it; a mismatch silently orphans the asset.
- Every FBX carries **one material slot per material it actually uses**, named
  `XCOM_<PascalEnemy>_<FAMILY>` — the *enemy* is in the slot name, so two enemies never share a
  slot.
- The family token in a material slot is the **uppercase underscore** form
  (`CHITIN_BONE`, `PLATE_DARK`, `PLATE_OXBLOOD`, `ACCENT_EMISSIVE`). It is not abbreviated.

### 2.2 UE side (assets)

| Asset | Path | Pattern | Example |
|---|---|---|---|
| Static mesh (LOD0) | `/Game/Enemies/XCOM` | `XCOM_<PascalEnemy>` | `/Game/Enemies/XCOM/XCOM_Sectoid.XCOM_Sectoid` |
| Master material | `/Game/Enemies/XCOM/Materials/Masters` | `M_XCOM_<Family>_Master` | `M_XCOM_Chitin_Master` |
| Material instance | `/Game/Enemies/XCOM/Materials/Instances` | `MI_XCOM_<PascalEnemy>_<FAMILY>` | `MI_XCOM_Muton_PLATE_OXBLOOD` |
| Texture (baked) | `/Game/Enemies/XCOM/Textures` | `T_XCOM_<Family>_<Map>` | `T_XCOM_Chitin_Normal` |
| Blueprint actor | `/Game/Enemies/XCOM/Blueprints` | `BP_XCOM_<PascalEnemy>` | `BP_XCOM_Viper` |
| Spawned actor label | in-level | `XCOM_<PascalEnemy>_<nn>` | `XCOM_Sectoid_03` |

**Rules:**

- The prefixes `M_` / `MI_` / `T_` / `BP_` are **mandatory and non-optional**. They exist because
  the v1 import wrote raw FBX material names straight into `/Game/Enemies/XCOM`
  (`XCOM_Chitin_Mid.uasset` and siblings), so mesh, material and texture share one flat
  namespace. The new scheme separates them.
- Masters and instances live in **subfolders**. The flat folder keeps **only the five mesh
  assets**, so a stale-name sweep is a one-pass, low-risk operation.
- **The `M_` / `MI_` / `T_` tokens use the PascalCase family spelling**
  (`Chitin`, `PlateDark`, `Oxblood`, `Bone`, `Accent`, `AccentDim`) because they are
  *UE material families*, while the **FBX slot keeps the uppercase underscore form**
  (`CHITIN`, `PLATE_DARK`). The mapping between the two spellings is fixed and is the one place
  a typo can break the link. **A tracker that normalises case and underscores on both sides is
  mandatory** — see §3.4.
- `MI_XCOM_<PascalEnemy>_<FAMILY>` keeps the **uppercase** family token, matching the FBX slot
  it was made from, so a slot → instance mapping is a literal suffix match.

### 2.3 Target tree

```
/Game/Enemies/XCOM/
├── XCOM_Sectoid.uasset         (StaticMesh LOD0, collision = ComplexAsSimple)
├── XCOM_Viper.uasset
├── XCOM_Floater.uasset
├── XCOM_Muton.uasset
├── XCOM_Chryssalid.uasset
├── Materials/
│   ├── Masters/                 M_XCOM_<Family>_Master.uasset  (7 families)
│   └── Instances/               MI_XCOM_<PascalEnemy>_<FAMILY>.uasset  (24 = one per FBX slot)
├── Textures/                    T_XCOM_<Family>_<Map>.uasset
└── Blueprints/                  BP_XCOM_<PascalEnemy>.uasset
```

### 2.4 Slot census — the numbers the tracker must reconcile

The current FBX carry **24 material slots** across **6 families in active use** (the 7th,
`ACCENT_DIM`, is declared but unused):

| Family | Slots | Enemies carrying it |
|---|---|---|
| `CHITIN` | 5 | Sectoid, Viper, Floater, Muton, Chryssalid |
| `CHITIN_BONE` | 4 | Sectoid, Viper, Floater, Chryssalid |
| `PLATE` | 4 | Sectoid, Viper, Muton, Chryssalid |
| `PLATE_DARK` | 5 | all five |
| `PLATE_OXBLOOD` | 1 | **Muton only** |
| `ACCENT_EMISSIVE` | 5 | all five |
| **total** | **24** | 5 + 4 + 4 + 5 + 1 + 5 |

Per enemy: Sectoid 5, Viper 5, Floater 4, Muton 5, Chryssalid 5.

**The DoD therefore demands exactly 24 material instances**, one per slot, and a per-enemy count
matching the table above. A missing `MI_XCOM_Muton_PLATE_OXBLOOD` is a one-off miss that this
census makes visible.

### 2.5 Why the count matters mechanically

**Blender's procedural material graphs do not survive FBX export.** Every one of the five FBX
carries **Texture count 0, Video count 0, Deformer count 0** — verified by scanning the binary
`Texture`/`Video`/`Deformer` records in each file. The kit therefore renders **flat in-engine
today**: the meshes import with correct geometry, correct collision and correct slot names, but
with untextured, unlit-by-graph materials. The import report's own note says
`material_note: "kept-fbx-authored"`, and the material list it records for each mesh is the
**old flat family set** (`XCOM_Chitin_Mid, XCOM_Chitin_Pale, XCOM_Chitin_Dark, XCOM_Eye_Emissive,
…`) — the v1 names, not the current per-enemy slot names.

**Consequence for the DoD:** the 24 material instances cannot be a mechanical copy of the FBX
slots, because the FBX slots carry no graph to instance from. The masters must be **authored in
UE** (or the textures must be **baked**), and the instances must be **created from the masters
by hand or by script**. The tracker must record, per instance, whether it is authored or
inherited, and must not report a kit as done on slot count alone.

---

## 3. The asset-tracking system

### 3.1 What must exist

| Artefact | Path | Purpose |
|---|---|---|
| **Tracker script** | `Tools/python/track_xcom_assets.py` | Walks the kit, computes hashes, reconciles Blender ↔ UE ↔ manifest, writes the ledger and prints a verdict. |
| **Ledger (machine)** | `CommandCenter/outputs/asset_tracking/xcom_asset_ledger.json` | The single current-truth file. One record per asset, with hashes and provenance. |
| **Ledger (human)** | `CommandCenter/outputs/asset_tracking/xcom_asset_ledger.md` | The same data as a table, plus the verdict and the gap list. |
| **Import receipt** | `CommandCenter/outputs/asset_tracking/import_receipt.json` | Per-import run: which FBX hash went in, which UE assets came out, retention, collision readback, material mapping. |

No tracker exists today — `find . -name "*asset_track*" -o -name "*dod*"` returns nothing, and
`Tools/python/` contains no tracker (it has `import_xcom_fbx.py`, `build_manifest.py`,
`ue_build_report.py`, `ue_parity_verify.py` — importers and probes, but nothing that reconciles
the three sides).

### 3.2 The ledger schema

One record per asset, per side. Required fields — every one of them is either a hash, a
timestamp, or a foreign key to another record. **No field may be null**; an unknown is the
string `"UNKNOWN"`, so "missing" is never silently the same as "not applicable".

```jsonc
{
  "schema": "xcom_asset_ledger/1",
  "generated_utc": "2026-10-21T11:31:00Z",
  "project": "<repo root>",
  "kit": "XCOM",
  "enemies": ["XCOM_Sectoid","XCOM_Viper","XCOM_Floater","XCOM_Muton","XCOM_Chryssalid"],
  "records": [
    {
      "id": "fbx:XCOM_Sectoid",
      "side": "blender",                 // blender | ue
      "kind": "mesh",                   // mesh | material | material_instance | texture | blueprint | audio | manifest | preview
      "name": "XCOM_Sectoid",
      "path": "Tools/blender/out_xcom/XCOM_Sectoid.fbx",
      "bytes": 191244,
      "sha256": "4eda8123…",
      "mtime_utc": "2026-10-21T08:24:27Z",
      "source_id": null,                // for UE records: the fbx:<name> it came from
      "slot_of": null,                  // for material_instance: the fbx slot it realises
      "material_family": null,          // "CHITIN" | … | "Chitin" (normalised)
      "triangles": 7308,
      "collision": null,
      "imported_tris": null,
      "retention_pct": null,
      "status": "CURRENT",              // CURRENT | STALE | MISSING | ORPHAN | NAMING_VIOLATION
      "notes": ""
    }
  ],
  "summary": {
    "total": 0, "current": 0, "stale": 0, "missing": 0, "orphan": 0, "naming_violation": 0,
    "verdict": "FAIL"
  }
}
```

### 3.3 The five checks the tracker runs

| # | Check | What it compares | FAIL condition |
|---|---|---|---|
| **C1** | **Freshness** | UE mesh `.uasset` mtime vs the source FBX mtime | UE asset older than its FBX → `STALE` |
| **C2** | **Hash link** | FBX sha256 in the ledger vs the FBX sha256 recorded in the last import receipt | FBX hash changed since import → `STALE` |
| **C3** | **Naming** | every asset name against the §2 patterns | any deviation → `NAMING_VIOLATION` |
| **C4** | **Slot census** | FBX slot count per enemy vs the number of `MI_` instances for that enemy, and vs the §2.4 table | mismatch → `MISSING` / `ORPHAN` |
| **C5** | **Manifest agreement** | `xcom_manifest.json` (tris, height, flags) vs the FBX on disk and vs the UE bounds | disagreement → `NAMING_VIOLATION` / note |

**C2 is the check that would have caught the current situation.** The UE assets were imported
from an FBX build whose hash is no longer on disk; a hash comparison flags that immediately and
without ambiguity, where an mtime comparison alone can be fooled by a copied file.

### 3.4 Family-token normalisation (mandatory)

The tracker must compare family tokens case- and underscore-insensitively:

```
normalise_family(t) = t.replace("_", "").upper()
    "CHITIN_BONE" → "CHITINBONE"
    "ChitinBone"   → "CHITINBONE"
    "PlateDark"    → "PLATEDARK"
    "PLATE_DARK"   → "PLATEDARK"
```

without this, `M_XCOM_PlateDark_Master` and `MI_XCOM_Muton_PLATE_DARK` will never match, and
the tracker will report false orphans on every dark-plate slot.

### 3.5 Command surface

```
python Tools/python/track_xcom_assets.py            # write ledger + print verdict
python Tools/python/track_xcom_assets.py --check    # exit 1 if the verdict is FAIL, no writes
python Tools/python/track_xcom_assets.py --json     # machine-readable stdout only
```

**`--check` is the DoD command.** It must be safe to run in CI: read-only, deterministic, and
it exits non-zero on any `STALE` / `MISSING` / `ORPHAN` / `NAMING_VIOLATION`.

### 3.6 What the tracker prints

A per-enemy line and a per-asset table, plus the summary and the verdict:

```
XCOM_Sectoid   fbx 04:24:27 sha 4eda8123  ue 01:13:31  → STALE  (ue 3h11m older than fbx)
XCOM_Viper     fbx 04:25:27 sha 0dabde0e  ue 01:13:32  → STALE
XCOM_Floater   fbx 04:26:13 sha e90fb732  ue 01:13:32  → STALE
XCOM_Muton     fbx 04:26:54 sha 7fcb1a6a  ue 01:13:32  → STALE
XCOM_Chryssalid fbx 04:27:47 sha acc9f5a7  ue 01:13:33 → STALE

naming violations : 11   (flat v1 materials, M_XCOM_Chitin without _Master, no subfolders)
missing instances : 24   (expected 24 MI_XCOM_<Enemy>_<FAMILY>, found 0)
orphan UE assets  : 11   (XCOM_Chitin_Mid, XCOM_Chitin_Pale, …)
verdict: FAIL
```

---

## 4. Definition of Done

The DoD has three parts: **what must exist**, **where**, and **what measurement proves it**.
Every gate below is machine-checkable by `track_xcom_assets.py --check`.

### 4.A Source side (Blender)

| # | Gate | Where | Proof |
|---|---|---|---|
| **A1** | Exactly 5 FBX, one per enemy, named `XCOM_<PascalEnemy>.fbx` | `Tools/blender/out_xcom/` | `len(fbx) == 5` and each matches `^XCOM_[A-Z][a-z]+\.fbx$` |
| **A2** | 4 preview PNGs per enemy (`.png`, `_turn.png`, `_scale.png`, `_silh.png`) | `Tools/blender/out_xcom/` | 20 PNGs present, none 0 bytes |
| **A3** | A manifest entry per enemy, `name` == FBX stem | `Tools/blender/out_xcom/xcom_manifest.json` | 5 entries; `name` == stem for each |
| **A4** | Manifest geometry matches the FBX on disk (tris, height, ground-contact, hover, weapon, emissive, face-detail) | same | tracker C5 passes for all 5 |
| **A5** | 24 FBX material slots, named `XCOM_<PascalEnemy>_<FAMILY>`, families from the 7-family list | inside each FBX | slot count per enemy == manifest census (§2.4); every slot name matches the pattern and its family is in the list |
| **A6** | Every FBX has a recorded sha256 in the ledger | ledger | `records` contain 5 `side=blender, kind=mesh` entries with non-null sha256 |

### 4.B UE side

| # | Gate | Where | Proof |
|---|---|---|---|
| **B1** | 5 static meshes `XCOM_<PascalEnemy>.uasset` in the **flat** folder | `/Game/Enemies/XCOM/` | exactly 5 `.uasset` in the flat dir, all mesh names |
| **B2** | A `Materials/Masters/` subfolder with **7** masters `M_XCOM_<Family>_Master` | `/Game/Enemies/XCOM/Materials/Masters/` | 7 files, names match `^M_XCOM_[A-Za-z]+_Master\.uasset$`, families == the 7-family list |
| **B3** | A `Materials/Instances/` subfolder with **24** instances `MI_XCOM_<PascalEnemy>_<FAMILY>` | `/Game/Enemies/XCOM/Materials/Instances/` | 24 files; per-enemy counts == §2.4; every instance's family normalises (§3.4) to a slot of **that same enemy** |
| **B4** | Every instance references a master that exists | same | no instance points at a missing master |
| **B5** | Every UE asset is **newer than or hash-linked to** its source FBX | `/Game/Enemies/XCOM/` | tracker C1 **and** C2 both pass; a `STALE` record is a hard fail |
| **B6** | Collision on all 5 meshes is `CTF_USE_COMPLEX_AS_SIMPLE`, read back from the asset — not assumed from the import setting | same | `collision_readback` contains `CTF_USE_COMPLEX_AS_SIMPLE` for all 5 in the ledger |
| **B7** | Every mesh's bound **height** matches the manifest height, within 2 % (or the discrepancy is recorded) | same | `abs(ue_height_cm - manifest_height_m*100) / 100 <= 0.02` or a note in the ledger |
| **B8** | The Floater's UE bounds height ≈ 1.14 m (0.29 m body + 0.9 m hover) and it has **no** ground-contact assumption | same | Floater height_cm 114.37, `has_ground_contact: false` preserved in the ledger |
| **B9** | No legacy v1 flat material asset remains in the flat folder | `/Game/Enemies/XCOM/` | no `XCOM_Chitin_*`, `XCOM_Armor_*`, `XCOM_Flesh`, `XCOM_Gunmetal`, `XCOM_Core_Emissive`, `XCOM_Eye_Emissive`, `XCOM_Plasma_Emissive` at the flat level; any survivor is an explicit `ORPHAN` in the ledger, not a silent leftover |

### 4.C Naming conformance

| # | Gate | Proof |
|---|---|---|
| **C1** | Zero `NAMING_VIOLATION` records | tracker C3 |
| **C2** | Every asset name in the tree matches exactly one pattern in §2.1/§2.2 | regex sweep over the whole `/Game/Enemies/XCOM` tree |
| **C3** | No asset uses the `XCOM_` prefix **and** a family token without a type prefix (`M_`/`MI_`/`T_`/`BP_`) — this is what caught `M_XCOM_Chitin` | the same sweep, flagging "type-prefix missing" |
| **C4** | No asset name contains a space, a dash, a dot (except `.uasset`) or a lowercase word boundary | character-class check |

### 4.D Kit completeness

| # | Gate | Proof |
|---|---|---|
| **D1** | Every enemy has a `BP_XCOM_<PascalEnemy>` blueprint | 5 blueprints in `/Game/Enemies/XCOM/Blueprints/` |
| **D2** | Every master that needs a baked map has `T_XCOM_<Family>_<Map>` in `/Game/Enemies/XCOM/Textures/` | every material master that references a texture has a matching `T_` asset; **or** the master is explicitly listed as "untextured-by-design" in the ledger, with the reason (e.g. emissive-only family) |
| **D3** | The kit renders in-engine with its material graph, not flat | a UE render of one enemy per family shows the material's intended surface response; until textures exist, the DoD for D3 is **"documented flat"**, not "textured" |
| **D4** | The reveal's five stings exist | `Content/Audio/SFX/SFX_XCOM_Reveal_<Enemy>.wav` × 5, non-empty, each ≤ 2 s (see TASK-03 §7.3) |
| **D5** | Every enemy has one encounter placement, and every placed actor label matches `XCOM_<PascalEnemy>_<nn>` | the level's actor list is swept against the pattern |

### 4.E Provenance and reproducibility

| # | Gate | Proof |
|---|---|---|
| **E1** | An import receipt exists for the current FBX hashes | `import_receipt.json` lists the sha256 of the FBX that produced the current UE assets; it matches the ledger's FBX hashes |
| **E2** | The receipt records per-enemy `source_fbx_tris`, `imported_tris`, `retention_pct`, `collision_readback`, `material` mapping | all five enemies have all six fields, non-null |
| **E3** | Triangle retention is understood, not just recorded | the report's own explanation is carried forward: the gap is **UE 5.8 import-time degenerate/duplicate removal on geometry assembled from joined primitives**, *not* a Blender export defect. Retention 39–91 % is therefore expected — a retention of ~100 % should be treated as suspicious, and a retention of 0 % as a failed import |
| **E4** | The tracker runs clean | `python Tools/python/track_xcom_assets.py --check` exits **0** and prints `verdict: PASS` |

### 4.F The DoD, as one line

> The X-COM enemy kit is **done** when `python Tools/python/track_xcom_assets.py --check` exits 0
> with `verdict: PASS`: five current FBX, five current UE meshes, seven masters, 24 instances,
> five blueprints, five stings, every name conforming, every link hash-provable, and the ledger
> on disk.

---

## 5. Current state against the DoD (measured 2026-10-21)

| Gate | State | Evidence |
|---|---|---|
| A1 | **PASS** | 5 FBX, `XCOM_Sectoid/Viper/Floater/Muton/Chryssalid.fbx` |
| A2 | **PASS** | 20 PNGs (4 per enemy), all non-empty |
| A3 | **PASS** | `xcom_manifest.json` — list of 5, `name` == stem |
| A4 | **PASS** | manifest tris 7308/5764/2184/5216/6252 match the FBX audit |
| A5 | **PASS** | 24 slots, names `XCOM_<Enemy>_<FAMILY>`, families from the 7-list (6 in use) |
| A6 | **FAIL** | no ledger exists at all |
| B1 | **PASS** | 5 mesh uassets in the flat folder (plus 11 material assets — see B9) |
| B2 | **FAIL** | no `Materials/Masters/` folder; one `M_XCOM_Chitin.uasset` (no `_Master` suffix) |
| B3 | **FAIL** | 0 `MI_` instances (need 24) |
| B4 | **FAIL** | no masters to point at |
| B5 | **FAIL** | **all five UE meshes are stale** — see below |
| B6 | **PASS (stale build)** | the *old* import recorded `CTF_USE_COMPLEX_AS_SIMPLE` for all 5, but it describes the old assets |
| B7 | **PASS** | UE heights 197.0 / 198.5 / 114.37 / 202.0 / 93.66 cm vs manifest 1.39 / 2.06 / 0.29+0.9 / 2.07 / 1.03 m |
| B8 | **PASS** | Floater 114.37 cm ≈ 0.29 + 0.9 hover; no ground contact |
| B9 | **FAIL** | 11 legacy flat assets sit in the flat folder: `XCOM_Chitin_Mid/_Pale/_Dark`, `XCOM_Armor_Plate/_Accent`, `XCOM_Flesh`, `XCOM_Gunmetal`, `XCOM_Core_Emissive`, `XCOM_Eye_Emissive`, `XCOM_Plasma_Emissive` |
| C1–C4 | **FAIL** | 11 naming violations (the 10 flat materials + `M_XCOM_Chitin`) |
| D1 | **FAIL** | no `Blueprints/` folder, no `BP_XCOM_*` anywhere in `Content/` |
| D2 | **FAIL** | no `Textures/` folder under `Content/Enemies/XCOM`; `Content/Textures` does not exist |
| D3 | **FAIL** | kit renders **flat** — FBX Texture count 0 in all five |
| D4 | **FAIL** | no `SFX_XCOM_Reveal_*` — `Content/Audio/SFX/` holds only 4 cues |
| D5 | **FAIL** | encounter labels in use are the Plymouth set (`ENC_Drone_01/02/03`, `ENC_Zealot_01/02`, `ENC_Phantom_01`, `ENC_Brute_Pit`, `ENC_Golem_Platform`, `ENC_Boss_NorEaster`) — none match `XCOM_<PascalEnemy>_<nn>` |
| E1 | **FAIL** | the receipt (import report, 04:41:30) describes the **old** FBX; no hash is recorded |
| E2 | **PASS (stale build)** | all six fields present for all five in the old report |
| E3 | **PASS** | retention explained in the report; expected range documented |
| E4 | **FAIL** | no tracker exists |

### 5.1 The staleness, precisely

| Enemy | FBX rebuilt | UE mesh written | Gap |
|---|---|---|---|
| `XCOM_Sectoid` | 04:24:27 | 01:13:31 | **3 h 11 m** |
| `XCOM_Viper` | 04:25:27 | 01:13:32 | **3 h 12 m** |
| `XCOM_Floater` | 04:26:13 | 01:13:32 | **3 h 13 m** |
| `XCOM_Muton` | 04:26:54 | 01:13:32 | **3 h 13 m** |
| `XCOM_Chryssalid` | 04:27:47 | 01:13:33 | **3 h 14 m** |

The UE meshes and the 10 flat material assets were all written in one import pass between
**01:04:13** and **01:13:33**. The FBX were rebuilt **04:24–04:27** with the v3 builder. The
import report is dated **04:41:30** — *after* the FBX rebuild, yet it still reports the **old
material names** (`XCOM_Chitin_Mid, XCOM_Chitin_Pale, XCOM_Chitin_Dark, XCOM_Eye_Emissive,
XCOM_Core_Emissive` for the Sectoid) and the old retention figures. **The report was regenerated
from the old import, not from a fresh import of the current FBX.** That is the specific defect
E1/E2 exist to catch.

**The one that must not be repeated:** the report's own `triangle_count_note` is right that the
39–91 % retention is UE-side import cleanup, not a Blender export defect. But the *material
names* in that report are v1 names that the current FBX no longer uses. A reader who trusts
"imported=5 failed=0" would conclude the kit is current. It is not.

### 5.2 The naming conflict that has to be settled

The current FBX slot names are `XCOM_Sectoid_CHITIN`, `XCOM_Muton_PLATE_OXBLOOD`, and so on —
**per-enemy** slots. The imported UE assets carry `XCOM_Chitin_Mid`, `XCOM_Chitin_Pale`,
`XCOM_Chitin_Dark`, `XCOM_Armor_Plate`, `XCOM_Armor_Accent`, `XCOM_Eye_Emissive`,
`XCOM_Core_Emissive`, `XCOM_Gunmetal`, `XCOM_Plasma_Emissive`, `XCOM_Flesh` — a **flat
family** set, i.e. the v1 scheme.

Note the mapping is **not** 1:1: the FBX has 24 per-enemy slots over 6 families; the flat UE
set is 10 materials over 5 coarse groups. A tracker that naively maps FBX slot → UE material by
name will find **zero** matches, and a tracker that maps by "family-ish" will find false ones.
The correct map is: **FBX slot `XCOM_<Enemy>_<FAMILY>` → UE instance
`MI_XCOM_<Enemy>_<FAMILY>` → UE master `M_XCOM_<Family>_Master`**, and the 10 legacy flat
materials are the **v1 ancestors** of those masters — they are inputs to the migration, not
targets.

### 5.3 What has to happen, in order

1. Write the tracker (`Tools/python/track_xcom_assets.py`) and generate the ledger. → A6, C1–C4
2. Re-import the five current FBX into `/Game/Enemies/XCOM` with the §2.2 paths, into
   `Materials/Masters/` and `Materials/Instances/`, producing 7 masters and 24 instances. → B2, B3, B4, B5, E1
3. Author the 7 masters in UE (or bake the textures) so the kit is not flat. → D2, D3
4. Retire the 10 legacy flat material assets **after** the masters exist. → B9
5. Build the 5 blueprints. → D1
6. Synthesise the 5 reveal stings. → D4
7. Re-point the encounter placements at `XCOM_<PascalEnemy>_<nn>` labels. → D5
8. Re-run `track_xcom_assets.py --check` → **exit 0**.

---

## 6. Conflicts reported, not fixed

### 6.1 The roster does not contain these enemies

`Docs/generated/weapons_enemies_v1.json` currently defines six **Plymouth eldritch** creatures —
`e_01 Barnacle Drone`, `e_02 Pilgrim Zealot`, `e_03 Mayflower Phantom`, `e_04 Lobster Brute`,
`e_05 Rock Golem`, `e_06 Nor-Easter Titan` — with **zero overlap** with the five X-COM
originals this kit is built from. `TASK-04` (swarm-w4) lists **17 flagged conflicts**, including
weapon-damage disagreements across **three separate sources**.

**What the tracker depends on:** the enemy list is the set of five X-COM names (§1). If the
roster is reconciled *away* from the X-COM five, the tracker, the naming spine and the DoD all
have to be re-pointed together. The tracker must read the enemy list from **one** place — the
ledger's `enemies` array — so that a roster change is a one-line edit rather than five.

### 6.2 `target_height()` would mis-scale every alien

`Tools/python/populate_encounters.py::target_height(label)` returns 300 for `ENC_NorEaster`,
160 for `ENC_Brute`, 150 for `ENC_Golem`, 60 for `ENC_Drone`, 180 for any other `ENC_`, 40 for
`PU_`, 60 for `WP_`, and **100 otherwise**. Those are Plymouth-roster values, and the X-COM
enemies have no `ENC_` label of their own, so they would silently fall to the 100 uu default.

**What the tracker depends on:** gate **B7** compares the UE bound height against the
**manifest** height, never against `target_height()`. The manifest is authoritative. If a future
lane re-points the meshes, `target_height()` must not be used for the X-COM five.

### 6.3 The Floater's pivot sits on the floor

The Floater's pivot is at floor level, so it must spawn at **+100 cm** and levitate. Its
manifest entry says `has_ground_contact: false`, `hover_clearance_m: 0.9`; its UE bounds height
is 114.37 cm, consistent with a 29 cm body riding 90 cm of hover. **B8** exists to make sure
that stays true through a re-import — a Floater re-imported with a corrected pivot would read
29 cm and fail B8, which is the intended signal, not a nuisance.

### 6.4 No bloom in the engine

`Config/DefaultEngine.ini` sets `r.DefaultFeature.Bloom=False` (with `AutoExposure=False`,
`AmbientOcclusion=False`, `MotionBlur=False`, `Projector=False`), and **no PostProcessVolume
asset exists in `Content/`**. The emissive materials (`XCOM_Eye_Emissive`,
`XCOM_Core_Emissive`, `XCOM_Plasma_Emissive`) will therefore have no glow in game. For the
asset tracker this is one row: if a bloom PPV is added for the reveal, **D3's in-engine render
must be re-taken with the PPV active**, because bloom changes how the emissive families read.

### 6.5 The rig is drifting under the kit

`Tools/blender/rig_evidence.py` is being edited by another lane (source last modified 07:33:40,
after the 07:33:03 render the lighting evidence comes from). The kit tracker and the lighting
tracker are separate concerns, but the *render* side of the DoD (D3) is affected: any in-engine
render used as DoD evidence must be pinned to a generation stamp, because
`Tools/blender/out_lighting/` is **not tracked by git** and can be replaced without a diff.
See TASK-03 §13.

---

## 7. Source index

| Fact | Source |
|---|---|
| Naming spine, folder tree, FBX stem = UE asset name rule | `CommandCenter/outputs/swarm-w2/TASK-07_ue_import_pipeline.md` §2 |
| FBX hashes, triangle counts, dimensions, flags | `Tools/blender/out_xcom/xcom_manifest.json` + direct sha256 of the FBX |
| FBX material slot names, Texture/Video/Deformer counts | binary scan of `Tools/blender/out_xcom/*.fbx` |
| UE import results, retention, collision readback, material lists | `CommandCenter/outputs/ue_import/xcom_ue_import_report.md`, `Docs/generated/xcom_ue_import_report.json` |
| Current UE asset inventory and mtimes | `Content/Enemies/XCOM/` (16 `.uasset`, 01:04–01:13) |
| Roster conflicts (17), encounter labels, `e_01`–`e_06` | `CommandCenter/outputs/swarm-w4/TASK-04_roster_integration.md`, `Docs/generated/weapons_enemies_v1.json` |
| `target_height()` normaliser | `Tools/python/populate_encounters.py` |
| Reveal stings, bloom | `CommandCenter/outputs/swarm-w3/TASK-03_reveal_effect_spec.md` §7, `Config/DefaultEngine.ini` |
| Rig drift | `Tools/blender/rig_evidence.py` git diff; TASK-03 §13 |
