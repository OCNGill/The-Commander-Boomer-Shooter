"""UE 5.8 probe #3 - the actual colour data carried by each material.

For every MaterialInstanceConstant in /Game/Enemies/XCOM and
/Game/Tests/UEParity, dump the vector/scalar parameter overrides by name and
value. This is what makes XCOM_Sectoid_PLATE differ from
XCOM_Sectoid_CHITIN, and it is what the shots will actually show.

Also checks whether the Interchange parent material exists on disk, and
whether it is a real asset or a session-transient object.

Read-only. Writes CommandCenter/outputs/ue_verify/ue_material_colors.json
"""

import json
import os

import unreal

REPO = r'C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter'
OUT = REPO + '/CommandCenter/outputs/ue_verify'
FOLDERS = ['/Game/Enemies/XCOM', '/Game/Tests/UEParity']


def L(m):
    unreal.log('[COL] ' + str(m))


def mat_colors(mat):
    d = {'name': mat.get_name(), 'class': mat.get_class().get_name(),
         'path': mat.get_path_name()}
    vec = []
    try:
        for v in mat.get_editor_property('vector_parameter_values'):
            vec.append({
                'name': str(v.get_editor_property('parameter_name')),
                'value': str(v.get_editor_property('parameter_value')),
            })
    except Exception as e:
        d['vec_error'] = repr(e)
    d['vectors'] = vec
    sca = []
    try:
        for v in mat.get_editor_property('scalar_parameter_values'):
            sca.append({
                'name': str(v.get_editor_property('parameter_name')),
                'value': str(v.get_editor_property('parameter_value')),
            })
    except Exception as e:
        d['sca_error'] = repr(e)
    d['scalars'] = sca
    try:
        p = mat.get_editor_property('parent')
        d['parent'] = p.get_path_name() if p else None
        if p is not None:
            # is the parent a persistent asset on disk?
            d['parent_on_disk'] = bool(
                unreal.EditorAssetLibrary.does_asset_exist(p.get_path_name()))
            d['parent_is_transient'] = bool(
                p.get_outermost().get_name().startswith('/Temp/')
                or p.get_outermost().get_name().startswith('/Engine/Transient'))
            d['parent_package_name'] = p.get_outermost().get_name()
    except Exception as e:
        d['parent_error'] = repr(e)
    return d


def main():
    res = {'materials': {}, 'interchange_parent': {}}

    for folder in FOLDERS:
        try:
            assets = unreal.EditorAssetLibrary.list_assets(folder, True, False)
        except Exception as e:
            res['list_error_' + folder] = repr(e)
            continue
        for a in assets:
            m = unreal.EditorAssetLibrary.load_asset(a)
            if m is None or 'Material' not in m.get_class().get_name():
                continue
            res['materials'][a] = mat_colors(m)

    # does the Interchange parent live on disk?
    for p in ('/InterchangeAssets/Materials/FBXLegacyPhongSurfaceMaterial',
              '/InterchangeAssets/Materials/FBXLegacyPhongSurfaceMaterial'
              '.FBXLegacyPhongSurfaceMaterial'):
        res['interchange_parent'][p] = bool(
            unreal.EditorAssetLibrary.does_asset_exist(p))
    try:
        res['interchange_parent']['list'] = [
            x for x in unreal.EditorAssetLibrary.list_assets(
                '/InterchangeAssets', True, False)]
    except Exception as e:
        res['interchange_parent']['list'] = repr(e)

    path = os.path.join(OUT, 'ue_material_colors.json')
    with open(path, 'w') as f:
        json.dump(res, f, indent=2, sort_keys=True, default=str)
    L('wrote ' + path)
    for k, v in res['materials'].items():
        L('%s -> %s' % (k.split('/')[-1],
                        [(x['name'], x['value'][:40]) for x in v['vectors']]))
    L('END')


main()
