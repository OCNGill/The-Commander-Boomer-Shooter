# CHARACTER SPEC — EDI
### `CRW_EDI_SPEC_v01` · 2026-10-28 · Target: 25k–35k tris, baked 2K PBR

**Reference plates (from Commander, 2026-10-28)**
- `nude-star-smokes-hot-gilian-anderson-cigarmonkeys-13.jpg` — dusk, copper-red, latex catsuit
- `Gillian-Anderson-cigar-smoke-cigarmonkeys-1.jpg` — noir, platinum, satin dress

**Likeness target:** actress Gillian Anderson. **She smokes.** Squadron 42 has her modeled — reference their head/face approach, take techniques only.

**Shipped name:** `EDI` is fine as a character callsign. The **voice key `edi`** and the actress's name are **internal only** — exports are `CRW_EDI_*`, `VO_EDI_*`. Never `gillian`, never `anderson` in a filename.

---

## §1 — DESIGN LOCK: **"BLACK ICE" (Look B) primary, "NOIR" (Look A) alternate costume**

| | **BLACK ICE — primary** | **NOIR — alternate** |
|---|---|---|
| Hair | Copper auburn, shoulder-length, deep side part, voluminous wave | Ash/platinum, extra-long past waist, sleek flat-ironed |
| Eyes | Cool blue-grey, pale iris, dark limbal ring | Dark brown / near-black |
| Wardrobe | Glossy black-indigo **latex catsuit**, high neck, deep V front zip | Long-sleeve black satin dress, low scoop neck |
| Jewelry | Gunmetal rings ×2, studded chain cuff | Black tassel choker, statement ring |
| Lips | Matte, defined cupid's bow, neutral-to-severe | Dark matte oxblood / near-black |
| Mood | Dusk, confrontational, dangerous | Noir, low-key, high contrast |

**Why B is primary:** combat silhouette reads better at game distance (narrow waist + wide hair + gloss highlights), the catsuit is cyberpunk-native, and shoulder-length hair is 3× cheaper than a waist-length groom. **A ships as a reward costume** — same mesh, different groom + material set.

---

## §2 — FACE GEOMETRY (both plates agree; this is the likeness)

| Feature | Target |
|---|---|
| **Skull** | Oval / heart, wider at the temples, narrowing to the jaw. High cranium, flat mid-face. |
| **Jaw** | Strong, defined angle, slight squareness, tapering to the chin. **Not** soft, **not** a heavy masculine mandible. |
| **Cheekbones** | **The dominant plane.** High, sharp zygomatic arch, hard under-bone hollow. The malar shelf must be sculpted HARD — this is the single strongest likeness cue. |
| **Brow** | Straight to slightly arched, low-set, moderate ridge (a smooth shelf, not a protrusion). Brows dark, medium thickness, swept up at the tail. |
| **Nose** | Straight narrow bridge, low and smooth, **no dorsal hump**. Small refined tip, slight upturn at the columella, narrow nostrils. |
| **Lips** | Full, sharp lip line, clear philtrum, defined cupid's bow. **Lower lip plumper than upper.** Mouth closed, neutral-to-severe (never a smile). |
| **Chin** | Short, slightly pointed, strong mental ridge. Cleft-free. |
| **Read** | Mature — **30s to 40s**. Angular, severe, sculpted "old-Hollywood" bone structure with **low facial fat**. |

> **Silhouette rule:** at gameplay camera distance the likeness lives in three cues — the **cheekbone shelf**, the **cupid's-bow lip**, and the **jaw taper**. Lock those before touching pore detail.

---

## §3 — EYES (where cheap characters die)

- **Shape:** almond, slightly hooded, heavy upper lid. Outer corner level-to-slightly-down.
- **Makeup:** thick black **winged** liner with a sharp flick, smoky charcoal blended crease, dark matte lashes. **No gloss.**
- **Build:** parallax cornea, iris depth, visible limbal ring, a wet line at the lower lid. Sclera not pure white — slight warm tint, faint veins.
- **This is the highest-value detail in the whole character.** Spend the texture budget here.

---

## §4 — SKIN

| Property | Value |
|---|---|
| Tone | Fair, neutral-warm with cool shadow (`#E8C2A6` base) |
| Quality | Smooth, **low pore detail** — porcelain, not plastic |
| SSS | Subtle at ears, lips, nose tip. Pre-integrated subsurface |
| Specular | **Dual-lobe**, matte-to-satin. **No oil sheen on the face** — reserve high gloss for the latex |
| Detail maps | Baked normal + AO + micro-detail. Avoid a uniform noise pass |

---

## §5 — HAIR

| | Primary (B) | Alternate (A) |
|---|---|---|
| Color | `#9C4221` copper auburn, darker mahogany roots, caramel flyaway tips | `#B8A98C` ash/platinum, cool neutral |
| Length | Shoulder to upper-neck | Past waist to mid-thigh |
| Part | Deep side part (her right), swept across the forehead | Center / slight off-center |
| Style | Voluminous 80s/90s wave, loose curls at the ends | Sleek, straight, glassy, flat-ironed |
| Volume | High — **silhouette wider than the shoulders**, back-heavy mass | High at crown, sleek down the length |
| Build | Card/clump cards + 2–3 guide curves, flyaway strands at crown/edges, vary curl radius | Long straight cards 1–2 cm, slight overlap, alpha tips, fanned crown cards |

**Engine route:** **hair cards** (game-cheap) over strand groom. Bake a slight wind lift so she never looks static.

---

## §6 — THE CIGAR / CIGARETTE (signature prop — non-negotiable)

| Property | Spec |
|---|---|
| Type | Slim cigarette, white paper, tan filter *(short cigarillo is the alternate costume's prop)* |
| Hold | Pinched between **index + middle finger**, relaxed grip, hand at chest or hip height |
| Ash | 8–12 mm grey-white, slightly crumbled tip, faint crack |
| **Ember** | Orange-red glow, **emissive, pulsing 0.5–1 Hz** |
| Smoke | Thin rising column, 2–3 curling wisps, drifting up with slight lateral wind. Low density, soft alpha, dissipates by head height |
| Animation | **Hand-to-mouth montage**, idle drag, exhale. A static prop is a failure |

**Implementation:** Niagara smoke (soft alpha, wind vector), emissive ember material with a sine-pulse parameter, and a looping `hand-to-mouth` montage driven by an anim notify. Smoke must respect the bullet-time `User.TimeDilation`.

---

## §7 — HANDS

- Slender, **long** fingers, defined knuckles, lightly modelled tendons. **No sausage fingers.**
- ~4.5 head-heights hand length.
- Nails: short, dark/neutral polish, clean cuticles.
- Smoking hand: relaxed, fingers slightly curled, thumb tucked.
- Other hand: on hip, fingers splayed over the waist — **power pose**.

---

## §8 — LIGHTING (reference both plates)

| Position | Spec |
|---|---|
| **Key** | Front-high, soft, slightly cool — defines the face and the latex highlights |
| **Fill** | Low, cool blue from below/side — keeps shadows readable |
| **Rim** | Strong warm/white edge on hair + shoulders — separates her from the background |
| **Mood** | Noir, confident, dangerous. **High contrast on the suit, soft on the skin.** |

---

## §9 — PALETTE

| Swatch | BLACK ICE (primary) | NOIR (alt) |
|---|---|---|
| Hair | `#9C4221` | `#B8A98C` |
| Skin | `#E8C2A6` | `#D9C3B0` |
| Wardrobe | `#0E1426` | `#141414` |
| Smoke | `#B9C2CE` | `#9AA0A6` |
| Background | `#3E5C8A` | `#2A2D31` |
| Accent (lips / ember) | `#9E1B1B` | `#7A1E2B` |

---

## §10 — DELIVERABLES

| File | Content |
|---|---|
| `CRW_EDI_v01.blend` | sculpt + groom + wardrobe |
| `CRW_EDI_v01.fbx` | game mesh, **25–35k tris**, embedded materials |
| `CRW_EDI_tex_basecolor_v01.png` | 2K |
| `CRW_EDI_tex_normal_v01.png` | 2K |
| `CRW_EDI_tex_roughness_v01.png` | 2K |
| `CRW_EDI_tex_metalness_v01.png` | 2K |
| `CRW_EDI_tex_emissive_v01.png` | 2K — lips + ember |
| `CRW_EDI_view-hero_v01.png` | hero render |
| `CRW_EDI_view-turnaround_v01.png` | 8-angle turnaround |
| `CRW_EDI_view-face_v01.png` | close-up likeness check |
| `CRW_EDI_view-smoke_v01.png` | cigarette + ember + smoke |
| `MANIFEST_CRW_EDI_v01.json` | tri counts, material slots, texture hashes |
| `ITERLOG_CRW_EDI_v01.md` | what changed and why |

**Gate:** Ebert **≥ 6.2 weighted**, no rounding. Min 5 screenshots + console audit. Any axis at 1.0 = categorical fail.

---

## §11 — LIKENESS / LEGAL NOTE

A recognizable-actress likeness in a commercial product carries **right-of-publicity** risk. Two safe paths:
1. **"Inspired by"** — keep the silhouette and the attitude, shift the facial proportions 10–15 % so it reads as *a* striking woman, not *that specific* woman.
2. **Licensed** — only if the Commander obtains permission.

**Recommendation: path 1 for anything that ships.** The reference plates are for **art direction and craft**, not for a photogrammetric likeness. Squadron 42's version is likewise a licensed performance — we study their **technique** (head-scan pipeline, facial rig, skin shader), never their asset.

Flagging for the Commander's call. Not blocking the sculpt.

---

*"A good name is rather to be chosen than great riches." — Proverbs 22:1 (ESV). Chosen because what we call her, and what we ship under, matters more than how fast we ship it.*
