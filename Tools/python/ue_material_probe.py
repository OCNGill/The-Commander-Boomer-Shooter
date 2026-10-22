"""UE 5.8 probe - measure material identity, parents, textures and slot names.

Read-only. Writes CommandCenter/outputs/ue_verify/ue_material_probe.json.
Runs with -nullrhi (no shader compile, fast).
"""

import json
import os

import unreal

REPO = r'C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter'
OUT = REPO + '/CommandCenter/outputs/ue_verify'
SHIPPING = '/Game/Enemies/XCOM'
THROW = '/Game/Tests/UEParity'
ENEMIES = ['XCOM_Sectoid', 'XCOM_Viper', 'XCOM_Floater', 'XCOM_Muton',
           'XCOM_Chryssalid']


def L(m):
    unreal.log('[PROBE] ' + str(m))


def obj_path(base, name):
    return '%s/%s.%s' % (base, name, name)


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


def describe(mat):
    d = {'name': mat.get_name(), 'class': mat.get_class().get_name(),
         'path': mat.get_path_name()}
    # parent
    try:
        p = mat.get_editor_property('parent')
        d['parent'] = p.get_path_name() if p is not None else None
    except Exception as e:
        d['parent'] = 'n/a:%r' % (e,)
    # texture params
    try:
        params = mat.get_editor_property('texture_parameters')
        d['texture_parameters'] = [str(x.get_editor_property('parameter_name'))
                                   for x in params]
    except Exception:
        d['texture_parameters'] = []
    # vector params (base color etc.)
    try:
        vp = mat.get_editor_property('vector_parameters')
        d['vector_parameters'] = [str(x.get_editor_property('parameter_name'))
                                  for x in vp]
    except Exception:
        d['vector_parameters'] = []
    # expressions if it is a real Material
    try:
        ex = mat.get_editor_property('expressions')
        d['expressions'] = len(ex)
        d['expr_classes'] = sorted(set(e.get_class().get_name() for e in ex))
    except Exception:
        d['expressions'] = None
    # referenced textures
    try:
        from unreal import MaterialEditingLibrary
        t = MaterialEditingLibrary.get_material_texture_property_names(mat)
        d['texture_props'] = [str(x) for x in t]
    except Exception as e:
        d['texture_props'] = 'n/a:%r' % (e,)
    return d


def main():
    res = {'enemies': {}, 'shipping_materials': {}, 'world': {}}

    # what is loaded / what level is open
    try:
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        w = ues.get_editor_world()
        if w is not None:
            res['world'] = {'name': w.get_name(),
                            'path': w.get_path_name(),
                            'actors': len(w.get_actors()) if hasattr(
                                w, 'get_actors') else None}
    except Exception as e:
        res['world'] = {'error': repr(e)}
    L('world: %r' % (res['world'],))

    # every material in the shipping folder
    try:
        for a in unreal.EditorAssetLibrary.list_assets(SHIPPING, True, False):
            m = unreal.EditorAssetLibrary.load_asset(a)
            if m is not None and 'Material' in m.get_class().get_name():
                res['shipping_materials'][a] = describe(m)
    except Exception as e:
        res['shipping_materials_error'] = repr(e)

    for name in ENEMIES:
        rec = {}
        for tag, base in (('shipping', SHIPPING), ('verification', THROW)):
            p = obj_path(base, name)
            if not unreal.EditorAssetLibrary.does_asset_exist(p):
                rec[tag] = {'error': 'missing ' + p}
                continue
            mesh = unreal.EditorAssetLibrary.load_asset(p)
            if mesh is None:
                rec[tag] = {'error': 'load failed ' + p}
                continue
            slots = slots_of(mesh)
            rec[tag] = {
                'slots': [s for s, _m in slots],
                'assigned': [(m.get_path_name() if m else None)
                             for _s, m in slots],
                'materials': [describe(m) for _s, m in slots if m is not None],
            }
        res['enemies'][name] = rec
        L('%s done' % name)

    path = os.path.join(OUT, 'ue_material_probe.json')
    with open(path, 'w') as f:
        json.dump(res, f, indent=2, sort_keys=True, default=str)
    L('wrote ' + path)
    unreal.log('[PROBE] END')


main()
