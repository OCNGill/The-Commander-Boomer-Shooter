"""Rebuild the SW pit as a REAL recessed pit with a hole in the floor, and rebuild the NE ramp.

WHY (2026-10-21): the level builder's FINDING 1 - "BO_Floor is a single unbroken 40x40m plane at z=0.0m with no
hole cut in it, so the pit, its rim, ENC_Brute_Pit, PU_KeyRed_Pit and PU_Health_Pit sit under the floor surface
and cannot be seen or entered. The renders cut the floor open so the intent is visible." The renders showed a pit
the MAP DID NOT CONTAIN. This makes the map match the intent. Also BO_Ramp_NE sat at (950,950) - INSIDE the
platform footprint (800..1600) - so it was buried in the platform and never reached the floor.

Everything is derived from the live actors: the arena floor surface height S is read off the actual floor mesh
(plane -> S = loc.z, cube -> S = loc.z + scale.z*50), the floor is re-cut around a hole with the SAME mesh, the
pit floor is placed 100u below S, and the pit walls are 200u tall so they stand 100u proud of the surface (too
high to step over - the default UE character step height is 45u). The only way in is the 200u (2m) gap in the
east wall, which faces the arena centre.

RUN: UnrealEditor-Cmd.exe TheCommander.uproject -run=pythonscript -script=Tools/python/fix_pit_and_ramp.py
"""
import unreal, json, os, math, time

REPO = r"C:\Users\Gillsystems Laptop\source\repos\OCNGill\The_Commander_Boomer_Shooter"
JSON = os.path.join(REPO, "Docs", "generated", "level_transforms.json")
CUBE = "/Engine/BasicShapes/Cube.Cube"
PLANE = "/Engine/BasicShapes/Plane.Plane"
MAP = "/Game/Maps/M_Blockout01"

rows = {}
try:
    for r in json.load(open(JSON, encoding="utf-8")):
        if r.get("label"):
            rows[r["label"]] = r
except Exception as e:
    unreal.log("[FIX] no transform json: %s" % e)

sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
actors = {}
for a in sub.get_all_level_actors():
    try:
        actors[a.get_actor_label()] = a
    except Exception:
        pass
unreal.log("[FIX] actors found: %d" % len(actors))


def destroy(a):
    for fn in (lambda x: sub.destroy_actor(x),
               lambda x: unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(x),
               lambda x: unreal.EditorLevelLibrary.destroy_actor(x)):
        try:
            if fn(a):
                return True
        except Exception:
            continue
    return False


def spawn(label, loc, scale, rot=(0.0, 0.0, 0.0), mesh=None):
    old = actors.get(label)
    if old is not None:
        destroy(old)
        actors.pop(label, None)
    a = sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc),
                                   unreal.Rotator(pitch=rot[0], yaw=rot[1], roll=rot[2]))
    if a is None:
        raise RuntimeError("spawn returned NULL for " + label)
    a.set_actor_label(label)
    a.static_mesh_component.set_static_mesh(unreal.load_asset(mesh or CUBE))
    a.set_actor_scale3d(unreal.Vector(*scale))
    actors[label] = a
    return a


def move(label, loc=None, scale=None):
    a = actors.get(label)
    if a is None:
        unreal.log("[FIX] MISSING for move: " + label)
        return None
    if loc is not None:
        a.set_actor_location(unreal.Vector(*loc))
    if scale is not None:
        a.set_actor_scale3d(unreal.Vector(*scale))
    return a


# ---------------------------------------------------------------- the arena floor surface
floor = actors.get("BO_Floor")
if floor is None:
    unreal.log("[FIX] *** BO_Floor not found - aborting, refusing to guess the floor ***")
    raise SystemExit(1)
mesh_name = floor.static_mesh_component.get_static_mesh().get_name() if floor.static_mesh_component.get_static_mesh() else "?"
floc = floor.get_actor_location()
fsc = floor.get_actor_scale3d()
is_plane = "Plane" in str(mesh_name)
S = floc.z if is_plane else floc.z + fsc.z * 50.0
unreal.log("[FIX] arena floor mesh=%s scale=(%.2f,%.2f,%.2f) -> surface S=%.0f" % (
    mesh_name, fsc.x, fsc.y, fsc.z, S))
FLOOR_MESH = PLANE if is_plane else CUBE
FLOOR_SZ = fsc.z

# ---------------------------------------------------------------- 1. cut the floor around the hole
HX0, HX1 = -1525.0, -875.0
HY0, HY1 = -1525.0, -1075.0
AX0, AX1, AY0, AY1 = -2000.0, 2000.0, -2000.0, 2000.0


def seg(label, x0, x1, y0, y1):
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    spawn(label, (cx, cy, floc.z), ((x1 - x0) / 100.0, (y1 - y0) / 100.0, FLOOR_SZ), mesh=FLOOR_MESH)
    unreal.log("[FIX] %s x[%s..%s] y[%s..%s]" % (label, x0, x1, y0, y1))


destroy(floor)
actors.pop("BO_Floor", None)
unreal.log("[FIX] removed the unbroken floor")
seg("BO_Floor_N", AX0, AX1, HY1, AY1)
seg("BO_Floor_S", AX0, AX1, AY0, HY0)
seg("BO_Floor_E", HX1, AX1, HY0, HY1)
seg("BO_Floor_W", AX0, HX0, HY0, HY1)

# ---------------------------------------------------------------- 2. the pit
PZ = S - 100.0
move("BO_PitFloor", loc=(-1200.0, -1200.0, PZ - 25.0), scale=(10.0, 10.0, 0.5))
unreal.log("[FIX] pit floor surface z=%.0f (100u below the arena floor at %.0f)" % (PZ, S))

move("BO_PitRim_W", loc=(-1500.0, -1300.0, S), scale=(0.5, 4.5, 2.0))
move("BO_PitRim_S", loc=(-1200.0, -1500.0, S), scale=(5.5, 0.5, 2.0))
move("BO_PitRim_N", loc=(-1200.0, -1100.0, S), scale=(5.5, 0.5, 2.0))
spawn("BO_PitRim_E1", (-900.0, -1462.5, S), (0.5, 1.25, 2.0))
spawn("BO_PitRim_E2", (-900.0, -1137.5, S), (0.5, 1.25, 2.0))
old_e = actors.get("BO_PitRim_E")
if old_e is not None:
    destroy(old_e)
    actors.pop("BO_PitRim_E", None)
unreal.log("[FIX] pit walls rebuilt - 200u tall, 2m entrance gap in the east wall y[-1400,-1200]")

for lbl in ("PU_KeyRed_Pit", "PU_Health_Pit", "ENC_Brute_Pit"):
    a = actors.get(lbl)
    if a is None:
        continue
    loc = a.get_actor_location()
    a.set_actor_location(unreal.Vector(loc.x, loc.y, PZ))
    unreal.log("[FIX] %s set onto the pit floor z=%.0f" % (lbl, PZ))

# ---------------------------------------------------------------- 3. the ramp to the NE platform
plat = rows.get("BO_Platform_NE")
if plat:
    px, py, pz = [float(v) for v in plat["loc"]]
    psx, psy, psz = [float(v) for v in plat["scale"]]
    top = pz + psz * 50.0
    half_y = psy * 50.0 / 2.0
    run = 1500.0
    length = math.hypot(run, top - S)
    angle = math.degrees(math.atan2(top - S, run))
    mid_y = (py - half_y) - run / 2.0
    mid_z = S + (top - S) / 2.0
    width = 600.0
    for sign in (-1.0, 1.0):
        a = spawn("BO_Ramp_NE", (px, mid_y, mid_z), (width / 100.0, length / 100.0, 0.5),
                  rot=(0.0, 0.0, sign * angle))
        xf = a.get_actor_transform()
        hi = xf.transform_location(unreal.Vector(0.0, 50.0, 0.0))
        lo = xf.transform_location(unreal.Vector(0.0, -50.0, 0.0))
        ok = (abs(hi.z - top) < 150.0) and (abs(lo.z - S) < 150.0)
        unreal.log("[FIX] ramp roll=%+0.1f  high end z=%.0f (want %.0f)  low end z=%.0f (want %.0f)  ok=%s" % (
            sign * angle, hi.z, top, lo.z, S, ok))
        if ok:
            unreal.log("[FIX] BO_Ramp_NE OK - length=%.0f pitch=%.1f deg" % (length, angle))
            break
    else:
        unreal.log("[FIX] *** ramp tilt could not be verified - check the log ***")
else:
    unreal.log("[FIX] BO_Platform_NE missing from the json - ramp untouched")

# ---------------------------------------------------------------- 4. save and verify the FILE
_map_file = os.path.join(REPO, "Content", "Maps", "M_Blockout01.umap")
_before = os.path.getsize(_map_file) if os.path.exists(_map_file) else -1
unreal.EditorLoadingAndSavingUtils.save_map(MAP)
try:
    unreal.EditorAssetLibrary.save_asset(MAP, only_if_is_dirty=False)
except Exception as e:
    unreal.log("[FIX] save_asset failed: %s" % e)
try:
    unreal.EditorLevelLibrary.save_current_level()
except Exception as e:
    unreal.log("[FIX] save_current_level failed: %s" % e)
time.sleep(2.0)
_after = os.path.getsize(_map_file) if os.path.exists(_map_file) else -1
unreal.log("[FIX] on-disk umap before=%d after=%d grew=%s" % (_before, _after, _after > _before))
unreal.log("[FIX] SAVE_PERSISTED bytes=%d" % _after if _after > _before else "[FIX] *** THE SAVE DID NOT PERSIST ***")
unreal.log("[FIX] done")
