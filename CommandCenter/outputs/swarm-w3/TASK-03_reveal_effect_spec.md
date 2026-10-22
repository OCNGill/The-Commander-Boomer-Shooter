# TASK-03 — The Creep Reveal: effect specification

- **Slot:** swarm-w3
- **Lane:** W3 (rendering / reveal-effect lane)
- **Written:** 2026-10-21T07:25:00-04:00
- **Status:** spec only — nothing in `Tools/blender/**`, `Content/**`, `Docs/**` or `Config/**` was edited.
- **Companions:** `CommandCenter/outputs/swarm-w3/CLAIM_TASK-03.md`, `CommandCenter/outputs/swarm-w3/LEDGER_LINE.md`

---

## 0. What this document is for, and what it is not

This is the **implementation-ready spec for the enemy reveal**: the single authored beat that
introduces a creature to the player. It exists so that another lane can build the reveal in
Blender and in UE5 **without asking a question** — the frame sequence, the light rig and the
order the lights come up in, the per-enemy timings, the audio cue points, the camera language
and the numeric pass/fail gates are all written down here.

It is a spec, not a patch. Three things are explicitly out of scope and are **reported, not
fixed** (see §11):

1. The current rig source has drifted away from the rig that was last rendered (§13).
2. The enemy roster in `Docs/generated/weapons_enemies_v1.json` has **zero overlap** with the
   five X-COM originals this reveal is built for (§11.1).
3. The UE asset tree the reveal will be authored against is two rebuilds stale, and the import
   report that certifies it does not describe the assets on disk (§11.2, and TASK-08).

---

## 1. The grammar being preserved (inherited, not invented)

The reveal grammar is inherited verbatim from `CommandCenter/outputs/swarm-w1/TASK-01_xcom1994_roster.md`
§5 ("The reveal grammar, stated once, for TASK-03 to inherit"). It is restated here only so the
implementer has it in one place:

1. **Black.** The tile the enemy is on is unlit and the enemy is not visible.
2. **A sound arrives first.** The contact sting plays on the same frame as the light snap — the
   player's ear knows before the eye does.
3. **A hard light snap — no fade.** A cold key with a hard shadow, off-axis, sculpting the *face*
   and dropping the lower body into black. *1994 had no fade; a pop from black. Do not add a fade-in.*
4. **The silhouette resolves, not the body.** Only the head, the eyes and one shoulder are fully
   readable; the rest is falloff.
5. **The eyes are the brightest pixels in the frame.**
6. **A ground anchor.** A tight contact-occlusion seam at the soles and one clear cast shadow
   falling away from the camera — except the Floater, whose only ground element is its shadow.
7. **The under-glow is under the creature, not in front of it.** A floor pool is not an under-glow.
8. **Enemy-specific first read** (§6).

The 1994 original had **no spawn-flash**: units were 32×32 sprites popping out of black fog of
war with an audio exclamation. The rig in this repository is a **valid modernisation of that
grammar** — the modern equivalent of "pop from black" is an **8-frame EMERGE pose, not a fade**
(`TASK-06` §3.4). Do not add a spawn flash, a fade-in, or a screen-space effect to "improve" it.

**Hard rules, non-negotiable:**

- The reveal is **not** a fade. There is no alpha ramp, no dissolve, no material lerp.
- The reveal is **not** a camera move. The camera does not dolly, cut or shake (§8).
- The reveal is **audio-first**: the sting and the light snap share a frame (§7).
- The eyes must end up as the brightest pixels in the frame, above the rim band.

---

## 2. The clip

| Property | Value | Source |
|---|---|---|
| Clip name | `A_<E>_Reveal` (one per enemy) | `TASK-06` §3.0 |
| Length | **8 frames** | `TASK-06` §3.0, §3.4 |
| Source rate | 30 fps → 0.267 s | `TASK-06` §3.0 |
| Loop | no | `TASK-06` §3.0 |
| Playback | plays once, on the spawn/reveal event, at source rate (no time dilation) | `TASK-06` §3.4 |
| Root motion | none — the pose is an in-place rise; the light does the work | `TASK-06` §3.4 |

The clip is authored at 8 frames and the **entire light schedule below is expressed in clip
frames**, so the reveal is frame-rate independent: at 30 fps it is 0.267 s, and the light
schedule scales with the clip.

**What the pose must sell:** the creature was *already crouched there in the dark, waiting*. Each
enemy gets its own crouch (§6).

---

## 3. The five lights and their roles

The rig is five lights, all parented to the spawn actor. Names, types and colours are the
**locked vocabulary** in `Tools/blender/rig_evidence.py` and the UE handoff
`Docs/generated/lighting_rig_spec.md`:

| # | Name | Type | Colour (linear) | Role | Shadow |
|---|---|---|---|---|---|
| 1 | `reveal_key` | Spot, cone 40° | `(0.62, 0.78, 1.00)` cold | the only shadow direction that matters — front-left, above, aimed at the chest; sculpts the face | **ON** |
| 2 | `reveal_rim` | **Spot, cone 45°** | `(0.03, 1.00, 0.12)` alien green | **the separation light** — the only thing drawing the outline against a near-black backdrop | ON |
| 3 | `reveal_under` | Spot, cone 26°, small source (radius 0.01) | `(0.45, 0.90, 1.00)` cyan | tight local uplight at the feet; the under-glow lives *under* the creature | **OFF** |
| 4 | `reveal_pool` | Spot, cone 22° | `(0.52, 0.72, 1.00)` cold | the bounded pool of light on the floor = the contact shadow + the cast shadow | ON |
| 5 | `reveal_wash` | Area, dim | `(0.45, 0.55, 0.70)` blue-grey | keeps the shadow side of the floor readable; the only ambient term | OFF |

Supporting constants (locked): `HAZE 0.003`, `GROUND_ALBEDO 0.18`, `WORLD_STRENGTH 0.10`,
`WORLD_COLOR (0.006, 0.008, 0.012)`, `EMIT_COLORS` accent/eye `(0.05, 1.00, 0.25)`,
core `(0.05, 0.60, 1.00)`, plasma `(0.45, 0.05, 1.00)`, `EMIT_STRENGTH 0.1`,
`PROOF_EMIT_SCALE 6.0` (proof renders only — never ship the 6× scale).

**Geometry** (as last rendered, 07:32:29 `rig_params.json`; §13 records the drift): `CAM_AZ 305`,
`CAM_LENS 50`, `CAM_COVER 2.35`, `CAM_H 0.62`, `CAM_TARGET_Z 0.42`,
`KEY_AZ 262 / KEY_EL 42 / KEY_DIST 1.00 / KEY_SPOT 40`,
`RIM_AZ 240 / RIM_EL 20 / RIM_DIST 1.10 / RIM_CONE 45`,
`UNDER_Z 0.04 / UNDER_OFF 0.06 / UNDER_CONE 26 / UNDER_RADIUS 0.01`,
`POOL_AZ 145 / POOL_EL 70 / POOL_DIST 1.30 / POOL_CONE 22`,
`WASH_AZ 300 / WASH_EL 55 / WASH_DIST 1.20 / WASH_SIZE 1.20`,
`REF_HEIGHT 1.0`, `POOL_G 0.35`, `POOL_LAT 0.32`, `POOL_SHADOW 0.60`, `POOL_EDGE 0.42`.

**Energy** (rig units; Blender watts = `value × (body_height / REF_HEIGHT)²`, so illuminance is
proportional across the set): key **320**, rim **2000**, under **3000**, pool **90**, wash **0.6**.

**`reveal_rim` is a spot, not an area strip.** The live rig states the reason in one line: *"the
rim MUST be a cone. An area light floods"*. An area strip at rim energy washes the floor and
loses the outline it was meant to draw. Anyone re-implementing this from the older
area-strip description is building the bug the rig already fixed.

**Rule of separation:** the key and the rim are 43° apart in azimuth from the camera and cannot
be at the same azimuth. The rim must never be culled, dimmed to zero, or replaced by a fill —
with a near-black backdrop it is the only thing separating the silhouette from the void.

---

## 4. The order of introduction (normative)

This is the heart of the spec. The reveal is **a sequence of five introductions**, not one flash.
Each step is a beat; the beat order is what makes the creature *arrive* rather than *appear*.

| Beat | Clip frame | Time @30 fps | What happens | Lights |
|---|---|---|---|---|
| **A** | 0 | 0.000 s | **Black → snap.** The sting starts on this exact frame. The key snaps to 100% in one frame (≤ 33 ms). No fade. The face is lit; the lower body falls into black. | `reveal_key` ON 100% |
| **B** | 1 → 3 | 0.033 s | **Separation.** The green rim comes up from 35% and reaches 100% at frame 3. The outline starts to detach from the black. | `reveal_rim` ON, ramp 35→100% |
| **C** | 2 → 5 | 0.067 s | **Eyes.** Emissive ramps to its reveal peak. By frame 5 the eyes are the brightest pixels in the frame. | emissive ramp (eyes / core / plasma) |
| **D** | 3 | 0.100 s | **Ground anchor.** The bounded pool snaps on: contact seam at the soles + one cast shadow falling away from the camera. | `reveal_pool` ON 100% |
| **E** | 4 | 0.133 s | **Under-glow + fill.** The tight cyan uplight fades up *under* the creature over 0.4 s. The dim wash fills the shadow side of the floor. | `reveal_under` ON, 0.4 s fade-in; `reveal_wash` ON, ramp to 100% by frame 7 |
| **F** | 5 → 8 | 0.167 s | **Hold.** The body resolves out of the falloff; the 8-frame rise completes. | all at target |
| **G** | 8 → 16 | 0.267 s | **Settle.** The creature finishes standing up at t = 0.533 s (frame 16). | `reveal_under` OFF at 0.533 s with a 0.20 s ramp down |
| **H** | 16 → | 0.533 s | **Hold for the encounter.** The key, rim, pool and wash stay on; the under-glow is gone. | key / rim / pool / wash ON |

**Ordering constraints, in one place, so an implementer cannot get it wrong:**

- The **sting and the key snap are the same frame** (beat A). Audio never lags the light.
- The **key is the only hard-edged transition.** Every other light is a ramp. A key that fades
  is a failed reveal.
- The **rim comes after the key**, never before. The silhouette is separated *after* the face
  appears, not before.
- The **emissives ramp after the key is up** (beat C), so the eyes punch out of an already-lit
  head rather than floating in the dark.
- The **pool comes after the body has a head** (beat D): the ground anchor is the *last* thing
  that establishes the creature is standing on something.
- The **under-glow is the last light up and the first light off.** It exists only for the rise.
- The **wash is the dimmest thing in the rig** and must never become a second key. If the wash
  reads on the body, the wash is too strong.

**If the engine only supports one "reveal event":** the event enables `reveal_key`,
`reveal_rim`, `reveal_pool`, `reveal_wash` and starts `reveal_under` on a 0.4 s fade-in, and
the per-light ramp times in the table above are the schedule those five components follow
(`Docs/generated/lighting_rig_spec.md` §6, wired identically).

---

## 5. Frame-by-frame intent

| Frame | The player should see |
|---|---|
| 0 | A cold light hits a face that was not there. Nothing else is lit. The sting hits the same instant. |
| 1 | A green edge appears along the shoulder and jaw. The shape is still unreadable. |
| 2 | Two eyes ignite. They are the brightest thing on screen. The head is on a body. |
| 3 | The feet meet the ground — a hard contact seam and a shadow running away from the camera. |
| 4 | Cyan light appears *under* the creature. It is not a spotlight in front of it. |
| 5 | The silhouette resolves. The lower body is still mostly falloff. |
| 6 | The stance is legible — weight, weapon, limbs. |
| 7 | The creature is fully readable but the light is still doing the work. |
| 8 | The rise completes. The under-glow begins to die. |

---

## 6. Per-enemy timings and first reads

Every enemy's reveal is the same eight frames with the same light order, but the **first read**
and the **emphasis** differ. The first-read assignments are inherited from `TASK-01` §5.8; the
timing adjustments below are this spec's.

| Enemy | Height | First read (inherited) | Clip beat | Key on | Rim on | Emissive lead | Pool on | Under | Extra |
|---|---|---|---|---|---|---|---|---|---|
| **Sectoid** | 1.39 m | A pale smudge; no mouth; the *absence* is the scare | f0 | **f0, 100%** | f1 (ramp) | f1 (eyes) | f3 | f4, **50% energy** | Slowest resolve: the cranium catches the key, the rest stays black. The rim is the read. |
| **Viper** | 2.06 m | The **weapon coil glow first**, then the snout and rib ridge | f0 | **f1** (one frame late, behind the coil) | f1 | **f0 (plasma coil, full)** | f3 | f4, **80%** | The coil is lit *before* the key — the weapon is the first thing the eye finds. No under-glow from the creature; the coil is the under-light. |
| **Floater** | 0.29 m body, hovers 0.9 m | **Ground shadow first, body second, light third**; it descends into the fog | f0 | **f5 (late)** | f5 | f3 | **f0 (first light of all)** | **n/a** | **Order is inverted on purpose.** Beat D becomes beat A: the shadow arrives first, the body descends over f0→f7, the key lands last. No contact shadow (it never touches the ground); its only ground element is its cast shadow. |
| **Muton** | 2.07 m | The **red visor band and oxblood chest** are the first two things in frame; it arrives as a wall | f0 | **f1** | f2 (delayed one more) | **f0 (visor + oxblood, full)** | f3 | f4, **60%** | Heaviest key, slowest body resolve. The wall reads before the mass does. |
| **Chryssalid** | 1.03 m | **Two small green points moving across a dark tile**; it resolves late and arrives first | f0 | **f5 (late)** | f6 | **f0 (two green points, full)** | f3 | f4, **100%** | The body stays near-black until f5 — the two points *arrive first* and the creature resolves onto them. The green points must read against black, not against a lit body. |

**Floater-specific rules** (because its manifest says `has_ground_contact: false`,
`hover_clearance_m: 0.9`):

- It has **no contact seam** and **no under-glow**; its only ground element is its cast shadow.
- It **descends** into frame: the 8-frame pose is a descent, not a rise.
- Its pivot sits on the floor, so in UE it **must spawn at +100 cm** and be levelled by hover
  (see `TASK-07`'s Floater trap).
- Its measured `contact_shadow_ratio` is 0.011 — near zero, and correct.

---

## 7. Audio cue points

### 7.1 The cue map

| Cue | When | What it must do |
|---|---|---|
| **Sting** | **frame 0, same frame as the key snap** | The player's ear knows before the eye does. Non-voiced, short, transient, dry. Must not be a taunt (taunts are the insult bank, a separate system). |
| **Body of the reveal** | frames 0 → 8 | Low-level bed that rises with the rig — the *approach*, not the sting. Optional; if present it must duck under the sting. |
| **Under-glow tick** | frame 4 | Optional, sub-audible, per-enemy. A low pulse that supports the cyan under-light without a new asset. |
| **Settle** | frame 8 → 16 | Optional, a breath/settle that lets the under-glow die. Must not be a second sting. |

### 7.2 What exists today

`Content/Audio/SFX/` contains exactly four real cues: `sfx_burp.wav`, `sfx_defeat_squelch.wav`,
`sfx_menace_hum.wav`, `sfx_pizza_impact.wav` (plus `_dbg/` and `_normtest*/` scratch folders).
`Docs/generated/insult_bank_contract.md` maps `sfx_pizza_impact` → **"reveal sting"** ("short bright
transient with a splat tail") and `sfx_menace_hum` → "hit" (slow detuned low drone).

**Consequence:** there is **no dedicated reveal sting asset**, and no per-enemy variants. The
reveal cannot ship on `sfx_pizza_impact` — a pizza splat is a comedy cue and it is already
spoken for by the insult bank.

### 7.3 Required audio deliverable

| ID | Requirement |
|---|---|
| **A1** | One dedicated reveal sting per enemy (5), named `SFX_XCOM_Reveal_<Enemy>` — short bright transient, 0.15–0.4 s, non-voiced, no tail longer than 0.4 s. `Sectoid`, `Viper`, `Floater`, `Muton`, `Chryssalid`. |
| **A2** | The sting must be **transient-first**: its attack must be ≤ 20 ms so it reads as a *snap* against a key-light snap, not as a swell. |
| **A3** | The sting must be **spectrally distinct per enemy** — the Chryssalid's is thin and high (two points), the Muton's is low and broad (a wall), the Viper's has a coil-hum character, the Floater's is airy and rising, the Sectoid's is a dry scrape. |
| **A4** | Until A1 exists, `sfx_pizza_impact` is the **placeholder only** and must be flagged as such in the asset tracker (TASK-08). |
| **A5** | The sting must be triggerable on the **exact frame** the key light enables, from the same event that drives the reveal clip. Sub-frame drift of more than one frame breaks grammar rule 2. |

---

## 8. Camera language

The reveal is a **lighting and pose** event, never a camera event.

| Rule | Value |
|---|---|
| Camera movement during the reveal | **none** — no dolly, no cut, no shake, no roll, no FOV change |
| The reveal happens in the *gameplay* camera | the tile camera the player already owns. The rig is authored so it reads from any of the isometric tile cameras. |
| The hero/verification camera (a measuring instrument, not the shipping camera) | az 305°, lens 50 mm, camera height 0.62·h, target 0.42·h, cover distance 2.35·h |
| Per-enemy cover distance | Sectoid 3.27 m, Viper 4.84 m, Muton 4.86 m, Chryssalid 2.42 m, **Floater 5.39 m** (it is 2.48 m wide and hovers, so it needs its own distance) |
| Framing | full body, nothing cropped, the creature reads against a near-black backdrop, the floor pool and cast shadow inside the frame |
| The key/rim azimuth relationship | fixed: the key is camera-left-front, the rim is behind-left. Never swap them for an enemy, never re-aim the key at the floor |

**Why the camera is static:** the 1994 reveal was a pop in the player's field of view. A camera
move adds a second event to the beat, and two events in 0.267 s read as a cutscene, not a
contact. If the framing is wrong, fix the framing — never animate the camera during the reveal.

---

## 9. Acceptance criteria (normative)

### 9.1 The thirteen measured gates

The rig already carries a verification harness with 13 criteria and a numeric bar. **The reveal
is not done until all five enemies pass all thirteen.** These are the gate names and their
thresholds as coded in `Tools/blender/rig_evidence.py` and `Tools/blender/out_lighting/verification.json`:

| # | Criterion | Threshold |
|---|---|---|
| 1 | `no_clipped_white` | `clipped_white_pixels == 0` |
| 2 | `no_clipped_body` | `clipped_body_pixels == 0` |
| 3 | `no_colour_clip_off_emissive` | no non-emissive colour clipping |
| 4 | `floor_zones_in_window` | every probed floor zone mean inside the window |
| 5 | `floor_zones_differ_15pct` | min lateral difference between floor probes ≥ **15 %** |
| 6 | `background_darkness_le_40` | outer-border mean luminance ≤ **40** |
| 7 | `contact_shadow_present` | `contact_shadow_ratio_mask ≤ 0.85` |
| 8 | `face_p99_ge_25` | face-zone p99 luminance ≥ **25** |
| 9 | `torso_p99_ge_25` | torso-zone p99 luminance ≥ **25** |
| 10 | `rim_3pct_of_body` | `rim_bright_over_body ≥ 0.03` |
| 11 | `rim_band_mean_ge_120` | `rim_band_mean_lum ≥ 120` |
| 12 | `under_lowbody_1_3x_torso` | under-glow over torso ≥ **1.3×** |
| 13 | `under_feet_1_3x_torso` | under-glow over feet ≥ **1.3×** |

**Windows** (`window` block): `face_p99 [60, 180]`, `torso_p99 [60, 180]`, `floor_mean [45, 175]`,
`floor_pool [95, 150]`, `floor_shadow [45, 105]`, `background_darkness [0, 40]`,
`rim_band_mean [120, 240]`.

**Bar** (`bar` block): `face_p99_min 25`, `torso_p99_min 25`, `floor_front_over_face_min 1.5`,
`floor_zone_min_diff_pct 15.0`, `rim_bright_over_body_min 0.03`, `rim_band_mean_min 120.0`,
`under_lowbody_over_torso_min 1.3`, `under_feet_over_torso_min 1.3`, `clipped_max 0`,
`background_darkness_max 40.0`, `floor_mean_min 45.0`, `floor_mean_max 175.0`.

**Render conditions for a valid measurement:** 720 × 900, EEVEE (Blender 4.2), 48 samples,
AgX view transform, 5 of 5 enemies rendered, 0 skipped, ground albedo 0.18, world strength 0.10,
haze 0.003.

### 9.2 The reveal-specific gates (this spec, not in the harness)

| # | Gate | How it is measured |
|---|---|---|
| 14 | The key is a **step, not a ramp** | capture the reveal sequence; luminance of the face zone at frame 0 must be ≥ 90 % of its frame-8 value, and frame 0 must not be interpolated from a pre-reveal black frame |
| 15 | **No alpha / no dissolve** | the reveal clip must not drive any material opacity, and the mesh must be at full opacity on frame 0 |
| 16 | **The sting and the key share a frame** | the sting's event timestamp equals the key light's enable timestamp, ± 1 frame |
| 17 | **Eyes are the brightest pixels** | in the reveal frame, the brightest non-background pixel must lie in an eye/core emissive region; no light source pixel may exceed it |
| 18 | **The under-glow is under the creature** | the under-glow's floor footprint must lie behind the feet line, not between the camera and the feet |
| 19 | **One cast shadow, falling away from the camera** | exactly one shadow direction; its axis must not point toward the camera |
| 20 | **No camera motion during the reveal** | camera transform identical at reveal frame 0 and frame 8 |
| 21 | **The reveal is 8 frames at source rate** | clip length 8 frames @ 30 fps, plays once |

---

## 10. The current measured failures this spec exists to fix

**Measurement generation: `Tools/blender/out_lighting/verification.json`, generated
`2026-10-21T07:33:03` (sha256 prefix `d1f887a230`), 5 of 5 rendered, 0 skipped, 720×900,
EEVEE 48 samples, AgX, renderer "EEVEE (Blender 4.2)".**
**All five enemies still fail.** Pass counts: Muton 6/13, Chryssalid 7/13, Sectoid 7/13,
Viper 8/13, Floater 8/13.

> **This section was rewritten at 07:36.** The rig was reworked and re-rendered by another lane
> at 07:32:29/07:33:03, which changed the failure profile substantially: the **floor white-out
> is fixed** (the floor now sits inside its window on four of five enemies and the backdrop
> passes on all five) but **clipping has exploded** (2442 clipped pixels on the Sectoid, up
> from 491). Any earlier reading of this document that cites the 06:40:13 generation is
> superseded. Numbers below are the 07:33:03 generation.

### 10.1 What the rework fixed — and what it broke

**Fixed: the floor white-out (§10.1 of the previous revision).** The under-glow no longer floods
the ground. The backdrop now passes on **all five** enemies, and the bottom border band has
collapsed from 59–121 to 0.42–41.7:

| Enemy | background darkness (≤ 40) | top band | **bottom band** | floor_front mean | floor_shadow mean | floor_key mean |
|---|---|---|---|---|---|---|
| Sectoid | **20.871** ✔ | 0.99 | 34.83 | 88.93 | 62.60 | 26.99 |
| Viper | **22.964** ✔ | 1.00 | 38.01 | 89.65 | 51.11 | 32.50 |
| Muton | **22.851** ✔ | 0.99 | 41.70 | 90.52 | 63.99 | 26.75 |
| Chryssalid | **6.595** ✔ | 0.97 | 5.10 | 32.84 | 5.05 | 2.13 |
| Floater | **0.699** ✔ | 0.97 | 0.42 | 1.38 | 0.66 | 0.48 |

**Fixed: the floor contrast.** `floor_zones_differ_15pct` now passes on **all five** — the floor
is no longer a flat white card:

| Enemy | min lateral difference | bar | verdict |
|---|---|---|---|
| Chryssalid | **57.86 %** | 15 % | pass |
| Viper | **36.41 %** | 15 % | pass |
| Sectoid | **29.60 %** | 15 % | pass |
| Muton | **29.32 %** | 15 % | pass |
| Floater | **26.86 %** | 15 % | pass |

**Fixed: the rim's brightness ratio.** `rim_3pct_of_body` now passes on three of five (Viper
0.0799, Muton 0.0413, Sectoid 0.0414, all above 0.03).

**Broken: clipping.** The rig traded floor blowout for body blowout:

| Enemy | clipped white/body pixels | colour clip off emissive | was (06:40:13) |
|---|---|---|---|
| **Sectoid** | **2442** | 0 | 491 |
| **Muton** | **1271** | **235** | 0 |
| **Viper** | **1081** | 0 | 0 |
| **Chryssalid** | **525** | 0 | 0 |
| Floater | 0 | 0 | 268 |

The Muton is the only enemy now clipping **off-emissive** colour (235 px) — that is a *material*
problem, not an energy problem: a surface is driven past its colour ceiling. The `KEY_COLOR_MAX
0.62` ceiling on the cold key is what protects the other three; the Muton's oxblood plate
absorbs and re-emits, so the key at 320 rig units over-drives it.

**Still broken: the rim band.** `rim_band_mean_ge_120` still fails on three of five, and the
two that fail badly are the two smallest creatures:

| Enemy | `rim_band_mean_lum` (need ≥ 120) | `rim_bright_over_body` (need ≥ 0.03) |
|---|---|---|
| Viper | **134.088** ✔ | 0.07987 ✔ |
| Muton | **111.443** ✘ (93 % of the bar) | 0.04133 ✔ |
| Sectoid | **105.322** ✘ (88 %) | 0.04140 ✔ |
| Chryssalid | **31.078** ✘ (26 %) | 0.00769 ✘ |
| Floater | **1.977** ✘ (2 %) | 0.0 ✘ |

The rim is now a **spot cone (45°, az 240, el 20)**, and a spot at rim energy lands its hot
centre somewhere the band probe does not read. On the two big bipeds it is nearly there
(93 % and 88 % of the bar); on the **Chryssalid (1.03 m) and the Floater (0.29 m, 5.39 m
away) it is essentially absent** — 2 % of the required band. The Floater's `rim_pixels` is
**0**: the rim contributes nothing to its silhouette at all. That is the single clearest
remaining defect and it is a *scale* problem: rim energy is fixed in rig units while the
Floater sits 5.39 m from the camera and only 0.29 m tall.

**Still broken: the under-glow ratios.** `under_lowbody_1_3x_torso` fails on four of five:

| Enemy | `under_lowbody_over_torso` (need ≥ 1.3) | `under_feet_over_torso` (need ≥ 1.3) | reading |
|---|---|---|---|
| Floater | **1.8749** ✔ | 0.4011 ✘ | under owns the body but not the feet |
| Viper | 0.8509 ✘ | 0.2115 ✘ | under is on the floor, not the body |
| Sectoid | 0.8338 ✘ | 0.3927 ✘ | same |
| Muton | 0.7023 ✘ | 0.4311 ✘ | same |
| Chryssalid | 0.5905 ✘ | **2.2388** ✔ | feet read, low body does not |

The under-glow still lights the ground rather than the creature. The rework raised under
energy to 3000 rig units and tightened the cone to 26° with a 0.01 m source radius, which
made the falloff steeper — but a steeper falloff from a source at `UNDER_Z 0.04` still lands
on the floor first. The Floater is the exception that proves the mechanism: it hovers 0.9 m
above the floor, so its under-glow *can* reach the body (1.87×) and cannot reach the floor
(0.40×). **The fix direction follows directly: the under-glow's source must be nearer the
body's underside than the ground.**

**Still broken: the Floater's empty face.** `face_p99` is **0.00** (face mean 0.00, p99 0.00,
torso mean 3.67) → fails `face_p99_ge_25`. The Floater's whole body is dark: `visible_body_pixels`
is **868** out of a 11 755-pixel body, and `emissive_pixels` is **15** (the other four enemies
carry 20 798–38 004). The Floater is currently **effectively unlit**. Its floor mean is 1.38 —
far below the `floor_mean` window of [45, 175] — so it fails `floor_zones_in_window` on the
*dark* side. **The Floater is the opposite failure of the 06:40 generation: it was blown out,
and now it is black.**

### 10.2 The current gate scoreboard (07:33:03)

| Enemy | Passing | Failing criteria |
|---|---|---|
| XCOM_Muton | 6/13 | clipped white, clipped body, colour clip off emissive, floor in window, rim band 120, under lowbody, under feet |
| XCOM_Sectoid | 7/13 | clipped white, clipped body, floor in window, rim band 120, under lowbody, under feet |
| XCOM_Chryssalid | 7/13 | clipped white, clipped body, floor in window, rim 3 %, rim band 120, under lowbody |
| XCOM_Viper | 8/13 | clipped white, clipped body, floor in window, under lowbody, under feet |
| XCOM_Floater | 8/13 | floor in window, face p99, rim 3 %, rim band 120, under feet |

**Reading the scoreboard.** The four bipeds now fail on the same pair of issues — *the body is
too hot* (clipping) and *the under-glow is on the floor* — plus a rim band that is 7–12 % short.
The Chryssalid adds a rim that is 74 % short. The Floater fails almost everything because it
is too dark, not too bright.

**The honest summary: the rework traded a floor white-out for a body white-out, and left the
under-glow and the small-enemy rim unresolved.** Three defects, in priority order:

1. **Clipping on the four bipeds** (Sectoid 2442, Muton 1271, Viper 1081, Chryssalid 525) —
   the key/rim/under energies are now too hot for the body, and the Muton additionally clips
   off-emissive.
2. **The under-glow lights the floor** (`under_lowbody` 0.59–0.85 on four of five against a
   1.3 bar; the feet ratios 0.21–0.43 on three of five).
3. **The rim is absent on the small enemies** (Chryssalid band 31 of 120; Floater band 2 of 120
   with `rim_pixels` 0).

### 10.3 What still has to be true of the reveal itself

The rework fixed the *floor*. It did not touch the reveal grammar, and the reveal-specific
gates (§9.2) are still unmeasured — there is no rendered reveal sequence in the repo, only
per-enemy stills. Gate **14** (the key is a step, not a ramp) and gate **16** (the sting and
the key share a frame) cannot be evaluated from a still at all. That work is still outstanding
and is listed in §12 (R3, R7).

### 10.4 Independent re-measure (second opinion)

`CommandCenter/outputs/lighting/verification_independent.json` was generated at **06:32:18** —
i.e. against the *previous* rig generation, so it is **not** a second opinion on the 07:33:03
numbers. It remains useful as a record of the 06:40 state, and it flagged a disagreement worth
carrying forward: the Floater's `contact_shadow_ratio_mask` measured **1.2203** there (which
would fail `contact_shadow_present` at ≤ 0.85) while the harness reported 0.011 and passed it.
The 07:33:03 harness value for the Floater is **0.4765** — still under the bar, but the
two-measure disagreement on the Floater's contact shadow has never been resolved, and the
Floater's ground element is the one ground element the reveal grammar explicitly calls for.
**Re-run the independent measure against the 07:33 generation and reconcile it before the
Floater is signed off.**

---

## 11. Conflicts this spec depends on (reported, not fixed)

### 11.1 The roster does not contain these enemies

`Docs/generated/weapons_enemies_v1.json` currently holds six **Plymouth eldritch** creatures:
`e_01 Barnacle Drone`, `e_02 Pilgrim Zealot`, `e_03 Mayflower Phantom`, `e_04 Lobster Brute`,
`e_05 Rock Golem`, `e_06 Nor-Easter Titan`. There is **no overlap** with the five X-COM originals
this reveal is built for (Sectoid, Viper, Floater, Muton, Chryssalid). `e_06` is an unfilled boss
slot. `TASK-04` (swarm-w4) lists 17 flagged conflicts in this area, including weapon-damage
disagreements across three separate sources.

**What the reveal depends on:** the per-enemy first-read table (§6) and the five stings (§7.3)
are keyed to the X-COM five. If the roster is not reconciled, the reveal ships against a roster
that does not contain it. **Not fixed here.**

### 11.2 The UE side the reveal will be authored against is stale

The reveal rig is a UE actor component. The UE assets in `Content/Enemies/XCOM/` are dated
**01:04–01:13**, while the FBX they were imported from are dated **04:24–04:27** — the UE tree
is **two rebuilds stale**. The import report is dated 04:41:30 but its recorded triangle counts
(2864 / 3712 / 1980 / 2520 / 2536) do not match the current manifest (7308 / 5764 / 2184 / 5216 /
6252) — 39–91 % retention — so the report's claim that "triangle counts match the Blender
manifest exactly" is not true against the manifest on disk. See **TASK-08** for the full
tracking and DoD.

### 11.3 `target_height()` would mis-scale every alien

`Tools/python/populate_encounters.py::target_height(label)` returns 300 for `ENC_NorEaster`,
160 for `ENC_Brute`, 150 for `ENC_Golem`, 60 for `ENC_Drone`, 180 for any other `ENC_`, 40 for
`PU_`, 60 for `WP_`, and **100 otherwise**. Those are Plymouth-roster values. The X-COM enemies
have no `ENC_` label of their own, so they would fall through to the 100 uu default. Any reveal
spawn that re-points a mesh must not use this normaliser for the X-COM five — the manifest
heights are authoritative (Sectoid 1.39 m, Viper 2.06 m, Floater 0.29 m + 0.9 m hover,
Muton 2.07 m, Chryssalid 1.03 m).

### 11.4 The Floater's pivot

The Floater's pivot sits on the floor. It must spawn at **+100 cm** and levitate. Reveal
grounding is impossible for it by construction; the reveal grammar already accounts for this
(§6, `TASK-01` rule 6).

### 11.5 Bloom is globally off

`Config/DefaultEngine.ini` sets `r.DefaultFeature.Bloom=False` (alongside
`AutoExposure=False`, `AmbientOcclusion=False`, `MotionBlur=False`, `Projector=False`), and
**no PostProcessVolume asset exists in `Content/`**. The emissive reveal — eyes, core, plasma
coil — will therefore have **no bloom in game**. That is survivable (the eyes must read as the
brightest pixels, not as a glow), but it must be a decision: either the reveal ships without
bloom, or a Post Process Volume with bloom enabled is added in the reveal area. If bloom is
added, the acceptance thresholds in §9 must be re-measured in-game, because bloom raises
`clipped_white_pixels` and the rim band.

### 11.6 Drift in the rig source itself

The rig source has been edited *after* the last render (source touched 07:33:40, render
07:33:03). See §13 for the full four-generation drift table — this is the single most important
thing for the implementing lane to know before touching the rig.

---

## 12. What the implementing lane must deliver

| # | Deliverable | Where |
|---|---|---|
| R1 | The five-light rig rebuilt to the §3 vocabulary, with the §4 order of introduction | `Tools/blender/rig_evidence.py` + the UE rig component |
| R2 | A per-enemy light schedule matching §6 | rig params / anim data |
| R3 | `A_<E>_Reveal` 8-frame clips, one per enemy, with the per-enemy crouch | animation set |
| R4 | 5 reveal stings (A1–A3) | `Content/Audio/SFX/` |
| R5 | A re-render of all 5 enemies at 720×900 / EEVEE 48 / AgX | `Tools/blender/out_lighting/` |
| R6 | `verification.json` showing **13/13 on all five** | `Tools/blender/out_lighting/` |
| R7 | A UE sequence capture proving gates 14–21 (hard step, no alpha, same-frame sting, eyes brightest, under-glow under, one shadow, static camera, 8 frames) | `CommandCenter/outputs/lighting/` |
| R8 | The Floater's `contact_shadow_ratio` disagreement (§10.4) resolved and recorded | verification notes |
| R9 | The Floater's face-zone mapping fixed or explicitly exempted (§10.1) | verification notes |

**Definition of done:** five enemies at 13/13 on the thirteen harness gates, plus all eight
reveal-specific gates verified from a captured sequence, plus the drift in §13 reconciled and the
numbers in this document re-measured against the final rig.

---

## 13. Drift disclosure (read this before touching the rig)

`Tools/blender/rig_evidence.py` is being actively edited by another lane. The file was last
modified at **07:33:40** — *after* the 07:33:03 verification render that every number in §10
comes from, and after the 07:32:29 `rig_params.json`. **The rig is moving faster than this
document can be edited.** Four parameter generations have existed in this session alone:

| Parameter | "Locked" vocabulary (task brief) | 06:39:40 render | **07:32:29 render (current)** | live source (07:33:40) |
|---|---|---|---|---|
| `RIM_AZ` / `RIM_EL` | 155 / 32 | 122 / 30 | **240 / 20** | 240 / 20 |
| `RIM_CONE` | 50 | 50 | **45** | 45 |
| rim type | AREA strip | AREA strip | **SPOT cone** | SPOT cone — *"the rim MUST be a cone. An area light floods"* |
| `RIM_COLOR` | (0.20, 1.00, 0.42) | (0.03, 1.00, 0.12) | **(0.03, 1.00, 0.12)** | (0.03, 1.00, 0.12) |
| `KEY_DIST` | 1.85 | 1.85 | **1.00** | 1.00 |
| `POOL_DIST` | — | 1.80 | **1.30** | 1.30 |
| `WASH_DIST` | — | 1.60 | **1.20** | 1.20 |
| `UNDER_Z` | 0.10 | 0.04 | **0.04** | 0.040 |
| `UNDER_CONE` | 30 | 20 | **26** | 26 |
| `REF_HEIGHT` | — | 2.0 | **1.0** | 1.0 |
| key / rim / under / pool / wash energy | — | 45 / 260 / 3000 / 350 / 20 | **320 / 2000 / 3000 / 90 / 0.6** | 320 / 2000 / 3000 / 90 / 0.6 |
| `EMIT_STRENGTH` | — | 0.1 each | **0.05 each** | 0.05 each |

**The energy model changed.** The old model scaled watts by `(body_height / 2)²` with
`REF_HEIGHT = 2.0`; the current model scales by `(body_height / 1.0)²` with `REF_HEIGHT = 1.0`,
so illuminance is `value / DIST²` and proportional across the set. The rig values are
therefore **not comparable** to the older base-watt numbers, and the 06:40 measurements cannot
be compared to the 07:33 ones without a conversion.

**Therefore:**

1. Every number in §10 is cited against the **07:33:03 verification generation** (sha256
   prefix `d1f887a230`) and the **07:32:29 `rig_params.json`** (sha256 prefix `a0a7774756`).
   Say so whenever they are quoted.
2. **Before any rig change is judged, re-render and re-measure.** Do not reason from this
   document, from the task digest, or from any earlier reading of it — reason from
   `Tools/blender/out_lighting/verification.json` on disk, and quote its `generated` stamp.
3. `Tools/blender/out_lighting/` is **not tracked by git** — a render can be replaced without a
   diff. Pin the generation stamp *and* the file's sha256 in any handoff.
4. The §3 vocabulary, the §4 order of introduction, the §6 first reads and the §9 gates are
   **generation-independent** and survive any retune. That is exactly why they are specified in
   terms of *role, order and gate* rather than *watts*. If the rig moves again, those four
   sections do not need rewriting — only §10 and this one do.

---

## 14. Source index

| Fact | Source |
|---|---|
| Reveal grammar (8 rules), per-enemy first reads | `CommandCenter/outputs/swarm-w1/TASK-01_xcom1994_roster.md` §5 |
| 8-frame `A_<E>_Reveal` clip, rig owns the pose / light owns the flash / audio owns the sting | `CommandCenter/outputs/swarm-w1/TASK-06_rig_plan.md` §3.0, §3.4 |
| Light vocabulary, UE wiring, bloom and fog guidance | `Docs/generated/lighting_rig_spec.md` |
| Rig energy table, criteria definitions, drift | `Tools/blender/rig_evidence.py` |
| Measured gates | `Tools/blender/out_lighting/verification.json` (07:33:03) |
| Independent re-measure | `CommandCenter/outputs/lighting/verification_independent.json` (06:32:18) |
| Rendered rig parameters | `Tools/blender/out_lighting/rig_params.json` (07:32:29) |
| Audio cue map | `Docs/generated/insult_bank_contract.md`, `Docs/generated/sound_design_list.md`, `Content/Audio/SFX/` |
| Naming, spawn traps, Floater +100 cm | `CommandCenter/outputs/swarm-w2/TASK-07_ue_import_pipeline.md` §2 |
| Roster conflicts | `CommandCenter/outputs/swarm-w4/TASK-04_roster_integration.md` |
| Fix list the rig is working against | `CommandCenter/briefs/LIGHTING_V2_FIXLIST.md` |
