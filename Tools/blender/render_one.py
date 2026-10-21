"""Render one material and write its files.

Used to keep peak memory down: the full run holds too many 2048x2048 float
buffers at once, so the heavy materials are rendered in separate processes.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_textures_v2 as mt  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
# skip flags AND their values (--out <dir>); the material name is the first
# remaining bare word
name = None
skip_next = False
for a in argv:
    if skip_next:
        skip_next = False
        continue
    if a.startswith('--'):
        skip_next = True
        continue
    name = a
    break
if name is None:
    raise SystemExit('usage: render_one.py -- <material name>')
print('RENDERING %s -> %s' % (name, mt.OUT), flush=True)
try:
    diff, crops, err = mt.render(name, mt.BUILDERS[name])
    mean, std = mt.luma_stats(diff)
    print('[TEXTURE] %-22s mean=%6.2f std=%6.2f crops=%d byte_err=%d'
          % (name, mean, std, len(crops), err), flush=True)
except Exception:
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
    raise
print('ONE DONE', flush=True)
