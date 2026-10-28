# THE COMMANDER: PLYMOUTH — GAME DESIGN
### `GDD-PLY-001` · v01 · 2026-10-28 · Owner: Commander Stephen Gill · Executor: Commander Hermes

---

## §0 — COMMANDER DIRECTIVES (2026-10-28, verbatim intent)

| # | Directive | Disposition |
|---|---|---|
| 1 | Crew **3** squad companions | **LOCKED** — RIGGER / SABLE / PARSON |
| 2 | **No agent real names** in the game | **LOCKED** — `geordi`/`liara`/`medic`/`edi` are internal voice keys only, never shipped |
| 3 | No named heavyweight at McGovern | **LOCKED** — generic heavy unit |
| 4 | HTPC during asset sprint | **CLOSE INFERENCE** — done, 5.9 GB freed |
| 5 | Seedance | **NO — hold off** — MiniMax H3 local only |
| 6 | Genie 4 | **NO** |
| 7 | MegaJam | **MAYBE** — not a dependency, our game is the goal |
| 8 | **NEO BERLIN 2087** | **THE VISUAL TARGET** — "exactly what we want" |
| 9 | Cyber alt-future map you can **flip into** | **BUILD IT** |
| 10 | FPS → **3rd person + bullet time** | **BUILD IT** |
| 11 | Crew weapon wheel **like Mass Effect** | **BUILD IT** |
| 12 | **EDI** modeled after Gillian Anderson, **she smokes** | **BUILD IT** |
| 13 | Squadron 42 has her modeled — **steal what you can** | **DO IT** |
| 14 | **UE stock assets** where possible, don't build what's free | **MANDATE** |
| 15 | Threats include **drones launched inbound from the water** | **BUILD IT** |
| 16 | Must look **as good as that new game** | **NEO BERLIN 2087 BAR** |
| 17 | **Optimize for performance** | **MANDATE** |
| 18 | Good **title screen + options screen** | **BUILD IT** |
| 19 | YOLO execution, all nodes, until **Ebert says good state** | **ACTIVE** |

---

## §1 — THE PITCH

You are **THE COMMANDER**. A real 102 sq mi Plymouth–Duxbury, Massachusetts corridor — your actual commute, your actual streets, the actual ocean.

Then the sky tears open and **the machines come in off the water.**

A cyber-kitted electric scooter. A three-person squad on comms. A coastal town under assault by drones that launch from the sea.

**Two worlds, one map.** Flip between the real Plymouth and **Plymouth 2087** — the same streets, drowned in neon, wet with rain, stacked with holograms and corporate towers where the storefronts used to be.

---

## §2 — THE TARGET BAR: NEO BERLIN 2087

> "IT better look as good as that new game. Ours will be better and come to market quicker."

| Property | NEO BERLIN 2087 | Ours |
|---|---|---|
| Genre | Cyberpunk immersive sim | Cyberpunk action shooter |
| Setting | Alternate-history Berlin | **Alternate-future Plymouth/Duxbury** |
| Bar | Premium AAA-adjacent visuals | **Match or beat** |
| Advantage | Large team, long cycle | **Sovereign hardware, no budget, speed** |

### What we take from it (techniques, not assets)
- **Neon-soaked wet-night lighting** — emissive signage density, puddle reflections, volumetric haze
- **Teal/magenta/gold grading** with heavy bloom and chromatic aberration at the edges
- **Verticality + holographic UI litter** layered on real architecture
- **Rain as a system** — wet material response, ripples, drips, reflections on everything
- **Dense environmental storytelling** — signage, graffiti, trash, propaganda

### What we do NOT do
- Copy assets, characters, logos, names, or story
- Take the genre-name convention ("2087" is fine as an internal art-bible tag, not a shipped subtitle)

---

## §3 — THE FLIP: TWO STATES OF ONE MAP

The map is **one persistent 102 sq mi world** with two render states.

| | **STATE A — "Shoreline"** | **STATE B — "Plymouth 2087"** |
|---|---|---|
| Era | Now | Alternate future |
| Look | Real coastal Massachusetts at night | Neon cyberpunk, rain-soaked, holographic |
| Buildings | Real OSM massing, brick/wood/vinyl | Same massing, re-skinned: black glass, emissive trim, holo-signage |
| Roads | Asphalt, real markings | Wet black, glowing lane lines, maglev-quiet traffic |
| Sky | Dark coastal overcast | Smog-orange horizon, drone swarms, searchlights |
| Water | Atlantic, dark | Bioluminescent, drone launch platforms offshore |
| Population | Empty, hostile machines | Same — machines, plus corporate enforcers |

### Flip mechanic
- **Diegetic trigger** — a device, a gateway, a moment in the story
- **Instant swap** via **material + post-process + sky swap**, NOT a second map
  - Same geometry, same collision, same nav
  - World Partition cells swap a **material layer** and a **PostProcessVolume blend**
  - Niagara swaps the ambient VFX set (rain, holograms, drones)
- **Cost:** one material instance parameter set + one PP blend. This is the killer feature and it is cheap.

### Implementation notes
- Two **Material Parameter Collections**: `MPC_State` (0 = Shoreline, 1 = 2087)
- Every surface material lerps between two looks on `MPC_State`
- `PostProcessVolume` blends: bloom, grading, vignette, chromatic aberration, fog color
- Lumen GI re-solves per state — anchor the emissive budget so the 2087 state doesn't blow the frame
- **Performance guard:** the 2087 state is the expensive one. Budget for IT, then Shoreline is free headroom.

---

## §4 — CAMERA & MOVEMENT

### 4a. FPS ↔ 3rd person toggle
| Mode | Use | Feel |
|---|---|---|
| **FPS** | Aim, precision, interior, tight corridors | Immersion, weapon weight |
| **3rd Person** | Melee, traversal, scooter riding, squad visibility | Hero read, spatial awareness |

- **Hot toggle** — one input, no menu, no reload
- **Spring arm + camera lag**, tuned per mode (FPS: no lag, tight; 3P: lag + slight orbit follow)
- **Weapon alignment** uses a shared `AimOffset` so the same animation drives both
- On the **scooter** the camera auto-promotes to 3rd person (you need to see the bike and the road)
- **Animation warping** for strafe and lean so 3rd person doesn't foot-slide

### 4b. Scooter — the ride
Real spec baked to physics (from the actual Laped folding e-scooter):

| Condition | Speed |
|---|---:|
| Flat | **22 mph** cap |
| Down 3 % | 24 |
| Down 6 % | 27 |
| Down 9 %+ | **30** gravity cap |
| Up 4 % | 16 |
| Up 8 %+ | 11 |
| Off-road | 65 % of current |

`v = clamp(22 + 1.1·grade, 22, 30)` down · `v = 22 − 1.4·|grade|` up · grades sampled every **30 m**.

**Mount / dismount** animated, interruptible. Cyber-kitbash: glowing trim, armor panels, weapon mounts, a HUD slaved to the dash.

---

## §5 — BULLET TIME

Slow motion is a **core verb**, not a power-up.

| Property | Spec |
|---|---|
| Trigger | Input hold / killstreak meter / low-health adrenaline |
| Global time dilation | **0.25–0.35** (player stays near 1.0 — `CustomTimeDilation`) |
| Camera | Slight FOV punch-in, reduced camera shake frequency |
| Audio | Global pitch drop + ducking, heartbeat layer, weapon reports become *cracks* |
| VFX | Niagara: radial blur edges, light trails on projectiles, floating debris/embers |
| UI | Subtle vignette + desaturation at the border |
| Exit | Smooth ramp back over 0.2–0.4 s, never a hard snap |

**Feel references:** Max Payne shootdodge, Vanquish slide-slowmo, Mass Effect 1 Marksman.
The rule: **the player should feel faster in slow motion, not slower.**

Implementation: `UGameplayStatics::SetGlobalTimeDilation` on a curve, per-actor `CustomTimeDilation` for the player and their weapons, Niagara `User.TimeDilation`, and an audio parameter that drives pitch/ducking off the same curve.

---

## §6 — THE WEAPON WHEEL (Mass Effect style)

Radial menu, **time-dilates to ~0.15 while open**, squad-aware.

### Layout
```
                    [ WEAPON 1 ]
        [ SQUAD POWER ]        [ WEAPON 2 ]
   [ GRENADE ]                        [ WEAPON 3 ]
        [ SQUAD POWER ]        [ WEAPON 4 ]
                    [ CONSUMABLE ]
```

| Slot type | Examples |
|---|---|
| Weapons (4) | sidearm, SMG, rifle, heavy |
| Squad powers (2) | RIGGER turret / SABLE cloak mark / PARSON revive |
| Grenade | frag, EMP, smoke |
| Consumable | **48 oz iced coffee** (heal / stamina), med-kit |

### Behaviour
- **Left stick / mouse** rotates the selection
- **Shoulder buttons** swap between weapon page and squad-power page
- **Squad page** selects a power *and* the squad-mate who casts it — Mass Effect's chain: SABLE marks → RIGGER overloads → PARSON revives
- Highlights the hovered entry with a VFX + audio tick
- Never fully pauses — the fight keeps breathing at 0.15×

Enhanced Input: one `IMC_UIMap` with the wheel axis, and a `WidgetBP_RadialWheel` that reads the axis to rotate the highlight. No custom C++ needed for v1.

---

## §7 — THREATS

### 7a. The water is the vector
> "AI robot threat can be drones launched inbound from the water etc."

| Threat | Origin | Behaviour |
|---|---|---|
| **SURGE** — USV (unmanned surface vessel) | Open ocean | Runs the surf line, launches aerial drones, detonates on the pier |
| **TIDEWALKER** — UUV | Undersea | Hits piers, boats, foundations; surfaces to deploy |
| **FROM THE WATER** — launch swarm | Offshore mothership | Drones lift off the water surface and come inland |
| **OVER THE HORIZON** — aerial swarm | High altitude | Cruise in, drop sub-munitions over the retail strip |
| **LOCUST** — beach quadrupeds | Long Beach spit | 3-mile beach assault, flanking up the sand |

### 7b. The full roster (16 units)
**Flesh — 5:** GRAYTIDE · RATLINE · DRIFTER · BULWARK · HARROWER
**Machine — 11:** MITE · LANCE · SENTRY · SPINNER · HOUND · PACKMASTER · WOLFPACK · GOLIATH · CARRIER · WARDEN · ANVIL
**Plus the water vector:** SURGE · TIDEWALKER (replacing two of the machine slots, keeping 16 total)

**Ladder:** MARK I → II → III → IV.

### 7c. Fight zones
| Zone | Enemies |
|---|---|
| Pilgrim Hill — CVS / Walgreens | massed MITEs + HOUND packs |
| McGovern Chevrolet | generic heavy + BULWARK escort |
| McDonald's / Samoset strip | mixed flesh + SENTRY overwatch |
| Seven Hills / South Meadow | traffic hazard + WARDEN jamming your scooter |
| Power station + transmission lines | ANVIL turrets, DRIFTERs on the wires |
| Oak St | ambush corridor, SPINNER (no easy out) |
| **Long Beach / the surf line** | **SURGE + TIDEWALKER + LOCUST** — the signature assault |

---

## §8 — EDI

Modeled after **Gillian Anderson**. **She smokes** — it is core to the read.

| Property | Spec |
|---|---|
| Height | ~170 cm, 1:1 human scale |
| Face | High, prominent cheekbones (dominant plane); tapered V-jaw, soft not square; low-to-moderate brow ridge; straight narrow nose, small slightly-rounded tip; full lips with a sharp cupid's bow, lower lip plumper; rounded chin with subtle point; oval/heart skull, wider at the temples |
| Eyes | Almond, slightly upturned outer corners; heavy smoky winged eyeliner |
| Hair | Two viable reads from reference — **platinum, long, straight, off-center part** (noir) OR **copper-auburn, shoulder-length, side-swept** (dusk). **Art direction picks at D2**; the noir cigar look is the stronger silhouette |
| Skin | Low facial fat, sculpted "old-Hollywood" bone structure, hard shadow plane under the cheekbones |
| Signature | **Cigar / cigarette** — held in the fingers, ember shader, Niagara smoke, hand-to-mouth loop |
| Wardrobe | Tailored, severe, dark — she reads as command, not combat |

### Likeness approach (steal from Squadron 42 where we legally can)
- **Silhouette-first sculpt.** At game camera distance the silhouette and the cheekbone/lip read carry the likeness. Get those right before any pore detail.
- **Head scan is not available** — sculpt from the two reference plates. Use **MetaHuman Creator** if a custom sculpt can be driven in 5.8; otherwise a hand-sculpted head with baked normal/AO/microdetail.
- **Eyes sell it.** Parallax cornea, iris depth, wet-line. This is where cheap characters fail.
- **Skin:** pre-integrated subsurface, dual-lobe specularity, subtle micro-normal. Avoid plastic.
- **Hair:** hair cards (game-cheap) over strand groom. Long platinum hair = cards with a strong specular sweep.
- **Smoking:** Niagara smoke + emissive ember + a `hand-to-mouth` montage. Never a static prop.

**Internal voice key `edi` → shipped as `VO_EDI_*`.** The word "EDI" and the actress's name never appear in shipped filenames.

---

## §9 — UI

### 9a. Title screen
- **Hero plate:** the cyber-Plymouth skyline over the harbor, rain, neon reflecting on the water, the scooter silhouette
- Animated: slow camera drift, falling rain, flickering sign, distant drone swarms
- Menu: **NEW GAME · CONTINUE · LOAD · OPTIONS · EXTRAS · QUIT**
- Audio: low synth drone, rain bed, occasional distant explosion
- FSR-friendly: no full-screen post chain just for the menu

### 9b. Options screen — "all the normal options"
| Tab | Options |
|---|---|
| **Display** | Resolution · Window mode (Fullscreen / Borderless / Windowed) · VSync · Frame rate cap · **Upscaling (FSR Quality / Balanced / Performance / Native AA)** · Motion blur · Film grain · Chromatic aberration · Bloom · Lens flare · FOV slider · HUD scale · Brightness / HDR calibration |
| **Graphics** | Scalability preset (Low→Ultra) · View distance · Anti-aliasing (TSR/FSR) · Shadows · Global Illumination (Lumen) · Reflections · Post-processing · Textures · Effects · Foliage · Shading |
| **Audio** | Master · Music · SFX · Dialogue · Ambient · **Voice cast volume** · Dynamic range · Subtitles on/off + size + background |
| **Controls** | Input remap (mouse/keyboard + gamepad) · Mouse sensitivity + smoothing + invert · Gamepad deadzone + vibration · **Camera mode default (FPS / 3rd Person)** · **Bullet time toggle (hold / toggle)** |
| **Gameplay** | Difficulty · Aim assist · Damage numbers · Camera shake · Subtitles · Language · **Squad command verbosity** |
| **Accessibility** | Colorblind mode · Subtitle size · UI scaling · Hold-to-toggle · Screen shake strength · Flash intensity |

Everything writes to `GameUserSettings.ini`, and the **FSR dropdown is first-class** because we are AMD-only.

### 9c. Performance mandate
| Budget | Target |
|---|---|
| 1080p / FSR Balanced | **60 fps** on an RX 7600 class |
| 1440p / FSR Quality | **60 fps** on RX 7900 XTX |
| Deck | **40 fps** at FSR 3.1.5 Performance, dynamic resolution on |
| Frame time | **< 16.6 ms** steady, no spikes over 25 ms |
| Draw calls | < 2,500 per frame |
| Material instances | Shared via MPC, no per-object unique materials |
| Nanite | On for hard-surface static meshes |
| Lumen | Software fallback path kept for lower presets |
| Instancing | PCG for foliage/scatter, ISM for all repeated props |
| Only one heavy post chain | Rain/wetness baked into materials where possible, not full-screen |

**Every asset gets a LOD chain and a budget. Every system gets a stat budget. Anything that misses gets cut or simplified before Ebert's gate.**

---

## §10 — UE STOCK ASSET MANDATE

> "MAke sure you're not doing stuff you dont need. Using UE stock assets where possible."

**Rule:** before any asset is modeled from scratch, an agent must prove the engine and the free ecosystem do not already supply it.

| Reuse | Examples |
|---|---|
| UE mannequins + animation | Quinn / UE5 Manny, Third Person template anims, Animation Starter Pack |
| Lyra Starter Game | weapons, abilities, UI, enemy AI patterns |
| Megascans / Quixel | surfaces, props, rocks, foliage — free with UE |
| Fab free packs | cyberpunk kits, street sets, vehicles, drones |
| Engine plugins | **PCG**, World Partition, Water, Vehicle Movement, Motion Matching, Control Rig, Niagara, Enhanced Input, **Common UI** |
| Built-in systems | Mass Entity for swarms, Behavior Trees, EQS, MetaHuman, Groom |

Anything custom is justified only when the free option is wrong for the art direction or the silhouette.

---

## §11 — SEQUENCING

| Phase | Deliverable | Gate |
|---|---|---|
| **D1** | Art bible (NEO BERLIN 2087 → Plymouth 2087 translation), IP cleanse, FSR-only config | Ebert |
| **D2** | EDI + 3 squad specs, bestiary spec, UI spec, tech arch | Ebert |
| **P1** | Crew: EDI + RIGGER + SABLE + PARSON, 25–35k tris, baked 2K PBR | Ebert ≥ 6.2 |
| **P2** | Texture bake pipeline, FBX embedded | UE import clean |
| **P3** | Bestiary 16 × MARK I–IV | Ebert |
| **P4** | Scooter + rider + cyber-kit, mount/dismount | Ebert |
| **P5** | Plymouth geo, 12 zones, both states (Shoreline + 2087) | Flythrough |
| **P6** | Voice cast (~2,000 lines) — HTPC `tts-on` → batch → `tts-off` | Spot-check |
| **P7** | Wildlife 13 species | In-level |
| **P8** | Combat: FPS/3TP, bullet time, weapon wheel, squad AI | Playable |
| **P9** | Cutscenes (H3 local) + title/options UI | Ebert |
| **P10** | Package Win64, run the real exe on Deck | **Ships** |

---

## §12 — STANDING RULES FOR THIS PROJECT

1. **Ebert is the gate.** Weighted **≥ 6.2, no rounding.** Any axis at 1.0 = categorical fail. Min 5 screenshots + console audit per artifact.
2. **No agent real names** anywhere in shipped content, filenames, or UI.
3. **UE stock assets first.** Justify every custom build.
4. **Performance is a feature.** Budget before build.
5. **Miles, mph, feet** — never metric in UI.
6. **TTS off unless actively used.** `tts-on` → batch → `tts-off`.
7. **Your GPU is sacred.** Check game launchers before touching Main.
8. **Window owns inference.** Never resurrect a dead llama-server.
9. **Local first, then GitHub.** Local File Explorer path before anything publishes.
10. **Only the most recent version is kept.** Deletion and replacement is always an option.

---

*"Let all things be done decently and in order." — 1 Corinthians 14:40 (ESV). Chosen because this is now a real product with a real bar, and beauty without order is just noise.*
