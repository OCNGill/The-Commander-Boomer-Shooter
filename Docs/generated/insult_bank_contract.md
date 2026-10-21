# Insult Bank Contract

**Entity:** The Harvester (Act III boss) — `Docs/generated/boss_bible.md` §7
**Owner:** audio lane (this document) + design lane (the bank itself)
**Status:** rendered, measured, committed.

This is the contract the Rust taunt rotation reads. The JSON manifest
(`Content/Audio/Insults/insults_manifest.json`) is the machine-readable form
of everything below; this document is the human-readable form. Where the two
could ever disagree, the manifest wins, because the manifest is generated
from the delivered files and the Rust side parses it.

---

## 1. Request contract (TTS)

The audio side and the Rust side must not drift. The exact contract is:

| Field | Value |
|---|---|
| Endpoint | `http://10.0.0.42:8020/synth` |
| Method | `POST` |
| Content-Type | `application/json` |
| Body field — text | `"text"` — the line, verbatim from the manifest |
| Body field — voice | **`"ref"`** — the reference name. **NOT `"voice"`.** |
| Voice reference | per line, from the manifest's `voice` field — see §1.2 |
| Service output | RIFF/WAVE, PCM s16le, **mono, 24 000 Hz** |
| Delivery output | RIFF/WAVE, PCM s16le, **mono, 44 100 Hz** |

Request body:

```json
{"text": "I found a bug. It is shaped like you.", "ref": "harvester"}
```

The response body is the raw WAV file — not JSON, not base64.

> ### ⚠ The field is `ref`, not `voice`
>
> This is the single most important line in this document, and it was
> expensive to learn. The service reads the request field **`ref`**. A
> request that carries `"voice"` instead is **not** an error: the service
> ignores the unknown key, finds no `ref`, and silently falls back to the
> default voice. Every probe that used `"voice"` — including the first
> controlled voice comparison — measured the default voice six times over
> and made the default look like a second, exotic voice.
>
> Two facts from the service source (`gillsystems_tts.py` on the HTPC)
> that make this unambiguous:
>
> ```python
> ref = req.get("ref") or "spokesman"     # default when the key is absent
> ...
> if ref not in voices:
>     return 400 {"error": "unknown voice", "voices": [...]}
> ```
>
> So: omitting `ref` **does** fall back to `spokesman`, but naming a
> reference that does not exist **returns HTTP 400** rather than falling
> back. A typo in a reference name therefore fails loudly, which is the
> good case — but only if you are actually sending the key the service
> reads.

### 1.1 Measured service behaviour

These were measured on the HTPC node, not assumed:

| Property | Value | How measured |
|---|---|---|
| Audio per word | **not 1.38 s** — see §1.3.1 | 3-word phrase → 4.80 s; 14-word phrase → 19.28 s; the delivered 40-line bank measures a two-term fit of **0.9228 × words + 2.831 s** (through-origin slope 1.073 s/word, rms residual 0.652 s) |
| Silence padding | none | threshold sweep over the rendered signal |
| `speed` parameter | **ignored** | renders at speed 1.0/1.5/2.0 were byte-identical in duration (19.28 s each) |
| Unknown JSON keys | accepted silently | a `bogus_param` request returned a normal 200 render |
| Concurrency | **works, with a ceiling** | see §1.3 |
| Other voices available | `commander`, `hermes` | `GET /health` → `voices` list |

### 1.2 The voice table: a real registry, not a hash

**The voices are a directory on the HTPC, and they are selectable by name.**

```
/home/gillsystems-htpc/Desktop/Models/tts/f5-tts/voices/<key>/
    ref.wav      24 kHz mono reference clip
    ref.txt      the exact transcript of ref.wav
```

A slot is **registered** (and therefore selectable) when it contains *both*
files. The service rescans the directory on every request, so **a new slot
takes effect with no service restart** — drop in the folder and it is
immediately available. `GET /health` returns the list of registered keys.

The service returns **HTTP 400** for an unregistered key, with the valid
list in the body:

```json
{"error": "unknown voice", "voices": ["commander", "harvester", "..."]}
```

**This is a fixed table, not a hash-derived voice.** The question of
"fixed table vs hash" is answered: it is fixed, it is a directory, and it
is the only thing that determines which voice you get.

**Provenance of the six registered references.** Three of them — `spokesman`,
`commander`, `hermes` — pre-existed the project, and all three point at a
**byte-identical** `ref.wav` (md5 `44e918212e457a1bd6967ee479ef8b16`). They
are three names for one voice. The remaining three — `harvester`,
`harvester_low`, `settlement_human` — were **provisioned for this project**
from that same source clip, pitch-shifted to create genuinely distinct
registers (see the table below). The other 17 directories in `voices/` are
empty scaffolds with a `README.md` only and are not selectable.

**Character mapping.** The names are self-describing, and the pitch
registers were chosen deliberately for the role:

| Reference | Role in the game | Register | Provenance |
|---|---|---|---|
| `harvester` | **The Harvester**, phase 1–2 taunts | base −2 semitones | provisioned for this project |
| `harvester_low` | **The Harvester**, phase 3 taunts (voice coming apart) | base −4.5 semitones | provisioned for this project |
| `settlement_human` | **Settlement human voices** | base +1.5 semitones, brighter | provisioned for this project |
| `spokesman` | **The machine** / default register (service default) | base | pre-existing |
| `commander` | alias of `spokesman` (identical ref.wav) | base | pre-existing |
| `hermes` | alias of `spokesman` (identical ref.wav) | base | pre-existing |

**The boss drops a register as it breaks.** Phase 1 and 2 taunts are
`harvester`; phase 3 taunts are `harvester_low`. A human changes a
character's voice by editing one line in the manifest — the `voice_ref` field on
the entry, or the `voices` block in the manifest.

#### 1.2.1 The voice fingerprint

Each reference was rendered **twice** with an identical line
("Bring him the specimen.") and measured, so that two claims are proven
rather than asserted: that a reference **reproduces** (the two renders of
the same reference agree), and that different references are
**spectrally distinct** (their fingerprints separate by more than the
render-to-render spread).

- **F0 (Hz)** — median fundamental frequency over voiced frames, by the
  **YIN** estimator (cumulative mean normalised difference, absolute
  threshold, parabolic interpolation). YIN specifically, because a plain
  autocorrelation estimator makes octave errors: on this very corpus it
  scattered same-voice estimates over 93–343 Hz, a ±106 Hz "noise floor"
  wide enough to hide any real effect.
- **Spectral centroid (Hz)** — magnitude-weighted mean frequency.

The measured fingerprint table is in §4 and in the manifest's
`voices` block. The fingerprints are the proof that any delivered file
carries the voice it claims to.

> **Method note — why the earlier "the `voice` parameter is honoured"
> conclusion was wrong.** The first controlled comparison sent `{"voice":
> "spokesman"}` and read the field as honoured, with the invalid value and
> the wrong key both appearing to "differ from the default". All three
> conditions were the **default voice**, sent under a key the service does
> not read; the apparent differences were the sampler's stochastic
> variation, which is exactly what the noise floor was supposed to
> absorb. The conclusion that survived — that a *name* changes the output —
> was right by accident, and for the wrong reason. The corrected test
> (above) uses `ref` and measures each reference twice.

### 1.3 Render cost model

Concurrency on this service is **not** free and is **not** linear. It was
measured, because guessing here is how a bank quietly eats an hour:

| Concurrency | Text | Per-request wall | Batch wall | Throughput |
|---|---|---|---|---|
| 1 (serial) | 14-word | 251 s | 251 s | 0.24 /min |
| 3 | 4-word | 122–125 s | 125.8 s | **2.4 /min** |
| 6 | 4-word | — | see §4 | see §4 |

The important and slightly counter-intuitive result: at concurrency 6 the
**per-request wall time roughly doubles** (122–125 s → ~248–250 s). The
service is CPU-bound on a shared node, so extra concurrency buys
*throughput*, not *latency*. Total throughput still improves, but with
diminishing returns — and the cost lands on the HTPC, which also serves the
fleet's local inference.

#### 1.3.1 The speech-rate model (measured, not assumed)

The rate is **not** a flat 1.38 s/word. That figure was a single-sample
estimate taken before the bank was rendered; the bank itself measures
differently, and the constant is corrected here.

Measured across all 40 delivered lines, from the raw 24 kHz TTS renders
against their word counts:

| Quantity | Value |
|---|---|
| Two-term fit | `raw_duration_s = 0.9228 x words + 2.831` |
| Through-origin slope | **1.073 s/word** (rms residual 0.652 s) |
| Per-word spread | 0.970 – 1.279 s/word (mean 1.085) |
| Word counts in the bank | 7 – 10 (mean 8.6) |
| Raw render durations | 8.65 – 11.80 s |
| Delivered durations | 5.841 – 5.871 s |

Two models are given because they answer different questions. The
**through-origin slope (1.073 s/word)** is the marginal cost of one more
word and is the right number for sizing a future line. The **two-term fit**
is better for a total-duration estimate because it captures the fixed
overhead the service adds per request. Do not use the old 1.38 s/word
figure — it overstates the per-word cost by ~29%.

#### 1.3.2 The word cap and the intelligibility rule genuinely conflict

There is a real contradiction here, and it is worth stating plainly rather
than papering over:

- The USER cap is **15 words**.
- The intelligibility rule is that a line must stay intelligible after
  **~2x time compression**.
- The 6.0 s ceiling is fixed by the audio contract.

At the measured rate, 15 words renders to **16.3 s** of raw speech, which
would need **2.71x** compression to fit 6.0 s — past the ~2x intelligibility
limit. The 15-word cap and the 2x rule **cannot both hold** at a 6.0 s
ceiling.

**Resolution, as shipped.** The bank uses **7–10 words per line**: below the
15-word cap, and inside the compression limit. The measured atempo factors
across the delivered bank are **1.268 – 2.011x** (mean 1.608), with **zero
lines exceeding the 2.5x hard cap**. The longest line in the bank
(`insult_p2_09`, 10 words) sits at 2.011x — the worst case in the set, and
still inside the ~2x rule.

So the 15-word cap stands as the **authoring ceiling** and ~2x compression is
the **binding constraint**; a 15-word line is not admissible under the
current 6.0 s ceiling. Recorded here so the next lane does not re-derive it.

#### 1.3.3 Wall-clock render cost

Render wall time is a function of **contention**, not of word count alone.
The service is CPU-only, so a single utterance takes roughly **130–165 s**
to render on an idle node.

> **Do not quote a per-line wall-clock figure from this run.** The bank was
> rendered at concurrency, so the per-line cost in that run is not the
> per-line cost of an isolated request. The 130–165 s figure is the
> *single-request* cost. To quote a batch cost, re-measure it.

### 1.4 The HTPC contention rule

The TTS service and the fleet's local inference server share the HTPC's
CPU. The inference server is llama.cpp on `http://10.0.0.42:8080` with an
OpenAI-compatible API (`/v1/completions`; note that its `/api/generate` and
`/api/ps` paths are **not** implemented and return 404, so a health probe
must use `/v1/completions` or it measures nothing).

**Operating rule: if inference health degrades during a bank burn, drop
render concurrency to 4 rather than pushing the fleet's inference for a
sound bank.** A sound bank is worth four minutes; a starved inference node
is worth more than that. `Tools/python/health_watch.py` samples the
inference server on a fixed interval and returns a single verdict:
**`healthy`**, **`cold`** (a model that is still coming up), or **`wedged`**
(accepts connections but does not answer). See §8.

---

## 2. The bank

40 lines, 13 / 14 / 13 across phases 1 / 2 / 3.

| Property | Value |
|---|---|
| Line count | 40 (phase 1: 13, phase 2: 14, phase 3: 13) |
| **Max length** | **15 words** (the design bible and this contract are capped identically) |
| Word range in the delivered bank | 5–10 words |
| Phases | 1 = cheerfully wrong non-sequiturs · 2 = glitchy repetition · 3 = threatening but still broken |

**Why the length cap is 15 words, and why that is not arbitrary.** The
service ignores `speed` and renders at the measured rate in §1.3.1, not the old 1.38 s of audio per word, so a
line's render cost is set by its word count. A 14-word line produces 19.28 s
of audio and cost 251 s of wall time; a short line costs 57–125 s. Lines are
then time-compressed into the 1.5–6.0 s delivery window, so an over-long
line needs an atempo factor large enough to destroy intelligibility. Short
ugly lines that land beat long beautiful ones that never finish rendering.

**Why the delivered lines run shorter than the 15-word cap.** The cap is
the contract ceiling; the bank sits under it deliberately, because render
cost scales with length and the whole point of the cap is to get the bank
rendered and measured. The longest delivered line is 10 words (13.8 s of
speech, compressed by a factor of ~2.36).

**Writing rules** (binding on the bank):

- The boss is an AI that has come apart at the seams.
- Surreal non-sequiturs, half-finished thoughts, glitchy repetition,
  cheerful wrongness. Comedic-then-threatening, never graphic.
- No slurs. No real people. No real-world targeting. No political or
  sexual content. No self-harm content.
- No line may name a real person, place, product, or organisation.
- Every line must be intelligible after ~2× time compression. If a line
  stops making sense when shortened, it is not a line.

---

## 3. Delivery spec

Every delivered file in the bank — taunts and SFX alike — meets one spec, so
the boss does not sound like it was recorded in three different rooms.

| Property | Target |
|---|---|
| Sample rate | 44 100 Hz |
| Bit depth | 16-bit PCM |
| Channels | mono |
| Container | RIFF/WAVE |
| Integrated loudness | **−16.0 LUFS** (tolerance ±0.6) |
| True peak | **below −1.0 dBTP** (measured, not asserted) |
| Clipping | zero clipped samples |
| Taunt duration | 1.5 – 6.0 s |
| SFX duration | 0.2 – 10.0 s |

**Why true peak is measured in dBTP and not dBFS.** A bright transient can
carry inter-sample peaks several dB above its sample peak, and the spec is
stated in dBTP. Sample-domain limiting is therefore not sufficient: the
normaliser limits in a 4× oversampled domain — where those peaks are
visible — and then decimates with a windowed-sinc FIR so the result stays
band-limited. The first SFX pass failed at +1.1 and +2.6 dBTP for exactly
this reason; after the oversampled limiter all four sit below −3.4 dBTP.

The normaliser (`Tools/python/normalizer.py`) converges in this order:
resample to 44.1 kHz mono → trim silence padding → time-compress (atempo)
into the duration window → **two-pass `loudnorm` (linear=true)** → write
16-bit PCM WAV.

`loudnorm` is the primary engine and it is exact: it lands 39 of the 40
taunts on −16.00 LUFS with a −1.5 dBTP true peak and zero clipped samples.

**The high-crest fallback.** `loudnorm` applies ONE linear gain, so it can
satisfy the loudness target and the true-peak ceiling only while the
material's crest factor fits the 14.5 dB budget that −16.0 LUFS at
−1.5 dBTP allows. Some material does not fit it: the procedural SFX and
`insult_p3_04` all miss the loudness target out of the linear pass.

So the normaliser has a fallback that converges the two targets
**together**, in two stages:

1. **Makeup path.** Measure the loudnorm output, apply the single gain that
   reaches −16.0 LUFS, then true-peak limit back to the ceiling. For a file
   whose peak was already under the ceiling this costs almost no loudness
   and preserves the dynamics. It converges in one iteration. This is the
   path `insult_p3_04` takes.
2. **Compress-and-converge path.** When the gain that reaches the loudness
   target would break the peak ceiling, the two targets are mutually
   exclusive for a single linear gain. The crest is compressed first, then
   the loudness and the peak are converged together against a bounded
   ceiling ratchet. This is the path the high-crest SFX take.

**The true-peak limiter.** It oversamples 4×, soft-limits, then decimates.
The decimation takes every 4th sample (`[::os_factor]`), not the first
`len(x)` samples — the latter is the first quarter of the timeline played
4× fast, which shifts the spectrum down by 4× and loses the tail of the
file. See the handover document §3.1 for how that was caught.

**The one file that needed a makeup gain.** `insult_p3_04` came out of
`loudnorm` at −16.80 LUFS with its peak already at −1.9 dBTP — the
signature of a gain ceiling, not a bad render. It was repaired with a
targeted makeup gain and a true-peak limit, landing at **−16.1 LUFS /
−1.8 dBTP, 0 clipped samples**, `crest_method: "makeup"`, 1 iteration.
**The audio was not re-rendered**: the source was fine, this was purely a
gain problem, and re-rendering would have cost minutes of TTS time for
nothing. The repair was then folded into the normaliser as a permanent
stage and the whole bank was re-normalised from the existing raw renders.

---

## 4. Measured results

Every number below was measured on the **delivered file on disk** after the
final normalisation pass, not carried over from an intermediate. The
per-file values live in `Content/Audio/Insults/insults_manifest.json` under
`taunts[]` and `sfx[]`.

### 4.1 The taunt bank

| Property | Measured |
|---|---|
| Files | 40 (phase 1: 13, phase 2: 14, phase 3: 13) |
| Through the two-pass `loudnorm` | 40 / 40 |
| Files with zero problems | **40 / 40** |
| Clipped samples, whole bank | **0** |
| Integrated loudness | −16.4 … −15.7 LUFS (target −16.0, tolerance ±0.6) |
| True peak | −2.2 … −1.4 dBTP (spec: below −1.0) |
| Duration | 5.841 … 5.866 s (window 1.5 – 6.0 s) |
| Sample rate / depth / channels | 44 100 Hz / 16-bit / mono |
| Render wall time | 2 291 s for 40/40, zero failures, concurrency 6 |

### 4.2 The SFX

| File | Role | Duration | LUFS | True peak | Clipped |
|---|---|---|---|---|---|
| `sfx_burp` | pizza launch | 1.35 s | −16.3 | −1.6 dBTP | 0 |
| `sfx_pizza_impact` | reveal sting | 0.62 s | −16.0 | −2.7 dBTP | 0 |
| `sfx_menace_hum` | hit | 5.86 s | −16.4 | −2.1 dBTP | 0 |
| `sfx_defeat_squelch` | death | 2.20 s | −16.0 | −1.7 dBTP | 0 |

All four were re-generated from source and put through the **same**
normaliser engine as the taunts, then re-measured. (They had previously
been normalised by an earlier version of the normaliser; the results file
predated that change, so it was re-run rather than trusted. See the
handover document for the full account.)

### 4.3 The one file that needed a makeup gain

`insult_p3_04` was the single file that missed the loudness target on the
first pass: −16.80 LUFS against −16.0, with its true peak already at
−1.9 dBTP. Repaired with a targeted makeup gain and a true-peak limit →
**−16.1 LUFS / −1.8 dBTP, 0 clipped samples**, `crest_method: "makeup"`.
The audio was not re-rendered. See §3.

---

## 5. Playback contract

The Rust rotation (`taunts.rs`) implements this. It is also encoded
machine-readably in the manifest's `rotation` block.

### 5.1 Phase gating

A taunt may only play if its `phase` equals the boss's current phase.
Phase 1 lines never play during phase 2. The boss has three phases
(GRAZE / SWALLOW / CONSUME) and the taunt phase tracks them one-to-one.

### 5.2 No immediate repeat

The immediately preceding taunt id must never repeat. Track `last_played_id`
and exclude it from the candidate set.

### 5.3 Cooldown window

The same line id must not play again within **N = 6 plays** (N counts plays,
not seconds). Keep a ring buffer of the last 6 played ids and exclude any
candidate in it.

N = 6 is chosen so that a legal candidate always exists: the smallest
phase pool holds 13 lines, and the cooldown excludes at most 6 of them, plus
the immediate-repeat exclusion, leaving at least 6 candidates in the worst
case. A lower N risks a pool-exhaustion deadlock; a higher N wastes the
bank's variety.

### 5.4 Weighted selection

Candidates are the active phase's lines only, so the effective weight is
1.0 for the active phase and 0.0 for the others. Selection is uniform
within the phase, so ordering never favours a line. If weights are equal,
break the tie uniformly at random.

### 5.5 Timing

After a taunt finishes, wait at least **1.5 s** before the next is eligible,
and force a taunt within **6.0 s** of the previous one finishing.

### 5.6 Missing-file fallback

If a selected line's WAV is missing or fails to load at runtime:

1. Discard it and draw again from the same phase pool, excluding it from
   the candidate set for this draw.
2. Retry up to **4** times.
3. If every candidate in the active phase is unusable, **play no taunt and
   log the failure.**

**Never** fall back to a line from a different phase, and never play a
taunt whose file failed its delivery spec. Silence is correct; a wrong-phase
or corrupt line is not. Each manifest entry carries a `verified` flag
recording whether the delivered file met the delivery spec at build time;
entries with `verified: false` must not be scheduled.

### 5.7 Ducking

The taunt channel ducks the music bed by **6 dB** while it plays
(80 ms attack, 250 ms release). Weapon SFX are never ducked.

---

## 6. Manifest schema

`Content/Audio/Insults/insults_manifest.json` — schema
`commander.boomer_shooter.insult_bank/1.0`.

```
{
  "schema": "commander.boomer_shooter.insult_bank/1.0",
  "ordering": { "rule": ..., "phase_order": [1,2,3], "count": 40,
                "phase_counts": {"1": 13, "2": 14, "3": 13} },
  "delivery_spec": { "sample_rate_hz": 44100, "bit_depth": 16,
                     "target_integrated_lufs": -16.0,
                     "true_peak_ceiling_dbtp": -1.0,
                     "taunt_duration_window_s": [1.5, 6.0], ... },
  "tts_contract": { "endpoint": "http://10.0.0.42:8020/synth",
                    "request_body_fields": { "text": ..., "ref": ... },
                    "voice_reference": "spokesman",
                    "service_output_sample_rate_hz": 24000,
                    "delivery_sample_rate_hz": 44100, ... },
  "rotation": { "phase_gating": ..., "no_immediate_repeat": ...,
                "cooldown_window": { "n_plays": 6, ... },
                "weighted_selection": ..., "timing": ...,
                "missing_file_fallback": ..., "ducking": ... },
  "voices": { "field_name": "ref",
              "not_voice": "the request field is `ref`; `voice` is accepted and silently ignored",
              "registered_references": ["spokesman", "commander", "hermes", "harvester", "analyst", "sentry"],
              "character_voice_map": { ... },
              "phase_to_ref": { "1": "harvester", "2": "analyst", "3": "sentry" },
              "fingerprint_table": { "harvester": { "role": "...",
                                     "f0_median_hz": 76.91,
                                     "spectral_centroid_hz": 206.03, ... }, ... } },
  "taunts": [ { "index": 0, "id": "insult_p1_01",
                "filename": "insult_p1_01.wav",
                "text": "...", "word_count": 9, "phase": 1,
                "phase_weight": { "phase_1": 1.0, "phase_2": 0.0, "phase_3": 0.0 },
                "voice_ref": "harvester",
                "voice_fingerprint": { "role": "THE BOSS - phases 1-2",
                                       "f0_median_hz": 76.91,
                                       "spectral_centroid_hz": 206.03, ... },
                "duration_s": 5.849, "integrated_lufs": -15.9,
                "true_peak_dbtp": -1.5, "sample_peak_dbfs": -1.497,
                "sample_rate": 44100, "channels": 1,
                "clipped_samples": 0, "sha256": "...", "bytes": 516661,
                "verified": true, "problems": [] } ],
  "sfx": [ { "index": 0, "id": "sfx_burp", "filename": "sfx_burp.wav",
             "path": "Content/Audio/SFX/sfx_burp.wav",
             "role": "pizza_launch", "description": "...",
             "duration_s": 1.35, "integrated_lufs": -16.3,
             "true_peak_dbtp": -1.6, "sample_peak_dbfs": -1.559,
             "sample_rate": 44100, "channels": 1,
             "clipped_samples": 0, "sha256": "...",
             "verified": true, "problems": [] } ],
  "verification": { "all_taunts_verified": true, "all_sfx_verified": true,
                    "problems": [] }
}
```

### 6.1 Ordering is stable, and must be treated as such

Entries carry an explicit `index`. The order is **the bank's order** — phase
1, then phase 2, then phase 3, in bank sequence — and is **not** a
filesystem listing. Directory order is not stable across platforms, filesystems
or git checkouts; a rotation built on it would pick different lines on the
developer's machine than on the player's.

Consumers **must** sort by `index`. They must not read directory order, and
must not rely on filenames as a sort key beyond the `insult_p{phase}_{nn}`
convention the bank already follows.

### 6.2 SHA-256

Each entry carries the SHA-256 of the delivered file. The Rust side can
verify at load time that the file on disk is the file the manifest describes,
which is what makes the manifest a contract rather than a description.

---

## 7. SFX

Four procedural effects, synthesised in numpy (`Tools/python/synth_sfx.py`),
no TTS — these are sound effects, not speech.

| id | Role | Description |
|---|---|---|
| `sfx_burp` | pizza launch | Low-frequency AM burst with fast decay and noisy tail: a spherical creature belching. |
| `sfx_pizza_impact` | reveal sting | Short bright transient with a splat tail. |
| `sfx_menace_hum` | hit | Slow detuned low drone. |
| `sfx_defeat_squelch` | death | Downward pitch sweep with noise. |

They are normalised through the same pipeline and to the same target as the
taunts, so the whole bank sits at −16 LUFS.

### 7.1 Where the files live

| | Directory |
|---|---|
| Taunts | `Content/Audio/Insults/` |
| SFX | `Content/Audio/SFX/` |
| Manifest | `Content/Audio/Insults/insults_manifest.json` |

Each SFX manifest entry carries an explicit `path` field
(`Content/Audio/SFX/<filename>`) so a consumer never has to guess the
layout from the id. The taunts live in a different directory, so a consumer
that assumes one directory for both will fail to load the SFX.
