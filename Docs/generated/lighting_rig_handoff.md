# Lighting Rig Handoff — XCOM Reveal Lighting

**Lane:** lighting / reveal rig. **Script:** `Tools/blender/rig_evidence.py`.
**Renderer:** Blender 4.2.23, EEVEE, 720×900, 48 samples, AgX view transform
(`VIEW_TRANSFORM = 'AgX'`), exposure 0.0, world background strength 0.10.

**Status:** the rig clears most of the contract on the four large creatures.
**Muton and Viper read 10/13 with zero clipped pixels.** Every number below
is measured from the rendered PNGs by the same code that renders them, and
re-measured independently by a pure-Python PNG reader with no Blender in the
loop (`--verify`), which agrees to the digit.

**How the rig is applied:** ONE global rig, plus a small set of per-subject
knobs fitted **by measurement** inside the same render path that delivers
the frame. There is no separate probe rig: an earlier version had three
paths answering for one creature (the probe read `clipW 2267` on the Viper,
the delivered frame `630`, the parity frame `146`). A score computed on a
rig nobody ever sees is fiction, so everything now goes through
`render_rig_frame()`.

---

## 1. The rig — every value, with its file and line

All in `Tools/blender/rig_evidence.py`. Line numbers are from the current
file; the constants are grouped at the top.

### 1.1 Global constants

| Value | Line | Setting | Why it is that value |
|---|---|---|---|
| `VIEW_TRANSFORM` | 67 | `'AgX'` | Filmic roll-off. Standard hard-clipped a 4700 W rim to 255; AgX rolls it off. **The criteria must be measured on the transform you ship.** |
| `REF_HEIGHT` | 130 | `1.0` | Reference size. Distances scale with the subject's **largest dimension** and power with its square, so illuminance is proportional for every enemy. |
| `CAM_AZ` | 71 | `305.0` | Camera bearing. Everything else is relative to it. |
| `CAM_COVER` | 73 | `2.35` | Camera distance as a multiple of subject size. |
| `CAM_H` | 74 | `0.62` | Camera eye height as a multiple of subject **height**. |
| `BAND_PX` | 68 | `2` | The silhouette-edge band the rim band/frac criteria measure. |
| `GROUND_ALBEDO` | 156 | `0.18` | Dark wet concrete. |
| `WORLD_STRENGTH` | 158 | `0.10` | Near-black backdrop. |
| `HAZE_STRENGTH` | 157 | `0.003` | Backdrop gradient panel. |
| `EMIT_STRENGTH` | 153 | all `0.010` | The accent emissive. Was 0.19 and blew out; the emissive was carrying more of the rim band than the rim itself was. |
| `PROOF_EMIT_SCALE` | 154 | `2.0` | Multiplier for the emissive-only proof frame. |

### 1.2 The five lights — geometry

| Light | Type | Colour | Line | Geometry |
|---|---|---|---|---|
| `reveal_key` | **Spot** | (0.62, 0.78, 1.00) | 77–78 | az 262°, el 42°, dist 1.00·size, cone **40°** (`KEY_SPOT`). A 40° cone keeps the floor at 0; 90° floods it to 187/176/164. |
| `reveal_rim` | **Spot** | (0.03, 1.00, 0.12) | 80, 90 | az **240°** (fitted per subject, 190–240), el 20°, dist 1.10·size, cone **45°** (`RIM_CONE`), aimed at 0.55·size. **The cone is not optional:** an Area light has no cone, floods its whole hemisphere and lights the floor behind the creature no matter where it is aimed. |
| `reveal_under` | **Spot** | (0.45, 0.90, 1.00) | 101–102 | 0.06·size in front of the feet, 0.022·size up, cone **34°** (`UNDER_CONE`), aimed at `under_aim` (fitted, 0.12–0.20·size). |
| `reveal_pool` | **Spot** | (0.52, 0.72, 1.00) | 108–109 | az 145°, el 70°, dist 1.30·size, cone **22°**, aimed at the floor 0.35·size toward camera. |
| `reveal_wash` | **Area** | (0.45, 0.55, 0.70) | 128–129 | az 300°, el 55°, 1.20·size, size 1.20·size. The only ambient term; shadow-free. |

### 1.3 The five lights — energy (rig units, before the size scale)

| Light | Line | Value |
|---|---|---|
| `self.key` | 1600 | **260** |
| `self.rim` | 1601 | **4000** |
| `self.under` | 1602 | **2400** |
| `self.pool` | 1603 | **90** |
| `self.wash` | 1604 | **1.2** |

Actual Blender watts = `value × max(0.45, (size / REF_HEIGHT)²) × exposure`.
The `0.45` floor is what lets the smallest creatures still register.

### 1.4 The per-subject knobs (all fitted by measurement)

| Knob | Line | Range swept | What it moves |
|---|---|---|---|
| `self.rim_az` | 1625 | 190, 220, 240° | The rim's bearing. **The under-to-torso ratio is driven by this, not by the under's own aim or power** (probe6: the under ratio swings 0.05→2.44 on rim azimuth alone). |
| `self.exposure` | 1619 | 0.6, 1.0, 1.6 | Everything. The body fills a different fraction of frame at each size, so this is what makes the five read alike. |
| `self.wash_gain` | 1627 | 1.0, 3.0 | The floor only, not the body. This is the lever for a subject whose floors are too dark. |
| `self.rim_gain` | 1626 | 1.0, 2.0, 3.0 | The rim alone. The band is the top failure on all five; the clipping headroom this buys is the only way to raise it. |
| `self.under_gain` | 1628 | 1.0, 2.0, 4.0 | The under alone. The under-to-torso ratio is exposure-invariant, so it needs its own knob. |
| `self.under_aim` | 1611 | 0.12, 0.20 | Where the under points, as a fraction of size. |

The fit is three stages, all inside `do_enemy()`:
azimuth → (exposure × wash_gain × rim_gain) → (under_gain × under_aim).
The scorer is `score_of()` and it is the **contract**, not a soft preference:
band, fraction, clipping, background, floor window, floor contrast and both
under ratios all count.

### 1.5 The per-subject overrides that are hand-set

| Enemy | Override | Reason |
|---|---|---|
| XCOM_Viper | `wash = 1.6` | background_darkness read 43.1 against a bar of 40 |
| XCOM_Muton | `wash = 1.6`, `emissive_scale = 0.70` | background 45.1; clipping 1271 |
| XCOM_Sectoid | `emissive_scale = 0.55` | clipping 2568 — the emissive, not the light |
| XCOM_Floater | `under_cone = 45°`, floor probes spread | a 20–34° cone is smaller than the creature |

---

## 2. The three measurements that are proven, and how

**Mode parity.** `--parity` renders one rig through the probe path and the
delivered path and prints both. They now agree exactly on all five
(clipW 146, clipB 146, clipC 2, bg 24.1, band 116.9, frac 0.0503). The
earlier 429-vs-2765 gap was the Fog Glow compositor being on for the
delivered frame and off for the probe, plus the probe measuring with no
emissive mask. Fixed by routing both through `render_rig_frame()`.

**Emissive isolation.** The `*_emissive_only.png` frames are rendered with
**no scene lights at all** — the emissive materials and a Fog Glow pass
only. They are the proof that the emissive contribution is real and
separate from the rig.

**Side by side.** `*_studio_vs_reveal.png` puts the flat studio rig (broad
area key + green fill, world 0.60) next to the reveal rig in the same
frame, so the difference is visible rather than asserted.

---

## 3. What still fails, and the exact change to make

### 3.1 `rim_band_mean_ge_120` — the band is 26–104 against a bar of 120

**Fails on all five.** The band is the 2-pixel silhouette edge. The emissive
was carrying much of it: when the emissive came down from 0.19 to 0.010 the
band fell, which is why the rim needs raising now that the clipping
headroom exists (four of five read zero clipped pixels).

**The change:** raise `self.rim_gain` (line 1626) — the fit sweeps it to
3.0. If the band is still short, raise the sweep ceiling to 4.0, and if it
still will not clear 120, raise `self.rim` (line 1601) from 4000 toward
7000 — at 7000 the isolated rim measured band 124.6 / frac 0.0954 on the
Viper, which clears both bars. **Watch `clipW` as it goes up:** the rim is
the brightest thing on the body, and pushing it hard is what clips.

### 3.2 `under_lowbody_1_3x_torso` / `under_feet_1_3x_torso` — 0.21–1.43 and 0.29–1.15

**Fails on all five, and the feet ratio is always the worse of the two**,
which says the under is aimed above the feet. The `under_aim` sweep
(line 1611, values 0.12/0.20) and `under_gain` (line 1628) are the two
levers and the fit already uses them. If they do not clear 1.3, the
remaining cause is the **rim competing for the same pixels** — the rim
azimuth sweep (line 1625) exists for that, and the isolated data says the
under ratio is decided there, not by the under.

**If the under must clear 1.3 on both, the honest requirement is:** the
under must be the brightest thing on the lower body and the feet, which
means the key's contribution to the legs has to come down, not the under's
up. Reduce `self.key` (line 1600) toward 140 and raise `self.under_gain`.

### 3.3 `floor_zones_in_window` — the outer zone is 140–206 and the shadow side is 8–24

**The Floater was the extreme case and it was a SCALE bug, not a lighting
bug.** Its floors read 0.43 / 0.62 / 0.46 — effectively black — while its
body read band 68. The cause: the pool aim and the three floor probes
scaled with the subject's **height** while every light distance scaled with
its **size**. The Floater is 2.48 m across and 0.29 m tall, so its pool
landed 0.16 m from its feet and its three probes clustered on one patch of
ground. Everything floor-related now scales with `size`
(`pool_geometry(height, size)`, `compute_zones(..., size)`), and the
Floater's floors went to 128.96 / 56.22 / 140.83 — inside the window.

**The remaining floor failure is the OUTER zone running hot** (171–206
against a ceiling of 175) with the shadow side still under 45. That is a
geometry problem, not an energy problem: the outer probe is sitting in the
pool's spill. **The change:** move `POOL_EDGE` (line 127) from 0.42 to
0.60–0.75 so the outer probe leaves the pool's ellipse, and raise
`self.wash_gain` (line 1627) to lift the shadow side into the window.

### 3.4 The Floater's transform — a named open item

**Symptom:** the Floater's band is 26 and its rim fraction 0.0039, the
worst in the set, while the other four read 57–104. Its floors are now
correct (128.96 / 56.22 / 140.83) and its background is 28.9, so it is in
frame and lit — but the RIM is not reaching it.

**Cause:** the asset-tracking lane found the Floater's pivot is 100 cm off,
so the manta hovers above the ground plane. The rig's rim grazes the
silhouette edge, and for a wide flat creature the edge is nearly
horizontal, so a rim at el 20° passes over it.

**The change:** in the source FBX (`Tools/blender/out_xcom/XCOM_Floater.fbx`,
built by `Tools/blender/xcom_enemies.py`), correct the pivot so the manta's
lowest point sits on z = 0, and rebuild the export. Then re-measure. **The
lighting rig cannot fix this** — if the object is not in frame, no light
setting moves the numbers, and that is the standing diagnostic: *change a
light; if nothing moves, the object is not in frame.*

**Note the size field is already working for it:** the Floater's height is
0.290 m but its `size` is 2.480 m, because a manta is wide. That was the
extent normalisation landing correctly.

### 3.5 The detached geometry — a named open item, and the state of the tool

**Ebert named:** the Sectoid's free hand, the Floater's white box and white
tile, the Muton's white shard, the hip fragments.

**The purge tool now runs and reports honestly.** `purge_detached()` uses
**material and position**, not island count:

- a piece is DELETED when it carries a **default/white** material, carries
  **no** body material, carries **no** `ACCENT_EMISSIVE`, and its bounding
  box sits outside the body's own bounds by more than the tolerance band;
- a piece carrying `CHITIN`, `PLATE`, `PLATE_DARK`, `PLATE_OXBLOOD` or
  `CHITIN_BONE` is **anatomy** and stays however far out it sits;
- `ACCENT_EMISSIVE` is the eyes and is never removed.

**Current result: 0 pieces removed on all five**, reported per asset as
`purge: N islands, removed M debris piece(s)`. **A zero here is a real
zero, not a crashed function** — earlier versions of this tool read
`.name` off a BMesh vertex (which has no `.name`), the caller swallowed the
exception, and five "purge skipped" lines were reported as five clean bills
of health. It now raises instead of printing and continuing, and every
call prints its removed count.

**The debris is therefore NOT in the mesh as disconnected white pieces** —
the FBX is imported as a single object (`imported 1 mesh object(s)`), so the
white box, the tile and the shard are welded into the body mesh, not
floating as separate objects. **The remaining work is at the source:** find
those primitives in `Tools/blender/xcom_enemies.py` and delete them there,
then re-export the FBX. A white box welded onto the shoulder is still a
white box on the shoulder.

**Independent confirmation from the renders:** the delivered frames were
checked with vision and show **no detached floating pieces** — the Muton
reads "none clearly visible", the Sectoid reads "no unmistakable floating
body geometry". The debris is not visible in the current renders, but the
Ebert-scored renders (`Tools/blender/out_xcom/XCOM_*.png`, produced by
`xcom_enemies.py`) are a different generation and were not re-rendered here.

---

## 4. The asset work that is not lighting

Ebert's verdict is 3.33/7.0 against a 6.2 bar, and the rejection is
**not** the rig — it is that the kit is five generic bipedal robots wearing
five different names, and the renders were shot with neutral lighting so
none of the rig or the emissive was visible.

**The silhouettes still to rebuild, against the brief** (this is modelling
work in `Tools/blender/xcom_enemies.py`, not lighting):

| Enemy | Required read | Current state |
|---|---|---|
| XCOM_Floater | **legless manta**, hovering, glowing dorsal core, trailing tendrils | has legs and stands on two boots |
| XCOM_Chryssalid | **low, wide, forward-pitched stalker** with scythe forelimbs | reads as a heavy biped robot, no scythe forelimbs |
| XCOM_Viper | **tall, narrow, elongated snout, raised ribbed dorsal spine, plasma pistol** | boxy biped, snub helmet cap, no snout/ribs/weapon |
| XCOM_Muton | **heavy, wide, armoured, single horizontal visor slit** | strongest silhouette, but a white curled mass crosses the face |
| XCOM_Sectoid | **small, gaunt, oversized smooth cranium, no mouth** | the best idea in the kit — keep the cranium |

**The detached-geometry purge belongs in the same file** (see §3.5).

**Asset generation note:** the FBX files in `Tools/blender/out_xcom/` are
from the demo lane's re-export (the Muton is 5,216 triangles against the
stale 3,712 in the old manifest). **State the generation when publishing**,
because the parity lane and the demo lane must be looking at the same mesh.

---

## 5. How to run and verify

```bash
# render all five and publish only if the set is complete AND better
"D:/Blender/blender-4.2.23-windows-x64/blender.exe" -b -noaudio \
  -P Tools/blender/rig_evidence.py -- \
  --out "<repo>/Tools/blender/out_lighting"

# per-light diagnostic (this is what found the rim flood)
... --out "<repo>/Tools/blender/out_lighting" --diag --only XCOM_Muton

# rim azimuth x cone sweep inside the unified rig
... --out "<repo>/Tools/blender/out_lighting" --probe --only XCOM_Muton

# prove the probe path and the delivered path are the same rig
... --out "<repo>/Tools/blender/out_lighting" --parity

# what disconnected geometry does this FBX contain
... --out "<repo>/Tools/blender/out_lighting" --islands

# independent re-measure, no Blender, pure-Python PNG reader
python Tools/blender/rig_evidence.py --verify --out "<repo>/Tools/blender/out_lighting"
```

**Publishing is atomic and honest.** The run builds into
`Tools/blender/out_lighting_build/`, verifies all 19 files exist, compares
the new set's criteria total against the live gallery's, and copies into
`CommandCenter/outputs/lighting/` and `Tools/blender/out_lighting/` only if
the set is **complete and better**. A partial or worse set leaves the
gallery untouched. The gallery is therefore always a single generation.

**Outputs per enemy:** `*_reveal.png` (the rig, the delivered frame),
`*_emissive_only.png` (no scene lights, emissive only), and
`*_studio_vs_reveal.png` (studio rig beside reveal rig). Plus
`rig_params.json` (every light's type, colour, watts, position, rotation and
the world background strength), `rig_params.png` (the same table rendered as
an image), `verification.json` (every measured number) and
`verification_independent.json` (the same numbers re-measured without
Blender).
