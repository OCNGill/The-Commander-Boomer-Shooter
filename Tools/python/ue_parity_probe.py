"""Throwaway API probe for the UE 5.8 parity run.

Answers, at runtime, exactly the questions the parity script needs:
  - does the editor world exist and does it have a usable level?
  - can we spawn a StaticMeshActor into it?
  - do SceneCapture2D / create_render_target_2d / export_render_target exist?
  - which triangle-count API actually works?
  - does a fresh FBX import into /Game/Tests/UEParity work, and how many
    material slots / does an ACCENT_EMISSIVE slot survive?

Writes nothing outside /Game/Tests/UEParity. Never opens or saves a map.
"""

import json
import os

import unreal

REPO = r'C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter'
FBX_DIR = REPO + '/Tools/blender/out_xcom'
THROW = '/Game/Tests/UEParity'
SHIPPING = '/Game/Enemies/XCOM'

R = {}


def L(m):
    unreal.log('[UEPROBE] ' + str(m))


def names(obj, needles):
    try:
        d = dir(obj)
    except Exception:
        return []
    return sorted([n for n in d if any(x.lower() in n.lower() for x in needles)])


def sset(obj, prop, val):
    try:
        obj.set_editor_property(prop, val)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- API surface
R['has_SceneCapture2D'] = hasattr(unreal, 'SceneCapture2D')
R['has_SceneCaptureComponent2D'] = hasattr(unreal, 'SceneCaptureComponent2D')
R['has_KismetRenderingLibrary'] = hasattr(unreal, 'KismetRenderingLibrary')
R['kismet_names'] = names(getattr(unreal, 'KismetRenderingLibrary', None),
                          ['render_target', 'capture'])
R['scene_capture_source_enum'] = []
try:
    for n in dir(unreal.SceneCaptureSource):
        if n.startswith('SCS'):
            R['scene_capture_source_enum'].append(n)
except Exception as e:
    R['scene_capture_source_enum'] = ['ERR ' + repr(e)]
R['editor_static_mesh_lib_tri'] = names(
    getattr(unreal, 'EditorStaticMeshLibrary', None), ['tri', 'vert', 'section'])
R['static_mesh_editor_subsystem_tri'] = names(
    getattr(unreal, 'StaticMeshEditorSubsystem', None), ['tri', 'vert'])
R['editor_level_library'] = names(getattr(unreal, 'EditorLevelLibrary', None),
                                  ['new_level', 'load_level', 'spawn', 'actor'])
R['unreal_editor_subsystem'] = names(getattr(unreal, 'UnrealEditorSubsystem', None),
                                     ['world', 'level'])
R['texture_render_target_format'] = [n for n in dir(unreal.TextureRenderTargetFormat)
                                     if n.startswith('RTF')]
L('API ' + json.dumps({k: v for k, v in R.items() if k != 'unreal_editor_subsystem'},
                      default=str))

# ------------------------------------------------------------------- world
subs = None
world = None
try:
    subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    R['editor_actor_subsystem'] = True
except Exception as e:
    R['editor_actor_subsystem'] = 'ERR ' + repr(e)
try:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    R['world_class'] = world.get_class().get_name() if world else None
    R['world_name'] = world.get_name() if world else None
except Exception as e:
    R['world_class'] = 'ERR ' + repr(e)

if world is not None:
    for prop in ('current_level', 'persistent_level'):
        try:
            lv = world.get_editor_property(prop)
            R[prop] = lv.get_name() if lv else None
        except Exception as e:
            R[prop] = 'ERR ' + repr(e)
    try:
        R['all_level_actors'] = len(unreal.EditorLevelLibrary.get_all_level_actors())
    except Exception as e:
        R['all_level_actors'] = 'ERR ' + repr(e)

# ------------------------------------------------------- spawn smoke test
spawned = None
try:
    cube = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube')
    R['cube_loaded'] = bool(cube)
    if cube:
        spawned = subs.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(0, 0, 50), unreal.Rotator(0, 0, 0))
        R['spawn_actor'] = bool(spawned)
        if spawned:
            smc = spawned.static_mesh_component
            smc.set_static_mesh(cube)
            R['spawn_label'] = spawned.get_actor_label()
            R['smc_world_scale'] = str(smc.get_world_scale3d())
except Exception as e:
    R['spawn_actor'] = 'ERR ' + repr(e)
    import traceback
    R['spawn_traceback'] = traceback.format_exc()[-1200:]

# ------------------------------------------- triangle count on shipping mesh
ship_mesh = None
try:
    ship_mesh = unreal.EditorAssetLibrary.load_asset(SHIPPING + '/XCOM_Sectoid.XCOM_Sectoid')
    R['shipping_loaded'] = bool(ship_mesh)
    R['shipping_class'] = ship_mesh.get_class().get_name() if ship_mesh else None
except Exception as e:
    R['shipping_loaded'] = 'ERR ' + repr(e)

tri_result = {}
if ship_mesh is not None:
    for fn in ('get_number_triangles', 'get_triangle_count', 'get_num_triangles',
               'get_number_verts', 'get_number_vertices'):
        f = getattr(unreal.EditorStaticMeshLibrary, fn, None)
        if f is None:
            continue
        for args in ((ship_mesh, 0), (ship_mesh,), ()):
            try:
                tri_result['ESML.%s%s' % (fn, len(args))] = f(*args)
            except Exception as e:
                tri_result['ESML.%s%s' % (fn, len(args))] = 'ERR ' + repr(e)[:80]
    for fn in ('get_num_triangles', 'get_triangle_count', 'get_number_triangles',
               'get_num_vertices', 'get_num_sections'):
        f = getattr(ship_mesh, fn, None)
        if f is None:
            continue
        for args in ((0,), ()):
            try:
                tri_result['mesh.%s%s' % (fn, len(args))] = f(*args)
            except Exception as e:
                tri_result['mesh.%s%s' % (fn, len(args))] = 'ERR ' + repr(e)[:80]
    try:
        smes = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        for fn in ('get_number_verts', 'get_number_triangles', 'get_number_vertices'):
            f = getattr(smes, fn, None)
            if f is None:
                continue
            for args in ((ship_mesh, 0), (ship_mesh,)):
                try:
                    tri_result['SMES.%s%s' % (fn, len(args))] = f(*args)
                except Exception as e:
                    tri_result['SMES.%s%s' % (fn, len(args))] = 'ERR ' + repr(e)[:80]
    except Exception as e:
        tri_result['SMES'] = 'ERR ' + repr(e)
    # static materials of the shipping asset
    try:
        slots = ship_mesh.get_editor_property('static_materials')
        R['shipping_slot_count'] = len(slots)
        R['shipping_slot_names'] = [str(s.get_editor_property('material_slot_name'))
                                    for s in slots]
        R['shipping_slot_mats'] = []
        for s in slots:
            mi = s.get_editor_property('material_interface')
            R['shipping_slot_mats'].append(mi.get_name() if mi else None)
    except Exception as e:
        R['shipping_slot_count'] = 'ERR ' + repr(e)
R['tri_probe'] = tri_result
L('TRI ' + json.dumps(tri_result, default=str))

# ------------------------------------------------------------ fresh import
fresh = {}
name = 'XCOM_Sectoid'
try:
    fbx = FBX_DIR + '/' + name + '.fbx'
    R['fbx_exists'] = os.path.isfile(fbx)
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
    R['smi_found'] = smi is not None
    if smi is not None:
        for p, v in (('combine_meshes', True), ('generate_lightmap_u_vs', False),
                     ('auto_generate_collision', False), ('remove_debris', True),
                     ('convert_scene', True)):
            sset(smi, p, v)
        sset(options, 'static_mesh_import_data', smi)
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    R['imported_paths'] = list(task.imported_object_paths)
    mesh = None
    for p in task.imported_object_paths:
        o = unreal.EditorAssetLibrary.load_asset(p)
        if isinstance(o, unreal.StaticMesh):
            mesh = o
            R['fresh_path'] = p
            break
    if mesh is not None:
        slots = mesh.get_editor_property('static_materials')
        fresh['slot_count'] = len(slots)
        fresh['slot_names'] = [str(s.get_editor_property('material_slot_name'))
                               for s in slots]
        mats = []
        for s in slots:
            mi = s.get_editor_property('material_interface')
            mats.append(mi.get_name() if mi else None)
        fresh['slot_mats'] = mats
        fresh['accent_emissive_slot'] = any('ACCENT_EMISSIVE' in n.upper()
                                            for n in fresh['slot_names'])
        fresh['accent_emissive_assigned'] = any(
            'ACCENT_EMISSIVE' in n.upper() and m is not None
            for n, m in zip(fresh['slot_names'], mats))
        # texture nodes across assigned materials
        tex = 0
        for m in mats:
            if not m:
                continue
            try:
                mi = unreal.EditorAssetLibrary.load_asset(THROW + '/' + m)
                for e in mi.get_editor_property('expressions'):
                    if 'Texture' in e.get_class().get_name():
                        tex += 1
            except Exception:
                pass
        fresh['texture_nodes'] = tex
        # triangle count on the fresh mesh with the same candidates
        ftri = {}
        for fn in ('get_number_triangles', 'get_triangle_count', 'get_num_triangles'):
            f = getattr(unreal.EditorStaticMeshLibrary, fn, None)
            if f is None:
                continue
            for args in ((mesh, 0), (mesh,)):
                try:
                    ftri['ESML.%s%s' % (fn, len(args))] = f(*args)
                except Exception as e:
                    ftri['ESML.%s%s' % (fn, len(args))] = 'ERR ' + repr(e)[:80]
        for fn in ('get_num_triangles', 'get_triangle_count'):
            f = getattr(mesh, fn, None)
            if f is None:
                continue
            for args in ((0,), ()):
                try:
                    ftri['mesh.%s%s' % (fn, len(args))] = f(*args)
                except Exception as e:
                    ftri['mesh.%s%s' % (fn, len(args))] = 'ERR ' + repr(e)[:80]
        try:
            smes = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
            f = getattr(smes, 'get_number_verts', None)
            if f:
                for args in ((mesh, 0), (mesh,)):
                    try:
                        ftri['SMES.get_number_verts%s' % len(args)] = f(*args)
                    except Exception as e:
                        ftri['SMES.get_number_verts%s' % len(args)] = 'ERR ' + repr(e)[:80]
        except Exception as e:
            ftri['SMES'] = 'ERR ' + repr(e)
        fresh['tri_probe'] = ftri
except Exception as e:
    import traceback
    fresh['error'] = repr(e)
    fresh['traceback'] = traceback.format_exc()[-1500:]
R['fresh'] = fresh
L('FRESH ' + json.dumps(fresh, default=str))

# ------------------------------------------------------ render smoke test
render = {}
if world is not None and spawned is not None and \
        os.environ.get('UEPARITY_MEASURE_ONLY') != '1':
    try:
        rt = unreal.KismetRenderingLibrary.create_render_target_2d(
            world, 320, 400, unreal.TextureRenderTargetFormat.RTF_RGBA8,
            unreal.LinearColor(0.3, 0.3, 0.32, 1.0))
        render['rt'] = bool(rt)
        cap_actor = subs.spawn_actor_from_class(
            unreal.SceneCapture2D, unreal.Vector(300, -300, 150), unreal.Rotator(-10, 40, 0))
        render['cap_actor'] = bool(cap_actor)
        if cap_actor:
            cap = cap_actor.get_component_by_class(unreal.SceneCaptureComponent2D)
            render['cap_component'] = bool(cap)
            if cap:
                sset(cap, 'texture_target', rt)
                sset(cap, 'capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
                cap.capture_scene()
                try:
                    samples = unreal.KismetRenderingLibrary.read_render_target(world, rt)
                    nz = 0
                    for c in samples:
                        v = (c.r, c.g, c.b) if hasattr(c, 'r') else (c[0], c[1], c[2])
                        if v != (0, 0, 0):
                            nz += 1
                    render['sampled'] = len(samples)
                    render['nonzero'] = nz
                except Exception as e:
                    render['readback'] = 'ERR ' + repr(e)
                od = REPO + '/CommandCenter/outputs/ue_verify'
                if not os.path.isdir(od):
                    os.makedirs(od)
                unreal.KismetRenderingLibrary.export_render_target(
                    world, rt, od, '_probe_render.png')
                p = od + '/_probe_render.png'
                render['png_bytes'] = os.path.getsize(p) if os.path.isfile(p) else 0
    except Exception as e:
        import traceback
        render['error'] = repr(e)
        render['traceback'] = traceback.format_exc()[-1500:]
R['render'] = render
L('RENDER ' + json.dumps(render, default=str))

# cleanup spawned probe actors
for a in (spawned,):
    try:
        if a is not None:
            subs.destroy_actor(a)
    except Exception:
        pass

out = REPO + '/CommandCenter/outputs/ue_verify'
if not os.path.isdir(out):
    os.makedirs(out)
with open(out + '/ue_probe.json', 'w') as f:
    json.dump(R, f, indent=2, sort_keys=True, default=str)
L('PROBE_DONE')
