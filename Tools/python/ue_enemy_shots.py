"""UE 5.8 - PHASE B: in-engine parity shots of the five shipping XCOM enemies.

Renders each /Game/Enemies/XCOM static mesh with a scene capture in a
controlled studio (neutral grey background, flat floor, key + fill + rim) and
writes CommandCenter/outputs/ue_verify/shots/XCOM_<Enemy>_ue.png.

WHY THIS FILE IS TICK-DRIVEN
----------------------------
A scene capture needs a real render pass to have happened before its render
target can be read.  Doing the whole shot list inline inside
-ExecutePythonScript does NOT work: the script runs during editor startup,
before the engine loop has ticked, so capture_scene() queues a render that
never happens and read_render_target() hands back the render target's
UNINITIALISED memory.

That garbage is deterministic, which is exactly how it fooled the earlier
runs: a scene WITH a floor and lights produced byte-identical capture
statistics to a scene with NEITHER, and the exported PNGs showed a smooth
curved gradient with a blown-out white lower half - never a creature.  The
run reported ok=5/5 because the garbage had plenty of unique colours.

So the work is driven from a slate post-tick callback: one state per tick,
and the render target is read on a LATER tick than the capture was issued.
Every stage is logged so a run is diagnosable from the log alone.

Content/Maps is never opened for writing: the proofing COPY of the arena map
(Content/Tests/M_Proof_Blockout.umap, byte-identical to M_Blockout01.umap)
is loaded read-only, and a byte-for-byte guard restores it if the editor
ever autosaves it.
"""

import json
import math
import os
import traceback

import unreal

REPO = os.environ.get('UE_REPO',
                       r'C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter')
OUT = REPO + '/CommandCenter/outputs/ue_verify'
SHOTS = OUT + '/shots'
SHIPPING = '/Game/Enemies/XCOM'
# The proofing COPY of the frozen arena map.  Content/Tests/M_Proof_Blockout.umap
# is byte-identical to Content/Maps/M_Blockout01.umap, so the frozen map is
# never opened.  This map is loaded read-only: it is never saved.
MAP = '/Game/Tests/M_Proof_Blockout'
ENEMIES = ['XCOM_Sectoid', 'XCOM_Viper', 'XCOM_Floater', 'XCOM_Muton',
           'XCOM_Chryssalid']

WIDTH = 1080
HEIGHT = 1350
FOV = 35.0
FILL = 0.62          # fraction of frame height the creature should occupy
AZIMUTH = 30.0       # degrees off the model's +X (front) axis
ELEVATION = 14.0     # degrees above the model's centre
BG = (0.19, 0.20, 0.22, 1.0)   # neutral grey background (linear)

VAL_W, VAL_H = 160, 200

FLOOR_MESH = '/Engine/BasicShapes/Cube.Cube'
FLOOR_MAT = '/Engine/BasicShapes/BasicShapeMaterial'

# A capture must be READ on a later tick than it was issued, otherwise the
# render target still holds uninitialised memory.
TICKS_BEFORE_READ = 3
TICKS_BEFORE_EXPORT = 2


def L(m):
    unreal.log('[SHOT] ' + str(m))


def setp(obj, prop, value):
    """Set an editor property; tolerate a missing/renamed property."""
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
        L('UnrealEditorSubsystem world failed %r' % (e,))
    try:
        return unreal.EditorLevelLibrary.get_editor_world()
    except Exception as e:
        L('EditorLevelLibrary world failed %r' % (e,))
    return None


def set_rot(actor, rot, tag):
    """Set an actor's rotation AND PROVE it took.

    In UE 5.8 an editor actor's transform is applied on the next tick, and a
    Python-side set_actor_rotation can silently not stick -- the scene
    capture then renders from the default +X orientation, which looks like a
    plausible render of the wrong thing.  So: set it, read it back, and if
    the read-back disagrees, set the component's relative rotation too.
    """
    try:
        actor.set_actor_rotation(rot, False)
    except Exception as exc:
        L('%s actor rot raised %r' % (tag, exc))
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


def aim_ok(actor, pos, target, tag):
    """Apply the aim, verify it, and fall back to the component transform."""
    rot = aim(pos, target)
    if not set_rot(actor, rot, tag):
        try:
            c = actor.get_editor_property('capture_component2d')
            c.set_editor_property('relative_rotation', rot)
            L('%s component fallback applied' % tag)
        except Exception as exc:
            L('%s component fallback failed %r' % (tag, exc))
    return rot


def spawn(world, cls, loc=(0, 0, 0), rot=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if rot is None:
        rot = unreal.Rotator(0.0, 0.0, 0.0)
    return sub.spawn_actor_from_class(cls, unreal.Vector(*loc), rot)


def comp_of(actor, *names):
    """First light component of an actor, by property name then by class."""
    for n in names:
        try:
            c = actor.get_editor_property(n)
            if c is not None:
                return c
        except Exception:
            pass
    for cn in ('SpotLightComponent', 'PointLightComponent',
               'DirectionalLightComponent'):
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
    """Rotation whose +X axis points from pos to target."""
    d = (target[0] - pos[0], target[1] - pos[1], target[2] - pos[2])
    ln = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
    if ln < 1e-6:
        return unreal.Rotator(0.0, 0.0, 0.0)
    yaw = math.degrees(math.atan2(d[1], d[0]))
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, d[2] / ln))))
    return unreal.Rotator(0.0, pitch, yaw)


def clear_world(world):
    """Remove the default new-level actors so lighting is fully controlled."""
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
    L('cleared %d default actors: %s' % (len(removed), sorted(set(removed))))
    return removed


def build_studio(world, center, size):
    """Flat floor + key (soft shadow) + fill + rim."""
    actors = []

    floor_mesh = unreal.EditorAssetLibrary.load_asset(FLOOR_MESH)
    floor_mat = unreal.EditorAssetLibrary.load_asset(FLOOR_MAT)
    fa = spawn(world, unreal.StaticMeshActor)
    fcomp = fa.static_mesh_component
    fcomp.set_static_mesh(floor_mesh)
    if floor_mat is not None:
        fcomp.set_material(0, floor_mat)
    ext = max(8.0, size * 2.5)
    fa.set_actor_scale3d(unreal.Vector(ext, ext, 0.1))
    fa.set_actor_location(unreal.Vector(center.x, center.y, -0.05), False, True)
    actors.append(fa)

    # KEY: soft spot from front-left-above. Casts the contact shadow; the
    # large source radius softens its edge.
    key_pos = (center.x - size * 0.8, center.y + size * 1.0,
               center.z + size * 1.5)
    ka = spawn(world, unreal.SpotLight)
    kc = comp_of(ka, 'spot_light_component')
    if kc is not None:
        setp(kc, 'intensity', 12000.0 * (size / 100.0) ** 2)
        setp(kc, 'light_color', unreal.LinearColor(1.0, 0.95, 0.87))
        setp(kc, 'cast_shadows', True)
        setp(kc, 'source_radius', 12.0)
        setp(kc, 'inner_cone_angle', 35.0)
        setp(kc, 'outer_cone_angle', 65.0)
    ka.set_actor_location(unreal.Vector(*key_pos), False, True)
    aim_ok(ka, key_pos, (center.x, center.y, center.z), 'KEY')
    actors.append(ka)

    # FILL: cool point light from camera-right, no shadow
    fill_pos = (center.x + size * 1.3, center.y - size * 1.1,
                center.z + size * 0.4)
    fla = spawn(world, unreal.PointLight)
    fc = comp_of(fla, 'point_light_component')
    if fc is not None:
        setp(fc, 'intensity', 1500.0 * (size / 100.0) ** 2)
        setp(fc, 'light_color', unreal.LinearColor(0.60, 0.72, 0.92))
        setp(fc, 'cast_shadows', False)
        setp(fc, 'source_radius', 30.0)
    fla.set_actor_location(unreal.Vector(*fill_pos), False, True)
    actors.append(fla)

    # RIM: cool directional from behind-above, no shadow
    rim_pos = (center.x - size * 1.5, center.y - size * 1.7,
               center.z + size * 1.4)
    ra = spawn(world, unreal.DirectionalLight)
    rc = comp_of(ra, 'directional_light_component')
    if rc is not None:
        setp(rc, 'intensity', 3.0)
        setp(rc, 'light_color', unreal.LinearColor(0.72, 0.86, 1.0))
        setp(rc, 'cast_shadows', False)
    ra.set_actor_location(unreal.Vector(*rim_pos), False, True)
    aim_ok(ra, rim_pos, (center.x, center.y, center.z), 'RIM')
    actors.append(ra)

    return actors


def place_camera(world, center, size):
    """3/4 front view, framed so the creature fills FILL of the frame."""
    half_h = size * 0.5
    dist = half_h / (math.tan(math.radians(FOV) * 0.5) * FILL)
    az = math.radians(AZIMUTH)
    el = math.radians(ELEVATION)
    pos = (center.x + math.cos(az) * math.cos(el) * dist,
           center.y + math.sin(az) * math.cos(el) * dist,
           center.z + math.sin(el) * dist)
    target = (center.x, center.y, center.z - size * 0.06)
    ca = spawn(world, unreal.SceneCapture2D)
    cc = ca.capture_component2d
    setp(cc, 'fov_angle', FOV)
    ca.set_actor_location(unreal.Vector(*pos), False, True)
    aim_ok(ca, pos, target, 'CAM')
    return ca, cc, pos, dist


def read_rt(world, vrt, w, h):
    """Read a render target and summarise it.

    The summary includes the fraction of the frame that is blown out and the
    fraction that is pure black.  A capture that never rendered shows up
    here as a deterministic garbage histogram, which is how the
    uninitialised render target was caught in the first place.
    """
    samples = unreal.RenderingLibrary.read_render_target(world, vrt)
    if not samples:
        return None
    vals = [(c.r, c.g, c.b) for c in samples]
    lum = [(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) for c in vals]
    n = len(lum)
    mid = (h // 2) * w + w // 2
    return {
        'pixels': n,
        'unique_colors': len(set(vals)),
        'min': min(min(v) for v in vals),
        'max': max(max(v) for v in vals),
        'corners': [list(vals[0]), list(vals[w - 1]),
                    list(vals[-w]), list(vals[-1])],
        'centre': list(vals[mid]),
        'blown_frac': round(sum(1 for l in lum if l > 0.95) / n, 4),
        'dark_frac': round(sum(1 for l in lum if l < 0.05) / n, 4),
    }


def _map_guard():
    """Snapshot the proofing .umap so a stray save can never be committed.

    The map is only ever edited in memory, but the editor can autosave.  We
    keep a byte-identical copy and restore it on exit if the file changed.
    """
    import hashlib
    import shutil
    import atexit
    try:
        root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        p = os.path.join(root, 'Content', 'Tests', 'M_Proof_Blockout.umap')
        if not os.path.isfile(p):
            return None
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        bak = p + '.paritybak'
        shutil.copyfile(p, bak)
        atexit.register(_map_guard_verify, (p, h, bak))
        return (p, h, bak)
    except Exception as exc:
        L('map guard unavailable: %s' % exc)
        return None


def _map_guard_verify(guard):
    """Restore the .umap byte-for-byte if the editor touched it on disk."""
    if not guard:
        return None
    import hashlib
    import shutil
    p, h, bak = guard
    try:
        h2 = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    except Exception:
        return None
    if h2 == h:
        try:
            os.remove(bak)
        except Exception:
            pass
        return h2
    try:
        shutil.copyfile(bak, p)
        os.remove(bak)
        L('MAP MODIFIED ON DISK - restored %s to %s' % (p, h[:16]))
    except Exception as exc:
        L('MAP RESTORE FAILED for %s: %s' % (p, exc))
    return h2


# ---------------------------------------------------------------------------
# The tick-driven state machine.
# ---------------------------------------------------------------------------

class Shooter(object):
    def __init__(self):
        self.report = {'width': WIDTH, 'height': HEIGHT, 'fov': FOV,
                       'fill': FILL, 'azimuth': AZIMUTH,
                       'elevation': ELEVATION, 'enemies': {}}
        self.world = None
        self.state = 'boot'
        self.index = 0
        self.rec = None
        self.comp = None
        self.vrt = None
        self.wait = 0
        self.center = None
        self.size = 0.0
        self.guard = None
        self.ticks = 0

    def report_path(self):
        return os.path.join(OUT, 'ue_shots_report.json')

    def save(self):
        write_json(self.report_path(), self.report)

    def world_ready(self):
        w = editor_world()
        if w is None:
            return None
        path = w.get_path_name()
        if not path or 'Untitled' in path:
            return None
        return w

    # -- states -----------------------------------------------------------
    def do_boot(self):
        if not os.path.isdir(SHOTS):
            os.makedirs(SHOTS)
        self.guard = _map_guard()
        try:
            ok = bool(unreal.EditorLoadingAndSavingUtils.load_map(MAP))
            L('load_map(%s) -> %s' % (MAP, ok))
        except Exception as exc:
            L('load_map(%s) raised: %s' % (MAP, exc))
        self.report['map_guard_sha256'] = self.guard[1] if self.guard else None
        self.state = 'wait_world'
        self.wait = 0

    def do_wait_world(self):
        self.wait += 1
        w = self.world_ready()
        if w is not None:
            self.world = w
            self.report['map'] = w.get_path_name()
            L('world: %s' % self.report['map'])
            clear_world(self.world)
            self.state = 'next_enemy'
            return
        if self.wait > 120:
            L('NO WORLD - aborting')
            self.report['error'] = 'no world after 120 ticks'
            self.save()
            self.state = 'done'
            return
        if self.wait % 10 == 0:
            L('waiting for world (%d ticks)' % self.wait)

    def do_next_enemy(self):
        if self.index >= len(ENEMIES):
            self.state = 'done'
            return
        name = ENEMIES[self.index]
        self.rec = {'enemy': name, 'ok': False, 'slots': []}
        path = '%s/%s.%s' % (SHIPPING, name, name)
        try:
            mesh = unreal.EditorAssetLibrary.load_asset(path)
        except Exception as exc:
            mesh = None
            L('%s mesh load raised %r' % (name, exc))
        if mesh is None:
            self.rec['error'] = 'mesh load failed: ' + path
            L('%s MESH LOAD FAILED' % name)
            self.report['enemies'][name] = self.rec
            self.save()
            self.index += 1
            return

        for s in mesh.get_editor_property('static_materials'):
            mi = s.get_editor_property('material_interface')
            self.rec['slots'].append({
                'slot': str(s.get_editor_property('material_slot_name')),
                'material': mi.get_name() if mi else None})

        bounds = mesh.get_bounds()
        org = bounds.origin
        ext = bounds.box_extent
        ma = spawn(self.world, unreal.StaticMeshActor)
        mc = ma.static_mesh_component
        mc.set_static_mesh(mesh)
        # sit the model on the floor (z = 0)
        ma.set_actor_location(
            unreal.Vector(0.0, 0.0, -org.z + ext.z), False, True)
        self.rec['bounds'] = {'origin': [org.x, org.y, org.z],
                               'extent': [ext.x, ext.y, ext.z]}

        # model centre and largest dimension -> framing
        self.center = unreal.Vector(0.0, 0.0, ext.z)
        self.size = max(ext.x, ext.y, ext.z) * 2.0
        self.rec['size'] = self.size
        self.rec['center'] = [self.center.x, self.center.y, self.center.z]
        L('%s model placed size=%.1f' % (name, self.size))

        build_studio(self.world, self.center, self.size)
        cap, comp, campos, dist = place_camera(self.world, self.center, self.size)
        self.rec['camera'] = {'pos': [campos[0], campos[1], campos[2]],
                               'distance': dist}
        self.comp = comp
        self.state = 'capture'
        self.wait = 0

    def do_capture(self):
        """Issue the capture now; read it on a later tick."""
        try:
            self.vrt = unreal.RenderingLibrary.create_render_target2d(
                self.world, WIDTH, HEIGHT,
                unreal.TextureRenderTargetFormat.RTF_RGBA8,
                unreal.LinearColor(*BG))
            self.comp.set_editor_property('texture_target', self.vrt)
            # PRM_RenderScenePrimitives: primitives only, so the world sky
            # cannot bleed into the background - the clear colour shows
            setp(self.comp, 'primitive_render_mode', 1)
            self.comp.capture_scene()
            L('%s capture issued (read in %d ticks)'
              % (self.rec['enemy'], TICKS_BEFORE_READ))
            self.wait = 0
            self.state = 'wait_read'
        except Exception as exc:
            self.rec['error'] = repr(exc)
            self.rec['traceback'] = traceback.format_exc()[-800:]
            L('%s capture ERROR %r' % (self.rec['enemy'], exc))
            self.report['enemies'][self.rec['enemy']] = self.rec
            self.save()
            self.index += 1
            self.state = 'next_enemy'

    def do_wait_read(self):
        self.wait += 1
        if self.wait < TICKS_BEFORE_READ:
            return
        info = read_rt(self.world, self.vrt, WIDTH, HEIGHT)
        if not info:
            self.rec['error'] = 'render target read returned nothing'
            L('%s NO READBACK' % self.rec['enemy'])
            self.report['enemies'][self.rec['enemy']] = self.rec
            self.save()
            self.index += 1
            self.state = 'next_enemy'
            return
        self.rec['validation'] = info
        L('%s readback %s' % (self.rec['enemy'],
                              json.dumps(info, default=str)))
        if info['pixels'] == 0 or info['unique_colors'] < 8:
            self.rec['error'] = ('render target unusable (unique=%d)'
                                 % info['unique_colors'])
            L('%s BAD CAPTURE - not exporting' % self.rec['enemy'])
            self.report['enemies'][self.rec['enemy']] = self.rec
            self.save()
            self.index += 1
            self.state = 'next_enemy'
            return
        self.state = 'export'
        self.wait = 0

    def do_export(self):
        self.wait += 1
        if self.wait < TICKS_BEFORE_EXPORT:
            return
        name = self.rec['enemy']
        before = set(os.listdir(SHOTS))
        try:
            unreal.RenderingLibrary.export_render_target(
                self.world, self.vrt, SHOTS, '%s_ue' % name)
        except Exception as exc:
            L('%s export raised %r' % (name, exc))
        after = set(os.listdir(SHOTS))
        new = sorted(after - before)
        produced = [f for f in after
                    if f.lower().startswith('%s_ue' % name.lower())]
        # normalise to exactly XCOM_<Enemy>_ue.png
        final = None
        for f in produced:
            p = os.path.join(SHOTS, f)
            if not os.path.isfile(p) or os.path.getsize(p) < 2000:
                continue
            if f.lower().endswith('.png'):
                final = f
                break
            final = f + '.png'
            try:
                os.replace(p, os.path.join(SHOTS, final))
            except Exception:
                final = f
        self.rec['exported'] = new
        self.rec['file'] = final
        self.rec['bytes'] = (os.path.getsize(os.path.join(SHOTS, final))
                             if final else 0)
        self.rec['ok'] = bool(final and self.rec['bytes'] > 2000)
        L('%s exported %s (%d bytes)' % (name, final, self.rec['bytes']))
        self.report['enemies'][name] = self.rec
        self.save()
        self.index += 1
        self.state = 'next_enemy'

    def do_done(self):
        self.save()
        ok = sum(1 for v in self.report['enemies'].values() if v.get('ok'))
        L('PHASE B COMPLETE ok=%d/5' % ok)
        try:
            unreal.SystemLibrary.quit_editor()
        except Exception as exc:
            L('quit_editor failed: %s' % exc)
        return False

    def tick(self, dt):
        self.ticks += 1
        try:
            st = self.state
            if st == 'boot':
                self.do_boot()
            elif st == 'wait_world':
                self.do_wait_world()
            elif st == 'next_enemy':
                self.do_next_enemy()
            elif st == 'capture':
                self.do_capture()
            elif st == 'wait_read':
                self.do_wait_read()
            elif st == 'export':
                self.do_export()
            elif st == 'done':
                return self.do_done()
        except Exception as exc:
            L('TICK ERROR in state %s: %r' % (self.state, exc))
            L(traceback.format_exc()[-1200:])
            if self.rec is not None:
                self.rec['error'] = repr(exc)
                self.report['enemies'][self.rec['enemy']] = self.rec
                self.save()
            self.index += 1
            self.state = 'next_enemy'
        return True


SHOOTER = Shooter()


def _on_tick(dt):
    try:
        if not SHOOTER.tick(dt):
            try:
                unreal.unregister_slate_post_tick_callback(_on_tick)
            except Exception:
                pass
    except Exception:
        pass


def main():
    L('PHASE B starting (tick-driven)')
    try:
        unreal.register_slate_post_tick_callback(_on_tick)
        L('tick callback registered')
    except Exception as exc:
        L('register_slate_post_tick_callback failed %r' % (exc,))


main()
