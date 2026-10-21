# Voice contract — handover findings (design lane, 2026-10-21)

**Status: handover. This lane is done; the audio lane owns the voice contract
from here. The roster bible amendment, cutscene beats, pizza attack, human
collaborators, cyborgs and skin jobs moved to a separate lane.**

Nothing in `Docs/generated/roster_bible.json` or `roster_bible.md` was
written by this lane. Both files were read-only for this work. (A separate
lane edited `roster_bible.json` at 09:18 — voice-ref wording only, verified
by `git diff`; that change is theirs, not this lane's.)

Source of truth for the service behaviour below: the service source
(`gillsystems_tts.py` on the HTPC, mirrored at
`%LOCALAPPDATA%/hermes/cache/scratch/full_svc.py`), the service's own log
(`tts.log` — 178 `synth` / 159 `done` events, timestamped), the live
`/health` endpoint, the 12 already-rendered WAVs in `.audio_work/voices/`,
the four reference clips in `.audio_work/refs/`, and the shipped
`Content/Audio/Insults/insults_manifest.json` with its 40 delivered WAVs.
**No new renders were consumed for this handover.**

> **Correction to an earlier draft of this document.** A first pass fitted
> every duration against `(bytes−44)/24000`, which assumes 8-bit samples.
> The service emits **16-bit** PCM at 24 kHz, so the correct divisor is
> **48 000 bytes/sec**. Every duration, s/word figure and cost-model
> coefficient below is at the corrected scale. Two conclusions from the
> earlier draft were wrong and are retracted here: the boss register table
> (§3.3) and the "pitch does not transfer" claim (§3.2). The estimator used
> for F0 also changed — the earlier draft used a plain autocorrelation
> estimator, which octave-errors; this one uses the repo's own
> `Tools/python/voiceprint.py`, which is octave-correct and reproduces the
> shipped fingerprint table exactly.

---

## 1. The request contract, as the service actually answers it

| Property | Measured value |
|---|---|
| Endpoint | `POST http://10.0.0.42:8020/synth` |
| Health probe | `GET http://10.0.0.42:8020/health` → `{"ok":true,"loaded":true,"voices":[...]}` |
| Content-Type | `application/json` |
| Body field — text | `"text"` (required; empty → HTTP 400 `{"error":"no text"}`) |
| Body field — reference | **`"ref"`** — **not** `"voice"` |
| Reference default | `"spokesman"` when `ref` is absent (`ref = req.get("ref") or "spokesman"`) |
| Unknown reference | **HTTP 400** `{"error":"unknown voice","voices":[...]}` — fails loudly, does not fall back |
| Response body | raw WAV bytes (`audio/wav`), not JSON, not base64 |
| Service output format | RIFF/WAVE, PCM **s16le**, **mono, 24 000 Hz** — uniform across all 12 controlled renders and all 4 reference clips (verified from WAV headers) |
| Delivery format (post-process) | RIFF/WAVE, PCM s16le, mono, **44 100 Hz** |
| Engine | F5-TTS v1 Base, **CPU-only** (`CUDA_VISIBLE_DEVICES=-1`, `HIP_VISIBLE_DEVICES=-1`, `OMP_NUM_THREADS=4`) |
| Diffusion steps | `GILLSYSTEMS_TTS_NFE=16` in the systemd unit (source default 32) — **a live speed lever** |
| Server | `ThreadingHTTPServer`, no semaphore, no queue cap; **peak 11 requests in flight** observed |

Request body:

```json
{"text": "I found a bug. It is shaped like you.", "ref": "harvester"}
```

**The single most important line in this document: the field is `ref`.** A
request that carries `"voice"` is *not* an error — the service ignores the
unknown key, finds no `ref`, and silently falls back to `spokesman`. Every
probe that used `"voice"` measured the default voice and made the default
look like a second, exotic voice. Note the asymmetry: **omitting** `ref`
falls back to `spokesman`, but **naming a ref that does not exist** returns
HTTP 400. A typo fails loudly *only* if you are actually sending the key the
service reads.

### Valid `ref` values — the registry census

`scan_voices()` registers a name only when `voices/<name>/` contains **both**
`ref.wav` and `ref.txt`. The service directory `f5-tts/voices/` holds **23
directories; exactly 6 are selectable.** The live `/health` endpoint returns
those same 6:

`spokesman`, `commander`, `hermes`, `harvester`, `harvester_low`, `settlement_human`

The other **17 directories are empty scaffolds** (`adam`, `architect`,
`courier`, `ebert`, `edi`, `gaben`, `geordi`, `herald`, `lamp`, `liara`,
`medic`, `orchestrator`, `scout`, `scribe`, `sentinel`, `spark`, `theo`) — a
`README.md` only, no `ref.wav`, so they are not in the registry and any
request naming them returns HTTP 400.

### How many *voices* actually exist

Six names are selectable, but only **four distinct reference audios**:

| Reference | md5 (first 12) | Bytes | Distinct audio? |
|---|---|---|---|
| `spokesman` | `44e918212e45` | 252 044 | — |
| `commander` | `44e918212e45` | 252 044 | **byte-identical to `spokesman`** |
| `hermes` | `44e918212e45` | 252 044 | **byte-identical to `spokesman`** |
| `harvester` | `133d9a343f10` | 252 078 | yes |
| `harvester_low` | `50484b3bbf83` | 252 078 | yes |
| `settlement_human` | `a83698883894` | 252 078 | yes |

All six `ref.txt` transcripts are the same line: `"Bring him the specimen."`

So the answer to "does the service expose more than one voice" is: **yes, but
four, not six.** Three of the six names are one audio file. The field does
**not** accept an arbitrary string — it is validated against the registry, so
the manifest must name one of the real six rather than inventing roleplay
names. A name that does not exist is a loud 400, not a silent wrong voice.

### Measured render cost per line, and the concurrency effect

Wall time is **not** a function of line length. From 84 reliably-paired
requests (tqdm completion line immediately followed by `INFO done N bytes`),
split by service restart:

| Regime | n | Fit | R² |
|---|---|---|---|
| All requests | 84 | `wall_s = 8.16 × audio_s + 136.9` | **0.085** |
| Quiet window | 22 | `wall_s = 7.23 × audio_s + 35.0` | 0.872 |
| Busy window | 218 | `wall_s = 30.45 × audio_s + 26.5` | 0.448 |

**Text length explains about 8% of wall-time variance.** Three facts pin
this down, and none of them is a length effect:

- **Identical output, 5× wall spread.** 78 renders of *the same line*
  produced byte-identical 6.549 s output (314 412 bytes) with per-request
  wall times from **70 s to 365 s** — a 5.2× spread on identical work.
- **The 251 s "long line" is not a long line.** No request in the log took
  248–254 s. The 240–260 s band contains only **3- and 6-word** lines
  (`Alpha one two.`, `Bravo six seven eight nine ten.`). The actual
  13-word line (`Would you like to file a complaint about the weather…`)
  rendered in **92 s** on one pass and **325 s** on another — the same
  text, 3.5× apart, both at 19.3 s of audio.
- **Throughput, not latency, is what concurrency buys.** 40 renders of one
  identical line took **49.6 minutes** of wall clock end-to-end
  (0.81 renders/min) at a peak of 11 requests in flight, against
  `OMP_NUM_THREADS=4` and no server-side cap.

**Per-request wall time is contention-bound, not length-bound.** Render the
bank at concurrency 3–4 and the per-line cost drops several-fold. The
`GILLSYSTEMS_TTS_NFE` knob (currently 16, default 32) is a second lever.

The roster bible's `render_cost_measured` note — *"the service ignores a
speed parameter, so line length is the only cost lever"* — is **wrong on
both halves**: the service does honour a diffusion-step parameter, and at
concurrency > 4 line length is not the dominant term.

---

## 2. Duration comes from the text, not the voice

This is the cleanest result in the handover. All 12 renders are the same
line (`"Bring him the specimen."`, from `Tools/python/voice_fingerprint.py`),
2 reps × 6 names:

| Property | Value across all 12 |
|---|---|
| Byte count | **240 684 — identical for all 12** |
| Frames / duration | 120 320 / **5.0133 s — identical for all 12** |
| Sample rate / channels / depth | 24 000 Hz / mono / 16-bit — identical for all 12 |
| SHA-256 | **12 distinct values** |

**Identical requests return identical byte counts with different hashes.**
Byte count is a pure function of the input text; the hash varies because the
sampler is stochastic. That is why byte- and hash-comparison could never
separate voices — and it is also why the `sha256` recorded per taunt in the
manifest is a *delivery integrity* check (per §6.2) and must never be read as
a voice fingerprint.

Duration and byte count are therefore useless as voice evidence. The metric
that carries signal is **timbre** (spectral centroid); pitch carries signal
in the *reference clips* but not in the output (§3.2).

### The duration is model-predicted, not arithmetic

A stronger statement than "duration comes from the text": the duration is
**not derivable from the text's length either**. Across 36 distinct
character counts in the log, **13 map to more than one byte count**:

```
chars=20 -> [69164, 209452]      chars=23 -> [240684, 314412]
chars=30 -> [146476, 314412]     chars=37 -> [429612, 471596]
chars=38 -> [174124, 398380, 503340]
```

Same text, same `ref`, different lengths — F5-TTS *predicts* how long to
speak from the text's content, so a 20-character line can come out at
1.4 s or 4.4 s. Any cost model that treats duration as a function of
character count is wrong.

---

## 3. Voice separation: timbre transfers, pitch does not

Agreed with the Commander's read on the n=2 sample: at two renders per name
the sampler's own variance is comparable to the between-name spread, so the
*per-name* separation is not settled. But the question can be settled
differently, and this lane settled it on the data already in the repo.

All numbers below use the repo's own estimator, `Tools/python/voiceprint.py`
(YIN F0, threshold 0.45, sub-harmonic suppressed; power-weighted spectral
centroid). **Re-running it reproduces the shipped
`.audio_work/voices/voice_fingerprints.json` exactly** (all 6 names, both
metrics, to 2 dp) — so these numbers are directly comparable to the
manifest's `voice_fingerprint` blocks.

### 3.1 The control group

`spokesman` / `commander` / `hermes` are one byte-identical reference, so
their three names are a natural noise floor.

| Measurement | Value |
|---|---|
| Alias-group centroid means (n=2 pool) | 274.11 / 275.26 / 287.16 Hz → spread **13.05 Hz** |
| Alias-group centroid means (n=6, one session) | 312.07 / 222.43 / 272.95 Hz → spread **89.65 Hz** |
| Worst rep-to-rep centroid delta (any name) | **81.24 Hz** |
| ⇒ pooled within-name SD (df=6) | 34.52 Hz → **SE of a 2-rep mean = 24.41 Hz** |
| ⇒ pooled within-name SD (df=30, n=6 session) | **84.72 Hz** → SE of a 6-rep mean = **34.59 Hz** |
| ⇒ per-render SD, independent 24-rep same-voice pool | **77.72 Hz** |
| Alias-group f0 means | 75.41 / 75.16 / 73.54 Hz → spread **1.87 Hz** |
| ⇒ pooled within-name f0 SD (df=6) | 4.90 Hz → **SE of a 2-rep mean = 3.47 Hz** |

**The 13.05 Hz figure is a 2-replicate draw, not a floor** — see §3.5, where
6 replicates put the floor at 89.65 Hz. Everything downstream in this
section is computed against the understated 13.05 Hz figure and should be
read with that caveat.

### 3.2 Does reference timbre/pitch transfer to output?

The decisive test: rank the 4 **distinct** reference clips by a property,
rank the 4 corresponding **output** means by the same property, and ask
whether the order survives. (The earlier draft compared *output* r0 against
*output* mean, which is not a transfer test — that flaw is fixed here.)

| Property | Reference order | Output order | ρ | exact p (one-sided) |
|---|---|---|---|---|
| **Brightness (centroid)** | harvester_low < harvester < spokesman < settlement_human | same | **+1.000** | **1/24 = 0.0417** (the n=4 floor) |
| **Pitch (f0)** | harvester_low < harvester < spokesman < settlement_human | **reversed** | **−0.800** | 0.9583 |

**Brightness transfers perfectly; pitch does not transfer at all** — and in
fact inverts. This is not a defect, it is how F5-TTS works: it regenerates
the output fundamental from its own prosody model, so every reference renders
at ~73–77 Hz regardless of the pitch of the clip it was given. The repo
already says this in `build_manifest.py`:

> *"F0 does NOT discriminate on rendered OUTPUT (F5-TTS regenerates the
> fundamental from its own prosody model, so every reference lands at
> ~73-77 Hz); the spectral centroid and the log-mel timbre profile DO."*

**The claim is therefore: `ref` selects a timbre, and the timbre is
honoured and verifiable.** Per-name separation from the alias control:

| Distinct-ref name | Output centroid mean | Distance to nearest alias mean | σ |
|---|---|---|---|
| `harvester` | 206.03 Hz | 68.07 Hz | **2.79** |
| `harvester_low` | 172.59 Hz | 101.52 Hz | **4.16** |
| `settlement_human` | 474.82 Hz | 187.66 Hz | **7.69** |

Against the alias noise floor of 13.05 Hz, those are 5.2×, 7.8× and 14.4×
the spread of three names that share one audio file. The relabel permutation
test (any 3 of the 6 as the control group) gives p = 2/20 = 0.100 for
centroid and 4/20 = 0.200 for f0.

> **Caveat, added after the settling test (§3.5).** These ratios are
> against the 13.05 Hz floor, which a 6-replicate session puts at
> **89.65 Hz**. Re-measured the same way (6 replicates, one session), the
> minimum separation is **47.68 Hz** against that 89.65 Hz floor — i.e.
> **0.53×, not 5.2×**. The *ranking* result above is unaffected (brightness
> rho = +1.000 reproduces exactly at n=6); it is the *magnitude* of the
> margin that does not survive more replicates.

**The settling test the audio lane should run is therefore narrower than
"3 renders per name":** the question is not whether names separate, it is
whether *timbre* separation is stable enough to be a delivery check. The
right test is 3+ renders per name, **centroid** (not f0) as the statistic,
and a stated minimum separation in Hz rather than a p-value. **Run — result
in §3.5: the centroid does not settle.**

### 3.3 The boss register table is CORRECT (the earlier draft's claim is retracted)

The earlier draft said the contract's boss register table (−2 st / −4.5 st)
was wrong and that "both boss refs are the same pitch". **That was an
artefact of the octave-erroring estimator**, and it is retracted. Measured
with the repo's own YIN on the **reference clips** (not the output):

| Reference | f0 | Measured vs `spokesman` | Contract says |
|---|---|---|---|
| `spokesman` | 64.55 Hz | base | base |
| `harvester` | 59.41 Hz | **−1.44 st** | −2 st |
| `harvester_low` | 52.08 Hz | **−3.72 st** | −4.5 st |
| `settlement_human` | 70.79 Hz | **+1.60 st** | +1.5 st |

All three land within ~0.8 st of the design targets, and the **boss pair
separates by −2.28 st** — "the boss drops a register as it breaks" is
physically present in the reference audio.

The `MISMATCH` verdicts in `.audio_work/refs/ref_audit.json`
(*"expected -2 got -8"*) are a **units bug in that audit script**: it
compares an expected value in **semitones** against the applied shift in
**mel bins**. Those are different units (−8 mel bins ≈ −2 st is plausible;
−8 semitones is not). The verdict is not evidence of a problem and should
not be actioned. That audit's `f0_median_hz` values (62.34 / 197.33 / 67.64)
are also unreliable — `harvester_low` is 197 Hz there against a true 52.08 Hz,
an octave error on a 4-voiced-frame measurement (0.8% voiced fraction).

### 3.4 The delivered bank behaves as designed

Measured on the 40 shipped WAVs (excluding the corrupt file in §5.2):

| Group | n | Delivered centroid median | Range |
|---|---|---|---|
| `harvester` (phases 1–2) | 27 | 291.29 Hz | 199.8 – 408.8 |
| `harvester_low` (phase 3) | 12 | 197.20 Hz | 90.0 – 342.4 |

Median gap **94.1 Hz**, Monte-Carlo permutation **p = 0.00015**, Welch
t = 4.23 (dof 17). The phase-3 register change survives delivery and
normalisation. (Delivered centroids are not comparable to raw-render
centroids — the files are time-compressed ~2.3× and normalised — so this is
a behavioural check, not a fingerprint.)

### 3.5 The settling test: the 13.05 Hz alias floor does not hold up

§3.2's separation figures are computed from a **2-replicate** pool, and
§6.7 asks for the settling test to be run on centroid with 3+ replicates.
`Tools/python/settling_test.py` does exactly that: it renders N
replicates of one fixed line per registered reference and reports the
alias floor, the separations, and the settling curve in Hz.

**Result (n=6 per reference, one session):**

| Quantity | Value |
|---|---|
| Per-render centroid SD (pooled within-name, df=30) | **84.72 Hz** |
| Per-render centroid SD (independent 24-render same-voice pool) | **77.72 Hz** |
| Alias floor (three names sharing one `ref.wav`) | **89.65 Hz** |
| Alias floor as published in §3.1 (n=2) | 13.05 Hz |
| `harvester` distance to nearest alias mean | 47.68 Hz (0.53× floor) |
| `harvester_low` distance to nearest alias mean | 58.44 Hz (0.65× floor) |
| `settlement_human` distance to nearest alias mean | 133.93 Hz (1.49× floor) |
| **Minimum separation** | **47.68 Hz** |
| **Settles above the alias floor?** | **No** |

The 13.05 Hz figure in §3.1 is **not a stable noise floor** — it is one
2-replicate draw. The same three alias names, sharing one byte-identical
`ref.wav`, spread 89.65 Hz apart when measured with 6 replicates in a
single session, and the independent 24-render same-voice pool shows a
per-render SD of 77.72 Hz. A floor that small cannot be a floor: with
per-render SD ~78–85 Hz, the expected spread of three 2-replicate means
is ~93 Hz, so 13.05 Hz was a ~1-in-many low draw.

**The settling curve** (this session, floor and minimum separation as
replicates are added):

| Reps | Alias floor | Min separation | Ratio |
|---|---|---|---|
| 1 | 46.50 Hz | 0.74 Hz | 0.02× |
| 2 | 119.62 Hz | 16.06 Hz | 0.13× |
| 3 | 122.09 Hz | 23.01 Hz | 0.19× |
| 4 | 117.60 Hz | 59.99 Hz | 0.51× |
| 5 | 111.75 Hz | 52.07 Hz | 0.47× |
| 6 | 89.65 Hz | 47.68 Hz | 0.53× |

The ratio never reaches 1.0. The minimum separation is consistently
**below** the alias floor: the boss voices are *not* separable from the
alias group by scalar centroid on this statistic. §3.2's "5.2×, 7.8×,
14.4× the floor" were ratios against an understated floor, and the
underlying separation is real but smaller than the noise on the statistic.

**Why: the centroid is a spectral-tilt statistic, and tilt is a per-render
lottery.** Correlation between per-render spectral tilt and per-render
centroid is **+0.62** (n=18). The repo's own log-mel profile distance
*mean-centres* the band profile, so it cancels that tilt — and it
separates cleanly: within-name max **1.313**, between-name min **1.831**,
a **1.39× margin**, and every one of 12 single renders classified to the
correct reference clip. So the timbre separation the manifest claims is
real and robust **in mel-profile space**; it is the scalar centroid that
is too noisy to certify a single file.

**What this means for the contract.** §3.2's brightness-transfer result
is confirmed and is the right claim to keep: brightness rank order
transfers perfectly (rho = +1.000, p = 1/24, at the n=4 floor) in both
the 2-replicate pool and the fresh 6-replicate session. But a *delivery
check* that certifies "this file carries voice X" should use the mel
profile, not the centroid. The `voice_fingerprint` blocks in the manifest
already carry `spectral_centroid_hz`; they should be read as
*ordering* evidence, not as a per-file threshold.

---

## 4. The 15-word cap, and why the contract's own rule caps it lower

The contract sets **15 words** (§2) and separately sets a binding writing
rule: *"Every line must be intelligible after ~2× time compression."* Those
two numbers are in conflict, and the conflict is worth resolving because it
is the actual delivery constraint.

The delivery window is 1.5–6.0 s and the delivered bank sits at 5.841–5.866 s
— at the very top of the window. So the atempo factor needed to fit a line
into 6.0 s is:

| Words | Speech @ 1.38 s/word | atempo into 6.0 s | Passes the ~2× rule? |
|---|---|---|---|
| 7 | 9.66 s | 1.61× | yes |
| 8 | 11.04 s | 1.84× | yes |
| 9 | 12.42 s | 2.07× | **no** |
| 10 | 13.80 s | 2.30× | **no** (the delivered longest line) |
| 13 | 17.94 s | 2.99× | no |
| 15 | 20.70 s | **3.45×** | no |

**The contract's own ~2× intelligibility rule implies an 8-word ceiling, not
15.** The delivered bank already exceeds it: its longest line is 10 words,
needing 2.30×. This is a genuine internal inconsistency in the contract, and
it should be resolved explicitly — either the cap drops to ~8 words, or the
intelligibility rule is relaxed to ~2.4×, or the delivery window widens.

### The 1.38 s/word constant is not a law

It is a two-point extrapolation and it does not generalise:

- The two anchors the contract cites are **confirmed exactly** at the
  corrected scale: 3-word → 4.800 s (230 444 bytes), 13-word → 19.285 s
  (925 708 bytes). But 4.800/3 = **1.60** s/word and 19.285/13 = **1.48**
  s/word — the two anchors disagree by 8%.
- Across 75 unambiguous real lines the relation is
  **`audio_s = 0.917 × words + 1.94`** (residual SD 2.71 s), with per-line
  rates spanning **0.36 – 2.93 s/word**.
- The 14-word figure in the contract is itself a miscount: the 19.28 s line
  is 76 characters and 13 words.

A zero-intercept 1.38 s/word over-predicts a 15-word line by 32% (20.7 s
vs 15.7 s fitted). The cap should be justified on **measured** per-line
duration, not on a constant multiplied by a word count.

---

## 5. Defects found in the shipped artefacts

### 5.1 `insults_manifest.json` and the contract disagree on the field name — the contract is wrong

The contract §1.2 says:

> *"A human changes a character's voice by editing one line in the manifest
> — the `voice` field on the entry, or the `voice_cast` table."*

Neither exists in the built manifest:

- **0** occurrences of a JSON key `"voice"` anywhere in the manifest. The
  per-entry field is **`voice_ref`** (40 occurrences).
- **0** occurrences of `voice_cast`. The top-level block is **`voices`**
  (with `registered_references`, `character_voice_map`, `phase_to_ref`,
  `fingerprint_table`, `fingerprint_caveat`).
- `request_body_fields` correctly says `{"text": ..., "ref": ...}`, and
  `build_manifest.py` correctly writes `"ref"` (line 268). **The generator
  and the manifest are right; the prose in contract §1.2 (lines 126–127)
  and §4 (line 147) is stale.** A human following the contract would edit
  a field that does not exist.

The contract's §6 schema block also omits `voice_ref` and `voice_fingerprint`
from the per-taunt entry, though the built manifest has both.

### 5.2 `insult_p3_04.wav` — the file is sound; the original observation was a transient mid-repair artifact

The snapshot that produced the original §5.2 no longer describes the
repository. Measured now, on disk:

| | |
|---|---|
| On-disk sha256 | `b4772125525613aa8cb5c1856ad3790f2203db132915d084410fe76a64db0d90` — 516 704 bytes |
| Manifest sha256 | **the same value** — manifest and file agree |
| Manifest `verified` | `true`, `problems: []` |
| Measured on the file | 258 330 frames @ 44 100 Hz, 16-bit mono, 5.858 s; **30 423 unique sample values**; sample sd 4982.3; mean −69.2 (**0.21 %** of full scale); spectral centroid **273.4 Hz** (the other 39 taunts run 90–409 Hz); envelope modulation **4.10 Hz** (the other 39: 2.05–7.86 Hz) |
| Both shas quoted originally | `22863d38a35c0ebf…` (manifest) and `ab110bda98e9cb72…` (file) — **neither exists anywhere in the tree now** |

The constant-DC block that was measured still exists, but as a
*work-directory intermediate*, not as a deliverable:
`.audio_work/norm/_converge.wav` and `.audio_work/t1/_converge.wav` are
516 704 bytes / 258 330 frames with **1 unique sample value and sd exactly
0.0** — the broken limiter's converged output, the same shape and length as
the file that was observed. Its mtime is **09:23:24**, and the observed WAV
was **09:23:26**: the delivered file *was* the DC block at the moment of
the observation.

The repair chain is visible in the work directory:

| mtime | file | what it is |
|---|---|---|
| 08:55 | `.audio_work/norm/_a.wav`, `_b.wav`, `_c2.wav` (516 738 B) | pre-makeup 44.1 kHz intermediates |
| 09:23 | `.audio_work/norm/_converge.wav` | **constant-DC output** of the broken limiter |
| 10:05 | `.audio_work/norm/_makeup.wav` = sha `b4772125…` | repaired output — byte-identical to the delivered file |
| 10:05 | `Content/Audio/Insults/insult_p3_04.wav` | delivered file (sha `b4772125…`) |
| 10:07 | `Content/Audio/Insults/insults_manifest.json` | manifest rebuilt **after** the file, hashing it correctly |
| 10:16 | commit `568f892` | file + manifest + bank shipped |

So the original §5.2 was a true observation of a real intermediate
state, taken **42 minutes before** the file was repaired and the manifest
rebuilt. The current manifest and the current file agree byte for byte, and
all 44 delivered files re-verify against the manifest (0 discrepancies).
The hash-checked delivery the contract claims is now the delivered state.

### 5.3 The SFX directory is not derivable from the manifest — **FIXED**

The manifest lives in `Content/Audio/Insults/` and lists SFX as bare
filenames (`sfx_burp.wav`, …). The files are actually in
`Content/Audio/SFX/`. The SFX entries carry **no path, directory or
subdirectory key** — a loader resolving them relative to the manifest's own
directory finds nothing. The taunt filenames *are* relative to the manifest
directory and do resolve. Either add a path/dir key to the SFX entries or
state the layout in the contract.

**Fixed in `build_manifest.py`**: every SFX entry now carries an explicit
`path`, and the manifest was regenerated and re-verified. The only
difference from the committed manifest is those four `path` lines:

```
"path": "Content/Audio/SFX/sfx_burp.wav"
"path": "Content/Audio/SFX/sfx_pizza_impact.wav"
"path": "Content/Audio/SFX/sfx_menace_hum.wav"
"path": "Content/Audio/SFX/sfx_defeat_squelch.wav"
```

Taunt entries are unchanged: their `filename` is relative to the manifest's
own directory, so they resolve as before. Regeneration is idempotent —
re-running `build_manifest.py` reproduces the file byte for byte, and all
44 files re-verify against their manifest hashes.

### 5.4 The manifest's `measured_service_behaviour` note repeats the cost-model error

> *"Concurrency was verified: 3 concurrent renders completed in 126 s wall
> vs 171 s serial. Render cost is dominated by audio length, so short lines
> are also cheap lines."*

Both clauses are wrong at the corrected scale: length explains 8% of
wall-time variance, and the same 6.549 s line took 70 s and 365 s on
different passes. `speed_parameter_honoured: false` is *true* for a `speed`
field (the service ignores it), but the service does honour
`GILLSYSTEMS_TTS_NFE` — which is the actual speed lever.

### 5.5 The `voice_fingerprint` values in the manifest are fingerprints of the *reference*, not of the delivered file

Each taunt entry carries a `voice_fingerprint` block copied from the
reference's controlled renders (e.g. `harvester`: f0 76.91, centroid
206.03). The **delivered** file's own measurements are nothing like that
(`insult_p1_01.wav`: f0 75.89, centroid 408.84) because the delivered file
is time-compressed ~2.3× and normalised. Nothing in the manifest says so, so
a consumer could reasonably read `voice_fingerprint` as a property of the
file it ships. It is a property of the *reference clip* the file was
rendered from.

---

## 6. What the audio lane should do

1. **Re-render `insult_p3_04` and rebuild the manifest.** The file on disk is
   a DC block. Rebuild the manifest *after* the render so hashes are current.
   **ALREADY DONE** — the file was repaired (10:05), the manifest rebuilt
   (10:07), both shipped in `568f892`. See §5.2.
2. **Fix contract §1.2 and §4** to name `voice_ref` and the `voices` block
   instead of `voice` and `voice_cast`, and add `voice_ref` /
   `voice_fingerprint` to the §6 per-taunt schema. **DONE** — §1.2 now
   names `voice_ref` and the `voices` block, and §1.2.1 names the `voices`
   block; the per-taunt manifest schema in §6 carries `voice_ref` and
   `voice_fingerprint`.
3. **Give the SFX entries a path** or document the `Content/Audio/SFX/`
   layout in the contract. **DONE** — `build_manifest.py` now emits
   `path` on every SFX entry; the manifest was regenerated and re-verified.
   See §5.3.
4. **Resolve the 15-word vs ~2× intelligibility conflict** (§4). One of the
   two numbers has to move; the delivered 10-word line already needs 2.30×.
5. **Replace the 1.38 s/word constant** with the fitted
   `0.917 × words + 1.94` plus its 2.71 s residual, and re-derive the
   render-cost note from the contention measurement rather than from a
   length model. **DONE, with this item's own figures superseded** — the
   measured two-term fit in §1.3.1 is **`raw_duration_s = 0.9228 x words +
   2.831`** with a **0.652 s rms residual** and a 1.073 s/word through-origin
   slope. The 0.917 / 1.94 / 2.71 figures quoted in this item were an
   earlier estimate and do NOT match the bank. §1.1's cost row and the §4.1
   cap rationale now point at the measured model, and the old 1.38 s/word
   figure is gone from the contract.
6. **Do not action the `ref_audit.json` MISMATCH verdicts** — they compare
   semitones against mel bins. Re-run that audit with the repo's
   `voiceprint.py` if a register check is wanted; the register is correct.
   **DONE** — `ref_audit.py` now compares semitones to semitones and
   reports **OK** for all three character references (−1.44, −3.72, +1.60 st
   against targets −2, −4.5, +1.5 st, within 1 st).
7. **Run the settling test on centroid, not f0**, and report a minimum
   separation in Hz against the 13.05 Hz alias floor. **DONE** —
   `Tools/python/settling_test.py`, 6 replicates per reference, one
   session. The alias floor is **89.65 Hz**, not 13.05 Hz; minimum
   separation is **47.68 Hz**, which is **below** the floor. The centroid
   does not settle as a per-file discriminator. See §3.5.

---

## 7. Loose end, not this lane's

`Docs/generated/boss_bible.md` (untracked) claims a companion
`Docs/generated/boss_bible.json` that does not exist. `roster_bible.json`
already carries a `bosses[]` block, so the `.md` is the orphan, not the
missing file. Left alone — the new lane owns the boss document.

---

## 8. Files touched by this handover

| File | Change |
|---|---|
| `Docs/generated/voice_contract_handover.md` | **new** — this document |
| `Docs/generated/roster_bible.json` | **not written** (stand-down) |
| `Docs/generated/roster_bible.md` | **not written** (stand-down) |
| `Docs/generated/insult_bank_contract.md` | **modified** — §1.1 cost row, §1.2 field names, §4.1 cap rationale |
| `Tools/python/build_manifest.py` | **modified** — now emits `path` on every SFX entry |
| `Tools/python/ref_audit.py` | **modified** — compares semitones to semitones; reports OK for all three character references |
| `Tools/python/settling_test.py` | **new** — 6 replicates per reference, centroid settling |
| `Content/Audio/Insults/insults_manifest.json` | **regenerated** — SFX entries carry `path`; `insult_p3_04` sha256 matches the file on disk |
| `Agents/TEMPORAL_CHECK.md` (repo root, outside the game repo) | one compact board entry |

Analysis scripts live in the Hermes scratch directory
(`%LOCALAPPDATA%\hermes\cache\scratch\`): `definitive_voice.py`,
`final_findings.py`, `delivered_fp.py`, and the raw service log
`tts_raw.log`. No new TTS renders were performed; the only network call to
the service was a validation-only `POST` with an unknown `ref` to confirm the
HTTP 400 path, which consumes no render.
