# MEGAJAM RULES NOTES — v01
### Document ID: `MEGAJAM_RULES_NOTES_v01` · 2026-11-12 (jam D1) · Owner: Commander · Executor: Hermes
### Source of truth: https://itch.io/jam/2026-epic-ai-megajam + Epic kickoff stream (Nov 11) + epicgames.box.com Official Rules

---

## 1. THE FACTS (verbatim where quoted)

| Field | Value |
|---|---|
| Jam | 2026 Epic AI MegaJam |
| Window | **Nov 12, 12:00 AM ET → Nov 15, 5:59 PM PST (8:59 PM ET)** — submissions open Nov 12 05:00 UTC, close Nov 16 01:59 UTC |
| Theme | **DIRECTOR'S CUT** — Epic (Nov 11 kickoff): *"This year's MegaJam Theme is... DIRECTOR'S CUT! Your vision, your specific edits and ultimately: your final cut - your Director's Cut"* — "the feature that didn't make it, the mechanic scoped out at 2 AM, or an idea you've been holding on to" |
| Engine | Unreal Engine **or** UEFN — **not both** (we: UE 5.8) |
| AI | Any tools, unlimited agents, **not required** |
| Prizes | $65,000 cash + Development Continuation Grants up to $50,000/team + partner prizes |
| Categories (known) | Best Team ($5,000) · Render Royalty ($2,500, best visuals) · **Glass Box** (dev log showing the AI workflow) · Best Overall UE · Ambition · Fun · Pocket Powerhouse UE · Best Student (conditional) |
| Judging | 7 criteria, scored 1–5: ambition/innovation, **theme**, fun, gameplay, visuals, level design, audio |
| Who | 18+, active Epic Games account |
| Winners | notified on/about **Jan 29, 2027** |

## 2. ALLOWED / NOT ALLOWED (jam page, verbatim two columns)

✅ Any AI tools: coding agents, asset generation, audio, writing, anything
✅ Solo or team of ≤5 humans; no limit on agents
✅ Assets you didn't make (Fab etc.) with the right license — **list them in submission**
✅ Build custom gameplay beyond Epic's starter templates

❌ **Don't start building your game before November 12. Declare anything you made earlier.** (prompts, scripts, agent skills, assets — keep a list, include with entry)
❌ Don't enter with both UE and UEFN
❌ Don't submit unpackaged UE projects
❌ No content that breaks Official Rules, including **other people's IP** and inappropriate content

## 3. WHAT TO SUBMIT

| Item | Spec |
|---|---|
| Game | **Packaged UE development build** — Win64 playable on Win10/11 (also macOS/Android/iOS), `.zip` named `TeamName_GameName`, **< 1 GB** (itch butler for bigger) |
| Video | **30–60 s gameplay video** — gameplay in the first five seconds |
| Details | team name, each member's name + Epic account email |
| Third-party assets | listed with pack name, creator, license |
| Pre-jam declaration | every prompt/script/asset made before Nov 12 |
| Glass Box | dev log (optional otherwise, **required for the category**) |
| Late | **disqualified** — submit early |

## 4. HARD CONSTRAINTS THIS IMPOSES ON OUR ENTRY

1. **Theme is mandatory.** "Using the theme is one of the seven judging criteria." Our read: the whole game is about what makes the final cut — choices that decide who is saved, the System's edited version of reality vs the Commander's. The jam slice must show this on screen, not just in lore.
2. **The declaration ledger is a ship-critical artifact.** Everything predating 00:00 ET Nov 12 gets listed: UE project shell (71 uassets), M_Blockout01 + 14 FBX blockouts + 18 encounter actors, Plymouth OSM corridor, 5 enemy meshes (out_xcom), core-four crew FBXs, 15 insult WAVs, 19 TTS voices, packaged exe + PSO lane. **The jam BUILD = the new work we make Nov 12–15** — the R2 "Run Home" slice, new encounters, theme integration, new art pass. Pre-jam pieces are declared, never hidden.
3. **IP gate = Official Rules.** X-COM kit must be IP-clean before submission (see IP_CLEANSE gate in 7D plan §15). This is a disqualification-class risk if missed.
4. **One engine, one team.** We enter as the Gillsystems team (Commander = sole human), UE track only.
5. **Gameplay, levels, art must be made during the jam** (kickoff statement). The blockout shell is declared infrastructure — the *playable content* we ship is what we build these 4 days.

## 5. OUR ANGLES (from 7D plan §4, re-confirmed)

- **Glass Box** — the honest AI-native dev log: one workstation + three appliances, fleet of agents, sovereign local inference, geodata-built 102 sq mi corridor. This is our differentiation; almost nobody else can show this pipeline.
- **Render Royalty** — visual craft: real Plymouth night lighting, horror fog, hero waterfront shots.
- **Theme (Director's Cut)** — our story layer IS the theme. Strongest of the three.

## 6. TIMELINE (jam-local)

| When (ET) | What |
|---|---|
| **NOW (Nov 12 03:00)** | D1: rules notes (this doc) · IP cleanse · FSR-only config · UE seat verify · PSO pre-cache on Deck |
| Nov 12 (D1) | Jam-slice scope lock: R2 "Run Home" playable slice + theme beat + 2–3 encounter types + finish state. Combat loop (Track 4) build — headless where possible, editor where not. |
| Nov 13 (D2) | Content passes: new enemy visuals pass (IP-clean bestiary names), level dress on the corridor, audio (TTS batch on HTPC), cutscene beats (Sequencer on Main) |
| Nov 14 (D3) | Integration, Ebert gate (≥6.2, no axis at 1.0), package, **run the real exe**, Deck validation, 30–60 s capture video |
| Nov 15 | Polish, final package < 1 GB, **submit by 8:59 PM ET** — target 6:00 PM for buffer. Dev log (Glass Box) finalized. |

## 7. DECISION LOG (Hermes, no-input needed)

| # | Decision | Why |
|---|---|---|
| D-01 | Jam entry = **playable Plymouth R2 slice** ("The Run Home"), not the full 102 sq mi build | 4 days; the slice is completable, jam-scope, and carries the theme |
| D-02 | **Declare the entire pre-jam inventory** in the submission details + dev log | rules require it; Glass Box *wants* the provenance; honesty is the differentiator |
| D-03 | IP cleanse executes **before** any jam content ships | Official Rules: other people's IP = rules violation |
| D-04 | FSR-only render config (DLSS/StreamlineNGX/XeSS off) | all-AMD fleet; §14c of the plan |
| D-05 | **PSO pre-cache = top Deck fix** | the packaged build currently fails on first runtime PSO (E_INVALIDARG) — the one verified blocker to a clean packaged run |
| D-06 | Submit target **6:00 PM ET Nov 15**, hard deadline 8:59 | late = DQ; itch upload of ~1 GB needs bandwidth headroom |
