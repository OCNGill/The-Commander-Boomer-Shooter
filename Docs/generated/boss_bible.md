# BOSS BIBLE — THE HARVESTER
### *The Pac-Man / Sonic hybrid boss of The Commander Boomer Shooter*

**Version:** 1.0 · **2026-10-21** · **Owner:** Hermes (design lane)
**Machine-readable companion:** `Docs/generated/boss_bible.json`
**Rubric:** Ebert `zero_trust_likert_rubric.md` v1.0 — bar 6.2/7.0, no rounding, screenshots mandatory.
**Status:** **DESIGNED — not built.** No render of this boss exists. This document specifies what
must be built and photographed; it does not claim any of it has been.

---

## 1. The pitch, in one paragraph

The Harvester is a **Lattice**-class organism: a thing that eats structures the way a bulldozer
eats a fence, converting them into spore-mass it can carry. It is not a general, it is not a
hunter, it is **logistics**. It came to Plymouth because Plymouth was on a manifest.

Its body is a **grinder** (Pac-Man): a segmented radial maw that consumes **power nodes** out of
the arena geometry, one bite at a time, and that visibly *swallows the level around the player*.
Its locomotion is a **spin** (Sonic): when the maw is empty it collapses into a wheel and
**rolls**, and a rolling Harvester travels the arena's outer rail at more than twice the
player's sprint speed, unable to turn, unable to stop, and — crucially — **unable to defend
itself from behind**.

The fight is therefore not a damage race. It is a **scarcity problem**: the arena is a finite
resource, the boss eats it, the player can either shoot the boss or shoot its food, and it
cannot do both. The three-phase arc is the arc of that dilemma collapsing.

---

## 2. Why this boss exists (design justification)

Three problems in the current game that this boss fixes, and one thing it adds.

**Problem 1 — the game has no arena-shaped threat.** Every enemy to date is a creature that
walks at you. Nothing in the game currently threatens the *level*. A boomer shooter needs one
boss that changes the room, or Act III is just Act I with a bigger health bar.

**Problem 2 — the X-COM material is all "terror mission".** The 1994 roster is designed to
scare you with *wonder* (the reveal) and *pressure* (the panic). The Harvester is a **third
verb**: it is *indifferent*. It does not want to kill the Commander. It wants the shipping
container to be full. Fear of indifference is a different, and better, note than fear of a
bigger claw.

**Problem 3 — the player currently has no resource-management decision that matters.** Ammo is
generous (1.5× a standard clear). The Harvester is the first fight where **withholding a
resource is the correct play**, which is a different verb from "shoot the thing".

**What it adds.** It is the first entity in the game that **talks** (§7), and the first one
whose speech is the *lore*. The Harvester is filling in a manifest. Its lines are the boss's
dialogue, and the insult bank is the game's only fully voiced character.

**The hybrid, precisely.** Pac-Man contributes: the **grid**, the **mouth**, the **pell** (the
power node), the **power-pellet** (a node that, when shot, makes the eater vulnerable). Sonic
contributes: the **spin**, the **momentum**, the **rail**, and — critically — the **rolling
attack is the vulnerable state**, which is a direct inversion of Pac-Man's power-pellet
vulnerability. The two games meet in the middle: the thing that makes Pac-Man's ghost edible
is, here, the thing that makes the Harvester killable.

---

## 3. Silhouette and anatomy (Rule S1 first)

> **The black-shape spec.** It must read as a distinct shape at 40 px tall in pure black.

### 3.1 The form

A **radial grinder**: a sphere-bodied organism whose forward-facing third is a **four-lobed
radial maw** — a segmented iris of chitin plates that opens like a camera shutter and closes
like a mill. Around the maw, a ring of **nine chitin teeth** of unequal length (so the
silhouette is toothy, not scalloped). Behind the maw, the body swells into a **dorsal hump**
carrying a segmented emissive core.

Around the hump, **six articulated legs** — long, thin, jointed *backwards* at the knee, the
way an insect's are. The legs are not for walking. **They are for rolling.** Folded against the
body in a tripod, they read as a spiky corona. Extended, they are the thing that walks. The
silhouette must therefore work in **two poses** and both must read:

| Pose | Silhouette | Read |
|---|---|---|
| **Grinding** (mouth open, legs folded) | a spiky ring with a hole in the front | a mouth |
| **Rolling** (mouth sealed, legs tucked, body a wheel) | a smooth disc with a spine ridge | a wheel |

### 3.2 The two-feature rule (from Ebert's v1 verdict)

Ebert's highest-leverage fix for the enemy kit was *"rebuild each enemy around one unmistakable
silhouette"*. So the Harvester gets **two features that are never optional and never occluded**:

1. **The maw.** Always present, always at the front, always the largest opening on the body.
   Even sealed, the nine teeth show as nine notches in the outline.
2. **The dorsal spine ridge.** Six chitin spurs along the hump, running front-to-back, taller at
   the front. This is what makes the *rolling* pose read as a wheel and not a ball.

### 3.3 Palette and materials

| Part | Material | Colour |
|---|---|---|
| Body shell | `XCOM_Chitin_Dark` | wet black-green |
| Maw plates (inner) | `XCOM_Chitin_Pale` | bone |
| Nine teeth | `XCOM_Armor_Plate` (metal 0.65) | gunmetal |
| Dorsal core | `XCOM_Core_Emissive` (emission 22) | cyan |
| Spine spurs | `XCOM_Armor_Accent` (oxblood) | oxblood — **the single warm hue**, on six small parts only |
| Eye-lens (behind the maw, only visible when it opens) | `XCOM_Eye_Emissive` (emission 14) | alien green |
| Spore-mass (the "food" it chews) | `XCOM_Flesh` | pale, wet |

**Rule S3 compliance:** the oxblood is on **six spurs**, not on the body. The cyan core is the
only large emissive. Nothing else on this creature glows.

### 3.4 Geometry budget (Steam Deck 'low')

| Item | Value | Notes |
|---|---|---|
| Triangles | **18,500** (ceiling 22,000) | 7 materials; merge the two dark chitins before ship |
| Vertices | ~9,800 | |
| Texture | 2048² body atlas (ceiling 2048) | 1024² maw interior |
| Materials | **7** (hard cap) | the only entity in the game allowed 7 |
| Skeleton bones | **32** | 6 legs × 3 + 9 maw plates + 3 jaw + 6 spine + core + root = 32 |
| Animated bones at once | ≤14 | the Deck budget: maw plates animate, spines are static |
| Emissive channels | 2 (core, eye-lens) + 1 VFX (spore trail) | |
| VFX systems | 5 | spore trail, node-bite puff, rail seam, maw glow, spore-ball |
| Shadow | 1 shadow-casting spot (the reveal key) | no contact shadow when airborne |

**Deck-specific:**
- The roll is a **rotation of the root**, not an animated wheel — the body is radially symmetric
  enough that a root spin is indistinguishable and costs nothing.
- The maw open/close is **one float driving nine plates** with per-plate offsets baked into the
  skeleton — nine curves, not nine timelines.
- At 'low', the spore trail is a single Niagara system with a 32-particle budget.
- Total in-frame cost with the Harvester + 6 Chryssalids + the level: **must stay under
  100k visible triangles** and 5 dynamic lights.

---

## 4. The arena: the manifest

The Act III arena `M_Harbor03` is a **12×12 grid of cells**, 4,000 uu across (same footprint as
`M_Blockout01` so the existing level tooling and camera rig reapply).

### 4.1 Power nodes

**12 power nodes** stand on the grid intersections — physical objects with geometry, a light,
and a name. When the Harvester eats one, **the object is removed from the level** and the cell
it stood on becomes open ground.

| Node | Type | Grid position | Consumed at | What it was |
|---|---|---|---|---|
| `PN_01` | **Crane leg** | NW | Phase I, 20 s | A dock crane's leg — tall, lattice-iron, casts the arena's best shadow |
| `PN_02` | **Container stack** | N | Phase I, 20 s | Two shipping containers, the classic |
| `PN_03` | **Pillar** | NE | Phase I, 20 s | A stone bollard-pillar |
| `PN_04` | **Bollard** | W | Phase I, 20 s | Cast-iron mooring bollard |
| `PN_05` | **Container stack** | E | Phase I, 20 s | |
| `PN_06` | **Lamp mast** | SW | Phase II, 12 s | A sodium lamp — killing it **removes light from the arena** |
| `PN_07` | **Gantry segment** | S | Phase II, 12 s | An overhead gantry leg |
| `PN_08` | **Crane leg** | SE | Phase II, 12 s | |
| `PN_09` | **Tide gate** | centre-N | Phase II, 12 s | A huge iron tide gate, the biggest silhouette on the map |
| `PN_10` | **Breakwater** | centre-S | Phase III (never — arena is too small) | |
| `PN_11` | **Watch house** | centre-W | Phase III (never) | |
| `PN_12` | **Signal mast** | centre-E | Phase III (never) | |

**Rule (anti-frustration):** the arena **never reduces below a 12×12 uu safe island at the
centre**. When no further node can be consumed without violating that, the boss **stops eating**
and the fight becomes pure DPS. This is checked by the arena logic, not by the level designer
hoping for the best.

### 4.2 The rail

The outer ring of the 12×12 grid is a **rail**: a 3,000 uu perimeter track, visible as a
**glowing seam** in the floor plating. The Harvester's roll runs on it.

- The seam **illuminates 0.8 s before every roll** (the telegraph). It is never off.
- The seam has **one gap**, at the south-west, where the tide gate `PN_09` meets the rail. The
  Harvester **cannot cross the gap** — it has to come off the rail to change direction. This is
  the player's "get behind it" window and it is the only reliable damage window in Phase III.
- The rail is 3,000 uu around, so a full circuit at 1,100 uu/s takes **2.7 s**. A Phase III roll
  is therefore a 2.7-second pass the player can survive by moving 900 uu.

### 4.3 The other consumable — dropped nodes

**Enemy-dropped nodes.** Each Chryssalid the Harvester spawns drops a **spore-node** on death:
a small, glowing, walk-over pickup. It is **edible by the Harvester** (heals it 120 HP) and
**also edible by the player** (a 40 HP health pickup, because it is full of processed
spore-matter). This is the game's only "pick up the enemy's food" moment and it is deliberately
ambiguous: the thing that saves you is the thing that feeds it.

---

## 5. The fight

### 5.1 The core loop

```
   ┌─► node in world ──► player SHOOTS it (denies heal, costs the pickup)
   │                    └─► Harvester reaches it ──► EATS it (+heal, +arena shrink)
   │
   └─► Harvester's mouth OPEN (1.2 s after each bite) ──► player hits the mouth (x2 damage)
```

The player is always choosing between:
- **Shooting the boss** — always available, always the small-damage play.
- **Shooting the node** — removes the boss's heal AND removes the player's pickup AND removes
  cover from the arena (a container stack was cover).
- **Leaving it** — free, but the boss heals 120 and the arena loses a wall.

### 5.2 Phase table

| Phase | HP | Node cadence | Movement | New behaviour | Taunt phase |
|---|---|---|---|---|---|
| **I — GRAZE** | 100–66% | 1 node / **20 s** | Grid-locked, 200 uu/s | `bite` (1.4 s tell) `roll` along the rail (1.8 s tell) | 1 |
| **II — SWALLOW** | 66–33% | 1 node / **12 s** | Grid-locked, 260 uu/s | + `famine-lunge` (1.0 s tell, 700 uu/s straight line, 55 dmg) · spawns 2 Chryssalids per node eaten | 2 |
| **III — ROLL** | 33–0% | **stops** (arena too small) | **continuous roll, 1,100 uu/s** | Cannot stop. Only the rail-gap window and the open mouth hurt it. `shriek` (foghorn) on entry. | 3 |

### 5.3 Damage model

| Weak point | Multiplier | Availability |
|---|---|---|
| **Open mouth (inner maw)** | **×2.0** | 1.2 s after every bite, and 1.4 s after every grid turn. It is *always* reachable if you are close — and being close is what the roll punishes. |
| **Exposed back (while rolling)** | **×1.5** | Only in Phase III, only from the rail gap, only during the 0.8 s pass. |
| **Body (all other times)** | ×1.0 | |
| **Node (player shooting it)** | n/a | 120 HP heal denied |

**Base HP:** 5,600 (Phase I) — the Harvester is a **tank** and it is meant to be. It is not a
bullet sponge; it is a *geometry* boss, and the fight is won by denying it food, not by
out-DPSing it. TTK with a clean ×2.0 mouth window, Mayflower Cannon at 250 dmg: **≈ 23 s**.
With a Rocket at 120 direct + 60 splash: **≈ 41 s**. The player is *supposed* to be slower than
that. The fight is supposed to be about the arena, not the damage number.

### 5.4 The three-phase transition tells

Each transition is a **1.2 s freeze + a foghorn sustain + a HUD change**, so the player always
knows the rules just changed:

| Transition | What happens |
|---|---|
| **I → II** (66%) | The Harvester **stops eating for 3 s** and howls. The HUD manifest row for the current node fills in. Two Chryssalids crawl out of the maw. The rail seam starts to glow on both sides. |
| **II → III** (33%) | The **foghorn sounds** — the 1926 horn that killed nine men. The Harvester seals its maw, the legs fold into the tripod, and the body begins to spin. The rail seam goes from a hint to a hard line. The HUD shows the manifest **complete**. |
| **III → death** | The body **spins down** over 2.5 s, the maw opens one final time and does not close, and the spore-mass vents upward as a column. The bombast: the foghorn, cut short. |

---

## 6. Anti-frustration guarantees (binding on the build)

1. **No un-telegraphed damage.** Every attack has a visible tell AND an audible tell, and the
   tell duration scales with damage (0.6 s ≤10 dmg → 1.8 s ≥45 dmg), matching the game-wide
   contract. The `famine-lunge` at 55 dmg gets 1.0 s — which is *below* the 1.8 s the global
   rule would imply, so **the lunge's damage is reduced to 45** to keep the global rule honest.
2. **The rail seam is never off.** The player always knows where the roll will travel.
3. **The safe island.** 12×12 uu at the centre, enforced by the arena logic.
4. **The mouth always opens.** 1.2 s after every bite. The player is never locked out of the
   ×2.0 window for longer than 1.4 s (the grid-turn interval).
5. **No instant death.** Every hit is survivable on full health, and the arena is always
   navigable to the safe island.
6. **The fight cannot stall.** If the player has not damaged the Harvester for 8 s, the boss
   **stops eating** (it can only be inedible by the player, never un-attackable) and the fight
   becomes DPS. The arena can never become a place where no damage is possible.
7. **Ammo sufficiency.** The Harvester fight is budgeted at 6 Rockets + 4 Cannons (from the
   Arena's ammo economy) with a **1.35× multiplier** applied over the Arena, because this is
   the hardest fight and running dry is acceptable *only* if it is a choice, not a surprise.

---

## 7. Voice — the Harvester speaks

The Harvester's dialogue is the **insult bank**: 40 lines of cheerful, half-finished, glitchy
non-sequiturs in three phases, matching the three boss phases exactly.

**The character's voice, in one line:** it is filling in a shipping manifest and it is
**cheerfully, pathologically helpful**. The comedy is that it wants to help you. The threat is
that it is a *process*.

The full contract — schema, safety rules, selection, timing, render pipeline, and the WAV
format the Rust side parses — is in **`Docs/generated/insult_bank_contract.md`**.

### 7.1 Voice at a glance

| Property | Value |
|---|---|
| Lines | 40 (13 / 14 / 13 across phases 1/2/3) |
| Max length | 15 words (longest line in the bank: 10) |
| Engine | F5-TTS, HTPC, `http://10.0.0.42:8020/synth` |
| Voice | selected by the **`ref`** field — `harvester` (phases 1–2), `harvester_low` (phase 3). **Not `voice`**: the service accepts `voice`, silently ignores it, and renders the default register, so a typo produces a wrong-character render with no error. An unknown `ref` returns HTTP 400. |
| Output | service: RIFF/WAVE, PCM s16le, **mono, 24,000 Hz**. **Delivered: 44,100 Hz, 16-bit mono**, −16 LUFS, true peak below −1.0 dBTP, 0 clipped samples |
| Rendering cost | measured: 2.61 s of audio for a 2-word line in **93 s** wall; ~63 s for the same line. **Roughly 15–25× realtime on CPU.** |
| Selection | pure Rust: phase-gated, no immediate repeat, 1.5 s minimum gap, 6 s max gap |
| Priority | the taunt channel ducks the music bed by 6 dB and never ducks weapon SFX |
| Contract | `Content/Audio/Insults/insults_manifest.json` (read `index`, `phase`, `voice_ref`) — handover in `Docs/generated/audio_handover.md` |

### 7.2 Phase-gated examples (from the bank, verbatim)

- **Phase 1** — *"Hello! Would you like to file a complaint about the weather inside my mouth?"*
- **Phase 2** — *"Wrong. Wrong. Wrong. That is not the error code. Wrong. Thank you for confirming wrong."*
- **Phase 3** — *"I will not delete you. Deleting is for files. You are a file. Oh no. You are a file."*

---

## 8. Photograph plan (Ebert evidence)

This boss is a **boss** and therefore the hardest thing in the game to photograph well, because
Ebert's "first-impression impact" axis and his "visual craft" axis both peak on the boss frame.

| # | Frame | Requirement | Why it exists |
|---|---|---|---|
| 1 | **Hero — grinding pose** | 3/4 front, maw **open**, reveal rig, 720×900+, full body, uncropped, ground plane with contact shadow | proves the maw is the largest opening on the body |
| 2 | **Hero — rolling pose** | side view, body a disc, six legs tucked, spine ridge silhouetted | proves the two-pose silhouette rule (§3.1) |
| 3 | **Silhouette plate** | pure black on flat mid-grey, both poses | Rule S1 proof; Ebert's v1 top fix |
| 4 | **Turnaround** | front / 3-4 / profile, grinding pose | |
| 5 | **Scale** | 1.8 m human reference — the Harvester is **3.40 m** and towers | |
| 6 | **Emissive proof** | lit by only its own emissives (core + eye-lens + spore trail) | proves the glow emits |
| 7 | **Studio vs reveal** | side-by-side | the lighting bar |
| 8 | **In-engine, Act III arena** | at gameplay camera distance, 1.6 m eye height, real FOV, with a Chryssalid for scale | Ebert's "in-engine at real camera distance" bar |
| 9 | **The 12 power nodes** | one orthographic line-up of all 12 nodes, true relative scale | proves the consumable set exists and is legible |
| 10 | **The rail + gap** | a top-down frame of the arena showing the rail seam and the single SW gap | proves the Phase III damage window is real and findable |
| 11 | **Mid-fight frame** | the maw open, one node mid-consumption, spore trail, 2 Chryssalids alive | the "mid-action" game screenshot the rubric requires |
| 12 | **Death frame** | the final spin-down, maw open, spore column | the "score-or-failure state" the rubric requires |

**Minimum for a score: 12 frames.** The rubric's game rule is *idle, mid-action, and one
score-or-failure state*; the rest are the boss-specific bar. **Submitting fewer than 12 is
INCOMPLETE and no score is issued.**

**Honesty rule.** If a frame does not exist, the category is marked **UNSCORED**. A stand-in
image is a fabricated result and sets Truthfulness to 1.0.

---

## 9. Build order

| # | Task | Deliverable | Depends on |
|---|---|---|---|
| 1 | Blender model of the Harvester, 2 poses | `Tools/blender/out_boss/harvester.fbx` + manifest entry | — |
| 2 | Silhouette plate, both poses | `harvester_silh.png` | 1 |
| 3 | Reveal-rig hero renders, both poses | `harvester.png`, `harvester_roll.png` | 1 |
| 4 | Material split (7 materials, oxblood on 6 spurs only) | in manifest | 1 |
| 5 | Act III arena `M_Harbor03` with 12 nodes, rail, gap, safe island | `.umap` + `level_stats.json` | — |
| 6 | Rust: node table, phase machine, damage multipliers, safe-island check | `harvester.rs` + unit tests | 1, 5 |
| 7 | Rust: taunt selection + phase gating + cooldown | `taunts.rs` + unit tests | `insult_bank_contract.md` |
| 8 | Render the 40-line insult bank (fix the payload key first) | `Content/Audio/Insults/*.wav` | `insult_bank_contract.md` |
| 9 | In-engine gameplay frames at 1.6 m | 8+ frames | 3, 5, 6 |
| 10 | Submit to Ebert | evidence pack | 1–9 |

**Task 6 is the one that must not be skipped.** The safe-island rule, the stall rule and the
phase-cadence table are *logic*, and if they are implemented in Blueprint and then reimplemented
in Rust, they will drift. They are specified once in `Docs/generated/boss_bible.json` and
generated into both sides from that file.

---

## 10. Definition of done

- [x] Concept, silhouette, palette, materials, and a per-part budget
- [x] Arena design: 12 power nodes, the rail, the single gap, the safe island
- [x] Three phases with cadence, movement, new behaviours and taunt phase
- [x] Damage model with the ×2.0 mouth window and ×1.5 exposed back
- [x] Seven binding anti-frustration guarantees
- [x] Rust/engine split, with the safe-island and stall rules explicitly in the logic column
- [x] 12-frame photograph plan mapped to Ebert's bar
- [x] Ordered build plan with dependencies
- [ ] **The model.** Not built.
- [ ] **The arena.** Not built.
- [ ] **The renders.** None exist.
- [x] **The audio.** The 40-line insult bank is **rendered, normalised and measured**. All 40 verify clean: −16.4…−15.7 LUFS, true peaks −2.2…−1.4 dBTP, 0 clipped samples, 5.841–5.866 s, 44 100 Hz 16-bit mono. Four procedural SFX delivered alongside. Manifest (the playback contract) at `Content/Audio/Insults/insults_manifest.json`; handover at `Docs/generated/audio_handover.md`.

*Every figure in this document is a design target and is labelled as one. The measured
values are the TTS service's output format and render latency, the audio lane's delivered
loudness/duration measurements (all 40 taunts and all 4 SFX, measured on the delivered
files), and the node's live inference health. They are marked measured.*
