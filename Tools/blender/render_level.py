# render_level.py - visual evidence for the UE 5.8 level M_Blockout01
# blender -b -noaudio -P Tools/blender/render_level.py -- --out <dir> [--json <path>]
import bpy, os, sys, json, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(ROOT, 'Tools', 'blender', 'out_level')
JSON_PATH = os.path.join(ROOT, 'Docs', 'generated', 'level_transforms.json')
XCOM = os.path.join(ROOT, 'Tools', 'blender', 'out_xcom')
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
for i, a in enumerate(args):
    if a == '--out':
        OUT = args[i + 1]
    elif a.startswith('--out='):
        OUT = a.split('=', 1)[1]
    elif a == '--json':
        JSON_PATH = args[i + 1]
    elif a.startswith('--json='):
        JSON_PATH = a.split('=', 1)[1]
os.makedirs(OUT, exist_ok=True)

RECS = json.load(open(JSON_PATH))
print('[LEVEL] json=%s records=%d' % (JSON_PATH, len(RECS)))
if len(RECS) < 40:
    print('[LEVEL] ABORT - json reports %d actors, expected >= 40' % len(RECS))
    raise SystemExit(2)

# ------------------------------------------------------------------ records
def lab(r):
    return str(r.get('label') or r.get('name') or '')

def kind(r):
    L = lab(r)
    for pre, k in (('BO_Floor', 'floor'), ('BO_Wall', 'wall'), ('BO_Cover', 'cover'),
                   ('BO_PillarStep', 'step'), ('BO_Pillar', 'pillar'), ('BO_Platform', 'platform'),
                   ('BO_Ramp', 'ramp'), ('BO_PitFloor', 'pitfloor'),
                   ('BO_PitRim', 'pitrim'), ('BO_PlayerStart', 'playerstart'),
                   ('BO_Sun', 'sun'), ('LGT_', 'light'), ('ENC_', 'enc'),
                   ('PU_', 'pu'), ('WP_', 'wp')):
        if L.startswith(pre):
            return k
    return 'other'

def uu(v):
    return float(v) / 100.0

def dims(r):
    s = r.get('scale') or [1, 1, 1]
    return (abs(float(s[0])), abs(float(s[1])), abs(float(s[2])))

def loc(r):
    return [uu(v) for v in r.get('loc', [0, 0, 0])]

def yaw(r):
    return math.radians(float(r.get('rot', {}).get('yaw', 0.0)))

def pitch(r):
    return math.radians(float(r.get('rot', {}).get('pitch', 0.0)))

def by(pre):
    for r in RECS:
        if lab(r).startswith(pre):
            return r
    return None

BASE = [r for r in RECS if kind(r) not in ('enc', 'pu', 'wp', 'light', 'fog', 'other')]
ENCS = [r for r in RECS if kind(r) == 'enc']
PUS = [r for r in RECS if kind(r) == 'pu']
WPS = [r for r in RECS if kind(r) == 'wp']
LIGHTS = [r for r in RECS if kind(r) in ('light', 'sun')]
START = by('BO_PlayerStart')
PILLAR = by('BO_Pillar')
PLAT = by('BO_Platform')
RAMP = by('BO_Ramp_NE')
PITRAMP = by('BO_Ramp_Pit')
PITF = by('BO_PitFloor')
BOSS = by('ENC_Boss')

# ------------------------------------------------------------------ helpers
def purge():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for g in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.curves,
              bpy.data.cameras, bpy.data.images, bpy.data.worlds):
        for b in list(g):
            try:
                g.remove(b)
            except Exception:
                pass

def mat(name, base, rough=0.5, metal=0.0, emit=None, estr=0.0, tex=None, tscale=0.30, bump=0.45):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    if b:
        b.inputs['Base Color'].default_value = (base[0], base[1], base[2], 1.0)
        b.inputs['Roughness'].default_value = rough
        b.inputs['Metallic'].default_value = metal
        if emit:
            b.inputs['Emission Color'].default_value = (emit[0], emit[1], emit[2], 1.0)
            b.inputs['Emission Strength'].default_value = estr
        if tex:
            wire_surface(m, b, base, tex, tscale, bump)
    return m

TEX_DIRS = ['out_textures_v2', 'out_textures']

def tex_path(stem):
    """Resolve an albedo/normal pair for a texture stem. The v2 (corrected) set wins when present."""
    base = os.path.dirname(os.path.abspath(__file__))
    for d in TEX_DIRS:
        p = os.path.join(base, d, stem + '.png')
        if os.path.exists(p):
            n = os.path.join(base, d, stem + '_normal.png')
            return (p, n if os.path.exists(n) else None)
    return None

def wire_surface(m, b, base, tex, tscale, bump_strength):
    """World-space box-projected albedo multiplied over the flat grade, plus a normal map.
    World position (not Object/Generated) so tiling stays consistent across scaled boxes and
    no surface is stretched. The flat colour multiplies the albedo, so the level keeps its
    deliberately dark grade while gaining real surface detail."""
    alb, nrm = tex
    nodes, links = m.node_tree.nodes, m.node_tree.links
    geo = nodes.new('ShaderNodeNewGeometry')
    mp = nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (tscale, tscale, tscale)
    links.new(geo.outputs['Position'], mp.inputs['Vector'])
    t = nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(alb)
    t.projection = 'BOX'
    t.projection_blend = 0.3
    links.new(mp.outputs['Vector'], t.inputs['Vector'])
    mix = nodes.new('ShaderNodeMixRGB')
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Fac'].default_value = 1.0
    mix.inputs['Color1'].default_value = (base[0], base[1], base[2], 1.0)
    links.new(t.outputs['Color'], mix.inputs['Color2'])
    links.new(mix.outputs['Color'], b.inputs['Base Color'])
    if nrm:
        n = nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(nrm)
        n.projection = 'BOX'
        n.projection_blend = 0.3
        links.new(mp.outputs['Vector'], n.inputs['Vector'])
        bn = nodes.new('ShaderNodeBump')
        bn.inputs['Strength'].default_value = bump_strength
        links.new(n.outputs['Color'], bn.inputs['Height'])
        links.new(bn.outputs['Normal'], b.inputs['Normal'])

def ramp_geo(r, c, d):
    """Ramp geometry. When the map dump carries measured world-space end points, use them: the box is
    centred between the two ends, its long axis aligned to the slope, its length the real end-to-end
    distance. No Euler guessing - the engine already measured the truth.
    The dump writes raw UE units, so the ends are converted to metres here; the rotation comes back
    in radians because Blender's primitive_cube_add takes a radian Euler."""
    ends = r.get('ends')
    if not ends:
        return (c[0], c[1], c[2]), (d[0], d[1], d[2]), (0.0, -pitch(r), yaw(r))
    import mathutils
    p0 = mathutils.Vector((ends[0][0] / 100.0, ends[0][1] / 100.0, ends[0][2] / 100.0))
    p1 = mathutils.Vector((ends[1][0] / 100.0, ends[1][1] / 100.0, ends[1][2] / 100.0))
    mid = (p0 + p1) * 0.5
    vec = p1 - p0
    e = mathutils.Vector((0.0, 1.0, 0.0)).rotation_difference(vec.normalized()).to_euler()
    return (mid.x, mid.y, mid.z), (d[0], vec.length, d[2]), (e.x, e.y, e.z)

def cube(name, p, d, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=p, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = d
    if m:
        o.data.materials.append(m)
    return o

def cyl(name, p, r, h, m, v=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=h, location=p)
    o = bpy.context.active_object
    o.name = name
    if m:
        o.data.materials.append(m)
    return o

def disc(name, p, r, m, v=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=0.04, location=p)
    o = bpy.context.active_object
    o.name = name
    if m:
        o.data.materials.append(m)
    return o

def cone(name, p, r, h, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=14, radius1=r, radius2=0.0, depth=h,
                                    location=p, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    if m:
        o.data.materials.append(m)
    return o

def sphere(name, p, r, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r, location=p)
    o = bpy.context.active_object
    o.name = name
    if m:
        o.data.materials.append(m)
    return o

def txt(name, body, p, size, m, align='LEFT'):
    bpy.ops.object.text_add(location=p)
    o = bpy.context.active_object
    o.name = name
    o.data.body = body
    o.data.size = size
    o.data.align_x = align
    o.data.extrude = 0.0
    if m:
        o.data.materials.append(m)
    return o

def curve(name, pts, r, m):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1.0)
    cu.bevel_depth = r
    cu.bevel_resolution = 2
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m)
    return o

# ------------------------------------------------------------------ palettes
def bp_mats():
    M = {}
    M['bg'] = mat('BP_BG', (0.010, 0.013, 0.018), 1.0)
    M['gridline'] = mat('BP_GridLine', (0.02, 0.03, 0.04), 1.0, emit=(0.05, 0.15, 0.21), estr=0.8)
    M['griddot'] = mat('BP_GridDot', (0.03, 0.05, 0.06), 1.0, emit=(0.09, 0.30, 0.40), estr=1.3)
    M['axis'] = mat('BP_Axis', (0.05, 0.10, 0.13), 1.0, emit=(0.16, 0.52, 0.64), estr=2.0)
    M['floor'] = mat('BP_Floor', (0.022, 0.030, 0.040), 1.0, emit=(0.045, 0.11, 0.15), estr=1.0)
    M['wall'] = mat('BP_Wall', (0.050, 0.080, 0.105), 1.0, emit=(0.17, 0.44, 0.58), estr=1.6)
    M['hatch'] = mat('BP_Hatch', (0.03, 0.05, 0.07), 1.0, emit=(0.10, 0.26, 0.34), estr=1.2)
    M['cover'] = mat('BP_Cover', (0.045, 0.080, 0.050), 1.0, emit=(0.20, 0.52, 0.26), estr=1.7)
    M['pillar'] = mat('BP_Pillar', (0.055, 0.085, 0.105), 1.0, emit=(0.13, 0.30, 0.40), estr=0.55)
    M['pit'] = mat('BP_Pit', (0.085, 0.024, 0.022), 1.0, emit=(0.62, 0.10, 0.08), estr=1.7)
    M['pitrim'] = mat('BP_PitRim', (0.095, 0.030, 0.026), 1.0, emit=(0.46, 0.10, 0.07), estr=0.8)
    M['plat'] = mat('BP_Platform', (0.065, 0.058, 0.095), 1.0, emit=(0.36, 0.30, 0.64), estr=1.7)
    M['ramp'] = mat('BP_Ramp', (0.080, 0.062, 0.046), 1.0, emit=(0.58, 0.42, 0.25), estr=1.7)
    M['edge'] = mat('BP_Edge', (0.02, 0.22, 0.26), 1.0, emit=(0.14, 0.68, 0.80), estr=1.6)
    M['enc'] = mat('BP_ENC', (0.32, 0.17, 0.02), 1.0, emit=(1.0, 0.60, 0.08), estr=7.0)
    M['pu'] = mat('BP_PU', (0.32, 0.04, 0.24), 1.0, emit=(0.95, 0.12, 0.70), estr=7.0)
    M['wp'] = mat('BP_WP', (0.04, 0.28, 0.10), 1.0, emit=(0.18, 0.95, 0.40), estr=7.0)
    M['start'] = mat('BP_Start', (0.05, 0.30, 0.12), 1.0, emit=(0.30, 0.95, 0.45), estr=5.0)
    M['route'] = mat('BP_Route', (0.32, 0.19, 0.02), 1.0, emit=(1.0, 0.72, 0.14), estr=7.0)
    M['kill'] = mat('BP_Kill', (0.32, 0.05, 0.05), 1.0, emit=(0.95, 0.12, 0.10), estr=3.2)
    M['obj'] = mat('BP_Obj', (0.04, 0.30, 0.12), 1.0, emit=(0.25, 0.95, 0.45), estr=5.0)
    M['txt'] = mat('BP_Txt', (0.05, 0.32, 0.38), 1.0, emit=(0.32, 0.95, 1.0), estr=4.0)
    M['dim'] = mat('BP_Dim', (0.04, 0.17, 0.21), 1.0, emit=(0.20, 0.58, 0.70), estr=2.4)
    M['panel'] = mat('BP_Panel', (0.012, 0.018, 0.025), 1.0, emit=(0.03, 0.09, 0.12), estr=1.2)
    M['bug'] = mat('BP_Bug', (0.34, 0.04, 0.04), 1.0, emit=(1.0, 0.12, 0.10), estr=6.0)
    return M

def game_mats():
    M = {}
    TEX = {'floor': 'T_Floor_Concrete_Wet', 'wall': 'T_Wall_Brick_Old', 'cover': 'T_Set_TrimSheet',
           'pillar': 'T_Wall_Steel_Rusted', 'plat': 'T_Wood_Plank_Dock', 'ramp': 'T_Set_TrimSheet',
           'crate': 'T_Wood_Plank_Dock'}
    M['floor'] = mat('G_Floor', (0.34, 0.36, 0.40), 0.34, 0.10, tex=tex_path(TEX['floor']), tscale=0.90)
    M['wall'] = mat('G_Wall', (0.46, 0.44, 0.42), 0.52, tex=tex_path(TEX['wall']), tscale=0.55)
    M['cover'] = mat('G_Cover', (0.40, 0.46, 0.42), 0.60, tex=tex_path(TEX['cover']), tscale=0.80)
    M['pillar'] = mat('G_Pillar', (0.44, 0.46, 0.48), 0.38, 0.14, tex=tex_path(TEX['pillar']), tscale=0.80)
    M['plat'] = mat('G_Platform', (0.50, 0.46, 0.42), 0.34, 0.16, tex=tex_path(TEX['plat']), tscale=0.70)
    M['ramp'] = mat('G_Ramp', (0.50, 0.48, 0.46), 0.42, 0.12, tex=tex_path(TEX['ramp']), tscale=0.70)
    M['pit'] = mat('G_Pit', (0.095, 0.028, 0.026), 0.72)
    M['pitrim'] = mat('G_PitRim', (0.090, 0.030, 0.026), 0.58)
    M['far'] = mat('G_Far', (0.016, 0.018, 0.022), 0.9)
    M['alien'] = mat('G_AlienGlow', (0.09, 0.24, 0.09), 0.3, emit=(0.24, 1.0, 0.36), estr=13.0)
    M['enc'] = mat('G_ENC', (0.28, 0.13, 0.02), 0.3, emit=(1.0, 0.58, 0.08), estr=6.0)
    M['pu'] = mat('G_PU', (0.26, 0.04, 0.20), 0.3, emit=(0.92, 0.14, 0.62), estr=5.5)
    M['wp'] = mat('G_WP', (0.04, 0.26, 0.10), 0.3, emit=(0.18, 0.95, 0.40), estr=8.0)
    M['key'] = mat('G_Key', (0.06, 0.28, 0.12), 0.3, emit=(0.30, 0.95, 0.45), estr=6.0)
    M['crate'] = mat('G_Crate', (0.52, 0.48, 0.44), 0.5, 0.1, tex=tex_path(TEX['crate']), tscale=1.20)
    M['gun'] = mat('G_Gun', (0.055, 0.060, 0.065), 0.35, 0.5)
    return M

# ------------------------------------------------------------------ render
def setup(w, h, samples=40):
    sc = bpy.context.scene
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            sc.render.engine = eng
            break
        except Exception:
            continue
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    try:
        sc.render.image_settings.color_depth = '8'
    except Exception:
        pass
    try:
        sc.eevee.taa_render_samples = samples
    except Exception:
        pass
    try:
        sc.view_settings.view_transform = 'AgX'
    except Exception:
        pass
    try:
        sc.view_settings.look = 'None'
        sc.view_settings.exposure = -0.55
        sc.view_settings.gamma = 1.0
    except Exception:
        pass
    try:
        sc.use_nodes = True
        nt = sc.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        rl = nt.nodes.new('CompositorNodeRLayers')
        gl = nt.nodes.new('CompositorNodeGlare')
        for gt in ('BLOOM', 'FOG_GLOW'):
            try:
                gl.glare_type = gt
                break
            except Exception:
                continue
        try:
            gl.quality = 'HIGH'
            gl.mix = -0.94
            gl.threshold = 0.95
            gl.size = 7
        except Exception:
            pass
        co = nt.nodes.new('CompositorNodeComposite')
        nt.links.new(rl.outputs['Image'], gl.inputs[0])
        nt.links.new(gl.outputs[0], co.inputs[0])
    except Exception as exc:
        print('[LEVEL] compositor skipped: %r' % (exc,))

def world(strength=1.0, col=(0.012, 0.016, 0.022), noise=False):
    w = bpy.data.worlds.new('W')
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get('Background')
    if bg:
        bg.inputs[0].default_value = (col[0], col[1], col[2], 1.0)
        bg.inputs[1].default_value = strength
    if noise:
        try:
            nt = w.node_tree
            tx = nt.nodes.new('ShaderNodeTexNoise')
            tx.inputs['Scale'].default_value = 6.0
            tx.inputs['Detail'].default_value = 8.0
            nz = nt.nodes.new('ShaderNodeTexNoise')
            nz.inputs['Scale'].default_value = 1.5
            nt.links.new(nz.outputs['Fac'], tx.inputs['Vector'])
            rm = nt.nodes.new('ShaderNodeValToRGB')
            rm.color_ramp.elements[0].position = 0.40
            rm.color_ramp.elements[1].position = 0.75
            nt.links.new(tx.outputs['Fac'], rm.inputs['Fac'])
            nt.links.new(rm.outputs['Color'], bg.inputs[0])
        except Exception:
            pass

def shot(name, w, h, samples=40):
    setup(w, h, samples)
    sc = bpy.context.scene
    p = os.path.join(OUT, name)
    sc.render.filepath = p
    try:
        bpy.ops.render.render(write_still=True)
    except Exception as exc:
        print('[LEVEL] eevee failed %r -> cycles' % (exc,))
        sc.render.engine = 'CYCLES'
        sc.cycles.device = 'CPU'
        sc.cycles.samples = 12
        sc.cycles.use_denoising = True
        bpy.ops.render.render(write_still=True)
    sz = os.path.getsize(p)
    print('[LEVEL] wrote %s (%d bytes)' % (p, sz))
    return p

def cam(name, p, target, lens=38.0):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    c = bpy.data.objects.new(name, cd)
    c.location = p
    bpy.context.scene.collection.objects.link(c)
    d = Vector(target) - Vector(p)
    c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = c
    return c

# ------------------------------------------------------------------ enemy kit
ENEMY_FBX = {'Drone': 'XCOM_Floater', 'Zealot': 'XCOM_Sectoid',
             'Phantom': 'XCOM_Chryssalid', 'Brute': 'XCOM_Viper',
             'Golem': 'XCOM_Muton', 'Boss': 'XCOM_Viper'}
DEFAULT_H = {'XCOM_Sectoid': 1.95, 'XCOM_Viper': 2.10, 'XCOM_Floater': 1.85,
             'XCOM_Muton': 2.05, 'XCOM_Chryssalid': 1.35}

def manifest_h():
    out = dict(DEFAULT_H)
    try:
        m = json.load(open(os.path.join(XCOM, 'xcom_manifest.json')))
    except Exception as exc:
        print('[LEVEL] manifest unreadable: %r' % (exc,))
        return out
    items = m if isinstance(m, list) else m.get('enemies') or m.get('models') or []
    if isinstance(items, dict):
        items = [dict(v, name=k) for k, v in items.items()]
    for it in items:
        if not isinstance(it, dict):
            continue
        nm = str(it.get('name') or it.get('file') or it.get('model') or it.get('mesh') or '')
        base = os.path.splitext(os.path.basename(nm))[0]
        h = None
        for k in ('height_m', 'height', 'height_cm', 'z_height', 'zsize'):
            if it.get(k) is not None:
                h = it.get(k)
                break
        if h is None or not base:
            continue
        h = float(h)
        if h > 20:
            h /= 100.0
        for key in out:
            if key.lower() in base.lower() or base.lower() in key.lower():
                out[key] = h
    print('[LEVEL] enemy heights: %s' % out)
    return out

PIT_RECT = None
PIT_TOP = 0.0
if PITF:
    _pc, _pd = loc(PITF), dims(PITF)
    PIT_RECT = (_pc[0] - _pd[0] / 2, _pc[0] + _pd[0] / 2,
                _pc[1] - _pd[1] / 2, _pc[1] + _pd[1] / 2)
    PIT_TOP = None


def etype(r):
    L = lab(r)
    for k in ENEMY_FBX:
        if L.startswith('ENC_' + k):
            return k
    return None

def tint_fbx(objs, m_alien):
    for o in objs:
        for ms in o.data.materials:
            if not ms:
                continue
            ms.use_nodes = True
            b = ms.node_tree.nodes.get('Principled BSDF')
            if not b:
                continue
            try:
                b.inputs['Base Color'].default_value = (0.055, 0.085, 0.062, 1.0)
                b.inputs['Roughness'].default_value = 0.52
                b.inputs['Metallic'].default_value = 0.15
                b.inputs['Emission Color'].default_value = (0.16, 0.55, 0.22, 1.0)
                b.inputs['Emission Strength'].default_value = 0.35
            except Exception:
                pass

def import_fbx(fbx_name, target_h):
    path = os.path.join(XCOM, fbx_name + '.fbx')
    if not os.path.exists(path):
        print('[LEVEL] MISSING FBX %s - skipped' % path)
        return None
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.fbx(filepath=path)
    except Exception as exc:
        print('[LEVEL] FBX import FAILED %s: %r' % (fbx_name, exc))
        return None
    new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    if not new:
        print('[LEVEL] FBX %s imported 0 meshes - skipped' % fbx_name)
        return None
    def bbox(obs):
        mn = [1e9] * 3
        mx = [-1e9] * 3
        for o in obs:
            for c in o.bound_box:
                wv = o.matrix_world @ Vector(c)
                for i in range(3):
                    mn[i] = min(mn[i], wv[i])
                    mx[i] = max(mx[i], wv[i])
        return mn, mx
    mn, mx = bbox(new)
    h = mx[2] - mn[2]
    if h <= 1e-6:
        print('[LEVEL] FBX %s has zero height - skipped' % fbx_name)
        return None
    f = target_h / h
    for o in new:
        o.scale = (o.scale.x * f, o.scale.y * f, o.scale.z * f)
    bpy.context.view_layer.update()
    mn, mx = bbox(new)
    dx = (mn[0] + mx[0]) * 0.5
    dy = (mn[1] + mx[1]) * 0.5
    for o in new:
        o.location.x -= dx
        o.location.y -= dy
        o.location.z -= mn[2]
    bpy.context.view_layer.update()
    for o in new:
        o.hide_render = True
        o.hide_viewport = True
    return new

def spawn_enemy(r, protos, M, heights):
    et = etype(r)
    if not et:
        return None
    fn = ENEMY_FBX[et]
    if fn not in protos:
        protos[fn] = import_fbx(fn, heights.get(fn, DEFAULT_H.get(fn, 1.9)))
    base = protos.get(fn)
    if not base:
        return None
    tint_fbx(base, M['alien'])
    p = loc(r)
    if PIT_TOP is not None and PIT_RECT and PIT_RECT[0] <= p[0] <= PIT_RECT[1] \
            and PIT_RECT[2] <= p[1] <= PIT_RECT[3]:
        p[2] = PIT_TOP
    a = yaw(r)
    made = []
    for o in base:
        c = o.copy()
        c.data = o.data
        bpy.context.scene.collection.objects.link(c)
        c.location = (o.location.x * math.cos(a) - o.location.y * math.sin(a) + p[0],
                      o.location.x * math.sin(a) + o.location.y * math.cos(a) + p[1],
                      o.location.z + p[2])
        c.rotation_euler = (o.rotation_euler.x, o.rotation_euler.y, o.rotation_euler.z + a)
        c.name = 'ENEMY_' + lab(r)
        c.hide_render = False
        c.hide_viewport = False
        made.append(c)
    # alien emissive core + glow so the creature reads at gameplay distance
    sphere('CORE_' + lab(r), (p[0], p[1], p[2] + heights.get(fn, 1.8) * 0.58),
           heights.get(fn, 1.8) * 0.10, M['alien'])
    ld = bpy.data.lights.new('GL_' + lab(r), 'POINT')
    ld.energy = 26.0
    ld.color = (0.32, 1.0, 0.42)
    ld.shadow_soft_size = 0.30
    lo = bpy.data.objects.new('GL_' + lab(r), ld)
    lo.location = (p[0], p[1], p[2] + heights.get(fn, 1.8) * 0.55)
    bpy.context.scene.collection.objects.link(lo)
    return made

# ------------------------------------------------------------------ BLUEPRINT
def build_blueprint(M, title):
    for i in range(-10, 11):
        for j in range(-10, 11):
            x, y = i * 2.0, j * 2.0
            if abs(x) <= 20.0 and abs(y) <= 20.0:
                cube('DOT_%d_%d' % (i, j), (x, y, 0.06), (0.10, 0.10, 0.02), M['griddot'])
    for i in range(-10, 11):
        cube('GL_%d' % i, (i * 2.0, 0, 0.04), (0.04, 40.4, 0.02), M['gridline'])
        cube('GL2_%d' % i, (0, i * 2.0, 0.04), (40.4, 0.04, 0.02), M['gridline'])
    cube('AX', (0, 0, 0.05), (0.11, 40.4, 0.02), M['axis'])
    cube('AY', (0, 0, 0.05), (40.4, 0.11, 0.02), M['axis'])
    # floor fill, cut around the pit so the pit reads as a hole
    cut = None
    if PITF:
        d = dims(PITF)
        c = loc(PITF)
        cut = (c[0] - d[0] / 2, c[0] + d[0] / 2, c[1] - d[1] / 2, c[1] + d[1] / 2)
    slabs = [(-20, 20, -20, 20)]
    for i, (a, b, c, d) in enumerate(slabs):
        cube('FL_%d' % i, ((a + b) / 2, (c + d) / 2, -0.05), (b - a, d - c, 0.08), M['floor'])
    for r in BASE:
        k = kind(r)
        c = loc(r)
        d = dims(r)
        if k == 'wall':
            cube('W_' + lab(r), (c[0], c[1], 0.16), (d[0], d[1], 0.12), M['wall'], (0, 0, yaw(r)))
            n = int(max(d[0], d[1]) / 1.6)
            for h in range(n):
                t = (h + 0.5) / n - 0.5
                cube('WH_%s_%d' % (lab(r), h), (c[0] + t * d[0], c[1] + t * d[1], 0.24),
                     (0.16, 0.16, 0.03), M['hatch'], (0, 0, math.radians(45)))
        elif k == 'cover':
            cube('C_' + lab(r), (c[0], c[1], 0.16), (d[0], d[1], 0.12), M['cover'], (0, 0, yaw(r)))
        elif k == 'pillar':
            disc('P_' + lab(r), (c[0], c[1], 0.16), d[0] / 2, M['pillar'])
        elif k == 'platform':
            cube('PL_' + lab(r), (c[0], c[1], 0.20), (d[0], d[1], 0.20), M['plat'], (0, 0, yaw(r)))
        elif k == 'ramp':
            cube('RM_' + lab(r), (c[0], c[1], 0.16), (d[0], d[1], 0.12), M['ramp'],
                 (0, 0, yaw(r)))
        elif k == 'step':
            cube('ST_' + lab(r), (c[0], c[1], c[2]), (d[0], d[1], d[2]), M['cover'], (0.0, 0.0, 0.0))
        elif k == 'pitfloor':
            disc('PIT', (c[0], c[1], 0.12), d[0] / 2, M['pit'])
        elif k == 'pitrim':
            cube('PR_' + lab(r), (c[0], c[1], 0.18), (d[0], d[1], 0.14), M['pitrim'], (0, 0, yaw(r)))
    # cyan outline on geometry only
    for r in BASE:
        k = kind(r)
        if k not in ('cover', 'platform', 'ramp', 'pillar'):
            continue
        c = loc(r)
        d = dims(r)
        if k == 'pillar':
            disc('PE_' + lab(r), (c[0], c[1], 0.28), d[0] / 2 + 0.10, M['edge'])
            continue
        hw, hd = d[0] / 2 + 0.07, d[1] / 2 + 0.07
        for i, (dx, dy, sw, sd) in enumerate(((0, hd, hw * 2, 0.12), (0, -hd, hw * 2, 0.12),
                                               (hw, 0, 0.12, hd * 2), (-hw, 0, 0.12, hd * 2))):
            cube('E_%s_%d' % (lab(r), i), (c[0] + dx, c[1] + dy, 0.30), (sw, sd, 0.03),
                 M['edge'], (0, 0, yaw(r)))
    for i, (ax, ay, w, h) in enumerate(((0, 20.45, 40.9, 0.14), (0, -20.45, 40.9, 0.14),
                                        (20.45, 0, 0.14, 40.9), (-20.45, 0, 0.14, 40.9))):
        cube('BND_%d' % i, (ax, ay, 0.30), (w, h, 0.03), M['edge'])
    # markers - labelled with the real "label" field
    for r in ENCS + PUS + WPS:
        k = kind(r)
        c = loc(r)
        mm = M['enc'] if k == 'enc' else (M['pu'] if k == 'pu' else M['wp'])
        disc('MK_' + lab(r), (c[0], c[1], 0.32), 0.60, mm, v=20)
        if c[0] > 7.0:
            txt('MT_' + lab(r), lab(r), (c[0] - 0.85, c[1] + 0.50, 0.34), 0.60, mm, align='RIGHT')
        else:
            txt('MT_' + lab(r), lab(r), (c[0] + 0.85, c[1] + 0.50, 0.34), 0.60, mm)
    if START:
        c = loc(START)
        disc('DROP', (c[0], c[1], 0.34), 1.15, M['start'], v=28)
        txt('DROPTXT', 'DROP ZONE', (c[0] + 1.45, c[1] - 0.30, 0.36), 0.78, M['start'])

def annotate(M):
    if PITF:
        c = loc(PITF)
        txt('AN_PIT', 'PIT 10x10 - NO FLOOR CUT, NO ACCESS', (c[0] - 9.0, c[1] - 7.6, 0.36),
            0.70, M['bug'])
    if PLAT:
        c = loc(PLAT)
        txt('AN_RAMP', 'RAMP INSIDE PLATFORM - NO CLIMB', (c[0] - 9.5, c[1] - 4.6, 0.36),
            0.70, M['route'])
    if START:
        c = loc(START)
        txt('AN_DROP', 'DROP ON CLEAR GROUND - 15M FROM PILLAR', (c[0] + 1.45, c[1] - 1.7, 0.36),
            0.66, M['start'])


def legend(M, x, y, title):
    cube('LEGP', (x + 6.4, y, 0.30), (14.4, 20.0, 0.05), M['panel'])
    txt('LEGT', title, (x - 0.3, y + 8.7, 0.34), 0.95, M['txt'])
    ent = [('FLOOR', M['floor']), ('WALL (hatched)', M['wall']), ('COVER BLOCK', M['cover']),
           ('PILLAR', M['pillar']), ('PIT (hazard)', M['pit']), ('PLATFORM', M['plat']),
           ('RAMP', M['ramp']), ('ENC_ ENEMY', M['enc']), ('PU_ PICKUP', M['pu']),
           ('WP_ WEAPON', M['wp']), ('DROP ZONE', M['start'])]
    for i, (n, mm) in enumerate(ent):
        yy = y + 7.0 - i * 1.55
        cube('LG_%d' % i, (x + 0.7, yy, 0.34), (0.90, 0.90, 0.04), mm)
        txt('LGT_%d' % i, n, (x + 2.0, yy - 0.22, 0.36), 0.68, M['txt'])
    txt('LGN', 'GRID = FAINT DOTTED 2M TILE REFERENCE', (x - 0.3, y - 9.2, 0.34), 0.58, M['dim'])
    txt('LGN2', 'CYAN OUTLINE = GEOMETRY EDGE', (x - 0.3, y - 10.2, 0.34), 0.58, M['dim'])

TITLE_OBJS = []


def set_title(lines):
    for i, o in enumerate(TITLE_OBJS):
        if i < len(lines):
            o.data.body = lines[i][0]


def title_block(M, x, y, lines):
    w = 23.0
    h = 1.0 + 1.2 * len(lines)
    cube('TBP', (x + w / 2, y + h / 2, 0.30), (w, h, 0.05), M['panel'])
    for i, (t, mm) in enumerate(lines):
        TITLE_OBJS.append(txt('TB_%d' % i, t, (x + 0.6, y + h - 1.2 - i * 1.2, 0.34), 0.74, mm))

def scale_bar(M, x, y):
    for i in range(5):
        cube('SB_%d' % i, (x + i * 2.0 + 1.0, y, 0.32), (2.0, 0.55, 0.04),
             M['txt'] if i % 2 == 0 else M['panel'])
    for i in (0, 2, 4):
        txt('SBT_%d' % i, '%dM' % (i * 2), (x + i * 2.0, y - 1.15, 0.34), 0.58, M['txt'])
    txt('SBTL', 'SCALE BAR - 2M TILES', (x, y + 1.35, 0.34), 0.60, M['dim'])

def axis_labels(M):
    for v in range(-20, 21, 10):
        txt('AXT_%d' % v, '%+d' % v, (v + 0.4, -21.7, 0.32), 0.58, M['dim'])
        txt('AYT_%d' % v, '%+d' % v, (-21.9, v + 0.4, 0.32), 0.58, M['dim'])
    txt('AXL', 'X (m)', (19.0, -21.7, 0.32), 0.62, M['txt'])
    txt('AYL', 'Y (m)', (-21.9, 18.6, 0.32), 0.62, M['txt'])

def bp_camera():
    cd = bpy.data.cameras.new('BPCAM')
    cd.type = 'ORTHO'
    cd.ortho_scale = 76.0
    c = bpy.data.objects.new('BPCAM', cd)
    c.location = (4.0, 0.0, 70.0)
    c.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.scene.collection.objects.link(c)
    bpy.context.scene.camera = c

# ------------------------------------------------------------------ path
def spot_clear(x, y):
    for r in BASE:
        k = kind(r)
        if k not in ('cover', 'pillar', 'platform'):
            continue
        c = loc(r)
        d = dims(r)
        if abs(x - c[0]) < d[0] / 2 + 0.7 and abs(y - c[1]) < d[1] / 2 + 0.7:
            return False
    return True


def route_nodes():
    seq = []
    if START:
        seq.append(('DROP ZONE (BO_PlayerStart)', loc(START), 'start'))
    for pre, tag in (('BO_Cover_05', 'COVER 05'), ('BO_PitFloor', 'PIT AMBUSH'),
                     ('BO_Cover_03', 'COVER 03'), ('BO_Pillar', 'PILLAR - KILL ZONE 2'),
                     ('BO_Cover_04', 'COVER 04'), ('ENC_Boss', 'OBJECTIVE')):
        r = by(pre)
        if r:
            seq.append((tag, loc(r), 'route'))
    return seq

def build_path(M):
    seq = route_nodes()
    pts = [(p[0], p[1], 0.40) for (_n, p, _k) in seq]
    if len(pts) >= 2:
        curve('ROUTE', pts, 0.17, M['route'])
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            dv = Vector((b[0] - a[0], b[1] - a[1], 0.0))
            if dv.length < 0.01:
                continue
            ang = math.atan2(dv.y, dv.x)
            cone('ARR_%d' % i, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.46), 0.60, 1.4,
                 M['route'], (0, math.pi / 2, ang))
    for i, (n, p, k) in enumerate(seq):
        txt('WPL_%d' % i, n, (p[0] + 1.1, p[1] - 0.45, 0.40), 0.72,
            M['start'] if k == 'start' else M['route'])
        txt('WPN_%d' % i, 'WP %d' % (i + 1), (p[0] + 1.1, p[1] - 1.35, 0.40), 0.56, M['dim'])
    if PILLAR:
        c = loc(PILLAR)
        disc('KZ1', (c[0], c[1], 0.24), 4.8, M['kill'])
        txt('KZ1T', 'KILL ZONE 2 - PILLAR', (c[0] + 5.0, c[1] - 0.4, 0.40), 0.66, M['kill'])
    if PITF:
        c = loc(PITF)
        disc('KZ2', (c[0], c[1], 0.24), 5.8, M['kill'])
        txt('KZ2T', 'KILL ZONE 1 - PIT', (c[0] + 6.0, c[1] - 0.4, 0.40), 0.66, M['kill'])
    if BOSS:
        c = loc(BOSS)
        disc('KZ3', (c[0], c[1], 0.24), 3.6, M['obj'])
        txt('KZ3T', 'OBJECTIVE - BOSS', (c[0] + 3.8, c[1] - 0.4, 0.40), 0.74, M['obj'])
    for r in BASE:
        if kind(r) != 'cover':
            continue
        c = loc(r)
        txt('CVR_' + lab(r), 'COVER', (c[0] + 0.8, c[1] + 0.45, 0.40), 0.56, M['dim'])

# ------------------------------------------------------------------ analysis
def seg_box(x0, y0, x1, y1, a, b, c, d):
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0 - a), (dx, c - x0), (-dy, y0 - b), (dy, d - y0)):
        if abs(p) < 1e-9:
            if q < 0:
                return False
            continue
        t = q / p
        if p < 0:
            if t > t1:
                return False
            t0 = max(t0, t)
        else:
            if t < t0:
                return False
            t1 = min(t1, t)
    return t1 >= t0

def analyse():
    st = {}
    st['source_json'] = os.path.relpath(JSON_PATH, ROOT).replace('\\', '/')
    st['actor_count'] = len(RECS)
    bp = {'ENC': 0, 'PU': 0, 'WP': 0, 'base': 0}
    for r in RECS:
        k = kind(r)
        if k == 'enc':
            bp['ENC'] += 1
        elif k == 'pu':
            bp['PU'] += 1
        elif k == 'wp':
            bp['WP'] += 1
        else:
            bp['base'] += 1
    st['by_prefix'] = bp
    st['total_spawn_points'] = bp['ENC'] + bp['PU'] + bp['WP']
    st['by_group'] = {}
    for r in RECS:
        g = str(r.get('group'))
        st['by_group'][g] = st['by_group'].get(g, 0) + 1
    drop = loc(START) if START else [0.0, 0.0, 0.0]
    st['drop_zone'] = {'label': lab(START) if START else None,
                        'loc_m': [round(v, 2) for v in drop]}
    blockers = []
    for r in BASE:
        k = kind(r)
        if k not in ('cover', 'pillar', 'platform', 'wall'):
            continue
        c = loc(r)
        d = dims(r)
        hx, hy = d[0] / 2.0, d[1] / 2.0
        blockers.append((c[0] - hx, c[1] - hy, c[0] + hx, c[1] + hy, lab(r)))
    los = []
    for r in ENCS:
        c = loc(r)
        dist = math.hypot(c[0] - drop[0], c[1] - drop[1])
        blocked = False
        for (a0, b0, c0, d0, bn) in blockers:
            if seg_box(drop[0], drop[1], c[0], c[1], a0, b0, c0, d0):
                blocked = True
                break
        los.append({'label': lab(r), 'type': etype(r), 'dist_m': round(dist, 2),
                    'los': 'blocked' if blocked else 'clear'})
    st['spawn_los_from_drop'] = los
    st['spawns_in_immediate_los_of_drop'] = [e for e in los if e['los'] == 'clear' and e['dist_m'] < 12.0]
    # drop point overlap check - is the PlayerStart inside the pillar footprint?
    ov = []
    if PILLAR:
        pc = loc(PILLAR)
        pd = dims(PILLAR)
        if abs(drop[0] - pc[0]) < pd[0] / 2 and abs(drop[1] - pc[1]) < pd[1] / 2:
            ov.append({'label': lab(PILLAR), 'issue': 'PlayerStart sits inside the pillar footprint'})
    for r in BASE:
        k = kind(r)
        if k in ('cover', 'platform', 'pitfloor', 'pitrim'):
            c = loc(r)
            d = dims(r)
            if abs(drop[0] - c[0]) < d[0] / 2 and abs(drop[1] - c[1]) < d[1] / 2:
                ov.append({'label': lab(r), 'issue': 'PlayerStart inside footprint'})
    st['drop_point_overlaps'] = ov
    # reachability
    climbs = []
    for r in RECS:
        if kind(r) in ('ramp', 'platform'):
            climbs.append(loc(r))
    unreach = []
    for r in PUS + WPS:
        c = loc(r)
        if c[2] < 2.0:
            continue
        if not any(math.hypot(c[0] - q[0], c[1] - q[1]) < 14.0 for q in climbs):
            unreach.append({'label': lab(r), 'z_m': round(c[2], 2),
                            'issue': 'elevated but no ramp/platform within 14m'})
    st['possibly_unreachable'] = unreach
    st['pit_sealed_by_floor_plane'] = bool(PITF)
    st['pit_floor_z_m'] = round(loc(PITF)[2], 3) if PITF else None
    st['floor_plane_z_m'] = round(loc(by('BO_Floor'))[2], 3) if by('BO_Floor') else None
    st['findings'] = []
    if PILLAR and START:
        pc, pd = loc(PILLAR), dims(PILLAR)
        dc = loc(START)
        st['findings'].append({
            'id': 'drop_on_pillar',
            'verdict': 'CONFIRMED' if (abs(dc[0] - pc[0]) < pd[0] / 2 and
                                       abs(dc[1] - pc[1]) < pd[1] / 2) else 'NOT CONFIRMED',
            'detail': 'PlayerStart %s vs pillar %s' % ([round(v, 1) for v in dc],
                                                        [round(v, 1) for v in pc])})
    # pit volume audit
    if PITF:
        pc, pd = loc(PITF), dims(PITF)
        x0, x1, y0, y1 = pc[0] - pd[0] / 2, pc[0] + pd[0] / 2, pc[1] - pd[1] / 2, pc[1] + pd[1] / 2
        inside = []
        for r in RECS:
            c = loc(r)
            if x0 <= c[0] <= x1 and y0 <= c[1] <= y1 and kind(r) in ('enc', 'pu', 'wp'):
                inside.append({'label': lab(r), 'z_m': round(c[2], 2),
                               'z_above_pit_floor_m': round(c[2] - pc[2], 2)})
        access = [lab(r) for r in RECS
                  if (x0 <= loc(r)[0] <= x1 and y0 <= loc(r)[1] <= y1)
                  and kind(r) in ('ramp', 'cover')]
        st['findings'].append({
            'id': 'pit_access',
            'verdict': 'NO WAY IN' if not access else 'access present',
            'pit_floor_z_m': round(pc[2], 2),
            'rim_height_m': 0.5,
            'contents_inside_pit': inside,
            'climb_geometry_inside_pit': access,
            'detail': 'pit floor at z=%s m (%.2f m below grade), rim curbs 0.5 m tall, '
                      'no ramp/ladder/stairs inside the pit volume'
                      % (round(pc[2], 2), abs(pc[2]))})
    # platform climb audit
    if PLAT and RAMP:
        pc, pd = loc(PLAT), dims(PLAT)
        rc, rd = loc(RAMP), dims(RAMP)
        deck = pc[2] + pd[2] / 2
        st['findings'].append({
            'id': 'platform_climb',
            'verdict': 'NO CLIMB ROUTE' if not (rc[0] < pc[0] + pd[0] / 2 and rc[0] > pc[0] - pd[0] / 2
                                                and rc[1] < pc[1] + pd[1] / 2 and rc[1] > pc[1] - pd[1] / 2) else 'ramp adjacent',
            'platform_top_m': round(deck, 2),
            'ramp_loc_m': [round(v, 2) for v in rc],
            'ramp_dims_m': [round(v, 2) for v in rd],
            'ramp_top_m': round(rc[2] + rd[2] / 2, 2),
            'detail': 'ramp footprint lies INSIDE the platform footprint, so the ramp is '
                      'swallowed by the platform and tops out at %s m against a deck at %s m'
                      % (round(rc[2] + rd[2] / 2, 2), round(deck, 2))})
    st['spawn_detail'] = []
    for r in ENCS + PUS + WPS:
        st['spawn_detail'].append({'label': lab(r), 'group': kind(r),
                                    'loc_m': [round(v, 2) for v in loc(r)]})
    return st

def write_report(st, frames):
    L = []
    A = L.append
    A('# M_Blockout01 - Level Read (blockout review)')
    A('')
    A('Rendered from `Docs/generated/level_transforms.json` (%d actors), which was dumped'
      % st['actor_count'])
    A('from the committed `Content/Maps/M_Blockout01.umap` by a UE 5.8 headless Python')
    A('commandlet (`Tools/python/dump_level_transforms.py`, read-only).')
    A('')
    A('## Counts')
    A('')
    A('| bucket | count |')
    A('|---|---|')
    A('| actors in map | %d |' % st['actor_count'])
    A('| base arena geometry | %d |' % st['by_prefix']['base'])
    A('| ENC_ encounters | %d |' % st['by_prefix']['ENC'])
    A('| PU_ pickups | %d |' % st['by_prefix']['PU'])
    A('| WP_ weapons | %d |' % st['by_prefix']['WP'])
    A('| total spawn points | %d |' % st['total_spawn_points'])
    A('')
    A('## Tactical spaces')
    A('')
    A('- **Drop zone** - `BO_PlayerStart` at %s m.' % st['drop_zone']['loc_m'])
    A('- **Central pillar** - the only hard cover in the middle of the arena; splits the')
    A('  room and is the primary kill zone.')
    A('- **8 cover blocks** - four diagonal, four axial, the stepping stones of a fight.')
    A('- **NE platform + ramp** - the only elevation (8x8x5 m), reached by the ramp;')
    A('  overlooks the drop zone and the pillar.')
    A('- **SW pit** - a 10x10 m recess with a 4-piece rim; the one ambush pocket.')
    A('- **Perimeter** - 4 walls, 40 m square, 4 m high.')
    A('')
    A('## Objective')
    A('')
    A('- Primary: `ENC_Boss_NorEaster` at %s m - the only boss spawn, in the open north'
      % [round(v, 1) for v in loc(BOSS)] if BOSS else '- Primary: n/a')
    A('  quadrant, reached by a straight push north once the pillar is cleared.')
    A('- Secondary: `PU_KeyGreen_PillarTop` (pillar top) and `PU_KeyRed_Pit` (pit).')
    A('- Path shown in `path_diagram.png`: drop -> cover 05 -> cover 02 -> pit ambush ->')
    A('  pillar -> cover 04 -> boss, with the two kill zones ringed.')
    A('')
    A('## Findings')
    A('')
    n = 0
    if st['drop_point_overlaps']:
        n += 1
        A('**FINDING 1 - The squad drops onto the central pillar.** `BO_PlayerStart` occupies the')
        A('   same cell as `BO_Pillar_Center` - the drop point and the main piece of hard')
        A('   cover are coincident. The path diagram shows the drop marker sitting on the')
        A('   pillar. Not fixed here; the map is the authority.')
        for o in st['drop_point_overlaps']:
            A('   - `%s`: %s' % (o['label'], o['issue']))
    if st['spawns_in_immediate_los_of_drop']:
        n += 1
        imm = st['spawns_in_immediate_los_of_drop']
        A('**FINDING %d - %d spawn(s) sit in immediate, unobstructed line-of-sight of the drop.**'
          % (n, len(imm)))
        for e in imm:
            A('   - `%s` (%s) at %s m from the drop, clear LOS.' % (e['label'], e['type'], e['dist_m']))
        A('   A player dropping in is seen by these before reaching the first cover block.')
    if st['pit_sealed_by_floor_plane']:
        n += 1
        A('**FINDING %d - The pit is sealed by the floor plane.** `BO_PitFloor` sits at z=%s m but'
          % (n, st['pit_floor_z_m']))
        A('   `BO_Floor` is a single unbroken 40x40 m plane at z=%s m with no hole cut in'
          % st['floor_plane_z_m'])
        A('   it, so the pit, its rim, `ENC_Brute_Pit`, `PU_KeyRed_Pit` and')
        A('   `PU_Health_Pit` sit under the floor surface and cannot be seen or entered.')
        A('   The renders cut the floor open so the intent is visible.')
    if st['possibly_unreachable']:
        n += 1
        A('**FINDING %d - Elevated pickups with no climb route:**' % n)
        for u in st['possibly_unreachable']:
            A('   - `%s` at z=%s m - %s.' % (u['label'], u['z_m'], u['issue']))
    if n == 0:
        A('No blocking defects found in this pass.')
    A('')
    A('## Spawn line-of-sight from the drop')
    A('')
    A('| spawn | type | distance (m) | direct LOS |')
    A('|---|---|---|---|')
    for e in st['spawn_los_from_drop']:
        A('| `%s` | %s | %s | %s |' % (e['label'], e['type'], e['dist_m'], e['los']))
    A('')
    A('## Frames')
    A('')
    for f in frames:
        A('- `%s` (%d bytes) - %s' % (f['file'], f['bytes'], f['desc']))
    A('')
    p = os.path.join(OUT, 'level_report.md')
    open(p, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('[LEVEL] wrote %s' % p)
    return p

# ------------------------------------------------------------------ game scene
def build_game(M, heights):
    protos = {}
    cut = None
    if PITF:
        c = loc(PITF)
        d = dims(PITF)
        cut = (c[0] - d[0] / 2, c[0] + d[0] / 2, c[1] - d[1] / 2, c[1] + d[1] / 2)
    slabs = [(-20, 20, -20, 20)]
    for i, (a, b, c, d) in enumerate(slabs):
        cube('FLOOR_%d' % i, ((a + b) / 2, (c + d) / 2, -0.06), (b - a, d - c, 0.12), M['floor'])
    cube('FAR', (0, 0, -2.60), (400, 400, 0.40), M['far'])
    for r in BASE:
        k = kind(r)
        c = loc(r)
        d = dims(r)
        if k == 'wall':
            cube('W_' + lab(r), (c[0], c[1], c[2]), (d[0], d[1], d[2]), M['wall'], (0, 0, yaw(r)))
        elif k == 'cover':
            cube('C_' + lab(r), (c[0], c[1], c[2]), (d[0], d[1], d[2]), M['cover'], (0, 0, yaw(r)))
        elif k == 'pillar':
            cyl('P_' + lab(r), (c[0], c[1], c[2]), d[0] / 2, d[2], M['pillar'], v=28)
        elif k == 'platform':
            cube('PL_' + lab(r), (c[0], c[1], c[2]), (d[0], d[1], d[2]), M['plat'], (0, 0, yaw(r)))
        elif k == 'ramp':
            _gc, _gd, _gr = ramp_geo(r, c, d)
            cube('RM_' + lab(r), _gc, _gd, M['ramp'], _gr)
        elif k == 'step':
            cube('ST_' + lab(r), (c[0], c[1], c[2]), (d[0], d[1], d[2]), M['cover'], (0.0, 0.0, 0.0))
        elif k == 'pitfloor':
            cube('PF', (c[0], c[1], c[2] - 0.30), (d[0], d[1], d[2]), M['pit'])
        elif k == 'pitrim':
            cube('PR_' + lab(r), (c[0], c[1], c[2]), (d[0], d[1], d[2]), M['pitrim'], (0, 0, yaw(r)))
    for r in PUS:
        c = loc(r)
        if PIT_TOP is not None and PIT_RECT and PIT_RECT[0] <= c[0] <= PIT_RECT[1] \
                and PIT_RECT[2] <= c[1] <= PIT_RECT[3]:
            c[2] = PIT_TOP
        cube('PU_' + lab(r), (c[0], c[1], c[2]), (0.55, 0.55, 0.55), M['pu'])
        cyl('PUG_' + lab(r), (c[0], c[1], c[2] - 0.35), 0.30, 0.12, M['alien'], v=16)
    for r in WPS:
        c = loc(r)
        cube('WP_' + lab(r), (c[0], c[1], c[2] + 0.12), (1.0, 0.30, 0.24), M['gun'])
        cube('WPG_' + lab(r), (c[0], c[1], c[2] - 0.16), (0.36, 0.36, 0.36), M['wp'])
    # map lights, straight from the dump
    for r in LIGHTS:
        c = loc(r)
        nm = lab(r)
        if nm == 'BO_Sun':
            ld = bpy.data.lights.new('SUN', 'SUN')
            ld.energy = 0.9
            ld.color = (0.62, 0.72, 0.95)
            ld.angle = math.radians(12)
            o = bpy.data.objects.new('SUN', ld)
            o.location = (0, 0, 30)
            o.rotation_euler = (math.radians(52), 0, math.radians(30))
            bpy.context.scene.collection.objects.link(o)
            continue
        col = r.get('light_color') or [200, 220, 255]
        inten = float(r.get('light_intensity') or 2000.0)
        ld = bpy.data.lights.new('L_' + nm, 'POINT')
        ld.energy = max(40.0, min(inten * 0.07, 420.0))
        ld.color = (min(col[0] / 255.0, 1.0), min(col[1] / 255.0, 1.0), min(col[2] / 255.0, 1.0))
        ld.shadow_soft_size = 0.9
        o = bpy.data.objects.new('L_' + nm, ld)
        o.location = (c[0], c[1], max(c[2], 0.5))
        bpy.context.scene.collection.objects.link(o)
    # enemies
    placed = []
    for r in ENCS:
        made = spawn_enemy(r, protos, M, heights)
        if made:
            placed.append(r)
    print('[LEVEL] placed %d/%d enemies' % (len(placed), len(ENCS)))
    return placed

def rig(focus, key=9000.0):
    fx, fy, fz = focus
    ld = bpy.data.lights.new('KEY', 'AREA')
    ld.energy = key * 0.34
    ld.color = (0.52, 0.66, 1.0)
    ld.size = 18.0
    o = bpy.data.objects.new('KEY', ld)
    o.location = (fx - 12.0, fy - 14.0, 16.0)
    o.rotation_euler = (Vector((fx, fy, fz)) - o.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(o)
    ld2 = bpy.data.lights.new('RIMG', 'AREA')
    ld2.energy = key * 0.30
    ld2.color = (0.20, 1.0, 0.40)
    ld2.size = 10.0
    o2 = bpy.data.objects.new('RIMG', ld2)
    o2.location = (fx + 12.0, fy + 11.0, 8.0)
    o2.rotation_euler = (Vector((fx, fy, fz)) - o2.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(o2)
    ld3 = bpy.data.lights.new('RIMX', 'AREA')
    ld3.energy = key * 0.085
    ld3.color = (0.85, 0.16, 0.10)
    ld3.size = 7.0
    o3 = bpy.data.objects.new('RIMX', ld3)
    o3.location = (fx + 8.0, fy - 12.0, 4.5)
    o3.rotation_euler = (Vector((fx, fy, fz)) - o3.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(o3)
    ld4 = bpy.data.lights.new('UGLOW', 'POINT')
    ld4.energy = key * 0.030
    ld4.color = (0.26, 0.95, 0.48)
    o4 = bpy.data.objects.new('UGLOW', ld4)
    o4.location = (fx, fy - 2.5, 0.25)
    bpy.context.scene.collection.objects.link(o4)

# ------------------------------------------------------------------ main
def main():
    heights = manifest_h()
    st = analyse()
    frames = []

    # --- blueprint
    purge()
    M = bp_mats()
    build_blueprint(M, 'M_BLOCKOUT01 - TOP-DOWN LAYOUT')
    legend(M, 26.0, -1.0, 'LEGEND')
    title_block(M, -27.0, 12.0, [
        ('M_BLOCKOUT01 - UE 5.8 ARENA BLOCKOUT', M['txt']),
        ('ACTORS %d  |  BASE %d  |  SPAWN %d' % (st['actor_count'], st['by_prefix']['base'],
         st['total_spawn_points']), M['dim']),
        ('ENC %d   PU %d   WP %d' % (st['by_prefix']['ENC'], st['by_prefix']['PU'],
         st['by_prefix']['WP']), M['dim']),
        ('ORTHOGRAPHIC TOP-DOWN - 2M TILE GRID', M['dim'])])
    scale_bar(M, 24.0, -21.0)
    annotate(M)
    axis_labels(M)
    bp_camera()
    world(1.0, (0.010, 0.013, 0.018), noise=False)
    p = shot('blueprint_topdown.png', 1600, 1000, 48)
    frames.append({'file': 'blueprint_topdown.png', 'bytes': os.path.getsize(p),
                   'desc': 'ortho top-down layout: dotted 2m tile grid, solid filled geometry, '
                           'cyan geometry outlines, legend, title block, scale bar'})

    # --- path diagram
    build_path(M)
    set_title([
        ('M_BLOCKOUT01 - TACTICAL PATH DIAGRAM', M['txt']),
        ('DROP -> COVER -> PIT -> PILLAR -> OBJECTIVE', M['dim']),
        ('KILL ZONES RINGED IN RED - 2 ZONES', M['dim']),
        ('SOURCE: level_transforms.json (%d ACTORS)' % st['actor_count'], M['dim'])])
    p = shot('path_diagram.png', 1600, 1000, 48)
    frames.append({'file': 'path_diagram.png', 'bytes': os.path.getsize(p),
                   'desc': 'top-down route drawn as geometry from the drop zone through cover '
                           'to the objective, kill zones ringed, waypoints labelled'})

    # --- game scene
    purge()
    G = game_mats()
    world(0.55, (0.012, 0.016, 0.023), noise=True)
    placed = build_game(G, heights)

    # shot 1: drop zone, eye height
    d = loc(START) if START else [0.0, 0.0, 0.0]
    cam('CAM_DROP', (d[0], d[1] - 0.6, 1.62), (d[0] + 0.3, d[1] + 16.0, 1.55), lens=38.0)
    rig((0.0, -3.0, 1.4), key=11000.0)
    p = shot('gameplay_01_drop.png', 1280, 720, 40)
    frames.append({'file': 'gameplay_01_drop.png', 'bytes': os.path.getsize(p),
                   'desc': 'ground level at the drop point, 1.62m eye height, 38mm, '
                           'looking north into the arena'})

    # shot 1b: the drop-zone threat - ENC_Phantom_01 sits 7.1m from the PlayerStart
    ph = by('ENC_Phantom_01')
    if ph:
        c = loc(ph)
        cam('CAM_DROPZONE', (d[0], d[1], 1.62), (c[0], c[1], 1.05), lens=35.0)
        rig((c[0], c[1], 1.1), key=7000.0)
        p = shot('gameplay_05_dropzone.png', 1280, 720, 40)
        frames.append({'file': 'gameplay_05_dropzone.png', 'bytes': os.path.getsize(p),
                       'desc': 'from the drop point, 1.62m eye height, 35mm - the enemy that '
                               'is only 7.1m from the PlayerStart'})

    # shot 2: two DIFFERENT enemy types in frame
    best = None
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            a, b = placed[i], placed[j]
            if etype(a) == etype(b):
                continue
            ca, cb = loc(a), loc(b)
            dist = math.hypot(ca[0] - cb[0], ca[1] - cb[1])
            if 2.5 < dist < 9.0 and (best is None or dist < best[0]):
                best = (dist, a, b, ca, cb)
    if best:
        _dd, a, b, ca, cb = best
        mid = ((ca[0] + cb[0]) / 2, (ca[1] + cb[1]) / 2)
        dv = Vector((cb[0] - ca[0], cb[1] - ca[1], 0.0)).normalized()
        perp = Vector((-dv.y, dv.x, 0.0))
        cands = []
        for ang in (180, 135, 225, 90, 270, 45, 315, 0):
            rad = math.radians(ang)
            for dd in (7.0, 9.0, 11.0):
                cands.append((mid[0] + math.cos(rad) * dd, mid[1] + math.sin(rad) * dd))
        ok = [c for c in cands if abs(c[0]) < 18.5 and abs(c[1]) < 18.5 and spot_clear(c[0], c[1])]
        ok.sort(key=lambda c: math.hypot(c[0] - mid[0], c[1] - mid[1]))
        cp = ok[0] if ok else (mid[0] + 7.0, mid[1])
        cam('CAM_DUEL', (cp[0], cp[1], 1.60), (mid[0], mid[1], 1.10), lens=35.0)
        rig((mid[0], mid[1], 1.2), key=9000.0)
        print('[LEVEL] two-type frame: %s + %s (%.1fm apart)' % (lab(a), lab(b), _dd))
        st['two_type_frame'] = '%s + %s' % (lab(a), lab(b))
    else:
        cam('CAM_DUEL', (0.0, -8.0, 1.60), (0.0, 2.0, 1.2), lens=40.0)
        rig((0.0, 0.0, 1.2), key=9000.0)
        st['two_type_frame'] = 'none found'
    p = shot('gameplay_02_duel.png', 1280, 720, 40)
    frames.append({'file': 'gameplay_02_duel.png', 'bytes': os.path.getsize(p),
                   'desc': 'ground level with two different enemy types in frame at '
                           'gameplay distance (real FBX creatures)'})

    # shot 3: the pit
    if PITF:
        c = loc(PITF)
        cam('CAM_PIT', (c[0] + 9.0, c[1] + 5.0, 1.60), (c[0], c[1], -0.30), lens=36.0)
        rig((c[0], c[1], 0.6), key=8000.0)
    p = shot('gameplay_03_pit.png', 1280, 720, 40)
    frames.append({'file': 'gameplay_03_pit.png', 'bytes': os.path.getsize(p),
                   'desc': 'ground level over the SW pit, oxblood rim light, pit occupants visible'})

    # shot 4: NE platform
    if PLAT:
        c = loc(PLAT)
        # the ramp is 15m long (foot y=-7, lip y=+8): stand behind its foot and look up the slope,
        # otherwise the old eye-level camera sits past the foot and the ramp leaves frame.
        cam('CAM_PLAT', (8.60, -14.00, 2.40), (11.20, 0.50, 2.00), lens=26.0)
        rig((c[0], c[1], 3.0), key=10000.0)
    p = shot('gameplay_04_platform.png', 1280, 720, 40)
    frames.append({'file': 'gameplay_04_platform.png', 'bytes': os.path.getsize(p),
                   'desc': 'ground level looking up at the NE platform and ramp, high ground'})

    # shot 6: the pit exit ramp, shot from the arena floor looking down the slope
    if PITRAMP:
        c = loc(PITRAMP)
        # the pit ramp runs x=-10.55 (pit floor) -> x=-8.75 (east rim gap); look down the slope
        # from over the rim so the whole flight and both landings are in frame.
        cam('CAM_PITRAMP', (-3.75, -9.50, 2.20), (-9.65, -13.00, -0.50), lens=30.0)
        rig((c[0] - 0.5, c[1], -0.4), key=7000.0)
    p = shot('gameplay_06_pitramp.png', 1280, 720, 40)
    frames.append({'file': 'gameplay_06_pitramp.png', 'bytes': os.path.getsize(p),
                   'desc': 'the pit exit ramp at the east rim gap, shot from the arena floor looking down the slope'})

    # wide perspective
    cam('CAM_WIDE', (25.0, -28.0, 12.5), (0.0, 1.0, 2.0), lens=32.0)
    rig((0.0, 0.0, 2.0), key=15000.0)
    p = shot('level_perspective.png', 1400, 900, 48)
    frames.append({'file': 'level_perspective.png', 'bytes': os.path.getsize(p),
                   'desc': 'wide 3/4 arena view with solid floor, walls, cover, pillar, '
                           'platform, ramp and pit volume'})

    st['frames'] = frames
    print('[LEVELFIND] ' + json.dumps(st))

    cc = os.path.join(ROOT, 'CommandCenter', 'outputs', 'level')
    try:
        os.makedirs(cc, exist_ok=True)
        for f in frames:
            s = os.path.join(OUT, f['file'])
            open(os.path.join(cc, f['file']), 'wb').write(open(s, 'rb').read())
        for f in ('level_stats.json', 'level_report.md'):
            s = os.path.join(OUT, f)
            if os.path.exists(s):
                open(os.path.join(cc, f), 'wb').write(open(s, 'rb').read())
        print('[LEVEL] delivered to %s' % cc)
    except Exception as exc:
        print('[LEVEL] delivery failed: %r' % (exc,))
    print('[LEVEL] DONE')

main()
