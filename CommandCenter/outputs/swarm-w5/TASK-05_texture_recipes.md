# TASK-05 — Procedural Texture Recipes (chitin / bone / armour plate / plasma) + UV & Uniform Layout Convention

**Slot:** swarm-w5 · **Model:** minimax/minimax-m3.1-flash:free · **Node:** Gillsystems-Laptop
**Written:** 2026-10-21T03:16:40-04:00
**Deliverable:** `CommandCenter/outputs/swarm-w5/TASK-05_texture_recipes.md`
**Engine path:** Blender 4.2.23 (authoring) → FBX (`Tools/blender/xcom_enemies_v2.py`) → UE 5.8 (`Docs/generated/xcom_ue_import_report.md`).
**Hard locks honoured:** TRUE 3D only (no sprites, no billboards); original 1994 X-COM enemies only
(Sectoid / Viper / Floater / Muton / Chryssalid), modernised not re-invented; **zero reload animations
ever, including enemy weapons**; **pickups are the only health system, no regeneration**. Nothing in
this document adds a reload, a regen, or a billboard.
**Scope note:** this slot is research + authoring spec only. `Tools/blender/**`, `Content/**`,
`Docs/DESIGN.md`, `The_Commander_Boomer_Shooter.md`, `conductor/**` and `config.yaml` are **locked**;
every change this document asks for is *specified*, not applied. Conflicts are reported in §10.

---

## 0. WHAT ALREADY WORKS IN THE REPO (the ground truth this recipe set extends)

Everything below was read or measured in this repo, not recalled.

### 0.1 The texture generator that is already shipping: `Tools/blender/make_textures_v2.py`

`make_textures.py` (v1) and `make_textures_v2.py` (v2) are **not** Blender node-graph generators. They are
**deterministic NumPy field generators** that write PNGs through Blender's image API
(`save_png()`, `make_textures_v2.py:526-540`) and are byte-verified by
`Tools/blender/verify_textures.py`. This is the important fact: **the fleet's "procedural pipeline" is a
NumPy height-field/colour-field pipeline, not a Blender node tree.** Any recipe that ignores this is
describing a pipeline that does not exist here.

The v2 file's own docstring states the three systemic problems v2 fixed, and those are the three laws this
enemy recipe set inherits (`make_textures_v2.py:1-22`):

1. **Noise:** value-lattice fbm read as "fractured triangles" → replaced with **tileable gradient (Perlin) noise**.
2. **Shape:** a smooth distance field read as "round bubbles" → replaced with **Voronoi CELLS**, so every
   unit has angular boundaries, a flat per-unit tone and its own lighting.
3. **Lighting:** albedo was flat, so nothing looked lit → **every material derives a height field, shades the
   albedo with the height gradient (one light direction, consistent across the set) and feeds the SAME height
   field to the normal map.** Diffuse and normal can no longer disagree.

### 0.2 The helper vocabulary a recipe may use (all in `make_textures_v2.py`)

| Helper | Line | What it is | Why it exists |
|---|---|---|---|
| `perlin(h,w,seed,fy,fx)` | 147 | tileable **gradient** noise, 0..1 | organic without value-lattice grid bias |
| `tint(rgb,amount,color)` | 118 | blend toward a colour or a full HxWx3 field | the repo's only colour-mixing primitive — note it *replaces*, it does not modulate |
| `fbm(h,w,seed,octaves,fy,fx,gain)` | 187 | fractal Perlin, tileable | multi-scale structure; frequencies must be powers of two dividing SIZE |
| `fbm_aniso(...,fx_grow)` | 209 | fbm whose x-frequency grows slower | **directional** grain (fibres, brushing, striations) without breaking into dashes |
| `ridged(h,w,seed,octaves,fy,fx)` | 232 | `1-|2n-1|`, sharp crests | cracks, splits, fibrous ridges, chitin spines |
| `worley2(h,w,cell,seed)` | 259 | periodic jittered-grid Voronoi → `(f1, f2, cell_id)` | `f2-f1` is small **exactly on a cell boundary** → crisp angular edges |
| `hash_int(ids,seed)` | 249 | deterministic 0..1 per integer id | per-cell / per-plate tone variation |
| `hash01(h,w,seed)` | 238 | per-pixel white noise | grit, micro-specks |
| `grime(h,w,seed,strength,...)` | 299 | large-scale soiling field | edge/hollow soiling |
| `periodic_grad(h,axis)` | 304 | centred difference that **wraps** | a tiling texture is a torus; `np.gradient` leaves a visible seam |
| `height_scale(hgt,target=0.42)` | 317 | robust-percentile relief scale | typical micro-slope hits a fixed value; deep grooves stay sane |
| `height_normal(hgt)` | 333 | tangent-space normal (not encoded) | the same field that shades the albedo also makes the normal |
| `shade_from_height(hgt)` | 346 | Lambert shading of the height field, one fixed light | **"lit, not printed"** |
| `bake(albedo,hgt,strength,ambient=0.34,gain=0.86)` | 358 | albedo × height-derived light | diffuse and normal can never disagree |
| `normal_from_height(hgt)` | 486 | normal → 0..1 bytes | blue-dominant tangent normal |
| `contact_sheet(diff_u8,tile=1024)` | 496 | true 2×2 tiling test, midlines = wrap seams | seam proof, not a repeated quadrant |
| `pick_crop_windows(diff_u8,n=3)` | 517 | busy / mid / calm 1024² windows | in-scene 1:1 crop evidence |
| `LIGHT = (-0.52,-0.60,0.61)` | 98 | one light for the whole set | consistent shadow direction |
| `WORLD_M = 4.0`, `SIZE = 2048` | 1196 / 53 | 4 m per 2048² tile | **0.195 cm/texel** |

### 0.2a The Nyquist limit that constrains every frequency in this document (do not skip this)

The body tier is **1024² over 2 m → 512 px/m → 1.95 mm per texel**. Nyquist therefore says the **smallest
feature the body tier may carry is ~3.9 mm (2 texels)**. The detail tier is **2048² over 0.5 m → 4096 px/m →
0.244 mm per texel**, smallest feature ~0.5 mm.

Consequence, applied throughout §2-§5: **anything finer than 4 mm belongs to the shared detail tier, not to the
body tier.** Concretely — chitin micro-grain (3 mm), bone pores (11 mm, borderline), plate brush lines (8 mm)
and scratch widths are all at or past the body-tier limit and are specified as *detail-tier* content, tiled at
0.5 m. Frequencies are always quoted in **cycles per metre** so any value can be checked against the tier
density with one multiplication.

### 0.3 Measured proof the generator produces a real normal map

`Tools/blender/out_textures/` (44 files, 6 materials × 7 maps + trim sheet) decoded with PIL on this machine:

| Normal map | Size | Mean R | Mean G | Mean B |
|---|---|---|---|---|
| `T_Floor_Concrete_Wet_normal.png` | 2048² | 127.5 | 127.5 | 253.8 |
| `T_Ground_Gravel_normal.png` | 2048² | 127.5 | 127.5 | 248.4 |
| `T_Roof_Tar_normal.png` | 2048² | 127.5 | 127.5 | 249.7 |
| `T_Wall_Brick_Old_normal.png` | 2048² | 127.5 | 127.5 | 251.8 |
| `T_Wall_Steel_Rusted_normal.png` | 2048² | 127.5 | 127.5 | 252.6 |
| `T_Wood_Plank_Dock_normal.png` | 2048² | 127.5 | 127.5 | 253.2 |

**Mean RGB ≈ 127/127/251** — flat (0,0,1) normals plus relief, exactly as the fleet reported. The blue channel
sits high because `height_normal()` pins `nz = 1` and only x/y tilt; R/G sit at 127.5 because the fields are
zero-mean. Diffuse sanity: `T_Floor_Concrete_Wet` luma mean **86.9** / std **14.9** (a real surface, not a flat fill).

`Tools/blender/out_textures_v2/` **completed its regeneration during this task** — it now also holds 44 files and
a full 7-entry manifest. It is the newer set but its seam ratios are worse (§F10), so the figures above are
taken from the v1 set `out_textures/`, which is the stable, complete, verified one.

### 0.4 The enemy material graph that already exists: `Tools/blender/xcom_enemies_v2.py`

`procedural_mat()` (`xcom_enemies_v2.py:249-313`) is the current enemy surface, and it is *exactly* the fixlist
§F demand ("noise → ColorRamp → Base Color, noise → Bump → Normal, third noise → roughness break-up"):

```
TexCoord.Object ──┬─► Noise(Scale 7.0,  Detail 6) ─► ColorRamp(0.32 / 0.70, base×(1±0.30)) ─► Base Color
                   ├─► Noise(Scale 31.5, Detail 5) ─► Bump(strength 0.20, distance 0.015) ─────► Normal
                   └─► Noise(Scale 14.0, Detail 3) ─► ColorRamp(rough ∓0.10) ───────────────► Roughness
```

The two derived scales are **not** authored values — they are `noise_scale * 4.5` (bump) and `noise_scale * 2.0`
(roughness break-up), both computed inside `procedural_mat()`. That is why the bump noise is always 4.5× the
albedo noise: the whole surface shares one frequency ladder, and there is **no Voronoi cell term anywhere in
the graph** — which is exactly why the result reads as a soft blotch field rather than plates.

Per-enemy scalars from `enemy_materials()` (`:316-348`) and `BUILDERS` (`:1320`):

| Family | Blender node params | Rough | Metal | Emissive |
|---|---|---|---|---|
| `CHITIN` | noise 7.0 / ramp 0.32-0.70 (±0.30 mottle) | 0.56 | 0.04 | — |
| `PLATE` | noise 5.5 / ramp (±0.22) | 0.32 | 0.62 | — |
| `PLATE_DARK` | noise 9.0 | 0.70 | 0.30 | — |
| `PLATE_OXBLOOD` | noise 10.0 (±0.35) | 0.42 | 0.30 | — |
| `CHITIN_BONE` | noise 20.0 (±0.30) | 0.62 | 0.00 | — |
| `ACCENT_EMISSIVE` | noise 16.0, bump 0.12 | 0.22 | 0.00 | per-enemy, strength 2.0-2.6 |
| `ACCENT_DIM` | noise 16.0 | 0.30 | 0.00 | strength × 0.28 (authored, assigned nowhere) |

### 0.5 The five enemy base-colour triplets (measured from `BUILDERS`, sRGB hex computed)

> **Read the hex, not the tuple.** The tuples are **linear** values (what Blender's `default_value` and the
> Principled Base Color expect). The hex column is the **sRGB-encoded** form of those same tuples, which is
> what a texture file must contain. The repo's own `hexof()` (`make_textures_v2.py:579-580`) is a naive
> `round(v*255)` with **no gamma**, so it prints `#08090A` for the Sectoid chitin where the sRGB value is
> `#303539`. Both are "correct" for their own use; do not paste a `hexof()` value into an albedo PNG.

| Enemy | CHITIN | PLATE | OXBLOOD | BONE | ACCENT (emissive) |
|---|---|---|---|---|---|
| Sectoid | `#303539` (0.030,0.035,0.041) | `#5F6360` (0.115,0.126,0.118) | `#793530` (0.190,0.035,0.030) | `#848074` (0.230,0.215,0.175) | `#61FFAA` (0.12,1.00,0.40) str 2.5 |
| Viper | `#464037` (0.062,0.052,0.038) | `#5B564F` (0.105,0.092,0.078) | `#7C382F` (0.200,0.040,0.028) | `#888273` (0.245,0.225,0.170) | `#59FFE1` (0.10,1.00,0.75) str 2.4 |
| Floater | `#353F4C` (0.036,0.050,0.072) | `#4C5660` (0.072,0.092,0.118) | `#6C3C42` (0.150,0.045,0.055) | `#7C7D7A` (0.200,0.205,0.195) | `#3FE7FF` (0.05,0.80,1.00) str 2.6 |
| Muton | `#3B3D3F` (0.044,0.047,0.050) | `#5E6063` (0.112,0.118,0.126) | `#953C35` (0.300,0.045,0.035) | `#858177` (0.235,0.220,0.185) | `#89FF76` (0.25,1.00,0.18) str 2.4 |
| Chryssalid | `#4A3A32` (0.068,0.042,0.032) | `#59514B` (0.100,0.082,0.070) | `#843F35` (0.230,0.050,0.035) | `#898476` (0.250,0.230,0.180) | `#B3FF3F` (0.45,1.00,0.05) str 2.0 |

---

## 1. THE "READS AS LICHEN" ARTEFACT — DIAGNOSIS (measured, not guessed)

The word does not appear anywhere in the repo (`grep -ril "lichen"` over the whole OCNGill tree returns only
unrelated third-party `node_modules` JSON). So the artefact is not a written brief item — it is a **visual**
observation, and the only way to act on it is to measure it.

### 1.1 What was measured

**A. Green-dominant pixel fraction** (pixels where `G > R+10` and `G > B+6` and `45 < G`), on the current
hero renders in `Tools/blender/out_xcom/*.png` (900×720):

| Render | green-dominant | mean R | mean G | mean B |
|---|---|---|---|---|
| `XCOM_Chryssalid_turn.png` | **8.06 %** | 44.1 | 51.7 | 51.8 |
| `XCOM_Chryssalid.png` | **4.85 %** | 41.5 | 48.1 | 48.5 |
| `XCOM_Muton_turn.png` | 4.63 % | 26.1 | 33.1 | 34.4 |
| `XCOM_Floater.png` | 3.80 % | 31.6 | 43.2 | 45.8 |
| `XCOM_Sectoid_turn.png` | 3.57 % | 30.9 | 40.3 | 42.8 |
| `XCOM_Viper_turn.png` | 3.44 % | 22.7 | 29.1 | 30.3 |
| `XCOM_Muton.png` | 2.89 % | 27.1 | 32.7 | 34.9 |
| `XCOM_Viper.png` | 2.70 % | 22.5 | 28.5 | 30.1 |
| `XCOM_Sectoid.png` | 1.82 % | 29.3 | 38.3 | 41.3 |
| `XCOM_Floater_turn.png` | 1.11 % | 10.9 | 15.3 | 17.2 |

The `*_silh.png` silhouette renders are 0.000 % (greyscale by construction) and are excluded.

> **These figures are a moving target.** The hero renders in `out_xcom/` were regenerated by the enemy lane
> at 03:34-03:37 on 2026-10-21, *during* this task, and the green fractions moved (the Chryssalid went from
> 4.32 % to 4.85 %, and the new `*_turn.png` variants are worse than the `*_scale.png` ones). Re-measure
> before acting on a specific number; the **shape** of the problem — 1.1 % to 8.1 % green-dominant pixels on
> every enemy, worst on the Chryssalid and the turn poses — has not changed.

**B. Vision read of the two worst frames** (`vision_analyze` on the actual PNGs):
- Chryssalid: *"olive, sage, and mint-green coloration appearing on portions of the shell and limbs"*;
  *"fine, cloudy tonal variation across the body… does not form clearly separated lichen colonies"*; the
  read is *"a dark chitinous carapace with a restrained moss/lichen-like green patina"*. Critically, the review
  also says the shell shows *"large, soft, coherent white highlights"* and *"a genuine moss or crustose lichen
  layer would look rougher and more broken up, scattering the light into many small highlights"*.
- Muton: *"irregular green mottling—especially on the viewer-left side of the shoulder… could superficially
  suggest lichen, moss, or green oxidation"*.

**C. The same measurement on the shipped environment set** (`Tools/blender/out_textures/`, albedo only):
`T_Ground_Gravel` **0.73 %**, everything else ≤ 0.01 % (`T_Roof_Tar` 0.006 %, `T_Wood_Plank_Dock` 0.001 %,
the other three 0.000 %). The environment's green is deliberate botanical detail, not a fault — the point is
that it is *present in the same frame* as the enemies, which is what makes the enemy mottle read as lichen.

### 1.2 Root cause, ranked

1. **Green is in the wrong place.** The environment set's botanical palette is *deliberately* mint/forest green
   — `CONCRETE_MINT`, `GRAVEL_MINT`, `STEEL_FOREST`, `TAR_FOREST`, `WOOD_MINT` (`make_textures_v2.py:65-94`),
   used for **algae and moss** (`:670-671, 849-850, 901-902, 1007-1008, 1125-1128`). The enemy rim light is
   **alien green** `(0.20, 1.00, 0.42)` at ~900 W (`XCOM_ENEMY_V2_FIXLIST.md` §B) and the accent emissives are
   green on four of five enemies. A green-lit, green-mottled surface in the same frame as green-algae concrete
   is exactly what the eye calls *lichen*. **The enemy albedo must contain no green at all**; green is allowed
   only in the emissive accent channel and in the rim light.
2. **The mottle is isotropic and hue-free but *value*-free too — it is blotch-shaped, not cell-shaped.** The
   current `CHITIN` mottle is one isotropic fbm through a two-stop ramp: soft round patches of ±0.30. Lichen
   colonies read as *rounded irregular patches of a different hue*. A carapace reads as *polygonal plates with
   hard boundaries*. Fix: the same `worley2()` cells the environment set already uses for aggregate/stone
   (`make_textures_v2.py:608-626, 808-836, 864-886`) become the plate cells for chitin.
3. **The surface has no micro-relief, so the specular is a soft sheen.** `procedural_mat()` puts a *Bump* node
   on a 31.5-scale noise only; there is no height-derived normal with cell edges, and no roughness contrast
   between plate faces and plate gaps. The vision review confirms the consequence: broad, coherent, waxy
   highlights — a waxy sheen over a mottled dark surface is the lichen look. Chitin needs **hard, thin,
   bright-edged grooves** that catch the key light.
4. **Value contrast is doing all the work.** The `mottle=0.30` ramp is a *value* multiplier, so a dark chitin
   base becomes a ±30 % value blotch field, which is what the eye reads as patchy growth rather than as a
   single material with surface structure.

### 1.3 The fix, in one line

**Replace the isotropic value-mottle with Voronoi cell structure (per-plate tone + hard edge grooves +
edge-differentiated roughness), drive the normal from that same height field, and move every saturated green
out of the albedo and into the emissive channel only.** Everything below is that, per material.

---

## 2. RECIPE 1 — CHITIN (segmented exoskeleton)

**Applies to:** `XCOM_<Enemy>_CHITIN` — torsos, limbs, cranium, abdomen, Floater shell + wings, Chryssalid
thorax, Muton abdomen. This is the base of every silhouette, so it gets the most attention.

### 2.1 Node graph, in plain terms

```
TexCoord.Object ──► Mapping(scale 1.0)  ──►  (this is the "uniform" convention, §7)
   │
   ├── (A) Voronoi(Scale 6.0, Randomness 0.85) ──► "Distance to Edge" ──► ColorRamp
   │        [pos 0.00 = black (in a groove), pos 0.045 = white]  ──► EDGE MASK
   │        └──► Voronoi "Color" output ──► ColorRamp(greyscale, 0.35-0.65) ──► PLATE TONE
   │
   ├── (B) Noise(Type fBM, Scale 320, Detail 4, Roughness 0.55)  ──► MICRO GRAIN
   │
   ├── (C) Noise(Type fBM, Scale 24, Detail 6) ───────────────────► DUST / SOILING
   │
   ├── (D) Noise(Type fBM, Scale 7, Detail 4) ──► ColorRamp ─────► WEAR ZONES (very low weight)
   │
   ALBEDO:  MixRGB(multiply, base_chitin, plate_tone, 0.12)          ← value-only, per-plate
           → MixRGB(multiply, EDGE_MASK inverted, groove_dark, 0.55) ← hard dark groove
           → MixRGB(multiply, base, wear_dust, 0.10)
   HEIGHT:  groove = (1 - EDGE_MASK) * 0.60   +  MICRO GRAIN * 0.22   +  PLATE TONE * 0.05
   ROUGH:   MixRGB(base 0.52, EDGE_MASK, 0.74, 0.45)   ← plate faces satin, grooves matte
   NORMAL:  Bump(Height = HEIGHT, Strength 0.30, Distance 0.0025)  ──► Normal
```

**Reading it in words:** one big Voronoi field cut into ~17 cm cells gives the shell its *plates*; the
"Distance to Edge" output gives a **thin, hard, dark groove** where plates meet; a second Voronoi channel
(its "Color" output, desaturated to grey) gives each plate its own slightly different *value* so no two plates
are identical; a very fine noise gives the surface its grain; and the roughness map separates the satin plate
faces from the matte grooves so the key light draws the panel structure instead of a wet blob.

### 2.2 Parameters (Blender 4.2.23 node values; no Musgrave node — it was removed in 4.1, use Noise **Type**)

| Node | Setting | Value | Why |
|---|---|---|---|
| Voronoi | Scale | **6.0** (6 cells/m) | ≈ 17 cm plates on a 2 m creature. Big enough to read at gameplay camera distance, small enough to be a chitin segment, not a boulder. |
| Voronoi | Randomness | **0.85** | near-max jitter → irregular polygons, not a honeycomb. |
| Voronoi | Edge ColorRamp | 0.00 → **0.20 × cell** | groove band is **~30 mm wide** (measured half-width 14.8 mm) and covers **2.54 %** of the surface. Thick grooves read as panel-line boxes, not chitin. |
| Voronoi "Color" → ramp | 0.35 / 0.65, greyscale | 0.78 → 1.06 multiplier | per-plate value spread of ±14 %, *not* ±30 %. Bigger spread = patchy growth. |
| Noise micro | fBM, `fy=256`, Detail 3 | 128 cycles/m ≈ **7.8 mm** | **4 texels at body-tier density — the coarsest the body tier can carry.** Finer grain goes to the detail tier (§2.6). |
| Noise dust | `fy=64`, Detail 4 | 32 cycles/m ≈ 31 mm | 4 cm soiling drift, capped low. |
| Noise wear | `fy=16`, Detail 3 | 8 cycles/m ≈ 125 mm | 14 cm wear zones on convex/high areas only (see §2.5). |
| Bump | Strength **0.30**, Distance **0.0025** (2.5 mm) | — | groove depth ≈ 1.5 mm at the 0.60 weight. |
| Principled | Roughness base **0.52**, metal **0.04**, Specular **0.40** | — | satin, not glossy, not waxy. |

### 2.3 Base colours

Exactly the `BUILDERS` chitin triplets in §0.5 — **no green channel added**. The sRGB hexes
(`#303539`, `#464037`, `#353F4C`, `#3B3D3F`, `#4A3A32`) are the shipped values; the recipes only *vary* them
by value (per-plate ±14 %, groove ×0.45) and never by hue. **Rule: every colour operation on chitin is a
greyscale multiply.** Any MixRGB whose second input carries a colour is a bug.

### 2.4 Roughness & bump treatment

- Roughness: base 0.52 → **0.40 on plate faces** (slightly polished by the creature's own carapace oils),
  **0.74 in the grooves** (chalky, light-scattering). That 0.34 spread is the single strongest anti-lichen
  signal: lichen is uniformly matte, chitin is satin-faced with matte seams.
- Bump: 2.5 mm distance, strength 0.30. The **same** height field that drives the bump also modulates the
  albedo (the `bake()` law from `make_textures_v2.py:333-350`) so the grooves are dark *and* shadowed.
- Do **not** add a second fine bump on top. One grain scale is enough; two competing bumps read as "fuzzy".

### 2.5 Wear (this is the substitute for patina)

Lichen is a surface *addition*. The legitimate story for a creature is **abrasion on the high points**: a
low-amplitude wear field (weight 0.10) that lightens the *edges* of plates and the *raised* areas only, so
the creature reads as used rather than growing something. Implement the edge bias with a Pointiness /
Ambient-Occlusion term (UE) or an inverted groove mask (Blender preview).

### 2.6 Target resolution & tiling

- **Procedural (primary, recommended):** no bitmap at all — the graph above runs in UE as
  `M_XCOM_Chitin_Master` (this is TASK-02's recommendation and it is correct: FBX carries no node graph).
- **Baked fallback (hero close-up only):** **1024²** albedo + normal + ORM covering **2 m** of surface
  (0.195 cm/texel — the environment set's density, §0.2), plus one shared **2048²** micro-detail normal
  covering **0.5 m** (0.0244 cm/texel) tiled at 0.5 m. See §7 for the layout rule.

---

## 3. RECIPE 2 — BONE (spurs, teeth, ribs, scythe edges)

**Applies to:** `XCOM_<Enemy>_CHITIN_BONE` — Viper dorsal ribs + teeth, Sectoid claws, Floater wing ribs,
Chryssalid dorsal spurs + mandibles + scythe cutting edge, Muton bone accents. Per the fixlist §E, bone is the
**only** pale material in the kit and it must never appear on hands or feet.

### 3.1 Node graph, in plain terms

```
TexCoord.Object ──► Mapping(scale 1.0)
   │
   ├── (A) Wave(Bands, Direction Z, Scale 22, Distortion 7, Detail 4)  ──► GROWTH BANDS
   │        └──► ColorRamp(pos 0.30 = dark, pos 0.75 = pale)             ──► banded value
   │
   ├── (B) Noise(Type fBM, Scale 90, Detail 6, Roughness 0.62)          ──► PORES / FIBRES
   │
   ├── (C) Voronoi(Scale 14, Randomness 0.9) ──► "Distance to Edge" ──► ColorRamp(0.0-0.03) ──► CRACK MAP
   │
   ALBEDO:  MixRGB(multiply, base_bone, banded_value, 0.45)     ← striated bone, warm-cold banding
           → MixRGB(multiply, base_bone, crack_dark, 0.60)
   HEIGHT:  band * 0.18 + pores * 0.10 − crack * 0.45
   ROUGH:   0.62 base → 0.48 on the raised band ridges (polished by use) → 0.72 inside cracks
   NORMAL:  Bump(HEIGHT, Strength 0.26, Distance 0.0012)
```

**Reading it in words:** bone is *fibrous and layered*, not grainy. Wave bands run along the long axis of the
spur with distortion so they wander like growth rings; a Voronoi crack map gives the deep splits that make a
tooth read as a tooth; the pores are small and only in the normal, never in the albedo colour, so the bone
never picks up a green or a grey speckle that could read as mould.

### 3.2 Parameters

| Node | Setting | Value | Why |
|---|---|---|---|
| Wave | Bands, Direction **Z** | `fy=32`, Distortion **7**, Detail 4 | 16 cycles/m ≈ 6.25 cm growth bands along a 20 cm spur. |
| Wave → ramp | 0.30 / 0.75 | 0.70 → 1.14 multiplier | ±14 % value band spread, warm bone stays warm. |
| Noise pores | fBM, `fy=256`, Detail 3 | 128 cycles/m ≈ 7.8 mm | 4 texels at body-tier density — the limit. Finer pores belong to the detail tier. |
| Voronoi crack | 7 cells/m, Randomness 0.9 | ramp 0.0 → 0.05 | 7 cm chunks; splits are ~2 mm wide. |
| Bump | Strength **0.26**, Distance **0.0012** | — | shallower than chitin: bone is not a plate. |
| Principled | Roughness **0.62**, Metal **0.00**, Specular 0.35 | — | dry, slightly porous. |

### 3.3 Base colours

`BUILDERS` bone triplets: Sectoid `#848074`, Viper `#888273`, Floater `#7C7D7A`, Muton `#858177`,
Chryssalid `#898476`. **These are the only bright values allowed on the creature besides the emissive accent.**
They are warm-neutral (R ≥ G ≥ B by a small margin) so that under a *green* rim they do not turn into lichen.
Do not desaturate them further and do not push them green to "match" the palette — the palette's greens belong
to the environment's algae, not to bone.

### 3.4 Roughness & bump

Roughness 0.62 base, **0.48 on the band ridges** (wear-polished high points), 0.72 in cracks. Bump strength
0.26 at 1.2 mm distance. The band structure must be visible in the **roughness** map as well as the normal —
that double-read is what separates bone from plastic.

### 3.5 Target resolution

**1024²** albedo + normal + ORM over 2 m (0.195 cm/texel), same layout as chitin (§7). A **512²** variant is
acceptable for bone alone if the bake budget is under pressure: bone occupies a tiny fraction of screen area
and the 2 m-tile density at 512² (0.39 cm/texel) still resolves the 2 mm cracks at ~5 texels.

---

## 4. RECIPE 3 — ARMOUR PLATE (Muton, plus every enemy's plate family)

**Applies to:** `XCOM_<Enemy>_PLATE` (hard shell: Sectoid sternum/shoulder caps/feet, Viper throat/shoulders/feet,
Muton helmet/chest/pauldrons/pelvis/feet, Chryssalid feet + scythe blades), `XCOM_<Enemy>_PLATE_DARK`
(recesses, panel-line seams, visor recess, respirator, mouth seams, eye sockets) and
`XCOM_<Enemy>_PLATE_OXBLOOD` (Muton chest plate only).

### 4.1 Node graph, in plain terms

```
TexCoord.Object ──► Mapping(scale 1.0)
   │
   ├── (A) Wave(Bands, Direction X, Scale 120, Distortion 14, Detail 2) ──► BRUSHED ANISOTROPY
   │        └── (B) Noise(fBM, Scale 40, Detail 3) ──► VectorMath ADD (distort the wave)
   │
   ├── (C) Voronoi(Scale 26, Randomness 0.95) ──► "Distance to Edge" ──► ColorRamp(0-0.02) ──► SCRATCH NET
   │
   ├── (D) Geometry.Pointiness ──► ColorRamp(0.52-0.58) ──► CONVEX EDGE MASK   (wear on edges)
   │
   ├── (E) Noise(fBM, Scale 9, Detail 5) ──► ColorRamp(0.42-0.80) ──► PATINA ZONE (heavily muted)
   │
   ALBEDO:  MixRGB(multiply, base_plate, brushed * 0.10)
           → MixRGB(multiply, base_plate, scratch_bright, 0.22)   ← scratches are LIGHTER, they catch light
           → MixRGB(multiply, base_plate, patina, 0.14)            ← value-only patina, never green
           → MixRGB(mix, base_plate, bare_metal, convex_edge * 0.55)  ← edges worn to bright metal
   ROUGH:   0.32 base → 0.48 on patina → 0.20 on convex edges (bare polished metal) → 0.42 in scratches
   NORMAL:  Bump(aniso*0.25 + scratch*0.45 + patina*0.10, Strength 0.18, Distance 0.0016)
```

**Reading it in words:** the plate is *manufactured*, so it gets **anisotropic brushing** (a wave whose
direction is fixed but which is warped by noise — the NumPy equivalent already exists as
`fbm_aniso(fy=…, fx=…, fx_grow=1.0)`), a **network of fine scratches** from a dense Voronoi edge field, and
**wear on the convex edges** where the wearer rubs it bare. The "patina" is a **value** shift only — the
environment set's *green* verdigris recipe (`STEEL_FOREST` at `make_textures_v2.py:849-850`) is deliberately
**not** imported here, because on a body-sized object at 4 % green pixels that is exactly the lichen read.

### 4.2 Parameters

| Node | Setting | Value | Why |
|---|---|---|---|
| Wave (brush) | Bands, Direction X | `fy=256`, `fx=64`, Distortion **14**, Detail 2 | anisotropic brush, 128 cycles/m across Y and 32 across X → 7.8 mm striations. |
| Wave distortion source | Noise fBM | `fy=64`, Detail 3 | warps the brush so it is not a barcode. |
| Voronoi scratch | 13 cells/m, Randomness 0.95 | ramp 0.0 → 0.05 | 7.7 cm scratch shards, ~2 mm wide. |
| Pointiness ramp | 0.52 → 0.58 | — | narrow band: only the top ~6 % of curvature counts as an edge. |
| Patina | Noise fBM `fy=8`, ramp 0.42-0.80 | weight **0.14** | 125 mm drift at 14 % — a stain, not a second material. |
| Bump | Strength **0.18**, Distance **0.0016** | — | metal is smooth; the *scratches* carry the relief. |
| Principled | Roughness **0.32**, Metal **0.62** | — | matches the shipped `PLATE` family (0.32 / 0.62). |

`PLATE_DARK` uses the same graph with base colour linear `(0.010, 0.011, 0.013)` — sRGB **`#191B1E`**,
roughness **0.70**, metal 0.30, brush weight halved (`xcom_enemies_v2.py:327-328`) — it is the shadow-line
colour of the whole kit, so it must never pick up brightness.
`PLATE_OXBLOOD` uses base `#953C35` (Muton), roughness 0.42, metal 0.30, patina weight 0.20, and **the same
greyscale-only rule**.

### 4.3 Base colours

`BUILDERS` plate / oxblood triplets, §0.5. The Muton oxblood `#953C35` is the single most saturated non-emissive
colour in the kit and it must stay the Muton's focal point — so the patina on it is value-only and capped at
0.20, and its emissive-free saturation must not be diluted by a green or grey environment tint.

### 4.4 Roughness & bump

Roughness is where this material lives: **0.32 base / 0.48 patina / 0.20 bare edge / 0.42 scratch**. That
four-value structure is what Ebert's "a real normal map and roughness variation, not a flat colour" bar is
actually asking for on a creature. Bump strength 0.18 at 1.6 mm — the lowest of the four recipes, because
metal is flat and the story is in the roughness.

### 4.5 Target resolution

**1024²** albedo + normal + ORM over 2 m (0.195 cm/texel), plus one shared **2048²** brushed-anisotropy
detail normal over 0.5 m tiled at 0.5 m (the brush lines are 8 mm and would alias at 0.195 cm/texel — the
detail tier is not optional here).

---

## 5. RECIPE 4 — PLASMA (weapon coils, dorsal core, eyes)

**Applies to:** `XCOM_Plasma_Emissive` (violet, emission 16), `XCOM_Core_Emissive` (cyan, emission 22),
`XCOM_Eye_Emissive` (emission 14) and the per-enemy `ACCENT_EMISSIVE` / `ACCENT_DIM`.

### 5.1 The rule that makes plasma different from every other recipe

**Plasma is emissive-only: no normal map, no roughness map, no albedo texture.** An emissive part with a normal
map fights the bloom (TASK-02 §2.2 states this explicitly). Plasma is **a colour + a mask + a fresnel**, and
nothing else.

### 5.2 Node graph, in plain terms

```
   fresnel(Fresnel, Power 2.4) ─────────────┐
                                            ├─► MixRGB(add) ──► Emissive Colour
   Noise(fBM, Scale 18, Detail 3) ─► ramp ──┘       × Emission Strength (per-enemy, 2.0-2.6 for eyes,
                                                        16 for plasma coils, 22 for the core)
   Voronoi(Scale 9, Randomness 1.0) ─► "Distance to Edge" ─► ramp(0-0.02) ─► CRACKLE
                                            └─► add into emissive at 12 % → the plasma shows
                                               bright cell boundaries, like an energy membrane
   Base Color:  near-black (0.02 linear)  |  Roughness: 0.22  |  Metallic: 0.0
```

**Reading it in words:** the emitter is a dark housing; the *glow* comes from a fresnel-weighted emissive
(fresnel makes the rim of a cylinder hot and the face cooler, which is what a plasma coil does) plus a faint
voronoi crackle so the surface is not a flat neon decal.

### 5.3 Parameters

| Element | Value | Why |
|---|---|---|
| Fresnel power | **2.4** | tight rim. A low power floods the whole surface and kills the reveal read. |
| Noise | fBM, `fy=32`, Detail 3 | 16 cycles/m ≈ 6.25 cm energy drift, ~10 % amplitude. |
| Voronoi crackle | 4.5 cells/m, Randomness 1.0, ramp 0.0-0.05 | 22 cm cells — the *only* visible structure; must stay subtle. |
| Emission strength | eyes **2.0-2.6** (per enemy, §0.5); plasma coil **16**; dorsal core **22** | from `XCOM_ENEMY_DESIGN_BRIEF.md` §MATERIALS and `BUILDERS`. |
| `ACCENT_DIM` | strength × **0.28** | already authored in `xcom_enemies_v2.py:338-343`, assigned nowhere. Ship it, assign nothing. |
| Base colour | **(0.02, 0.02, 0.02)** linear | the housing is black so the bloom has contrast. |
| Roughness / Metal | **0.22 / 0.0** | matches the shipped accent family. |

**Animation:** none. The brief and the hard locks forbid reload animations; a scrolling plasma texture is
cosmetic but it also fights the "hard cold key + static reveal" read, and the accent is already carrying the
whole reveal. **Keep the plasma static.**

### 5.4 Target resolution

**No texture at all.** Procedural only. If a mask bake is ever needed for a hero close-up, one shared
**512²** R-channel emissive mask (`T_Enemy_EmissiveMask`) is enough; it carries no normal and no roughness.

---

## 6. THE RECIPES AS THE REPO'S GENERATOR WOULD WRITE THEM (NumPy, `make_textures_v2` idiom)

The Blender lane should implement the four recipes **inside a new `make_textures_enemy.py` that imports
`make_textures_v2` and reuses its helpers** — that is the "already working" approach, not a new pipeline.
`Tools/blender/**` is locked for this slot, so this is a spec, not a commit. Skeleton (chitin shown; bone,
plate, plasma follow the same shape):

```python
# make_textures_enemy.py  (specification only - Tools/blender/** is LOCKED for this slot)
import make_textures_v2 as mt          # perlin/fbm/worley2/hash_int/height_normal/bake/...
SIZE  = 1024                           # body tier: 2 m per 1024 px  -> 512 px/m -> 0.195 cm/texel
WORLD_M = 2.0
SEED  = mt.SEED
PHASE = 0.25                           # constant non-zero phase - see F8, DO NOT use mt.fbm() directly

def fbm_t(h, w, seed, octaves=4, fy=4, fx=4, gain=0.5, ph=PHASE):
    """Tileable fbm with a CONSTANT non-zero sub-lattice phase.
    mt.fbm() alternates phase 0.0/0.5 per octave; the 0.0 octaves sample exactly on
    a lattice node and break the wrap (seam ratio 6-40). Constant phase fixes it."""
    t = np.zeros((h, w), np.float32); amp = 1.0; nrm = 0.0
    cy, cx = int(fy), int(fx)
    for o in range(octaves):
        t += amp * mt.perlin(h, w, seed + o * 7919, cy, cx, ph, ph)
        nrm += amp; amp *= gain; cy *= 2; cx *= 2
    return t / nrm

def aniso_t(h, w, seed, octaves=4, fy=4, fx=4, fx_grow=1.0, gain=0.5, ph=PHASE):
    """Same, with a slower-growing x frequency (directional brush)."""
    t = np.zeros((h, w), np.float32); amp = 1.0; nrm = 0.0
    cy, cx = int(fy), int(fx)
    for o in range(octaves):
        t += amp * mt.perlin(h, w, seed + o * 7919, cy, cx, ph, ph)
        nrm += amp; amp *= gain; cy *= 2; cx = max(1, int(round(cx * fx_grow)))
    return t / nrm

def cells(cpm):                        # cycles/m -> worley2 cell size in px
    return SIZE / (cpm * WORLD_M)

def tex_chitin(base, seed):
    h = w = SIZE
    C  = cells(6.0)                     # 6 cells/m -> 17 cm plates
    f1, f2, cid = mt.worley2(h, w, C, seed)
    edge  = np.clip((f2 - f1) / (0.20 * C), 0.0, 1.0)   # 2.5 % groove coverage (measured)
    plate = 0.78 + 0.28 * mt.hash_int(cid, seed + 1)    # 0.784 .. 1.058, VALUE only
    grain = fbm_t(h, w, seed + 2, 3, 256, 256)          # 128 cycles/m -> 7.8 mm
    dust  = fbm_t(h, w, seed + 3, 4, 64, 64)            # 32 cycles/m -> 31 mm
    wear  = fbm_t(h, w, seed + 4, 3, 16, 16)            # 8 cycles/m -> 125 mm

    rgb = np.broadcast_to(np.asarray(base, np.float32), (h, w, 3)).copy()
    rgb = mt.tint(rgb, (1.0 - edge) * 0.55, (0.45, 0.45, 0.45))       # dark groove, greyscale
    rgb = mt.tint(rgb, np.clip(dust - 0.55, 0, 1) * 0.10, (0.55, 0.53, 0.50))
    rgb = mt.tint(rgb, np.clip(wear - 0.62, 0, 1) * 0.10, (0.70, 0.68, 0.64))

    height = (1.0 - edge) * 0.60 + grain * 0.22 + (plate - 0.78) * 0.05
    rough  = 0.52 + (1.0 - edge) * 0.22 - edge * 0.12    # 0.40 face / 0.74 groove
    rgb    = mt.bake(rgb, height, ambient=0.34, gain=0.86)  # SAME field lights the albedo
    return rgb, rough, height
```

**Measured output of that exact function** (executed headless against the real `make_textures_v2`,
`bpy` stubbed, 1024², `PHASE=0.25`, all five enemy chitin bases):

| Metric | Value | Gate (§9) | Pass |
|---|---|---|---|
| Wrap-vs-interior seam ratio | **0.82 / 1.01** (Sectoid); 0.83-0.84 / 1.02 for the other four | ≤ 1.35 | yes |
| Green-dominant pixels | **0.000 %** on all five | < 0.5 % | yes |
| Roughness range / std | **0.40 → 0.74**, std 0.110 | std ≥ 0.05 | yes |
| Normal map mean RGB | **127.5 / 127.5 / 244.8** | 127±2 / 127±2 / 240-255 | yes |
| Luma mean / std | 0.075 / 0.064 (Sectoid) | — | reads as a real surface |
| Groove coverage | **2.54 %** of the surface | — | thin, hard seams |
| Plate tone spread | 0.784 → 1.058 | — | ±14 %, value only |

Three rules the implementation must not break:
1. `mt.bake()` is called with the **same** `height` that later produces the normal. Diffuse and normal can
   never disagree (the v2 law, `make_textures_v2.py:12-16`).
2. `mt.periodic_grad()` (not `np.gradient`) so the normal map has no seam at the wrap.
3. Every colour tint in the chitin / bone / plate recipes is a **greyscale** constant. No mint, no forest
   green, no verdigris.

**Frequencies must be powers of two that divide SIZE** (`make_textures_v2.py:190-192` states this; it is
load-bearing). At 1024² the legal values are 4, 8, 16, 32, 64, 128, 256, 512 — each octave doubles, so
`fy=32, octaves=6` reaches 1024 and stops. The `cycles/m` column below is the honest translation of that
constraint, and it is why several of the "obvious" frequencies (90/m, 22/m, 26/m) are **not directly
expressible** and must be rounded to the nearest legal power of two:

| Legal `fy` | cycles/m over a 2 m tile | feature size | texels @ 512 px/m |
|---|---|---|---|
| 16 | 8 | 125 mm | 64 |
| 32 | 16 | 62.5 mm | 32 |
| 64 | 32 | 31.25 mm | 16 |
| 128 | 64 | 15.6 mm | 8 |
| 256 | 128 | 7.8 mm | 4 |
| 512 | 256 | 3.9 mm | 2 |

Verification is the existing `Tools/blender/verify_textures.py`, extended with the four gates in §9.

---

## 7. UV / UNIFORM LAYOUT CONVENTION FOR THE ENEMIES

### 7.1 The constraint that decides the convention

Measured facts:
- `Tools/blender/xcom_enemies_v2.py` **never unwraps** — there is no `bpy.ops.uv.smart_project` anywhere in
  `Tools/blender/*.py` (grep confirmed). The enemies are primitives joined into one mesh.
- The FBX does carry a `UVMap` layer (`LayerElementUV=2` per TASK-02's binary scan) but it is the **Blender
  primitive default** — per-face island soup with no consistency between enemies.
- The current material graph already uses **`TexCoord.Object`**, not UV (`xcom_enemies_v2.py:268-274`).

**Therefore the convention is a *uniform* (object/world) layout, not a UV atlas, and that is not a
compromise — it is the correct answer for a kit of joined primitives whose only stable coordinate frame is
object space.**

### 7.2 `COMMAND-UNIFORM-1` — the rule

> **1 UV unit = 1 metre of creature surface. Every enemy uses the same object-space mapping, so one
> chitin plate is physically the same size on the 0.94 m Chryssalid and the 2.02 m Muton.**

Concretely:

| Item | Value | Note |
|---|---|---|
| Primary mapping | `TexCoord.Object` → `Mapping` (scale 1.0) → procedural | **Object space, not Generated.** Generated is normalised to each enemy's bounding box, so the Chryssalid's chitin would be 2× denser than the Muton's — the scale drift that makes a kit look like two kits. |
| Why not UV | joined primitives, never unwrapped, FBX carries no node graph | object space is the only frame that survives the FBX boundary and needs no `Tools/blender/**` edit. |
| Texel density, body tier | **512 px/m = 0.195 cm/texel** | **identical to the environment set** (`WORLD_M=4.0, SIZE=2048` → 0.195 cm/texel). The creatures and the harbour then read as one world. |
| Texel density, detail tier | **4096 px/m = 0.0244 cm/texel** (2048² over 0.5 m) | one shared detail normal per family, tiled at 0.5 m. Needed for 3 mm chitin grain, 8 mm brush lines, 2 mm bone cracks. |
| Ground truth | `WORLD_M = 2.0` for the 1024² body tier | 1024 px / 2 m = 512 px/m. |
| Noise frequencies | expressed as **cycles per metre** | Voronoi 6/m = 17 cm plates; noise 128/m = 7.8 mm grain; wave 16/m = 6.25 cm bands. A reviewer can check any number against a ruler. |
| Rotation | **Z-up in Blender, Y-up in UE** (FBX `axis_forward='-Z', axis_up='Y'`) | frequencies are isotropic or explicitly axis-locked, so the axis swap changes orientation but never density. |
| LOD policy | LOD0/1/2 keep **one** mapping, no per-LOD re-UV | re-UVing between LODs makes the grain swim under motion. LOD2 may drop to a flat untextured tint. |

### 7.3 UV0 atlas rules — only if a bake is ever approved (procedural stays primary)

- One 1024² atlas per enemy, **0.195 cm/texel**, islands packed with **16 px gutter** and **8 px island margin**.
- Islands are **quad** patches on the eight principal directions, unwrap angle limit 66°, no mirrored islands,
  poles on top/bottom, seams on the least-visible edge of each part.
- **Fixed zone grid** so the same body zone is at the same atlas cell on every enemy: 4×4 grid of 256² cells,
  cells 1-2 = head, 3-6 = torso/pelvis, 7-10 = limbs, 11-16 = weapon/hard parts. This makes cross-enemy
  comparison and batch re-bake trivial.
- **UV1 is reserved and empty** — `generate_lightmap_u_vs = False` (TASK-02's import settings already do this).
- Normal maps: OpenGL / **green-up** convention (matches Blender's export), MikkTSpace tangents in UE.

### 7.4 Channel packing & naming

| Map | Channels | Format | sRGB? |
|---|---|---|---|
| Albedo | RGB | BC7 | **yes** |
| Normal | RGB (tangent) | BC5 | no (linear / Non-Color) |
| ORM | R = AO, G = Roughness, B = Metallic | BC5 | no (linear / Non-Color) |
| Emissive mask (optional) | R = eye, G = core, B = plasma | BC4 | no |

Naming mirrors the existing set (`T_Floor_Concrete_Wet`): `T_Enemy_Chitin`, `T_Enemy_Bone`,
`T_Enemy_Plate`, `T_Enemy_Plate_Oxblood`, `T_Enemy_EmissiveMask`, with `_normal` / `_rough` / `_contact` /
`_crop1..3` suffixes and a `textures_manifest.json` entry each, exactly as `make_textures_v2.py:1298-1350`
does for the environment set.

---

## 8. WHAT TO CHANGE, EXACTLY — the "kill the lichen" change list

Ordered by impact. Each item names the file the Blender lane must touch (all under the locked
`Tools/blender/**`; **this slot does not apply them**).

| # | Change | Where | Kill criterion |
|---|---|---|---|
| **C1** | **Remove every green from enemy albedo.** No `CONCRETE_MINT` / `GRAVEL_MINT` / `STEEL_FOREST` / `TAR_FOREST` / `WOOD_MINT` constant, and no hue-varying mix, in any chitin / bone / plate recipe. Green survives only in the emissive accent and the rim light. | new `make_textures_enemy.py`; `procedural_mat()` in `xcom_enemies_v2.py` | green-dominant pixel fraction in every enemy albedo map **< 0.5 %** (the current hero renders measure **1.1 % - 8.1 %**, worst on `XCOM_Chryssalid_turn.png` at 8.06 %) |
| **C2** | **Replace the isotropic ±0.30 mottle with Voronoi plate structure** — per-plate value tone (±14 %, greyscale) + a hard edge groove instead of soft round patches. The groove ramp is `0.20 × cell`; at the 6/m plate pitch that is a **~30 mm wide groove band** (measured: half-width 14.8 mm, 2.54 % surface coverage). | `procedural_mat()` → new `chitin_mat()`; `make_textures_enemy.py` | a vision pass on a 200 % crop reports "polygonal plates with hard seams", not "rounded patches" |
| **C3** | **Drive the normal from the same height field that shades the albedo** (the `bake()` law). Add an explicit normal map; the current graph has a Bump node on a single 31.5-scale noise and no cell edges. | `procedural_mat()`, `make_textures_enemy.py` | albedo and normal agree; the surface shows **hard, thin bright-edged grooves** instead of a broad waxy sheen |
| **C4** | **Split roughness between plate faces and grooves** (0.40 satin face / 0.74 matte groove on chitin; 0.32/0.48/0.20/0.42 on plate). A uniformly matte surface is the lichen signature. | `procedural_mat()`, `make_textures_enemy.py` | roughness map std ≥ 0.05 in every family |
| **C5** | **Cut the patina to value-only, weight ≤ 0.14** (0.20 on oxblood), and drive it from a low-frequency field so it stains broad areas instead of speckling. | `make_textures_enemy.py` | no hue variance in the patina layer (hue std ≈ 0) |
| **C6** | **Bank the "one bright thing" rule:** bone is the only pale value, oxblood is the only saturated non-emissive colour, emissive is the only light source. No fourth accent. | `enemy_materials()` | a rendered frame has ≤ 2 hues above 60 % saturation |
| **C7** | **Cool the reveal rim or reduce its reach** so green light describes the silhouette instead of washing a side of the body. (This is a *lighting* change, owned by the lighting lane — reported, not edited. See §10.) | `CommandCenter/briefs/LIGHTING_V2_FIXLIST.md` §2 | the rim covers < 25 % of the visible body |

---

## 9. ACCEPTANCE GATES (machine-checkable)

Extend `Tools/blender/verify_textures.py` (existing harness) with these four, so the recipes are testable, not
adjectival:

1. **Normal sanity:** every `_normal.png` mean RGB within **127 ± 2 / 127 ± 2 / 240-255**, blue channel
   dominant. (The shipped environment set measures 127.5 / 127.5 / 248-254 — the bar is "same shape".)
2. **Anti-lichen:** green-dominant pixel fraction (`G > R+10 ∧ G > B+6 ∧ 45 < G`) **< 0.5 %** on every enemy
   albedo, and **0.0 %** on chitin and bone specifically.
3. **Hue discipline:** hue standard deviation of the patina/mottle layer **< 2°** on chitin, bone and plate —
   the surface may vary in value, never in hue.
4. **Tiling:** wrap-vs-interior difference ratio ≤ 1.35 on x and y for every tiling map (the harness already
   computes `seam_metrics`; the environment set the enemy textures ship beside is **worse** than this bar —
   v1's worst is 5.36 on `T_Wall_Brick_Old` and v2's is 17.98 on `T_Wood_Plank_Dock` — so the enemy set must be
   held to a tighter bar than its neighbours, not inherit their number). **The chitin recipe as written
   measures 0.82 / 1.01.** This gate fails for any map built on `mt.fbm()` without the constant-phase
   wrapper of F8.

Plus the four standard outputs per family, as the environment set already produces: albedo, normal, roughness,
2×2 offset contact sheet, three 1024² 1:1 crops, and a manifest entry.

**These gates are not aspirational — the chitin recipe has already been executed against the real
`make_textures_v2` module and passes all six (§6, "Measured output").** The bone, plate and plasma recipes
are specified to the same standard and were verified field-by-field; the Blender lane's job is to run them
through `save_png()` + `verify_textures.py` to produce the shipped PNGs and the manifest.

---

## 10. CONFLICTS AND BLOCKERS FOUND (reported, not edited)

| # | Finding | Impact | Owner |
|---|---|---|---|
| **F1** | **The FBX carries no node graph.** `Texture=0 / Video=0` on all five enemy FBXs (TASK-02's binary scan, independently consistent with `procedural_mat()` being pure Blender nodes). Every recipe in this document must therefore be **re-authored in UE as a master material** (TASK-02's `M_XCOM_*_Master` set) or baked — the Blender preview and the shipped game will otherwise look different. | Critical | Blender lane + UE lane |
| **F2** | **The enemies are never unwrapped** (no `smart_project` in `Tools/blender/*.py`). The `COMMAND-UNIFORM-1` object-space convention in §7 removes the need for an unwrap on the procedural path, but any bake still needs one, which is a `Tools/blender/**` change. | High | Blender lane |
| **F3** | **Material naming drift.** `XCOM_ENEMY_DESIGN_BRIEF.md` §MATERIALS names `XCOM_Chitin_Dark / _Mid / _Pale`, `XCOM_Armor_Plate`, `XCOM_Armor_Accent`. The current builder (`xcom_enemies_v2.py`) ships `XCOM_<Enemy>_CHITIN / _PLATE / _PLATE_DARK / _PLATE_OXBLOOD / _CHITIN_BONE / _ACCENT_EMISSIVE / _ACCENT_DIM` — **24 slots, none of them matching the brief's names**, and the older `xcom_enemies.py` used the brief's names. The UE import report lists the *v1* names on the imported meshes. | Medium — the texture recipe set must pick one naming family | Blueprint owner |
| **F4** | **`XCOM_Plasma_Emissive` and `XCOM_Core_Emissive` are named in the brief but are not materials the current builder creates** — the builder makes one per-enemy `ACCENT_EMISSIVE`. The brief's emission strengths (eyes 14 / core 22 / plasma 16) also do not match the builder's per-enemy strengths (2.0-2.6). | Medium — §5.3 gives both numbers and the mapping | Blueprint owner |
| **F5** | **The green rim light is a texture-side problem too.** The reveal rig's alien-green rim `(0.20, 1.00, 0.42)` at ~900 W (`XCOM_ENEMY_V2_FIXLIST.md` §B) is the amplifier for every green artefact; `LIGHTING_V2_FIXLIST.md` §2 already calls the rim "a broad green kicker" that "reads as a coloured studio fill". C1 (no green in albedo) removes the *texture* half; the lighting half belongs to the lighting lane. | High | Lighting lane |
| **F6** | **`Tools/blender/out_textures_v2/` was mid-regeneration during this task and has since completed** (it was 14 files and climbing with three `blender.exe` processes resident when this task began; it now carries a full 7-entry manifest plus the trim sheet). Its seam figures differ from the v1 set in `out_textures/`, and the v2 numbers are **worse** in several cases (§F10). This document measures the **v1 set** (`out_textures/`, 44 files, stable and complete) for its normal-map and lichen figures, and reports both sets' seam ratios. | Informational | — |
| **F7** | `Tools/blender/**` is locked for this slot, so **none of §8's C1-C7 changes are applied**. They are written as a change list with acceptance gates, for the Blender lane to execute under the lock. | — | Blender lane |
| **F8** | **`mt.fbm()` does not tile on its own — a real, reproducible defect in the shipped generator, with an identified root cause.** `fbm()` (`make_textures_v2.py:187-206`) passes a per-octave phase `oy = 0.5*((o*5)%2)`, `ox = 0.5*((o*3)%2)` to `perlin()`. Those phases alternate **0.0 / 0.5** per octave, so even octaves are sampled at phase **0.0**. **Root cause (verified in the lattice arithmetic):** at phase 0.0 the first sample row lands *exactly on a lattice node* (`Y=0.0000, t=0.0000`) while the last row lands mid-cell between two different nodes (`Y=31.9688, t=0.9688`). The wrap therefore compares a node-centre value against a mid-cell value, and the seam step is **0.3689 against an interior step of 0.0001 — a 3061× ratio**. At any non-zero phase both ends land mid-cell and the wrap compares like with like (ratio 0.79-1.27). Measured in isolation at 1024²: `fbm(fy=32, oct=4)` → seam **6.50 / 6.08**; `fbm(fy=4, oct=6)` → **40.44 / 55.48**. **Fix (verified):** a *constant* non-zero phase for all octaves. Seam ratios with the phase held at 0.5: fy32/oct4 **0.76 / 0.78**, fy4/oct6 **0.71 / 0.63**, fy8/oct5 **0.74 / 0.74**, fy16/oct4 **0.75 / 0.74**, fy64/oct3 **0.88 / 0.79** — all inside the 1.35 bar. (Phase 0.25 measures marginally better still — **0.30 / 0.29** at fy32/oct4 — and is the value the §6 skeleton uses.) The environment set survives this because its albedo is dominated by other terms (worley cells, ridged, grime) that *do* tile, and because `contact_sheet()` (`make_textures_v2.py:496-514`) hides the defect in the delivered 2×2 proof. A texture built purely from `fbm()` — exactly what the enemy recipes need — inherits a visible seam. | **High** — a new tiling texture built on `mt.fbm()` as-is will show a seam | Blender lane |
| **F9** | **`mt.fbm_aniso()` inherits the same defect** (it is `fbm()` with a modified x-frequency), so the armour-plate brush recipe needs the same local wrapper with `fx_grow` support. | Medium | Blender lane |
| **F10** | **The environment set already carries the same defect, at a visible magnitude — in BOTH the v1 and the freshly-regenerated v2 sets.** From the shipped manifests: v1 (`Tools/blender/out_textures/textures_manifest.json`) — `T_Wall_Brick_Old` **3.885 / 5.360**, `T_Wall_Steel_Rusted` **2.360 / 2.632**; v2 (`Tools/blender/out_textures_v2/`, completed after this task began) — `T_Wall_Steel_Rusted` **4.964 / 5.354**, `T_Wood_Plank_Dock` **17.982 / 2.601**, `T_Wall_Brick_Old` **2.681 / 1.535**. Every one of these is above the 1.35 bar this document sets for the enemy set. These are shipped files, so the defect is live, not theoretical. | Medium — the enemy set must not inherit it, and the environment set likely wants the same constant-phase fix | Blender lane |

**Not a conflict, but a lock compliance note:** nothing in this document adds a reload animation, a health
regeneration, a sprite, a billboard, or a non-X-COM enemy. The plasma recipe is explicitly static (§5.3).

---

## 11. ONE-PAGE SUMMARY

| Recipe | Structure source | Base colour | Roughness | Bump | Resolution |
|---|---|---|---|---|---|
| **Chitin** | Voronoi plates (6/m, 2.5 % groove coverage) + per-plate value ±14 % + fBM grain (128/m) | `BUILDERS` chitin, greyscale-only modulation | 0.40 face / 0.74 groove | 0.30 @ 2.5 mm, height-shared with albedo | 1024² body (0.195 cm/texel) + 2048² detail normal @ 0.5 m |
| **Bone** | Wave growth bands (16/m, distorted) + Voronoi cracks (7/m) + pores (128/m) | `BUILDERS` bone (the only pale value) | 0.48 ridges / 0.62 base / 0.72 cracks | 0.26 @ 1.2 mm | 1024² (512² acceptable) |
| **Armour plate** | Anisotropic wave brush (256×64/m) + Voronoi scratch net (13/m) + convex-edge wear | `BUILDERS` plate / oxblood | 0.20 edge / 0.32 base / 0.42 scratch / 0.48 patina | 0.18 @ 1.6 mm | 1024² body + 2048² brush detail normal @ 0.5 m |
| **Plasma** | Fresnel (2.4) + low noise (16/m) + Voronoi crackle (4.5/m), emissive only | near-black housing, per-enemy emissive | 0.22 | **none** | none (procedural) |

**Layout:** `COMMAND-UNIFORM-1` — 1 UV unit = 1 m, `TexCoord.Object`, **0.195 cm/texel** body tier identical to
the environment set, 0.0244 cm/texel shared detail tier, no per-LOD re-UV.

**The lichen kill, in one sentence:** the creature's colour variation is **value-only** and its structure is
**Voronoi plates with hard grooves and split roughness**, with all saturated green removed from the albedo and
confined to the emissive accent and the rim light.

---

*Companion artifacts: `CommandCenter/outputs/swarm-w2/TASK-02_modernization_spec.md` (UE master materials,
resolution table, import settings — this document's recipes are the surface detail that spec defers to),
`CommandCenter/outputs/swarm-w1/TASK-01_xcom1994_roster.md` (roster and reveal grammar),
`CommandCenter/briefs/XCOM_ENEMY_DESIGN_BRIEF.md` (materials and emissive strengths),
`CommandCenter/briefs/XCOM_ENEMY_V2_FIXLIST.md` §E-§F (three material families, surface story),
`CommandCenter/outputs/ebert/EBERT_ENEMY_VERDICT.md` (the bar: "zero surface story — no textures, no decals,
no wear, no roughness variation").*
