"""UE 5.8 - diagnostic: why do the in-engine parity shots show no creature?

The main shot script (ue_enemy_shots.py) reports ok=5/5, but the exported
PNGs show a smooth curved surface filling the frame with a blown-out white
lower half - no character.  This script isolates the cause by rendering the
SAME enemy four ways and logging the scene state:

  V1  as-shipped            : floor + key/fill/rim lights, studio at origin
  V2  no floor, no lights   : model against the clear colour only
  V3  studio far from level : floor + lights, studio moved off the level
  V4  camera much closer    : floor + lights, distance x 0.30

It also logs the level actor inventory, the model's world placement, and the
camera's world transform, so the failure is diagnosable from the log alone.
"""

import json
import math
import os
import time
import traceback

import unreal

REPO = os.environ.get('UE_REPO',
                       r'C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter')
OUT = REPO + '/CommandCenter/outputs/ue_verify/diag'
SHOTS = OUT + '/shots'
SHIPPING = '/Game/Enemies/XCOM'
MAP = '/Game/Tests/M_Proof_Blockout'
ENEMY = 'XCOM_Muton'

W, H = 480, 600
FOV = 35.0
FILL = 0.62
AZIMUTH = 30.0
ELEVATION = 14.0
BG = (0.19, 0.20, 0.22, 1.0)
FLOOR_MESH = '/Engine/BasicShapes/Cube.Cube'
FLOOR_MAT = '/Engine/BasicShapes/BasicShapeMaterial'
FAR = 50000.0          # studio offset for V3, far outside any level geometry


def L(m):
    unreal.log('[DIAG] ' + str(m))


def setp(obj, prop, value):
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False


def write_json(path, obj):
    try:
        d = os.path.dirname(path)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        with open(path, 'w') as f:
            json.dump(obj, f, indent=2, sort_keys=True, default=str)
    except Exception as e:
        L('write_json failed %r' % (e,))


def editor_world():
    try:
        w = unreal.get_editor_subsystem(
            unreal.UnrealEditorSubsystem).get_editor_world()
        if w is not None:
            return w
    except Exception as e:
        L('world failed %r' % (e,))
    try:
        return unreal.EditorLevelLibrary.get_editor_world()
    except Exception as e:
        L('world failed %r' % (e,))
    return None


def spawn(world, cls, loc=(0, 0, 0)):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    return sub.spawn_actor_from_class(cls, unreal.Vector(*loc),
                                      unreal.Rotator(0.0, 0.0, 0.0))


def comp_of(actor, *names):
    for n in names:
        try:
            c = actor.get_editor_property(n)
            if c is not None:
                return c
        except Exception:
            pass
    for cn in ('SpotLightComponent', 'PointLightComponent',
               'DirectionalLightComponent', 'SkyLightComponent'):
        cls = getattr(unreal, cn, None)
        if cls is None:
            continue
        try:
            for c in actor.get_components_by_class(cls):
                return c
        except Exception:
            pass
    return None


def aim(pos, target):
    d = (target[0] - pos[0], target[1] - pos[1], target[2] - pos[2])
    ln = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
    if ln < 1e-6:
        return unreal.Rotator(0.0, 0.0, 0.0)
    yaw = math.degrees(math.atan2(d[1], d[0]))
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, d[2] / ln))))
    return unreal.Rotator(0.0, pitch, yaw)


def set_rot(actor, rot, tag):
    try:
        actor.set_actor_rotation(rot, False)
    except Exception as exc:
        L('%s rot raised %r' % (tag, exc))
    got = None
    try:
        got = actor.get_actor_rotation()
    except Exception:
        pass
    ok = (got is not None
          and abs(((got.yaw - rot.yaw + 180.0) % 360.0) - 180.0) < 0.5
          and abs(got.pitch - rot.pitch) < 0.5)
    L('%s rot want yaw=%.2f pitch=%.2f got yaw=%.2f pitch=%.2f ok=%s'
      % (tag, rot.yaw, rot.pitch,
         got.yaw if got else -999, got.pitch if got else -999, ok))
    return ok


def place(actor, loc, tag):
    """Set the location and READ IT BACK.  UE 5.8 editor actors can accept a
    set_actor_location without applying it to the component transform, which
    is exactly how a creature ends up outside the camera's frustum."""
    try:
        actor.set_actor_location(unreal.Vector(*loc), False, True)
    except Exception as exc:
        L('%s loc raised %r' % (tag, exc))
    got = None
    try:
        got = actor.get_actor_location()
    except Exception:
        pass
    L('%s loc want (%s) got (%s)' % (tag, [round(v, 2) for v in loc],
                                     [round(got.x, 2), round(got.y, 2),
                                      round(got.z, 2)] if got else 'None'))
    return got


def inventory(world):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = sub.get_all_level_actors()
    kinds = {}
    for a in actors:
        try:
            k = a.get_class().get_name()
        except Exception:
            k = '?'
        kinds[k] = kinds.get(k, 0) + 1
    L('LEVEL INVENTORY %d actors: %s' % (len(actors), sorted(kinds.items())))
    return kinds


def build_studio(world, center, size, with_floor=True, with_lights=True,
                 origin=(0.0, 0.0, 0.0)):
    actors = []
    ox, oy, oz = origin
    if with_floor:
        floor_mesh = unreal.EditorAssetLibrary.load_asset(FLOOR_MESH)
        floor_mat = unreal.EditorAssetLibrary.load_asset(FLOOR_MAT)
        fa = spawn(world, unreal.StaticMeshActor)
        fcomp = fa.static_mesh_component
        fcomp.set_static_mesh(floor_mesh)
        if floor_mat is not None:
            fcomp.set_material(0, floor_mat)
        ext = max(8.0, size * 2.5)
        fa.set_actor_scale3d(unreal.Vector(ext, ext, 0.1))
        place(fa, (center.x + ox, center.y + oy, -0.05 + oz), 'FLOOR')
        actors.append(fa)

    if with_lights:
        key_pos = (center.x - size * 0.8 + ox, center.y + size * 1.0 + oy,
                   center.z + size * 1.5 + oz)
        ka = spawn(world, unreal.SpotLight)
        kc = comp_of(ka, 'spot_light_component')
        if kc is not None:
            setp(kc, 'intensity', 12000.0)
            setp(kc, 'light_color', unreal.LinearColor(1.0, 0.95, 0.87))
            setp(kc, 'cast_shadows', True)
            setp(kc, 'source_radius', 12.0)
            setp(kc, 'inner_cone_angle', 35.0)
            setp(kc, 'outer_cone_angle', 65.0)
        place(ka, key_pos, 'KEY')
        set_rot(ka, aim(key_pos, (center.x + ox, center.y + oy, center.z + oz)),
                'KEY')
        actors.append(ka)

        fill_pos = (center.x + size * 1.3 + ox, center.y - size * 1.1 + oy,
                    center.z + size * 0.4 + oz)
        fla = spawn(world, unreal.PointLight)
        fc = comp_of(fla, 'point_light_component')
        if fc is not None:
            setp(fc, 'intensity', 1500.0)
            setp(fc, 'light_color', unreal.LinearColor(0.60, 0.72, 0.92))
            setp(fc, 'cast_shadows', False)
            setp(fc, 'source_radius', 30.0)
        place(fla, fill_pos, 'FILL')
        actors.append(fla)

        rim_pos = (center.x - size * 1.5 + ox, center.y - size * 1.7 + oy,
                   center.z + size * 1.4 + oz)
        ra = spawn(world, unreal.DirectionalLight)
        rc = comp_of(ra, 'directional_light_component')
        if rc is not None:
            setp(rc, 'intensity', 3.0)
            setp(rc, 'light_color', unreal.LinearColor(0.72, 0.86, 1.0))
            setp(rc, 'cast_shadows', False)
        place(ra, rim_pos, 'RIM')
        set_rot(ra, aim(rim_pos, (center.x + ox, center.y + oy, center.z + oz)),
                'RIM')
        actors.append(ra)
    return actors


def place_camera(world, center, size, dist_scale=1.0, origin=(0.0, 0.0, 0.0)):
    ox, oy, oz = origin
    half_h = size * 0.5
    dist = half_h / (math.tan(math.radians(FOV) * 0.5) * FILL) * dist_scale
    az = math.radians(AZIMUTH)
    el = math.radians(ELEVATION)
    pos = (center.x + ox + math.cos(az) * math.cos(el) * dist,
           center.y + oy + math.sin(az) * math.cos(el) * dist,
           center.z + oz + math.sin(el) * dist)
    target = (center.x + ox, center.y + oy, center.z + oz - size * 0.06)
    ca = spawn(world, unreal.SceneCapture2D)
    cc = ca.capture_component2d
    setp(cc, 'fov_angle', FOV)
    place(ca, pos, 'CAM')
    set_rot(ca, aim(pos, target), 'CAM')
    return ca, cc, pos, dist


def shoot(world, comp, tag):
    vrt = unreal.RenderingLibrary.create_render_target2d(
        world, W, H, unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(*BG))
    comp.set_editor_property('texture_target', vrt)
    setp(comp, 'primitive_render_mode', 1)
    comp.capture_scene()
    samples = unreal.RenderingLibrary.read_render_target(world, vrt)
    info = {'tag': tag, 'pixels': len(samples) if samples else 0}
    if samples:
        vals = [(c.r, c.g, c.b) for c in samples]
        info['unique'] = len(set(vals))
        info['min'] = min(min(v) for v in vals)
        info['max'] = max(max(v) for v in vals)
        corners = [vals[0], vals[W - 1], vals[-W], vals[-1]]
        info['corners'] = [list(c) for c in corners]
        mid = (H // 2) * W + W // 2
        info['centre'] = list(vals[mid])
        # luminance histogram: how much of the frame is blown out?
        lum = [(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) for c in vals]
        info['blown_frac'] = round(sum(1 for l in lum if l > 0.95) / len(lum), 4)
        info['dark_frac'] = round(sum(1 for l in lum if l < 0.05) / len(lum), 4)
    try:
        unreal.RenderingLibrary.export_render_target(world, vrt, SHOTS,
                                                      'diag_%s' % tag)
    except Exception as exc:
        L('export %s failed %r' % (tag, exc))
    L('%s %s' % (tag, json.dumps(info, default=str)))
    return info


def main():
    report = {}
    if not os.path.isdir(SHOTS):
        os.makedirs(SHOTS)
    report['map'] = MAP
    report['enemy'] = ENEMY
    report['variants'] = {}

    try:
        ok = bool(unreal.EditorLoadingAndSavingUtils.load_map(MAP))
        L('load_map -> %s' % ok)
    except Exception as exc:
        L('load_map raised %r' % (exc,))
    world = None
    wpath = ''
    for _ in range(20):
        world = editor_world()
        wpath = world.get_path_name() if world is not None else ''
        if world is not None and wpath and 'Untitled' not in wpath:
            break
        time.sleep(0.5)
    if world is None:
        L('NO WORLD')
        write_json(os.path.join(OUT, 'diag_report.json'), report)
        return
    L('world: %s' % wpath)
    report['world'] = wpath
    report['inventory_before'] = inventory(world)

    # clear the level the same way the shot script does
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    keep = ('WorldSettings', 'Brush', 'InfoBrush', 'Landscape')
    removed = []
    for a in sub.get_all_level_actors():
        try:
            cn = a.get_class().get_name()
            if cn in keep:
                continue
            sub.destroy_actor(a)
            removed.append(cn)
        except Exception:
            pass
    L('cleared %d actors: %s' % (len(removed), sorted(set(removed))))
    report['inventory_after'] = inventory(world)

    path = '%s/%s.%s' % (SHIPPING, ENEMY, ENEMY)
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    if mesh is None:
        L('MESH LOAD FAILED %s' % path)
        write_json(os.path.join(OUT, 'diag_report.json'), report)
        return
    L('mesh loaded: %s' % mesh.get_name())
    for s in mesh.get_editor_property('static_materials'):
        mi = s.get_editor_property('material_interface')
        L('  slot %s -> %s' % (s.get_editor_property('material_slot_name'),
                              mi.get_name() if mi else None))

    variants = [
        ('V1_as_shipped', dict(floor=True, lights=True, far=False, ds=1.0)),
        ('V2_no_floor_no_lights', dict(floor=False, lights=False, far=False, ds=1.0)),
        ('V3_far_from_level', dict(floor=True, lights=True, far=True, ds=1.0)),
        ('V4_close_camera', dict(floor=True, lights=True, far=False, ds=0.30)),
    ]

    for tag, cfg in variants:
        try:
            ma = spawn(world, unreal.StaticMeshActor)
            mc = ma.static_mesh_component
            mc.set_static_mesh(mesh)
            bounds = mesh.get_bounds()
            org = bounds.origin
            ext = bounds.box_extent
            want = (0.0, 0.0, -org.z + ext.z)
            got = place(ma, want, 'MODEL_' + tag)
            center = unreal.Vector(0.0, 0.0, ext.z)
            size = max(ext.x, ext.y, ext.z) * 2.0
            origin = (FAR, FAR, 0.0) if cfg['far'] else (0.0, 0.0, 0.0)
            build_studio(world, center, size, with_floor=cfg['floor'],
                         with_lights=cfg['lights'], origin=origin)
            cap, comp, campos, dist = place_camera(
                world, center, size, dist_scale=cfg['ds'], origin=origin)
            L('%s model_local_org=%s ext=%s size=%.1f cam=%s dist=%.1f'
              % (tag, [round(v, 2) for v in (org.x, org.y, org.z)],
                 [round(v, 2) for v in (ext.x, ext.y, ext.z)], size,
                 [round(v, 1) for v in campos], dist))
            report['variants'][tag] = shoot(world, comp, tag)
        except Exception as e:
            L('%s ERROR %r' % (tag, e))
            report['variants'][tag] = {'error': repr(e),
                                       'tb': traceback.format_exc()[-800:]}

    write_json(os.path.join(OUT, 'diag_report.json'), report)
    L('DIAG COMPLETE variants=%d' % len(report['variants']))
    try:
        unreal.SystemLibrary.quit_editor()
    except Exception as exc:
        L('quit failed %r' % (exc,))


main()
