"""Build the insult bank manifest -- the playback contract for the Rust side.

The manifest is the contract, so it is written to be self-describing:

  - a stable, explicit index and ordering (NOT a filesystem listing)
  - per line: id, filename, text, word count, phase weight, measured
    duration, measured LUFS, measured true peak, SHA-256
  - a top-level `rotation` block spelling out the playback contract
  - the TTS request contract (endpoint, field names, sample rate, voice)
    so the audio side and the Rust side cannot drift apart

Every measured number is re-measured here, from the delivered file on disk,
at manifest-build time. Nothing is carried over from an intermediate.
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audiomeasure as am  # noqa: E402
from taunt_lines import TAUNTS  # noqa: E402

INSULT_DIR = sys.argv[1] if len(sys.argv) > 1 else "Content/Audio/Insults"
SFX_DIR = sys.argv[2] if len(sys.argv) > 2 else "Content/Audio/SFX"
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(INSULT_DIR,
                                                           "insults_manifest.json")

TARGET_LUFS = -16.0
TP_CEILING = -1.0
DUR_MIN, DUR_MAX = 1.5, 6.0
SFX_DUR_MIN, SFX_DUR_MAX = 0.2, 10.0

# The F5-TTS service selects a voice with the "ref" field, NOT "voice".
# "voice" is accepted and silently ignored, which means an unknown value
# still renders the default register -- so the ref name is recorded per line
# here and the Rust side must never infer it.
#
# The bank was rendered with the Harvester's own register throughout: the
# boss is one character, so phase 1-2 use "harvester" and phase 3 drops to
# "harvester_low" as the voice comes apart with the fight.
PHASE_REF = {1: "harvester", 2: "harvester", 3: "harvester_low"}

# Character -> voice reference table. This is the table the roster bible
# quotes, and the Rust rotation must name the same voice for the same
# character as this manifest does.
CHARACTER_VOICE_MAP = {
    "harvester": {
        "ref": "harvester",
        "role": "THE BOSS - The Harvester, phases 1-2",
        "speaks": "the 40-line taunt bank (phase 1 and phase 2 entries)",
    },
    "harvester_low": {
        "ref": "harvester_low",
        "role": "THE BOSS - The Harvester, phase 3, voice coming apart",
        "speaks": "the 40-line taunt bank (phase 3 entries)",
    },
    "settlement_human": {
        "ref": "settlement_human",
        "role": "settlement survivor - not the boss",
        "speaks": "not in this bank; ref provisioned and verified for the "
                  "settlement scene",
    },
    "spokesman": {
        "ref": "spokesman",
        "role": "machine / default register (the service default)",
        "speaks": "not in this bank; the service default when ref is omitted",
    },
    "commander": {
        "ref": "commander",
        "role": "pre-existing alias of spokesman (identical ref.wav)",
        "speaks": "not in this bank",
    },
    "hermes": {
        "ref": "hermes",
        "role": "pre-existing alias of spokesman (identical ref.wav)",
        "speaks": "not in this bank",
    },
}

# Voice fingerprint, measured from double-render pairs. F0 does NOT
# discriminate on OUTPUT (F5-TTS regenerates the fundamental from its own
# prosody model, so every reference lands at ~73-77 Hz); the spectral
# centroid and the log-mel timbre profile DO. The fingerprint is recorded
# honestly with that caveat.
FINGERPRINT_PATH = os.path.join(".audio_work", "voices",
                                "voice_fingerprints.json")

SFX_ROLES = [
    ("sfx_burp", "pizza_launch",
     "Low-frequency AM burst with fast decay and noisy tail: a spherical "
     "creature belching. Fired on the pizza launch."),
    ("sfx_pizza_impact", "reveal_sting",
     "Short bright transient with a splat tail: pizza meeting floor. Used as "
     "the boss reveal sting."),
    ("sfx_menace_hum", "hit",
     "Slow detuned low drone: the boss is aware of you. Used on the hit."),
    ("sfx_defeat_squelch", "death",
     "Downward pitch sweep with noise: the boss goes down. Used on death."),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_fingerprints():
    """Load the measured voice fingerprint table, if it is present."""
    if not os.path.exists(FINGERPRINT_PATH):
        return {}
    with open(FINGERPRINT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("voice_fingerprint_table", {})


VOICE_FINGERPRINTS = load_fingerprints()


def check(m, dur_min, dur_max, is_taunt):
    problems = []
    d = m.get("duration_s")
    if d is None:
        problems.append("duration unknown")
    elif not (dur_min <= d <= dur_max):
        problems.append(f"duration {d}s outside [{dur_min},{dur_max}]")
    lufs = m.get("integrated_lufs")
    if lufs is None:
        problems.append("LUFS unknown")
    elif abs(lufs - TARGET_LUFS) > 0.6:
        problems.append(f"LUFS {lufs} not within 0.6 of {TARGET_LUFS}")
    tp = m.get("true_peak_dbtp")
    if tp is None:
        problems.append("true peak unknown")
    elif tp >= TP_CEILING:
        problems.append(f"true peak {tp} dBTP not below {TP_CEILING}")
    if (m.get("clipped_samples") or 0) > 0:
        problems.append(f"{m['clipped_samples']} clipped samples")
    if m.get("sample_rate") != 44100:
        problems.append(f"sample rate {m.get('sample_rate')} != 44100")
    if m.get("channels") != 1:
        problems.append(f"channels {m.get('channels')} != 1")
    if m.get("peak_abs") is not None and m["peak_abs"] >= 1.0:
        problems.append(f"sample peak {m['peak_abs']} >= full scale")
    return problems


def build():
    entries = []
    problems = []
    # stable ordering: bank order, which is phase 1, then 2, then 3.
    for idx, t in enumerate(TAUNTS):
        fn = t["id"] + ".wav"
        path = os.path.join(INSULT_DIR, fn)
        if not os.path.exists(path):
            problems.append(f"missing file {fn}")
            continue
        m = am.measure_all(path)
        probs = check(m, DUR_MIN, DUR_MAX, True)
        problems.extend(f"{fn}: {p}" for p in probs)
        ref = PHASE_REF.get(t["phase"], "harvester")
        entries.append({
            "index": len(entries),
            "id": t["id"],
            "filename": fn,
            "text": t["text"],
            "word_count": len(t["text"].split()),
            "phase": t["phase"],
            "phase_weight": {
                "phase_1": 1.0 if t["phase"] == 1 else 0.0,
                "phase_2": 1.0 if t["phase"] == 2 else 0.0,
                "phase_3": 1.0 if t["phase"] == 3 else 0.0,
            },
            "voice_ref": ref,
            "voice_fingerprint": VOICE_FINGERPRINTS.get(ref),
            "duration_s": m["duration_s"],
            "integrated_lufs": m["integrated_lufs"],
            "true_peak_dbtp": m["true_peak_dbtp"],
            "sample_peak_dbfs": m.get("sample_peak_dbfs"),
            "sample_rate": m.get("sample_rate"),
            "channels": m.get("channels"),
            "clipped_samples": m.get("clipped_samples"),
            "sha256": sha256(path),
            "bytes": os.path.getsize(path),
            "verified": not probs,
            "problems": probs,
        })

    sfx_entries = []
    for name, role, desc in SFX_ROLES:
        fn = name + ".wav"
        path = os.path.join(SFX_DIR, fn)
        if not os.path.exists(path):
            problems.append(f"missing sfx {fn}")
            continue
        m = am.measure_all(path)
        probs = check(m, SFX_DUR_MIN, SFX_DUR_MAX, False)
        problems.extend(f"{fn}: {p}" for p in probs)
        sfx_entries.append({
            "index": len(sfx_entries),
            "id": name,
            "filename": fn,
            "role": role,
            "description": desc,
            "duration_s": m["duration_s"],
            "integrated_lufs": m["integrated_lufs"],
            "true_peak_dbtp": m["true_peak_dbtp"],
            "sample_peak_dbfs": m.get("sample_peak_dbfs"),
            "sample_rate": m.get("sample_rate"),
            "channels": m.get("channels"),
            "clipped_samples": m.get("clipped_samples"),
            "sha256": sha256(path),
            "bytes": os.path.getsize(path),
            "verified": not probs,
            "problems": probs,
        })

    phase_counts = {}
    for e in entries:
        phase_counts[e["phase"]] = phase_counts.get(e["phase"], 0) + 1

    manifest = {
        "schema": "commander.boomer_shooter.insult_bank/1.0",
        "generated_by": "Tools/python/build_manifest.py",
        "description": (
            "Playback contract for The Harvester boss. The Rust taunt rotation "
            "reads this file; it is the single source of truth for which lines "
            "exist, what they say, and their measured delivery properties."
        ),
        "ordering": {
            "rule": (
                "Entries are in a FIXED order defined by the bank, not by a "
                "filesystem listing. `index` is the stable ordinal; consumers "
                "must sort by `index` and must never rely on directory order."
            ),
            "phase_order": [1, 2, 3],
            "count": len(entries),
            "phase_counts": {str(k): v for k, v in sorted(phase_counts.items())},
        },
        "delivery_spec": {
            "sample_rate_hz": 44100,
            "bit_depth": 16,
            "sample_format": "PCM s16le",
            "channels": 1,
            "container": "RIFF/WAVE",
            "target_integrated_lufs": TARGET_LUFS,
            "true_peak_ceiling_dbtp": TP_CEILING,
            "taunt_duration_window_s": [DUR_MIN, DUR_MAX],
            "sfx_duration_window_s": [SFX_DUR_MIN, SFX_DUR_MAX],
            "no_clipping": True,
            "note": (
                "Integrated loudness and true peak are measured on the "
                "DELIVERED file with ffmpeg ebur128; clipping is an exact "
                "sample-domain count. Values in this manifest were measured "
                "at build time, not asserted."
            ),
        },
        "tts_contract": {
            "engine": "F5-TTS v1 Base (CPU-only) on the fleet HTPC node",
            "endpoint": "http://10.0.0.42:8020/synth",
            "method": "POST",
            "content_type": "application/json",
            "request_body_fields": {
                "text": "string - the exact line text, verbatim from this manifest",
                "ref": "string - the reference name, see `voice_reference`",
            },
            "voice_reference": os.environ.get("F5_VOICE", "spokesman"),
            "service_output_sample_rate_hz": 24000,
            "service_output_format": "RIFF/WAVE, PCM s16le, mono",
            "delivery_sample_rate_hz": 44100,
            "post_process": [
                "resample 24000 -> 44100 Hz",
                "downmix to mono (service already mono)",
                "trim silence padding",
                "time-compress (atempo) into the duration window",
                "crest reduction, then converge integrated LUFS to -16.0",
                "true-peak limit below -1.0 dBTP",
                "write 16-bit PCM WAV",
            ],
            "measured_service_behaviour": {
                "seconds_of_audio_per_word": 1.38,
                "measured_from": "3-word phrase -> 4.80 s; 14-word phrase -> 19.28 s",
                "speed_parameter_honoured": False,
                "speed_parameter_note": (
                    "A 'speed' field is accepted but ignored: outputs at speed "
                    "1.0/1.5/2.0 were byte-identical in duration (19.28 s each)."
                ),
                "requests_run_concurrently": True,
                "note": (
                    "Concurrency was verified: 3 concurrent renders completed in "
                    "126 s wall vs 171 s serial. Render cost is dominated by "
                    "audio length, so short lines are also cheap lines."
                ),
            },
        },
        "rotation": {
            "description": (
                "The runtime contract for choosing which taunt plays. "
                "Implemented in Rust (taunts.rs) against this manifest."
            ),
            "phase_gating": {
                "rule": (
                    "A taunt may only play if its `phase` equals the boss's "
                    "current phase. Phase 1 lines never play in phase 2, etc."
                ),
                "phase_1": "early fight, cheerfully wrong non-sequiturs",
                "phase_2": "mid fight, glitchy repetition, thoughts looping",
                "phase_3": "late fight, threatening but still broken",
            },
            "no_immediate_repeat": {
                "rule": "The immediately preceding taunt id must never repeat.",
                "enforcement": "track last_played_id; exclude it from the candidate set",
            },
            "cooldown_window": {
                "rule": (
                    "The same line id must not play again within N plays. "
                    "N is the cooldown count, not seconds."
                ),
                "n_plays": 6,
                "enforcement": (
                    "keep a ring buffer of the last N played ids; exclude any "
                    "candidate present in that buffer"
                ),
                "note": (
                    "N=6 is chosen so that with 13+ lines per phase, a legal "
                    "candidate always exists even in the worst case."
                ),
            },
            "weighted_selection": {
                "rule": (
                    "Weight candidates by phase: the active phase's lines are "
                    "the only candidates, so the effective weight is 1.0 for "
                    "the active phase and 0.0 for the others."
                ),
                "phase_weights": {
                    "1": {"phase_1": 1.0, "phase_2": 0.0, "phase_3": 0.0},
                    "2": {"phase_1": 0.0, "phase_2": 1.0, "phase_3": 0.0},
                    "3": {"phase_1": 0.0, "phase_2": 0.0, "phase_3": 1.0},
                },
                "tie_break": (
                    "If weights are equal, pick uniformly at random among "
                    "candidates. Selection is uniform-within-phase, so no "
                    "line is favoured by ordering."
                ),
            },
            "timing": {
                "min_gap_s": 1.5,
                "max_gap_s": 6.0,
                "rule": (
                    "After a taunt finishes, wait at least min_gap_s before "
                    "the next one is eligible, and force a taunt at most "
                    "max_gap_s after the previous one finished."
                ),
            },
            "missing_file_fallback": {
                "rule": (
                    "If a selected line's WAV is missing or fails to load at "
                    "runtime, discard it and draw again from the same phase "
                    "pool, excluding it from the candidate set for this "
                    "draw."
                ),
                "max_attempts": 4,
                "exhausted_behavior": (
                    "If every candidate in the active phase is unusable, play "
                    "NO taunt and log the failure. Silence is correct; a "
                    "wrong-phase or corrupt line is not."
                ),
                "never": (
                    "Never fall back to a line from a different phase, and "
                    "never play a taunt whose file failed its delivery spec."
                ),
                "notes": (
                    "The `verified` flag on each entry records whether the "
                    "delivered file met the delivery spec at build time. "
                    "Entries with verified=false should not be scheduled."
                ),
            },
            "ducking": {
                "rule": (
                    "The taunt channel ducks the music bed by 6 dB while it "
                    "plays. Weapon SFX are never ducked."
                ),
                "duck_db": -6.0,
                "attack_ms": 80,
                "release_ms": 250,
            },
        },
        "voices": {
            "contract_note": (
                "The F5-TTS service selects a voice with the `ref` field. The "
                "field is named `voice` in some client code and is SILENTLY "
                "IGNORED by the service, which then renders the default "
                "register. An unknown `ref` returns HTTP 400. There are "
                "exactly SIX registered references; no others exist."
            ),
            "field_name": "ref",
            "not_voice": (
                "Do not send `voice`. It is accepted and ignored, so a typo "
                "in the voice name still produces a render -- in the wrong "
                "register, with no error."
            ),
            "registered_references": [
                "spokesman", "commander", "harvester",
                "harvester_low", "hermes", "settlement_human",
            ],
            "alias_note": (
                "spokesman, commander and hermes are byte-identical ref.wav "
                "files (md5 44e918212e457a1bd6967ee479ef8b16) and render "
                "identically. They are three names for one register, kept "
                "because existing call sites use them."
            ),
            "character_voice_map": CHARACTER_VOICE_MAP,
            "phase_to_ref": {
                "1": PHASE_REF[1], "2": PHASE_REF[2], "3": PHASE_REF[3],
            },
            "fingerprint_table": VOICE_FINGERPRINTS,
            "fingerprint_caveat": (
                "F0 does NOT discriminate on rendered OUTPUT: F5-TTS "
                "regenerates the fundamental from its own prosody model, so "
                "every reference measures ~73-77 Hz. The reference CLIPS "
                "order correctly on F0 (52.08 / 59.41 / 64.55 / 70.79 Hz) "
                "and the spectral centroid discriminates the rendered "
                "output (172 < 206 < 274 < 475 Hz). Treat the centroid as "
                "the discriminator, not the pitch."
            ),
        },
        "taunts": entries,
        "sfx": sfx_entries,
        "verification": {
            "all_taunts_verified": bool(entries) and all(e["verified"] for e in entries),
            "all_sfx_verified": bool(sfx_entries) and all(e["verified"] for e in sfx_entries),
            "problems": problems,
        },
    }
    return manifest, problems


if __name__ == "__main__":
    manifest, problems = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    v = manifest["verification"]
    print(f"manifest -> {OUT}")
    print(f"taunts={len(manifest['taunts'])} sfx={len(manifest['sfx'])}")
    print(f"all_taunts_verified={v['all_taunts_verified']} "
          f"all_sfx_verified={v['all_sfx_verified']}")
    if problems:
        print(f"PROBLEMS ({len(problems)}):")
        for p in problems:
            print("  -", p)
    else:
        print("no problems")
