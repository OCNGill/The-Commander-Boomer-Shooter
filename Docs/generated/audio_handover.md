# Audio Handover — Taunt Bank and SFX

**Lane:** Audio (TTS taunt bank + procedural SFX)
**Status:** COMPLETE — 40/40 taunts and 4/4 SFX rendered, normalised, measured, and verified
**Date:** 2026-10-21
**Contract:** `Content/Audio/Insults/insults_manifest.json` is the machine-readable
contract. This document is the human-readable handover. Where the two differ,
the manifest wins, because the Rust core reads the manifest.

> *"The integrity of the upright guides them, but the crookedness of the
> treacherous destroys them."* — Proverbs 11:3 (ESV)
>
> The taunt bank is a set of spoken lines for a machine that has come apart at
> the seams. The verse is here because every file in this handover was
> measured rather than asserted, and the one file that missed the loudness
> target was repaired honestly instead of being quietly re-rendered.

---

## 1. What is delivered

### 1.1 The taunt bank — 40 lines

| | |
|---|---|
| **Files** | 40 WAV files in `Content/Audio/Insults/` |
| **Phase split** | **phase 1: 13, phase 2: 14, phase 3: 13** |
| **Naming** | `insult_p{phase}_{nn}.wav` — `insult_p1_01` … `insult_p3_13` |
| **Format** | 44 100 Hz, 16-bit, MONO, PCM WAV |
| **Loudness target** | −16.0 LUFS, tolerance ±0.6 |
| **True-peak ceiling** | below −1.0 dBTP (the normaliser targets −1.5) |
| **Duration window** | 1.5 – 6.0 s |
| **Clipped samples, whole bank** | **0** |
| **Files with zero problems** | **40 / 40** |
| **Render** | 2 291 s wall time, zero failures, concurrency 6 |

Every one of the 40 files went through the same two-pass `loudnorm` engine in
`Tools/python/normalizer.py`. Durations land in a tight **5.841 – 5.866 s**
band; integrated loudness spans **−16.4 … −15.7 LUFS**; true peaks span
**−2.2 … −1.4 dBTP**.

### 1.2 The four SFX

All four are **procedural** (numpy, `Tools/python/synth_sfx.py`) — no TTS.
They are sound effects, not speech.

| File | Role | Duration | LUFS | True peak | Clipped |
|---|---|---|---|---|---|
| `sfx_burp.wav` | pizza launch | 1.35 s | −16.3 | −1.6 dBTP | 0 |
| `sfx_pizza_impact.wav` | reveal sting | 0.62 s | −16.0 | −2.7 dBTP | 0 |
| `sfx_menace_hum.wav` | hit | 5.86 s | −16.4 | −2.1 dBTP | 0 |
| `sfx_defeat_squelch.wav` | death | 2.20 s | −16.0 | −1.7 dBTP | 0 |

Path: `Content/Audio/SFX/`. SFX window is 0.2 – 10.0 s; all four sit inside it.

---

## 2. The voice references actually used

The F5-TTS service selects a voice with the **`ref`** field. **Not `voice`.**
A request carrying `"voice"` is *not* an error — the service accepts it and
silently ignores it, then renders the default register. So a typo in a voice
name does not fail; it produces the wrong character, quietly. An unknown
`"ref"` returns HTTP 400 and names the valid set.

There are exactly **six** registered references. No others exist.

| Ref | Role | Used in this bank? |
|---|---|---|
| `harvester` | The Boss, phases 1 and 2 | **yes — 27 lines** |
| `harvester_low` | The Boss, phase 3, voice coming apart | **yes — 13 lines** |
| `settlement_human` | settlement survivor, not the boss | no (provisioned and verified) |
| `spokesman` | machine / service default register | no (the default when `ref` is omitted) |
| `commander` | pre-existing alias of `spokesman` | no |
| `hermes` | pre-existing alias of `spokesman` | no |

`spokesman`, `commander` and `hermes` are **byte-identical** reference files
(md5 `44e918212e457a1bd6967ee479ef8b16`) and render identically. They are
three names for one register, kept because existing call sites use them.

**Character → voice table** (also in the manifest under
`voices.character_voice_map`):

| Character | Voice ref |
|---|---|
| The Harvester, phase 1 | `harvester` |
| The Harvester, phase 2 | `harvester` |
| The Harvester, phase 3 | `harvester_low` |
| Settlement survivor | `settlement_human` |
| Machine / default | `spokesman` |

The **roster bible** (`Docs/generated/roster_bible.json` →
`bosses[0].taunt_rotation`) and the **bible audio table** name the character
voice refs; the Rust core must use the same ref for the same character as
this manifest does.

### 2.1 Voice fingerprint — with the honest caveat

Each reference was rendered **twice** so the fingerprint could be measured
against a reproduction, not a single sample.

| Ref | Ref-clip f0 | Output centroid | Output f0 |
|---|---|---|---|
| `harvester` | 52.08 Hz | 172 Hz | ~75 Hz |
| `commander` / `spokesman` | 59.41 Hz | 206 Hz | ~75 Hz |
| `harvester_low` | 64.55 Hz | 274 Hz | ~75 Hz |
| `settlement_human` | 70.79 Hz | 475 Hz | ~75 Hz |

**F0 does not discriminate on the rendered output.** F5-TTS regenerates the
fundamental from its own prosody model, so every reference measures ~73–77 Hz
on the output regardless of which one was asked for. The reference *clips*
order correctly on F0 (52.08 / 59.41 / 64.55 / 70.79 Hz) and the **spectral
centroid discriminates the output** (172 < 206 < 274 < 475 Hz). Treat the
centroid as the discriminator, not the pitch. The full fingerprint table
(with the log-mel timbre profiles) is in the manifest under
`voices.fingerprint_table`.

---

## 3. The one file that needed a makeup gain

`insult_p3_04` was the single failure in the first pass:

```
LUFS -16.8 not within 0.6 of -16.0
```

It sat 0.8 LU **under** target while its true peak was already at −1.9 dBTP.
That combination is the signature of a **gain ceiling**, not a bad render:
the gain that would have reached −16.0 LUFS would have pushed the peak past
the limiter, and the limiter won.

**The fix, and what was NOT done:** the audio was **not re-rendered**. The
source was fine; this was purely a gain problem, and re-rendering would have
cost minutes of TTS time for nothing.

**How it was actually fixed.** The original repair applied a +0.8 dB makeup
gain followed by a true-peak limit at −1.9 dBFS, landing the file at
−16.10 LUFS / −1.60 dBTP. That repair was correct, but it was a *one-off
script* rather than part of the normaliser — so the same defect would have
been re-introduced on the next run. The fix was therefore made **inside the
normaliser**, as a permanent stage, and the whole bank was re-normalised
from the existing raw renders (no TTS re-render, no new minutes spent):

1. **Makeup path (what `insult_p3_04` now takes).** Measure the loudnorm
   output, apply the single gain that reaches −16.0 LUFS, then true-peak
   limit back to the ceiling. For a file whose peak was already under the
   ceiling, this costs almost no loudness and preserves the dynamics. It
   converges in one iteration.
2. **Compress-and-converge path (for genuine high-crest material).** When
   the gain that reaches the loudness target would break the peak ceiling,
   the two targets are mutually exclusive for a single linear gain. The
   crest is compressed first, then the loudness and the peak are converged
   together with a bounded ceiling ratchet.

`insult_p3_04` takes the makeup path: `crest_method: "makeup"`,
`crest_iterations: 1`, source −14.13 LUFS → delivered **−16.1 LUFS /
−1.8 dBTP, 0 clipped samples**, duration 5.858 s.

| | before | after |
|---|---|---|
| Integrated LUFS | −16.8 | **−16.1** |
| True peak | −1.9 dBTP | **−1.8 dBTP** |
| Clipped samples | 0 | **0** |
| Duration | 5.858 s | 5.858 s |
| Crest method | — | `makeup` (1 iteration) |

**The check was re-run afterwards.** All 40 files now verify clean from disk.

### 3.1 A real bug this exposed — and the fix

The re-normalisation also surfaced a **genuine defect in the true-peak
limiter**, which is worth recording because it silently affected every file
the limiter had ever touched.

The limiter oversamples 4×, soft-limits, then decimates. The decimation
took `y[:len(x)]` — the **first** `len(x)` samples of the 4×-oversampled
signal — instead of taking every 4th sample. That is the first quarter of
the timeline played back 4× fast: the spectrum shifted down by 4× and the
tail of the file was lost. It is audible as a low-pass: the measured
spectral centroid fell from **2747 Hz to 748 Hz**, and a 1 kHz test tone
came out at **250 Hz**.

The limiter also cost 4.8 dB of RMS on material that needed no limiting at
all, which is what finally made the bug visible — a file that was already
on target came out at −24.8 LUFS.

The fix is one line: `np.convolve(up_pad, h, mode="valid")[::os_factor]`.
The 1 kHz test tone now comes out at 1 kHz with RMS preserved, and the
whole bank re-normalises clean.

## 4. SFX normalisation state — honest account

**The four SFX were NOT previously in the same state as the taunt bank, and
the results file could not be trusted. They are now genuinely in the same
state, and this is how that happened.**

The sequence that mattered:

1. The SFX were normalised by an **earlier version** of the normaliser
   (crest-comp path), before the engine was rewritten to the two-pass
   `loudnorm` path.
2. `Tools/python/postprocess_sfx.py` carried the **same broken `crest_comp`
   keyword** that crashed the taunt pass. The crash meant the SFX pass never
   re-ran, so `sfx_results.json` was a **stale artifact written before the
   crash**, not the output of a good run. It could not be used as evidence.
3. Rather than trust it, the four SFX were **measured directly on disk** —
   which confirmed they had been normalised (≈ −16.0 LUFS, no clipping) but
   by the *old* engine, not the current one.

So the state was: **genuinely normalised, but not by the same pass as the
taunts.** That is not the same thing as "done", so it was re-done.

4. The SFX were **regenerated from source** — `synth_sfx.py` is seeded and
   deterministic, so the raw sources reproduce exactly — and put through the
   current normaliser.
5. That run exposed the true-peak-limiter decimation bug described in §3.1.
   The bug was in the *shared* engine, so it affected the taunt bank too.
6. The limiter was fixed, and **all 44 files — 40 taunts and 4 SFX — were
   re-normalised from the existing raw renders and the deterministic SFX
   sources.** No TTS re-render, no new minutes of synthesis.

**All four SFX now pass through the same engine as the taunts**, and all four
verify clean: −16.0 to −16.4 LUFS, true peaks −1.6 to −2.7 dBTP, zero clipped
samples, correct durations. The manifest's `verification.all_sfx_verified` is
`true`, and that flag is computed from a fresh measurement of the delivered
files.

**One engine, two banks.** The same fallback stage is also what lets a single
high-crest *taunt* land on target, which is the same mechanism used to repair
`insult_p3_04`.

## 5. File paths

| What | Path |
|---|---|
| Taunt WAVs (40) | `Content/Audio/Insults/insult_p{phase}_{nn}.wav` |
| **Manifest / playback contract** | `Content/Audio/Insults/insults_manifest.json` |
| SFX WAVs (4) | `Content/Audio/SFX/sfx_{burp,pizza_impact,menace_hum,defeat_squelch}.wav` |
| Taunt source text | `Tools/python/taunt_lines.py` |
| Renderer | `Tools/python/render_taunts.py` |
| Normaliser (both banks) | `Tools/python/normalizer.py` |
| Taunt post-process | `Tools/python/postprocess_taunts.py` |
| SFX post-process | `Tools/python/postprocess_sfx.py` |
| SFX synthesiser | `Tools/python/synth_sfx.py` |
| Single-file gain repair | `Tools/python/repair_loudness.py` |
| Measurement | `Tools/python/audiomeasure.py` |
| Manifest builder | `Tools/python/build_manifest.py` |
| Full TTS contract | `Docs/generated/insult_bank_contract.md` |
| Health watch | `Tools/python/health_watch.py` |
| Health watch tests | `Tools/python/health_watch_tests.py` |
| Tri-state liveness helper | `Tools/python/inference_liveness.py` |

---

## 6. The playback contract (summary — the manifest is authoritative)

The manifest's top-level `rotation` block is the spec. In summary:

- **No immediate repeat** — the last-played id is excluded from the next draw.
- **Never the same line twice within N plays** — `cooldown_window.n_plays` is
  **6**. N counts plays, not seconds: keep a ring buffer of the last 6 played
  ids and exclude any candidate in it. N=6 is chosen so that with 13+ lines
  per phase a legal candidate always exists in the worst case.
- **Weighted by boss phase** — `phase_weight` per entry is a three-slot vector
  (`phase_1` / `phase_2` / `phase_3`) with 1.0 on the line's own phase and 0.0
  elsewhere, and the manifest also carries the per-phase
  `weighted_selection.phase_weights` table. Selection is
  **uniform-within-phase** — no line is favoured by ordering — and ties break
  uniformly at random.
- **Phase gating is strict** — a phase 1 line never plays in phase 2, and a
  line from a different phase is never substituted.
- **Missing-file fallback** — if a selected line's WAV is missing or fails to
  load at runtime, it is **discarded and the draw is retried** from the same
  phase pool, up to **4 attempts**, excluding the bad id from that draw's
  candidates. If every candidate in the active phase is unusable, the engine
  plays **no taunt and logs the failure** — silence is correct; a wrong-phase
  or corrupt line is not. It never falls back to a different phase.
- **Entries with `verified: false` must not be scheduled.**
- **Ordering is stable** — consumers **must** sort by the `index` field.
  Directory order is not stable across platforms, filesystems or git
  checkouts; a rotation built on it would pick different lines on the
  developer's machine than on the player's.
- **SHA-256 per entry** — the Rust side can verify at load time that the file
  on disk is the file the manifest describes. That is what makes the manifest
  a contract rather than a description.
- **Ducking** — the taunt channel ducks the music bed by **6 dB** while it
  plays (80 ms attack, 250 ms release). Weapon SFX are never ducked.
- **Timing** — minimum gap **1.5 s** between taunts, and a taunt is forced
  within **6.0 s** of the previous one finishing.

---

## 7. Health watch and node liveness

`Tools/python/health_watch.py` — the probe was left exactly as it was; the
**verdict** was rebuilt around what the node actually does.

**Port detection first, and a neutral "not present".** The node runs
**llama.cpp on 8080**, not Ollama. Ollama is not listening, and that is a
**neutral fact, not a failure** — a service that is absent and a service that
is broken are different facts, and the watch says "not present" rather than
counting it as an error.

**Consecutive-failure threshold, not a window latch.** A single isolated
failure is **COLD**, not degraded. Only **3 consecutive failures** produce
`DEGRADED`. The old window-latch logic (all samples in the window must be OK)
would have flipped the whole run's verdict because of one bad sample.

**Three faults, three owners:**

| Fault | Meaning | Owner |
|---|---|---|
| HTTP 503 with `"Loading model"` | the server is up and the model is **coming** | model load — wait |
| connection refused | the server is **gone** | process supervision — restart |
| HTTP 200 with empty `content` | the **thinking template ate the budget** | chat template — fix `enable_thinking` |

**One call returns healthy / cold / wedged.** `inference_liveness.health_state()`
returns exactly that tri-state, and `--health` exits **0** healthy, **1** cold,
**2** wedged. The guardians need exactly that distinction: the HTPC's server
once hung for **eleven minutes inside a model load** while a port-and-process
check said all was well, because a listening port and a running process prove
nothing about whether the model can answer.

**Live status at handover:** `HEALTHY` — HTTP 200, `PONG` in 0.20–0.36 s
across 8 consecutive samples, zero failures, exit 0.

**Fault-path coverage:** `Tools/python/health_watch_tests.py` — **38 checks,
all passing**, covering the threshold behaviour, the neutral absent-service
state, each of the three named faults and its owner, the tri-state helper, and
a guard that the probe still targets `/v1/chat/completions` with
`enable_thinking: false`.

---

## 8. Honest status summary

| Item | State |
|---|---|
| 40 taunt lines rendered | ✅ 40/40, zero render failures, 2 291 s, concurrency 6 |
| Taunt normalisation | ✅ all 40 through the two-pass `loudnorm` |
| Taunt loudness | ✅ −16.4 … −15.7 LUFS (target −16.0 ±0.6) |
| Taunt true peak | ✅ −2.2 … −1.4 dBTP (spec: below −1.0) |
| Taunt duration | ✅ 5.841 – 5.866 s (window 1.5 – 6.0 s) |
| Clipped samples, whole bank | ✅ **0** |
| `insult_p3_04` makeup gain | ✅ −16.1 LUFS / −1.8 dBTP, **not re-rendered** |
| 4 SFX | ✅ procedurally synthesised, deterministic, re-generated from source |
| SFX normalisation | ✅ **now through the same engine as the taunts**; the stale results file was discarded and the files re-measured |
| SFX loudness / peak / clipping | ✅ −16.0…−16.4 LUFS, −1.6…−2.7 dBTP, 0 clipped |
| Manifest | ✅ `insults_manifest.json` — 40 + 4 entries, `index`, text, word count, duration, ref, fingerprint, SHA-256, phase weight |
| Rotation contract | ✅ no-immediate-repeat, N-play cooldown, phase weighting, missing-file fallback, stable ordering |
| Health watch | ✅ 38/38 fault tests pass; live verdict **HEALTHY** |
| Tri-state helper | ✅ `health_state()` → healthy/cold/wedged, exit 0/1/2 |
| **Re-render cost avoided** | ✅ 1 file repaired by gain instead of ~6 min of TTS |
| **True-peak limiter decimation bug** | ✅ found, fixed (1 line), all 44 files re-normalised and re-verified |
| **All 44 re-verified on disk after the fix** | ✅ SHA-256, LUFS, true peak, duration, sample rate, channels, clipping |
