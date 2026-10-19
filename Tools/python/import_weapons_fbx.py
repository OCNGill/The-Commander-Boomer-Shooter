"""Import Blender FBX blockouts into /Game/Weapons as static meshes.

Run:  UnrealEditor-Cmd.exe TheCommander.uproject -run=pythonscript -script=Tools/python/import_weapons_fbx.py -unattended -nosplash
FBX dir is fixed relative to the project: Tools/blender/out
"""
import unreal
import os

PROJ = unreal.SystemLibrary.get_project_directory()          # .../The_Commander_Boomer_Shooter/
FBX_DIR = os.path.join(PROJ, 'Tools', 'blender', 'out')
DEST = '/Game/Weapons'
LINES = []

def L(m):
    t = '[IMPORT] ' + str(m)
    unreal.log(t); LINES.append(t)

ok, failed = [], []
if not os.path.isdir(FBX_DIR):
    L('FBX DIR MISSING: ' + FBX_DIR)
else:
    files = [f for f in os.listdir(FBX_DIR) if f.lower().endswith('.fbx')]
    L('found %d fbx files' % len(files))
    for fname in files:
        try:
            task = unreal.AssetImportTask()
            task.filename = os.path.join(FBX_DIR, fname)
            task.destination_path = DEST
            task.destination_name = os.path.splitext(fname)[0]
            task.replace_existing = True
            task.save = True
            task.automated = True
            options = unreal.FbxImportUI()
            options.import_mesh = True
            options.import_as_skeletal = False
            options.static_mesh_import_data.combine_meshes = True
            options.static_mesh_import_data.generate_lightmap_u_vs = True
            task.options = options
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            imported = list(task.imported_object_paths)
            if imported:
                ok.append((fname, imported))
                L('IMPORTED %s -> %s' % (fname, imported))
            else:
                failed.append(fname)
                L('EMPTY import result for ' + fname)
        except Exception as e:
            failed.append(fname)
            L('FAILED %s: %r' % (fname, e))

# verify on-disk assets
found_assets = unreal.EditorAssetLibrary.list_assets(DEST, recursive=False, include_folder=False) if unreal.EditorAssetLibrary.does_asset_exist(DEST) or True else []
L('assets now under %s: %s' % (DEST, list(found_assets)))
unreal.log('[IMPORT_SUMMARY] ' + 'imported=%d failed=%d' % (len(ok), len(failed)))
