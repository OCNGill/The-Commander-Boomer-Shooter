"""Import X-COM enemy FBX blockouts into /Game/Enemies/XCOM as static meshes.

Run:
  UnrealEditor-Cmd.exe TheCommander.uproject -run=pythonscript \
      -script=Tools/python/import_xcom_fbx.py -unattended -nosplash -stdout -FullStdOutLogOutput

Read-only with respect to Content/Maps/ - no map is ever opened or saved.
Writes Docs/generated/xcom_ue_import_report.json.
"""
import unreal
import os
import json
import traceback

PROJ = unreal.SystemLibrary.get_project_directory()
FBX_DIR = os.path.join(PROJ, 'Tools', 'blender', 'out_xcom')
DEST = '/Game/Enemies/XCOM'
REPORT_JSON = os.path.join(PROJ, 'Docs', 'generated', 'xcom_ue_import_report.json')

ENEMIES = [
    ('XCOM_Sectoid', 'M_XCOM_Chitin'),
    ('XCOM_Viper', 'M_XCOM_Chitin'),
    ('XCOM_Floater', 'M_XCOM_Chitin'),
    ('XCOM_Muton', 'M_XCOM_Chitin'),
    ('XCOM_Chryssalid', 'M_XCOM_Chitin'),
]

# Parent material used for the trivial instance we create for the enemies.
MAT_PARENT = '/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial'


def L(m):
    unreal.log('[XCOMIMPORT] ' + str(m))


def tri_count(mesh):
    """Best-effort LOD0 triangle count across several UE 5.8 API shapes."""
    # 1) EditorStaticMeshLibrary helpers
    for fn in ('get_number_triangles', 'get_triangle_count', 'get_num_triangles'):
        f = getattr(unreal.EditorStaticMeshLibrary, fn, None)
        if f is None:
            continue
        for args in ((mesh, 0), (mesh,), ()):
            try:
                v = f(*args)
                if v:
                    return int(v), fn
            except Exception:
                continue
    # 2) methods directly on the StaticMesh
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
    # 3) StaticMeshDescription
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
    # 4) render data
    try:
        return int(mesh.get_editor_property('render_data').get_num_triangles(0)), 'render_data'
    except Exception:
        pass
    return 0, 'unknown'


def bounds_of(mesh):
    """Return (origin, box_extent_full_cm) for the mesh."""
    origin = None
    extent = None
    src = None
    try:
        b = mesh.get_bounds()
        origin = (b.origin.x, b.origin.y, b.origin.z)
        extent = (b.box_extent.x, b.box_extent.y, b.box_extent.z)
        src = 'get_bounds'
    except Exception:
        try:
            b = mesh.get_editor_property('extended_bounds')
            origin = (b.origin.x, b.origin.y, b.origin.z)
            extent = (b.box_extent.x, b.box_extent.y, b.box_extent.z)
            src = 'extended_bounds'
        except Exception:
            pass
    if extent is None:
        return None, None, 'none'
    return origin, tuple(float(v) * 2.0 for v in extent), src


def carried_materials(mesh):
    names = []
    try:
        slots = mesh.get_editor_property('static_materials')
        for s in slots:
            mi = s.get_editor_property('material_interface')
            names.append(mi.get_name() if mi else '<none>')
    except Exception:
        pass
    return names


def ensure_material(mat_name):
    """Create /Game/Enemies/XCOM/<mat_name> as a MaterialInstanceConstant if absent.
    Returns (asset_or_None, note)."""
    path = '%s/%s' % (DEST, mat_name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        try:
            return unreal.EditorAssetLibrary.load_asset(path), 'existing'
        except Exception:
            pass
    try:
        parent = unreal.EditorAssetLibrary.load_asset(MAT_PARENT)
        if parent is None:
            return None, 'parent-missing'
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        asset = None
        # Prefer a MaterialInstanceConstant off a shipped parent material.
        try:
            f = unreal.MaterialInstanceConstantFactoryNew()
            try:
                f.set_editor_property('initial_parent', parent)
            except Exception:
                pass
            asset = tools.create_asset(mat_name, DEST, unreal.MaterialInstanceConstant, f)
        except Exception:
            asset = None
        if asset is None:
            # Fall back to a plain Material asset.
            try:
                f2 = unreal.MaterialFactoryNew()
                asset = tools.create_asset(mat_name, DEST, unreal.Material, f2)
            except Exception as e:
                return None, 'create-failed: %r' % (e,)
        if asset is None:
            return None, 'create-asset-returned-none'
        # give it a distinct tint if the parent exposes a Color/BaseColor param
        for pname, val in (('BaseColor', unreal.LinearColor(0.35, 0.42, 0.18, 1.0)),
                           ('Color', unreal.LinearColor(0.35, 0.42, 0.18, 1.0))):
            try:
                unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                    asset, pname, val)
                break
            except Exception:
                continue
        try:
            unreal.EditorAssetLibrary.save_asset(path)
        except Exception:
            pass
        return asset, 'created'
    except Exception as e:
        return None, 'failed: %r' % (e,)


def assign_material(mesh, mat, mat_path):
    """Assign mat to every material slot of the static mesh (UE 5.8: StaticMesh.set_material)."""
    try:
        n = 0
        for i in range(len(mesh.get_editor_property('static_materials'))):
            mesh.set_material(i, mat)
            n += 1
        return 'assigned:%s to %d slots' % (mat_path, n)
    except Exception as e:
        try:
            slots = mesh.get_editor_property('static_materials')
            for s in slots:
                s.set_editor_property('material_interface', mat)
            mesh.set_editor_property('static_materials', slots)
            return 'assigned-via-static_materials:%s' % mat_path
        except Exception as e2:
            return 'assign-failed: %r / %r' % (e, e2)


def main():
    results = []
    imported = 0
    failed = 0

    try:
        api = sorted([n for n in dir(unreal.EditorStaticMeshLibrary)
                      if any(k in n.lower() for k in ('tri', 'collision', 'bound'))])
        L('EditorStaticMeshLibrary API probe: %s' % ','.join(api))
    except Exception:
        pass

    if not os.path.isdir(FBX_DIR):
        L('FBX DIR MISSING: %s' % FBX_DIR)
        L('SUMMARY imported=0 failed=5')
        return

    for name, mat_name in ENEMIES:
        fbx_path = os.path.join(FBX_DIR, name + '.fbx')
        entry = {
            'enemy': name,
            'fbx': fbx_path,
            'asset_path': '',
            'triangle_count': 0,
            'triangle_source': 'none',
            'bounds_origin_cm': [0.0, 0.0, 0.0],
            'bounds_extent_cm': [0.0, 0.0, 0.0],
            'bounds_source': 'none',
            'height_cm': 0.0,
            'width_cm': 0.0,
            'depth_cm': 0.0,
            'collision': 'unknown',
            'collision_readback': 'unknown',
            'material': '',
            'material_note': '',
            'status': 'FAIL',
            'error': '',
        }
        try:
            if not os.path.isfile(fbx_path):
                raise IOError('missing fbx %s' % fbx_path)

            task = unreal.AssetImportTask()
            task.filename = fbx_path
            task.destination_path = DEST
            task.destination_name = name
            task.replace_existing = True
            task.save = True
            task.automated = True
            options = unreal.FbxImportUI()

            def sset(obj, prop, val):
                """Set an editor property only if this UE build exposes it."""
                try:
                    obj.set_editor_property(prop, val)
                    return True
                except Exception:
                    return False

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
                # write the mutated struct back onto the import UI
                sset(options, 'static_mesh_import_data', smi)
            task.options = options

            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            paths = list(task.imported_object_paths)
            L('name=%s imported_object_paths=%s' % (name, paths))
            if not paths:
                raise RuntimeError('no imported object paths')

            mesh = None
            mesh_path = ''
            for p in paths:
                obj = unreal.EditorAssetLibrary.load_asset(p)
                if isinstance(obj, unreal.StaticMesh):
                    mesh = obj
                    mesh_path = p
                    break
                if mesh is None and obj is not None:
                    try:
                        subs = obj.get_editor_property('static_materials')
                    except Exception:
                        subs = None
            if mesh is None:
                # fall back: load by expected path
                expected = '%s/%s.%s' % (DEST, name, name)
                obj = unreal.EditorAssetLibrary.load_asset(expected)
                if isinstance(obj, unreal.StaticMesh):
                    mesh = obj
                    mesh_path = expected
            if mesh is None:
                raise RuntimeError('no StaticMesh among %s' % paths)

            entry['asset_path'] = mesh_path
            entry['mesh_object'] = mesh.get_name()

            # ---- collision: Use Complex as Simple (enemies must block player) ----
            coll_status = 'unknown'
            coll_detail = ''
            f = getattr(unreal.EditorStaticMeshLibrary, 'set_collision_complex_as_simple', None)
            if f is not None:
                try:
                    f(mesh)
                    coll_status = 'UseComplexAsSimple'
                    coll_detail = 'EditorStaticMeshLibrary.set_collision_complex_as_simple'
                except Exception as e:
                    coll_status = 'set-failed: %r' % (e,)
            else:
                # UE 5.8 exposes no library helper - drive BodySetup.CollisionTraceFlag.
                try:
                    body = mesh.get_editor_property('body_setup')
                    flag = None
                    for n in dir(unreal.CollisionTraceFlag):
                        if 'COMPLEX_AS_SIMPLE' in n:
                            flag = getattr(unreal.CollisionTraceFlag, n)
                            break
                    if flag is None:
                        raise RuntimeError('no COMPLEX_AS_SIMPLE member on CollisionTraceFlag')
                    body.set_editor_property('collision_trace_flag', flag)
                    coll_status = 'UseComplexAsSimple'
                    coll_detail = 'body_setup.collision_trace_flag=%s' % flag
                except Exception as e:
                    coll_status = 'set-failed: %r' % (e,)
                # extra fallback: legacy StaticMesh.collision_complexity property
                if coll_status != 'UseComplexAsSimple':
                    try:
                        cplx = None
                        for n in dir(unreal.CollisionComplexity):
                            if 'COMPLEX_AS_SIMPLE' in n:
                                cplx = getattr(unreal.CollisionComplexity, n)
                                break
                        if cplx is not None:
                            mesh.set_editor_property('collision_complexity', cplx)
                            coll_status = 'UseComplexAsSimple'
                            coll_detail = 'mesh.collision_complexity=%s' % cplx
                    except Exception as e:
                        coll_detail += '; legacy-fallback-failed: %r' % (e,)
            entry['collision'] = coll_status
            entry['collision_detail'] = coll_detail

            # UE 5.8 has no StaticMesh.collision_complexity property; the authoritative
            # value is BodySetup.CollisionTraceFlag. Read that FIRST.
            rb = ''
            try:
                body = mesh.get_editor_property('body_setup')
                rb = str(body.get_editor_property('collision_trace_flag'))
            except Exception:
                pass
            if not rb:
                try:
                    rb = str(mesh.get_editor_property('collision_complexity'))
                except Exception:
                    pass
            entry['collision_readback'] = rb or coll_status
            entry['collision_is_complex_as_simple'] = 'CTF_USE_COMPLEX_AS_SIMPLE' in rb

            # ---- material ----
            # The FBXs carry their own authored material set (chitin / eyes / armour).
            # Keep them when present; only fall back to a created UE instance when the
            # FBX brought none.
            mats = carried_materials(mesh)
            if any(m and m != '<none>' for m in mats):
                entry['material'] = ', '.join(mats)
                entry['material_note'] = 'kept-fbx-authored'
            else:
                mat_asset, note = ensure_material(mat_name)
                if mat_asset is not None:
                    assign_note = assign_material(mesh, mat_asset, '%s/%s' % (DEST, mat_name))
                    entry['material'] = '%s/%s' % (DEST, mat_name)
                    entry['material_note'] = '%s/%s' % (note, assign_note)
                else:
                    entry['material'] = ''
                    entry['material_note'] = 'no material created (%s)' % (note,)

            # ---- triangles + bounds ----
            tris, tsrc = tri_count(mesh)
            entry['triangle_count'] = tris
            entry['triangle_source'] = tsrc
            origin, extent, bsrc = bounds_of(mesh)
            if extent is not None:
                entry['bounds_origin_cm'] = [round(v, 2) for v in origin]
                entry['bounds_extent_cm'] = [round(v, 2) for v in extent]
                entry['bounds_source'] = bsrc
                entry['height_cm'] = round(extent[2], 2)
                entry['width_cm'] = round(extent[0], 2)
                entry['depth_cm'] = round(extent[1], 2)

            # save the static mesh package only (never a map)
            try:
                unreal.EditorAssetLibrary.save_asset(mesh_path)
            except Exception as e:
                entry['material_note'] += '; save-asset-failed: %r' % (e,)

            entry['status'] = 'OK'
            imported += 1
            L('name=%s status=OK mesh=%s tris=%d path=%s' % (name, mesh.get_name(), tris, mesh_path))
        except Exception as e:
            failed += 1
            entry['error'] = repr(e)
            entry['status'] = 'FAIL'
            L('name=%s status=FAIL mesh= tris=0 path= error=%r' % (name, e))
            unreal.log(traceback.format_exc())
        results.append(entry)

    try:
        generated = unreal.SystemLibrary.get_datetime_now().isoformat()
    except Exception:
        try:
            generated = str(unreal.SystemLibrary.get_datetime_now())
        except Exception:
            generated = ''

    report = {
        'generated_utc': generated,
        'project': PROJ,
        'fbx_dir': FBX_DIR,
        'destination': DEST,
        'enemies': results,
        'summary': 'imported=%d failed=%d' % (imported, failed),
    }
    try:
        os.makedirs(os.path.dirname(REPORT_JSON), exist_ok=True)
        with open(REPORT_JSON, 'w') as fh:
            json.dump(report, fh, indent=2)
        L('report written: %s' % REPORT_JSON)
    except Exception as e:
        L('report write failed: %r' % (e,))

    L('SUMMARY imported=%d failed=%d' % (imported, failed))


main()
