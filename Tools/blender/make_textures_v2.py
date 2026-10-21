"""
THE COMMANDER - background texture set, v2.

Rebuilds all six environment textures so they read as BELIEVABLE PBR surfaces
rather than graphic patterns. The three systemic problems this fixes:

  1. Noise: value-lattice fbm read as "fractured triangles". Replaced with
     tileable gradient (Perlin) noise.
  2. Shape: aggregate built from a smooth distance field read as "round
     bubbles". Replaced with Voronoi CELLS, so every stone has angular
     boundaries, a flat per-stone tone and its own lighting.
  3. Lighting: albedo was flat, so nothing looked lit. Every material now
     derives a height field, shades the albedo with the height gradient
     (one light direction, consistent across the set) and feeds the SAME
     height field to the normal map. Diffuse and normal can no longer
     disagree.

Also: soft, broken cracks (no contour-map outlines), directional wetness
that reads through sheen and pooling rather than a hue shift, and the
mint / sage / forest / oxblood palette with a single oxblood carrier.

Deterministic: fixed seed, no external assets, no image painting.

Usage:
  blender -b -noaudio -P Tools/blender/make_textures.py -- \
      --out <out_textures> [--copy-to <dir>]
"""

import gc
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402

# ------------------------------------------------------------------ args
OUT = None
COPY_TO = None
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
for i, a in enumerate(argv):
    if a == '--out':
        OUT = argv[i + 1]
    if a == '--copy-to':
        COPY_TO = argv[i + 1]
if OUT is None:
    OUT = os.path.join(HERE, 'out_textures')
os.makedirs(OUT, exist_ok=True)

SIZE = 2048
CROP = 1024
THUMB = 512
SEED = 1994001
SAVE_CS = 'sRGB'

# ------------------------------------------------------------------ palette
# (r, g, b) linear-ish working values; hex reported in the manifest.
CONCRETE_BASE = (0.300, 0.302, 0.298)
CONCRETE_CHIP_PALE = (0.470, 0.462, 0.440)
CONCRETE_CHIP_DARK = (0.120, 0.122, 0.128)
CONCRETE_WET = (0.150, 0.160, 0.170)
CONCRETE_MINT = (0.400, 0.560, 0.450)
CONCRETE_COLD = (0.230, 0.250, 0.270)

BRICK_OXBLOOD = (0.250, 0.105, 0.080)
BRICK_DARK = (0.120, 0.070, 0.060)
BRICK_PALE = (0.330, 0.200, 0.160)
BRICK_MORTAR = (0.520, 0.500, 0.450)
BRICK_SAGE = (0.450, 0.480, 0.430)

STEEL_BASE = (0.330, 0.345, 0.370)
STEEL_RUST = (0.420, 0.230, 0.110)
STEEL_RUST_DEEP = (0.300, 0.145, 0.105)
STEEL_FOREST = (0.180, 0.280, 0.190)

GRAVEL_BASE = (0.300, 0.295, 0.280)
GRAVEL_DARK = (0.130, 0.135, 0.140)
GRAVEL_PALE = (0.440, 0.430, 0.410)
GRAVEL_MINT = (0.380, 0.520, 0.430)
GRAVEL_WET = (0.110, 0.125, 0.140)

TAR_BASE = (0.085, 0.088, 0.095)
TAR_GRIT = (0.420, 0.415, 0.395)
TAR_SEAM = (0.180, 0.185, 0.200)
TAR_FOREST = (0.170, 0.270, 0.185)
TAR_WET = (0.300, 0.340, 0.400)

WOOD_SAGE = (0.420, 0.430, 0.400)
WOOD_BROWN = (0.280, 0.230, 0.185)
WOOD_DARK = (0.170, 0.150, 0.130)
WOOD_MINT = (0.330, 0.470, 0.380)
WOOD_RUST = (0.400, 0.240, 0.130)

# One light direction for the whole set: from the upper left, slightly high.
LIGHT = (-0.52, -0.60, 0.61)

MATERIALS = ['T_Floor_Concrete_Wet', 'T_Wall_Brick_Old', 'T_Wall_Steel_Rusted',
             'T_Ground_Gravel', 'T_Roof_Tar', 'T_Wood_Plank_Dock']


# ==================================================================== math
def clamp01(a):
    return np.clip(a, 0.0, 1.0).astype(np.float32)


def smoothstep(e0, e1, x):
    """Smooth ramp between e0 and e1. Works with e0 > e1 (descending ramp)."""
    d = e1 - e0
    if abs(d) < 1e-9:
        return (x >= e0).astype(np.float32)
    t = clamp01((x - e0) / d)
    return t * t * (3.0 - 2.0 * t)


def tint(rgb, amount, color):
    """Blend rgb toward color. color may be a 3-tuple or a full HxWx3 image."""
    c = np.asarray(color, np.float32)
    if c.ndim == 1:
        c = c.reshape(1, 1, 3)
    return rgb * (1.0 - amount[..., None]) + c * amount[..., None]


def lattice(h, w, cy, cx, seed):
    """Tileable value lattice with quintic interpolation."""
    rng = np.random.RandomState(int(seed) & 0x7FFFFFFF)
    a = rng.rand(cy + 1, cx + 1).astype(np.float32)
    Y = np.arange(h, dtype=np.float32)[:, None] * (cy / float(h))
    X = np.arange(w, dtype=np.float32)[None, :] * (cx / float(w))
    y0 = Y.astype(np.int32)
    x0 = X.astype(np.int32)
    fy = Y - y0
    fx = X - x0
    u = fy * fy * fy * (fy * (fy * 6 - 15) + 10)
    v = fx * fx * fx * (fx * (fx * 6 - 15) + 10)
    a = a[np.ix_(y0.ravel(), x0.ravel())].reshape(h, w)
    b = a[np.ix_(y0.ravel(), (x0.ravel() + 1) % (cx + 1))].reshape(h, w)
    c = a[np.ix_((y0.ravel() + 1) % (cy + 1), x0.ravel())].reshape(h, w)
    d = a[np.ix_((y0.ravel() + 1) % (cy + 1), (x0.ravel() + 1) % (cx + 1))].reshape(h, w)
    top = a * (1.0 - v) + b * v
    bot = c * (1.0 - v) + d * v
    return top * (1.0 - u) + bot * u


def perlin(h, w, seed, fy=4, fx=4, oy=0.0, ox=0.0):
    """Tileable gradient (Perlin) noise in 0..1.

    Gradient vectors repeat with the lattice, so the field is exactly periodic
    over the texture. Reads as organic, unlike the value lattice's grid bias.

    oy/ox shift the sample phase in CELL units. Each fbm octave uses a
    different phase: without it the octaves stack on the same grid and the
    surface reads as a mosaic of square modules.
    """
    ny = max(1, int(fy))
    nx = max(1, int(fx))
    rng = np.random.RandomState(int(seed) & 0x7FFFFFFF)
    ang = rng.rand(ny, nx).astype(np.float32) * (2.0 * np.pi)
    gxs = np.cos(ang).astype(np.float32)
    gys = np.sin(ang).astype(np.float32)
    Y = (np.arange(h, dtype=np.float32)[:, None] / np.float32(h)) * np.float32(ny) + np.float32(oy)
    X = (np.arange(w, dtype=np.float32)[None, :] / np.float32(w)) * np.float32(nx) + np.float32(ox)
    y0 = np.floor(Y).astype(np.int64)
    x0 = np.floor(X).astype(np.int64)
    vy = Y - y0
    vx = X - x0
    u = vy * vy * vy * (vy * (vy * 6.0 - 15.0) + 10.0)
    v = vx * vx * vx * (vx * (vx * 6.0 - 15.0) + 10.0)

    def grad(dy, dx):
        iy = (y0 + dy) % ny
        ix = (x0 + dx) % nx
        return gys[iy, ix] * dy + gxs[iy, ix] * dx

    n00 = grad(0, 0)
    n10 = grad(0, 1)
    n01 = grad(1, 0)
    n11 = grad(1, 1)
    top = n00 + u * (n10 - n00)
    bot = n01 + u * (n11 - n01)
    n = top + v * (bot - top)
    return clamp01(n * 0.72 + 0.5)


def perlin_at(h, w, seed, fy, fx, Yc, Xc):
    """Gradient noise sampled at ARBITRARY cell-space coordinates.

    The gradient lattice is periodic with period ny (nx) in cell space, so
    any coordinate offset is fine as long as the offset itself is periodic
    over the texture. That is what makes the domain warping below seamless.
    """
    ny = max(1, int(fy))
    nx = max(1, int(fx))
    rng = np.random.RandomState(int(seed) & 0x7FFFFFFF)
    ang = rng.rand(ny, nx).astype(np.float32) * (2.0 * np.pi)
    gxs = np.cos(ang).astype(np.float32)
    gys = np.sin(ang).astype(np.float32)
    Yc = np.broadcast_to(Yc, (h, w)).astype(np.float32)
    Xc = np.broadcast_to(Xc, (h, w)).astype(np.float32)
    # int32 indices: at 2048x2048 an int64 index array costs 33 MB each and
    # this function is called several times per material
    y0 = np.floor(Yc).astype(np.int32)
    x0 = np.floor(Xc).astype(np.int32)
    vy = Yc - y0
    vx = Xc - x0
    u = vy * vy * vy * (vy * (vy * 6.0 - 15.0) + 10.0)
    v = vx * vx * vx * (vx * (vx * 6.0 - 15.0) + 10.0)

    def grad(dy, dx):
        iy = (y0 + dy) % ny
        ix = (x0 + dx) % nx
        return gys[iy, ix] * dy + gxs[iy, ix] * dx

    n00 = grad(0, 0)
    n10 = grad(0, 1)
    n01 = grad(1, 0)
    n11 = grad(1, 1)
    top = n00 + u * (n10 - n00)
    bot = n01 + u * (n11 - n01)
    n = top + v * (bot - top)
    return clamp01(n * 0.72 + 0.5)


def fbm(h, w, seed, octaves=5, fy=4, fx=4, gain=0.5, warp=0.55):
    """Fractal gradient noise with DOMAIN WARPING.

    A square gradient lattice leaves axis-aligned artefacts: threshold the
    field and you get a mosaic of square cells rather than organic shapes.
    Warping the sample coordinates by a low-frequency periodic field breaks
    that alignment, so the lattice is no longer visible in the output. The
    warp is periodic, so the result still tiles exactly.
    """
    total = np.zeros((h, w), np.float32)
    amp = 1.0
    norm = 0.0
    cy, cx = int(fy), int(fx)
    # These MUST be column/row vectors. A 1-D array of length h broadcast to
    # (h, w) aligns to the WIDTH axis, which silently transposes the noise
    # and turns every lengthwise feature into a crosswise one.
    base_y = (np.arange(h, dtype=np.float32) / np.float32(h))[:, None]
    base_x = (np.arange(w, dtype=np.float32) / np.float32(w))[None, :]
    # the warp fields are themselves periodic, low frequency and smooth
    wy = fbm_raw(h, w, seed + 1013, 3, 2, 2)
    wx = fbm_raw(h, w, seed + 2027, 3, 2, 2)
    for o in range(octaves):
        # The warp displacement is CAPPED in cells. Scaling it with the
        # octave frequency displaces the high octaves by tens of cells and
        # scrambles the field into loops and whorls.
        cell_amp = min(cy, 6.0)
        Yc = base_y * cy + (wy - 0.5) * warp * cell_amp
        Xc = base_x * cx + (wx - 0.5) * warp * min(cx, 6.0)
        total += amp * perlin_at(h, w, seed + o * 7919, cy, cx, Yc, Xc)
        norm += amp
        amp *= gain
        cy *= 2
        cx *= 2
    return total / norm


def fbm_raw(h, w, seed, octaves=5, fy=4, fx=4, gain=0.5):
    """Unwarped fractal gradient noise (used for the warp fields)."""
    total = np.zeros((h, w), np.float32)
    amp = 1.0
    norm = 0.0
    cy, cx = int(fy), int(fx)
    for o in range(octaves):
        total += amp * perlin(h, w, seed + o * 7919, cy, cx)
        norm += amp
        amp *= gain
        cy *= 2
        cx *= 2
    return total / norm


def fbm_aniso(h, w, seed, octaves=5, fy=4, fx=4, fx_grow=1.0, gain=0.5):
    """Fractal noise whose x frequency can grow more slowly than its y.

    A wood grain is long fibres running along the board: the y frequency must
    climb to make fine lines across the grain, but the x frequency has to
    stay low or the fibres break into short dashes and the surface reads as
    a grid of rectangular modules. fx_grow < 1 keeps the fibres continuous.
    """
    total = np.zeros((h, w), np.float32)
    amp = 1.0
    norm = 0.0
    cy, cx = int(fy), int(fx)
    # These MUST be column/row vectors. A 1-D array of length h broadcast to
    # (h, w) aligns to the WIDTH axis, which silently transposes the noise
    # and turns every lengthwise feature into a crosswise one.
    base_y = (np.arange(h, dtype=np.float32) / np.float32(h))[:, None]
    base_x = (np.arange(w, dtype=np.float32) / np.float32(w))[None, :]
    wy = fbm_raw(h, w, seed + 3011, 3, 2, 2)
    wx = fbm_raw(h, w, seed + 4021, 3, 2, 2)
    for o in range(octaves):
        cell_amp = min(cy, 6.0)
        Yc = base_y * cy + (wy - 0.5) * 0.5 * cell_amp
        Xc = base_x * cx + (wx - 0.5) * 0.5 * min(cx, 6.0)
        total += amp * perlin_at(h, w, seed + o * 7919, cy, cx, Yc, Xc)
        norm += amp
        amp *= gain
        cy *= 2
        cx = max(1, int(round(cx * fx_grow)))
    return total / norm


def ridged(h, w, seed, octaves=4, fy=8, fx=8):
    """Ridged noise: sharp crests, used for cracks and splits."""
    n = fbm(h, w, seed, octaves=octaves, fy=fy, fx=fx)
    return 1.0 - np.abs(n - 0.5) * 2.0


def hash01(h, w, seed):
    """Deterministic per-pixel white noise."""
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


def worley2(h, w, cell, seed):
    """Periodic jittered-grid Voronoi. Returns (f1, f2, cell_id).

    f2 - f1 is small exactly on a cell boundary, which gives the crisp
    ANGULAR edges that stone, gravel and granules actually have.

    The grid is fitted to the texture (ny = round(h / cell)) rather than
    floor-divided, so the spacing is exactly h / ny and the pattern wraps
    seamlessly even when the requested cell size does not divide h.
    """
    ny = max(1, int(round(h / float(cell))))
    nx = max(1, int(round(w / float(cell))))
    cy_eff = h / float(ny)
    cx_eff = w / float(nx)
    rng = np.random.RandomState(int(seed) & 0x7FFFFFFF)
    jy = rng.rand(ny, nx).astype(np.float32)
    jx = rng.rand(ny, nx).astype(np.float32)
    Y = np.arange(h, dtype=np.float32)[:, None]
    X = np.arange(w, dtype=np.float32)[None, :]
    cy = (Y / cy_eff).astype(np.int64)
    cx = (X / cx_eff).astype(np.int64)
    best = np.full((h, w), 1e9, np.float32)
    second = np.full((h, w), 1e9, np.float32)
    bestid = np.zeros((h, w), np.int64)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            sy = cy + dy
            sx = cx + dx
            iy = sy % ny
            ix = sx % nx
            py = sy * cy_eff + jy[iy, ix] * cy_eff
            px = sx * cx_eff + jx[iy, ix] * cx_eff
            d = (Y - py) ** 2 + (X - px) ** 2
            m = d < best
            second = np.where(m, best, np.minimum(second, d))
            best = np.where(m, d, best)
            bestid = np.where(m, iy * nx + ix, bestid)
    return np.sqrt(best), np.sqrt(second), bestid


def grime(h, w, seed, strength=0.35, fy=4, fx=4):
    """Large scale soiling field, 0 = clean, 1 = filthy (tileable)."""
    return clamp01(smoothstep(0.35, 0.85, fbm(h, w, seed, octaves=4, fy=fy, fx=fx)) * strength)


def periodic_grad(hgt, axis):
    """Centred difference that WRAPS.

    np.gradient uses one-sided differences on the first and last row/column,
    which tilts the shading and the normal map exactly at the texture's
    wrap edge and leaves a visible seam. A tiling texture has to be treated
    as a torus, so the gradient is taken across the wrap.
    """
    a = np.roll(hgt, -1, axis=axis)
    b = np.roll(hgt, 1, axis=axis)
    return (a - b) * 0.5


def height_scale(hgt, target=0.42):
    """Relief scale for a height field.

    Height fields are authored in convenient units (grain ~0.1, mortar
    recess ~0.5), so their raw gradients are far too small to drive a
    normal map. Scale by a robust percentile of the gradient magnitude so
    the TYPICAL micro-slope reaches a fixed value, then clamp the steep
    edges so deep grooves stay sane instead of turning sideways.
    """
    gy = periodic_grad(hgt.astype(np.float32), 0)
    gx = periodic_grad(hgt.astype(np.float32), 1)
    m = np.sqrt(gx * gx + gy * gy)
    ref = float(np.percentile(m, 60.0))
    return target / max(ref, 1e-7)


def height_normal(hgt, scale=None):
    """Surface normal (not yet encoded) from a height field."""
    gy = periodic_grad(hgt.astype(np.float32), 0)
    gx = periodic_grad(hgt.astype(np.float32), 1)
    if scale is None:
        scale = height_scale(hgt)
    nx = np.clip(-gx * scale, -1.25, 1.25)
    ny = np.clip(-gy * scale, -1.25, 1.25)
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + 1.0)
    return np.stack([nx / ln, ny / ln, nz / ln], axis=2)


def shade_from_height(hgt, strength=1.0):
    """Lambert shading of a height field, one fixed light direction.

    This is what makes a surface look LIT rather than printed: the albedo is
    modulated by the same micro-relief that the normal map encodes.
    """
    n = height_normal(hgt)
    lx, ly, lz = LIGHT
    d = n[:, :, 0] * lx + n[:, :, 1] * ly + n[:, :, 2] * lz
    return clamp01(d)


def bake(albedo, hgt, strength=1.0, ambient=0.34, gain=0.86):
    """Apply height-derived lighting to an albedo."""
    sh = shade_from_height(hgt)
    light = ambient + gain * sh
    return np.clip(albedo * light[..., None], 0, 1)


# ==================================================================== PNG
def png_header(path):
    """(width, height, bitdepth, colourtype) read from the file on disk."""
    import struct
    with open(path, 'rb') as f:
        head = f.read(33)
    if head[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a PNG: %s' % path)
    w, h, depth, ctype = struct.unpack('>IIBB', head[16:26])
    return w, h, depth, ctype


def write_png_filter0(path, arr_u8):
    """Write a PNG with every row using filter type 0 (trivially decodable)."""
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


def decode_png(path):
    """Minimal PNG decoder: 8-bit, non-interlaced, colour type 2 or 6.

    Independent of Blender, so it proves what is actually on disk.
    """
    import struct
    import zlib
    data = open(path, 'rb').read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'not a PNG: %s' % path
    pos = 8
    idat = b''
    w = h = depth = ctype = 0
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + ln]
        if tag == b'IHDR':
            w, h, depth, ctype = struct.unpack('>IIBB', payload[:10])
        elif tag == b'IDAT':
            idat += payload
        elif tag == b'IEND':
            break
        pos += 12 + ln
    assert depth == 8 and ctype in (2, 6), 'unsupported PNG (depth=%d ctype=%d)' % (depth, ctype)
    nch = 3 if ctype == 2 else 4
    raw = zlib.decompress(idat)
    stride = w * nch
    out = np.zeros((h, stride), np.uint8)
    prev = np.zeros(stride, np.int32)
    p = 0
    for y in range(h):
        ft = raw[p]
        p += 1
        line = np.frombuffer(raw[p:p + stride], np.uint8).astype(np.int32)
        p += stride
        if ft == 0:
            cur = line
        elif ft == 1:
            cur = np.zeros(stride, np.int32)
            for c in range(nch):
                cur[c::nch] = np.cumsum(line[c::nch]) % 256
        elif ft == 2:
            cur = (line + prev) % 256
        elif ft == 3:
            cur = np.zeros(stride, np.int32)
            for i in range(stride):
                a = cur[i - nch] if i >= nch else 0
                cur[i] = (line[i] + ((a + prev[i]) >> 1)) % 256
        elif ft == 4:
            cur = np.zeros(stride, np.int32)
            for i in range(stride):
                a = cur[i - nch] if i >= nch else 0
                b = prev[i]
                c = prev[i - nch] if i >= nch else 0
                pa = abs(b - c)
                pb = abs(a - c)
                pc = abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[i] = (line[i] + pr) % 256
        else:
            raise ValueError('bad PNG filter %d' % ft)
        out[y] = cur.astype(np.uint8)
        prev = cur
    return out.reshape(h, w, nch)[:, :, :3]


def readback_raw(path):
    """Read a PNG back through Blender with no colour transform."""
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = 'Non-Color'
    img.reload()
    w, h = img.size
    buf = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(buf)
    px = buf.reshape(h, w, 4)[::-1, :, :3]
    out = (np.clip(px, 0, 1) * 255.0 + 0.5).astype(np.uint8)
    bpy.data.images.remove(img)
    return out


def to_u8(a):
    return (np.clip(a, 0, 1) * 255.0 + 0.5).astype(np.uint8)


def gray(a):
    if a.ndim == 2:
        a = a[:, :, None]
    return np.repeat(a[:, :, :1], 3, axis=2)


def normal_from_height(hgt, strength=None):
    """Tangent-space normal map from a height field (blue dominant).

    Uses the same relief scale as the diffuse lighting, so the normal map
    and the shaded albedo describe the SAME surface.
    """
    n = height_normal(hgt)
    return n * 0.5 + 0.5


def contact_sheet(diff_u8, tile=1024):
    """TRUE 2x2 tiling test.

    The texture is scaled to half resolution and then tiled 2x2, so the
    sheet's midlines ARE the texture's wrap seams. Any discontinuity
    across a midline is a genuine tiling defect, which a sheet that merely
    repeats one quadrant would never reveal.
    """
    h, w = diff_u8.shape[0], diff_u8.shape[1]
    half = downscale(diff_u8, tile)
    out = np.zeros((h, w, 3), np.uint8)
    out[:tile, :tile] = half
    out[:tile, tile:] = half
    out[tile:, :tile] = half
    out[tile:, tile:] = half
    # hairline guides on the midlines so a reviewer can see the seam exactly
    out[tile - 1:tile + 1, :] = (255, 60, 60)
    out[:, tile - 1:tile + 1] = (255, 60, 60)
    return out


def pick_crop_windows(diff_u8, n=3):
    """Pick three 1:1 windows: a busy one, a calm one, a typical one.

    Scoring uses a strided subsample so it stays fast at 2048x2048.
    """
    h, w = diff_u8.shape[0], diff_u8.shape[1]
    l = (0.299 * diff_u8[:, :, 0] + 0.587 * diff_u8[:, :, 1] +
         0.114 * diff_u8[:, :, 2]).astype(np.float32)
    step = 128
    cands = []
    for oy in range(0, h - CROP + 1, step):
        for ox in range(0, w - CROP + 1, step):
            blk = l[oy:oy + CROP:8, ox:ox + CROP:8]
            cands.append((float(blk.std()), oy, ox))
    cands.sort()
    calm = cands[len(cands) // 8]
    busy = cands[-1]
    mids = sorted(cands, key=lambda c: abs(c[0] - (busy[0] + calm[0]) * 0.5))
    picks = [busy, mids[0], calm]
    return [(oy, ox) for _s, oy, ox in picks]


def save_png(name, arr_u8, path, non_color=False):
    """Write a PNG through Blender so it matches the shipped pipeline."""
    rgba = np.empty((arr_u8.shape[0], arr_u8.shape[1], 4), np.float32)
    rgba[:, :, :3] = arr_u8[:, :, :3].astype(np.float32) / 255.0
    rgba[:, :, 3] = 1.0
    img = bpy.data.images.new(name, width=arr_u8.shape[1], height=arr_u8.shape[0],
                              alpha=False, float_buffer=False)
    img.colorspace_settings.name = 'Non-Color' if non_color else SAVE_CS
    img.pixels.foreach_set(rgba[::-1].ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    return path


def luma_stats(px_u8):
    l = (0.299 * px_u8[:, :, 0] + 0.587 * px_u8[:, :, 1] +
         0.114 * px_u8[:, :, 2])
    return float(l.mean()), float(l.std())


def seam_metrics(px_u8):
    """Edge-vs-interior wrap continuity.

    For a seamless texture, the difference across the wrap edge should be
    comparable to the difference between neighbouring interior columns. A
    ratio near 1 means no seam; a ratio far above 1 means a visible seam.
    """
    l = (0.299 * px_u8[:, :, 0] + 0.587 * px_u8[:, :, 1] +
         0.114 * px_u8[:, :, 2])
    h, w = l.shape
    wrap_x = float(np.abs(l[:, 0] - l[:, -1]).mean())
    wrap_y = float(np.abs(l[0, :] - l[-1, :]).mean())
    interior_x = float(np.abs(l[:, 1:] - l[:, :-1]).mean())
    interior_y = float(np.abs(l[1:, :] - l[:-1, :]).mean())
    return (wrap_x / max(interior_x, 1e-6), wrap_y / max(interior_y, 1e-6),
            wrap_x, interior_x, wrap_y, interior_y)


def hexof(c):
    return '#%02X%02X%02X' % tuple(int(round(v * 255)) for v in c[:3])


def selftest_bytes(tmp_dir):
    """Prove the decode path is byte-exact before trusting any measurement."""
    rng = np.random.RandomState(7)
    src = rng.randint(0, 256, size=(64, 64, 3)).astype(np.uint8)
    src[0, 0] = (0, 0, 0)
    src[1, 1] = (255, 255, 255)
    src[2, 2] = (128, 64, 32)
    path = os.path.join(tmp_dir, '_selftest.png')
    write_png_filter0(path, src)
    d1 = int(np.abs(decode_png(path).astype(np.int32) - src.astype(np.int32)).max())
    d2 = int(np.abs(readback_raw(path).astype(np.int32) - src.astype(np.int32)).max())
    os.remove(path)
    print('[TEXTURE] selftest: stdlib decoder max diff = %d, blender readback max diff = %d '
          '(both must be 0)' % (d1, d2))
    return d1, d2


# ================================================================ materials
def tex_concrete():
    """Wet harbour concrete: exposed aggregate, air voids, broken cracks,
    directional drainage streaks and glossy pooling."""
    h = w = SIZE
    paste = fbm(h, w, SEED + 2, octaves=6, fy=16, fx=16)
    fine = fbm(h, w, SEED + 3, octaves=5, fy=64, fx=64)
    grit = hash01(h, w, SEED + 1)

    rgb = np.zeros((h, w, 3), np.float32)
    rgb[:, :, 0] = CONCRETE_BASE[0] + (paste - 0.5) * 0.085
    rgb[:, :, 1] = CONCRETE_BASE[1] + (paste - 0.5) * 0.085
    rgb[:, :, 2] = CONCRETE_BASE[2] + (paste - 0.5) * 0.085

    height = (paste - 0.5) * 0.10 + (fine - 0.5) * 0.06
    stone_all = np.zeros((h, w), np.float32)

    # ---- exposed aggregate: VORONOI CELLS with FLAT angular facets --------
    # A flat plateau per cell (not a dome) is what makes a chip read as
    # broken stone rather than a rounded pebble. Only a minority of cells
    # are exposed: a surface where every cell is a proud chip reads as
    # lichen colonies rather than concrete.
    for cell, chip_a, chip_b, chip_c in ((18, 0.62, 0.10, 0.04),
                                         (44, 0.46, 0.08, 0.03)):
        f1, f2, cid = worley2(h, w, cell, SEED + 101 + cell)
        tone = hash_int(cid, SEED + 102 + cell)
        exposed = smoothstep(0.66, 0.84, tone)
        edge = smoothstep(3.2, 0.0, f2 - f1)           # 1 on a cell boundary
        facet = smoothstep(1.5, 7.0, f2 - f1)          # flat inside, bevelled edge
        stone = exposed * (1.0 - edge * 0.80)
        sc = np.zeros((h, w, 3), np.float32)
        sc[:, :, 0] = 0.430
        sc[:, :, 1] = 0.428
        sc[:, :, 2] = 0.415
        sc = tint(sc, smoothstep(0.72, 0.96, tone) * 0.90, CONCRETE_CHIP_PALE)
        sc = tint(sc, smoothstep(0.28, 0.05, tone) * 0.88, CONCRETE_CHIP_DARK)
        sc = tint(sc, smoothstep(0.44, 0.58, tone) * 0.40, (0.400, 0.360, 0.315))
        rgb = tint(rgb, stone * chip_a, sc)
        height = height + stone * facet * chip_b
        # a faint seam of shadow at the stone boundary, not a black outline
        rgb = tint(rgb, stone * edge * chip_c, (0.150, 0.152, 0.156))
        stone_all = np.maximum(stone_all, stone)

    # ---- cement paste veil: stones are PARTLY BURIED, not sitting on top --
    # Exposed aggregate that stands proud of the matrix reads as flakes
    # dropped on the surface. A soft overlay of paste, feathered by noise,
    # embeds the stones and breaks up their outlines.
    veil = smoothstep(0.40, 0.78, fbm(h, w, SEED + 120, octaves=5, fy=32, fx=32))
    bury = stone_all * veil
    rgb = tint(rgb, bury * 0.62, (0.352, 0.356, 0.352))
    rgb = tint(rgb, stone_all * (1.0 - veil) * 0.20, (0.430, 0.428, 0.415))
    height = height - bury * 0.10

    # ---- air voids: a FEW round blow holes with a lit lower lip -----------
    # Voids hold water: they go dark and saturated, and the water in them
    # catches a small sharp glint. That is what makes them read as pores.
    vf1, vf2, vcid = worley2(h, w, 7, SEED + 140)
    void_tone = hash_int(vcid, SEED + 141)
    is_void = smoothstep(0.972, 0.996, void_tone)
    void_shape = smoothstep(3.6, 1.4, vf1) * is_void
    void_lip = smoothstep(4.1, 2.9, vf1) * smoothstep(1.6, 2.9, vf1) * is_void
    void_glint = smoothstep(1.9, 1.1, vf1) * is_void * \
        smoothstep(0.55, 0.85, fbm(h, w, SEED + 141, octaves=3, fy=64, fx=64))
    rgb = tint(rgb, void_shape * 0.90, (0.030, 0.034, 0.042))
    rgb = tint(rgb, void_glint * 0.55, (0.780, 0.820, 0.880))
    rgb = tint(rgb, void_lip * 0.45, (0.470, 0.465, 0.445))
    height = height - void_shape * 0.30 + void_lip * 0.05

    # ---- cracks: soft, broken, with a spalled edge ------------------------
    cr = ridged(h, w, SEED + 6, octaves=4, fy=16, fx=16)
    zone = smoothstep(0.38, 0.68, fbm(h, w, SEED + 110, octaves=4, fy=16, fx=16))
    crack = smoothstep(0.80, 0.99, cr) * zone
    crack = crack * smoothstep(0.26, 0.68, fbm(h, w, SEED + 111, octaves=3, fy=32, fx=32))
    spall = smoothstep(0.78, 0.95, cr) * zone
    rgb = tint(rgb, crack * 0.78, (0.075, 0.078, 0.084))
    rgb = tint(rgb, spall * 0.38, (0.430, 0.420, 0.400))
    height = height - crack * 0.26

    # ---- directional wetness: vertical drainage streaks + pooling --------
    # The WET read has to come from optics: a broad sky reflection and
    # darkened, saturated damp patches. A hue shift alone reads as lichen.
    streak = fbm(h, w, SEED + 112, octaves=5, fy=4, fx=32)
    damp = smoothstep(0.44, 0.78, streak)
    pool = smoothstep(0.56, 0.74, fbm(h, w, SEED + 113, octaves=4, fy=8, fx=8))
    wet = clamp01(damp * 0.55 + pool * 0.85)
    rgb = tint(rgb, wet * 0.42, CONCRETE_WET)
    rgb = tint(rgb, pool * 0.32, (0.055, 0.060, 0.068))
    # a broad, soft sky reflection along the drainage direction
    rgb = tint(rgb, smoothstep(0.52, 0.90, streak) * 0.30, (0.620, 0.660, 0.720))
    # a tighter, brighter specular where the film is deepest
    rgb = tint(rgb, smoothstep(0.72, 0.94, streak) * 0.24, (0.780, 0.820, 0.870))
    rgb = tint(rgb, smoothstep(0.70, 0.90, pool) * 0.20, (0.600, 0.660, 0.740))
    # sharp glints on the high points of the aggregate under the water film:
    # small, bright, isolated specks are what say "a film of water is here"
    glint = smoothstep(0.86, 0.99, fbm(h, w, SEED + 114, octaves=3, fy=128, fx=128))
    rgb = tint(rgb, glint * (0.35 + 0.65 * wet) * 0.65, (0.850, 0.880, 0.930))
    height = height - pool * 0.05

    # ---- algae only where it is genuinely damp ----------------------------
    algae = smoothstep(0.64, 0.86, fbm(h, w, SEED + 8, octaves=4, fy=8, fx=8))
    rgb = tint(rgb, algae * wet * 0.16, CONCRETE_MINT)
    rgb = tint(rgb, smoothstep(0.74, 0.92, fbm(h, w, SEED + 9, octaves=3, fy=16, fx=16))
               * wet * 0.10, (0.180, 0.280, 0.190))

    g = grime(h, w, SEED + 4, strength=0.30, fy=4, fx=4)
    rgb = tint(rgb, g * 0.30, (0.215, 0.215, 0.205))
    rgb = np.clip(rgb + (grit[:, :, None] - 0.5) * 0.045, 0, 1)
    rgb = np.clip(rgb, 0, 1)

    rough = 0.88 - 0.38 * damp - 0.66 * pool - 0.05 * algae
    rough = np.clip(rough - 0.05 * (1.0 - void_shape), 0.07, 0.97)

    # A gentle relief: a strongly embossed surface reads as carved lichen
    # rather than a flat concrete slab. Real wetness is carried by the
    # roughness map and the reflection, not by deep relief.
    rgb = bake(rgb, height, strength=2.6, ambient=0.52, gain=0.62)
    return rgb, rough, height


def tex_brick():
    """Old oxblood harbour brick: running bond, chipped arrises, recessed
    lime mortar, soot and vertical water staining."""
    h = w = SIZE
    row_h = 64
    brick_w = 128
    mortar = 7
    Y = np.arange(h, dtype=np.int64)[:, None]
    X = np.arange(w, dtype=np.int64)[None, :]
    r = Y // row_h
    off = (r % 2) * (brick_w // 2)
    u = X + off
    bx = u % brick_w
    by = Y % row_h
    # The brick index must be taken modulo the number of bricks per row, or
    # the offset course runs off the end of the texture and the brick at the
    # wrap is a different brick from the one that starts it -> visible seam.
    per_row = w // brick_w
    bid = r * 100003 + (u // brick_w) % per_row

    d = np.minimum(np.minimum(bx, brick_w - bx), np.minimum(by, row_h - by)).astype(np.float32)
    chip = (fbm(h, w, SEED + 21, octaves=4, fy=64, fx=64) - 0.5) * 5.0
    d2 = d + chip
    is_mortar = d2 < mortar
    # corner chips: erode the arrises unevenly
    corner = np.minimum(np.minimum(bx, brick_w - bx), np.minimum(by, row_h - by)).astype(np.float32)
    edge_break = smoothstep(mortar, mortar + 9.0, d2)

    tone = hash_int(bid, SEED + 22)
    rgb = np.zeros((h, w, 3), np.float32)
    rgb[:, :, 0] = BRICK_OXBLOOD[0]
    rgb[:, :, 1] = BRICK_OXBLOOD[1]
    rgb[:, :, 2] = BRICK_OXBLOOD[2]
    rgb = tint(rgb, smoothstep(0.62, 0.92, tone) * 0.85, BRICK_PALE)
    rgb = tint(rgb, smoothstep(0.30, 0.05, tone) * 0.80, BRICK_DARK)
    rgb = tint(rgb, smoothstep(0.44, 0.56, tone) * 0.30, (0.280, 0.230, 0.205))
    # per-brick surface grain
    grain = fbm(h, w, SEED + 23, octaves=4, fy=32, fx=32)
    rgb = np.clip(rgb + (grain - 0.5)[:, :, None] * 0.10, 0, 1)

    # mortar
    mort_tone = fbm(h, w, SEED + 24, octaves=4, fy=32, fx=32)
    mortar_col = np.zeros((h, w, 3), np.float32)
    mortar_col[:, :, 0] = BRICK_MORTAR[0]
    mortar_col[:, :, 1] = BRICK_MORTAR[1]
    mortar_col[:, :, 2] = BRICK_MORTAR[2]
    mortar_col = tint(mortar_col, smoothstep(0.55, 0.85, mort_tone) * 0.5, BRICK_SAGE)
    rgb = tint(rgb, is_mortar.astype(np.float32), mortar_col)

    # ambient occlusion: shadow under the top arris of each brick
    ao = (1.0 - smoothstep(mortar, mortar + 14.0, d2)) * (1.0 - by.astype(np.float32) / row_h)
    ao = np.clip(ao, 0, 1) * (1.0 - is_mortar.astype(np.float32))
    rgb = tint(rgb, ao * 0.55, (0.055, 0.045, 0.042))
    # and a lit lower edge on the brick
    lit = smoothstep(0.72, 0.98, by.astype(np.float32) / row_h) * edge_break
    rgb = tint(rgb, lit * 0.22, (0.560, 0.430, 0.360))

    # chipped arris: exposed pale brick body at the edges
    chipped = smoothstep(mortar + 7.0, mortar + 1.0, d2) * (1.0 - is_mortar.astype(np.float32))
    chipped = chipped * smoothstep(0.45, 0.80, fbm(h, w, SEED + 25, octaves=4, fy=32, fx=32))
    rgb = tint(rgb, chipped * 0.45, (0.430, 0.330, 0.270))

    # soot and water staining
    soot = grime(h, w, SEED + 26, strength=0.60, fy=4, fx=4)
    rgb = tint(rgb, soot * 0.45, (0.075, 0.072, 0.072))
    stain = fbm(h, w, SEED + 27, octaves=5, fy=2, fx=64)
    wet_stain = smoothstep(0.52, 0.82, stain) * (0.35 + 0.65 * soot)
    rgb = tint(rgb, wet_stain * 0.45, (0.150, 0.130, 0.115))
    # salt bloom
    rgb = tint(rgb, smoothstep(0.70, 0.92, fbm(h, w, SEED + 28, octaves=4, fy=8, fx=8)) * 0.30,
               BRICK_SAGE)

    height = np.zeros((h, w), np.float32)
    height = height - is_mortar.astype(np.float32) * 0.55
    height = height + (grain - 0.5) * 0.10
    height = height - chipped * 0.12
    height = height - ao * 0.10

    rough = 0.84 - 0.20 * wet_stain - 0.10 * soot
    rough = np.clip(rough + is_mortar.astype(np.float32) * 0.10, 0.35, 0.99)

    rgb = bake(rgb, height, strength=2.2, ambient=0.42, gain=0.76)
    return rgb, rough, height


def tex_steel():
    """Rusted steel plate: rolled seams, rivet grid, ochre rust bleeding
    downward, corrosion pitting."""
    h = w = SIZE
    # Plates are large (512 px = 1 m at this texel density). A tighter grid
    # made the whole sheet read as one small unit repeated 4x4.
    plate = 512
    Y = np.arange(h, dtype=np.float32)[:, None]
    X = np.arange(w, dtype=np.float32)[None, :]
    sy = np.abs(((Y + plate / 2) % plate) - plate / 2)
    sx = np.abs(((X + plate / 2) % plate) - plate / 2)
    seam = np.maximum(smoothstep(4.0, 0.0, sy), smoothstep(4.0, 0.0, sx))
    seam_lip = smoothstep(9.0, 3.0, sy) * smoothstep(-1.0, -8.0, sy)

    metal = fbm(h, w, SEED + 31, octaves=5, fy=8, fx=8)
    brush = fbm(h, w, SEED + 32, octaves=4, fy=2, fx=64)
    scale = fbm(h, w, SEED + 33, octaves=5, fy=32, fx=32)

    rgb = np.zeros((h, w, 3), np.float32)
    rgb[:, :, 0] = STEEL_BASE[0] + (metal - 0.5) * 0.16
    rgb[:, :, 1] = STEEL_BASE[1] + (metal - 0.5) * 0.16
    rgb[:, :, 2] = STEEL_BASE[2] + (metal - 0.5) * 0.16
    rgb = np.clip(rgb + (brush[:, :, None] - 0.5) * 0.12, 0, 1)
    rgb = tint(rgb, smoothstep(0.45, 0.80, scale) * 0.45, (0.255, 0.268, 0.250))

    height = np.zeros((h, w), np.float32)
    height = height - seam * 0.35 + seam_lip * 0.20

    # ---- rivets: domed heads, spaced on a grid that DIVIDES the texture --
    # A step that does not divide 2048 would shift the rivet phase across the
    # wrap and open a visible seam.
    step = 32.0
    ry = ((Y + step / 2) % step) - step / 2
    rx = ((X + step / 2) % step) - step / 2
    d = np.sqrt(ry ** 2 + rx ** 2)
    # each plate has its own rivet layout, so the field is not one rigid grid
    pid = ((Y // plate).astype(np.int64) * 1000 + (X // plate).astype(np.int64))
    pvar = hash_int(pid, SEED + 34)
    present = smoothstep(0.12, 0.30, pvar)          # some plates lost rivets
    head = smoothstep(4.6, 3.0, d) * present
    dome = smoothstep(4.6, 0.0, d)
    rgb = tint(rgb, head * (1.0 - dome) * 0.55, (0.150, 0.160, 0.172))
    height = height + head * dome * 0.30
    # rust weeping from under some rivets
    rust_run = smoothstep(0.55, 0.90, hash01(h, w, SEED + 344)) * head
    rgb = tint(rgb, rust_run * 0.35, STEEL_RUST_DEEP)

    # ---- rust: voronoi cells give ragged patch edges ---------------------
    f1, f2, cid = worley2(h, w, 64, SEED + 35)
    tone = hash_int(cid, SEED + 36)
    patch = smoothstep(0.44, 0.66, fbm(h, w, SEED + 35, octaves=5, fy=8, fx=8))
    blob = smoothstep(0.36, 0.0, f2 - f1)
    # per-plate rust amount: plates corrode unevenly, which stops the sheet
    # reading as one 256-pixel unit repeated 4x4
    plate_tone = 0.55 + 0.75 * hash_int(pid, SEED + 37)
    rust = clamp01(patch * blob * 1.3 * plate_tone)
    # fine scale on the rust
    rust_tex = fbm(h, w, SEED + 37, octaves=5, fy=32, fx=32)
    rgb = tint(rgb, rust * 0.95, STEEL_RUST)
    rgb = tint(rgb, rust * smoothstep(0.55, 0.85, rust_tex) * 0.45, STEEL_RUST_DEEP)
    rgb = tint(rgb, np.clip(rust - 0.60, 0, 1) * 1.4, (0.240, 0.110, 0.080))
    # vertical bleed under the seams
    bleed = smoothstep(0.54, 0.82, fbm(h, w, SEED + 38, octaves=5, fy=2, fx=32))
    below = 1.0 - np.clip(sy / 150.0, 0, 1)
    rgb = tint(rgb, bleed * (0.30 + 0.70 * below) * 0.60, STEEL_RUST)
    height = height + rust * 0.16

    # ---- pitting ---------------------------------------------------------
    pf1, pf2, pcid = worley2(h, w, 4, SEED + 39)
    ptone = hash_int(pcid, SEED + 40)
    pit = smoothstep(0.93, 0.99, ptone) * smoothstep(1.9, 0.7, pf1)
    pit_rim = smoothstep(2.4, 1.4, pf1) * smoothstep(0.7, 1.5, pf1) * smoothstep(0.90, 0.97, ptone)
    rgb = tint(rgb, pit * 0.75, (0.070, 0.052, 0.042))
    rgb = tint(rgb, pit_rim * 0.40, (0.420, 0.265, 0.155))
    height = height - pit * 0.30 + pit_rim * 0.08

    moss = smoothstep(0.60, 0.84, fbm(h, w, SEED + 41, octaves=4, fy=16, fx=16)) * rust
    rgb = tint(rgb, moss * 0.50, STEEL_FOREST)

    g = grime(h, w, SEED + 42, strength=0.32, fy=4, fx=4)
    rgb = tint(rgb, g * 0.42, (0.115, 0.112, 0.104))
    rgb = np.clip(rgb, 0, 1)

    rough = 0.40 + 0.52 * rust + 0.12 * (brush - 0.5) - 0.20 * head + 0.10 * moss
    rough = np.clip(rough, 0.14, 0.99)

    rgb = bake(rgb, height, strength=2.4, ambient=0.42, gain=0.78)
    return rgb, rough, height


def tex_gravel():
    """Wet harbour gravel: individual rounded stones, water in the gaps."""
    h = w = SIZE
    mud = fbm(h, w, SEED + 51, octaves=6, fy=4, fx=4)
    fine = fbm(h, w, SEED + 52, octaves=5, fy=64, fx=64)

    rgb = np.zeros((h, w, 3), np.float32)
    rgb[:, :, 0] = 0.190 + (mud - 0.5) * 0.10
    rgb[:, :, 1] = 0.185 + (mud - 0.5) * 0.10
    rgb[:, :, 2] = 0.175 + (mud - 0.5) * 0.10
    height = (mud - 0.5) * 0.12

    # ---- stones: two Voronoi scales, per-stone tone and domed relief ------
    for cell, cover, relief in ((26, 0.85, 0.55), (14, 0.60, 0.40)):
        f1, f2, cid = worley2(h, w, cell, SEED + 53 + cell)
        tone = hash_int(cid, SEED + 54 + cell)
        edge = smoothstep(2.2, 0.0, f2 - f1)
        dome = smoothstep(cell * 0.50, 0.0, f1)
        stone = (1.0 - edge * 0.9)
        sc = np.zeros((h, w, 3), np.float32)
        sc[:, :, 0] = GRAVEL_BASE[0]
        sc[:, :, 1] = GRAVEL_BASE[1]
        sc[:, :, 2] = GRAVEL_BASE[2]
        sc = tint(sc, smoothstep(0.68, 0.94, tone) * 0.9, GRAVEL_PALE)
        sc = tint(sc, smoothstep(0.28, 0.05, tone) * 0.85, GRAVEL_DARK)
        sc = tint(sc, smoothstep(0.46, 0.58, tone) * 0.30, (0.320, 0.270, 0.230))
        rgb = tint(rgb, stone * cover, sc)
        rgb = tint(rgb, stone * edge * 0.55, (0.070, 0.075, 0.080))
        height = height + stone * dome * relief

    # ---- water in the gaps ------------------------------------------------
    gap = 1.0 - clamp01((height - height.min()) / max(height.max() - height.min(), 1e-6))
    gap = smoothstep(0.30, 0.02, gap)
    rgb = tint(rgb, gap * 0.80, GRAVEL_WET)
    # wet sheen catching the sky on the wet stones
    rgb = tint(rgb, smoothstep(0.55, 0.85, fine) * 0.10, (0.560, 0.600, 0.640))

    # ---- moss in the damp gaps -------------------------------------------
    moss = smoothstep(0.60, 0.86, fbm(h, w, SEED + 56, octaves=4, fy=16, fx=16))
    rgb = tint(rgb, moss * gap * 0.55, GRAVEL_MINT)
    rgb = tint(rgb, smoothstep(0.74, 0.92, fbm(h, w, SEED + 57, octaves=3, fy=8, fx=8)) * 0.22,
               (0.200, 0.300, 0.210))

    g = grime(h, w, SEED + 58, strength=0.35, fy=4, fx=4)
    rgb = tint(rgb, g * 0.40, (0.115, 0.112, 0.104))
    rgb = np.clip(rgb + (fine[:, :, None] - 0.5) * 0.05, 0, 1)
    rgb = np.clip(rgb, 0, 1)

    rough = 0.62 - 0.45 * gap + 0.10 * (fine - 0.5)
    rough = np.clip(rough, 0.10, 0.98)

    rgb = bake(rgb, height, strength=2.8, ambient=0.40, gain=0.80)
    return rgb, rough, height


def tex_tar():
    """Tar roof: rolled seams, patch repairs, embedded grit, blisters,
    broken splits and a wet sheen."""
    h = w = SIZE
    Y = np.arange(h, dtype=np.float32)[:, None]
    X = np.arange(w, dtype=np.float32)[None, :]

    # Rolled roofing has PARALLEL laps running one way. Every other field
    # here uses a frequency that is deliberately INCOMMENSURATE with the
    # 256 px seam pitch, so nothing lines up with the seams and no second
    # direction of banding appears.
    base = fbm(h, w, SEED + 61, octaves=6, fy=24, fx=20)
    grit = hash01(h, w, SEED + 62)

    rgb = np.zeros((h, w, 3), np.float32)
    rgb[:, :, 0] = TAR_BASE[0] + (base - 0.5) * 0.055
    rgb[:, :, 1] = TAR_BASE[1] + (base - 0.5) * 0.055
    rgb[:, :, 2] = TAR_BASE[2] + (base - 0.5) * 0.055
    height = (base - 0.5) * 0.10

    # ---- embedded granules: angular chips, bedded into the tar -----------
    # The grit is the clearest tar cue, so it is dense, angular, and sits IN
    # the surface rather than scattered on top of it.
    f1, f2, cid = worley2(h, w, 5, SEED + 63)
    tone = hash_int(cid, SEED + 64)
    gsel = smoothstep(0.30, 0.46, tone) * smoothstep(0.66, 0.44, tone)
    gsel = np.clip(gsel + smoothstep(0.74, 0.90, tone) * 0.9, 0, 1)
    gedge = smoothstep(1.4, 0.0, f2 - f1)
    gdome = smoothstep(2.4, 0.0, f1)
    rgb = tint(rgb, gsel * (1.0 - gedge * 0.8) * 0.80, TAR_GRIT)
    rgb = tint(rgb, gsel * gedge * 0.40, (0.030, 0.032, 0.036))
    height = height + gsel * gdome * 0.16
    # a second, coarser scatter of larger stones, bedded down
    k1, k2, kcid = worley2(h, w, 19, SEED + 63)
    ksel = smoothstep(0.82, 0.94, hash_int(kcid, SEED + 641))
    kedge = smoothstep(2.0, 0.0, k2 - k1)
    rgb = tint(rgb, ksel * (1.0 - kedge * 0.85) * 0.85, (0.480, 0.470, 0.445))
    rgb = tint(rgb, ksel * kedge * 0.45, (0.026, 0.028, 0.032))
    height = height + ksel * smoothstep(9.0, 0.0, k1) * 0.22

    # ---- rolled seams: a raised lap with a lit top edge and a cast shadow --
    # A rolled seam is a lap, not a drawn line: it wanders, and it is broken
    # by patches and wear rather than running dead straight for 2048 px.
    pitch = 256.0
    sy = ((Y + pitch / 2) % pitch) - pitch / 2
    wander = (fbm(h, w, SEED + 65, octaves=4, fy=2, fx=16) - 0.5) * 26.0
    ragged = (fbm(h, w, SEED + 651, octaves=4, fy=8, fx=32) - 0.5) * 5.0
    s = sy + wander + ragged
    lip_r = smoothstep(11.0, 0.0, np.abs(s))
    # the crown of the roll catches the sky; the trough below it is in shade
    crown = smoothstep(7.0, 2.0, s) * smoothstep(-4.0, -10.0, s)
    trough = smoothstep(6.0, 16.0, s) * smoothstep(26.0, 15.0, s)
    rgb = tint(rgb, lip_r * 0.45, TAR_SEAM)
    # a narrow, bright, CONTINUOUS highlight along the crown: this is what
    # makes the lap read as a raised roll rather than a drawn line
    rgb = tint(rgb, crown * 0.60, (0.520, 0.535, 0.560))
    rgb = tint(rgb, trough * 0.70, (0.015, 0.017, 0.020))
    height = height + lip_r * 0.85 + crown * 0.50 - trough * 0.45

    # ---- patch repairs: a trowelled patch with a raised, ragged edge ------
    # The patch shape comes from a MULTI-OCTAVE field rather than one
    # thresholded lattice: a single lattice draws its own grid, and the
    # surface then reads as a mosaic of square tiles.
    patch_f = fbm(h, w, SEED + 66, octaves=6, fy=20, fx=28)
    patch = smoothstep(0.52, 0.66, patch_f)
    patch_edge = patch * smoothstep(0.66, 0.60, patch_f)
    trowel = fbm_aniso(h, w, SEED + 67, octaves=4, fy=64, fx=11)
    rgb = tint(rgb, patch * 0.38, (0.045, 0.047, 0.053))
    rgb = tint(rgb, patch * smoothstep(0.55, 0.80, trowel) * 0.22, (0.085, 0.087, 0.094))
    rgb = tint(rgb, patch_edge * 0.40, (0.115, 0.118, 0.128))
    height = height + patch * 0.14 + patch_edge * 0.18

    # ---- blisters: domed bulges of trapped air under a stretched skin -----
    bf1, bf2, bcid = worley2(h, w, 34, SEED + 68)
    btone = hash_int(bcid, SEED + 681)
    blister = smoothstep(0.88, 0.98, btone) * smoothstep(7.0, 2.0, bf1)
    # the skin over a blister is taut and catches a bright highlight
    blister_rim = smoothstep(8.0, 5.0, bf1) * smoothstep(2.5, 5.0, bf1) * smoothstep(0.86, 0.95, btone)
    rgb = tint(rgb, blister * 0.45, (0.150, 0.158, 0.172))
    rgb = tint(rgb, blister * 0.55, (0.290, 0.300, 0.320))
    rgb = tint(rgb, blister_rim * 0.50, (0.420, 0.428, 0.445))
    height = height + blister * 0.55 + blister_rim * 0.20

    # ---- broken splits ----------------------------------------------------
    sp = ridged(h, w, SEED + 69, octaves=4, fy=16, fx=16)
    allow = smoothstep(0.48, 0.82, fbm(h, w, SEED + 70, octaves=3, fy=8, fx=8))
    width = fbm(h, w, SEED + 71, octaves=3, fy=32, fx=32)
    split = smoothstep(0.94, 1.0, sp) * allow * smoothstep(0.30, 0.75, width)
    rgb = tint(rgb, split * 0.60, (0.012, 0.014, 0.018))
    rgb = tint(rgb, split * smoothstep(0.55, 0.95, grit) * 0.28, (0.320, 0.326, 0.340))
    height = height - split * 0.30

    # ---- wet sheen: standing water with a broad sky reflection ------------
    # A multi-octave field, not one coarse lattice: a single lattice would
    # draw its own grid and the pools would read as square tiles.
    wet_f = fbm(h, w, SEED + 72, octaves=6, fy=28, fx=18)
    wet = smoothstep(0.50, 0.66, wet_f)
    pool_edge = smoothstep(0.50, 0.55, wet_f) * smoothstep(0.66, 0.60, wet_f)
    rgb = tint(rgb, wet * 0.45, (0.030, 0.038, 0.052))
    # a glossy, directional reflection in the wet areas: tar roofs read wet
    # from the SPECULAR response, not from being dark
    rgb = tint(rgb, smoothstep(0.55, 0.90, wet) * 0.40, (0.330, 0.380, 0.450))
    rgb = tint(rgb, pool_edge * 0.50, (0.560, 0.610, 0.680))
    gloss = smoothstep(0.80, 0.97, fbm(h, w, SEED + 76, octaves=3, fy=64, fx=64))
    rgb = tint(rgb, gloss * wet * 0.45, (0.720, 0.780, 0.860))
    height = height - wet * 0.06

    moss = smoothstep(0.66, 0.86, fbm(h, w, SEED + 73, octaves=4, fy=32, fx=9))
    rgb = tint(rgb, moss * 0.42, TAR_FOREST)
    rgb = tint(rgb, smoothstep(0.80, 0.94, fbm(h, w, SEED + 74, octaves=3, fy=16, fx=5)) * 0.24,
               (0.330, 0.360, 0.300))

    g = grime(h, w, SEED + 75, strength=0.25, fy=16, fx=5)
    rgb = tint(rgb, g * 0.35, (0.195, 0.192, 0.180))
    rgb = np.clip(rgb + (grit[:, :, None] - 0.5) * 0.035, 0, 1)
    rgb = np.clip(rgb, 0, 1)

    rough = 0.86 - 0.44 * wet - 0.12 * lip_r + 0.10 * (base - 0.5)
    rough = np.clip(rough, 0.16, 0.99)

    rgb = bake(rgb, height, strength=2.2, ambient=0.44, gain=0.76)
    return rgb, rough, height


def tex_wood():
    """Weathered dock planks: silvered boards, water-filled gaps, knots and
    rusted nail heads."""
    h = w = SIZE
    Y = np.arange(h, dtype=np.int64)[:, None]
    X = np.arange(w, dtype=np.int64)[None, :]
    plank_h = 256
    gap = 6
    r = Y // plank_h
    by = (Y % plank_h).astype(np.float32)
    pid = r * 100003 + 0

    # Grain from a RIDGED field stretched along the board. The boards run
    # horizontally, so the field must vary quickly ACROSS them (y) and
    # slowly ALONG them (x): that puts the streaks lengthwise.
    gfield = fbm_aniso(h, w, SEED + 81, octaves=5, fy=96, fx=2, fx_grow=1.0)
    phase = hash_int(r * 100003 + 3, SEED + 92)          # (h, 1), per board
    gfield = gfield + phase * 0.53
    streaks = 1.0 - np.abs(gfield * 2.0 - 1.0)           # ridged: sharp crests
    grain_line = smoothstep(0.45, 0.94, streaks)
    # a second, finer set of fibres
    fibre = fbm_aniso(h, w, SEED + 82, octaves=3, fy=48, fx=2, fx_grow=1.0)
    knot_f = fbm(h, w, SEED + 83, octaves=3, fy=8, fx=8)

    tone = hash_int(pid, SEED + 84)
    rgb = np.zeros((h, w, 3), np.float32)
    rgb[:, :, 0] = WOOD_BROWN[0] + (tone - 0.5) * 0.09
    rgb[:, :, 1] = WOOD_BROWN[1] + (tone - 0.5) * 0.07
    rgb[:, :, 2] = WOOD_BROWN[2] + (tone - 0.5) * 0.06
    rgb = tint(rgb, smoothstep(0.45, 0.85, tone) * 0.85, WOOD_SAGE)
    rgb = tint(rgb, smoothstep(0.28, 0.06, tone) * 0.80, WOOD_DARK)
    # the dark late-wood grain lines, and the pale early-wood between them
    rgb = tint(rgb, grain_line * 0.62, WOOD_DARK)
    rgb = tint(rgb, (1.0 - grain_line) * 0.30, (0.480, 0.460, 0.415))
    rgb = np.clip(rgb + (fibre - 0.5)[:, :, None] * 0.09, 0, 1)

    # ---- knots: a few per board, each with concentric growth rings --------
    # Knots are PLACED, not taken from a Voronoi cell: a per-cell tone on a
    # coarse lattice draws the lattice itself and the board reads as a grid
    # of panels.
    knot = np.zeros((h, w), np.float32)
    knot_rim = np.zeros((h, w), np.float32)
    for rr in range(h // plank_h):
        row = rr * plank_h
        n_knots = int(hash_int(np.array([rr]), SEED + 95)[0] * 2.4)
        for kk in range(n_knots):
            kx = int(hash_int(np.array([rr * 3 + kk]), SEED + 96)[0] * w) % w
            ky = (row + int(hash_int(np.array([rr * 7 + kk]), SEED + 97)[0] *
                             (plank_h - 24)) + 12) % h
            rad = 9.0 + 13.0 * hash_int(np.array([rr * 5 + kk]), SEED + 98)[0]
            # distance with wrap, so a knot near the edge stays continuous
            dx = np.minimum(np.abs(X.astype(np.float32) - kx), w - np.abs(X.astype(np.float32) - kx))
            dy = np.minimum(np.abs(Y.astype(np.float32) - ky), h - np.abs(Y.astype(np.float32) - ky))
            dd = np.sqrt(dx * dx + dy * dy)
            # concentric growth rings fanning out of the knot
            rings_k = np.abs(np.sin(dd / max(rad, 1e-3) * np.pi))
            knot = np.maximum(knot, smoothstep(rad * 1.9, rad * 0.5, dd) *
                              (0.35 + 0.65 * rings_k))
            knot_rim = np.maximum(knot_rim, smoothstep(rad * 2.1, rad * 1.5, dd) *
                                  smoothstep(rad * 0.9, rad * 1.5, dd) * 0.8)
    rgb = tint(rgb, knot * 0.80, WOOD_DARK)
    rgb = tint(rgb, knot_rim * 0.40, (0.240, 0.190, 0.150))

    # ---- gaps between planks, with water standing in them -----------------
    # Each plank is a separate board: give it its own grain contrast and
    # tone so the boards read as individual timbers, not one striped sheet.
    # r is (h, 1): one plank per row, so this broadcasts across the row
    board_contrast = 0.70 + 0.60 * hash_int(r * 100003 + 7, SEED + 89)
    grain_line = (grain_line - 0.5) * board_contrast + 0.5
    fibre = (fibre - 0.5) * board_contrast + 0.5
    in_gap = (by < gap) | (by > plank_h - gap)
    rgb = tint(rgb, in_gap.astype(np.float32) * 0.90, (0.055, 0.060, 0.062))
    # standing water in the gap: a dark trough with a bright sky reflection
    # along its length, which is what makes a gap read as WET
    gap_core = smoothstep(gap, 0.0, by) + smoothstep(plank_h - gap, plank_h, by)
    gap_core = np.clip(gap_core, 0, 1)
    wet_line = smoothstep(0.45, 0.85, fbm_aniso(h, w, SEED + 92, octaves=3, fy=8, fx=2))
    rgb = tint(rgb, gap_core * 0.60, (0.075, 0.088, 0.098))
    rgb = tint(rgb, gap_core * wet_line * 0.70, (0.430, 0.480, 0.530))
    # a bright meniscus right at the edge of the water line
    rgb = tint(rgb, gap_core * (1.0 - wet_line) * 0.30, (0.170, 0.190, 0.205))
    height = (grain_line - 0.5) * 0.16 + (fibre - 0.5) * 0.06
    height = height - in_gap.astype(np.float32) * 0.70
    height = height - knot * 0.35 + knot_rim * 0.10
    height = height - gap_core * 0.20

    # ---- nail heads, two per plank near the ends --------------------------
    # Nails are stamped with wrap-around so a head at the texture edge is
    # continued on the opposite edge instead of being cut in half.
    nails = np.zeros((h, w), np.float32)
    rust = np.zeros((h, w), np.float32)
    nail_r = 7.0

    def stamp_disc(field, cx, cy, r0, fn):
        r0 = int(r0)
        yy = (np.arange(cy - r0 - 1, cy + r0 + 2) % h).astype(np.int64)
        xx = (np.arange(cx - r0 - 1, cx + r0 + 2) % w).astype(np.int64)
        dd = np.sqrt((yy[:, None] - cy) ** 2 + (xx[None, :] - cx) ** 2)
        np.maximum.at(field, (yy[:, None], xx[None, :]), fn(dd))

    for rr in range(h // plank_h):
        row = rr * plank_h
        for pos in (0.08, 0.36, 0.64, 0.92):
            # each nail gets its own position along the board: a fixed set of
            # x values would stack every head into one vertical column
            jx = hash_int(np.array([rr * 11 + int(pos * 100)]), SEED + 87)[0]
            jy2 = hash_int(np.array([rr * 5 + int(pos * 100)]), SEED + 88)[0]
            cx = int((pos + (jx - 0.5) * 0.10) * w) % w
            cy = (row + int(plank_h * (0.22 + 0.56 * jy2))) % h
            stamp_disc(nails, cx, cy, nail_r,
                       lambda d: smoothstep(nail_r, nail_r - 1.6, d))
            stamp_disc(rust, cx, cy, nail_r + 5,
                       lambda d: smoothstep(nail_r + 5.0, nail_r, d) *
                       smoothstep(nail_r - 1.0, nail_r + 1.0, d))
    # a nail head is a bright steel disc in a rusty socket: the specular
    # cap and the rust ring are what make it read as a nail
    rgb = tint(rgb, nails * 0.55, (0.140, 0.135, 0.130))
    rgb = tint(rgb, nails * 0.40, (0.360, 0.365, 0.370))
    rgb = tint(rgb, rust * 0.65, WOOD_RUST)
    height = height + nails * 0.26

    # ---- algae rot at the plank edges and in the gaps ---------------------
    rot = smoothstep(0.58, 0.88, fbm(h, w, SEED + 89, octaves=4, fy=16, fx=16))
    edge_rot = np.clip(smoothstep(plank_h * 0.42, plank_h * 0.5, by), 0, 1)
    rgb = tint(rgb, rot * (0.35 + 0.65 * edge_rot) * 0.55, WOOD_MINT)
    rgb = tint(rgb, rot * in_gap.astype(np.float32) * 0.40, (0.210, 0.300, 0.215))

    # water staining along the grain: it has to run LENGTHWISE, so the
    # field must vary quickly across the board (y) and slowly along it (x)
    stain = smoothstep(0.56, 0.84, fbm(h, w, SEED + 90, octaves=4, fy=32, fx=4))
    rgb = tint(rgb, stain * 0.38, (0.150, 0.140, 0.125))

    g = grime(h, w, SEED + 91, strength=0.30, fy=4, fx=4)
    rgb = tint(rgb, g * 0.38, (0.140, 0.138, 0.128))
    rgb = np.clip(rgb, 0, 1)

    rough = 0.82 - 0.22 * stain - 0.10 * rot + 0.08 * (grain_line - 0.5)
    rough = np.clip(rough + in_gap.astype(np.float32) * 0.08, 0.30, 0.99)

    rgb = bake(rgb, height, strength=2.2, ambient=0.42, gain=0.78)
    return rgb, rough, height


BUILDERS = {
    'T_Floor_Concrete_Wet': tex_concrete,
    'T_Wall_Brick_Old': tex_brick,
    'T_Wall_Steel_Rusted': tex_steel,
    'T_Ground_Gravel': tex_gravel,
    'T_Roof_Tar': tex_tar,
    'T_Wood_Plank_Dock': tex_wood,
}

PALETTE = {
    'T_Floor_Concrete_Wet': [hexof(CONCRETE_BASE), hexof(CONCRETE_CHIP_PALE),
                             hexof(CONCRETE_CHIP_DARK), hexof(CONCRETE_WET), hexof(CONCRETE_MINT)],
    'T_Wall_Brick_Old': [hexof(BRICK_OXBLOOD), hexof(BRICK_PALE), hexof(BRICK_DARK),
                         hexof(BRICK_MORTAR), hexof(BRICK_SAGE)],
    'T_Wall_Steel_Rusted': [hexof(STEEL_BASE), hexof(STEEL_RUST), hexof(STEEL_RUST_DEEP),
                            hexof(STEEL_FOREST)],
    'T_Ground_Gravel': [hexof(GRAVEL_BASE), hexof(GRAVEL_PALE), hexof(GRAVEL_DARK),
                        hexof(GRAVEL_MINT), hexof(GRAVEL_WET)],
    'T_Roof_Tar': [hexof(TAR_BASE), hexof(TAR_GRIT), hexof(TAR_SEAM), hexof(TAR_FOREST),
                   hexof(TAR_WET)],
    'T_Wood_Plank_Dock': [hexof(WOOD_SAGE), hexof(WOOD_BROWN), hexof(WOOD_DARK),
                          hexof(WOOD_MINT), hexof(WOOD_RUST)],
}

NOTES = {
    'T_Floor_Concrete_Wet': 'Wet harbour concrete: neutral cold-grey cement paste with exposed light and dark angular aggregate, round air voids, broken cracks, vertical drainage streaks and glossy pooling. Mint algae only in damp patches. Wetness reads through sheen and pooling, not hue.',
    'T_Wall_Brick_Old': 'Old oxblood harbour brick (the set oxblood carrier): running bond with individually varied brick tone, chipped arrises, recessed lime mortar with shadow under each course, soot and vertical water staining, sage salt bloom.',
    'T_Wall_Steel_Rusted': 'Rusted steel plate: rolled panel seams, domed rivet grid, ochre rust with ragged voronoi patch edges bleeding downward, corrosion pitting, forest algae on old rust.',
    'T_Ground_Gravel': 'Wet harbour gravel: individual rounded stones of two sizes with per-stone tone and domed relief, water pooled in the gaps, mint moss in the damp hollows.',
    'T_Roof_Tar': 'Tar roof: rolled seams, patch repairs, embedded angular grit, tar blisters, broken splits, cold puddle sheen, forest moss in the splits.',
    'T_Wood_Plank_Dock': 'Weathered dock planks: silvered sage boards with directional grain, knots, water-filled gaps, rusted nail heads, green algae rot at the plank edges.',
}

WORLD_M = 4.0


# ==================================================================== font
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
    '(': ('.#.', '#..', '#..', '#..', '.#.'), ')': ('.#.', '..#', '..#', '..#', '.#.'),
    '+': ('...', '.#.', '###', '.#.', '...'), ',': ('...', '...', '...', '.#.', '#..'),
}


def draw_text(canvas, x, y, text, scale=3, color=(235, 235, 225)):
    """Blit bitmap text onto a uint8 HxWx3 canvas."""
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[' '])
        for gy in range(5):
            row = glyph[gy]
            for gx in range(3):
                if row[gx] == '#':
                    y0 = y + gy * scale
                    x0 = cx + gx * scale
                    if 0 <= y0 < canvas.shape[0] - scale and 0 <= x0 < canvas.shape[1] - scale:
                        canvas[y0:y0 + scale, x0:x0 + scale] = color
        cx += 4 * scale
    return cx


def downscale(arr_u8, target):
    """Box-filter downscale of a uint8 image."""
    h, w = arr_u8.shape[0], arr_u8.shape[1]
    fy = h // target
    fx = w // target
    a = arr_u8[:target * fy, :target * fx].astype(np.float32)
    a = a.reshape(target, fy, target, fx, arr_u8.shape[2]).mean(axis=(1, 3))
    return a.astype(np.uint8)


# ==================================================================== driver
def render(name, fn):
    rgb, rough, height = fn()
    diff = to_u8(rgb)
    norm = to_u8(normal_from_height(height))
    rgh = to_u8(gray(rough))
    del rgb, rough, height
    contact = contact_sheet(diff)

    save_png(name, diff, os.path.join(OUT, name + '.png'))
    save_png(name + '_normal', norm, os.path.join(OUT, name + '_normal.png'), non_color=True)
    save_png(name + '_rough', rgh, os.path.join(OUT, name + '_rough.png'), non_color=True)
    save_png(name + '_contact', contact, os.path.join(OUT, name + '_contact.png'))
    del contact, norm, rgh

    crops = []
    for i, (oy, ox) in enumerate(pick_crop_windows(diff)):
        c = diff[oy:oy + CROP, ox:ox + CROP]
        fn2 = '%s_crop%d.png' % (name, i + 1)
        save_png('%s_crop%d' % (name, i + 1), c, os.path.join(OUT, fn2))
        crops.append(fn2)

    disk = decode_png(os.path.join(OUT, name + '.png'))
    err = int(np.abs(disk.astype(np.int32) - diff.astype(np.int32)).max())
    del disk
    return diff, crops, err


def build_trim_sheet():
    """4096x4096 trim sheet built from the files actually on disk.

    Every material appears as DIFFUSE / NORMAL / ROUGHNESS / CONTACT, each
    labelled with its name and index, so a level designer can pick from one
    file. Thumbnails are box-filtered down, so only one 2048 image is held
    in memory at a time.
    """
    side = 4096
    cell = 512
    sheet = np.zeros((side, side, 3), np.uint8)
    sheet[:, :] = (14, 16, 18)
    kinds = [('DIFFUSE', ''), ('NORMAL', '_normal'), ('ROUGH', '_rough'), ('CONTACT', '_contact')]
    label_x = 56
    col_w = cell + 28
    row_h = cell + 96

    draw_text(sheet, label_x, 40, 'THE COMMANDER - TEXTURE TRIM SHEET', 5, (150, 210, 180))
    draw_text(sheet, label_x, 90, '6 MATERIALS - 2048 PX - 4 MAPS EACH - 1 TO 6', 3, (120, 150, 140))
    draw_text(sheet, 3000, 40, 'PLYMOUTH MA HARBOUR', 3, (120, 150, 140))

    for col, name in enumerate(MATERIALS):
        x0 = label_x + col * col_w
        idx = col + 1
        # material header: index badge + name
        sheet[140:190, x0:x0 + 40] = (36, 60, 48)
        draw_text(sheet, x0 + 12, 152, str(idx), 6, (170, 225, 195))
        draw_text(sheet, x0 + 52, 148, name.replace('T_', '').replace('_', ' '), 3, (225, 225, 215))
        draw_text(sheet, x0 + 52, 168, 'DIFFUSE NORMAL ROUGH CONTACT', 2, (120, 150, 140))
        for row, (kind, suffix) in enumerate(kinds):
            y0 = 220 + row * (cell + 24)
            px = readback_raw(os.path.join(OUT, name + suffix + '.png'))
            thumb = downscale(px, cell)
            del px
            sheet[y0:y0 + cell, x0:x0 + cell] = thumb
            draw_text(sheet, x0, y0 + cell + 6, kind, 2, (150, 175, 165))
            # 1px frame so each cell reads as a separate swatch
            sheet[y0 - 2:y0, x0 - 2:x0 + cell + 2] = (70, 76, 78)
            sheet[y0 + cell:y0 + cell + 2, x0 - 2:x0 + cell + 2] = (70, 76, 78)
            sheet[y0 - 2:y0 + cell + 2, x0 - 2:x0] = (70, 76, 78)
            sheet[y0 - 2:y0 + cell + 2, x0 + cell:x0 + cell + 2] = (70, 76, 78)
            del thumb

    # footer: palette key
    fy = 220 + 4 * (cell + 24) + 40
    draw_text(sheet, label_x, fy, 'PALETTE', 3, (150, 210, 180))
    for col, name in enumerate(MATERIALS):
        x0 = label_x + col * col_w
        for i, hx in enumerate(PALETTE[name]):
            r = int(hx[1:3], 16)
            g = int(hx[3:5], 16)
            b = int(hx[5:7], 16)
            sheet[fy + 30:fy + 54, x0 + i * 34:x0 + i * 34 + 30] = (r, g, b)
        draw_text(sheet, x0, fy + 60, name.replace('T_', '').replace('_', ' '), 2, (110, 135, 125))

    path = os.path.join(OUT, 'T_Set_TrimSheet.png')
    # written directly: a 4096^2 sheet is heavy to push through Blender's
    # pixel buffer, and the stdlib writer is byte-verified by selftest_bytes
    write_png_filter0(path, sheet)
    return path


def build_manifest():
    import json
    manifest = []
    for name in MATERIALS:
        files = [name + '.png', name + '_normal.png', name + '_rough.png', name + '_contact.png',
                 name + '_crop1.png', name + '_crop2.png', name + '_crop3.png']
        info = []
        for f in files:
            p = os.path.join(OUT, f)
            w, h, _d, _c = png_header(p)
            b = os.path.getsize(p)
            info.append({'file': f, 'width': w, 'height': h, 'bytes': b,
                         'kb': round(b / 1024.0, 1)})
        px = readback_raw(os.path.join(OUT, name + '.png'))
        mean, std = luma_stats(px)
        sx, sy, _wx, _ix, _wy, _iy = seam_metrics(px)
        del px
        manifest.append({
            'name': name,
            'files': files,
            'file_info': info,
            'kb': [i['kb'] for i in info],
            'notes': NOTES[name],
            'size': [SIZE, SIZE],
            'world_tile_m': WORLD_M,
            'texel_density_cm': round(WORLD_M * 100.0 / SIZE, 3),
            'palette_hex': PALETTE[name],
            'mean': round(mean, 2),
            'std': round(std, 2),
            'seam_ratio_x': round(sx, 3),
            'seam_ratio_y': round(sy, 3),
            'maps': {'diffuse': files[0], 'normal': files[1], 'roughness': files[2],
                     'contact_sheet': files[3], 'crops_1to1': files[4:7]},
        })
    trim = 'T_Set_TrimSheet.png'
    p = os.path.join(OUT, trim)
    w, h, _d, _c = png_header(p)
    b = os.path.getsize(p)
    manifest.append({
        'name': 'T_Set_TrimSheet',
        'files': [trim],
        'file_info': [{'file': trim, 'width': w, 'height': h, 'bytes': b,
                       'kb': round(b / 1024.0, 1)}],
        'kb': [round(b / 1024.0, 1)],
        'notes': 'Trim sheet: diffuse / normal / roughness / offset contact for all six '
                 'materials, labelled and indexed 1-6.',
        'size': [w, h],
    })
    mpath = os.path.join(OUT, 'textures_manifest.json')
    with open(mpath, 'w') as f:
        json.dump(manifest, f, indent=1)
    return mpath, manifest


def main():
    d1, d2 = selftest_bytes(OUT)
    if d1 != 0 or d2 != 0:
        print('[TEXTURE] FATAL: decode path is not byte-exact (%d, %d)' % (d1, d2))
        return

    for name in MATERIALS:
        # resume: a material whose full set already exists on disk is not
        # re-rendered (Blender's PNG encoder is the slow part of a run)
        want = [name + s for s in ('', '_normal', '_rough', '_contact',
                                   '_crop1', '_crop2', '_crop3')]
        if all(os.path.exists(os.path.join(OUT, f + '.png')) for f in want):
            px = readback_raw(os.path.join(OUT, name + '.png'))
            mean, std = luma_stats(px)
            sx, sy, _a, _b, _c, _d = seam_metrics(px)
            del px
            print('[TEXTURE] %-22s mean=%6.2f std=%6.2f seam x=%.2f y=%.2f (cached)'
                  % (name, mean, std, sx, sy), flush=True)
            continue
        diff, crops, err = render(name, BUILDERS[name])
        mean, std = luma_stats(diff)
        sx, sy, _a, _b, _c, _d = seam_metrics(diff)
        print('[TEXTURE] %-22s mean=%6.2f std=%6.2f seam x=%.2f y=%.2f crops=%d byte_err=%d'
              % (name, mean, std, sx, sy, len(crops), err), flush=True)
        del diff
        # each material holds several 2048x2048 float buffers; release them
        # before the next one or the process runs out of address space
        gc.collect()

    trim = build_trim_sheet()
    tw, th, _d, _c = png_header(trim)
    print('[TEXTURE] TRIM SHEET %dx%d %.1fKB' % (tw, th, os.path.getsize(trim) / 1024.0))

    mpath, manifest = build_manifest()
    print('[TEXTURE] MANIFEST %s (%d entries)' % (mpath, len(manifest)))

    if COPY_TO:
        import shutil
        os.makedirs(COPY_TO, exist_ok=True)
        src = sorted(f for f in os.listdir(OUT) if f.lower().endswith(('.png', '.json')))
        for f in src:
            shutil.copy2(os.path.join(OUT, f), os.path.join(COPY_TO, f))
        dst = sorted(f for f in os.listdir(COPY_TO) if f.lower().endswith(('.png', '.json')))
        print('[TEXTURE] MIRROR src=%d dst=%d match=%s' % (len(src), len(dst), src == dst))

    rows = []
    for entry in manifest:
        for i in entry['file_info']:
            w, h = i['width'], i['height']
            f = i['file']
            if '_crop' in f:
                verdict = 'PASS-CROP-1024-1to1' if (w == CROP and h == CROP) else 'FAIL'
            elif f == 'T_Set_TrimSheet.png':
                verdict = 'PASS-TRIM' if (w >= 2048 and h >= 2048) else 'FAIL'
            else:
                verdict = 'PASS' if (w == SIZE and h == SIZE) else 'FAIL'
            rows.append((f, w, h, i['kb'], verdict))
    for f, w, h, kb, v in rows:
        print('[TEXTURE] %-38s %4dx%-4d %8.1fKB  %s' % (f, w, h, kb, v))
    fails = [r for r in rows if r[4] == 'FAIL']
    print('[TEXTURE] dimension summary: %d files checked, %d FAIL' % (len(rows), len(fails)))
    for r in fails:
        print('[TEXTURE] FAIL %s %dx%d' % (r[0], r[1], r[2]))
    print('[TEXTURE] DONE')


if __name__ == '__main__':
    main()
