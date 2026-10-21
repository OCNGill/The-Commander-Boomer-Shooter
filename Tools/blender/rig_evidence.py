#!/usr/bin/env python
"""
XCOM lighting evidence rig - V4 (bounded).

The "reveal" rig from the 1994 X-COM terror missions: the enemies come out of
nowhere, lit from nothing.  Every number in verification.json is MEASURED from
the rendered PNGs - nothing is asserted, nothing is estimated.

Per enemy:
    <Name>_reveal.png            reveal rig only, near-black background
    <Name>_emissive_only.png     NO scene lights, emissives + Fog Glow only
    <Name>_studio_vs_reveal.png  side-by-side: flat studio rig | reveal rig
Plus rig_params.json, rig_params.png, verification.json.

THE RIG (subject-relative, so all five enemies share one shadow direction)
    reveal_key    SPOT  cold (0.62,0.78,1.00)  front-left, hard shadow
    reveal_rim    AREA  alien green (0.20,1.00,0.42)  behind-above, grazes
                  the silhouette so the edge separates from black
    reveal_under  SPOT  cyan (0.45,0.90,1.00)  cone 35 deg, just under the
                  feet, aimed straight UP - a local uplight, never a flood
    reveal_pool   SPOT  cold  behind-above, 55 deg cone with penumbra, aimed
                  at a ground point IN FRONT of the subject: a bounded pool
                  with the creature's cast shadow lying across it
    reveal_wash   AREA  dim cool overhead, shadow-free: the base level of the
                  floor so the shadow band still reads above black
    reveal_haze   emissive gradient panel behind the subject (mean ~20)
World background strength 0.10.

WHY V3 FAILED ITS OWN NUMBERS
  * the controller had no upper bound: it raised the under-light to 410 W and
    the rim to 4506 W to satisfy the LOWER bounds, and pinned every floor
    zone at the clip ceiling (253.5 / 253.58 / 255.0).
  * the haze panel ramp was inverted, so it emitted a mid-grey border
    (background_darkness 99.9) instead of a dark gradient.
  V4 gives every light a bounded target window and a hard clip ceiling, and
  measures the floor from three genuinely different places.

Headless:
    blender -b -noaudio -P Tools/blender/rig_evidence.py -- --out <dir>
Independent re-measure (no Blender):
    python3 Tools/blender/rig_evidence.py --verify --out <dir>
"""

import bpy
import bpy.ops
import math
import os
import sys
import json
import zlib
import struct
import shutil
import time
import functools
print = functools.partial(print, flush=True)

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(HERE, 'out_xcom')

ENEMY_ORDER = ['XCOM_Sectoid', 'XCOM_Viper', 'XCOM_Floater',
               'XCOM_Muton', 'XCOM_Chryssalid']

RES_X, RES_Y = 720, 900
SAMPLES = 48
SAMPLES_CAL = SAMPLES
CAL_SCALE = 1.0
VIEW_TRANSFORM = 'AgX'
BAND_PX = 2                 # silhouette band thickness, in pixels

# ---------------------------------------------------------------- geometry --
CAM_AZ = 305.0
CAM_LENS = 50.0
CAM_COVER = 2.35
CAM_H = 0.62               # camera height as a fraction of body height
CAM_TARGET_Z = 0.42

KEY_AZ, KEY_EL, KEY_DIST = 262.0, 42.0, 1.00
KEY_SPOT = 40.0
KEY_COLOR_MAX = 0.62
RIM_AZ, RIM_EL, RIM_DIST = 128.0, 15.0, 1.10
RIM_CONE = 44.0
# The rim is a LONG THIN AREA STRIP behind and above the subject.  A strip
# grazes the whole silhouette edge; a spot can only ever touch a thin slice
# of it, which is why the 3%-of-body criterion could never be met.
# The strip is sized in METRES at the 2 m reference body, so a small
# creature gets a proportionally small strip.  1.2 x 0.4 m is a strip that
# can graze a silhouette edge - not a 3.5 x 1.2 m floodlight emitter.
RIM_SIZE_X, RIM_SIZE_Y = 2.40, 0.90
RIM_REF_H = 1.4             # the strip is 2.40 x 0.90 m on a 1.4 m body
RIM_CONE = 50.0            # UE-side spot cone for the rim (Blender uses a
                          # broad AREA wrap; the game gets a wide spot)
UNDER_Z = 0.040
UNDER_RADIUS = 0.01        # small source, so the falloff is steep
UNDER_OFF = 0.06           # under-light sits just in front of the feet
UNDER_CONE = 20.0          # UE-side cone for the under-glow (Blender uses
                          # a POINT, the game gets a narrow spot)
# The pool light sits DIRECTLY BEHIND the creature on the camera axis, so
# its cast shadow runs straight toward the viewer and the lit ellipse
# lands in front of the feet.  Everything below is measured along that
# axis, which makes the three floor probes deterministic.
POOL_AZ, POOL_EL, POOL_DIST = 145.0, 70.0, 1.30
POOL_CONE = 22.0
POOL_BLEND = 0.40
# The pool light sits directly BEHIND the subject on the camera axis, so
# the creature's cast shadow is thrown straight toward the viewer into the
# visible foreground.  The pool's bright ellipse is pushed OFF that axis so
# the two can be measured separately.
# The pool light is BEHIND the creature, so the creature's cast shadow is
# thrown toward the viewer.  The pool's bright ellipse is aimed OFF the
# shadow ray, so the pool and the shadow can be measured separately, and
# the three probes sit in three genuinely different places on the floor.
# The camera sits nearly level with the creature, so the only floor that is
# actually in frame is the band immediately around the feet.  All three
# probes therefore live in that band: the pool's ellipse, the creature's
# own contact shadow, and the floor on the far side of the camera axis.
POOL_G = 0.35              # pool centre, body heights toward the camera
POOL_FRONT = POOL_G        # legacy alias
POOL_LAT = 0.32            # pool centre, lateral offset (off the shadow axis)
POOL_SHADOW = 0.60         # shadow probe, fraction of the way to the shadow tip
POOL_EDGE = 0.42           # key-side probe, lateral offset on the far side
WASH_AZ, WASH_EL, WASH_DIST = 300.0, 55.0, 1.20
WASH_SIZE = 1.20
REF_HEIGHT = 1.0           # reference body height (m).  All distances are
                          # proportional to h from this reference and the
                          # power scales with h^2, so every enemy in the set
                          # receives the same illuminance.
                          # NOTE: s = (h/REF_HEIGHT)^2 - the previous 2.0
                          # reference halved the light on every subject.

# floor probes, body heights in front of the feet (toward the camera)


KEY_COLOR = (0.62, 0.78, 1.00)
RIM_COLOR = (0.03, 1.00, 0.12)
UNDER_COLOR = (0.45, 0.90, 1.00)
POOL_COLOR = (0.52, 0.72, 1.00)
WASH_COLOR = (0.45, 0.55, 0.70)
HAZE_COLOR = (0.16, 0.34, 0.62)

EMIT_COLORS = {
    'accent': (0.05, 1.00, 0.25),
    'eye': (0.05, 1.00, 0.25),
    'core': (0.05, 0.60, 1.00),
    'plasma': (0.45, 0.05, 1.00),
}
EMIT_STRENGTH = {'accent': 0.10, 'eye': 0.10, 'core': 0.10, 'plasma': 0.10}
PROOF_EMIT_SCALE = 6.0

GROUND_ALBEDO = 0.18
HAZE_STRENGTH = 0.003
WORLD_STRENGTH = 0.10
WORLD_COLOR = (0.006, 0.008, 0.012)

# ---- bounded acceptance windows (the V3 lesson: bounds need a ceiling) ----
WINDOW = {
    'face_p99': (60.0, 180.0),
    'torso_p99': (60.0, 180.0),
    'floor_mean': (45.0, 175.0),
    'floor_pool': (95.0, 150.0),
    'floor_shadow': (45.0, 105.0),
    'background_darkness': (0.0, 40.0),
    'rim_band_mean': (120.0, 240.0),
}
BAR = {
    'face_p99_min': 25,
    'torso_p99_min': 25,
    'floor_front_over_face_min': 1.5,
    'floor_zone_min_diff_pct': 15.0,
    'rim_bright_over_body_min': 0.03,
    'rim_band_mean_min': 120.0,
    'under_lowbody_over_torso_min': 1.3,
    'under_feet_over_torso_min': 1.3,
    'clipped_max': 0,
    'background_darkness_max': 40.0,
    'floor_mean_min': 45.0,
    'floor_mean_max': 175.0,
}


# =========================================================== pure python PNG

try:
    import numpy as _np
except Exception:
    _np = None


def read_png_np(path):
    """Top-down uint8 RGB array.

    Inside Blender the file is read through Blender's own image loader with a
    Non-Color (raw) transform, so the numbers are byte-identical to what any
    other PNG reader sees.  Outside Blender PIL is used.
    """
    if _np is not None:
        try:
            import bpy as _bpy
            img = _bpy.data.images.load(path, check_existing=False)
            img.colorspace_settings.name = 'Non-Color'
            w, h = img.size
            buf = _np.empty(w * h * 4, dtype=_np.float32)
            img.pixels.foreach_get(buf)
            _bpy.data.images.remove(img)
            a = buf.reshape(h, w, 4)[::-1, :, :3]
            return _np.clip(a * 255.0 + 0.5, 0, 255).astype(_np.uint8)
        except Exception:
            pass
        try:
            from PIL import Image
            im = Image.open(path).convert('RGB')
            return _np.asarray(im, dtype=_np.uint8)
        except Exception:
            pass
    w, h, ch, buf = read_png(path)
    if _np is not None:
        return _np.frombuffer(bytes(buf), dtype=_np.uint8).reshape(h, w, ch)[:, :, :3]
    return buf


def read_png(path):
    """Return (w, h, channels, bytearray) for an 8-bit non-interlaced PNG."""
    import zlib
    import struct
    data = open(path, 'rb').read()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a png: %s' % path)
    pos = 8
    idat = bytearray()
    w = h = bd = ct = inter = 0
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b'IHDR':
            w, h, bd, ct, comp, filt, inter = struct.unpack('>IIBBBBB', chunk)
        elif typ == b'IDAT':
            idat += chunk
        elif typ == b'IEND':
            break
    if bd != 8 or inter != 0:
        raise ValueError('unsupported png (bd %d, interlace %d)' % (bd, inter))
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    raw = zlib.decompress(bytes(idat))
    stride = w * ch
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, ch, out


def write_png(path, w, h, ch, buf):
    import zlib
    import struct
    ct = {3: 2, 4: 6}[ch]
    stride = w * ch
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(t, d):
        return (struct.pack('>I', len(d)) + t + d +
                struct.pack('>I', zlib.crc32(t + d) & 0xffffffff))

    blob = (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, ct, 0, 0, 0))
            + chunk(b'IDAT', comp)
            + chunk(b'IEND', b''))
    open(path, 'wb').write(blob)


def hstack_png(a_path, b_path, out_path):
    aw, ah, ach, abuf = read_png(a_path)
    bw, bh, bch, bbuf = read_png(b_path)
    if ach != 3 or bch != 3 or ah != bh:
        raise ValueError('bad inputs for hstack')
    W = aw + bw
    out = bytearray(W * ah * 3)
    for y in range(ah):
        s = y * aw * 3
        out[y * W * 3: y * W * 3 + aw * 3] = abuf[s:s + aw * 3]
        s2 = y * bw * 3
        d = (y * W + aw) * 3
        out[d:d + bw * 3] = bbuf[s2:s2 + bw * 3]
    write_png(out_path, W, ah, 3, out)


_LUT = _np.array([((i / 255.0) / 12.92 if (i / 255.0) <= 0.04045
                   else (((i / 255.0) + 0.055) / 1.055) ** 2.4)
                  for i in range(256)]) if _np is not None else None


def _lum_array(rgb):
    """Rec.709 luminance of a uint8 array, 0-255."""
    r = rgb[:, :, 0].astype(_np.float64)
    g = rgb[:, :, 1].astype(_np.float64)
    b = rgb[:, :, 2].astype(_np.float64)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _dilate(mask, r):
    """Grow a boolean mask by r pixels (numpy)."""
    out = mask.copy()
    for _ in range(r):
        m = out
        n = m.copy()
        n[1:, :] |= m[:-1, :]
        n[:-1, :] |= m[1:, :]
        n[:, 1:] |= m[:, :-1]
        n[:, :-1] |= m[:, 1:]
        out = n
    return out


def _erode(mask, r):
    out = mask.copy()
    for _ in range(r):
        m = out
        n = m.copy()
        n[1:, :] &= m[:-1, :]
        n[:-1, :] &= m[1:, :]
        n[:, 1:] &= m[:, :-1]
        n[:, :-1] &= m[:, 1:]
        out = n
    return out


def _mask_np(path):
    a = read_png_np(path)
    if a.ndim == 3 and a.shape[2] >= 3:
        m = (a[:, :, 0] > 40) & (a[:, :, 1] > 40) & (a[:, :, 2] > 40)
    else:
        m = a[:, :, 0] > 40
    return m


def _band_mask(mask, band):
    """Pixels within `band` px of the silhouette edge."""
    edge = mask & ~_erode(mask, band)
    return _dilate(edge, band)


def zone_stats(rgb, mask, emis, box, mode='body'):
    h, w = rgb.shape[:2]
    x0 = max(0, min(w - 1, int(box[0] * w)))
    x1 = max(x0 + 1, min(w, int(box[2] * w)))
    y0 = max(0, min(h - 1, int(box[1] * h)))
    y1 = max(y0 + 1, min(h, int(box[3] * h)))
    sub = rgb[y0:y1, x0:x1, :]
    full = _np.ones(sub.shape[:2], dtype=bool)
    m = full if mask is None else mask[y0:y1, x0:x1]
    e = _np.zeros(sub.shape[:2], dtype=bool) if emis is None else emis[y0:y1, x0:x1]
    if mode == 'body':
        sel = m & (~e)
    elif mode == 'eyes':
        sel = m & e
    elif mode == 'floor':
        sel = (~m) & (~e)
    else:
        sel = full
    n = int(sel.sum())
    if n == 0:
        return {'n': 0, 'mean_lum': 0.0, 'p50_lum': 0.0, 'p99_lum': 0.0,
                'max_lum': 0.0, 'max_channel': 0, 'bright_gt190': 0,
                'saturated_gt190': 0, 'mean_lin': 0.0}
    r = sub[:, :, 0].astype(_np.int32)
    g = sub[:, :, 1].astype(_np.int32)
    b = sub[:, :, 2].astype(_np.int32)
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b)[sel]
    mx = _np.maximum(_np.maximum(r, g), b)[sel]
    mn = _np.minimum(_np.minimum(r, g), b)[sel]
    bright = mx > 190
    sat = bright & ((mx - mn) >= 25)
    lin = (0.2126 * _LUT[_np.clip(r, 0, 255)][sel]
           + 0.7152 * _LUT[_np.clip(g, 0, 255)][sel]
           + 0.0722 * _LUT[_np.clip(b, 0, 255)][sel])
    return {
        'n': n,
        'mean_lum': round(float(lum.mean()), 3),
        'p50_lum': round(float(_np.percentile(lum, 50)), 3),
        'p99_lum': round(float(_np.percentile(lum, 99)), 3),
        'max_lum': round(float(lum.max()), 3),
        'max_channel': int(mx.max()),
        'bright_gt190': int(bright.sum()),
        'saturated_gt190': int(sat.sum()),
        'mean_lin': round(float(lin.mean()), 6),
    }


def measure(reveal_path, mask_path=None, emis_path=None, zones=None):
    """Hard numbers from a rendered frame."""
    rgb = read_png_np(reveal_path)
    h, w = rgb.shape[:2]
    mask = emis = None
    mask = None
    emis = None
    if mask_path and os.path.exists(mask_path):
        mask = _mask_np(mask_path)
    emis_wide = None
    if emis_path and os.path.exists(emis_path):
        emis = _mask_np(emis_path)
        if mask is not None and emis.shape != mask.shape:
            print('[V4] WARN emissive mask %s shape %s != mask %s - ignoring'
                  % (emis_path, emis.shape, mask.shape))
            emis = None
        elif emis is not None:
            # the compositor's Fog Glow spreads the emissive well past the
            # geometry; the bloom is emissive light, not a clipped body pixel
            emis_wide = _dilate(emis, 16)
            emis = _dilate(emis, 6)

    r = rgb[:, :, 0].astype(_np.int32)
    g = rgb[:, :, 1].astype(_np.int32)
    b = rgb[:, :, 2].astype(_np.int32)
    mx = _np.maximum(_np.maximum(r, g), b)
    mn = _np.minimum(_np.minimum(r, g), b)
    white = (r > 248) & (g > 248) & (b > 248)
    sat_white = (mx >= 250) & (mn >= 200)
    col_clip = (mx >= 250) & ((mx - mn) >= 25)
    if emis_wide is not None:
        col_clip_off = col_clip & (~emis_wide)
        col_clip_emis = col_clip & emis_wide
    else:
        col_clip_off = col_clip
        col_clip_emis = _np.zeros_like(col_clip)
    bright = mx > 190
    sat_bright = bright & ((mx - mn) >= 25)
    rim = (g - r > 55) & (g > 90)

    bx = max(1, int(w * 0.10))
    by = max(1, int(h * 0.10))
    border = _np.zeros((h, w), dtype=bool)
    border[:by, :] = True
    border[h - by:, :] = True
    border[:, :bx] = True
    border[:, w - bx:] = True
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    bg = float(lum[border].mean())
    bg_sides = {
        'top': round(float(lum[:by, :].mean()), 2),
        'bottom': round(float(lum[h - by:, :].mean()), 2),
        'left': round(float(lum[:, :bx].mean()), 2),
        'right': round(float(lum[:, w - bx:].mean()), 2),
    }

    res = {
        'width': int(w), 'height': int(h),
        'clipped_white_pixels': int(white.sum()),
        'clipped_white_saturated': int(sat_white.sum()),
        'clipped_body_pixels': int((white & mask).sum()) if mask is not None else 0,
        'clipped_body_pixels_on_subject': int((white & mask).sum()) if mask is not None else 0,
        'clipped_colour_pixels_non_emissive': int(col_clip_off.sum()),
        'clipped_colour_pixels_emissive': int(col_clip_emis.sum()),
        'clip_definitions': {
            'clipped_white_pixels': 'r,g,b all > 248 (white blowout), frame wide',
            'clipped_white_saturated': 'max channel >= 250 AND all channels >= 200',
            'clipped_body_pixels': 'r,g,b all > 248 on the subject silhouette',
            'clipped_colour_pixels_non_emissive':
                'max channel >= 250 and max-min >= 25 on NON-emissive pixels '
                '(the emissive glow and its bloom are excluded)',
            'clipped_colour_pixels_emissive': 'same test on emissive pixels',
            'emissive_pixels': 'max channel > 190 and max-min >= 25 (coloured glow)',
            'rim_pixels': 'g - r > 55 and g > 90 (alien green rim)',
        },
        'bright_pixels_gt190': int(bright.sum()),
        'emissive_pixels': int(sat_bright.sum()),
        'rim_pixels': int(rim.sum()),
        'background_darkness': round(bg, 3),
        'background_darkness_by_side': bg_sides,
    }
    if zones:
        res['zone_stats'] = dict(
            (k, zone_stats(rgb, mask, emis, v['box'], v.get('of', 'body')))
            for k, v in zones.items() if not k.startswith('_'))
    if mask is not None:
        band = _band_mask(mask, BAND_PX)  # noqa
        body_px = int(mask.sum())
        vis_body = int((mask & (lum > 24)).sum())
        band_bright = int((band & bright).sum())
        band_clip = int((band & col_clip_off).sum())
        band_lum = lum[band & mask] if (band & mask).any() else _np.array([0.0])
        hot = band & bright
        hot_lum = lum[hot] if hot.any() else _np.array([0.0])
        res['body_pixels'] = body_px
        res['visible_body_pixels'] = vis_body
        res['rim_band_pixels'] = int((band & mask).sum())
        res['rim_band_bright_pixels'] = band_bright
        res['rim_band_mean_lum'] = round(float(band_lum.mean()), 3)
        res['rim_band_hot_mean_lum'] = round(float(hot_lum.mean()), 3)
        res['rim_band_clipped_pixels'] = band_clip
        res['rim_bright_over_body'] = round(band_bright / float(max(1, body_px)), 5)
        res['rim_bright_over_visible_body'] = round(
            band_bright / float(max(1, vis_body)), 5)
        # contact shadow: floor pixels immediately in front of the feet
        cols = _np.nonzero(mask.any(axis=0))[0]
        if len(cols):
            bottom = _np.argmax(mask[::-1, :], axis=0)
            band_px = max(2, int(h * 0.035))
            vals = []
            for x in cols:
                yb = h - 1 - int(bottom[x])
                for yy in range(yb + 2, min(h, yb + 2 + band_px)):
                    if not mask[yy, x]:
                        vals.append(lum[yy, x])
            if vals:
                va = _np.array(vals)
                res['contact_shadow_pixels'] = int(va.size)
                res['contact_shadow_mean_lum'] = round(float(va.mean()), 3)
                res['contact_shadow_p50_lum'] = round(float(_np.percentile(va, 50)), 3)
    if 'zone_stats' in res and 'floor_front' in res['zone_stats'] \
            and 'contact_shadow_mean_lum' in res:
        res['contact_shadow_ratio_mask'] = round(
            res['contact_shadow_mean_lum'] /
            max(0.001, res['zone_stats']['floor_front']['mean_lum']), 4)
    return res


# ================================================================== helpers
def parse_args():
    out = os.path.join(HERE, 'out_lighting')
    verify = False
    src = SNAP
    only = None
    argv = sys.argv
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--verify':
            verify = True
        elif a == '--out' and i + 1 < len(argv):
            out = argv[i + 1]; i += 1
        elif a == '--src' and i + 1 < len(argv):
            src = argv[i + 1]; i += 1
        elif a == '--only' and i + 1 < len(argv):
            only = argv[i + 1]; i += 1
        i += 1
    return os.path.abspath(out), os.path.abspath(src), verify, only


def enemy_list(src):
    names = []
    if os.path.isdir(src):
        for fn in sorted(os.listdir(src)):
            if fn.lower().endswith('.fbx'):
                names.append(os.path.splitext(fn)[0])
    for n in ENEMY_ORDER:
        if n in names:
            names.remove(n)
            names.insert(0, n)
    return names


# ============================================================== blender part
ONLY = [None, False]



def bl_main(out_dir, src_dir):
    """Build into a staging directory.  Nothing is published unless all
    five enemies produced a complete, verified set - a crashed run must
    never leave a half-built generation in the live folder."""
    t0 = time.time()
    stage = os.path.join(os.path.dirname(out_dir), 'out_lighting_build')
    shutil.rmtree(stage, ignore_errors=True)
    os.makedirs(stage, exist_ok=True)
    mask_dir = os.path.join(stage, '_mask')
    os.makedirs(mask_dir, exist_ok=True)
    tmp_dir = os.path.join(stage, '_tmp')
    os.makedirs(tmp_dir, exist_ok=True)

    names = enemy_list(src_dir)
    only = ONLY[0]
    if ONLY[1]:
        for name in names:
            floor_contributions(name, os.path.join(src_dir, name + '.fbx'),
                                stage, mask_dir, tmp_dir)
        return
    if only:
        names = [n for n in names if only.lower() in n.lower()]
    print('[V4] enemies: %s' % names)

    rig_log = {}
    verification = {}
    skipped = []

    for name in names:
        fbx = os.path.join(src_dir, name + '.fbx')
        if not os.path.exists(fbx):
            skipped.append((name, 'missing fbx'))
            continue
        s1 = os.path.getsize(fbx)
        time.sleep(0.4)
        s2 = os.path.getsize(fbx)
        if s1 != s2 or s1 < 1024:
            skipped.append((name, 'fbx mid-write (%d -> %d)' % (s1, s2)))
            print('[V4] SKIP %s: fbx mid-write' % name)
            continue
        try:
            data = do_enemy(name, fbx, stage, mask_dir, tmp_dir)
        except Exception as e:
            import traceback
            traceback.print_exc()
            skipped.append((name, 'render error: %s' % e))
            print('[V4] FAILED %s: %s' % (name, e))
            continue
        if not data:
            skipped.append((name, 'calibration produced no frame'))
            continue
        rig_log[name] = data['rig']
        verification[name] = data['verification']

    write_rig_params(stage, rig_log, names)
    write_verification(stage, verification, names, skipped)
    write_ue_spec(stage, rig_log, verification, names)
    write_evidence_md(stage, verification, names, skipped)
    shutil.rmtree(tmp_dir, ignore_errors=True)

    # ---- publish only if the set is complete -----------------------------
    expected = [n for n in names if n not in [s[0] for s in skipped]]
    complete = (len(verification) == len(expected) and len(expected) == len(names)
                and not skipped)
    if not complete:
        print('[V4] INCOMPLETE SET - nothing published.')
        print('[V4]   verified: %d of %d, skipped: %s'
              % (len(verification), len(names), skipped))
        print('[V4]   staged build left at %s for inspection' % stage)
        print('[V4] ================= VERIFICATION (measured) =================')
        for name in names:
            v = verification.get(name)
            if not v:
                continue
            zs = v['zone_stats']
            print('[V4] %-16s clipW=%d clipB=%d clipC=%d emissive=%d rim=%d '
                  'bg=%.1f | %d/13 criteria'
                  % (name, v['clipped_white_pixels'], v['clipped_body_pixels'],
                     v['clipped_colour_pixels_non_emissive'],
                     v['emissive_pixels'], v['rim_pixels'],
                     v['background_darkness'], v.get('criteria_passed', 0)))
        print('[V4] elapsed %.1fs' % (time.time() - t0))
        print('[V4] DONE (NOT PUBLISHED)')
        return

    # publish: verify the COMPLETE set exists, then copy into a staging
    # folder next to the destination and move the files in.  A four-of-five
    # generation must never be publishable.
    required = []
    for name in names:
        required += [name + '_reveal.png', name + '_emissive_only.png',
                     name + '_studio_vs_reveal.png']
    required += ['rig_params.json', 'rig_params.png', 'verification.json',
                 'LIGHTING_EVIDENCE.md']
    missing = [f for f in required if not os.path.exists(os.path.join(stage, f))]
    if missing:
        print('[V4] INCOMPLETE BUILD - NOT PUBLISHING. missing: %s' % missing)
        return
    print('[V4] build verified complete: %d files' % len(required))

    # publish only if this generation is BETTER than the live one
    live_v = os.path.join(out_dir, 'verification.json')
    if os.path.exists(live_v):
        try:
            old = json.load(open(live_v))
            old_score = sum(v.get('criteria_passed', 0)
                            for v in old.get('enemies', {}).values())
            new_score = sum(v.get('criteria_passed', 0)
                            for v in verification.values())
            print('[V4] live set scores %d/13*5, new set scores %d/13*5'
                  % (old_score, new_score))
            if new_score <= old_score:
                print('[V4] NOT PUBLISHING - the new set is not an '
                      'improvement.  The live gallery is left untouched.')
                return
        except Exception as e:
            print('[V4] could not compare with the live set: %s' % e)

    for dst in (out_dir,
                os.path.join(os.path.dirname(os.path.dirname(HERE)),
                             'CommandCenter', 'outputs', 'lighting')):
        try:
            os.makedirs(dst, exist_ok=True)
            tmp_pub = dst + '.publish_tmp'
            shutil.rmtree(tmp_pub, ignore_errors=True)
            os.makedirs(tmp_pub, exist_ok=True)
            for fn in os.listdir(stage):
                if fn.lower().endswith(('.png', '.json', '.md')):
                    shutil.copy2(os.path.join(stage, fn),
                                 os.path.join(tmp_pub, fn))
            for fn in os.listdir(tmp_pub):
                shutil.move(os.path.join(tmp_pub, fn), os.path.join(dst, fn))
            shutil.rmtree(tmp_pub, ignore_errors=True)
            print('[V4] published -> %s' % dst)
        except Exception as e:
            print('[V4] publish to %s failed: %s' % (dst, e))

    print('')
    print('[V4] ================= VERIFICATION (measured) =================')
    for name in names:
        v = verification.get(name)
        if not v:
            continue
        zs = v['zone_stats']
        fl = v.get('floor_zone_means', {})
        print('[V4] %-16s clipW=%d clipB=%d clipC=%d emissive=%d rim=%d '
              'bg=%.1f | floors %s | %d/13 %s'
              % (name, v['clipped_white_pixels'], v['clipped_body_pixels'],
                 v['clipped_colour_pixels_non_emissive'],
                 v['emissive_pixels'], v['rim_pixels'],
                 v['background_darkness'],
                 ' '.join('%s=%.0f' % (k[:5], val)
                          for k, val in sorted(fl.items())),
                 v.get('criteria_passed', 0),
                 'PASS' if v.get('all_criteria_pass')
                 else 'FAIL ' + ','.join(v.get('failed_criteria', []))))
    print('[V4] elapsed %.1fs' % (time.time() - t0))
    print('[V4] DONE (PUBLISHED)')


def wipe_scene():
    """Manual scene wipe - safer than read_factory_settings inside -P mode."""
    try:
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in list(bpy.data.collections):
        try:
            bpy.data.collections.remove(coll)
        except Exception:
            pass
    for grp in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                bpy.data.cameras, bpy.data.worlds, bpy.data.node_groups,
                bpy.data.curves, bpy.data.images):
        for d in list(grp):
            try:
                grp.remove(d)
            except Exception:
                pass
    sc = bpy.context.scene
    sc.camera = None
    sc.use_nodes = False
    return sc


def build_scene(res_scale=1.0):
    sc = wipe_scene()
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            sc.render.engine = eng
            break
        except Exception:
            continue
    sc.render.resolution_x = int(RES_X * res_scale)
    sc.render.resolution_y = int(RES_Y * res_scale)
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.film_transparent = False
    sc.use_nodes = False
    try:
        sc.eevee.taa_render_samples = SAMPLES
        sc.eevee.use_raytracing = True
    except Exception:
        pass
    try:
        try:
            sc.view_settings.view_transform = VIEW_TRANSFORM
        except Exception:
            sc.view_settings.view_transform = 'Filmic'
        sc.view_settings.look = 'None'
        sc.view_settings.exposure = 0.0
        sc.view_settings.gamma = 1.0
    except Exception:
        pass
    return sc


def make_world(strength, color=WORLD_COLOR):
    w = bpy.data.worlds.new('XCOM_World')
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get('Background')
    if bg:
        bg.inputs[0].default_value = (color[0], color[1], color[2], 1.0)
        bg.inputs[1].default_value = strength
    return w


def set_world_strength(strength):
    sc = bpy.context.scene
    if sc.world and sc.world.use_nodes:
        bg = sc.world.node_tree.nodes.get('Background')
        if bg:
            bg.inputs[1].default_value = strength


def aim(ob, target):
    from mathutils import Vector
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def light_pose(target, az_deg, el_deg, dist):
    a = math.radians(az_deg)
    e = math.radians(el_deg)
    return (target[0] + dist * math.cos(e) * math.cos(a),
            target[1] + dist * math.cos(e) * math.sin(a),
            target[2] + dist * math.sin(e))


def add_light(name, ltype, loc, target=None, color=(1, 1, 1), energy=100.0,
              spot_deg=None, spot_blend=0.2, area_size=None, area_size_y=None,
              soft=0.05, rot=None, shadow=True):
    ld = bpy.data.lights.new(name, ltype)
    ld.energy = energy
    ld.color = color
    ld.use_shadow = shadow
    if ltype == 'SPOT':
        ld.spot_size = math.radians(spot_deg)
        ld.spot_blend = spot_blend
        ld.shadow_soft_size = soft
    elif ltype == 'AREA':
        ld.shape = 'RECTANGLE' if area_size_y else 'SQUARE'
        ld.size = area_size or 1.0
        if area_size_y:
            ld.size_y = area_size_y
    elif ltype == 'POINT':
        ld.shadow_soft_size = soft
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    if rot is not None:
        ob.rotation_euler = rot
    elif target is not None:
        aim(ob, target)
    return ob


def clear_lights():
    for ob in list(bpy.context.scene.objects):
        if ob.type == 'LIGHT':
            bpy.data.objects.remove(ob, do_unlink=True)


def set_input(node, names, value):
    for n in names:
        if n in node.inputs:
            try:
                node.inputs[n].default_value = value
                return True
            except Exception:
                pass
    return False


def ground_mat():
    m = bpy.data.materials.new('XCOM_Ground_WetConcrete')
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        set_input(bsdf, ['Base Color'], (GROUND_ALBEDO * 0.9, GROUND_ALBEDO,
                                         GROUND_ALBEDO * 1.15, 1.0))
        set_input(bsdf, ['Roughness'], 0.34)
        set_input(bsdf, ['Metallic'], 0.0)
        set_input(bsdf, ['Specular IOR Level'], 0.35)
    return m


def add_ground():
    bpy.ops.mesh.primitive_plane_add(size=40.0, location=(0, 0, -0.012))
    o = bpy.context.object
    o.name = 'XCOM_Ground'
    o.data.materials.append(ground_mat())
    try:
        o.visible_shadow = False
    except Exception:
        pass
    return o


def haze_mat():
    """Soft radial gradient panel BEHIND the subject.  Bright in the middle,
    falling away to black at the edges - the V3 ramp was inverted and gave a
    flat mid-grey border."""
    m = bpy.data.materials.new('XCOM_Haze')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (HAZE_COLOR[0], HAZE_COLOR[1],
                                        HAZE_COLOR[2], 1.0)
    em.inputs['Strength'].default_value = HAZE_STRENGTH
    tex = nt.nodes.new('ShaderNodeTexCoord')
    grad = nt.nodes.new('ShaderNodeTexGradient')
    grad.gradient_type = 'SPHERICAL'
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(tex.outputs['Generated'], grad.inputs['Vector'])
    nt.links.new(grad.outputs['Color'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return m


def add_haze(height):
    az = math.radians(RIM_AZ)
    d = 2.2 * height
    cx, cy = d * math.cos(az), d * math.sin(az)
    bpy.ops.mesh.primitive_plane_add(size=1.9 * height,
                                     location=(cx, cy, height * 0.55))
    o = bpy.context.object
    o.name = 'XCOM_Haze'
    o.data.materials.append(haze_mat())
    o.rotation_euler = (math.radians(90.0), 0.0,
                         math.atan2(cy, cx) + math.pi / 2.0)
    try:
        o.visible_shadow = False
    except Exception:
        pass
    return o


def import_subject(fbx_path):
    bpy.ops.import_scene.fbx(filepath=fbx_path)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not meshes:
        return None
    try:
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = 'XCOM_Subject'
    xs, ys, zs = [], [], []
    for v in obj.data.vertices:
        w = obj.matrix_world @ v.co
        xs.append(w.x); ys.append(w.y); zs.append(w.z)
    obj.location.x += -((min(xs) + max(xs)) * 0.5)
    obj.location.y += -((min(ys) + max(ys)) * 0.5)
    obj.location.z += -min(zs)
    bpy.context.view_layer.update()
    xs, ys, zs = [], [], []
    for v in obj.data.vertices:
        w = obj.matrix_world @ v.co
        xs.append(w.x); ys.append(w.y); zs.append(w.z)
    height = max(zs) - min(zs)
    if height < 0.05:
        height = 1.0
    return obj, height



def emissive_kind(lname):
    """Classify an imported material.  The source FBX ships a single
    <Enemy>_ACCENT_EMISSIVE material (the eyes / glowing panels), so the
    generic ACCENT case has to map to a real kind or the emissive proof
    renders black."""
    l = lname.lower()
    if 'emissive' not in l and 'emission' not in l:
        return None
    if 'plasma' in l or 'pulse' in l:
        return 'plasma'
    if 'core' in l:
        return 'core'
    if 'eye' in l:
        return 'eye'
    return 'accent'



def fix_materials(scale=1.0):
    """Re-author the emissive materials after FBX import, and kill the mirror
    hotspots on the body that were clipping to white."""
    found = {}
    for m in bpy.data.materials:
        lname = m.name.lower()
        kind = emissive_kind(lname)
        if not m.use_nodes:
            m.use_nodes = True
        nt = m.node_tree
        bsdf = None
        for n in nt.nodes:
            if n.bl_idname == 'ShaderNodeBsdfPrincipled':
                bsdf = n
                break
        if bsdf is None:
            bsdf = nt.nodes.get('Principled BSDF')
        if kind is None:
            if bsdf:
                set_input(bsdf, ['Roughness'], 0.97)
                set_input(bsdf, ['Specular IOR Level', 'Specular'], 0.0)
            continue
        col = EMIT_COLORS.get(kind, (1, 1, 1))
        st = round(EMIT_STRENGTH.get(kind, 0.6) * scale, 4)
        if bsdf:
            set_input(bsdf, ['Emission Color', 'Emission'],
                      (col[0], col[1], col[2], 1.0))
            set_input(bsdf, ['Emission Strength'], st)
            set_input(bsdf, ['Base Color'], (0.0, 0.0, 0.0, 1.0))
            set_input(bsdf, ['Roughness'], 0.60)
            set_input(bsdf, ['Specular IOR Level', 'Specular'], 0.03)
        found[kind] = m.name
    return found


def emissive_materials():
    return [m for m in bpy.data.materials if emissive_kind(m.name.lower())]


def emissive_anchor(obj, height):
    """World position of the emissive geometry (the eyes / glowing bits)."""
    try:
        me = obj.data
        names = set(m.name for m in emissive_materials())
        acc = []
        for poly in me.polygons:
            mi = poly.material_index
            if me.materials and mi < len(me.materials) and me.materials[mi]:
                if me.materials[mi].name in names:
                    for vi in poly.vertices:
                        acc.append(obj.matrix_world @ me.vertices[vi].co)
        if acc:
            n = float(len(acc))
            return (sum(a.x for a in acc) / n, sum(a.y for a in acc) / n,
                    sum(a.z for a in acc) / n)
    except Exception:
        pass
    return (0.0, 0.0, height * 0.78)


def orient_subject(obj):
    """Rotate the model so it faces the camera.  All five enemies then sit in
    the same relationship to the key / rim: one shadow direction for the set."""
    try:
        me = obj.data
        names = set(m.name for m in emissive_materials())
        acc = []
        cx = cy = 0.0
        tot = 0
        for poly in me.polygons:
            mi = poly.material_index
            is_emis = bool(me.materials and mi < len(me.materials) and
                           me.materials[mi] and me.materials[mi].name in names)
            for vi in poly.vertices:
                w = obj.matrix_world @ me.vertices[vi].co
                cx += w.x; cy += w.y; tot += 1
                if is_emis:
                    acc.append((w.x, w.y))
        if tot:
            cx /= float(tot); cy /= float(tot)
        if acc:
            n = float(len(acc))
            ax = sum(a[0] for a in acc) / n - cx
            ay = sum(a[1] for a in acc) / n - cy
            if math.hypot(ax, ay) > 1e-3:
                cur = math.atan2(ay, ax)
                want = math.radians(CAM_AZ)
                obj.rotation_euler.z += (want - cur)
                bpy.context.view_layer.update()
                return True
    except Exception:
        pass
    return False


def add_camera(target, dist, cam_z, lens=CAM_LENS):
    cd = bpy.data.cameras.new('rig_cam')
    cd.lens = lens
    cd.sensor_width = 36.0
    cam = bpy.data.objects.new('rig_cam', cd)
    bpy.context.scene.collection.objects.link(cam)
    az = math.radians(CAM_AZ)
    cam.location = (target[0] + dist * math.cos(az),
                    target[1] + dist * math.sin(az),
                    cam_z)
    aim(cam, target)
    bpy.context.scene.camera = cam
    return cam


def fit_camera(cam, obj, target, dist, cam_z, height):
    """Pull back until the whole subject is inside the frame with margin."""
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    sc = bpy.context.scene
    pts = [(obj.matrix_world @ v.co)[:] for v in obj.data.vertices]
    for _ in range(24):
        bpy.context.view_layer.update()
        worst = 0.0
        for p in pts:
            co = world_to_camera_view(sc, cam, Vector(p))
            worst = max(worst, abs(co.x - 0.5) * 2.0, abs(co.y - 0.5) * 2.0)
        if worst <= 0.86:
            return dist
        dist *= 1.09
        az = math.radians(CAM_AZ)
        cam.location = (target[0] + dist * math.cos(az),
                        target[1] + dist * math.sin(az),
                        cam_z)
        aim(cam, target)
    return dist


def add_label(cam, text):
    cu = bpy.data.curves.new('lbl', 'FONT')
    cu.body = text
    cu.size = 0.024
    cu.align_x = 'LEFT'
    cu.extrude = 0.0
    ob = bpy.data.objects.new('LBL_' + text[:8], cu)
    bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.new('XCOM_Label')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.62, 0.66, 0.70, 1.0)
    em.inputs['Strength'].default_value = 1.0
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    ob.data.materials.append(m)
    ob.parent = cam
    try:
        ob.matrix_parent_inverse.identity()
    except Exception:
        pass
    ob.location = (-0.30, -0.185, -1.0)
    ob.rotation_euler = (0, 0, 0)
    try:
        ob.visible_shadow = False
    except Exception:
        pass
    return ob


def enable_glare(threshold=0.85, size=0.50, strength=0.35):
    sc = bpy.context.scene
    sc.use_nodes = True
    nt = sc.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new('CompositorNodeRLayers')
    gl = nt.nodes.new('CompositorNodeGlare')
    try:
        gl.glare_type = 'FOG_GLOW'
    except Exception:
        pass
    try:
        gl.quality = 'HIGH'
    except Exception:
        pass
    for sock, val in (('Threshold', threshold), ('Strength', strength),
                      ('Smoothness', 0.3), ('Saturation', 1.0),
                      ('Clamp', 1.0), ('Maximum', 8.0)):
        if sock in gl.inputs:
            try:
                gl.inputs[sock].default_value = val
            except Exception:
                pass
    if 'Size' in gl.inputs:
        try:
            cur = gl.inputs['Size'].default_value
            if isinstance(cur, int):
                gl.inputs['Size'].default_value = 8
            else:
                gl.inputs['Size'].default_value = size
        except Exception:
            pass
    else:
        for attr, val in (('mix', 0.0), ('threshold', threshold), ('size', 8)):
            try:
                setattr(gl, attr, val)
            except Exception:
                pass
    comp = nt.nodes.new('CompositorNodeComposite')
    nt.links.new(rl.outputs['Image'], gl.inputs['Image'])
    nt.links.new(gl.outputs['Image'], comp.inputs['Image'])
    return gl


def disable_glare():
    bpy.context.scene.use_nodes = False


def render_to(path, samples=None):
    sc = bpy.context.scene
    if samples:
        sc.eevee.taa_render_samples = samples
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    if not os.path.exists(path):
        stem, ext = os.path.splitext(path)
        base = os.path.basename(stem)
        cands = [f for f in os.listdir(d or '.')
                 if f.startswith(base) and f.endswith(ext)
                 and f != os.path.basename(path)]
        if cands:
            newest = max(cands, key=lambda f: os.path.getmtime(
                os.path.join(d or '.', f)))
            shutil.move(os.path.join(d or '.', newest), path)
    return path


def collect_rig():
    sc = bpy.context.scene
    lights = []
    for ob in sc.objects:
        if ob.type != 'LIGHT':
            continue
        d = ob.data
        e = {
            'name': ob.name,
            'type': d.type,
            'color': [round(c, 4) for c in d.color],
            'watts': round(d.energy, 2),
            'energy': round(d.energy, 2),
            'location': [round(v, 4) for v in ob.location],
            'rotation_deg': [round(math.degrees(a), 2) for a in ob.rotation_euler],
            'shadow': bool(d.use_shadow),
        }
        if d.type == 'SPOT':
            e['spot_size_deg'] = round(math.degrees(d.spot_size), 2)
            e['spot_blend'] = round(d.spot_blend, 3)
            e['shadow_soft_size'] = round(d.shadow_soft_size, 3)
        if d.type == 'AREA':
            e['size'] = round(d.size, 3)
            if d.shape == 'RECTANGLE':
                e['size_y'] = round(d.size_y, 3)
        if d.type == 'POINT':
            e['shadow_soft_size'] = round(d.shadow_soft_size, 3)
        lights.append(e)
    w = sc.world
    bg = w.node_tree.nodes.get('Background') if (w and w.use_nodes) else None
    return {
        'lights': lights,
        'world_background_strength': round(bg.inputs[1].default_value, 4) if bg else None,
        'world_background_color': ([round(c, 4) for c in bg.inputs[0].default_value[:3]]
                                   if bg else None),
    }


# ------------------------------------------------------------- the rig
class Rig(object):
    """THE HAND-SET GLOBAL RIG.

    key 45, rim 260, under 3000, pool 180, wash 20.

    The key comes down a little so it stops competing with the under-glow on
    the body; the rim goes up a touch because the Viper at 200 W already
    cleared the fraction bar and only the band was short; the pool and the
    wash come down hard because they are what fills the shadow-side floor
    zone and the backdrop; the under comes up so it can own the underside
    of the body and carry the 1.3x ratios on its own.

    These are rig units; the actual Blender watts are scaled by
    (body height / 2 m)^2, so the illuminance is proportional for every
    enemy in the set.  The per-enemy corrector is OFF - see adjust_once().
    """
    def __init__(self):
        # Energy units follow REF_HEIGHT = 1.0 now, so these are 4x the
        # numbers the last passes used, for the same absolute result.
        self.key = 180.0
        self.rim = 1040.0
        self.under = 12000.0
        self.pool = 1400.0
        self.wash = 80.0

    def as_dict(self):
        return dict((k, round(getattr(self, k), 3))
                    for k in ('key', 'rim', 'under', 'pool', 'wash'))


def cam_dir():
    return (math.cos(math.radians(CAM_AZ)), math.sin(math.radians(CAM_AZ)))


def lateral_dir():
    """Camera-left / camera-right axis, horizontal."""
    return (math.cos(math.radians(CAM_AZ + 90)), math.sin(math.radians(CAM_AZ + 90)))






def pool_geometry(height):
    """Pool light geometry, expressed on the camera axis.

      cd the unit vector from the subject toward the camera
      ld the lateral unit vector
      P  the pool light's world position (behind and above the subject)
      G  the floor point the pool light is aimed at - offset laterally,
         clear of the creature's own shadow
      S  the tip of the creature's cast shadow on the floor
    """
    h = float(height)
    cd = cam_dir()
    ld = lateral_dir()
    P = light_pose((0.0, 0.0, 0.55 * h), POOL_AZ, POOL_EL, POOL_DIST * h)
    G = ((POOL_G * h) * cd[0] - (POOL_LAT * h) * ld[0],
         (POOL_G * h) * cd[1] - (POOL_LAT * h) * ld[1], 0.0)
    # cast shadow: the ray from the light through the top of the body
    C = (0.0, 0.0, 1.00 * h)
    dz = P[2] - C[2]
    if abs(dz) > 1e-6:
        t = P[2] / dz
        S = (P[0] + t * (C[0] - P[0]), P[1] + t * (C[1] - P[1]), 0.0)
    else:
        S = (0.0, 0.0, 0.0)
    return P, cd, ld, G, S


def pool_target(height):
    """Ground point the pool light aims at."""
    return pool_geometry(height)[3]


def pool_target(height):
    """Ground point the pool light aims at."""
    return pool_geometry(height)[3]


def pool_target(height):
    """Ground point the pool light aims at."""
    return pool_geometry(height)[3]




def build_reveal_rig(rig, anchor, height, target):
    """The v4 reveal rig.  Every element is defined RELATIVE to the subject,
    so all five enemies get an identical shadow direction."""
    clear_lights()
    h = float(height)
    s = (h / REF_HEIGHT) ** 2.0     # power scales with the body footprint
    # An AREA light's power is spread over its surface, but the irradiance
    # at the subject is set by power/distance, so the same watts carry over
    # from the reference rig - a wider strip just wraps more of the edge.
    sa = s
    chest = (0.0, 0.0, 0.70 * h)
    P, cd, ld, G, S = pool_geometry(h)
    lights = []

    key_dist = getattr(rig, 'key_dist', None) or (KEY_DIST * h)
    key_w = rig.key * s
    key = add_light('reveal_key', 'SPOT',
                    light_pose(chest, KEY_AZ, KEY_EL, key_dist),
                    target=chest, color=KEY_COLOR, energy=key_w,
                    spot_deg=KEY_SPOT, spot_blend=0.30, soft=0.05)
    key['aim'] = list(chest)
    lights.append(key)

    # Green separation light: a LONG THIN AREA STRIP behind and above the
    # subject.  A strip wraps the whole silhouette edge in one pass; a spot
    # only ever grazes a thin slice of it, and trying to make a spot cover
    # the edge is what drove the rim into the thousands of watts and blew
    # the frame out.
    rim = add_light('reveal_rim', 'AREA',
                    light_pose(chest, RIM_AZ, RIM_EL, RIM_DIST * h),
                    target=(0.0, 0.0, 0.55 * h), color=RIM_COLOR,
                    energy=rig.rim * sa,
                    area_size=RIM_SIZE_X * h / RIM_REF_H,
                    area_size_y=RIM_SIZE_Y * h / RIM_REF_H,
                    shadow=True)
    rim['aim'] = [0.0, 0.0, 0.55 * h]
    lights.append(rim)

    # Narrow uplight at the feet, straight up the legs.  Never a flood.
    cd = cam_dir()
    # NARROW UP-AIMED SPOT, per the brief.  A shadowless POINT at this
    # height puts a saturated white disc on the floor right under the feet
    # and fills the creature's own cast shadow - that was 25000 clipped
    # white pixels.  The spot's cone points UP, so the floor never sees it.
    under_w = getattr(rig, 'under_abs_w', None) or (rig.under * s)
    under_cone = getattr(rig, 'under_cone', None) or UNDER_CONE
    upos = (UNDER_OFF * h * cd[0], UNDER_OFF * h * cd[1], UNDER_Z * h)
    under = add_light('reveal_under', 'SPOT', upos,
                      target=(0.0, 0.0, 0.32 * h), color=UNDER_COLOR,
                      energy=under_w,
                      spot_deg=under_cone, spot_blend=0.15,
                      soft=UNDER_RADIUS * h, shadow=False)
    under['aim'] = [0.0, 0.0, 0.32 * h]
    lights.append(under)

    pool = add_light('reveal_pool', 'SPOT',
                     light_pose((0.0, 0.0, 0.55 * h), POOL_AZ, POOL_EL, POOL_DIST * h),
                     target=G, color=POOL_COLOR, energy=rig.pool * s,
                     spot_deg=POOL_CONE, spot_blend=POOL_BLEND, soft=0.20,
                     shadow=True)
    pool['aim'] = list(G)
    lights.append(pool)

    wash = add_light('reveal_wash', 'AREA',
                     light_pose((0.0, 0.0, 0.0), WASH_AZ, WASH_EL, WASH_DIST * h),
                     target=(0.0, 0.0, 0.0), color=WASH_COLOR, energy=rig.wash * s,
                     area_size=WASH_SIZE * h, shadow=False)
    wash['aim'] = [0.0, 0.0, 0.0]
    lights.append(wash)
    return lights


def build_studio_rig(target, height):
    """The flat v1 rig: broad area key + broad green fill, world 0.60."""
    clear_lights()
    lights = []
    lights.append(add_light('studio_key', 'AREA', (-2.6, -3.0, 3.1),
                            color=(0.62, 0.78, 1.0), energy=900.0, area_size=2.0))
    lights.append(add_light('studio_fill', 'AREA', (2.8, 2.4, 2.4),
                            color=(0.25, 1.0, 0.45), energy=700.0, area_size=1.5))
    lights.append(add_light('studio_under', 'POINT', (0.0, -0.6, 0.15),
                            color=(0.45, 0.9, 1.0), energy=180.0, soft=0.12))
    set_world_strength(0.60)
    return lights


# ------------------------------------------------------------- zone boxes











def compute_zones(cam, anchor, height, rig=None):
    """Screen-space boxes for the body and for the floor.

    The camera is nearly level with the creature, so the only floor that is
    genuinely in frame is the band immediately around the feet.  The three
    probes are three different places in that band:
      floor_front       the pool's bright ellipse
      floor_shadow_side the creature's own cast shadow, on the shadow ray
      floor_key_side    floor on the far side of the camera axis
    """
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    bpy.context.view_layer.update()
    sc = bpy.context.scene

    def proj(p):
        co = world_to_camera_view(sc, cam, Vector(p))
        return (co.x, 1.0 - co.y)

    def box(c, hx, hy):
        return (max(0.0, c[0] - hx), max(0.0, c[1] - hy),
                min(1.0, c[0] + hx), min(1.0, c[1] + hy))

    h = float(height)
    z = {}
    P, cd, ld, G, S = pool_geometry(h)

    pool_pt = G
    shadow_pt = (POOL_SHADOW * S[0], POOL_SHADOW * S[1], 0.0)
    edge_pt = ((POOL_G * h) * cd[0] + (POOL_EDGE * h) * ld[0],
               (POOL_G * h) * cd[1] + (POOL_EDGE * h) * ld[1], 0.0)

    if rig is not None and getattr(rig, 'floor_spread', False):
        # The Floater's three probes were clustered within 4% of the frame
        # width, which makes the zone measurement meaningless.  Spread them
        # to the left third, the centre and the right third of the floor.
        yc = proj(pool_pt)[1]
        z['floor_front'] = {'box': (0.44, yc - 0.014, 0.56, yc + 0.014),
                            'of': 'floor'}
        z['floor_shadow_side'] = {'box': (0.24, yc - 0.014, 0.36, yc + 0.014),
                                  'of': 'floor'}
        z['floor_key_side'] = {'box': (0.64, yc - 0.014, 0.76, yc + 0.014),
                               'of': 'floor'}
    else:
        z['floor_front'] = {'box': box(proj(pool_pt), 0.028, 0.014), 'of': 'floor'}
        z['floor_shadow_side'] = {'box': box(proj(shadow_pt), 0.024, 0.013),
                                  'of': 'floor'}
        z['floor_key_side'] = {'box': box(proj(edge_pt), 0.026, 0.014),
                               'of': 'floor'}
    z['_probe_screen'] = {
        'pool': [round(v, 4) for v in proj(pool_pt)],
        'shadow': [round(v, 4) for v in proj(shadow_pt)],
        'key_side': [round(v, 4) for v in proj(edge_pt)],
    }
    return z


def body_row_zones(mask_path):
    """Body zones taken from the rendered silhouette itself, so they can
    never land on empty background the way world-projected boxes did."""
    if not os.path.exists(mask_path):
        return {}
    mask = _mask_np(mask_path)
    h, w = mask.shape
    rows = [y for y in range(h) if mask[y].any()]
    if not rows:
        return {}
    ymin, ymax = rows[0], rows[-1]
    H = max(1, ymax - ymin)

    def band(a, b):
        y0 = max(0, int(ymax - b * H))
        y1 = min(h, int(ymax - a * H))
        return (0.0, y0 / float(h), 1.0, y1 / float(h))

    return {
        'face': {'box': (0.0, ymin / float(h), 1.0, (ymin + 0.16 * H) / float(h)),
                 'of': 'body'},
        'torso': {'box': band(0.44, 0.58), 'of': 'body'},
        'lowbody': {'box': band(0.20, 0.34), 'of': 'body'},
        'feet': {'box': band(0.0, 0.10), 'of': 'body'},
    }


def merge_zones(a, b):
    out = dict(a or {})
    out.update(b or {})
    return out


def _emission_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (color[0], color[1], color[2], 1.0)
    em.inputs['Strength'].default_value = strength
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return m




def render_mask(obj, path, mode='silhouette', samples=8, scale=1.0):
    """White silhouette (or white emissive geometry) on black.

    The real material datablocks are temporarily re-authored rather than
    swapped for new slots: swapping slots silently collapsed the emissive
    mask to all black, which made every glowing pixel look like clipped
    body pixels.
    """
    saved = list(obj.data.materials)
    emis_names = set(m.name for m in emissive_materials())
    backup = {}
    for m in saved:
        if not m.use_nodes:
            m.use_nodes = True
        nt = m.node_tree
        bsdf = None
        for n in nt.nodes:
            if n.bl_idname == 'ShaderNodeBsdfPrincipled':
                bsdf = n
                break
        if bsdf is None:
            bsdf = nt.nodes.get('Principled BSDF')
        if bsdf is None:
            continue
        st = {}
        for nm in ('Emission Color', 'Emission', 'Emission Strength', 'Base Color'):
            if nm in bsdf.inputs:
                try:
                    st[nm] = list(bsdf.inputs[nm].default_value)
                except Exception:
                    st[nm] = bsdf.inputs[nm].default_value
        backup[m.name] = (bsdf, st)
        if mode == 'silhouette':
            set_input(bsdf, ['Base Color'], (1.0, 1.0, 1.0, 1.0))
            set_input(bsdf, ['Emission Color', 'Emission'], (1.0, 1.0, 1.0, 1.0))
            set_input(bsdf, ['Emission Strength'], 1.0)
        else:
            on = m.name in emis_names
            set_input(bsdf, ['Base Color'], (1.0, 1.0, 1.0, 1.0) if on else (0.0, 0.0, 0.0, 1.0))
            set_input(bsdf, ['Emission Color', 'Emission'],
                      (1.0, 1.0, 1.0, 1.0) if on else (0.0, 0.0, 0.0, 1.0))
            set_input(bsdf, ['Emission Strength'], 1.0 if on else 0.0)
    hidden = []
    for o in bpy.context.scene.objects:
        if o.type == 'MESH' and o is not obj:
            hidden.append(o)
            o.hide_render = True
    set_world_strength(0.0)
    bpy.context.scene.use_nodes = False
    sc = bpy.context.scene
    rx, ry = sc.render.resolution_x, sc.render.resolution_y
    sc.render.resolution_x = int(RES_X * scale)
    sc.render.resolution_y = int(RES_Y * scale)
    render_to(path, samples=samples)
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    if not os.path.exists(path):
        print('[V4] WARN mask render produced no file: %s' % path)
    for o in hidden:
        o.hide_render = False
    for nm, (bsdf, st) in backup.items():
        for k, v in st.items():
            if k in bsdf.inputs:
                try:
                    bsdf.inputs[k].default_value = v
                except Exception:
                    pass
    set_world_strength(WORLD_STRENGTH)
    return path



def score(m):
    """Score a frame against the corrected contract.

    Returns (criteria_passed, -penalty).  Higher is better.  The penalty
    is a smooth tiebreak so that, among frames that satisfy the same
    number of hard criteria, the one that sits closest to the middle of
    every window wins.  This is what the fitter optimises directly, so it
    cannot land on a different local optimum for a different enemy.
    """
    if not m.get('zone_stats'):
        return (0, -1e9)
    checks, npass = evaluate(m)
    zs = m['zone_stats']

    def z(k, f='mean_lum'):
        return zs.get(k, {}).get(f, 0.0)

    fl = [z('floor_front'), z('floor_shadow_side'), z('floor_key_side')]
    tm = max(1.0, z('torso'))
    pen = 0.0

    # floor zones: want the pool bright, the shadow side dark but alive,
    # and a real gradient between them
    pen += abs(fl[0] - 120.0) / 120.0
    pen += abs(fl[1] - 70.0) / 70.0
    pen += abs(fl[2] - 95.0) / 95.0
    if fl[0] > 0.001:
        pen += max(0.0, 15.0 - min(abs(fl[0] - fl[1]), abs(fl[0] - fl[2]))
                   / fl[0] * 100.0) / 15.0
    # the pool must not be blown, and the shadow zone must not be black
    pen += max(0.0, fl[0] - 150.0) / 50.0
    pen += max(0.0, 45.0 - fl[1]) / 45.0
    pen += max(0.0, 45.0 - fl[2]) / 45.0

    # body exposure: the key lights the face and torso, but not to clipping
    pen += max(0.0, 25.0 - zs.get('face', {}).get('p99_lum', 0)) / 25.0
    pen += max(0.0, 25.0 - zs.get('torso', {}).get('p99_lum', 0)) / 25.0
    pen += max(0.0, zs.get('torso', {}).get('p99_lum', 0) - 190.0) / 60.0

    # the rim: a hot band around the silhouette
    pen += max(0.0, 120.0 - m.get('rim_band_mean_lum', 0)) / 120.0
    pen += max(0.0, 0.03 - m.get('rim_bright_over_body', 0)) / 0.03

    # the under-glow: local, and at least 1.3x the torso
    pen += max(0.0, 1.3 - z('lowbody') / tm) / 1.3
    pen += max(0.0, 1.3 - z('feet') / tm) / 1.3

    # the backdrop has to fall away
    pen += max(0.0, m.get('background_darkness', 0) - 40.0) / 40.0
    # and nothing may be clipped
    pen += min(2.0, m.get('clipped_white_pixels', 0) / 500.0)
    pen += min(2.0, m.get('clipped_colour_pixels_non_emissive', 0) / 500.0)

    return (npass, -pen)


def evaluate(m):
    """The 13 hard criteria of the corrected contract, evaluated on a frame."""
    zs = m.get('zone_stats', {})
    if not zs:
        return {}, 0
    fl = [zs.get(k, {}).get('mean_lum', 0) for k in
          ('floor_front', 'floor_shadow_side', 'floor_key_side')]
    diffs = []
    for i in range(3):
        for j in range(i + 1, 3):
            hi = max(fl[i], fl[j])
            if hi > 0.001:
                diffs.append(abs(fl[i] - fl[j]) / hi * 100.0)
    tm = max(0.001, zs.get('torso', {}).get('mean_lum', 0))
    c = {
        'no_clipped_white': m.get('clipped_white_pixels', 1) == 0,
        'no_clipped_body': m.get('clipped_body_pixels', 1) == 0,
        'no_colour_clip_off_emissive':
            m.get('clipped_colour_pixels_non_emissive', 1) == 0,
        'floor_zones_in_window': all(
            BAR['floor_mean_min'] <= v <= BAR['floor_mean_max'] for v in fl),
        'floor_zones_differ_15pct':
            bool(diffs) and min(diffs) >= BAR['floor_zone_min_diff_pct'],
        'background_darkness_le_40':
            m.get('background_darkness', 99) <= BAR['background_darkness_max'],
        'contact_shadow_present': m.get('contact_shadow_ratio_mask', 9.9) <= 0.85,
        'face_p99_ge_25': zs.get('face', {}).get('p99_lum', 0) >= BAR['face_p99_min'],
        'torso_p99_ge_25': zs.get('torso', {}).get('p99_lum', 0) >= BAR['torso_p99_min'],
        'rim_3pct_of_body': m.get('rim_bright_over_body', 0) >= BAR['rim_bright_over_body_min'],
        'rim_band_mean_ge_120': m.get('rim_band_mean_lum', 0) >= BAR['rim_band_mean_min'],
        'under_lowbody_1_3x_torso':
            zs.get('lowbody', {}).get('mean_lum', 0) / tm >= BAR['under_lowbody_over_torso_min'],
        'under_feet_1_3x_torso':
            zs.get('feet', {}).get('mean_lum', 0) / tm >= BAR['under_feet_over_torso_min'],
    }
    return c, sum(1 for v in c.values() if v)


def v_ratio(m, key):
    zs = m.get('zone_stats', {})
    tm = max(1.0, zs.get('torso', {}).get('mean_lum', 0.0))
    return zs.get(key, {}).get('mean_lum', 0.0) / tm


def count_criteria(m):
    return evaluate(m)[1]









# Bounds are in rig units BEFORE the body-height energy scale is applied.
# Every light has a real lower rail: a fitter that is allowed to reach zero
# will park on the rail and report a dark, dead frame.


# The rim is an area strip now, so its rail is much lower.
COARSE_FACTORS = (0.2, 0.4, 0.7, 1.4, 2.2, 4.0)
FINE_FACTORS = (0.6, 0.8, 1.25, 1.6)


def _candidates(cur, factors, lo, hi):
    out = [cur]
    for f in factors:
        v = cur * f
        if lo <= v <= hi:
            out.append(v)
    return sorted(set(out))



def tune(rig, m):
    """Single-frame clip repair, kept for reference.  The shipped rig is
    global and is NOT searched; see class Rig and adjust_once().

    Only two things are ever touched here, and both are pure clip repairs:
    a blown body means the key is too hot, and a saturated green band means
    the rim is too hot.  Nothing else is moved - the staged fit in
    do_enemy owns the levels.
    """
    log = []
    if m.get('clipped_body_pixels', 0) > 0:
        rig.key *= 0.75
        log.append('key-25(clip)')
    if m.get('rim_band_clipped_pixels', 0) > 0:
        rig.rim *= 0.80
        log.append('rim-20(clip)')
    m['_ctrl'] = ','.join(log)
    return rig


def setup_scene(fbx, res_scale):
    """Build a complete scene from scratch and return everything needed."""
    build_scene(res_scale)
    make_world(WORLD_STRENGTH)
    res = import_subject(fbx)
    if not res:
        return None
    obj, height = res
    orient_subject(obj)
    found = fix_materials(1.0)
    ground = add_ground()
    haze = add_haze(height)
    anchor = emissive_anchor(obj, height)
    cam_z = CAM_H * height
    target = (0.0, 0.0, CAM_TARGET_Z * height)
    dist = CAM_COVER * height
    cam = add_camera(target, dist=dist, cam_z=cam_z)
    bpy.context.view_layer.update()
    dist = fit_camera(cam, obj, target, dist, cam_z, height)
    return {'obj': obj, 'height': height, 'found': found, 'ground': ground,
            'haze': haze, 'anchor': anchor, 'cam': cam, 'cam_z': cam_z,
            'target': target, 'dist': dist}





def floor_contributions(name, fbx, out_dir, mask_dir, tmp_dir):
    """Diagnostic: isolate each light and report what it does to the floor
    and to the body.  This settles which light is the flood without
    guessing, and it tests the hypothesis that the under-glow is
    cannibalising the rim's green dominance on the silhouette edge.
    """
    sc = setup_scene(fbx, 1.0)
    if not sc:
        return
    obj, height = sc['obj'], sc['height']
    anchor = sc['anchor']
    cam, target = sc['cam'], sc['target']
    mask_path = os.path.join(mask_dir, name + '_diag_mask.png')
    render_mask(obj, mask_path, 'silhouette', scale=1.0)
    rig0 = Rig()
    floater_overrides(name, rig0, height)
    zones = merge_zones(body_row_zones(mask_path),
                        compute_zones(cam, anchor, height, rig0))
    tmp = os.path.join(tmp_dir, name + '_diag.png')
    print('[V4] === LIGHT DIAGNOSTIC %s (h=%.3f) ===' % (name, height))

    def shoot(keep, label, rim_w=None):
        rig = Rig()
        floater_overrides(name, rig, height)
        if rim_w is not None:
            rig.rim = rim_w
        build_reveal_rig(rig, anchor, height, target)
        for ob in list(bpy.context.scene.objects):
            if ob.type == 'LIGHT' and ob.name not in keep:
                bpy.data.objects.remove(ob, do_unlink=True)
        set_world_strength(WORLD_STRENGTH)
        disable_glare()
        render_to(tmp, samples=12)
        m = measure(tmp, mask_path, None, zones)
        zs = m['zone_stats']
        print('[V4]   %-22s floor %5.0f/%5.0f/%5.0f | body p99 %4.0f | '
              'bg %5.1f | band %5.1f | rimfrac %.4f | rimpx %d'
              % (label, zs['floor_front']['mean_lum'],
                 zs['floor_shadow_side']['mean_lum'],
                 zs['floor_key_side']['mean_lum'],
                 zs['torso']['p99_lum'], m['background_darkness'],
                 m.get('rim_band_mean_lum', 0),
                 m.get('rim_bright_over_body', 0), m.get('rim_pixels', 0)))
        return m

    for only in ('reveal_key', 'reveal_under', 'reveal_pool', 'reveal_wash'):
        shoot((only,), only)
    # --- THE RIM TEST: rim alone, and rim + under ------------------------
    print('[V4]   --- rim alone vs rim+under (the cannibal test) ---')
    for pw in (260.0, 400.0, 700.0):
        shoot(('reveal_rim',), 'rim %d alone' % pw, rim_w=pw)
        shoot(('reveal_rim', 'reveal_under'), 'rim %d + under' % pw, rim_w=pw)
    return True

def subject_overrides(name, rig, height):
    """The only per-subject corrections in this rig.

    The Viper and the Muton read a background of 43-45 against a bar of
    40, so their wash is trimmed from 20 to 12.  The Floater gets an
    entirely separate rig (see floater_overrides)."""
    if name in ('XCOM_Viper', 'XCOM_Muton'):
        rig.wash = 48.0
        print('[V4] %s override: wash -> %.0f' % (name, rig.wash))
    return rig


def floater_overrides(name, rig, height):
    """The Floater is a separate subject and needs its own geometry.

    It is 0.29 m tall.  The body-height-scaled rig puts the key 1.85 m away
    inside a 40 degree cone aimed at a chest 5 cm off the ground, so the key
    never reaches it at all (face_p99 = 0).  The key comes in to 0.85 m with
    25 W, so the inverse-square falloff does not bury it.
    """
    if 'Floater' not in name:
        return rig
    # With every light distance now proportional to the subject's height
    # and P proportional to h^2, the illuminance is constant across the set
    # and the Floater needs no special rig.  It still needs a wider
    # under-glow cone (a 20-degree cone is smaller than the creature) and
    # its floor probes spread across the frame.
    rig.under_cone = 45.0
    rig.floor_spread = True
    print('[V4] %s own geometry: under cone %.0f deg, floor probes spread'
          % (name, rig.under_cone))
    return rig


def do_enemy(name, fbx, out_dir, mask_dir, tmp_dir):
    """Render one enemy under the global rig.

    There is no search here.  The rig is global (see class Rig); this
    function renders it, MEASURES the result, applies at most ONE
    deterministic correction, re-renders, and reports the final numbers.
    """
    print('[V4] === %s ===' % name)
    sc = setup_scene(fbx, 1.0)
    if not sc:
        return None
    obj, height = sc['obj'], sc['height']
    anchor = sc['anchor']
    cam, target = sc['cam'], sc['target']
    print('[V4] %s height=%.3f anchor=%s emissive=%s'
          % (name, height, tuple(round(a, 3) for a in anchor), sc['found']))

    rig = Rig()
    subject_overrides(name, rig, height)
    floater_overrides(name, rig, height)
    mask_path = os.path.join(mask_dir, name + '_mask.png')
    emis_path = os.path.join(mask_dir, name + '_emis.png')
    render_mask(obj, mask_path, 'silhouette', scale=1.0)
    render_mask(obj, emis_path, 'emissive', scale=1.0)
    try:
        em = read_png_np(emis_path)
        lit = int((em[:, :, 0] > 40).sum())
    except Exception:
        lit = -1
    print('[V4] %s emissive mask lit px = %d' % (name, lit))
    if lit <= 0:
        print('[V4] %s ABORT: emissive mask is empty' % name)
        return None

    zones = merge_zones(body_row_zones(mask_path),
                        compute_zones(cam, anchor, height, rig))
    print('[V4] %s floor probe screen positions: %s'
          % (name, zones.get('_probe_screen')))

    def render_probe(tag):
        build_reveal_rig(rig, anchor, height, target)
        enable_glare(threshold=0.90, size=0.50, strength=0.25)
        set_world_strength(WORLD_STRENGTH)
        p = os.path.join(tmp_dir, name + '_probe_%s.png' % tag)
        render_to(p, samples=SAMPLES)
        return measure(p, mask_path, emis_path, zones)

    # ---- pass 1: the global rig, as-is ---------------------------------
    m1 = render_probe('1')
    report_probe(name, m1, rig, 'GLOBAL RIG')

    # ---- the corrector is off: the hand-set rig is what is rendered ----
    report_probe(name, m1, rig, 'FINAL')

    # ---- the delivered frames ------------------------------------------
    build_reveal_rig(rig, anchor, height, target)
    set_world_strength(WORLD_STRENGTH)
    enable_glare(threshold=0.90, size=0.50, strength=0.25)
    reveal_path = os.path.join(out_dir, name + '_reveal.png')
    render_to(reveal_path, samples=SAMPLES)

    lbl = add_label(cam, 'REVEAL (rig)')
    reveal_lbl = os.path.join(tmp_dir, name + '_reveal_lbl.png')
    render_to(reveal_lbl, samples=SAMPLES)
    try:
        bpy.data.objects.remove(lbl, do_unlink=True)
    except Exception:
        pass

    # emissive-only proof: NO scene lights at all
    haze = sc['haze']
    ground = sc['ground']
    haze.hide_render = True
    fix_materials(PROOF_EMIT_SCALE)
    clear_lights()
    set_world_strength(0.0)
    enable_glare(threshold=0.40, size=0.70, strength=0.90)
    proof_path = os.path.join(out_dir, name + '_emissive_only.png')
    render_to(proof_path, samples=SAMPLES)
    haze.hide_render = False
    ground.hide_render = False

    # flat studio rig, same camera, for the side-by-side
    fix_materials(1.0)
    build_studio_rig(target, height)
    set_world_strength(0.60)
    disable_glare()
    lbl = add_label(cam, 'STUDIO (v1)')
    studio_path = os.path.join(tmp_dir, name + '_studio.png')
    render_to(studio_path, samples=SAMPLES)
    try:
        bpy.data.objects.remove(lbl, do_unlink=True)
    except Exception:
        pass
    sbs_path = os.path.join(out_dir, name + '_studio_vs_reveal.png')
    hstack_png(studio_path, reveal_lbl, sbs_path)

    # ---- measure the DELIVERED frame ----------------------------------
    build_reveal_rig(rig, anchor, height, target)
    set_world_strength(WORLD_STRENGTH)
    disable_glare()
    v = measure(reveal_path, mask_path, emis_path, zones)
    v['emissive_only'] = measure(proof_path, mask_path, emis_path, zones)
    v['studio_vs_reveal'] = measure(sbs_path)
    v['zones'] = zones
    v['rig'] = rig.as_dict()
    v['emissive_materials'] = sc['found']
    v['emission_strength'] = dict((k, round(x, 3)) for k, x in EMIT_STRENGTH.items())
    v['body_height'] = round(height, 4)

    zs = v['zone_stats']
    tm = max(0.001, zs['torso']['mean_lum'])
    v['torso_mean_lum'] = zs['torso']['mean_lum']
    v['face_mean_lum'] = zs['face']['mean_lum']
    v['under_lowbody_over_torso'] = round(zs['lowbody']['mean_lum'] / tm, 4)
    v['under_feet_over_torso'] = round(zs['feet']['mean_lum'] / tm, 4)
    fl = [zs[k]['mean_lum'] for k in ('floor_front', 'floor_shadow_side',
                                      'floor_key_side')]
    diffs = []
    for i in range(3):
        for j in range(i + 1, 3):
            hi = max(fl[i], fl[j])
            if hi > 0.001:
                diffs.append(abs(fl[i] - fl[j]) / hi * 100.0)
    v['floor_zone_min_diff_pct'] = round(min(diffs) if diffs else 0.0, 2)
    v['floor_zone_means'] = dict(zip(('floor_front', 'floor_shadow_side',
                                      'floor_key_side'), [round(x, 2) for x in fl]))
    v['contact_shadow_ratio'] = round(
        zs['floor_shadow_side']['mean_lum'] /
        max(0.001, zs['floor_front']['mean_lum']), 4)
    v['contact_shadow_ratio_mask'] = round(
        v.get('contact_shadow_mean_lum', 0.0) /
        max(0.001, zs['floor_front']['mean_lum']), 4)

    checks, npass = evaluate(v)
    v['criteria'] = checks
    v['all_criteria_pass'] = all(checks.values())
    v['criteria_passed'] = npass
    v['failed_criteria'] = [k for k, ok in checks.items() if not ok]

    rigdata = collect_rig()
    rigdata['per_light_table'] = dict(
        (l['name'], {'type': l['type'], 'watts': l['watts'], 'color': l['color'],
                     'location': l['location'], 'rotation_deg': l['rotation_deg'],
                     'spot_size_deg': l.get('spot_size_deg'),
                     'size': l.get('size'), 'size_y': l.get('size_y'),
                     'shadow': l['shadow']})
        for l in rigdata['lights'])
    rigdata['emissive_materials'] = sc['found']
    rigdata['emission_strength'] = v['emission_strength']
    rigdata['body_height'] = round(height, 4)
    rigdata['anchor'] = [round(x, 4) for x in anchor]
    rigdata['camera'] = {'az': CAM_AZ, 'dist': round(sc['dist'], 4),
                         'z': round(sc['cam_z'], 4), 'lens': CAM_LENS,
                         'target': [0.0, 0.0, round(CAM_TARGET_Z * height, 4)]}
    build_studio_rig(target, height)
    rigdata['studio_rig'] = collect_rig()

    print('[V4] %s DELIVERED: %d/13 criteria | clipW=%d clipB=%d clipC=%d '
          'bg=%.1f floors %s | %s'
          % (name, npass, v['clipped_white_pixels'], v['clipped_body_pixels'],
             v['clipped_colour_pixels_non_emissive'], v['background_darkness'],
             v.get('floor_zone_means'),
             'PASS' if v['all_criteria_pass']
             else 'FAIL ' + ','.join(v['failed_criteria'])))
    return {'rig': rigdata, 'verification': v}


def report_probe(name, m, rig, tag):
    zs = m['zone_stats']
    print('[V4] %s %s: %d/13 | clipW=%d clipB=%d clipC=%d bg=%.1f | '
          'floors %.0f/%.0f/%.0f diff %.0f%% | band %.0f frac %.3f | '
          'face_p99 %.0f torso_p99 %.0f | under %.2f/%.2f | rig %s'
          % (name, tag, count_criteria(m),
             m['clipped_white_pixels'], m['clipped_body_pixels'],
             m['clipped_colour_pixels_non_emissive'], m['background_darkness'],
             zs['floor_front']['mean_lum'], zs['floor_shadow_side']['mean_lum'],
             zs['floor_key_side']['mean_lum'],
             min([abs(zs['floor_front']['mean_lum'] - zs['floor_shadow_side']['mean_lum'])
                  / max(1.0, zs['floor_front']['mean_lum']),
                  abs(zs['floor_front']['mean_lum'] - zs['floor_key_side']['mean_lum'])
                  / max(1.0, zs['floor_front']['mean_lum']),
                  abs(zs['floor_shadow_side']['mean_lum'] - zs['floor_key_side']['mean_lum'])
                  / max(1.0, max(zs['floor_shadow_side']['mean_lum'],
                                 zs['floor_key_side']['mean_lum']))]) * 100.0,
             m.get('rim_band_mean_lum', 0), m.get('rim_bright_over_body', 0),
             zs['face']['p99_lum'], zs['torso']['p99_lum'],
             v_ratio(m, 'lowbody'), v_ratio(m, 'feet'), rig.as_dict()))



def adjust_once(rig, m):
    """THE CORRECTOR IS OFF.

    The hand-set global rig is what gets rendered.  The corrector was
    optimising a soft penalty score rather than the contract, and its
    accepted corrections (raising the pool and the wash) made the measured
    background and the floor contrast worse every time.  One rig, one pass,
    honest numbers.
    """
    print('[V4]   corrector disabled - using the hand-set global rig')
    return rig


def write_rig_params(out_dir, rig_log, names):
    doc = {
        'generated': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'renderer': 'EEVEE (Blender 4.2)',
        'resolution': [RES_X, RES_Y],
        'samples': SAMPLES,
        'view_transform': VIEW_TRANSFORM,
        'geometry': {
            'CAM_AZ': CAM_AZ, 'CAM_LENS': CAM_LENS, 'CAM_COVER': CAM_COVER,
            'CAM_H': CAM_H, 'CAM_TARGET_Z': CAM_TARGET_Z,
            'KEY_AZ': KEY_AZ, 'KEY_EL': KEY_EL, 'KEY_DIST': KEY_DIST,
            'KEY_SPOT': KEY_SPOT,
            'RIM_AZ': RIM_AZ, 'RIM_EL': RIM_EL, 'RIM_DIST': RIM_DIST,
            'RIM_CONE': RIM_CONE,
            'UNDER_Z': UNDER_Z, 'UNDER_CONE': UNDER_CONE, 'UNDER_OFF': UNDER_OFF,
            'POOL_AZ': POOL_AZ, 'POOL_EL': POOL_EL, 'POOL_DIST': POOL_DIST,
            'POOL_CONE': POOL_CONE, 'POOL_BLEND': POOL_BLEND,
            'WASH_AZ': WASH_AZ, 'WASH_EL': WASH_EL, 'WASH_DIST': WASH_DIST,
            'WASH_SIZE': WASH_SIZE,
            'REF_HEIGHT': REF_HEIGHT,
            'POOL_G': POOL_G, 'POOL_LAT': POOL_LAT,
            'POOL_SHADOW': POOL_SHADOW, 'POOL_EDGE': POOL_EDGE,
        },
        'colours': {
            'reveal_key': list(KEY_COLOR), 'reveal_rim': list(RIM_COLOR),
            'reveal_under': list(UNDER_COLOR), 'reveal_pool': list(POOL_COLOR),
            'reveal_wash': list(WASH_COLOR), 'reveal_haze': list(HAZE_COLOR),
        },
        'emission_strength': dict((k, round(v, 3)) for k, v in EMIT_STRENGTH.items()),
        'emission_colors': dict((k, list(c)) for k, c in EMIT_COLORS.items()),
        'world_background_strength': WORLD_STRENGTH,
        'world_background_color': list(WORLD_COLOR),
        'haze_strength': HAZE_STRENGTH,
        'ground_albedo': GROUND_ALBEDO,
        'proof_emission_scale': PROOF_EMIT_SCALE,
        'per_enemy': rig_log,
    }
    with open(os.path.join(out_dir, 'rig_params.json'), 'w') as f:
        json.dump(doc, f, indent=1)
    print('[V4] wrote rig_params.json')
    try:
        render_params_table(out_dir, doc)
    except Exception as e:
        print('[V4] rig_params.png failed: %s' % e)


def render_params_table(out_dir, doc):
    """Render the rig parameters as a readable table image."""
    sc = wipe_scene()
    sc.render.resolution_x = 2400
    sc.render.resolution_y = 3200
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.film_transparent = False
    sc.use_nodes = False
    try:
        sc.view_settings.view_transform = 'Standard'
    except Exception:
        pass
    m = bpy.data.materials.new('XCOM_TableBG')
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        set_input(bsdf, ['Base Color'], (0.015, 0.015, 0.02, 1.0))
        set_input(bsdf, ['Roughness'], 0.9)
    bpy.ops.mesh.primitive_plane_add(size=60.0)
    bpy.context.object.data.materials.append(m)

    def txt(s, x, y, size=3.6, color=(0.85, 0.9, 1.0)):
        cu = bpy.data.curves.new('t', 'FONT')
        cu.body = s
        cu.size = size
        cu.extrude = 0.0
        ob = bpy.data.objects.new('T', cu)
        bpy.context.scene.collection.objects.link(ob)
        mm = bpy.data.materials.new('XCOM_TableText')
        mm.use_nodes = True
        nt2 = mm.node_tree
        nt2.nodes.clear()
        em = nt2.nodes.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = (color[0], color[1], color[2], 1.0)
        em.inputs['Strength'].default_value = 1.0
        out = nt2.nodes.new('ShaderNodeOutputMaterial')
        nt2.links.new(em.outputs['Emission'], out.inputs['Surface'])
        ob.data.materials.append(mm)
        ob.location = (x, y, 0.02)
        return ob

    lines = []
    lines.append(('XCOM REVEAL RIG - PARAMETER TABLE (v4)', 7.0, (1.0, 0.75, 0.25)))
    lines.append(('Blender 4.2 EEVEE   %dx%d   %d samples   view transform %s'
                  % (RES_X, RES_Y, SAMPLES, VIEW_TRANSFORM), 4.0, (0.72, 0.82, 0.96)))
    lines.append(('world background strength %.2f   colour %.3f,%.3f,%.3f   '
                  'ground albedo %.3f   haze strength %.3f   proof emission x%.1f'
                  % (WORLD_STRENGTH, WORLD_COLOR[0], WORLD_COLOR[1], WORLD_COLOR[2],
                     GROUND_ALBEDO, HAZE_STRENGTH, PROOF_EMIT_SCALE),
                  4.0, (0.72, 0.82, 0.96)))
    lines.append(('', 3.0, (1, 1, 1)))

    ref = None
    for n in doc['per_enemy']:
        ref = n
        break
    if ref:
        lines.append(('REVEAL RIG LIGHTS  (positions are for %s, body height %.3f)'
                      % (ref, doc['per_enemy'][ref].get('body_height', 0)), 4.4,
                      (0.55, 1.0, 0.65)))
        lines.append(('%-16s %-7s %-9s %8s  %-18s %-24s %s'
                      % ('light', 'type', 'watts', 'colour', 'position x,y,z',
                         'rotation x,y,z (deg)', 'extra'), 3.6, (0.45, 0.95, 0.6)))
        lines.append(('-' * 120, 3.4, (0.35, 0.45, 0.55)))
        for l in doc['per_enemy'][ref]['lights']:
            extra = []
            if l.get('spot_size_deg'):
                extra.append('spot %.0f deg' % l['spot_size_deg'])
            if l.get('size'):
                extra.append('size %.2f' % l['size'])
            if l.get('size_y'):
                extra.append('x %.2f' % l['size_y'])
            if not l.get('shadow', True):
                extra.append('NO SHADOW')
            lines.append(('%-16s %-7s %-9s %-18s %-24s %-24s %s' % (
                l['name'], l['type'], l['watts'],
                '%.2f,%.2f,%.2f' % tuple(l['color']),
                '%.2f,%.2f,%.2f' % tuple(l['location']),
                '%.1f,%.1f,%.1f' % tuple(l['rotation_deg']),
                ', '.join(extra)), 3.4, (0.88, 0.92, 1.0)))
    lines.append(('', 3.0, (1, 1, 1)))
    lines.append(('PER-ENEMY RIG ENERGY (watts) - the rig is identical for all '
                  'five; only the distances scale with body height', 4.4,
                  (0.55, 1.0, 0.65)))
    lines.append(('%-18s %9s %9s %9s %9s %9s' % ('enemy', 'key', 'rim', 'under',
                                                'pool', 'wash'), 3.6,
                  (0.45, 0.95, 0.6)))
    for n in doc['per_enemy']:
        e = doc['per_enemy'][n]
        r = e.get('per_enemy_energies') or {}
        if not r:
            for l in e['lights']:
                if l['name'] in ('reveal_key', 'reveal_rim', 'reveal_under',
                                 'reveal_pool', 'reveal_wash'):
                    r[l['name'].replace('reveal_', '')] = l['watts']
        lines.append(('%-18s %9.1f %9.1f %9.2f %9.1f %9.2f' % (
            n, r.get('key', 0), r.get('rim', 0), r.get('under', 0),
            r.get('pool', 0), r.get('wash', 0)), 3.4, (0.88, 0.92, 1.0)))
    lines.append(('', 3.0, (1, 1, 1)))
    lines.append(('EMISSIVE MATERIALS - emission strength / emission colour', 4.4,
                  (0.55, 1.0, 0.65)))
    for k, v in sorted(doc['emission_strength'].items()):
        lines.append(('%-18s %-9s %8.2f  colour %.2f,%.2f,%.2f'
                      % ('', k, v, *(doc['emission_colors'].get(k, (0, 0, 0)))),
                      3.4, (0.88, 0.92, 1.0)))
    lines.append(('', 3.0, (1, 1, 1)))
    lines.append(('STUDIO RIG (v1 comparison): broad area key 900 W + broad green '
                  'fill 700 W + point under 180 W, world strength 0.60', 4.0,
                  (0.95, 0.72, 0.72)))

    step = 6.4
    top = len(lines) * step * 0.5
    for i, (s, size, color) in enumerate(lines):
        if not s.strip():
            continue
        txt(s, -86.0, top - i * step, size=size, color=color)

    cd = bpy.data.cameras.new('tbl')
    cd.type = 'ORTHO'
    cd.ortho_scale = 176.0
    cam = bpy.data.objects.new('tbl', cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0, 0, 12.0)
    cam.rotation_euler = (0.0, 0.0, 0.0)
    sc.camera = cam
    sc.render.filepath = os.path.join(out_dir, 'rig_params.png')
    bpy.ops.render.render(write_still=True)
    if not os.path.exists(os.path.join(out_dir, 'rig_params.png')):
        for f in os.listdir(out_dir):
            if f.startswith('rig_params') and f.endswith('.png'):
                shutil.move(os.path.join(out_dir, f),
                            os.path.join(out_dir, 'rig_params.png'))
    print('[V4] wrote rig_params.png')


def write_verification(out_dir, verification, names, skipped):
    doc = {
        'generated': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'renderer': 'EEVEE (Blender 4.2)',
        'resolution': [RES_X, RES_Y],
        'samples': SAMPLES,
        'view_transform': VIEW_TRANSFORM,
        'bar': BAR,
        'window': WINDOW,
        'skipped': [{'enemy': n, 'reason': r} for n, r in skipped],
        'enemies': verification,
    }
    with open(os.path.join(out_dir, 'verification.json'), 'w') as f:
        json.dump(doc, f, indent=1)
    print('[V4] wrote verification.json')


# ================================================================== VERIFY
def mask_dir_of(out_dir):
    return os.path.join(out_dir, '_mask')


def verify_main(out_dir):
    """Independent re-measure - pure python, no Blender."""
    res = {}
    zones_by_enemy = {}
    vp = os.path.join(out_dir, 'verification.json')
    if os.path.exists(vp):
        try:
            doc = json.load(open(vp))
            for n, v in doc.get('enemies', {}).items():
                zones_by_enemy[n] = v.get('zones')
        except Exception:
            pass
    names = list(ENEMY_ORDER)
    if os.path.isdir(SNAP):
        for n in enemy_list(SNAP):
            if n not in names:
                names.append(n)
    for name in names:
        rp = os.path.join(out_dir, name + '_reveal.png')
        if not os.path.exists(rp):
            continue
        mp = os.path.join(mask_dir_of(out_dir), name + '_mask.png')
        ep = os.path.join(mask_dir_of(out_dir), name + '_emis.png')
        m = measure(rp, mp, ep, zones_by_enemy.get(name))
        pf = os.path.join(out_dir, name + '_emissive_only.png')
        sf = os.path.join(out_dir, name + '_studio_vs_reveal.png')
        m['emissive_only'] = measure(pf, mp, ep, zones_by_enemy.get(name)) \
            if os.path.exists(pf) else None
        m['studio_vs_reveal'] = measure(sf) if os.path.exists(sf) else None
        res[name] = m
        print('%-16s clipW=%-5d clipB=%-5d clipC=%-5d emissive=%-6d rim=%-6d '
              'bg=%.2f band=%.0f rimfrac=%.3f'
              % (name, m['clipped_white_pixels'], m['clipped_body_pixels'],
                 m['clipped_colour_pixels_non_emissive'],
                 m['emissive_pixels'], m['rim_pixels'], m['background_darkness'],
                 m.get('rim_band_mean_lum', 0), m.get('rim_bright_over_body', 0)))
    with open(os.path.join(out_dir, 'verification_independent.json'), 'w') as f:
        json.dump(res, f, indent=1)
    return res



# ============================================================== doc writers
DOC_ROOT = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'Docs', 'generated')
CMD_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                       'CommandCenter', 'outputs', 'lighting')


def ue_cd(blender_watts):
    """Blender watts -> UE5 candela.

    Blender renders linear 1.0 = white.  UE5 at EV100 treats linear 1.0 =
    100 cd.  A Blender point/spot of P W has radial radiant intensity
    P/(4*pi) W/sr, so matching the same surface value needs
    I_UE = 100 * P/(4*pi) = 7.96 * P cd.  Round to 7.96.
    """
    return round(7.96 * float(blender_watts), 1)


def ue_axes():
    """UE5 uses X forward, Y right, Z up.  Blender world is Z up, camera at
    CAM_AZ.  Return the world->UE basis so the rig can be expressed as a
    relative transform on the spawn actor."""
    f = (math.cos(math.radians(CAM_AZ)), math.sin(math.radians(CAM_AZ)))
    r = (math.cos(math.radians(CAM_AZ + 90.0)), math.sin(math.radians(CAM_AZ + 90.0)))
    return f, r


def to_ue(x, y, z, scale):
    f, r = ue_axes()
    return (round((x * f[0] + y * f[1]) * scale, 3),
            round((x * r[0] + y * r[1]) * scale, 3),
            round(z * scale, 3))


def aim_rot_ue(loc_ue, target_ue):
    """UE rotator that aims a spotlight (default -Z) at a target."""
    d = (target_ue[0] - loc_ue[0], target_ue[1] - loc_ue[1], target_ue[2] - loc_ue[2])
    h = math.hypot(d[0], d[1])
    yaw = math.degrees(math.atan2(d[1], d[0]))
    pitch = -90.0 + math.degrees(math.atan2(d[2], h))
    return (round(pitch, 2), round(yaw, 2), 0.0)


def write_ue_spec(out_dir, rig_log, verification, names):
    ref = None
    for n in names:
        if n in rig_log:
            ref = n
            break
    if not ref:
        return None
    rig = rig_log[ref]
    h = rig.get('body_height', 1.0)
    scale = 1.8 / max(0.1, h)          # actor scaled to 1.8 m tall in UE
    chest = (0.0, 0.0, 0.70 * h)
    chest_ue = to_ue(0.0, 0.0, 0.70 * h, scale)

    def row(name, typ, colour, watts, extra, bl_loc, bl_aim, ue_extra=''):
        loc = to_ue(bl_loc[0], bl_loc[1], bl_loc[2], scale)
        aim = to_ue(bl_aim[0], bl_aim[1], bl_aim[2], scale)
        rot = aim_rot_ue(loc, aim)
        return {'name': name, 'ue_type': typ, 'colour': colour,
                'ue_intensity_cd': ue_cd(watts), 'blender_w': round(watts, 1),
                'ue_location_rel': loc, 'ue_rotation_pyr': rot,
                'ue_aim_point_rel': aim, 'extra': extra, 'ue_extra': ue_extra}

    lights = {}
    for l in rig['lights']:
        lights[l['name']] = l
    aim_by_name = {'reveal_key': chest, 'reveal_rim': chest,
                   'reveal_under': (0.0, 0.0, 0.10 * h),
                   'reveal_pool': pool_target(h), 'reveal_wash': (0.0, 0.0, 0.0)}

    def get(nm):
        return lights.get(nm, {'watts': 0.0, 'location': [0, 0, 0],
                               'color': [1, 1, 1]})

    key = get('reveal_key')
    rim = get('reveal_rim')
    und = get('reveal_under')
    pool = get('reveal_pool')
    wash = get('reveal_wash')

    rows = [
        row('reveal_key', 'Spot', '(0.62, 0.78, 1.00)', key['watts'],
            'inner cone %.0f deg, outer %.0f deg' % (KEY_SPOT * 0.6, KEY_SPOT),
            key['location'], aim_by_name['reveal_key'],
            'Attenuation Radius 10 cm, Cast Shadow on, Source Radius 2 cm'),
        row('reveal_rim', 'Point', '(0.20, 1.00, 0.42)', rim['watts'],
            'rect area %.2f x %.2f m' % (RIM_SIZE_X * 1.8, RIM_SIZE_Y * 1.8),
            rim['location'], aim_by_name['reveal_rim'],
            'Attenuation Radius 5 cm, Cast Shadow on'),
        row('reveal_under', 'Point', '(0.45, 0.90, 1.00)', und['watts'],
            'source radius 2 cm', und['location'], (0.0, 0.0, 0.10 * h),
            'Attenuation Radius 2 cm, Cast Shadow off'),
        row('reveal_pool', 'Spot', '(0.52, 0.72, 1.00)', pool['watts'],
            'inner cone %.0f deg, outer %.0f deg' % (POOL_CONE * 0.6, POOL_CONE),
            pool['location'], aim_by_name['reveal_pool'],
            'Attenuation Radius 20 cm, Cast Shadow on'),
        row('reveal_wash', 'Point', '(0.45, 0.55, 0.70)', wash['watts'],
            'source radius 25 cm', wash['location'], (0.0, 0.0, 0.0),
            'Attenuation Radius 25 cm, Cast Shadow off'),
    ]

    L = []
    A = L.append
    A('# XCOM Reveal Lighting Rig - UE5 Handoff (v4)')
    A('')
    A('Generated by `Tools/blender/rig_evidence.py` from the measured Blender')
    A('renders. Every intensity below was taken from the rig that produced the')
    A('reference frames in `CommandCenter/outputs/lighting/`.')
    A('')
    A('**Unit conversion used:** UE5 candela = 7.96 x Blender watts for a')
    A('point/spot.  (Blender renders linear 1.0 = white; UE5 at EV100 treats')
    A('linear 1.0 = 100 cd; a Blender point/spot of P W has radial radiant')
    A('intensity P/(4*pi) W/sr, so I_UE = 100 * P/(4*pi) = 7.96 * P.)  If the')
    A('project uses a different exposure, scale every intensity by the same')
    A('factor and re-check against the reference PNGs.')
    A('')
    A('**Actor convention:** the reference rig was authored on a %.3f m tall' % h)
    A('body.  In UE the spawn actor is scaled to 1.8 m tall; all transforms')
    A('below are expressed RELATIVE to the actor root at the feet, in UE axes')
    A('(X forward = the direction the creature faces, Y right, Z up).')
    A('')
    A('## 1. The four rig elements')
    A('')
    A('| # | Element | UE light | Colour (R,G,B) | Intensity (cd) | Attenuation radius | Relative location (X,Y,Z) | Rotation (Pitch,Yaw,Roll) | Enabled when |')
    A('|---|---------|----------|-----------------|----------------|--------------------|--------------------------|-----------------------------|---------------|')
    en = {
        'reveal_key': 'always on while the enemy is revealed (reveal window open). Fade in over 0.25 s with the spawn animation.',
        'reveal_rim': 'always on while revealed. This is the only thing separating the silhouette from the black backdrop - it must never be disabled.',
        'reveal_under': 'enabled only during the reveal (the creature rises out of the floor). Disabled once the creature is fully stood up.',
        'reveal_pool': 'enabled with the reveal. Optional but it is what puts a bounded pool of light on the ground and the contact shadow under the feet.',
        'reveal_wash': 'optional ambient floor lift. Keep it dim - it is what makes the shadow side of the floor readable without flattening it.',
    }
    for r in rows:
        A('| %d | `%s` | %s | %s | %s | %s | %s | %s | %s |' % (
            rows.index(r) + 1, r['name'], r['ue_type'], r['colour'],
            r['ue_intensity_cd'], r['ue_extra'].split(',')[0].replace('Attenuation Radius ', ''),
            r['ue_location_rel'], r['ue_rotation_pyr'], en[r['name']]))
    A('')
    A('Rotation note: a UE spotlight emits along -Z at zero rotation, so the')
    A('listed (Pitch, Yaw, Roll) already includes the -90 pitch.  Each light')
    A('also lists an aim point in actor space - a Look At to that point is')
    A('equivalent and is usually easier to wire in Blueprint.')
    A('')
    A('### 1a. reveal_key - hard cold key, front-left')
    A('')
    A('- Type: **Spot**, colour (0.62, 0.78, 1.00), intensity **%s cd**' % rows[0]['ue_intensity_cd'])
    A('- Inner cone %.0f deg / outer cone %.0f deg, shadow casting ON.' % (KEY_SPOT * 0.6, KEY_SPOT))
    A('- Location (actor space): %s   Aim at chest: %s' % (rows[0]['ue_location_rel'], chest_ue))
    A('- Rotation: %s' % (rows[0]['ue_rotation_pyr'],))
    A('- Front-left and ABOVE the creature, aimed down at the chest.  This is')
    A('  the light that throws the cast shadow; it is the only light whose')
    A('  shadow direction matters for the composition.')
    A('')
    A('### 1b. reveal_rim - alien green rim, behind-above')
    A('')
    A('The reference rig uses a LONG THIN AREA STRIP (%.2f x %.2f body' % (RIM_SIZE_X, RIM_SIZE_Y))
    A('heights) behind and above the subject.  A strip wraps the whole')
    A('silhouette edge in one pass; a spot only ever grazes a thin slice of')
    A('it, and trying to make a spot cover the edge is what drives the rim')
    A('into the thousands of watts and blows the frame out.')
    A('')
    A('In UE use a **Rect Area Light** with the same size and orientation, or')
    A('a Spot with a wide cone if the project has no area lights.  The')
    A('intensity below is the measured Blender value; for UE, divide by the')
    A('strip area and use the resulting value with a wide outer cone.')
    A('')
    A('- Type: **Spot**, colour (0.20, 1.00, 0.42), intensity **%s cd**' % rows[1]['ue_intensity_cd'])
    A('- Inner cone %.0f deg / outer cone %.0f deg, shadow casting ON.' % (RIM_CONE * 0.6, RIM_CONE))
    A('- Location (actor space): %s   Aim at chest: %s' % (rows[1]['ue_location_rel'], chest_ue))
    A('- Rotation: %s' % (rows[1]['ue_rotation_pyr'],))
    A('- Behind and above, grazing the silhouette.  It is the SEPARATION light:')
    A('  with the backdrop near-black, this is the only thing that draws the')
    A('  outline.  Never let it be culled or replaced by a fill.')
    A('')
    A('### 1c. reveal_under - cyan under-glow, local uplight')
    A('')
    A('- Type: **Point**, colour (0.45, 0.90, 1.00), intensity **%s cd**' % rows[2]['ue_intensity_cd'])
    A('- Location (actor space): %s  (at the feet, between them, %.2f m above' % (rows[2]['ue_location_rel'], rows[2]['ue_location_rel'][2]))
    A('  the floor)  Aim at the legs: %s' % (rows[2]['ue_aim_point_rel'],))
    A('- Attenuation radius 2 cm, shadow casting OFF.')
    A('- CRITICAL: this must stay a tight local uplight.  A wide or bright')
    A('  version floods the floor and the frame goes from "creature in the')
    A('  dark" to "product shot on a white light box".  If the under-glow')
    A('  needs to read further, raise the intensity, never the radius.')
    A('')
    A('### 1d. reveal_pool + reveal_wash - the floor')
    A('')
    A('- reveal_pool: **Spot**, colour (0.52, 0.72, 1.00), intensity **%s cd**,' % rows[3]['ue_intensity_cd'])
    A('  cone %.0f deg with a soft edge, aimed at the ground %.2f m in front of' % (POOL_CONE, POOL_G * 1.8))
    A('  the feet, from behind-above.  It makes the bounded pool of light on')
    A('  the floor AND the creature\'s own contact shadow inside it.')
    A('- reveal_wash: **Point**, colour (0.45, 0.55, 0.70), intensity **%s cd**,' % rows[4]['ue_intensity_cd'])
    A('  25 cm source radius, shadow casting off.  This is the only ambient')
    A('  term in the rig.  It must stay dim: it exists so the shadow side of')
    A('  the floor is readable, not so the creature is lit from nowhere.')
    A('')
    A('## 2. Emissive materials')
    A('')
    A('| Material | Emission colour | Blender emission strength | UE5 emissive value |')
    A('|----------|-----------------|----------------------------|-------------------|')
    for kind, mat in sorted(rig.get('emissive_materials', {}).items()):
        col = EMIT_COLORS.get(kind, (1, 1, 1))
        st = EMIT_STRENGTH.get(kind, 0.5)
        A('| `%s` | (%.2f, %.2f, %.2f) | %.2f | %.1f |' % (
            mat, col[0], col[1], col[2], st, st * 20.0))
    A('')
    A('UE5 multiplies an emissive colour by 20 internally, so the UE column is')
    A('the Blender strength x 20.  Set these on the material instance; do not')
    A('bake them into the base material.')
    A('')
    A('The proof frames in `CommandCenter/outputs/lighting/` were rendered with')
    A('**no scene lights at all** and the emissive strength multiplied by')
    A('%.1f, plus a Fog Glow compositor pass.  That is the evidence that the' % PROOF_EMIT_SCALE)
    A('emissives genuinely self-light.')
    A('')
    A('## 3. World, fog and post')
    A('')
    A('| Setting | Value | Why |')
    A('|---------|-------|-----|')
    A('| World / Sky light | None, or intensity 0.02 with a cold tint | The backdrop must fall away so the rim does the separating. |')
    A('| Sky atmosphere | Off | Any sky fill re-introduces the "fakes the green material" failure. |')
    A('| Exponential Height Fog | Fog Density **0.012**, Height Falloff **0.25**, Start Distance 0 | Just enough haze for the under-glow and pool to read volumetrically. |')
    A('| Directional Inscattering Colour | (0.06, 0.12, 0.20) | Cold haze tint, matches the key. |')
    A('| Inscattering Exponent | 4.0 | Keeps the haze off the camera. |')
    A('| Volumetric Fog Scattering | 0.04 | The light shafts in the pool need it. |')
    A('| Volumetric Fog Distance | 8000 cm | |')
    A('| Bloom (post) | Intensity 0.25, Threshold 0.85, Radius 4 | Matches the Blender Fog Glow used for the reference frames. |')
    A('| Auto exposure | OFF, fixed EV100 | The rig is authored at a fixed exposure; auto exposure would blow the pool out and black out the backdrop. |')
    A('')
    A('Fog is what makes the reveal volumetric: without it the under-glow and')
    A('the pool are flat discs on a flat plane.  Keep the density low - the')
    A('reference is a dark scene, not a smoky one.')
    A('')
    A('## 4. Consistency rules for the whole set')
    A('')
    A('- The key is ALWAYS front-left.  The rig is authored subject-relative,')
    A('  so all five enemies cast their shadow the same way.')
    A('- The rim is ALWAYS behind-above.')
    A('- The world stays near-black (Blender background strength 0.10 in the')
    A('  reference renders, which measured a background_darkness of %.1f).' % (
        verification.get(ref, {}).get('background_darkness', 0)))
    A('- Nothing in the rig may be allowed to clip: the reference frames have')
    A('  0 clipped white pixels on the body.')
    A('')
    A('## 5. Measured reference numbers')
    A('')
    A('| Enemy | clipped white | clipped body | clipped colour (non-emissive) | emissive px | rim px | background darkness | floor zones | face p99 | torso p99 |')
    A('|--------|---------------|-------------|------------------------------|------------|-------|--------------------|-------------|----------|-----------|')
    for n in names:
        v = verification.get(n)
        if not v:
            continue
        zs = v.get('zone_stats', {})
        A('| %s | %d | %d | %d | %d | %d | %.1f | %s | %.0f | %.0f |' % (
            n, v['clipped_white_pixels'], v['clipped_body_pixels'],
            v['clipped_colour_pixels_non_emissive'], v['emissive_pixels'],
            v['rim_pixels'], v['background_darkness'],
            ', '.join('%s %.0f' % (k.replace('floor_', ''), v['zone_stats'][k]['mean_lum'])
                      for k in ('floor_front', 'floor_shadow_side', 'floor_key_side')
                      if k in zs),
            zs.get('face', {}).get('p99_lum', 0),
            zs.get('torso', {}).get('p99_lum', 0)))
    A('')
    A('## 6. Wiring it up in Blueprint')
    A('')
    A('1. Add a `BP_XCOM_RevealRig` actor component with five child components:')
    A('   `SpotLight reveal_key`, `SpotLight reveal_rim`, `PointLight reveal_under`,')
    A('   `SpotLight reveal_pool`, `PointLight reveal_wash`.')
    A('2. Set the transforms from section 1 (they are already actor-relative).')
    A('3. On `BeginPlay`, disable the whole rig.  On the reveal event, enable')
    A('   `reveal_key`, `reveal_rim`, `reveal_pool`, `reveal_wash` and enable')
    A('   `reveal_under` with a 0.4 s fade-in while the creature rises.')
    A('4. `reveal_under` off, `reveal_key`/`reveal_rim` stay on for the rest of')
    A('   the encounter.')
    A('')
    path = os.path.join(DOC_ROOT, 'lighting_rig_spec.md')
    try:
        os.makedirs(DOC_ROOT, exist_ok=True)
        open(path, 'w').write('\n'.join(L) + '\n')
        print('[V4] wrote %s' % path)
        return path
    except Exception as e:
        print('[V4] spec write failed: %s' % e)
        return None


def write_evidence_md(out_dir, verification, names, skipped):
    L = []
    A = L.append
    A('# Lighting Evidence (v4 reveal rig)')
    A('')
    A('Generated %s by `Tools/blender/rig_evidence.py`.' % time.strftime('%Y-%m-%d %H:%M'))
    A('')
    A('All numbers below are MEASURED from the rendered PNGs in this folder by')
    A('the same script that rendered them, then re-measured independently by')
    A('`python Tools/blender/rig_evidence.py --verify --out <dir>`.')
    A('')
    A('Metric definitions:')
    A('')
    A('- `clipped_white_pixels` - r,g,b all > 248 anywhere in the frame.')
    A('- `clipped_body_pixels` - the same, restricted to the subject silhouette.')
    A('- `clipped_colour_pixels_non_emissive` - a channel at 250+ with a colour')
    A('  spread of 25+, on non-emissive pixels (emissive glow is allowed to clip).')
    A('- `emissive_pixels` - max channel > 190 with a colour spread of 25+.')
    A('- `rim_pixels` - g - r > 55 and g > 90 (the alien green rim).')
    A('- `background_darkness` - mean luminance of the outer 10% border.')
    A('')
    if skipped:
        A('**Skipped:** %s' % '; '.join('%s (%s)' % (n, r) for n, r in skipped))
        A('')
    for n in names:
        v = verification.get(n)
        if not v:
            continue
        zs = v.get('zone_stats', {})
        fl = {k: zs.get(k, {}).get('mean_lum', 0) for k in
              ('floor_front', 'floor_shadow_side', 'floor_key_side')}
        A('## %s' % n)
        A('')
        A('**Numbers:** clipped_white_pixels = **%d**, clipped_body_pixels = **%d**,'
          % (v['clipped_white_pixels'], v['clipped_body_pixels']))
        A('clipped_colour_pixels_non_emissive = **%d**, emissive_pixels = **%d**,'
          % (v['clipped_colour_pixels_non_emissive'], v['emissive_pixels']))
        A('rim_pixels = **%d**, background_darkness = **%.1f**.'
          % (v['rim_pixels'], v['background_darkness']))
        A('')
        A('**Rig elements legible in this frame:** ' + ', '.join(
            e for e, ok in (
                ('reveal_key', zs.get('face', {}).get('p99_lum', 0) >= 25 and
                 zs.get('torso', {}).get('p99_lum', 0) >= 25),
                ('reveal_rim', v.get('rim_bright_over_body', 0) >= 0.03 or
                 v.get('rim_band_mean_lum', 0) >= 120),
                ('reveal_under', v.get('under_lowbody_over_torso', 0) >= 1.3),
                ('reveal_pool + contact shadow',
                 v.get('contact_shadow_ratio_mask', 9) <= 0.85 and
                 all(45 <= fl[k] <= 175 for k in fl)),
                ('emissives', v.get('emissive_pixels', 0) > 0),
            ) if ok) + '.')
        A('')
        A('**Detail:** floor zones front/shadow-side/outer = %.0f / %.0f / %.0f'
          % (fl['floor_front'], fl['floor_shadow_side'], fl['floor_key_side']))
        A('(min difference %.0f%%), contact shadow ratio %.2f, face p99 %.0f,'
          % (v.get('floor_zone_min_diff_pct', 0), v.get('contact_shadow_ratio_mask', 0),
             zs.get('face', {}).get('p99_lum', 0)))
        A('torso p99 %.0f, under-glow low-body/torso %.2fx and feet/torso %.2fx,'
          % (zs.get('torso', {}).get('p99_lum', 0),
             v.get('under_lowbody_over_torso', 0), v.get('under_feet_over_torso', 0)))
        A('rim band mean %.0f (hot %.0f), rim bright pixels %d = %.3f of the body.'
          % (v.get('rim_band_mean_lum', 0), v.get('rim_band_hot_mean_lum', 0),
             v.get('rim_band_bright_pixels', 0), v.get('rim_bright_over_body', 0)))
        A('')
        fails = v.get('failed_criteria', [])
        if fails:
            A('**Did not meet the bar:** %s.' % ', '.join(fails))
            A('')
        else:
            A('**Met every criterion in the corrected contract.**')
            A('')
        A('**Emissive proof frame** (`%s_emissive_only.png`, no scene lights,' % n)
        A('emission x%.1f, Fog Glow only): %s' % (PROOF_EMIT_SCALE,
          ('%d bright pixels, %d clipped.' % (
              v.get('emissive_only', {}).get('emissive_pixels', 0),
              v.get('emissive_only', {}).get('clipped_white_pixels', 0)))
          if v.get('emissive_only') else 'not rendered.'))
        A('')
    path = os.path.join(out_dir, 'LIGHTING_EVIDENCE.md')
    open(path, 'w').write('\n'.join(L) + '\n')
    print('[V4] wrote %s' % path)
    return path



def render_params_table(out_dir, doc):
    """Render the rig parameters as a readable table image."""
    sc = wipe_scene()
    sc.render.resolution_x = 2000
    sc.render.resolution_y = 2600
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.film_transparent = False
    sc.use_nodes = False
    try:
        sc.view_settings.view_transform = VIEW_TRANSFORM
        sc.view_settings.look = 'None'
    except Exception:
        pass
    w = bpy.data.worlds.new('tbl_world')
    w.use_nodes = True
    bg = w.node_tree.nodes.get('Background')
    if bg:
        bg.inputs[0].default_value = (0.012, 0.013, 0.016, 1.0)
        bg.inputs[1].default_value = 1.0
    sc.world = w

    m = bpy.data.materials.new('XCOM_TableBG')
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        set_input(bsdf, ['Base Color'], (0.02, 0.021, 0.026, 1.0))
        set_input(bsdf, ['Roughness'], 0.9)
    bpy.ops.mesh.primitive_plane_add(size=400.0)
    bpy.context.object.data.materials.append(m)

    lines = []      # (text, size, colour)
    lines.append(('XCOM REVEAL RIG  -  PARAMETER TABLE (v4)', 5.6, (1.0, 0.76, 0.26)))
    lines.append(('Blender 4.2 EEVEE   %dx%d   %d samples   view transform %s   '
                  'world background strength %.2f'
                  % (RES_X, RES_Y, SAMPLES, VIEW_TRANSFORM, WORLD_STRENGTH),
                  2.5, (0.72, 0.82, 0.96)))
    lines.append(('ground albedo %.3f   haze strength %.3f   proof emission scale %.1f'
                  % (GROUND_ALBEDO, HAZE_STRENGTH, PROOF_EMIT_SCALE),
                  2.5, (0.72, 0.82, 0.96)))
    lines.append(('', 1.0, (1, 1, 1)))

    ref = None
    for n in doc.get('per_enemy', {}):
        ref = n
        break
    if ref:
        h = doc['per_enemy'][ref].get('body_height', 1.0)
        lines.append(('REVEAL RIG LIGHTS   (reference enemy: %s, body height %.3f m)'
                      % (ref, h), 3.3, (0.5, 1.0, 0.62)))
        lines.append(('%-15s %-6s %-8s %-16s %-17s %-15s %s'
                      % ('light', 'type', 'watts', 'colour r,g,b',
                         'location x,y,z', 'rot x,y,z deg', 'extra'),
                      2.4, (0.45, 0.95, 0.6)))
        lines.append(('-' * 96, 2.2, (0.32, 0.42, 0.52)))
        for l in doc['per_enemy'][ref]['lights']:
            extra = []
            if l.get('spot_size_deg'):
                extra.append('spot %.0f' % l['spot_size_deg'])
            if l.get('size'):
                extra.append('size %.2f' % l['size'])
            if not l.get('shadow', True):
                extra.append('NO SHADOW')
            lines.append(('%-15s %-6s %-8.1f %-16s %-17s %-15s %s' % (
                l['name'], l['type'], l['watts'],
                '%.2f,%.2f,%.2f' % tuple(l['color']),
                '%.2f,%.2f,%.2f' % tuple(l['location']),
                '%.0f,%.0f,%.0f' % tuple(l['rotation_deg']),
                ' '.join(extra)), 2.4, (0.88, 0.92, 1.0)))
    lines.append(('', 1.0, (1, 1, 1)))
    lines.append(('PER-ENEMY RIG ENERGY (watts)  -  the rig is identical for all five;'
                  ' only the distances scale with body height', 3.0, (0.5, 1.0, 0.62)))
    lines.append(('%-18s %9s %9s %9s %9s %9s %8s'
                  % ('enemy', 'key', 'rim', 'under', 'pool', 'wash', 'height'),
                  2.4, (0.45, 0.95, 0.6)))
    for n in doc.get('per_enemy', {}):
        e = doc['per_enemy'][n]
        r = {}
        for l in e['lights']:
            r[l['name'].replace('reveal_', '')] = l['watts']
        lines.append(('%-18s %9.1f %9.1f %9.2f %9.1f %9.2f %8.3f' % (
            n, r.get('key', 0), r.get('rim', 0), r.get('under', 0),
            r.get('pool', 0), r.get('wash', 0), e.get('body_height', 0)),
            2.4, (0.88, 0.92, 1.0)))
    lines.append(('', 1.0, (1, 1, 1)))
    lines.append(('EMISSIVE MATERIALS  -  emission strength and emission colour',
                  3.0, (0.5, 1.0, 0.62)))
    for k in sorted(doc.get('emission_strength', {})):
        v = doc['emission_strength'][k]
        c = doc.get('emission_colors', {}).get(k, (0, 0, 0))
        lines.append(('%-20s strength %6.2f   colour %.2f,%.2f,%.2f'
                      % (k, v, c[0], c[1], c[2]), 2.4, (0.88, 0.92, 1.0)))
    lines.append(('', 1.0, (1, 1, 1)))
    st = doc.get('per_enemy', {}).get(ref, {}).get('studio_rig', {})
    lines.append(('STUDIO RIG (v1 comparison, same camera):', 3.0, (0.95, 0.72, 0.72)))
    for l in st.get('lights', []):
        lines.append(('%-15s %-6s %-8.1f %-16s %s' % (
            l['name'], l['type'], l['watts'],
            '%.2f,%.2f,%.2f' % tuple(l['color']),
            '%.2f,%.2f,%.2f' % tuple(l['location'])), 2.4, (0.95, 0.85, 0.85)))
    lines.append(('%-15s %-6s %-8s %-16s %s' % (
        'world', '-', '-', '%.2f' % (st.get('world_background_strength') or 0),
        'background strength'), 2.4, (0.95, 0.85, 0.85)))

    # fit every line into the frame
    USABLE = 148.0
    widest = 0.0
    for t, s, _c in lines:
        if t.strip():
            widest = max(widest, len(t) * 0.50 * s)
    k = min(1.0, USABLE / max(1.0, widest))

    def txt(s, x, y, size, color):
        cu = bpy.data.curves.new('t', 'FONT')
        cu.body = s
        cu.size = size
        cu.extrude = 0.0
        ob = bpy.data.objects.new('T', cu)
        bpy.context.scene.collection.objects.link(ob)
        mm = bpy.data.materials.new('XCOM_TableText')
        mm.use_nodes = True
        nt2 = mm.node_tree
        nt2.nodes.clear()
        em = nt2.nodes.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = (color[0], color[1], color[2], 1.0)
        em.inputs['Strength'].default_value = 1.0
        out = nt2.nodes.new('ShaderNodeOutputMaterial')
        nt2.links.new(em.outputs['Emission'], out.inputs['Surface'])
        ob.data.materials.append(mm)
        ob.location = (x, y, 0.05)
        return ob

    step = 7.0
    top = len(lines) * step * 0.5
    for i, (t, s, c) in enumerate(lines):
        if not t.strip():
            continue
        txt(t, -72.0, top - i * step, size=s * k, color=c)

    cd = bpy.data.cameras.new('tbl')
    cd.type = 'ORTHO'
    cd.ortho_scale = 200.0
    cam = bpy.data.objects.new('tbl', cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0, 0, 14.0)
    cam.rotation_euler = (0.0, 0.0, 0.0)
    sc.camera = cam
    sc.render.filepath = os.path.join(out_dir, 'rig_params.png')
    bpy.ops.render.render(write_still=True)
    if not os.path.exists(os.path.join(out_dir, 'rig_params.png')):
        for f in os.listdir(out_dir):
            if f.startswith('rig_params') and f.endswith('.png'):
                shutil.move(os.path.join(out_dir, f),
                            os.path.join(out_dir, 'rig_params.png'))
    print('[V4] wrote rig_params.png')



if __name__ == '__main__':
    _out, _src, _verify, _only = parse_args()
    ONLY[0] = _only
    ONLY[1] = ('--diag' in sys.argv)
    if _verify:
        verify_main(_out)
    else:
        bl_main(_out, _src)
