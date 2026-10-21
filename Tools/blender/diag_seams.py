"""Diagnose wrap seams in the v2 texture set (run inside Blender)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_textures_v2 as mt  # noqa: E402

OUT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.path.join(HERE, 'out_textures_v2')

for name in mt.MATERIALS:
    p = os.path.join(OUT, name + '.png')
    if not os.path.exists(p):
        print('MISSING %s' % name)
        continue
    px = mt.decode_png(p)
    l = (0.299 * px[:, :, 0] + 0.587 * px[:, :, 1] + 0.114 * px[:, :, 2]).astype(np.float32)
    h, w = l.shape
    dx = np.abs(l[:, 1:] - l[:, :-1]).mean(axis=0)   # per-column interior jump
    dy = np.abs(l[1:, :] - l[:-1, :]).mean(axis=1)   # per-row interior jump
    wrap_x = float(np.abs(l[:, 0] - l[:, -1]).mean())
    wrap_y = float(np.abs(l[0, :] - l[-1, :]).mean())
    med_x = float(np.median(dx))
    med_y = float(np.median(dy))
    # biggest interior jump, for reference (a real texture has some)
    print('%-22s wrap_x=%6.2f (median interior col jump %5.2f)  wrap_y=%6.2f (median row %5.2f)'
          % (name, wrap_x, med_x, wrap_y, med_y))
    print('    top column jumps: %s' % ', '.join(
        'c%d=%.1f' % (i, v) for i, v in sorted(enumerate(dx), key=lambda t: -t[1])[:5]))
    print('    top row jumps:    %s' % ', '.join(
        'r%d=%.1f' % (i, v) for i, v in sorted(enumerate(dy), key=lambda t: -t[1])[:5]))
    # how much of the wrap difference comes from a single column band?
    band = np.abs(l[:, 0] - l[:, -1])
    print('    wrap diff: mean=%.2f p90=%.2f max=%.2f' % (
        band.mean(), np.percentile(band, 90), band.max()))
    del px, l
print('DIAG DONE')
