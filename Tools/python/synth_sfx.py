"""Procedural SFX synthesis for the boss fight (numpy only, no TTS).

Four effects:
  1. burp        - low-frequency AM burst, fast decay, noisy tail (spherical belch)
  2. pizza_impact - short bright transient with a splat tail
  3. menace_hum  - slow detuned low drone
  4. defeat_squelch - downward pitch sweep with noise

All output: 44.1 kHz, 16-bit, MONO WAV.
Loudness normalisation is done by the shared post-process step (same as TTS):
-16 LUFS integrated, true peak below -1.0 dBTP, no clipping.
"""
import os
import sys
import wave

import numpy as np

SR = 44100
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "."


def _save(name, x):
    """Peak-normalise to 0.98, fade edges, write 16-bit mono WAV."""
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak > 0:
        x = x / peak * 0.98
    # 5 ms fade in/out to avoid clicks
    fade = int(SR * 0.005)
    n = min(fade, x.size // 2)
    if n > 0:
        ramp = np.linspace(0.0, 1.0, n, endpoint=True)
        x[:n] *= ramp
        x[-n:] *= ramp[::-1]
    pcm = np.clip(x, -1.0, 1.0)
    pcm16 = (pcm * 32767.0).astype("<i2")
    path = os.path.join(OUT_DIR, name)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm16.tobytes())
    print(f"wrote {path}  dur={x.size / SR:.3f}s")
    return path


def rng(seed):
    return np.random.default_rng(seed)


def make_burp():
    """Low-frequency AM burst, fast decay, noisy tail. Spherical creature belch."""
    r = rng(1001)
    dur = 1.9
    t = np.arange(int(SR * dur)) / SR

    # Body: fundamental sweeping down 95 -> 42 Hz, square-ish (odd harmonics)
    f0 = 95.0
    f1 = 42.0
    k = (f1 / f0) ** (1.0 / dur)
    phase = 2 * np.pi * f0 * (k ** t - 1.0) / np.log(k)
    body = np.zeros_like(t)
    for h, amp in ((1, 1.0), (3, 0.45), (5, 0.22), (7, 0.11)):
        body += amp * np.sin(h * phase + r.uniform(0, 2 * np.pi))

    # Amplitude: fast attack, fast-ish decay with a burp "bump" mid-decay
    env = np.exp(-t * 3.2)
    bump = 1.0 + 1.6 * np.exp(-((t - 0.16) ** 2) / (2 * 0.055**2))
    env = env * bump
    env *= np.clip(t / 0.02, 0, 1)  # 20 ms attack

    # Low-frequency AM "growl" (18 Hz tremolo)
    am = 0.55 + 0.45 * np.sin(2 * np.pi * 18.0 * t + 0.7)
    body = body * am * env

    # Noisy tail: filtered noise, band-passed down toward 300 Hz
    noise = r.normal(0, 1, t.size)
    # simple one-pole lowpass
    a = 0.06
    lp = np.empty_like(noise)
    acc = 0.0
    for i in range(noise.size):
        acc = (1 - a) * acc + a * noise[i]
        lp[i] = acc
    tail_env = np.exp(-t * 7.5)
    tail = lp * tail_env * 0.9

    x = body * 0.75 + tail
    # extra crackle transient at onset
    crack = r.normal(0, 1, t.size) * np.exp(-t * 60.0) * 0.25
    x = x + crack
    return x


def make_pizza_impact():
    """Short bright transient with a splat tail."""
    r = rng(2002)
    dur = 0.85
    t = np.arange(int(SR * dur)) / SR

    # Bright transient: fast-decaying broadband with metallic partials
    trans = r.normal(0, 1, t.size) * np.exp(-t * 42.0)
    metallic = np.zeros_like(t)
    for f, a, d in ((1850, 1.0, 26), (3120, 0.6, 30), (5400, 0.35, 38)):
        metallic += a * np.sin(2 * np.pi * f * t + r.uniform(0, 2 * np.pi)) * np.exp(-t * d)
    click = np.sin(2 * np.pi * 640 * t) * np.exp(-t * 90.0) * 0.5

    # Splat: pitch-dropping low body with a "blorp" formant
    f0 = 420.0
    f1 = 110.0
    k = (f1 / f0) ** (1.0 / dur)
    ph = 2 * np.pi * f0 * (k ** t - 1.0) / np.log(k)
    blorp = np.sin(ph) * np.exp(-t * 6.0) * 0.8
    blorp += 0.4 * np.sin(2 * ph) * np.exp(-t * 8.0)

    # Wet splatter noise, lowpassed
    noise = r.normal(0, 1, t.size)
    a = 0.12
    lp = np.empty_like(noise)
    acc = 0.0
    for i in range(noise.size):
        acc = (1 - a) * acc + a * noise[i]
        lp[i] = acc
    splat = lp * np.exp(-t * 11.0) * 0.85

    x = trans * 0.9 + metallic * 0.45 + click * 0.6 + blorp * 0.9 + splat
    return x


def make_menace_hum():
    """Slow detuned low drone."""
    r = rng(3003)
    dur = 6.0
    t = np.arange(int(SR * dur)) / SR

    # Three detuned low sines with slow beating
    x = np.zeros_like(t)
    for f, a, det in ((55.0, 1.0, 0.0), (55.0, 0.9, 0.31), (55.0 * 1.5, 0.45, 0.17)):
        ph = 2 * np.pi * (f + det) * t + r.uniform(0, 2 * np.pi)
        x += a * np.sin(ph)
    # Sub octave
    x += 0.5 * np.sin(2 * np.pi * 27.5 * t + 0.4)
    # Fifth above, quieter
    x += 0.22 * np.sin(2 * np.pi * 82.5 * t + 1.1)

    # Slow amplitude breathing
    x *= 0.72 + 0.28 * np.sin(2 * np.pi * 0.23 * t + 0.9)
    x *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.61 * t)

    # Subtle lowpassed noise bed for grit
    noise = r.normal(0, 1, t.size)
    a = 0.02
    lp = np.empty_like(noise)
    acc = 0.0
    for i in range(noise.size):
        acc = (1 - a) * acc + a * noise[i]
        lp[i] = acc
    x += lp * 0.35

    # Gentle fade in, long fade out
    fi = int(SR * 0.8)
    fo = int(SR * 1.2)
    x[:fi] *= np.linspace(0, 1, fi) ** 1.5
    x[-fo:] *= np.linspace(1, 0, fo) ** 2.0
    return x * 0.7


def make_defeat_squelch():
    """Downward pitch sweep with noise."""
    r = rng(4004)
    dur = 2.2
    t = np.arange(int(SR * dur)) / SR

    # Exponential downward pitch sweep 900 -> 55 Hz
    f0, f1 = 900.0, 55.0
    k = (f1 / f0) ** (1.0 / dur)
    ph = 2 * np.pi * f0 * (k ** t - 1.0) / np.log(k)

    # Vibrato that dies away
    vib = 1.0 + 0.08 * np.sin(2 * np.pi * 9.0 * t) * np.exp(-t * 0.9)
    tone = np.sin(ph * vib) * np.exp(-t * 1.6)
    tone += 0.45 * np.sin(2 * ph * vib) * np.exp(-t * 2.1)
    tone += 0.22 * np.sin(3 * ph * vib) * np.exp(-t * 2.8)

    # Squelch noise, band-limited by sweeping one-pole lowpass
    noise = r.normal(0, 1, t.size)
    lp = np.empty_like(noise)
    acc = 0.0
    for i in range(noise.size):
        cut = 0.45 * np.exp(-t[i] * 1.9) + 0.02
        acc = (1 - cut) * acc + cut * noise[i]
        lp[i] = acc
    # amplitude-modulated bubbling
    bub = 0.55 + 0.45 * np.sin(2 * np.pi * 16.0 * t + 2.0 * np.sin(2 * np.pi * 3.0 * t))
    sq = lp * bub * np.exp(-t * 2.4)

    x = tone * 0.85 + sq * 0.8
    # Wet "plop" at the very end
    plop_t = dur - 0.18
    m = t >= plop_t
    x[m] += 0.7 * np.sin(2 * np.pi * 70 * (t[m] - plop_t)) * np.exp(-(t[m] - plop_t) * 30)
    return x


BUILDERS = {
    "sfx_burp.wav": make_burp,
    "sfx_pizza_impact.wav": make_pizza_impact,
    "sfx_menace_hum.wav": make_menace_hum,
    "sfx_defeat_squelch.wav": make_defeat_squelch,
}

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, fn in BUILDERS.items():
        _save(name, fn())
    print("SFX_OK")
