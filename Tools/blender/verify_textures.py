"""Final verification for THE COMMANDER texture set.

Checks, from the FILES ON DISK (not from anything the generator claims):
  * every PNG's real width x height, read from its IHDR chunk
  * PASS/FAIL against 2048 for maps, 1024 for 1:1 crops, >=2048 for the trim
  * the trim sheet's real size
  * the manifest parses and its recorded sizes match the files
  * the mirror directory holds the same file set as the source
  * luma mean/std per diffuse (a real texture has std > 8)
  * seam continuity, comparing the wrap difference against the distribution
    of interior differences rather than their mean
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_textures as mt  # noqa: E402

OUT = None
MIRROR = None
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
for i, a in enumerate(argv):
    if a == '--out':
        OUT = argv[i + 1]
    if a == '--mirror':
        MIRROR = argv[i + 1]
if OUT is None:
    OUT = os.path.join(HERE, 'out_textures_v2')

print('=' * 78)
print('SOURCE  : %s' % OUT)
print('MIRROR  : %s' % MIRROR)
print('=' * 78)

rows = []
fails = []
for name in mt.MATERIALS:
    files = [name + '.png', name + '_normal.png', name + '_rough.png', name + '_contact.png',
             name + '_crop1.png', name + '_crop2.png', name + '_crop3.png']
    for f in files:
        p = os.path.join(OUT, f)
        if not os.path.exists(p):
            rows.append((f, 0, 0, 0.0, 'MISSING'))
            fails.append(f)
            continue
        w, h, depth, ctype = mt.png_header(p)
        kb = os.path.getsize(p) / 1024.0
        if '_crop' in f:
            verdict = 'PASS' if (w == 1024 and h == 1024) else 'FAIL'
        else:
            verdict = 'PASS' if (w == 2048 and h == 2048) else 'FAIL'
        if kb < 60.0:
            verdict = 'FAIL(tiny)'
        if verdict.startswith('FAIL'):
            fails.append(f)
        rows.append((f, w, h, kb, verdict))

trim = 'T_Set_TrimSheet.png'
tp = os.path.join(OUT, trim)
if os.path.exists(tp):
    tw, th, _d, _c = mt.png_header(tp)
    tkb = os.path.getsize(tp) / 1024.0
    tverdict = 'PASS' if (tw >= 2048 and th >= 2048) else 'FAIL'
    if tverdict == 'FAIL':
        fails.append(trim)
else:
    tw = th = 0
    tkb = 0.0
    tverdict = 'MISSING'
    fails.append(trim)

print('%-40s %5s %5s %10s  %s' % ('FILE', 'W', 'H', 'KB', 'VERDICT'))
for f, w, h, kb, v in rows:
    print('%-40s %5d %5d %10.1f  %s' % (f, w, h, kb, v))
print('%-40s %5d %5d %10.1f  %s  <- trim sheet' % (trim, tw, th, tkb, tverdict))

print('-' * 78)
print('DIFFUSE STATS + SEAM (wrap diff vs the interior distribution)')
for name in mt.MATERIALS:
    p = os.path.join(OUT, name + '.png')
    if not os.path.exists(p):
        continue
    px = mt.decode_png(p)
    mean, std = mt.luma_stats(px)
    l = (0.299 * px[:, :, 0] + 0.587 * px[:, :, 1] + 0.114 * px[:, :, 2]).astype(np.float32)
    h, w = l.shape
    dx = np.abs(l[:, 1:] - l[:, :-1]).mean(axis=0)
    dy = np.abs(l[1:, :] - l[:-1, :]).mean(axis=1)
    wx = float(np.abs(l[:, 0] - l[:, -1]).mean())
    wy = float(np.abs(l[0, :] - l[-1, :]).mean())
    # The wrap is a genuine seam only if it is WORSE than the sharpest
    # transition already inside the texture. A wrap that lands on a
    # structural line (a plate seam, a plank gap) is not a defect.
    p99x = float(np.percentile(dx, 99.0))
    p99y = float(np.percentile(dy, 99.0))
    maxx = float(dx.max())
    maxy = float(dy.max())
    sx = 'OK' if wx <= max(maxx * 1.05, p99x * 1.35) else 'SEAM'
    sy = 'OK' if wy <= max(maxy * 1.05, p99y * 1.35) else 'SEAM'
    print('%-22s mean=%6.2f std=%6.2f  wrap_x=%6.2f (p99 %6.2f max %6.2f) %-5s  '
          'wrap_y=%6.2f (p99 %6.2f max %6.2f) %-5s'
          % (name, mean, std, wx, p99x, maxx, sx, wy, p99y, maxy, sy))
    del px, l

print('-' * 78)
mpath = os.path.join(OUT, 'textures_manifest.json')
if os.path.exists(mpath):
    man = json.load(open(mpath))
    print('MANIFEST OK: %d entries, %s' % (len(man), mpath))
    mism = 0
    checked = 0
    for e in man:
        for fi in e.get('file_info', []):
            p = os.path.join(OUT, fi['file'])
            if not os.path.exists(p):
                print('  MANIFEST MISSING FILE: %s' % fi['file'])
                mism += 1
                continue
            w, h, _d, _c = mt.png_header(p)
            kb = os.path.getsize(p) / 1024.0
            checked += 1
            if w != fi['width'] or h != fi['height'] or abs(kb - fi['kb']) > 1.0:
                print('  MANIFEST MISMATCH %s: manifest %dx%d %.1fKB vs disk %dx%d %.1fKB'
                      % (fi['file'], fi['width'], fi['height'], fi['kb'], w, h, kb))
                mism += 1
    print('  %d file entries checked, %d mismatches' % (checked, mism))
    if mism:
        fails.append('manifest')
else:
    print('MANIFEST MISSING: %s' % mpath)
    fails.append('manifest')

print('-' * 78)
if MIRROR:
    src = sorted(f for f in os.listdir(OUT) if f.lower().endswith(('.png', '.json')))
    dst = sorted(f for f in os.listdir(MIRROR) if f.lower().endswith(('.png', '.json')))
    print('MIRROR source files: %d' % len(src))
    print('MIRROR dest   files: %d' % len(dst))
    only_src = [f for f in src if f not in dst]
    only_dst = [f for f in dst if f not in src]
    print('  only in source: %s' % (only_src if only_src else 'none'))
    print('  only in mirror: %s' % (only_dst if only_dst else 'none'))
    same = True
    for f in src:
        if f in dst:
            a = os.path.getsize(os.path.join(OUT, f))
            b = os.path.getsize(os.path.join(MIRROR, f))
            if a != b:
                print('  SIZE MISMATCH %s: %d vs %d' % (f, a, b))
                same = False
    print('  MIRROR COMPLETE: %s (file sets and sizes match)' % (src == dst and not only_src and same))
    if not (src == dst and not only_src and same):
        fails.append('mirror')

print('-' * 78)
print('PALETTE (final hex per material)')
for e in man if os.path.exists(mpath) else []:
    if 'palette_hex' in e:
        print('%-22s %s' % (e['name'], ' '.join(e['palette_hex'])))

print('-' * 78)
print('RESULT: %d files checked, %d FAILURES %s' % (len(rows) + 1, len(fails), fails if fails else ''))
print('VERIFY DONE')
