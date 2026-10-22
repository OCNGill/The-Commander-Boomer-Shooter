"""UE 5.8 - re-bind shipping X-COM enemy materials, then render parity shots.

PHASE A (re-bind)
  The five shipping meshes at /Game/Enemies/XCOM have WorldGridMaterial on
  every slot.  The correct per-slot materials are bound on the verification
  copies at /Game/Tests/UEParity, which is the AUTHORITY for slot -> material.

  Those per-enemy material assets live ONLY in the throwaway folder, which is
  deleted at cleanup - so they are RELOCATED (renamed, never re-authored) into
  /Game/Enemies/XCOM first, then bound by slot NAME, then the shipping meshes
  are saved and re-measured from disk.  No new material asset is created.

PHASE B (shots)
  Each shipping mesh is rendered in-engine into
  CommandCenter/outputs/ue_verify/shots/XCOM_<Enemy>_ue.png (>=900 px tall):
  neutral grey background (render-target clear colour, no sky), flat floor,
  key + fill + rim lights, 3/4 front view framed from the actor bounds.

Notes on the engine behaviour that this script relies on:
  * USceneCaptureComponent2D::CaptureScene() renders synchronously.
    CaptureSceneDeferred() only queues for end-of-frame, which never happens
    in a commandlet - so capture_scene() is the only usable path here.
  * Nothing in Content/Maps is opened, modified or saved.

Writes, incrementally as each step completes:
  CommandCenter/outputs/ue_verify/ue_rebind_report.json
  CommandCenter/outputs/ue_verify/ue_shots_report.json
  CommandCenter/outputs/ue_verify/shots/XCOM_<Enemy>_ue.png
"""

import json
import math
import os

import unreal

REPO = r'C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter'
SHIPPING = '/Game/Enemies/XCOM'
THROW = '/Game/Tests/UEParity'
OUT = REPO + '/CommandCenter/outputs/ue_verify'
SHOT_DIR = OUT + '/shots'

ENEMIES = ['XCOM_Sectoid', 'XCOM_Viper', 'XCOM_Floater', 'XCOM_Muton',
           'XCOM_Chryssalid']

W, H = 960, 1200          # >= 900 px tall, 4:5 like the approved hero plates
FOV = 40.0
MARGIN = 1.28             # framing slack
AZ = 40.0                # 3/4 front: azimuth off the model's +X front
EL = 12.0                # slight elevation


def L(msg):
    unreal.log('[UEP] ' + str(msg))


def sset(obj, name, value):
    """set_editor_property with a getattr/setattr fallback."""
    try:
        obj.set_editor_property(name, value)
        return True
    except Exception:
        try:
            setattr(obj, name, value)
            return True
        except Exception as e:
            L('sset %s failed: %r' % (name, e))
            return False


def rlib():
    for n in ('KismetRenderingLibrary', 'RenderingLibrary'):
        c = getattr(unreal, n, None)
        if c is not None:
            return c
    return None


def rl_call(fn_names, *args):
    """Call the first available rendering-library function by name."""
    rl = rlib()
    if rl is None:
        return None
    for fn in fn_names:
        f = getattr(rl, fn, None)
        if f is None:
            continue
        try:
            return f(*args)
        except Exception as e:
            L('rl_call %s failed: %r' % (fn, e))
            return None
    return None


def write_json(path, obj):
    try:
        d = os.path.dirname(path)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        with open(path, 'w') as f:
            json.dump(obj, f, indent=2, sort_keys=True, default=str)
        L('wrote ' + path)
        return True
    except Exception as e:
        L('write_json failed %r' % (e,))
        return False


def obj_path(base, name):
    return '%s/%s.%s' % (base, name, name)


def load(base, name):
    return unreal.EditorAssetLibrary.load_asset(obj_path(base, name))


# ------------------------------------------------------------------ phase A

def slots_of(mesh):
    out = []
    try:
        arr = mesh.get_editor_property('static_materials')
    except Exception:
        return out
    for s in arr:
        try:
            name = str(s.get_editor_property('material_slot_name'))
        except Exception:
            name = '<no-name>'
        try:
            mi = s.get_editor_property('material_interface')
        except Exception:
            mi = None
        out.append((name, mi))
    return out


def relocate_material(src_path, dst_path):
    """Move a material asset into the shipping folder. rename first."""
    if unreal.EditorAssetLibrary.does_asset_exist(dst_path):
        return 'already_present'
    if not unreal.EditorAssetLibrary.does_asset_exist(src_path):
        return 'missing_source'
    try:
        if unreal.EditorAssetLibrary.rename_asset(src_path, dst_path):
            try:
                if unreal.EditorAssetLibrary.does_asset_exist(src_path):
                    unreal.EditorAssetLibrary.delete_asset(src_path)
            except Exception:
                pass
            return 'renamed'
    except Exception as e:
        L('rename failed %r' % (e,))
    try:
        if unreal.EditorAssetLibrary.duplicate_asset(src_path, dst_path):
            return 'duplicated'
    except Exception as e:
        L('duplicate failed %r' % (e,))
    return 'failed'


def phase_a():
    report = {'shipping': SHIPPING, 'authority': THROW, 'enemies': {}}
    for name in ENEMIES:
        rec = {'enemy': name, 'ok': False}
        try:
            ver = load(THROW, name)
            ship = load(SHIPPING, name)
            if ver is None:
                rec['error'] = 'no verification copy ' + obj_path(THROW, name)
            elif ship is None:
                rec['error'] = 'no shipping mesh ' + obj_path(SHIPPING, name)
            else:
                rec['before'] = [(s, (m.get_name() if m else None))
                                 for s, m in slots_of(ship)]
                vslots = slots_of(ver)
                rec['authority_map'] = dict((s, m.get_name())
                                            for s, m in vslots if m is not None)

                # relocate the per-enemy materials into the shipping folder
                moves = {}
                for slot, mat_name in rec['authority_map'].items():
                    moves[slot] = {
                        'material': mat_name,
                        'src': obj_path(THROW, mat_name),
                        'dst': obj_path(SHIPPING, mat_name),
                        'result': relocate_material(obj_path(THROW, mat_name),
                                                   obj_path(SHIPPING, mat_name)),
                    }
                rec['material_moves'] = moves

                # bind by slot name
                new_slots = []
                bind = []
                for s, _m in slots_of(ship):
                    mat_name = rec['authority_map'].get(s)
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
                    bind.append({'slot': s,
                                 'assigned': mat.get_name() if mat else None})
                rec['bind'] = bind
                ship.set_editor_property('static_materials', new_slots)
                try:
                    ship.modify()
                except Exception:
                    pass
                rec['saved'] = bool(unreal.EditorAssetLibrary.save_asset(
                    obj_path(SHIPPING, name)))

                # re-measure from disk
                check = unreal.EditorAssetLibrary.load_asset(
                    obj_path(SHIPPING, name))
                after = [(s, (m.get_name() if m else None))
                         for s, m in slots_of(check)]
                rec['after'] = after
                rec['matches_authority'] = all(
                    rec['authority_map'].get(s) == m for s, m in after)
                rec['ok'] = bool(rec['saved'] and rec['matches_authority']
                                 and all(m for _s, m in after))
                L('%s after=%s ok=%s' % (name, after, rec['ok']))
        except Exception as e:
            rec['error'] = repr(e)
            try:
                import traceback
                rec['traceback'] = traceback.format_exc()[-1500:]
            except Exception:
                pass
            L('%s ERROR %r' % (name, e))
        report['enemies'][name] = rec
        write_json(os.path.join(OUT, 'ue_rebind_report.json'), report)
    return report


# ------------------------------------------------------------------ phase B

def ensure_world():
    """Current editor world, else a throwaway level in the throwaway folder."""
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = ues.get_editor_world()
    if world is not None:
        try:
            L('editor world: %s' % world.get_name())
        except Exception:
            pass
        return world, 'existing'
    try:
        lvl = unreal.EditorLevelLibrary.new_level(
            '/Game/Tests/UEParity/UEP_ShotLevel')
        L('new_level -> %r' % (lvl,))
        world = ues.get_editor_world()
        return world, 'new_level'
    except Exception as e:
        L('new_level failed: %r' % (e,))
        return None, 'failed'


def spawn_mesh(subs, mesh, loc):
    a = subs.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc),
                                    unreal.Rotator(0, 0, 0))
    if a is None:
        return None
    smc = a.static_mesh_component
    smc.set_static_mesh(mesh)
    return a


def bounds_of(actor):
    try:
        o, e = actor.get_actor_bounds(False)
        return unreal.Vector(o), unreal.Vector(e)
    except Exception:
        return unreal.Vector(0, 0, 0), unreal.Vector(50, 50, 50)


def make_light(subs, name, loc, rot, intensity, cls, color, shadows):
    a = subs.spawn_actor_from_class(cls, unreal.Vector(*loc),
                                    unreal.Rotator(*rot))
    if a is None:
        return None
    a.set_actor_label('UEP_' + name)
    comp = None
    for c in (unreal.DirectionalLightComponent, unreal.PointLightComponent,
              unreal.SpotLightComponent):
        try:
            comp = actor_comp = a.get_component_by_class(c)
        except Exception:
            comp = None
        if comp is not None:
            break
    if comp is not None:
        sset(comp, 'intensity', intensity)
        sset(comp, 'cast_shadows', shadows)
        if color:
            sset(comp, 'light_color', unreal.Color(*color))
        try:
            sset(comp, 'source_radius', 25.0)   # soft shadow penumbra
        except Exception:
            pass
    return a


def floor_material():
    for p in ('/Engine/BasicShapes/BasicShapeMaterial',
              '/Engine/EngineMaterials/DefaultMaterial',
              '/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial'):
        m = unreal.EditorAssetLibrary.load_asset(p)
        if m is not None:
            return m
    return None


def phase_b():
    report = {'shots': [], 'notes': []}
    world, how = ensure_world()
    if world is None:
        report['notes'].append('no world available')
        write_json(os.path.join(OUT, 'ue_shots_report.json'), report)
        return report
    report['world'] = how
    subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not os.path.isdir(SHOT_DIR):
        os.makedirs(SHOT_DIR)

    # --- static stage: floor ------------------------------------------------
    floor = None
    plane = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Plane')
    if plane is not None:
        floor = spawn_mesh(subs, plane, (0, 0, 0))
        if floor is not None:
            floor.set_actor_label('UEP_FLOOR')
            smc = floor.static_mesh_component
            smc.set_world_scale3d(unreal.Vector(40.0, 40.0, 40.0))
            fmat = floor_material()
            if fmat is not None:
                smc.set_material(0, fmat)
            else:
                report['notes'].append('no floor material found')

    for name in ENEMIES:
        shot = {'enemy': name, 'png': 'XCOM_%s_ue.png' % name, 'ok': False}
        try:
            mesh = load(SHIPPING, name)
            if mesh is None:
                shot['note'] = 'mesh not found'
            else:
                # sit the model on the floor
                actor = spawn_mesh(subs, mesh, (0, 0, 0))
                if actor is None:
                    shot['note'] = 'spawn failed'
                else:
                    actor.set_actor_label('UEP_MESH_' + name)
                    origin, extent = bounds_of(actor)
                    # drop so the lowest point sits on z=0
                    actor.set_actor_location(
                        unreal.Vector(0.0, 0.0, -(origin.z - extent.z)))
                    origin, extent = bounds_of(actor)
                    target = unreal.Vector(0.0, 0.0, origin.z)

                    # --- framing: fit the actor in the frame -----------------
                    vfov = math.radians(FOV)
                    aspect = float(W) / float(H)
                    hfov = math.atan(math.tan(vfov / 2.0) * aspect)
                    half_w = max(extent.x, extent.y)
                    dist = max((extent.z * MARGIN) / math.tan(vfov / 2.0),
                               (half_w * MARGIN) / math.tan(hfov / 2.0))
                    dist = max(dist, 120.0)
                    az = math.radians(AZ)
                    el = math.radians(EL)
                    dirv = unreal.Vector(math.cos(el) * math.cos(az),
                                        -math.cos(el) * math.sin(az),
                                        math.sin(el))
                    cam_loc = unreal.Vector(target.x + dirv.x * dist,
                                            target.y + dirv.y * dist,
                                            target.z + dirv.z * dist)
                    look = unreal.Vector(target.x - cam_loc.x,
                                         target.y - cam_loc.y,
                                         target.z - cam_loc.z)
                    yaw = math.degrees(math.atan2(look.y, look.x))
                    pitch = math.degrees(math.atan2(
                        look.z, math.hypot(look.x, look.y)))
                    shot['camera'] = {'loc': [cam_loc.x, cam_loc.y, cam_loc.z],
                                      'rot': [pitch, yaw, 0.0],
                                      'distance': dist,
                                      'target': [target.x, target.y, target.z],
                                      'bounds_origin': [origin.x, origin.y,
                                                        origin.z],
                                      'bounds_extent': [extent.x, extent.y,
                                                        extent.z]}

                    # --- lights: key + fill + rim --------------------------
                    key = make_light(subs, 'KEY', (-1.6, -2.0, 2.4),
                                     (-42, -38, 0), 6.0, unreal.DirectionalLight,
                                     (1.0, 0.97, 0.92), True)
                    fill = make_light(subs, 'FILL', (2.2, -1.6, 1.0),
                                      (-20, 54, 0), 2.4, unreal.PointLight,
                                      (0.72, 0.80, 1.0), False)
                    rim = make_light(subs, 'RIM', (0.8, 2.2, 1.6),
                                     (-28, 180, 0), 3.6, unreal.DirectionalLight,
                                     (0.85, 0.92, 1.0), False)

                    # --- scene capture ------------------------------------
                    rt = rl_call(('create_render_target_2d',
                                  'create_render_target2d'),
                                 world, W, H,
                                 unreal.TextureRenderTargetFormat.RTF_RGBA8,
                                 unreal.LinearColor(0.30, 0.31, 0.33, 1.0))
                    if rt is None:
                        shot['note'] = 'render target creation failed'
                    else:
                        cap_actor = subs.spawn_actor_from_class(
                            unreal.SceneCapture2D, cam_loc,
                            unreal.Rotator(pitch, yaw, 0.0))
                        if cap_actor is None:
                            shot['note'] = 'SceneCapture2D spawn failed'
                        else:
                            cap_actor.set_actor_label('UEP_CAP_' + name)
                            cap = None
                            for getter in ('get_component_by_class',):
                                try:
                                    cap = getattr(cap_actor, getter)(
                                        unreal.SceneCaptureComponent2D)
                                except Exception:
                                    cap = None
                            if cap is None:
                                try:
                                    cap = cap_actor.capture_component2d
                                except Exception:
                                    cap = None
                            if cap is None:
                                shot['note'] = 'no capture component'
                            else:
                                sset(cap, 'texture_target', rt)
                                try:
                                    sset(cap, 'capture_source',
                                         unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
                                except Exception:
                                    pass
                                sset(cap, 'fov_angle', FOV)
                                sset(cap, 'b_capture_every_frame', False)
                                try:
                                    cap.capture_scene()
                                    shot['captured'] = True
                                except Exception as e:
                                    shot['note'] = 'capture_scene failed %r' % (e,)

                                out = os.path.join(SHOT_DIR, shot['png'])
                                rl_call(('export_render_target',),
                                         world, rt, SHOT_DIR, shot['png'])
                                shot['png_path'] = out
                                shot['png_written'] = os.path.isfile(out)
                                shot['png_bytes'] = (os.path.getsize(out)
                                                     if shot['png_written'] else 0)
                                shot['ok'] = bool(shot['png_written']
                                                 and shot['png_bytes'] > 2000)
                                if not shot['ok']:
                                    shot['note'] = 'png missing or trivial'
                                subs.destroy_actor(cap_actor)
                    for a in (key, fill, rim):
                        try:
                            if a is not None:
                                subs.destroy_actor(a)
                        except Exception:
                            pass
                    subs.destroy_actor(actor)
        except Exception as e:
            shot['note'] = 'exception %r' % (e,)
            try:
                import traceback
                shot['traceback'] = traceback.format_exc()[-1500:]
            except Exception:
                pass
        report['shots'].append(shot)
        L('SHOT %s ok=%s bytes=%s note=%s'
          % (name, shot.get('ok'), shot.get('png_bytes'), shot.get('note')))
        write_json(os.path.join(OUT, 'ue_shots_report.json'), report)
    try:
        if floor is not None:
            subs.destroy_actor(floor)
    except Exception:
        pass
    return report


def main():
    L('START')
    write_json(os.path.join(OUT, 'ue_run_state.json'),
               {'phase': 'start', 'utc': __import__('datetime')
                .datetime.utcnow().isoformat() + 'Z'})
    reb = phase_a()
    write_json(os.path.join(OUT, 'ue_rebind_report.json'), reb)
    L('PHASE A done ok=%d' % sum(1 for v in reb['enemies'].values()
                                 if v.get('ok')))
    write_json(os.path.join(OUT, 'ue_run_state.json'),
               {'phase': 'phase_a_done', 'rebind_ok': sum(
                   1 for v in reb['enemies'].values() if v.get('ok'))})
    shots = phase_b()
    write_json(os.path.join(OUT, 'ue_shots_report.json'), shots)
    L('PHASE B done ok=%d' % sum(1 for s in shots['shots'] if s.get('ok')))
    write_json(os.path.join(OUT, 'ue_run_state.json'),
               {'phase': 'done', 'rebind_ok': sum(
                   1 for v in reb['enemies'].values() if v.get('ok')),
                'shots_ok': sum(1 for s in shots['shots'] if s.get('ok'))})
    L('END')


main()
