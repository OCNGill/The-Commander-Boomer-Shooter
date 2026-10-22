"""UE 5.8 - PHASE A: relocate the per-enemy materials and re-bind the shipping meshes.

STATE OF THE WORLD (measured in-engine, not assumed):
  * The five shipping meshes at /Game/Enemies/XCOM have the CORRECT slot NAMES
    (XCOM_Sectoid_PLATE, XCOM_Sectoid_CHITIN, ...) but every slot currently
    points at WorldGridMaterial.
  * The verification copies at /Game/Tests/UEParity have the same slot names
    bound to the per-enemy materials (XCOM_Sectoid_PLATE, ...), which are
    MaterialInstanceConstants over /InterchangeAssets/Materials/
    FBXLegacyPhongSurfaceMaterial and each carry their own colour overrides.
  * Those per-enemy material ASSETS live ONLY in the throwaway folder, which
    is deleted at cleanup. So they are RELOCATED (renamed - not recreated,
    not re-authored) into /Game/Enemies/XCOM first, and only then bound.
    A shipping mesh must not reference an asset that the cleanup deletes.
  * Nothing in Content/Maps is opened, modified or saved.

Writes CommandCenter/outputs/ue_verify/ue_rebind_report.json as it goes.
"""

import json
import os
import traceback

import unreal

REPO = os.environ.get('UE_REPO', r'C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter')
OUT = REPO + '/CommandCenter/outputs/ue_verify'
SHIPPING = '/Game/Enemies/XCOM'
THROW = '/Game/Tests/UEParity'
ENEMIES = ['XCOM_Sectoid', 'XCOM_Viper', 'XCOM_Floater', 'XCOM_Muton',
           'XCOM_Chryssalid']


def L(m):
    unreal.log('[REBIND] ' + str(m))


def obj_path(base, name):
    return '%s/%s.%s' % (base, name, name)


def write_json(path, obj):
    try:
        d = os.path.dirname(path)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        with open(path, 'w') as f:
            json.dump(obj, f, indent=2, sort_keys=True, default=str)
        L('wrote ' + path)
    except Exception as e:
        L('write_json failed %r' % (e,))


def slots_of(mesh):
    out = []
    for s in mesh.get_editor_property('static_materials'):
        try:
            name = str(s.get_editor_property('material_slot_name'))
        except Exception:
            name = '<none>'
        try:
            mi = s.get_editor_property('material_interface')
        except Exception:
            mi = None
        out.append((name, mi))
    return out


def param_rows(mat, prop):
    """Vector/scalar override rows, tolerant of 5.8 property naming."""
    rows = []
    try:
        vals = mat.get_editor_property(prop)
    except Exception:
        return rows
    for v in vals:
        name = None
        for p in ('parameter_info', 'parameter_name'):
            try:
                o = v.get_editor_property(p)
                name = str(o.get_editor_property('name')) if hasattr(
                    o, 'get_editor_property') else str(o)
                if name and name != 'None':
                    break
            except Exception:
                continue
        val = None
        for p in ('parameter_value', 'value'):
            try:
                val = str(v.get_editor_property(p))
                break
            except Exception:
                continue
        rows.append({'name': name, 'value': val})
    return rows


def describe(mat):
    if mat is None:
        return None
    d = {'name': mat.get_name(), 'class': mat.get_class().get_name(),
         'path': mat.get_path_name()}
    try:
        p = mat.get_editor_property('parent')
        d['parent'] = p.get_path_name() if p else None
        d['parent_class'] = p.get_class().get_name() if p else None
    except Exception as e:
        d['parent'] = 'err:%r' % (e,)
    d['vectors'] = param_rows(mat, 'vector_parameter_values')
    d['scalars'] = param_rows(mat, 'scalar_parameter_values')
    try:
        d['textures'] = [str(t.get_editor_property('parameter_name'))
                         for t in mat.get_editor_property(
                             'texture_parameter_values')]
    except Exception:
        d['textures'] = []
    return d


def relocate(src, dst):
    if unreal.EditorAssetLibrary.does_asset_exist(dst):
        return 'already_present'
    if not unreal.EditorAssetLibrary.does_asset_exist(src):
        return 'missing_source'
    try:
        if unreal.EditorAssetLibrary.rename_asset(src, dst):
            try:
                if unreal.EditorAssetLibrary.does_asset_exist(src):
                    unreal.EditorAssetLibrary.delete_asset(src)
            except Exception:
                pass
            return 'renamed'
    except Exception as e:
        L('rename failed %r' % (e,))
    try:
        if unreal.EditorAssetLibrary.duplicate_asset(src, dst):
            return 'duplicated'
    except Exception as e:
        L('duplicate failed %r' % (e,))
    return 'failed'


def main():
    report = {'shipping': SHIPPING, 'authority': THROW, 'enemies': {},
              'api': {}}

    # --- record the render API signatures we will need for phase B ---------
    for libname in ('RenderingLibrary', 'KismetRenderingLibrary'):
        lib = getattr(unreal, libname, None)
        if lib is None:
            continue
        for fn in ('create_render_target2d', 'export_render_target',
                   'read_render_target', 'create_render_target_2d'):
            f = getattr(lib, fn, None)
            if f is not None:
                report['api']['%s.%s' % (libname, fn)] = str(f.__doc__)[:900]
    for cls in ('SceneCaptureComponent2D', 'DirectionalLightComponent',
                'PointLightComponent', 'StaticMeshComponent'):
        c = getattr(unreal, cls, None)
        if c is not None:
            for prop in ('source_radius', 'cast_shadows', 'intensity',
                         'light_color', 'texture_target', 'capture_source',
                         'fov_angle'):
                if hasattr(c, prop):
                    report['api']['%s.%s' % (cls, prop)] = 'present'

    # --- world facts (for the shot phase) ---------------------------------
    try:
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        w = ues.get_editor_world()
        if w is not None:
            # UE 5.8 removed UWorld::GetActors from the Python surface.
            # EditorActorSubsystem.get_all_level_actors() is the supported
            # editor-side enumeration.
            _as = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            report['world'] = {'name': w.get_name(),
                               'path': w.get_path_name(),
                               'actors': sorted(set(a.get_class().get_name()
                                                    for a in _as.get_all_level_actors()))}
    except Exception as e:
        report['world'] = {'error': repr(e)}

    for name in ENEMIES:
        rec = {'enemy': name, 'ok': False}
        try:
            ship = unreal.EditorAssetLibrary.load_asset(obj_path(SHIPPING, name))
            ver = unreal.EditorAssetLibrary.load_asset(obj_path(THROW, name))
            if ship is None:
                rec['error'] = 'no shipping mesh'
            elif ver is None:
                rec['error'] = 'no verification copy'
            else:
                authority = {}
                for s, m in slots_of(ver):
                    if m is not None:
                        authority[s] = m.get_name()
                rec['authority_map'] = authority
                rec['before'] = [(s, m.get_name() if m else None)
                                 for s, m in slots_of(ship)]

                # 1) relocate the per-enemy material assets into the shipping
                #    folder so the binding survives the throwaway cleanup
                moves = {}
                for slot, mat_name in sorted(authority.items()):
                    src = obj_path(THROW, mat_name)
                    dst = obj_path(SHIPPING, mat_name)
                    res = relocate(src, dst)
                    moves[slot] = {'material': mat_name, 'src': src,
                                   'dst': dst, 'result': res}
                rec['material_moves'] = moves

                # 2) bind the shipping mesh by SLOT NAME
                new_slots = []
                bind = []
                for s, _old in slots_of(ship):
                    mat_name = authority.get(s)
                    mat = None
                    if mat_name:
                        mat = unreal.EditorAssetLibrary.load_asset(
                            obj_path(SHIPPING, mat_name))
                        if mat is None:
                            mat = unreal.EditorAssetLibrary.load_asset(
                                obj_path(THROW, mat_name))
                    sm = unreal.StaticMaterial()
                    sm.set_editor_property('material_slot_name', s)
                    sm.set_editor_property('material_interface', mat)
                    new_slots.append(sm)
                    bind.append({'slot': s, 'assigned': mat.get_name()
                                 if mat else None})
                rec['bind'] = bind
                ship.set_editor_property('static_materials', new_slots)
                try:
                    ship.modify()
                except Exception:
                    pass
                rec['saved'] = bool(unreal.EditorAssetLibrary.save_asset(
                    obj_path(SHIPPING, name)))

                # 3) re-measure from disk - quote, do not assert
                check = unreal.EditorAssetLibrary.load_asset(
                    obj_path(SHIPPING, name))
                after = slots_of(check)
                rec['after'] = [{'slot': s,
                                 'assigned': m.get_name() if m else None,
                                 'material': describe(m)}
                                for s, m in after]
                rec['matches_authority'] = all(
                    authority.get(s) == (m.get_name() if m else None)
                    for s, m in after)
                rec['ok'] = bool(rec['saved'] and rec['matches_authority']
                                 and all(m for _s, m in after))
                L('%s ok=%s after=%s'
                  % (name, rec['ok'],
                     [(s, m.get_name() if m else None) for s, m in after]))
        except Exception as e:
            rec['error'] = repr(e)
            rec['traceback'] = traceback.format_exc()[-1200:]
            L('%s ERROR %r' % (name, e))
        report['enemies'][name] = rec
        write_json(os.path.join(OUT, 'ue_rebind_report.json'), report)

    write_json(os.path.join(OUT, 'ue_rebind_report.json'), report)
    L('PHASE A COMPLETE ok=%d/5' % sum(1 for v in report['enemies'].values()
                                        if v.get('ok')))


main()
