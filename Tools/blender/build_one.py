"""Run one material builder and report any exception verbatim."""
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_textures as mt  # noqa: E402

name = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'T_Wood_Plank_Dock'
print('BUILDING %s' % name, flush=True)
try:
    rgb, rough, height = mt.BUILDERS[name]()
    print('OK rgb=%s rough=%s height=%s' % (rgb.shape, rough.shape, height.shape), flush=True)
    print('mean=%.2f std=%.2f' % mt.luma_stats(mt.to_u8(rgb)), flush=True)
except Exception:
    traceback.print_exc()
    sys.stdout.flush()
    sys.exit(1)
print('SINGLE DONE')
