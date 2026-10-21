"""fix_pit_and_ramp.py - cut a REAL hole in the arena floor for the SW pit, and rebuild the NE ramp.

WHY (2026-10-21): the level builder's FINDING 1 - "BO_Floor is a single unbroken 40x40m plane at z=0.0m
with no hole cut in it, so the pit, its rim, ENC_Brute_Pit, PU_KeyRed_Pit and PU_Health_Pit sit under the
floor surface and cannot be seen or entered. The renders cut the floor open so the intent is visible."
The renders showed a pit the MAP DID NOT CONTAIN. This makes the map match the intent.

Also: BO_Ramp_NE sat at (950,950) - INSIDE the platform footprint (800..1600) - so it was buried in the
platform and never reached the floor.

EVERYTHING IS READ FROM THE LIVE ACTORS (not from a stale JSON): the arena floor surface height S comes
off the actual floor mesh (plane -> S = loc.z, cube -> S = loc.z + scale.z*50), the platform's top and
footprint come off BO_Platform_NE, and the ramp's world endpoints are measured off the spawned actor's own
right vector. No guessing.

v2 fixes the v1 crashes:
  * v1 used unreal.UnrealEditorSubsystem.get_all_level_actors -> AttributeError (the class is
    unreal.EditorActorSubsystem - see ensure_base_geometry.py line 38, the proven pattern).
  * v1 never loaded the map, so a commandlet world would be empty.
  * v1 read the platform from a JSON key ("label") that the base actors do not have.
  * v1's ramp used a JSON half-extent that was half the true value and verified the tilt through
    Transform.transform_location, which is not a safe API.
  * v1's ramp ran straight through BO_Cover_06 at (1400,0).

RUN: UnrealEditor-Cmd.exe TheCommander.uproject -run=pythonscript -script=Tools/python/fix_pit_and_ramp.py
"""
import unreal
import os
import math
import time
import runpy

REPO = r"C:\Users\Gillsystems Laptop\source\repos\OCNGill\The_Commander_Boomer_Shooter"
DUMP = os.path.join(REPO, "Tools", "python", "dump_level_transforms.py")
MAP = "/Game/Maps/M_Blockout01"
CUBE = "/Engine/BasicShapes/Cube.Cube"
PLANE = "/Engine/BasicShapes/Plane.Plane"


def L(m):
    t = "[PITFIX] " + str(m)
    try:
        unreal.log(t)
    except Exception:
        pass
    try:
        print(t)
    except Exception:
        pass


# ---------------------------------------------------------------- load the map (a commandlet starts with no world)
try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    L("map load requested")
except Exception as exc:
    L("load_map failed: %r" % exc)
time.sleep(4.0)

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = {}
for a in sub.get_all_level_actors():
    try:
        actors[a.get_actor_label()] = a
    except Exception:
        pass
L("actors in map: %d" % len(actors))
if not actors:
    raise RuntimeError("[PITFIX] no actors in the map - load failed, aborting without touching the map")


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


def spawn(label, loc, scale, rot=(0.0, 0.0, 0.0), mesh_path=None):
    old = actors.get(label)
    if old is not None:
        destroy(old)
        actors.pop(label, None)
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path or CUBE)
    if not mesh:
        raise RuntimeError("[PITFIX] missing mesh " + str(mesh_path))
    a = sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc),
                                   unreal.Rotator(roll=rot[0], pitch=rot[1], yaw=rot[2]))
    if a is None:
        raise RuntimeError("[PITFIX] spawn returned NULL for " + label)
    a.static_mesh_component.set_static_mesh(mesh)
    set_scale(a, scale)
    a.set_actor_label(label)
    actors[label] = a
    return a


def set_loc(a, loc):
    """UE 5.8 python: set_actor_location(location, sweep, teleport) - try every arity."""
    v = unreal.Vector(*loc)
    last = None
    for args in ((v, False, False), (v, False), (v,)):
        try:
            a.set_actor_location(*args)
            return True
        except TypeError as exc:
            last = exc
    try:
        t = a.get_actor_transform()
        t.set_location(v)
        a.set_actor_transform(t, False)
        return True
    except Exception as exc:
        L("set_loc FAILED for %s: %r / %r" % (a.get_actor_label(), last, exc))
        return False


def set_scale(a, sc):
    v = unreal.Vector(*sc)
    last = None
    for args in ((v,), (v, False)):
        try:
            a.set_actor_scale3d(*args)
            return True
        except TypeError as exc:
            last = exc
    try:
        t = a.get_actor_transform()
        t.set_scale3d(v)
        a.set_actor_transform(t, False)
        return True
    except Exception as exc:
        L("set_scale FAILED: %r / %r" % (last, exc))
        return False


def move(label, loc=None, scale=None):
    a = actors.get(label)
    if a is None:
        L("MISSING for move: " + label)
        return None
    if loc is not None:
        set_loc(a, loc)
    if scale is not None:
        set_scale(a, scale)
    return a


def aabb(label):
    """world-space footprint of a cube actor: (x0,x1,y0,y1)"""
    a = actors.get(label)
    if a is None:
        return None
    p = a.get_actor_location()
    s = a.get_actor_scale3d()
    hx, hy = abs(s.x) * 50.0, abs(s.y) * 50.0
    return (p.x - hx, p.x + hx, p.y - hy, p.y + hy)


def comp_mesh(comp):
    """UE 5.8 component mesh accessor: the property is 'static_mesh', not a get_static_mesh() method."""
    for fn in (lambda: comp.static_mesh,
               lambda: comp.get_editor_property('static_mesh'),
               lambda: comp.get_static_mesh()):
        try:
            m = fn()
            if m:
                return m
        except Exception:
            continue
    return None


# ---------------------------------------------------------------- the arena floor surface
floor = actors.get("BO_Floor")
floor_is_segment = False
if floor is None:
    # the floor has already been split into segments - any segment carries the same mesh,
    # the same surface z and the same FLOOR_SZ, so the script is safe to re-run
    for cand in ("BO_Floor_N", "BO_Floor_S", "BO_Floor_E", "BO_Floor_W"):
        if cand in actors:
            floor = actors[cand]
            floor_is_segment = True
            L("BO_Floor absent (already split) - deriving the floor surface from %s" % cand)
            break
if floor is None:
    raise RuntimeError("[PITFIX] no floor actor found - refusing to guess the floor")
mesh = comp_mesh(floor.static_mesh_component)
mesh_name = mesh.get_name() if mesh else "?"
floc = floor.get_actor_location()
fsc = floor.get_actor_scale3d()
is_plane = "Plane" in str(mesh_name)
if mesh is None:
    L("WARNING: could not read the floor mesh - assuming PLANE")
    is_plane = True
S = floc.z if is_plane else floc.z + fsc.z * 50.0
FLOOR_MESH = PLANE if is_plane else CUBE
FLOOR_SZ = fsc.z
L("floor mesh=%s loc=(%.0f,%.0f,%.0f) scale=(%.2f,%.2f,%.2f) -> surface S=%.0f"
  % (mesh_name, floc.x, floc.y, floc.z, fsc.x, fsc.y, fsc.z, S))

# ---------------------------------------------------------------- 1. cut the floor around the hole
HX0, HX1 = -1525.0, -875.0
HY0, HY1 = -1525.0, -1075.0
AX0, AX1, AY0, AY1 = -2000.0, 2000.0, -2000.0, 2000.0


def seg(label, x0, x1, y0, y1):
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    spawn(label, (cx, cy, floc.z), ((x1 - x0) / 100.0, (y1 - y0) / 100.0, FLOOR_SZ), mesh_path=FLOOR_MESH)
    L("%s x[%s..%s] y[%s..%s]" % (label, x0, x1, y0, y1))


if not floor_is_segment:
    destroy(floor)
    actors.pop("BO_Floor", None)
    L("removed the unbroken floor")
else:
    L("floor already split - rebuilding the four segments in place")
seg("BO_Floor_N", AX0, AX1, HY1, AY1)
seg("BO_Floor_S", AX0, AX1, AY0, HY0)
seg("BO_Floor_E", HX1, AX1, HY0, HY1)
seg("BO_Floor_W", AX0, HX0, HY0, HY1)

# ---------------------------------------------------------------- 2. the pit, 100u below the surface
PZ = S - 100.0
move("BO_PitFloor", loc=(-1200.0, -1200.0, PZ - 25.0), scale=(10.0, 10.0, 0.5))
L("pit floor surface z=%.0f (100u below the arena floor at %.0f)" % (PZ, S))

move("BO_PitRim_W", loc=(-1500.0, -1300.0, S), scale=(0.5, 4.5, 2.0))
move("BO_PitRim_S", loc=(-1200.0, -1500.0, S), scale=(5.5, 0.5, 2.0))
move("BO_PitRim_N", loc=(-1200.0, -1100.0, S), scale=(5.5, 0.5, 2.0))
spawn("BO_PitRim_E1", (-900.0, -1462.5, S), (0.5, 1.25, 2.0))
spawn("BO_PitRim_E2", (-900.0, -1137.5, S), (0.5, 1.25, 2.0))
old_e = actors.get("BO_PitRim_E")
if old_e is not None:
    destroy(old_e)
    actors.pop("BO_PitRim_E", None)
L("pit walls rebuilt - 200u tall (100u proud), 2m entrance gap in the east wall y[-1400,-1200]")

for lbl in ("PU_KeyRed_Pit", "PU_Health_Pit", "ENC_Brute_Pit"):
    a = actors.get(lbl)
    if a is None:
        L("pit content missing: " + lbl)
        continue
    loc = a.get_actor_location()
    set_loc(a, (loc.x, loc.y, PZ))
    L("%s moved onto the pit floor z=%.0f" % (lbl, PZ))

# ---------------------------------------------------------------- 3. the ramp to the NE platform
plat = actors.get("BO_Platform_NE")
ramp_ok = False
if plat is None:
    L("*** BO_Platform_NE missing - ramp untouched ***")
else:
    p = plat.get_actor_location()
    s = plat.get_actor_scale3d()
    top = p.z + abs(s.z) * 50.0            # cube: half-height is scale*50
    half_y = abs(s.y) * 50.0               # half-extent in Y (scale*100 is the full size)
    run = 1500.0
    length = math.hypot(run, top - S)
    angle = math.degrees(math.atan2(top - S, run))
    mid_y = (p.y - half_y) - run / 2.0
    mid_z = S + (top - S) / 2.0
    width = 400.0
    # clear of BO_Cover_06 at (1400,0) which spans x[1350..1450]
    ramp_x = p.x - 80.0
    L("platform top=%.0f south edge y=%.0f | ramp mid=(%.0f,%.0f,%.0f) length=%.0f pitch=%.1f deg"
      % (top, p.y - half_y, ramp_x, mid_y, mid_z, length, angle))
    for sign in (-1.0, 1.0):
        a = spawn("BO_Ramp_NE", (ramp_x, mid_y, mid_z), (width / 100.0, length / 100.0, 0.5),
                  rot=(sign * angle, 0.0, 0.0))
        c = a.get_actor_location()
        right = a.get_actor_right_vector()          # world direction of the local +Y (long) axis
        half_len = abs(a.get_actor_scale3d().y) * 50.0
        hi = unreal.Vector(c.x + right.x * half_len, c.y + right.y * half_len, c.z + right.z * half_len)
        lo = unreal.Vector(c.x - right.x * half_len, c.y - right.y * half_len, c.z - right.z * half_len)
        ok = (abs(hi.z - top) < 150.0) and (abs(lo.z - S) < 150.0)
        L("ramp roll=%+0.1f  high end z=%.0f (want %.0f)  low end z=%.0f (want %.0f)  ok=%s"
          % (sign * angle, hi.z, top, lo.z, S, ok))
        if ok:
            ramp_ok = True
            L("BO_Ramp_NE OK - length=%.0f pitch=%.1f deg  high=%.0f low=%.0f" % (length, angle, hi.z, lo.z))
            break
    if not ramp_ok:
        L("*** ramp tilt could not be verified ***")

    # clearance: the ramp must not run through a cover or the pillar
    rx0, rx1 = ramp_x - width / 2.0, ramp_x + width / 2.0
    ry0, ry1 = mid_y - length / 2.0, mid_y + length / 2.0
    for lbl in list(actors.keys()):
        if not (lbl.startswith("BO_Cover") or lbl.startswith("BO_Pillar") or lbl.startswith("BO_Wall")):
            continue
        b = aabb(lbl)
        if b is None:
            continue
        if b[0] < rx1 and rx0 < b[1] and b[2] < ry1 and ry0 < b[3]:
            L("!!! ramp footprint x[%.0f..%.0f] y[%.0f..%.0f] OVERLAPS %s x[%.0f..%.0f] y[%.0f..%.0f]"
              % (rx0, rx1, ry0, ry1, lbl, b[0], b[1], b[2], b[3]))
L("ramp_ok=%s  actor count now: %d" % (ramp_ok, len(list(sub.get_all_level_actors()))))

# ---------------------------------------------------------------- 3b. a way OUT of the pit
# The pit is a 1m drop-in. A drop with no way out is a trap, so cut a ramp down through the
# east rim gap - measured from the live rim pieces, never assumed.
pit_ramp_ok = False
e1 = actors.get("BO_PitRim_E1")
e2 = actors.get("BO_PitRim_E2")
if e1 is None or e2 is None:
    L("*** east rim pieces missing - no pit ramp built ***")
else:
    p1 = e1.get_actor_location(); s1 = e1.get_actor_scale3d()
    p2 = e2.get_actor_location(); s2 = e2.get_actor_scale3d()
    gap_y0 = p1.y + abs(s1.y) * 50.0      # north edge of the lower rim piece
    gap_y1 = p2.y - abs(s2.y) * 50.0      # south edge of the upper rim piece
    gap_w = gap_y1 - gap_y0
    gap_cy = (gap_y0 + gap_y1) / 2.0
    if gap_w <= 50.0:
        L("*** east rim gap is not usable (y0=%.0f y1=%.0f width=%.0f) ***" % (gap_y0, gap_y1, gap_w))
    else:
        run = 180.0
        drop = S - PZ
        length = math.hypot(run, drop)
        angle = math.degrees(math.atan2(drop, run))
        rx = HX1 - run / 2.0
        rz = (S + PZ) / 2.0
        L("pit gap y[%.0f..%.0f] width=%.0f | ramp mid=(%.0f,%.0f,%.0f) length=%.0f pitch=%.1f deg"
          % (gap_y0, gap_y1, gap_w, rx, gap_cy, rz, length, angle))
        for yaw in (90.0, -90.0):
            for sgn in (-1.0, 1.0):
                a = spawn("BO_Ramp_Pit", (rx, gap_cy, rz), (gap_w / 100.0, length / 100.0, 0.5),
                          rot=(sgn * angle, 0.0, yaw))
                c = a.get_actor_location()
                right = a.get_actor_right_vector()
                half_len = abs(a.get_actor_scale3d().y) * 50.0
                hi = unreal.Vector(c.x + right.x * half_len, c.y + right.y * half_len, c.z + right.z * half_len)
                lo = unreal.Vector(c.x - right.x * half_len, c.y - right.y * half_len, c.z - right.z * half_len)
                # the deep end must sit on the pit floor, the shallow end flush with the arena floor
                ok = (abs(hi.z - PZ) < 60.0) and (abs(lo.z - S) < 60.0) and (abs(hi.x - (HX1 - run)) < 150.0)
                L("pit ramp yaw=%.0f roll=%+0.1f  deep end z=%.0f (want %.0f) x=%.0f  floor end z=%.0f (want %.0f) x=%.0f  ok=%s"
                  % (yaw, sgn * angle, hi.z, PZ, hi.x, lo.z, S, lo.x, ok))
                if ok:
                    pit_ramp_ok = True
                    L("BO_Ramp_Pit OK - the pit is no longer a trap")
                    break
            if pit_ramp_ok:
                break
        if not pit_ramp_ok:
            L("*** pit ramp tilt could not be verified ***")
        # clearance against cover / walls / pillars
        qx0, qx1 = HX1 - run, HX1
        qy0, qy1 = gap_y0, gap_y1
        for lbl in list(actors.keys()):
            if not (lbl.startswith("BO_Cover") or lbl.startswith("BO_Pillar") or lbl.startswith("BO_Wall")
                    or lbl.startswith("BO_PitRim")):
                continue
            b = aabb(lbl)
            if b is None:
                continue
            if b[0] < qx1 and qx0 < b[1] and b[2] < qy1 and qy0 < b[3]:
                L("!!! pit ramp footprint x[%.0f..%.0f] y[%.0f..%.0f] OVERLAPS %s x[%.0f..%.0f] y[%.0f..%.0f]"
                  % (qx0, qx1, qy0, qy1, lbl, b[0], b[1], b[2], b[3]))

# ---------------------------------------------------------------- 4. save, then PROVE it on disk
_map_file = os.path.join(REPO, "Content", "Maps", "M_Blockout01.umap")
_before = os.path.getsize(_map_file) if os.path.exists(_map_file) else -1
for fn, desc in ((lambda: unreal.EditorLoadingAndSavingUtils.save_map(MAP), "save_map"),
                 (lambda: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True), "save_dirty_packages"),
                 (lambda: unreal.EditorAssetLibrary.save_asset(MAP, only_if_is_dirty=False), "save_asset")):
    try:
        fn()
        L("save OK via " + desc)
        break
    except Exception as exc:
        L("save via %s failed: %r" % (desc, exc))
time.sleep(3.0)
_after = os.path.getsize(_map_file) if os.path.exists(_map_file) else -1
L("on-disk umap before=%d after=%d changed=%s" % (_before, _after, _after != _before))
if _after <= 0 or _after == _before:
    L("*** THE SAVE DID NOT PERSIST - the file on disk is unchanged ***")
else:
    L("SAVE_PERSISTED bytes=%d" % _after)

# ---------------------------------------------------------------- 5. refresh the transform dump from THIS state
try:
    runpy.run_path(DUMP, run_name="__main__")
    L("transform dump refreshed")
except Exception as exc:
    L("dump failed: %r" % exc)
L("done")
