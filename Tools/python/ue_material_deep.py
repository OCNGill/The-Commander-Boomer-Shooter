"""UE 5.8 probe #2 - what do the materials actually render as?

Answers, per material instance:
  * does the parent resolve, and is it a real UMaterial or a transient object
  * how many expressions does the parent have, and what textures does it sample
  * what parameter overrides does the MIC carry (base colour, textures)
  * is the parent package on disk, or does it vanish between sessions

Also records the SceneCaptureSource enum names and the light component
property names actually available in 5.8, so the render script does not
guess.

Read-only. Writes CommandCenter/outputs/ue_verify/ue_material_deep.json
"""

import json
import os

import unreal

REPO = r'C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter'
OUT = REPO + '/CommandCenter/outputs/ue_verify'
SHIPPING = '/Game/Enemies/XCOM'
THROW = '/Game/Tests/UEParity'
NAMES = ['XCOM_Sectoid_PLATE', 'XCOM_Sectoid_ACCENT_EMISSIVE',
         'XCOM_Sectoid_CHITIN', 'XCOM_Floater_CHITIN',
         'XCOM_Chryssalid_PLATE', 'XCOM_Muton_PLATE_OXBLOOD',
         'XCOM_Chitin_Mid', 'XCOM_Armor_Plate', 'XCOM_Eye_Emissive',
         'M_XCOM_Chitin']


def L(m):
    unreal.log('[DEEP] ' + str(m))


def obj_path(base, name):
    return '%s/%s.%s' % (base, name, name)


def deep_material(mat):
    d = {'name': mat.get_name(), 'class': mat.get_class().get_name(),
         'path': mat.get_path_name()}
    d['api_params'] = sorted([p for p in dir(mat)
                              if 'param' in p.lower() or 'override' in p.lower()])
    # parent
    try:
        p = mat.get_editor_property('parent')
    except Exception as e:
        p = None
        d['parent_error'] = repr(e)
    if p is None:
        d['parent'] = None
    else:
        d['parent'] = p.get_path_name()
        d['parent_class'] = p.get_class().get_name()
        try:
            pkg = p.get_outermost()
            d['parent_package'] = pkg.get_path_name()
            d['parent_package_flags'] = str(pkg.get_flags())
        except Exception as e:
            d['parent_package'] = 'n/a:%r' % (e,)
        try:
            ex = p.get_editor_property('expressions')
            d['parent_expressions'] = len(ex)
            d['parent_expr_classes'] = sorted(
                set(e.get_class().get_name() for e in ex))
        except Exception as e:
            d['parent_expressions'] = 'n/a:%r' % (e,)
        # textures sampled by the parent
        tex = []
        try:
            for e in p.get_editor_property('expressions'):
                if 'TextureSample' in e.get_class().get_name():
                    t = e.get_editor_property('texture')
                    tex.append({'node': e.get_name(),
                                'texture': t.get_path_name() if t else None})
        except Exception as e:
            tex = ['n/a:%r' % (e,)]
        d['parent_texture_samples'] = tex
        # constant colour inputs on the parent
        try:
            for e in p.get_editor_property('expressions'):
                if 'Constant3Vector' in e.get_class().get_name():
                    d.setdefault('parent_constants', []).append(
                        {'node': e.get_name(),
                         'value': str(e.get_editor_property('constant'))})
        except Exception:
            pass
    # MIC overrides
    for prop in ('base_property_overrides', 'vector_parameter_values',
                 'texture_parameter_values', 'scalar_parameter_values'):
        try:
            v = mat.get_editor_property(prop)
            d[prop] = len(v)
        except Exception:
            pass
    try:
        v = mat.get_editor_property('base_property_overrides')
        d['base_overrides'] = str(v)
    except Exception:
        pass
    return d


def main():
    res = {'materials': {}, 'enums': {}}

    for base, tag in ((SHIPPING, 'shipping'), (THROW, 'verification')):
        for n in NAMES:
            p = obj_path(base, n)
            if not unreal.EditorAssetLibrary.does_asset_exist(p):
                continue
            m = unreal.EditorAssetLibrary.load_asset(p)
            if m is None:
                continue
            res['materials']['%s/%s' % (tag, n)] = deep_material(m)

    # enum + component surface for the render phase
    try:
        res['enums']['SceneCaptureSource'] = [
            x for x in dir(unreal.SceneCaptureSource) if x.startswith('SCS_')]
    except Exception as e:
        res['enums']['SceneCaptureSource'] = repr(e)
    for cls_name in ('DirectionalLightComponent', 'PointLightComponent',
                     'SpotLightComponent', 'SceneCaptureComponent2D',
                     'SceneCapture2D', 'StaticMeshComponent'):
        c = getattr(unreal, cls_name, None)
        if c is None:
            res['enums'][cls_name] = 'MISSING'
            continue
        res['enums'][cls_name] = sorted(
            [p for p in dir(c)
             if any(k in p.lower() for k in
                    ('light', 'shadow', 'radius', 'capture', 'texture_target',
                     'fov', 'source', 'material', 'static_mesh', 'world_scale',
                     'location', 'rotation'))])

    # what is actually in the engine for grey surfaces
    for p in ('/Engine/BasicShapes/BasicShapeMaterial',
              '/Engine/EngineMaterials/DefaultMaterial',
              '/Engine/EngineMaterials/WorldGridMaterial',
              '/Engine/EngineMaterials/DefaultDiffuse',
              '/Engine/BasicShapes/Plane.Plane'):
        a = unreal.EditorAssetLibrary.load_asset(p)
        res['enums']['asset:' + p] = (a.get_class().get_name()
                                      if a is not None else None)

    path = os.path.join(OUT, 'ue_material_deep.json')
    with open(path, 'w') as f:
        json.dump(res, f, indent=2, sort_keys=True, default=str)
    L('wrote ' + path)
    for k, v in res['materials'].items():
        L('%s parent=%s exprs=%s tex=%s'
          % (k, v.get('parent'), v.get('parent_expressions'),
             v.get('parent_texture_samples')))
    L('END')


main()
