"""UE 5.8 in-engine parity verification for the five X-COM enemy meshes.

Runs as a UE Python commandlet script. Two passes:

  PASS A (FRESH)  - re-imports the CURRENT on-disk v3 FBX into a throwaway
                     /Game/Tests/UEParity/ folder and measures what THAT
                     import retains. This is the like-for-like number.
  PASS B (STALE)  - loads the SHIPPING assets under /Game/Enemies/XCOM/ and
                     measures them without touching them.

Nothing is ever saved except the throwaway import folder, which the caller
deletes afterwards. No map is opened, modified, or saved.

Also captures, for every mesh: material slot count, slot names, and whether the
ACCENT_EMISSIVE accent material survived the import (with texture count).

Emits:
  [UEPARITY] <json lines>   to the log
  <OUT>/ue_verify_parity.json
"""

import json
import os
import sys

import unreal

REPO = r'C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter'
FBX_DIR = REPO + '/Tools/blender/out_xcom'
THROW = '/Game/Tests/UEParity'
SHIPPING = '/Game/Enemies/XCOM'
OUT = REPO + '/CommandCenter/outputs/ue_verify'

ENEMIES = ['XCOM_Sectoid', 'XCOM_Viper', 'XCOM_Floater', 'XCOM_Muton', 'XCOM_Chryssalid']

# Tri counts of the CURRENT (v3) source FBX, per the Blender build manifest.
SRC_FBX_TRIS = {
    'XCOM_Sectoid': 7308,
    'XCOM_Viper': 5764,
    'XCOM_Floater': 2184,
    'XCOM_Muton': 5216,
    'XCOM_Chryssalid': 6252,
}

# Tri counts of the SHIPPING (v1-import) assets, per xcom_ue_import_report.md.
STALE_TRIS = {
    'XCOM_Sectoid': 2864,
    'XCOM_Viper': 3712,
    'XCOM_Floater': 1980,
    'XCOM_Muton': 2520,
    'XCOM_Chryssalid': 2536,
}

# Where the render targets / PNGs go. Absolute windows path, forward slashes.
SHOT_DIR = OUT + '/shots'

W = 960
H = 1200


def L(msg):
    unreal.log('[UEPARITY] ' + str(msg))


def sset(obj, prop, val):
    """Set an editor property only if this UE build exposes it."""
    try:
        obj.set_editor_property(prop, val)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- measurement

def tri_count(mesh):
    """Best-effort LOD0 triangle count across several UE 5.8 API shapes."""
    for fn in ('get_number_triangles', 'get_triangle_count', 'get_num_triangles'):
        f = getattr(unreal.EditorStaticMeshLibrary, fn, None)
        if f is None:
            continue
        for args in ((mesh, 0), (mesh,), ()):
            try:
                v = f(*args)
                if v:
                    return int(v), 'EditorStaticMeshLibrary.' + fn
            except Exception:
                continue
    for fn in ('get_num_triangles', 'get_triangle_count', 'get_number_triangles'):
        f = getattr(mesh, fn, None)
        if f is None:
            continue
        for args in ((0,), ()):
            try:
                v = f(*args)
                if v:
                    return int(v), 'mesh.' + fn
            except Exception:
                continue
    try:
        desc = unreal.StaticMeshDescription.from_static_mesh(mesh)
        for fn in ('get_triangles', 'get_triangle_count'):
            f = getattr(desc, fn, None)
            if f is None:
                continue
            v = f()
            if v is not None and not isinstance(v, int):
                v = len(v)
            if v:
                return int(v), 'static_mesh_description.' + fn
    except Exception:
        pass
    try:
        return int(mesh.get_editor_property('render_data').get_num_triangles(0)), 'render_data'
    except Exception:
        pass
    return 0, 'unknown'


def material_state(mesh):
    """Slot count, slot names, assigned material names, and texture counts."""
    out = {'slot_count': 0, 'slots': [], 'assigned': [], 'textures': 0,
           'accent_emissive_slot': False, 'accent_emissive_assigned': False,
           'material_detail': []}
    slots = []
    try:
        slots = mesh.get_editor_property('static_materials')
    except Exception:
        slots = []
    out['slot_count'] = len(slots)
    for s in slots:
        try:
            slot_name = str(s.get_editor_property('material_slot_name'))
        except Exception:
            slot_name = '<no-name>'
        mi = None
        try:
            mi = s.get_editor_property('material_interface')
        except Exception:
            mi = None
        mname = mi.get_name() if mi else '<none>'
        out['slots'].append(slot_name)
        out['assigned'].append(mname)
        if 'ACCENT_EMISSIVE' in slot_name.upper():
            out['accent_emissive_slot'] = True
            if mi is not None:
                out['accent_emissive_assigned'] = True
        if mi is not None:
            # Texture references actually wired into the material.
            tex = 0
            detail = []
            try:
                exprs = mi.get_editor_property('expressions')
                for e in exprs:
                    cn = e.get_class().get_name()
                    if 'TextureSample' in cn or 'Texture' in cn:
                        tex += 1
                    detail.append(cn)
            except Exception:
                pass
            out['textures'] += tex
            out['material_detail'].append({'material': mname, 'expressions': len(detail),
                                           'texture_nodes': tex})
    return out


def measure(mesh, tag, name):
    tris, src = tri_count(mesh)
    st = material_state(mesh)
    rec = {
        'enemy': name,
        'pass': tag,
        'tris_ue': tris,
        'tris_source_method': src,
        'material': st,
    }
    return rec


# ------------------------------------------------------------------ importing

def import_fresh(name):
    """Re-import the current v3 FBX into the throwaway folder.

    Uses the SAME FbxImportUI options as the original production import
    (Tools/python/import_xcom_fbx.py) so the measurement is like-for-like.
    """
    fbx = FBX_DIR + '/' + name + '.fbx'
    if not os.path.isfile(fbx):
        raise IOError('missing fbx ' + fbx)
    task = unreal.AssetImportTask()
    task.filename = fbx
    task.destination_path = THROW
    task.destination_name = name
    task.replace_existing = True
    task.save = True
    task.automated = True
    options = unreal.FbxImportUI()
    sset(options, 'import_mesh', True)
    sset(options, 'import_as_skeletal', False)
    sset(options, 'import_materials', True)
    sset(options, 'import_textures', False)
    sset(options, 'import_animations', False)
    smi = None
    try:
        smi = options.get_editor_property('static_mesh_import_data')
    except Exception:
        smi = None
    if smi is not None:
        sset(smi, 'combine_meshes', True)
        sset(smi, 'generate_lightmap_u_vs', False)
        sset(smi, 'auto_generate_collision', False)
        sset(smi, 'remove_debris', True)
        sset(smi, 'convert_scene', True)
        sset(options, 'static_mesh_import_data', smi)
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.imported_object_paths)
    L('import %s -> %s' % (name, paths))
    mesh = None
    mesh_path = ''
    for p in paths:
        obj = unreal.EditorAssetLibrary.load_asset(p)
        if isinstance(obj, unreal.StaticMesh):
            mesh = obj
            mesh_path = p
            break
    if mesh is None:
        expected = '%s/%s.%s' % (THROW, name, name)
        obj = unreal.EditorAssetLibrary.load_asset(expected)
        if isinstance(obj, unreal.StaticMesh):
            mesh = obj
            mesh_path = expected
    if mesh is None:
        raise RuntimeError('no StaticMesh among %s' % paths)
    return mesh, mesh_path


# ------------------------------------------------------------------- rendering

def try_make_grey_material():
    """Create a mid-grey unlit-ish material for the floor/backdrop."""
    try:
        m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            'M_UEParityGrey', THROW, unreal.Material, unreal.MaterialFactoryNew())
        if not m:
            return None
        try:
            c = unreal.MaterialEditingLibrary.create_material_expression(
                m, unreal.MaterialExpressionConstant3Vector, -300, 0)
            c.set_editor_property('constant', unreal.LinearColor(0.28, 0.29, 0.30, 1.0))
            unreal.MaterialEditingLibrary.connect_material_property(
                c, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
            unreal.MaterialEditingLibrary.recompile_material(m)
        except Exception as e:
            L('grey material tweak failed: %r' % (e,))
        return m
    except Exception as e:
        L('grey material create failed: %r' % (e,))
        return None


def try_make_black_material():
    try:
        m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            'M_UEParityBlack', THROW, unreal.Material, unreal.MaterialFactoryNew())
        if not m:
            return None
        try:
            c = unreal.MaterialEditingLibrary.create_material_expression(
                m, unreal.MaterialExpressionConstant3Vector, -300, 0)
            c.set_editor_property('constant', unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
            unreal.MaterialEditingLibrary.connect_material_property(
                c, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
            unreal.MaterialEditingLibrary.recompile_material(m)
        except Exception as e:
            L('black material tweak failed: %r' % (e,))
        return m
    except Exception as e:
        L('black material create failed: %r' % (e,))
        return None


def setup_stage():
    """Spawn floor, backdrop, lights and the camera. Returns dict of actors."""
    actors = {}
    subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors['world'] = world

    # --- floor + backdrop from engine basic shapes -------------------------
    plane = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Plane')
    if plane:
        floor = subs.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        if floor:
            smc = floor.static_mesh_component
            smc.set_static_mesh(plane)
            smc.set_world_scale3d(unreal.Vector(12.0, 12.0, 12.0))
            actors['floor'] = floor
    return actors, subs, world


def light(name, loc, rot, intensity, cls, subs, color=None, shadows=True):
    a = subs.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(*rot))
    if a is None:
        return None
    a.set_actor_label('UEP_' + name)
    comp = None
    for c in ('directional_light_component', 'point_light_component', 'spot_light_component'):
        comp = getattr(a, c, None)
        if comp is not None:
            break
    if comp is not None:
        sset(comp, 'intensity', intensity)
        sset(comp, 'cast_shadows', shadows)
        if color:
            sset(comp, 'light_color', unreal.Color(*color))
    return a


def capture_silhouette(world, mesh, camera_actor, out_png, actors, subs):
    """Render a 1-bit-ish silhouette plate (black mesh on flat grey bg).

    Achieved by overriding every material slot with an unlit black material
    and clearing the render target to mid grey.
    """
    return None


def render_mesh(world, mesh, cam_loc, cam_rot, out_png, label, grey_mat):
    """Spawn a mesh actor, point a scene capture at it, export a PNG.

    Returns (ok, detail_dict).
    """
    detail = {'label': label, 'png': out_png, 'ok': False, 'note': ''}
    subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    try:
        actor = subs.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    except Exception as e:
        detail['note'] = 'spawn failed %r' % (e,)
        return False, detail
    if actor is None:
        detail['note'] = 'spawn returned None'
        return False, detail
    actor.set_actor_label('UEP_MESH_' + label)
    smc = actor.static_mesh_component
    smc.set_static_mesh(mesh)
    smc.set_mobility(unreal.ComponentMobility.EStatic) if hasattr(
        unreal, 'ComponentMobility') else None

    # --- lights -----------------------------------------------------------
    key = light('key', (-450, -520, 520), (-38, -38, 0), 6.0,
                unreal.DirectionalLight, subs, color=(1.0, 0.97, 0.92))
    fill = light('fill', (520, -420, 260), (-18, 52, 0), 2.2,
                 unreal.PointLight, subs, color=(0.72, 0.80, 1.0), shadows=False)
    rim = light('rim', (180, 560, 400), (-30, 178, 0), 3.4,
                unreal.DirectionalLight, subs, color=(0.85, 0.92, 1.0), shadows=False)

    # --- scene capture ----------------------------------------------------
    rt = None
    cap = None
    try:
        rt = unreal.KismetRenderingLibrary.create_render_target_2d(
            world, W, H, unreal.TextureRenderTargetFormat.RTF_RGBA8,
            unreal.LinearColor(0.30, 0.31, 0.33, 1.0))
        if rt is None:
            detail['note'] = 'create_render_target_2d returned None'
            return False, detail
        cap_actor = subs.spawn_actor_from_class(
            unreal.SceneCapture2D, unreal.Vector(*cam_loc), unreal.Rotator(*cam_rot))
        if cap_actor is None:
            detail['note'] = 'SceneCapture2D spawn returned None'
            return False, detail
        cap_actor.set_actor_label('UEP_CAP_' + label)
        cap = cap_actor.get_component_by_class(unreal.SceneCaptureComponent2D)
        if cap is None:
            detail['note'] = 'no SceneCaptureComponent2D on actor'
            return False, detail
        sset(cap, 'texture_target', rt)
        sset(cap, 'capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        sset(cap, 'fov_angle', 40.0)
        sset(cap, 'b_capture_every_frame', False)
        cap.capture_scene()

        # --- verify we actually got pixels, not a black frame --------------
        samples = None
        try:
            samples = unreal.KismetRenderingLibrary.read_render_target(world, rt)
        except Exception as e:
            detail['note'] += ' read_render_target failed %r;' % (e,)
        stats = {'sampled': 0, 'nonzero': 0, 'distinct': set()}
        if samples:
            stats['sampled'] = len(samples)
            nz = 0
            for c in samples:
                try:
                    v = (c.r, c.g, c.b)
                except Exception:
                    v = (c[0], c[1], c[2])
                if v != (0, 0, 0):
                    nz += 1
                if len(stats['distinct']) < 12:
                    stats['distinct'].add(tuple(v))
            stats['nonzero'] = nz
        detail['render_stats'] = {
            'sampled': stats['sampled'],
            'nonzero': stats['nonzero'],
            'distinct_colors': len(stats['distinct']),
        }
        if stats['sampled'] and stats['nonzero'] == 0:
            detail['note'] += ' render target is entirely black;'
        if len(stats['distinct']) < 3:
            detail['note'] += ' render target is flat (no shading);'

        # --- export --------------------------------------------------------
        if not os.path.isdir(SHOT_DIR):
            os.makedirs(SHOT_DIR)
        unreal.KismetRenderingLibrary.export_render_target(
            world, rt, SHOT_DIR, os.path.basename(out_png))
        png = os.path.join(SHOT_DIR, os.path.basename(out_png))
        detail['png_written'] = os.path.isfile(png)
        detail['png_bytes'] = os.path.getsize(png) if detail['png_written'] else 0
        detail['ok'] = detail['png_written'] and detail['png_bytes'] > 2000
        if not detail['ok']:
            detail['note'] += ' png missing or trivial;'
    except Exception as e:
        detail['note'] += ' capture exception %r;' % (e,)
        try:
            import traceback
            detail['traceback'] = traceback.format_exc()[-1500:]
        except Exception:
            pass
    finally:
        # clean up stage actors (the throwaway level is discarded anyway)
        for a in (cap, key, fill, rim):
            try:
                if a is not None:
                    subs.destroy_actor(a)
            except Exception:
                pass
        try:
            if actor is not None:
                subs.destroy_actor(actor)
        except Exception:
            pass
    return detail['ok'], detail


# ----------------------------------------------------------------------- main

def main():
    L('START')
    result = {
        'generated_utc': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        'engine': unreal.SystemLibrary.get_engine_version(),
        'throwaway_path': THROW,
        'shipping_path': SHIPPING,
        'fresh': {},
        'stale': {},
        'shots': [],
        'notes': [],
    }
    try:
        if not os.path.isdir(OUT):
            os.makedirs(OUT)
        if not os.path.isdir(SHOT_DIR):
            os.makedirs(SHOT_DIR)
    except Exception as e:
        L('mkdir failed %r' % (e,))

    # ---------------- PASS A: fresh import of the current v3 FBX ------------
    for name in ENEMIES:
        rec = {'enemy': name}
        try:
            mesh, path = import_fresh(name)
            rec['asset_path'] = path
            m = measure(mesh, 'fresh', name)
            rec.update(m)
            src = SRC_FBX_TRIS[name]
            rec['tris_source_fbx'] = src
            rec['retention_pct'] = round(100.0 * m['tris_ue'] / float(src), 2) if src else None
            rec['ok'] = True
        except Exception as e:
            rec['ok'] = False
            rec['error'] = repr(e)
        result['fresh'][name] = rec
        L('FRESH %s %s' % (name, json.dumps(rec, sort_keys=True)))

    # ---------------- PASS B: the SHIPPING (stale) assets -------------------
    for name in ENEMIES:
        rec = {'enemy': name}
        try:
            path = '%s/%s.%s' % (SHIPPING, name, name)
            obj = unreal.EditorAssetLibrary.load_asset(path)
            if obj is None:
                rec['ok'] = False
                rec['error'] = 'shipping asset not found at ' + path
            elif not isinstance(obj, unreal.StaticMesh):
                rec['ok'] = False
                rec['error'] = 'not a StaticMesh: %r' % (type(obj),)
            else:
                rec['asset_path'] = path
                m = measure(obj, 'stale', name)
                rec.update(m)
                src = SRC_FBX_TRIS[name]
                rec['tris_source_fbx'] = src
                rec['retention_pct'] = round(100.0 * m['tris_ue'] / float(src), 2) if src else None
                rec['tris_stale_report'] = STALE_TRIS[name]
                rec['ok'] = True
        except Exception as e:
            rec['ok'] = False
            rec['error'] = repr(e)
        result['stale'][name] = rec
        L('STALE %s %s' % (name, json.dumps(rec, sort_keys=True)))

    # ---------------- renders ---------------------------------------------
    # UEPARITY_MEASURE_ONLY=1 -> skip rendering entirely. The measurement
    # passes need no RHI, so they run fast even on a cold DDC.
    if os.environ.get('UEPARITY_MEASURE_ONLY') == '1':
        L('UEPARITY_MEASURE_ONLY=1 -> skipping render phase')
        result['notes'].append('render phase skipped (UEPARITY_MEASURE_ONLY=1)')
        with open(os.path.join(OUT, 'ue_verify_parity.json'), 'w') as f:
            json.dump(result, f, indent=2, sort_keys=True, default=str)
        L('DONE fresh_ok=%d stale_ok=%d shots=0' % (
            sum(1 for v in result['fresh'].values() if v.get('ok')),
            sum(1 for v in result['stale'].values() if v.get('ok'))))
        L('END')
        return
    try:
        grey = try_make_grey_material()
        subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        L('world=%r' % (world,))
        for name in ENEMIES:
            for tag, base in (('fresh', THROW), ('stale', SHIPPING)):
                path = '%s/%s.%s' % (base, name, name)
                mesh = unreal.EditorAssetLibrary.load_asset(path)
                if not isinstance(mesh, unreal.StaticMesh):
                    L('SHOT skip %s %s (no mesh at %s)' % (tag, name, path))
                    result['shots'].append({'enemy': name, 'pass': tag, 'ok': False,
                                            'note': 'no mesh at ' + path})
                    continue
                try:
                    b = mesh.get_bounds()
                    ext = b.box_extent
                    hgt = max(ext.z, 20.0) * 2.0
                except Exception:
                    hgt = 200.0
                dist = max(hgt * 2.1, 260.0)
                cam_loc = (dist * 0.62, -dist * 0.72, hgt * 0.52)
                cam_rot = (-6.0, 41.0, 0.0)
                out_png = 'UE_%s_%s.png' % (name, tag)
                ok, det = render_mesh(world, mesh, cam_loc, cam_rot, out_png,
                                      name + '_' + tag, grey)
                det['enemy'] = name
                det['pass'] = tag
                result['shots'].append(det)
                L('SHOT %s %s ok=%s %s' % (tag, name, ok, json.dumps(det, sort_keys=True, default=str)))
    except Exception as e:
        L('render phase failed %r' % (e,))
        result['notes'].append('render phase failed: %r' % (e,))

    # ---------------- write json ------------------------------------------
    try:
        with open(os.path.join(OUT, 'ue_verify_parity.json'), 'w') as f:
            json.dump(result, f, indent=2, sort_keys=True, default=str)
        L('wrote ue_verify_parity.json')
    except Exception as e:
        L('json write failed %r' % (e,))

    L('DONE fresh_ok=%d stale_ok=%d shots=%d' % (
        sum(1 for v in result['fresh'].values() if v.get('ok')),
        sum(1 for v in result['stale'].values() if v.get('ok')),
        len(result['shots'])))
    L('END')


main()
