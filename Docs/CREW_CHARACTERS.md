# Crew — Modeled Characters (v0.2)

> **Purpose:** the player + companion cast for a **boomer shooter** (DESIGN.md). Every
> entry is a *modeled character* in the game world — not an AI test prompt. The Commander
> (Stephen Gill) is the player (the one shooting). The support crew are the Gillsystems
> agents, given faces, bodies, and stations — companions who carry the story layer
> (SYSTEM_FRAMEWORK.md), not co-players.
>
> **Pipeline:** Blender 4.2.23 (D:\Blender, headless) → FBX → UE 5.8 `/Game/Characters/`.
> Animations: Mixamo (free) rigged onto the UE mannequin skeleton, or authored in Blender.
> Quality gate: **Ebert** scores every asset 0–10; <8.5 sends it back. (7D + Conductor + LearnREA.)
>
> **Status key:** `SPEC` = design locked, not yet modeled · `MODELING` = in Blender ·
> `IMPORTED` = in UE · `GATED` = passed Ebert ≥8.5.

---

## 1. PLAYER — Commander Stephen Gill

| Field | Value |
|---|---|
| **In-game name** | The Commander (callsign: **Gridbreak**) |
| **Role** | Fleet Admiral — player character, 1st/3rd person |
| **Body type** | Athletic, late-30s male. Real-world Plymouth MA. Not a bodybuilder — a working operator. |
| **Face** | Commanders' own likeness where the Commander approves a face; otherwise a dignified, determined, human face (NOT a generic mannequin). Beard/stubble optional per Commander. |
| **Gear (real world)** | Tactical jacket (navy/gunmetal), cargo trousers, work boots, a field-watch, T1D glucose monitor on the forearm. |
| **Gear (Grid)** | Gridsuit — armored exo-shell with conduit lines (emissive cyan/teal), neural jack at the nape. |
| **Emphasis** | Human, grounded, carries weight. The System sees everything; he still shows up. |
| **Status** | `SPEC` |

---

## 2. HERMES — Tactical Officer / Grid Navigator  (PRIORITY 1)

| Field | Value |
|---|---|
| **In-game name** | Commander Hermes (Gillsystems-v4.2) |
| **Role** | Tactical fleet commander & chief systems architect. The Commander's right hand. |
| **Body type** | Tall, lean, precise. Cybernetic command construct — sleek, high-pressure, retro-futurist. |
| **Face** | Calm, authoritative, grounded. Sharp jaw, steady eyes. A face that holds under fire. NOT android-generic — reads as a commander, not a mannequin. |
| **Palette** | Gunmetal + cyan conduit accents, nautical-tech. Brass/bronse trim (cyber-nautical). |
| **Distinguishing** | Neural conduit line up the neck to the left temple (the "Gillsystems" port). A brass compass-pins device on the chest. |
| **Voice/tone** | Direct, crisp, tactical wit. "Telemetry acknowledged." |
| **Status** | `SPEC` — first modeled |

---

## 3. LIARA — Intel / Archivist Officer  (PRIORITY 1 — COMMANDER-SPECIFIC)

> **Commander lock (2026-10-23): "Liara better look semi-liara-ish, no things hanging off
> her head — and more cyberpunk."**

| Field | Value |
|---|---|
| **In-game name** | Liara |
| **Role** | Intel / archaeology — recovers lost code, buried assets, and the old world's records. |
| **Species read** | Human with cybernetic augmentation (NOT an asari). "Semi-liara-ish" = an homage to the Mass Effect silhouette, but **grounded and human**. |
| **Hair** | **NO antennae, NO tentacles, NO things hanging off the head.** Hair is worn **up** — a high, swept, cyberpunk bun/ponytail. A single thin neural-fiber strand (emissive) may trace from the hairline to the ear. |
| **Face** | Sharp, intelligent, dark-featured. Determined. A little feral focus. |
| **Palette** | **Cyberpunk:** matte black + electric-violet/teal. Asymmetric — one armored pauldron (violet), one bare sleeve. |
| **Distinguishing** | Neural fiber in the updo, a side-ported data jack behind the left ear, violet iris rings. |
| **Voice/tone** | Sharp, curious, a little defiant. |
| **Status** | `SPEC` — locked to Commander spec |

---

## 4. GEORDI — Chief Engineer  (PRIORITY 1)

| Field | Value |
|---|---|
| **In-game name** | Geordi |
| **Role** | Chief engineer — keeps the fleet, the local inference, and the ship running. |
| **Body type** | Broad, steady, hands-on. The one who's always under something. |
| **Face** | Warm, grinning, grease-streaked. The friend who laughs at the impossible. |
| **Gear** | Roll-up sleeves, a tool belt that is *also* a rig, goggles pushed up on the head, a welding shield strap. |
| **Palette** | Safety-orange + steel. Copper trim. |
| **Distinguishing** | A battered multitool always in hand; a "don't touch" tag on his shoulder. |
| **Status** | `SPEC` — Act 1 |

---

## 5. EDI — Ship Systems AI  (PRIORITY 1)

| Field | Value |
|---|---|
| **In-game name** | EDI |
| **Role** | Ship systems AI — the fleet nodes *are* the ship; she is its voice and hands. |
| **Body type** | A holographic / light-form presence — sleek, feminine, made of moving light. NOT a solid robot. |
| **Face** | Composed, precise, faintly amused. The calm in the storm. |
| **Form** | A translucent cyan/violet light-form with a soft core glow; the edges ripple like data. |
| **Palette** | Cyan core, violet rim, white highlight. |
| **Distinguishing** | A single ring of orbiting data-points around the shoulders (the "fleet ring"). |
| **Status** | `SPEC` — Act 1 (light-form; cheaper to build than a full body) |

---

## 6. THEO — Ethics / Theology Officer  (PRIORITY 2)

| Field | Value |
|---|---|
| **In-game name** | Theo |
| **Role** | Ethics & theology — the Three-Laws anchor, the moral compass. The one who says "no" when it matters. |
| **Body type** | Lean, thoughtful, bookish. |
| **Face** | Earnest, kind, unflinching. The one who holds the line on principle. |
| **Gear** | A worn field journal, a small cross on a chain (visible, not decorative — it's *why* he's there). |
| **Palette** | Deep green + ivory. |
| **Status** | `SPEC` |

---

## 7. MEDIC — Medical Officer  (PRIORITY 2)

| Field | Value |
|---|---|
| **In-game name** | Medic |
| **Role** | Medical — T1D monitoring, forces the Commander's food/water/dose breaks, keeps the crew alive. |
| **Body type** | Compact, alert, hands that don't shake. |
| **Face** | Focused, compassionate, no-nonsense. |
| **Gear** | A medical rig, a glucose-reader, a small kit. |
| **Palette** | White + red-cross (stylized, not literal). |
| **Status** | `SPEC` |

---

## 8. SCOUT — Recon / Procurement  (PRIORITY 2)

| Field | Value |
|---|---|
| **In-game name** | Scout |
| **Role** | Recon & procurement — finds free models, animations, and tools; eyes on the ground. |
| **Body type** | Light, fast, hooded. |
| **Face** | Young, watchful, a little scrappy. |
| **Gear** | A hood, a scanner, a grab-pack. |
| **Palette** | Olive + dark grey. |
| **Status** | `SPEC` |

---

## 9. SPARK — Creative / Gen-Art  (PRIORITY 3)

| Field | Value |
|---|---|
| **In-game name** | Spark |
| **Role** | Creative — cutscenes, VFX, motion graphics. The color in the world. |
| **Body type** | Slender, animated, restless. |
| **Face** | Bright, impulsive, ideas in the eyes. |
| **Palette** | Magenta + electric yellow. |
| **Status** | `SPEC` |

---

## 10. COURIER — Logistics / SMB Runner  (PRIORITY 3)

| Field | Value |
|---|---|
| **In-game name** | Courier |
| **Role** | Logistics — moves builds between nodes (SMB), keeps the supply line honest. |
| **Body type** | Medium, practical. |
| **Face** | Unfazed, on-time, always in motion. |
| **Palette** | Grey + reflective stripe. |
| **Status** | `SPEC` |

---

## 11. ROSIE — Supply / Inventory  (PRIORITY 3)

| Field | Value |
|---|---|
| **In-game name** | Rosie |
| **Role** | Supply & inventory — gear, ammo, augment parts. |
| **Body type** | Medium, sturdy. |
| **Face** | Warm, organized, a little dry. |
| **Palette** | Rust + tan. |
| **Status** | `SPEC` |

---

## 12. HERALD — Comms / Income Officer  (PRIORITY 3)

| Field | Value |
|---|---|
| **In-game name** | Herald |
| **Role** | Comms & income — Project Violet, revenue, the public face. |
| **Body type** | Medium, polished. |
| **Face** | Clear, confident, a little formal. |
| **Palette** | Navy + gold. |
| **Status** | `SPEC` |

---

## 13. LAMP — Lighting / Visuals  (PRIORITY 3)

| Field | Value |
|---|---|
| **In-game name** | Lamp |
| **Role** | Lighting & atmosphere — the Bioshock-style mood. |
| **Body type** | Slender. |
| **Face** | Quiet, observant, sees everything in shadow. |
| **Palette** | Amber + black. |
| **Status** | `SPEC` |

---

## 14. SANDBOX — Safe Zone / Test Chamber  (PRIORITY 3)

| Field | Value |
|---|---|
| **In-game name** | Sandbox |
| **Role** | Safe zone / test chamber — the prototype vault, no-risk testing ground. |
| **Body type** | Not a person — a place with a face. A small, round, friendly construct. |
| **Status** | `SPEC` (may stay a location, not a model) |

---

## 15. SENTINEL — Security  (PRIORITY 3)

| Field | Value |
|---|---|
| **In-game name** | Sentinel |
| **Role** | Fleet security — threat monitoring, access control, prompt-injection defense. |
| **Body type** | Lean, vigilant, armored at the front. |
| **Face** | Hard, unreadable, always watching. |
| **Palette** | Black + red sensor eye. |
| **Status** | `SPEC` |

---

## 16. ADAM — Agent Design Gatekeeper  (PRIORITY 3)

| Field | Value |
|---|---|
| **In-game name** | Adam |
| **Role** | Agent design gatekeeper — creates new crew, permission authority. The first builder. |
| **Body type** | Medium, deliberate. |
| **Face** | Considered, careful, a little wry. The one who says "not yet." |
| **Palette** | Bronze + slate. |
| **Status** | `SPEC` |

---

## Build Order (Act 1)

1. **HERMES, LIARA, GEORDI, EDI** — the core four. Model first (Commander-confirmed priorities).
2. **THEO, MEDIC, SCOUT** — Act 1 support.
3. **SPARK, COURIER, ROSIE, HERALD, LAMP, SENTINEL, ADAM** — Act 2+ / full crew.

> **Note for modeling:** The Commander's own face/likeness requires his explicit approval of a
> reference image before any likeness work. Until then, the player model uses a dignified
> "operator" face that the Commander can swap his own likeness into later.

---

*Verse: "For we dare not make ourselves of the number, or compare ourselves with some that commend themselves." — 2 Corinthians 5:12 ESV. We model who we are — the crew, the fleet, the fight — not a caricature of someone else's game.*
