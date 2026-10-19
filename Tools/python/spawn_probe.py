"""Spawn probe: engine mesh vs FBX mesh, loaded map vs fresh level, both spawn APIs."""
import unreal
import json

MAP = '/Game/Maps/M_Blockout01'
def L(m):
    unreal.log('[PROBE] ' + str(m))

# --- A: loaded map ---
unreal.EditorLoadingAndSavingUtils.load_map(MAP)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
L('world after load_map: %r outer=%r' % (w, w.get_outer() if w else None))
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
L('actor_sub=%r' % sub)

tests = []
def T(name, fn):
    try:
        r = fn()
        tests.append((name, bool(r), str(r.get_actor_label()) if r else '-'))
        L('TEST %-40s -> %s' % (name, 'OK:' + str(r.get_actor_label()) if r else 'NULL'))
    except Exception as e:
        tests.append((name, False, 'EXC:%r' % e))
        L('TEST %-40s -> EXC %r' % (name, e))

eng = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube')
fbx = unreal.EditorAssetLibrary.load_asset('/Game/Weapons/E_BarnacleDrone')
L('eng=%r fbx=%r' % (eng, fbx))
loc = unreal.Vector(0, -800, 300)

T('subsystem+engine mesh', lambda: sub.spawn_actor_from_object(eng, loc, unreal.Rotator()))
T('subsystem+fbx mesh',    lambda: sub.spawn_actor_from_object(fbx, loc, unreal.Rotator()))
T('EditorLevelLibrary+engine mesh', lambda: unreal.EditorLevelLibrary.spawn_actor_from_object(eng, loc, unreal.Rotator()))
T('EditorLevelLibrary+fbx mesh',    lambda: unreal.EditorLevelLibrary.spawn_actor_from_object(fbx, loc, unreal.Rotator()))
T('subsystem+StaticMeshActor class', lambda: sub.spawn_actor_from_class(unreal.StaticMeshActor, loc, unreal.Rotator()))

# if class-spawn worked, try assigning mesh manually
act = sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0,-700,300), unreal.Rotator())
if act:
    ok = False
    try:
        act.static_mesh_component.set_static_mesh(fbx); ok = True
    except Exception as e:
        L('manual assign EXC %r' % e)
    lab = 'PROBE_manual'
    act.set_actor_label(lab)
    L('manual assign fbx onto spawned actor: %s' % ok)

# --- B: FRESH level, same subsystem pattern as run2 (control) ---
try:
    unreal.EditorLevelLibrary.new_level('/Game/Maps/M_ProbeFresh')
    sub2 = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    r = sub2.spawn_actor_from_object(eng, loc, unreal.Rotator())
    L('CONTROL fresh level + engine mesh -> %s' % ('OK' if r else 'NULL'))
    r2 = sub2.spawn_actor_from_object(fbx, loc, unreal.Rotator())
    L('CONTROL fresh level + fbx mesh -> %s' % ('OK' if r2 else 'NULL'))
except Exception as e:
    L('CONTROL EXC %r' % e)

unreal.log('[PROBE_SUMMARY] ' + json.dumps({'tests': tests}))
