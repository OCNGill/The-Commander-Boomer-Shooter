"""
PROCEDURAL BACKGROUND TEXTURE SET for "The Commander" (Plymouth MA harbour horror FPS).

Six PBR material sets built entirely in numpy and written into bpy.data.images
buffers (no image painting operators, no external assets). Fixed seed ->
byte-identical reruns.

Per material:
  <name>.png            2048x2048 diffuse (sRGB)
  <name>_normal.png     2048x2048 tangent normal from the same height field
  <name>_rough.png      2048x2048 roughness (Non-Color, grayscale)
  <name>_contact.png    2048x2048 OFFSET CONTACT SHEET (2x2 tiling, 50% offset)
  <name>_crop1..3.png   1024x1024 native 1:1 crops (no downscaling) from 3 regions
Plus:
  T_Set_TrimSheet.png   4096x4096 trim sheet (diffuse / normal / rough / contact)
  textures_manifest.json  every file with its REAL width x height and byte size

Tiling: every pattern is authored periodic. Noise lattice frequencies are powers
of two that divide 2048, the hash field is periodic, the Worley cell grid wraps,
and the brick / plank / seam periods divide 2048, so the offset contact sheets
carry no seam. A wrap-edge-vs-interior continuity metric is printed per
material as proof.

Palette: cold blue-grey darks, wet concrete, sage / forest green, mint, and a
single oxblood carrier (the brick), so the harbour reads as one world with the
XCOM bioluminescence.

Usage (headless):
    blender -b -noaudio -P Tools/blender/make_textures.py -- --out <dir> [--copy-to <dir>]
"""

import bpy
import gc
import json
import os
import shutil
import sys

import numpy as np

# --------------------------------------------------------------------------- args
argv = sys.argv
tail = argv[argv.index('--') + 1:] if '--' in argv else argv
OUT = None
COPY_TO = None
for i, a in enumerate(tail):
    if a == '--out' and i + 1 < len(tail):
        OUT = tail[i + 1]
    if a == '--copy-to' and i + 1 < len(tail):
        COPY_TO = tail[i + 1]
if OUT is None:
    OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out_textures')
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)

# Straight (non-tonemapped) sRGB output so saved bytes carry the authored
# values. The probe below verifies this rather than trusting it.
try:
    scene = bpy.context.scene
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.display_settings.display_device = 'sRGB'
except Exception as exc:  # pragma: no cover
    print('[TEXTURE] colour management note: %s' % exc)

SIZE = 2048
CROP = 1024
THUMB = 512
SEED = 19941102

# ------------------------------------------------------------------------ palette
COLD_DARK = (0.105, 0.135, 0.160)     # cold blue-grey shadow
CONCRETE = (0.400, 0.432, 0.462)      # wet grey-blue concrete
MINT = (0.400, 0.610, 0.520)          # mint moss
SAGE = (0.470, 0.545, 0.445)          # sage weathering
FOREST = (0.135, 0.255, 0.185)        # forest green algae
OXBLOOD = (0.330, 0.098, 0.105)        # oxblood brick
RUST_OCHRE = (0.395, 0.235, 0.115)     # ochre rust
BONE = (0.560, 0.545, 0.505)          # bleached bone / salt

PALETTE_HEX = {
    'cold_dark': '#1B2229',
    'concrete': '#666E76',
    'mint': '#669C85',
    'sage': '#788B71',
    'forest': '#22412F',
    'oxblood': '#54191B',
    'rust_ochre': '#653C1D',
    'bone': '#8F8B81',
}


def hexof(rgb):
    return '#%02X%02X%02X' % tuple(int(round(c * 255)) for c in rgb)


# =========================================================================== math
def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def smoothstep(e0, e1, x):
    """Smooth interpolation between edges e0 and e1.

    Works for reversed edges (e0 > e1) as well: the denominator keeps its
    sign, so the ramp descends. A clamped positive denominator would turn
    every reversed call into a hard step, which is what makes procedural
    noise read as razor-thin "contour map" lines instead of soft cracks.
    """
    d = e1 - e0
    if abs(d) < 1e-9:
        return (x >= e0).astype(np.float32)
    t = clamp01((x - e0) / d)
    return t * t * (3.0 - 2.0 * t)


def lattice(h, w, fy, fx, seed):
    """Tileable bilinear value noise on a fy x fx lattice (smoothstep interp).

    fy/fx must divide h/w for seamlessness; all call sites use powers of two.
    fy << fx -> vertical streaks, fy >> fx -> horizontal streaks.
    """
    rng = np.random.RandomState(int(seed) & 0x7FFFFFFF)
    fy = max(1, fy)
    fx = max(1, fx)
    g = rng.rand(fy, fx).astype(np.float32)
    ys = np.arange(h, dtype=np.float32) * (fy / float(h))
    xs = np.arange(w, dtype=np.float32) * (fx / float(w))
    y0 = np.floor(ys).astype(np.int64) % fy
    x0 = np.floor(xs).astype(np.int64) % fx
    fyv = ys - np.floor(ys)
    fxv = xs - np.floor(xs)
    fyv = (fyv * fyv * (3.0 - 2.0 * fyv)).astype(np.float32)
    fxv = (fxv * fxv * (3.0 - 2.0 * fxv)).astype(np.float32)
    y1 = (y0 + 1) % fy
    x1 = (x0 + 1) % fx
    a = g[np.ix_(y0, x0)]
    b = g[np.ix_(y0, x1)]
    c = g[np.ix_(y1, x0)]
    d = g[np.ix_(y1, x1)]
    top = a * (1.0 - fxv)[None, :] + b * fxv[None, :]
    bot = c * (1.0 - fxv)[None, :] + d * fxv[None, :]
    return top * (1.0 - fyv)[:, None] + bot * fyv[:, None]


def fbm(h, w, seed, octaves=5, fy=4, fx=4, gain=0.5):
    """Fractal value noise. Octave frequencies double, so they stay tileable."""
    total = np.zeros((h, w), np.float32)
    amp = 1.0
    norm = 0.0
    cy, cx = fy, fx
    for o in range(octaves):
        total += amp * lattice(h, w, cy, cx, seed + o * 7919)
        norm += amp
        amp *= gain
        cy *= 2
        cx *= 2
    return total / norm


def hash01(h, w, seed):
    """Deterministic white noise from an integer hash (per pixel, no structure)."""
    y = np.arange(h, dtype=np.uint64)[:, None]
    x = np.arange(w, dtype=np.uint64)[None, :]
    n = (x * np.uint64(374761393) + y * np.uint64(668265263) +
         np.uint64(seed & 0xFFFFFFFF) * np.uint64(2654435761)) & np.uint64(0xFFFFFFFF)
    n = ((n ^ (n >> np.uint64(13))) * np.uint64(1274126177)) & np.uint64(0xFFFFFFFF)
    n = n ^ (n >> np.uint64(16))
    return (n & np.uint64(0xFFFFFF)).astype(np.float32) / np.float32(0xFFFFFF)


def hash_int(ids, seed):
    """Deterministic 0..1 scalar per integer id (per-brick / per-plank tone)."""
    i = (ids.astype(np.int64) + np.int64(seed)) & np.int64(0x7FFFFFFF)
    i = (i * np.int64(1103515245) + np.int64(12345)) & np.int64(0x7FFFFFFF)
    i = (i ^ (i >> np.int64(13))) & np.int64(0x7FFFFFFF)
    i = (i * np.int64(2654435761) + np.int64(12345)) & np.int64(0x7FFFFFFF)
    i = (i ^ (i >> np.int64(11))) & np.int64(0x7FFFFFFF)
    return (i % 100003).astype(np.float32) / 100003.0


def worley(h, w, cell, seed):
    """Periodic jittered-grid Worley. Returns (nearest_dist, cell_id).

    The jitter grid is indexed modulo, so the point set is exactly h/w periodic
    and the field wraps seamlessly across the texture edges.
    """
    ny = h // cell
    nx = w // cell
    rng = np.random.RandomState(int(seed) & 0x7FFFFFFF)
    jy = rng.rand(ny, nx).astype(np.float32)
    jx = rng.rand(ny, nx).astype(np.float32)
    Y = np.arange(h, dtype=np.float32)[:, None]
    X = np.arange(w, dtype=np.float32)[None, :]
    cy = (Y / cell).astype(np.int64)
    cx = (X / cell).astype(np.int64)
    best = np.full((h, w), 1e9, np.float32)
    bestid = np.zeros((h, w), np.int64)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            sy = cy + dy
            sx = cx + dx
            iy = sy % ny
            ix = sx % nx
            py = sy * cell + jy[iy, ix] * cell
            px = sx * cell + jx[iy, ix] * cell
            d = (Y - py) ** 2 + (X - px) ** 2
            m = d < best
            best = np.where(m, d, best)
            bestid = np.where(m, iy * nx + ix, bestid)
    return np.sqrt(best), bestid


def grime(h, w, seed, strength=0.35, fy=4, fx=4):
    """Large scale soiling field, 0 = clean, 1 = filthy (tileable)."""
    return clamp01(smoothstep(0.35, 0.85, fbm(h, w, seed, octaves=4, fy=fy, fx=fx)) * strength)


def tint(rgb, amount, color):
    """Blend rgb toward `color` by amount (amount is a HxW float array).

    `color` may be a 3-tuple (flat colour) or a full HxWx3 image (per-pixel
    tint, e.g. per-stone aggregate colour).
    """
    c = np.asarray(color, np.float32)
    if c.ndim == 1:
        c = c.reshape(1, 1, 3)
    return rgb * (1.0 - amount[..., None]) + c * amount[..., None]


# ==================================================================== PNG helpers
def png_header(path):
    """(width, height, bitdepth, colourtype) read from the file on disk."""
    import struct
    with open(path, 'rb') as f:
        head = f.read(33)
    if head[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a PNG: %s' % path)
    w, h, depth, ctype = struct.unpack('>IIBB', head[16:26])
    return w, h, depth, ctype


def decode_png(path):
    """Standalone PNG decoder (8-bit, non-interlaced) -> HxWx3 uint8.

    Pure stdlib, independent of Blender: this is the proof of what is on disk.
    """
    import struct
    import zlib

    data = open(path, 'rb').read()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a PNG: %s' % path)
    pos = 8
    idat = b''
    w = h = depth = ctype = None
    while pos < len(data):
        (length,) = struct.unpack('>I', data[pos:pos + 4])
        ctag = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctag == b'IHDR':
            w, h, depth, ctype, _c, _f, inter = struct.unpack('>IIBBBBB', chunk)
            if depth != 8 or inter != 0:
                raise ValueError('unsupported PNG depth=%s interlace=%s' % (depth, inter))
        elif ctag == b'IDAT':
            idat += chunk
        elif ctag == b'IEND':
            break
    if ctype not in (2, 6):
        raise ValueError('unsupported PNG colour type %s in %s' % (ctype, path))
    nch = 3 if ctype == 2 else 4
    raw = zlib.decompress(idat)
    stride = w * nch
    rows = np.frombuffer(raw, dtype=np.uint8).reshape(h, stride + 1)
    filters = rows[:, 0]
    lines = rows[:, 1:].astype(np.int32)
    out = np.zeros((h, stride), np.int32)
    prev = np.zeros(stride, np.int32)
    for y in range(h):
        ft = int(filters[y])
        line = lines[y]
        if ft == 0:
            cur = line.copy()
        elif ft == 1:
            # Sub: recon[i] = filt[i] + recon[i - bpp]. The predictor walks back
            # one PIXEL, so the cumulative sum is per colour channel, not across
            # channels.
            cur = np.zeros(stride, np.int32)
            for c in range(nch):
                cur[c::nch] = np.cumsum(line[c::nch]) % 256
        elif ft == 2:
            cur = (line + prev) % 256
        else:
            cur = np.zeros(stride, np.int32)
            for x in range(stride):
                a = cur[x - nch] if x >= nch else 0
                b = prev[x]
                if ft == 3:
                    cur[x] = (line[x] + ((a + b) >> 1)) % 256
                else:
                    c = prev[x - nch] if x >= nch else 0
                    pp = a + b - c
                    pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                    pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                    cur[x] = (line[x] + pr) % 256
        out[y] = cur
        prev = cur
    return (out % 256).astype(np.uint8).reshape(h, w, nch)[:, :, :3]


def readback_raw(path):
    """Load a PNG through Blender and return the raw stored bytes (Non-Color).

    Non-Color means no sRGB->linear conversion, so this is byte-exact.
    """
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = 'Non-Color'
    img.reload()  # re-read the file under Non-Color so no transform is applied
    w, h = img.size
    buf = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(buf)
    # Blender stores image rows bottom-up, PNG rows are top-down. The
    # selftest_bytes() proof (blender readback max diff == 0) only holds with
    # this flip, so it is required, not cosmetic.
    px = buf.reshape(h, w, 4)[::-1, :, :3]
    bpy.data.images.remove(img)
    return (np.clip(px, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def write_png_filter0(path, arr_u8):
    """Write a PNG with every row using filter type 0.

    Used by the self test: filter 0 is trivially decodable, so comparing our
    decoder against Blender's reader on this file proves BOTH are byte-exact
    and free of any colour transform.
    """
    import struct
    import zlib
    h, w = arr_u8.shape[0], arr_u8.shape[1]
    raw = b''.join(b'\x00' + arr_u8[y].tobytes() for y in range(h))

    def chunk(tag, payload):
        return (struct.pack('>I', len(payload)) + tag + payload +
                struct.pack('>I', zlib.crc32(tag + payload) & 0xFFFFFFFF))

    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    blob = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) +
            chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(blob)
    return path


def selftest_bytes(tmp_dir):
    """Prove the decode path is byte-exact.

    1. write a known RGB image as a filter-0 PNG
    2. decode it with our own stdlib decoder  -> must equal the source exactly
    3. read it back through Blender            -> must equal the source exactly
    A non-zero difference in step 2 or 3 means the pipeline is lying.
    """
    rng = np.random.RandomState(7)
    src = rng.randint(0, 256, size=(64, 64, 3)).astype(np.uint8)
    src[0, 0] = (0, 0, 0)
    src[1, 1] = (255, 255, 255)
    src[2, 2] = (128, 64, 32)
    path = os.path.join(tmp_dir, '_selftest.png')
    write_png_filter0(path, src)
    dec = decode_png(path)
    d1 = int(np.abs(dec.astype(np.int32) - src.astype(np.int32)).max())
    rb = readback_raw(path)
    d2 = int(np.abs(rb.astype(np.int32) - src.astype(np.int32)).max())
    os.remove(path)
    print('[TEXTURE] selftest: stdlib decoder max diff = %d, blender readback max diff = %d '
          '(both must be 0)' % (d1, d2))
    return d1, d2


def luma_stats(px_u8):
    lum = px_u8.astype(np.float32) @ np.asarray([0.2126, 0.7152, 0.0722], np.float32)
    return float(lum.mean()), float(lum.std())


def seam_metrics(px_u8):
    """Seam proof.

    For a truly periodic texture, the difference across the wrap edge
    (last column -> first column) must be statistically the same as the
    difference between any two interior adjacent columns. ratio ~ 1.0 = seamless.
    """
    lum = px_u8.astype(np.float32) @ np.asarray([0.2126, 0.7152, 0.0722], np.float32)
    wrap_x = float(np.abs(lum[:, -1] - lum[:, 0]).mean())
    inner_x = float(np.abs(np.diff(lum, axis=1)).mean())
    wrap_y = float(np.abs(lum[-1, :] - lum[0, :]).mean())
    inner_y = float(np.abs(np.diff(lum, axis=0)).mean())
    return (wrap_x / max(inner_x, 1e-6), wrap_y / max(inner_y, 1e-6),
            wrap_x, inner_x, wrap_y, inner_y)


# ==================================================================== colour probe
CAL_LUT = None
SAVE_CS = 'sRGB'


def probe_colour(path):
    """Save a known 256 step ramp, read it back, and build the inverse LUT so the
    bytes on disk equal the authored values exactly.

    Returns (max_error_before_correction, lut_or_None).
    """
    global CAL_LUT, SAVE_CS
    ramp = np.arange(256, dtype=np.float32) / 255.0
    best = None
    for cs in ('sRGB', 'Non-Color'):
        img = bpy.data.images.new('probe_%s' % cs, width=256, height=1, alpha=False,
                                  float_buffer=False)
        img.colorspace_settings.name = cs
        rgba = np.ones((1, 256, 4), np.float32)
        rgba[0, :, 0] = ramp
        rgba[0, :, 1] = ramp
        rgba[0, :, 2] = ramp
        img.pixels.foreach_set(rgba.ravel())
        img.filepath_raw = path
        img.file_format = 'PNG'
        img.save()
        bpy.data.images.remove(img)
        got = decode_png(path).reshape(256, 3)[:, 0]
        err = int(np.abs(got.astype(np.int32) - np.arange(256)).max())
        print('[TEXTURE] colour probe %-9s max byte error = %d' % (cs, err))
        if best is None or err < best[0]:
            best = (err, cs, got.copy())
    err, cs, got = best
    if err == 0:
        CAL_LUT = None
        SAVE_CS = cs
    else:
        # invert the measured forward map: authored value -> pre-compensated value
        lut = np.interp(np.arange(256), got.astype(np.float32),
                        np.arange(256, dtype=np.float32))
        CAL_LUT = np.clip(np.rint(lut), 0, 255).astype(np.uint8)
        SAVE_CS = cs
    return err


def apply_cal(arr_u8):
    if CAL_LUT is None:
        return arr_u8
    return CAL_LUT[arr_u8]


# ==================================================================== PNG writing
def save_png(name, arr_u8, path, non_color=False):
    """Write an HxWx3 uint8 array to PNG through a Blender image buffer.

    The image is removed right after saving so only one buffer is alive.
    """
    arr = apply_cal(arr_u8)
    h, w = arr.shape[0], arr.shape[1]
    img = bpy.data.images.new(name, width=w, height=h, alpha=False, float_buffer=False)
    img.colorspace_settings.name = 'Non-Color' if non_color else SAVE_CS
    rgba = np.ones((h, w, 4), np.float32)
    rgba[:, :, :3] = (arr[::-1].astype(np.float32) / 255.0)  # blender rows bottom-up
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    gc.collect()


def to_u8(arr):
    return (np.clip(arr, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def gray(arr):
    if arr.ndim == 2:
        arr = arr[:, :, None]
    return np.repeat(arr[:, :, :1], 3, axis=2)


# ==================================================================== TEXTURES
def tex_concrete():
    """Wet harbour concrete: cold blue-grey, mint algae bloom, puddles."""
    h = w = SIZE
    grain = hash01(h, w, SEED + 1)
    coarse = fbm(h, w, SEED + 2, octaves=6, fy=8, fx=8)
    fine = fbm(h, w, SEED + 3, octaves=5, fy=64, fx=64)
    pits = fbm(h, w, SEED + 7, octaves=4, fy=128, fx=128)

    rgb = np.zeros((h, w, 3), np.float32)
    rgb[:, :, 0] = CONCRETE[0]
    rgb[:, :, 1] = CONCRETE[1]
    rgb[:, :, 2] = CONCRETE[2]
    rgb = np.clip(rgb + (coarse - 0.5)[:, :, None] * 0.34, 0, 1)

    stone = smoothstep(0.80, 0.95, grain) * smoothstep(0.35, 0.65, coarse)
    rgb = tint(rgb, stone * 0.65, (0.520, 0.530, 0.540))

    g = grime(h, w, SEED + 4, strength=0.50, fy=4, fx=4)
    rgb = tint(rgb, g * 0.70, (0.115, 0.130, 0.140))

    algae = smoothstep(0.50, 0.76, fbm(h, w, SEED + 8, octaves=4, fy=8, fx=8))
    rgb = tint(rgb, algae * 0.42, MINT)
    rgb = tint(rgb, smoothstep(0.68, 0.88, fbm(h, w, SEED + 9, octaves=3, fy=16, fx=16)) * 0.32, FOREST)

    pud = smoothstep(0.52, 0.68, fbm(h, w, SEED + 5, octaves=4, fy=8, fx=8))
    rgb = tint(rgb, pud * 0.55, COLD_DARK)

    ridge = 1.0 - np.abs(fbm(h, w, SEED + 6, octaves=4, fy=16, fx=16) - 0.5) * 2.0
    crack = smoothstep(0.93, 1.0, ridge)
    rgb = tint(rgb, crack * 0.75, (0.055, 0.065, 0.075))

    rgb = np.clip(rgb + (fine[:, :, None] - 0.5) * 0.12, 0, 1)

    rough = 0.88 - 0.58 * pud - 0.14 * algae + 0.10 * (fine - 0.5)
    rough = np.clip(rough, 0.06, 0.98)

    height = (coarse - 0.5) * 0.35 + (fine - 0.5) * 0.22 + stone * 0.45 - crack * 0.90 - pits * 0.10
    return rgb, rough, height


def tex_brick():
    """Old oxblood harbour brick: recessed mortar, soot, water staining."""
    h = w = SIZE
    bh, bw = 64, 128
    mortar = 8.0
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]

    row = np.floor(yy / bh).astype(np.int64)
    offset = (row % 2) * (bw // 2)
    sx = (xx + offset) % w           # running bond; wraps because w % bw == 0
    col = np.floor(sx / bw).astype(np.int64)
    ly = yy - row * bh
    lx = sx - col * bw
    edge = np.minimum(np.minimum(lx, bw - lx), np.minimum(ly, bh - ly))
    is_mortar = smoothstep(mortar, mortar - 2.5, edge)

    tone = hash_int(row * 64 + col, SEED + 11)

    br = np.zeros((h, w, 3), np.float32)
    br[:, :, 0] = OXBLOOD[0] + (tone - 0.5) * 0.20
    br[:, :, 1] = OXBLOOD[1] + (tone - 0.5) * 0.075
    br[:, :, 2] = OXBLOOD[2] + (tone - 0.5) * 0.070
    burnt = smoothstep(0.80, 0.95, tone)
    br = tint(br, burnt * 0.70, (0.175, 0.120, 0.115))
    pale = smoothstep(0.16, 0.04, tone)
    br = tint(br, pale * 0.70, (0.455, 0.420, 0.385))

    grit = fbm(h, w, SEED + 12, octaves=5, fy=64, fx=64)
    br = np.clip(br + (grit[:, :, None] - 0.5) * 0.18, 0, 1)

    mortar_col = np.zeros((h, w, 3), np.float32)
    mortar_col[:, :, 0] = BONE[0]
    mortar_col[:, :, 1] = BONE[1]
    mortar_col[:, :, 2] = BONE[2]
    mortar_col = np.clip(mortar_col + (grit[:, :, None] - 0.5) * 0.24, 0, 1)
    rgb = br * (1.0 - is_mortar[:, :, None]) + mortar_col * is_mortar[:, :, None]

    soot = smoothstep(0.40, 0.72, fbm(h, w, SEED + 15, octaves=4, fy=4, fx=4))
    rgb = tint(rgb, soot * 0.55, (0.070, 0.072, 0.078))

    streak = fbm(h, w, SEED + 13, octaves=5, fy=4, fx=32)
    run = smoothstep(0.56, 0.80, streak)
    rgb = tint(rgb, run * 0.55, (0.105, 0.120, 0.125))

    bloom = smoothstep(0.60, 0.84, fbm(h, w, SEED + 14, octaves=4, fy=16, fx=16))
    rgb = tint(rgb, bloom * 0.38, SAGE)

    g = grime(h, w, SEED + 16, strength=0.30, fy=4, fx=4)
    rgb = tint(rgb, g * 0.45, (0.115, 0.110, 0.105))
    rgb = np.clip(rgb, 0, 1)

    rough = 0.90 - 0.26 * run + 0.06 * (grit - 0.5) + 0.08 * is_mortar
    rough = np.clip(rough, 0.30, 0.99)

    chip = smoothstep(0.80, 0.95, grit) * 0.25
    height = -is_mortar * 0.85 + (grit - 0.5) * 0.30 + (tone - 0.5) * 0.18 - chip
    return rgb, rough, height


def tex_steel():
    """Steel plate: rivet grid, panel seams, ochre rust bleeding downward."""
    h = w = SIZE
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]

    plate = 256.0
    sy = np.abs(((yy + plate / 2) % plate) - plate / 2)
    sx = np.abs(((xx + plate / 2) % plate) - plate / 2)
    seam = np.maximum(smoothstep(5.0, 0.0, sy), smoothstep(5.0, 0.0, sx))

    metal = fbm(h, w, SEED + 21, octaves=5, fy=8, fx=8)
    brush = fbm(h, w, SEED + 22, octaves=4, fy=4, fx=64)   # rolled steel, vertical grain
    rgb = np.zeros((h, w, 3), np.float32)
    rgb[:, :, 0] = 0.185 + (metal - 0.5) * 0.075
    rgb[:, :, 1] = 0.205 + (metal - 0.5) * 0.075
    rgb[:, :, 2] = 0.230 + (metal - 0.5) * 0.075
    rgb = np.clip(rgb + (brush[:, :, None] - 0.5) * 0.085, 0, 1)

    step = 32.0
    ry = ((yy + step / 2) % step) - step / 2
    rx = ((xx + step / 2) % step) - step / 2
    near_seam = np.maximum(smoothstep(20.0, 6.0, sy), smoothstep(20.0, 6.0, sx))
    d = np.sqrt(ry ** 2 + rx ** 2)
    rivet = smoothstep(5.4, 3.4, d) * near_seam
    lit = smoothstep(1.8, -1.8, rx + ry)
    rgb = tint(rgb, rivet * (1.0 - lit) * 0.65, (0.055, 0.060, 0.068))
    rgb = tint(rgb, rivet * lit * 0.60, (0.395, 0.410, 0.425))
    rgb = tint(rgb, seam * 0.85, (0.065, 0.072, 0.082))

    rust_mask = fbm(h, w, SEED + 23, octaves=5, fy=8, fx=8)
    rust = smoothstep(0.50, 0.78, rust_mask)
    streak = fbm(h, w, SEED + 24, octaves=5, fy=4, fx=32)
    below = 1.0 - np.clip(sy / 130.0, 0, 1)
    bleed = smoothstep(0.58, 0.80, streak) * (0.35 + 0.65 * below) * (0.4 + 0.6 * rust)
    rust_amt = clamp01(rust * 0.78 + bleed * 0.85)
    rgb = tint(rgb, rust_amt * 0.92, RUST_OCHRE)
    rgb = tint(rgb, clamp01(rust_amt - 0.62) * 1.4, (0.300, 0.150, 0.110))

    moss = smoothstep(0.62, 0.84, fbm(h, w, SEED + 26, octaves=4, fy=16, fx=16)) * rust_amt
    rgb = tint(rgb, moss * 0.40, FOREST)

    g = grime(h, w, SEED + 25, strength=0.30, fy=4, fx=4)
    rgb = tint(rgb, g * 0.45, (0.105, 0.105, 0.100))
    rgb = np.clip(rgb, 0, 1)

    rough = 0.40 + 0.52 * rust_amt + 0.12 * (brush - 0.5) - 0.18 * rivet
    rough = np.clip(rough, 0.16, 0.99)

    height = rivet * 0.85 - seam * 0.45 + (brush - 0.5) * 0.10 + rust_amt * 0.18
    return rgb, rough, height


def tex_gravel():
    """Wet harbour gravel: rounded stones, water-filled voids, mint moss."""
    h = w = SIZE
    dist, pid = worley(h, w, 32, SEED + 31)
    stone_tone = hash_int(pid, SEED + 32)
    jitter = fbm(h, w, SEED + 33, octaves=5, fy=64, fx=64)
    fine = hash01(h, w, SEED + 36)

    edge = smoothstep(14.0, 8.0, dist)
    top = smoothstep(2.0, 13.0, dist)

    rgb = np.zeros((h, w, 3), np.float32)
    rgb[:, :, 0] = 0.345 + (stone_tone - 0.5) * 0.19
    rgb[:, :, 1] = 0.335 + (stone_tone - 0.5) * 0.18
    rgb[:, :, 2] = 0.310 + (stone_tone - 0.5) * 0.15
    rgb = np.clip(rgb + (jitter[:, :, None] - 0.5) * 0.15, 0, 1)
    rgb = tint(rgb, (1.0 - top) * 0.50, (0.195, 0.190, 0.178))
    rgb = tint(rgb, (1.0 - edge) * 0.88, (0.078, 0.084, 0.086))

    wet = smoothstep(0.45, 0.72, fbm(h, w, SEED + 34, octaves=4, fy=8, fx=8))
    rgb = tint(rgb, wet * 0.45, COLD_DARK)
    moss = smoothstep(0.60, 0.84, fbm(h, w, SEED + 37, octaves=4, fy=16, fx=16)) * (1.0 - edge)
    rgb = tint(rgb, moss * 0.60, FOREST)
    rgb = tint(rgb, smoothstep(0.72, 0.92, fbm(h, w, SEED + 38, octaves=3, fy=8, fx=8)) * 0.28, MINT)
    g = grime(h, w, SEED + 35, strength=0.35, fy=4, fx=4)
    rgb = tint(rgb, g * 0.45, (0.118, 0.118, 0.108))
    rgb = np.clip(rgb + (fine[:, :, None] - 0.5) * 0.05, 0, 1)
    rgb = np.clip(rgb, 0, 1)

    rough = 0.92 - 0.55 * wet - 0.10 * edge + 0.10 * (jitter - 0.5)
    rough = np.clip(rough, 0.12, 0.99)

    height = (top - 0.5) * 1.15 * edge + (jitter - 0.5) * 0.30 - (1.0 - edge) * 0.55
    return rgb, rough, height


def tex_tar():
    """Tar roof: rolled seams, patch repairs, grit, cold sheen."""
    h = w = SIZE
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]

    base = fbm(h, w, SEED + 41, octaves=6, fy=8, fx=8)
    fine = fbm(h, w, SEED + 46, octaves=5, fy=32, fx=32)
    grit = hash01(h, w, SEED + 42)

    rgb = np.zeros((h, w, 3), np.float32)
    rgb[:, :, 0] = 0.098 + (base - 0.5) * 0.095
    rgb[:, :, 1] = 0.102 + (base - 0.5) * 0.095
    rgb[:, :, 2] = 0.112 + (base - 0.5) * 0.095
    rgb = np.clip(rgb + (fine[:, :, None] - 0.5) * 0.060, 0, 1)

    seam_pitch = 256.0
    sy = ((yy + seam_pitch / 2) % seam_pitch) - seam_pitch / 2
    lip = smoothstep(11.0, 0.0, np.abs(sy))
    lip_hi = smoothstep(9.0, 3.0, sy) * smoothstep(-2.0, -9.0, sy)
    rgb = tint(rgb, lip * 0.65, (0.160, 0.166, 0.178))
    rgb = tint(rgb, lip_hi * 0.45, (0.280, 0.288, 0.305))

    patch = smoothstep(0.52, 0.76, fbm(h, w, SEED + 43, octaves=3, fy=4, fx=4))
    rgb = tint(rgb, patch * 0.65, (0.042, 0.045, 0.052))

    spec = smoothstep(0.78, 0.96, grit)
    rgb = tint(rgb, spec * 0.75, (0.440, 0.432, 0.410))
    bubble = smoothstep(0.930, 0.995, grit)
    rgb = tint(rgb, bubble * 0.60, (0.330, 0.338, 0.352))

    ridge = 1.0 - np.abs(fbm(h, w, SEED + 47, octaves=4, fy=16, fx=16) - 0.5) * 2.0
    split = smoothstep(0.88, 1.0, ridge)
    rgb = tint(rgb, split * 0.65, (0.012, 0.014, 0.018))

    wet = smoothstep(0.50, 0.68, fbm(h, w, SEED + 44, octaves=4, fy=8, fx=8))
    rgb = tint(rgb, wet * 0.45, (0.032, 0.038, 0.048))

    moss = smoothstep(0.66, 0.86, fbm(h, w, SEED + 48, octaves=4, fy=16, fx=16))
    rgb = tint(rgb, moss * 0.36, FOREST)
    rgb = tint(rgb, smoothstep(0.78, 0.94, fbm(h, w, SEED + 49, octaves=3, fy=8, fx=8)) * 0.22, SAGE)

    g = grime(h, w, SEED + 45, strength=0.25, fy=4, fx=4)
    rgb = tint(rgb, g * 0.40, (0.195, 0.192, 0.180))
    rgb = np.clip(rgb, 0, 1)

    rough = 0.88 - 0.42 * wet - 0.10 * lip + 0.10 * (base - 0.5)
    rough = np.clip(rough, 0.20, 0.99)

    height = lip * 0.55 + lip_hi * 0.35 + bubble * 0.45 + spec * 0.22 - split * 0.60 + (fine - 0.5) * 0.15
    return rgb, rough, height


def tex_wood():
    """Weathered dock planks: sage-grey boards, knots, rusted nails."""
    h = w = SIZE
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]

    ph = 128.0
    gap = 9.0
    plank = np.floor(yy / ph).astype(np.int64)
    ly = yy - plank * ph
    tone = hash_int(plank, SEED + 51)

    grain = fbm(h, w, SEED + 52, octaves=5, fy=64, fx=4)
    fibre = fbm(h, w, SEED + 53, octaves=4, fy=128, fx=8)
    knot_n, knot_id = worley(h, w, 64, SEED + 54)
    knot_sel = smoothstep(0.78, 0.92, hash_int(knot_id, SEED + 59))
    knot = smoothstep(24.0, 8.0, knot_n) * knot_sel

    rgb = np.zeros((h, w, 3), np.float32)
    rgb[:, :, 0] = 0.385 + (tone - 0.5) * 0.24
    rgb[:, :, 1] = 0.330 + (tone - 0.5) * 0.21
    rgb[:, :, 2] = 0.262 + (tone - 0.5) * 0.17
    rgb = np.clip(rgb + (grain[:, :, None] - 0.5) * 0.26 +
                  (fibre[:, :, None] - 0.5) * 0.16, 0, 1)
    bleach = smoothstep(0.56, 0.92, tone)
    rgb = tint(rgb, bleach * 0.68, (0.520, 0.512, 0.482))
    rot = smoothstep(0.16, 0.03, tone)
    rgb = tint(rgb, rot * 0.75, (0.152, 0.124, 0.098))

    rgb = tint(rgb, knot * 0.88, (0.100, 0.068, 0.052))
    rgb = tint(rgb, smoothstep(32.0, 24.0, knot_n) * knot_sel * 0.42, (0.315, 0.250, 0.195))

    seam = smoothstep(gap, 0.0, np.minimum(ly, ph - ly))
    rgb = tint(rgb, seam * 0.93, (0.030, 0.028, 0.025))

    nstep = 256.0
    nxs = ((xx + 40.0) % nstep) - nstep / 2
    nys = ((yy + ph / 2) % ph) - ph / 2
    nrad = np.sqrt(nxs ** 2 + nys ** 2)
    nail = smoothstep(8.0, 4.5, nrad)
    rgb = tint(rgb, nail * 0.88, RUST_OCHRE)
    rgb = tint(rgb, smoothstep(3.2, 1.6, nrad) * 0.68, (0.058, 0.052, 0.046))

    algae = smoothstep(0.58, 0.80, fbm(h, w, SEED + 55, octaves=4, fy=8, fx=8))
    rgb = tint(rgb, algae * 0.48, FOREST)
    sagewear = smoothstep(0.52, 0.78, fbm(h, w, SEED + 57, octaves=4, fy=16, fx=16))
    rgb = tint(rgb, sagewear * 0.42, SAGE)

    g = grime(h, w, SEED + 56, strength=0.32, fy=4, fx=4)
    rgb = tint(rgb, g * 0.50, (0.108, 0.105, 0.098))
    rgb = np.clip(rgb, 0, 1)

    rough = 0.90 - 0.12 * bleach + 0.10 * (grain - 0.5) - 0.26 * algae
    rough = np.clip(rough, 0.38, 0.99)

    height = -seam * 1.0 + (grain - 0.5) * 0.45 + (fibre - 0.5) * 0.20 + nail * 0.55 + knot * 0.30
    return rgb, rough, height


TEXTURES = [
    ('T_Floor_Concrete_Wet', tex_concrete, 4.0, (CONCRETE, COLD_DARK, MINT, FOREST),
     'Wet harbour concrete: cold blue-grey slab, exposed aggregate, mint algae bloom, standing puddles, hairline cracks.'),
    ('T_Wall_Brick_Old', tex_brick, 4.0, (OXBLOOD, BONE, SAGE),
     'Old oxblood harbour brick (the set\'s oxblood carrier): recessed bone mortar courses, soot, vertical water staining, sage salt bloom.'),
    ('T_Wall_Steel_Rusted', tex_steel, 4.0, (RUST_OCHRE, FOREST, COLD_DARK),
     'Steel plate with rivet grid and panel seams; ochre rust bleeding downward, forest-green algae on the old rust.'),
    ('T_Ground_Gravel', tex_gravel, 4.0, (COLD_DARK, FOREST, MINT),
     'Wet harbour gravel: rounded stones, water-filled voids, mint moss in the gaps, cold damp patches.'),
    ('T_Roof_Tar', tex_tar, 4.0, (COLD_DARK, FOREST, SAGE),
     'Tar roof: rolled seams, patch repairs, embedded grit and tar bubbles, cold puddle sheen, forest moss in the splits.'),
    ('T_Wood_Plank_Dock', tex_wood, 4.0, (SAGE, FOREST, RUST_OCHRE),
     'Weathered dock planks: sage-silvered boards, water-filled gaps, knots, rusted nail heads, green algae rot.'),
]


# ==================================================================== normal map
def normal_from_height(height, strength=2.6):
    """Gradient of the height field -> tangent space normal map (RGB 0..1)."""
    h = height.astype(np.float32)
    gy = np.gradient(h, axis=0)
    gx = np.gradient(h, axis=1)
    nx = -gx * strength
    ny = gy * strength
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx, ny, nz], axis=-1) / ln[..., None]
    return n * 0.5 + 0.5


# ================================================================ contact sheet
def contact_sheet(u8):
    """2x2 tiling of the texture with a 50% offset.

    The texture is tiled 2x2 (4096) and the block is shifted half a tile, then
    cropped back to 2048. The texture's own wrap edges land on the sheet's
    quadrant borders, so any seam or obvious repeat is immediately visible.
    """
    h, w = u8.shape[0], u8.shape[1]
    tiled = np.tile(u8, (2, 2, 1))
    return tiled[h // 2:h // 2 + h, w // 2:w // 2 + w].copy()


# ==================================================================== trim sheet
FONT = {
    'A': ('.#.', '#.#', '###', '#.#', '#.#'), 'B': ('##.', '#.#', '##.', '#.#', '##.'),
    'C': ('.##', '#..', '#..', '#..', '.##'), 'D': ('##.', '#.#', '#.#', '#.#', '##.'),
    'E': ('###', '#..', '##.', '#..', '###'), 'F': ('###', '#..', '##.', '#..', '#..'),
    'G': ('.##', '#..', '#.#', '#.#', '.##'), 'H': ('#.#', '#.#', '###', '#.#', '#.#'),
    'I': ('###', '.#.', '.#.', '.#.', '###'), 'J': ('..#', '..#', '..#', '#.#', '.#.'),
    'K': ('#.#', '#.#', '##.', '#.#', '#.#'), 'L': ('#..', '#..', '#..', '#..', '###'),
    'M': ('#.#', '###', '###', '#.#', '#.#'), 'N': ('#.#', '###', '###', '###', '#.#'),
    'O': ('.#.', '#.#', '#.#', '#.#', '.#.'), 'P': ('##.', '#.#', '##.', '#..', '#..'),
    'Q': ('.#.', '#.#', '###', '#.#', '.##'), 'R': ('##.', '#.#', '##.', '#.#', '#.#'),
    'S': ('.##', '#..', '.#.', '..#', '##.'), 'T': ('###', '.#.', '.#.', '.#.', '.#.'),
    'U': ('#.#', '#.#', '#.#', '#.#', '###'), 'V': ('#.#', '#.#', '#.#', '#.#', '.#.'),
    'W': ('#.#', '#.#', '###', '###', '#.#'), 'X': ('#.#', '#.#', '.#.', '#.#', '#.#'),
    'Y': ('#.#', '#.#', '.#.', '.#.', '.#.'), 'Z': ('###', '..#', '.#.', '#..', '###'),
    '0': ('###', '#.#', '#.#', '#.#', '###'), '1': ('.#.', '##.', '.#.', '.#.', '###'),
    '2': ('##.', '..#', '.#.', '#..', '###'), '3': ('##.', '..#', '.#.', '..#', '##.'),
    '4': ('#.#', '#.#', '###', '..#', '..#'), '5': ('###', '#..', '##.', '..#', '##.'),
    '6': ('.##', '#..', '###', '#.#', '###'), '7': ('###', '..#', '.#.', '.#.', '.#.'),
    '8': ('###', '#.#', '###', '#.#', '###'), '9': ('###', '#.#', '###', '..#', '##.'),
    '_': ('...', '...', '...', '...', '###'), '-': ('...', '...', '###', '...', '...'),
    '.': ('...', '...', '...', '...', '.#.'), '/': ('..#', '..#', '.#.', '#..', '#..'),
    ':': ('...', '.#.', '...', '.#.', '...'), ' ': ('...', '...', '...', '...', '...'),
}


def draw_text(canvas, x, y, text, scale=3, color=(235, 235, 225)):
    """Blit 3x5 pixel text onto an RGB uint8 canvas."""
    h, w = canvas.shape[0], canvas.shape[1]
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[' '])
        for ry in range(5):
            for rx in range(3):
                if glyph[ry][rx] == '#':
                    y0 = y + ry * scale
                    x0 = cx + rx * scale
                    if 0 <= y0 < h - scale and 0 <= x0 < w - scale:
                        canvas[y0:y0 + scale, x0:x0 + scale] = color
        cx += 4 * scale
    return cx


def downscale(u8, target):
    """Box-filter downscale of a uint8 image."""
    h, w = u8.shape[0], u8.shape[1]
    fy = h // target
    fx = w // target
    trimmed = u8[:fy * target, :fx * target].astype(np.float32)
    trimmed = trimmed.reshape(target, fy, target, fx, 3).mean(axis=(1, 3))
    return np.clip(trimmed + 0.5, 0, 255).astype(np.uint8)


def build_trim_sheet(entries, path):
    """Trim sheet: diffuse / normal / roughness / contact for all six materials.

    entries: list of (name, [diffuse_thumb, normal_thumb, rough_thumb, contact_thumb])
    """
    side = 4096
    cell = THUMB
    sheet = np.zeros((side, side, 3), np.uint8)
    sheet[:, :] = (16, 18, 20)
    draw_text(sheet, 40, 30, 'THE COMMANDER - BACKGROUND TEXTURE TRIM SHEET', 5, (150, 210, 180))
    draw_text(sheet, 40, 80, 'ROWS: DIFFUSE / NORMAL / ROUGHNESS / OFFSET CONTACT   -   2048 SOURCE, SEAMLESS TILING', 2, (110, 130, 120))
    draw_text(sheet, 40, 110, 'PALETTE: COLD BLUE-GREY / WET CONCRETE / SAGE / FOREST GREEN / MINT / OXBLOOD', 2, (120, 135, 128))

    labels = ['DIFFUSE', 'NORMAL', 'ROUGH', 'CONTACT']
    for i, (name, maps) in enumerate(entries):
        for row, thumb in enumerate(maps):
            y0 = 200 + row * (cell + 40)
            x0 = 48 + i * (cell + 20)
            sheet[y0:y0 + cell, x0:x0 + cell] = thumb
            draw_text(sheet, x0 + 4, y0 - 26, '%s %s' % (name.replace('T_', ''), labels[row]),
                      2, (205, 210, 200))
    save_png('T_Set_TrimSheet', sheet, path)
    return side


# ======================================================================== main
def pick_crop_windows(diff_u8):
    """Choose three 1:1 windows: the busiest region, a typical region and the
    calmest (shadowed / flat) region - so the crops show resolvable detail,
    typical surface, and grime breakup respectively."""
    lum = diff_u8.astype(np.float32) @ np.asarray([0.2126, 0.7152, 0.0722], np.float32)
    cands = []
    for oy in range(0, SIZE - CROP + 1, 256):
        for ox in range(0, SIZE - CROP + 1, 256):
            win = lum[oy:oy + CROP, ox:ox + CROP]
            cands.append((float(win.std()), float(win.mean()), oy, ox))
    cands.sort()
    calm = cands[len(cands) // 8]                 # a calm (shadowed / worn) region
    busy = cands[-1]                              # the busiest, most detailed region
    mids = sorted(cands, key=lambda c: abs(c[0] - (busy[0] + calm[0]) * 0.5))
    mid = mids[0]                                 # a typical region
    picks = []
    for _ in range(3):
        for cand in (busy, mid, calm):
            if cand[2:] not in [p[2:] for p in picks]:
                picks.append(cand)
                break
    return [(p[2], p[3]) for p in picks]


def main():
    probe_path = os.path.join(OUT, '_probe.png')
    err = probe_colour(probe_path)
    if os.path.exists(probe_path):
        os.remove(probe_path)
    print('[TEXTURE] colour pipeline: max byte error %d, save colourspace %s%s'
          % (err, SAVE_CS, '' if CAL_LUT is None else ' (compensating LUT applied)'))

    manifest = []
    trim_entries = []
    problems = []
    dim_table = []

    for name, fn, world_m, pal, notes in TEXTURES:
        rgb, rough, height = fn()
        diff_u8 = to_u8(rgb)
        norm_u8 = to_u8(normal_from_height(height))
        rough_u8 = to_u8(gray(rough))
        contact_u8 = contact_sheet(diff_u8)
        del rgb, rough, height
        gc.collect()

        files = []
        for suffix, arr, nc in (('', diff_u8, False), ('_normal', norm_u8, True),
                                ('_rough', rough_u8, True), ('_contact', contact_u8, False)):
            fname = name + suffix + '.png'
            save_png(name + suffix, arr, os.path.join(OUT, fname), non_color=nc)
            files.append(fname)

        # three native 1:1 crops, chosen by data (busiest / typical / calmest)
        crops = []
        for i, (oy, ox) in enumerate(pick_crop_windows(diff_u8)):
            crop = diff_u8[oy:oy + CROP, ox:ox + CROP]
            fname = '%s_crop%d.png' % (name, i + 1)
            save_png('%s_crop%d' % (name, i + 1), crop, os.path.join(OUT, fname))
            files.append(fname)
            crops.append(fname)

        # ---- verification against the real bytes on disk -------------------------
        dpath = os.path.join(OUT, name + '.png')
        dw, dh, depth, ctype = png_header(dpath)
        disk = decode_png(dpath)                       # independent stdlib decoder
        author = apply_cal(diff_u8)
        byte_err = int(np.abs(disk.astype(np.int32) - author.astype(np.int32)).max())
        dm, ds = luma_stats(disk)
        sx, sy_, wx, ix, wy, iy = seam_metrics(disk)
        nmean, nstd = luma_stats(readback_raw(os.path.join(OUT, name + '_normal.png')))
        rmean, rstd = luma_stats(readback_raw(os.path.join(OUT, name + '_rough.png')))
        cmean, cstd = luma_stats(readback_raw(os.path.join(OUT, name + '_contact.png')))
        cbytes = os.path.getsize(dpath)
        print('[TEXTURE] %-22s %dx%d d%dc%d %7.1fKB mean=%6.2f std=%6.2f byte_err=%d | seam x=%.2f y=%.2f | normal std=%5.2f | rough std=%5.2f | contact std=%6.2f | std_ok=%s'
              % (name, dw, dh, depth, ctype, cbytes / 1024.0, dm, ds, byte_err,
                 sx, sy_, nstd, rstd, cstd, 'YES' if ds > 8 else 'NO'))
        if ds <= 8:
            problems.append('%s diffuse std %.2f <= 8' % (name, ds))
        if byte_err > 1:
            problems.append('%s saved bytes differ from authored by %d' % (name, byte_err))
        if max(sx, sy_) > 2.0:
            problems.append('%s seam ratio x=%.2f y=%.2f' % (name, sx, sy_))
        if nstd <= 4:
            problems.append('%s normal map too flat (std %.2f)' % (name, nstd))
        if cbytes < 60000:
            problems.append('%s diffuse only %d bytes' % (name, cbytes))
        for suffix, arr, nc in (('', diff_u8, False), ('_normal', norm_u8, True),
                                ('_rough', rough_u8, True), ('_contact', contact_u8, False)):
            fnm = name + suffix + '.png'
            w, h, _d, _c = png_header(os.path.join(OUT, fnm))
            dim_table.append((fnm, w, h, 'PASS' if (w == SIZE and h == SIZE) else 'FAIL'))
        for c in crops:
            w, h, _d, _c = png_header(os.path.join(OUT, c))
            dim_table.append((c, w, h, 'PASS-1:1-CROP' if (w == CROP and h == CROP) else 'FAIL'))

        trim_entries.append((name, [downscale(diff_u8, THUMB), downscale(norm_u8, THUMB),
                                    downscale(rough_u8, THUMB), downscale(contact_u8, THUMB)]))
        manifest.append({
            'name': name,
            'files': files,
            'file_info': [{'file': f,
                           'width': png_header(os.path.join(OUT, f))[0],
                           'height': png_header(os.path.join(OUT, f))[1],
                           'bytes': os.path.getsize(os.path.join(OUT, f)),
                           'kb': round(os.path.getsize(os.path.join(OUT, f)) / 1024.0, 1)}
                          for f in files],
            'kb': [round(os.path.getsize(os.path.join(OUT, f)) / 1024.0, 1) for f in files],
            'notes': notes,
            'size': [SIZE, SIZE],
            'world_tile_m': world_m,
            'texel_density_cm': round(world_m * 100.0 / SIZE, 3),
            'palette_hex': [hexof(c) for c in pal],
            'mean': round(dm, 2),
            'std': round(ds, 2),
            'normal_std': round(nstd, 2),
            'roughness_std': round(rstd, 2),
            'seam_ratio_x': round(sx, 3),
            'seam_ratio_y': round(sy_, 3),
            'maps': {'diffuse': name + '.png', 'normal': name + '_normal.png',
                     'roughness': name + '_rough.png', 'contact_sheet': name + '_contact.png',
                     'crops_1to1': crops},
        })
        del diff_u8, norm_u8, rough_u8, contact_u8
        gc.collect()

    trim_path = os.path.join(OUT, 'T_Set_TrimSheet.png')
    side = build_trim_sheet(trim_entries, trim_path)
    tw, th, depth, ctype = png_header(trim_path)
    dim_table.append(('T_Set_TrimSheet.png', tw, th,
                      'PASS' if (tw >= 2048 and th >= 2048) else 'FAIL'))
    print('[TEXTURE] T_Set_TrimSheet %dx%d d%dc%d %.1fKB' % (tw, th, depth, ctype,
                                                             os.path.getsize(trim_path) / 1024.0))
    manifest.append({
        'name': 'T_Set_TrimSheet',
        'files': ['T_Set_TrimSheet.png'],
        'file_info': [{'file': 'T_Set_TrimSheet.png', 'width': tw, 'height': th,
                       'bytes': os.path.getsize(trim_path),
                       'kb': round(os.path.getsize(trim_path) / 1024.0, 1)}],
        'kb': [round(os.path.getsize(trim_path) / 1024.0, 1)],
        'notes': 'Trim sheet: diffuse / normal / roughness / offset contact for all six materials.',
        'size': [tw, th],
    })

    with open(os.path.join(OUT, 'textures_manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=1)

    if COPY_TO:
        os.makedirs(COPY_TO, exist_ok=True)
        total = 0
        for entry in manifest:
            for fname in entry['files']:
                shutil.copy2(os.path.join(OUT, fname), os.path.join(COPY_TO, fname))
                total += 1
        shutil.copy2(os.path.join(OUT, 'textures_manifest.json'),
                     os.path.join(COPY_TO, 'textures_manifest.json'))
        print('[TEXTURE] copied %d files -> %s' % (total + 1, COPY_TO))

    # ---- final dimension table --------------------------------------------------
    print('[TEXTURE] ==== DIMENSION TABLE (bar: 2048x2048 for maps, 1024x1024 1:1 crops) ====')
    for fnm, w, h, verdict in dim_table:
        print('[TEXTURE] %-34s %4dx%-4d %s' % (fnm, w, h, verdict))
    fails = [d for d in dim_table if d[3] == 'FAIL']
    print('[TEXTURE] dimension check: %d files, %d FAIL' % (len(dim_table), len(fails)))
    for f in fails:
        print('[TEXTURE] FAIL: %s is %dx%d' % (f[0], f[1], f[2]))

    if problems:
        print('[TEXTURE] PROBLEMS: ' + '; '.join(problems))
    else:
        print('[TEXTURE] ALL CHECKS PASS')
    print('[TEXTURE] DONE %d materials -> %s' % (len(TEXTURES), OUT))


if __name__ == '__main__':
    main()
