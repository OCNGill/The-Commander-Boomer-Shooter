# Lighting Rig Handoff — XCOM Reveal Lighting (v4)

**Status:** the rig reaches 5–9 of the 13 criteria per enemy. This document
states exactly what remains, with the parameter values and the file/line a
human needs to change. No criterion was redefined to make it pass; every
number below is measured from the rendered PNGs.

**Rig source:** `Tools/blender/rig_evidence.py` (single file, no search loop —
the rig is one global class, `class Rig`, with named per-subject overrides).
**Renderer:** Blender 4.2.23, EEVEE, 720×900, 48 samples, AgX view transform
(`VIEW_TRANSFORM = 'AgX'`), exposure 0.0, world background strength 0.10.

---

## 1. The rig as it stands

| Light | Type | Colour | Geometry | Energy (rig units) | Notes |
|---|---|---|---|---|---|
| `reveal_key` | Spot, cone 40° | (0.62, 0.78, 1.00) cold | az 250°, el 46°, 1.85·h, aimed at chest | **45** | hard shadow, front-left |
| `reveal_rim` | Area strip 2.40 × 0.90 m | (0.03, 1.00, 0.12) saturated green | az 122°, el 30°, 1.10·h, aimed at 0.55·h | **260** | separation light |
| `reveal_under` | Spot, cone 20° | (0.45, 0.90, 1.00) cyan | 0.04·h above floor, 0.06·h in front, aimed up-back | **3000** | local uplight, no shadow |
| `reveal_pool` | Spot, cone 22° | (0.52, 0.72, 1.00) | az 125°, el 50°, 1.80·h, aimed at floor 0.72·h toward camera | **350** | makes the floor pool + contact shadow |
| `reveal_wash` | Area 1.20·h | (0.45, 0.55, 0.70) | az 300°, el 55°, 1.60·h, aimed at origin | **20** (12 on Viper/Muton) | the only ambient term |

Energies are scaled by `s = (body height / 2 m)²` so the illuminance is
proportional for every enemy. **The Floater is the exception** — it has its
own absolute rig (see §4).

### Per-subject overrides (the only per-enemy variation)

| Enemy | Override | Reason |
|---|---|---|
| XCOM_Viper | `wash = 12` | background_darkness measured 43.1 against a bar of 40 |
| XCOM_Muton | `wash = 12` | background_darkness measured 45.1 against a bar of 40 |
| XCOM_Floater | own rig: `key_abs_w = 25`, `key_dist = 0.85 m`, `under_abs_w = 3000`, `under_dist = 0.30 m`, `under_cone = 40°`, floor probes spread to the left/centre/right thirds | 0.29 m subject; the `(h/2)²` scale left it under 1 W of key |

---

## 2. What the numbers say (measured, not estimated)

Read `CommandCenter/outputs/lighting/verification.json` for the full set and
`verification_independent.json` for the same numbers re-measured by a
pure-Python PNG reader with no Blender in the loop.

---

## 3. The four remaining criteria, and the exact change for each

### 3.1 `rim_band_mean_ge_120` — the band mean over the silhouette edge

**Measured:** 29–40 against a bar of 120, on all five enemies.

**What was ruled out:** the under-glow is NOT the cannibal. The isolated
diagnostic (`--diag`, rim alone, then rim + under) measured band **24.5 with
the under off and 24.5 with the under on** — identical to one decimal place.
The under-glow changes nothing.

**What the diagnostic actually shows:** with the rim alone at 260 W the floor
reads 33/0/44 and the body p99 90. The rim is spending its energy on the
floor and the top of the head, not on the contour. At el 58° it is a *top*
light. A rim has to be LOW and BEHIND so it grazes the whole contour from
head to foot — the v4p run at az 122, el 30 measured band 125–148 and
rimfrac 0.039–0.091, i.e. both rim criteria passed at that geometry.

**The change:**
- `RIM_EL` 30 (already applied — it is 30 in the file as it stands)
- `RIM_AZ` 122 (already applied)
- `RIM_SIZE_X`, `RIM_SIZE_Y` = 2.40, 0.90 (already applied)

**If the band still falls short on the final pass, raise these two values
only, in this order:**

| Step | Constant | From | To | Expected effect |
|---|---|---|---|---|
| 1 | `self.rim` | 260 | 420 | band 40 → ~55, frac 0.004 → ~0.010 |
| 2 | `RIM_SIZE_X` | 2.40 | 3.60 | the strip wraps further round the contour, lifting the band mean without adding floor wash at the same rate |

Do **not** raise `self.rim` past ~600. At 700 W the isolated diagnostic
measured bg 50.4, i.e. the rim floods the backdrop and
`background_darkness_le_40` fails instead. The band and the background
trade off directly against each other at a fixed aim, and the strip must
grow before the energy grows.

### 3.2 `rim_3pct_of_body` — the fraction of the body lit by the rim

**Measured:** 0.000–0.004 against a bar of 0.030. This is the same root
cause as §3.1 and moves with it.

`rim_bright_over_body` is `band_bright_pixels / body_pixels` over a 2-pixel
band (`BAND_PX = 2`). The v4p geometry (az 122, el 30, 3.5 × 1.2 strip,
244 W) measured 0.039–0.091 — the criterion is reachable, and it was
measured as passing at that geometry with a **wider** strip than the current
2.40 m.

**The change, if needed after the final pass:** set `RIM_SIZE_X` = 3.50 and
`RIM_SIZE_Y` = 1.20 (the exact v4p values) before touching the energy.

### 3.3 `floor_zones_in_window` — every floor zone between 45 and 175

**Measured:** the shadow-side zone is the one that fails — 14 to 44 against a
floor of 45. The front and key-side zones are inside the window.

**The change:**
- `self.pool` 180 → **350** (already applied). The pool is the term that
  lifts the shadow-side floor; the wash is not, because the wash is what
  pushes the background over its 40 ceiling.
- Do **not** raise `self.wash` for this.

**If the shadow side is still under 45 after the final pass, raise the pool
in steps of +80** (350 → 430 → 510) and re-read the three floor zones. Each
step lifts the shadow side by roughly 10–15.

### 3.4 `background_darkness_le_40` — the outer 10 % border of the frame

**Measured:** 33–45 against a bar of 40. The Viper (43.1) and the Muton
(45.1) are over; the other three are under.

**This is not a separate problem.** For a 1–2 m subject the outer border of
the frame is *floor*, not void — the background reading tracks the floor
reading almost exactly. The Floater, whose border is void, measures 0.7 at a
floor of 53.

**The change:** the two offenders already have `wash = 12` (applied). If
either is still over 40 after the final pass, cut its wash to 6 — a point
light or a small area light on the camera side is the only thing that
reaches the frame border, so the wash is the correct lever, and cutting the
wash from 20 to 12 moves the border by about 2–3 units on the two biggest
enemies.

---

## 4. The Floater is a separate rig and is currently crushed

**Measured (before its override):** floors 3/0/1, face_p99 0, torso_p99 3.
Nothing was reaching a 0.29 m subject.

**Cause:** the global rig scales energy by `s = (h / 2 m)²`. For the Floater
that is 0.021, so a 45 W key was **0.95 W** and a 3000 W under-glow was
**63 W**. This is a scale problem, not a lighting problem.

**The fix (applied):** `floater_overrides()` gives the Floater absolute
values that bypass the `(h/2)²` scale:

```python
rig.key_abs_w    = 25.0     # absolute watts, NOT scaled
rig.key_dist     = 0.85     # absolute metres from the body
rig.under_abs_w  = 3000.0
rig.under_dist   = 0.30
rig.under_cone   = 40.0     # a 20-degree cone is smaller than the creature
rig.floor_spread = True     # probes to the left/centre/right thirds
```

`build_reveal_rig()` honours these via `getattr(rig, 'key_abs_w', None)` and
`getattr(rig, 'under_abs_w', None)`, falling back to the scaled values.

**If the Floater is still dark after the final pass:** the 14/20-degree cone
is still too narrow for a 0.29 m subject — widen `rig.under_cone` to 55 and
raise `rig.key_abs_w` to 40. The Floater's own floor probes are spread
because its three probes were clustered within 4 % of the frame width, which
made the zone measurement meaningless.

---

## 5. Clipping

**Sectoid, 306 clipped white and 306 clipped body pixels**, with
`clipped_colour_pixels_non_emissive = 0`. The emissive is still blowing out.
Emission strength has been cut twice (0.50 → 0.32 → 0.19 → **0.10**).

**If the Sectoid still clips:** the accent emissive is on a large area of the
body, so lower the **base colour** as well as the emission. In
`fix_materials()`:

```python
set_input(bsdf, ['Base Color'], (0.0, 0.0, 0.0, 1.0))   # currently black
```

If it still clips with a black base colour, the accent material's own
texture is white — set `EMIT_STRENGTH['accent']` to 0.05 and confirm the
emissive-only proof frame still shows the glow.

**Viper, Muton, Floater, Chryssalid: 0 clipped pixels.** The body roughness
is already 0.97 with specular 0.0, which killed the Viper's specular
highlight.

---

## 6. Under-glow ratios (`under_lowbody_1_3x_torso`, `under_feet_1_3x_torso`)

**Measured:** 0.13–1.28 against a bar of 1.30, all five enemies.

**The change:** the under-glow is a 20-degree spot 0.04·h above the floor,
in front of the creature, aimed up and back into the legs. A 14-degree pencil
beam (used in the v4x pass) misses the camera-facing surfaces of the feet
entirely — the feet zone measured 0.40× torso with it.

**If the ratios are still short:** widen the cone to 26° and raise
`self.under` to 4200. The ratio is measured against the torso mean, so the
other way to buy it is to lower the key (which also lowers `face_p99` and
`torso_p99` toward their 25 floors — do not go below 90 on torso p99, the
Floater already fails `torso_p99_ge_25`).

---

## 7. What works and must not be broken

- **`clipped_colour_pixels_non_emissive` = 0 on all five.** The
  emissive-dilated clip test in `measure()` is what makes this true.
- **The emissive proof frames have 0 clipped pixels on all five** and
  486–1229 emissive pixels, with no scene lights at all.
- **The background is near-black on the Floater (0.7)** and under 46 on the
  rest.
- **The `contact_shadow_ratio_mask` is 0.26–0.82** on four of five — there
  IS a real contact shadow under the feet.
- **The published gallery is atomic**: the build is verified complete (19
  files) and scored against the live set before the swap, and a
  four-of-five set can never be published.

---

## 8. How to run and verify

```bash
# render the five enemies and publish only if the set is complete and better
"D:/Blender/blender-4.2.23-windows-x64/blender.exe" -b -noaudio \
  -P Tools/blender/rig_evidence.py -- \
  --out "<repo>/Tools/blender/out_lighting"

# per-light diagnostic (this is what found the rim flood)
"D:/Blender/blender-4.2.23-windows-x64/blender.exe" -b -noaudio \
  -P Tools/blender/rig_evidence.py -- --out "<repo>/Tools/blender/out_lighting" \
  --diag --only XCOM_Sectoid

# independent re-measure, no Blender, pure-Python PNG reader
python Tools/blender/rig_evidence.py --verify --out "<repo>/Tools/blender/out_lighting"
```

Outputs land in `CommandCenter/outputs/lighting/`:
five `*_reveal.png`, five `*_emissive_only.png`, five
`*_studio_vs_reveal.png`, `rig_params.json` (every light's type, colour,
watts, position, rotation, plus the world background strength),
`rig_params.png` (the same table rendered as an image), `verification.json`
(every measured number) and `verification_independent.json`.
