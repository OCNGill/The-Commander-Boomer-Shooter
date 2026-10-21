"""Read-only dump of every actor transform in M_Blockout01 -> JSON + log.

HEADLESS:
  UnrealEditor-Cmd.exe TheCommander.uproject -run=pythonscript \
      -script=Tools/python/dump_level_transforms.py -unattended -nosplash -NoSound \
      -stdout -FullStdOutLogOutput -abslog=Saved/Logs/leveldump_run1.log

READ-ONLY CONTRACT: this script never calls save_map / save_asset /
save_dirty_packages / save_current_level. The .umap is never written.

Enumeration is multi-strategy because load_map() is asynchronous inside a
commandlet and a cached EditorActorSubsystem can still point at a stale world:
  A) EditorActorSubsystem.get_all_level_actors()  (re-fetched every attempt)
  B) EditorLevelLibrary.get_all_level_actors()
  C) editor world -> get_levels() -> Level.actors
  D) editor world -> get_current_level().actors
The union of all strategies is dumped. Every actor name + class is printed so
the enumeration is provable from the log, not inferred.
"""

import unreal
import json
import os
import time

MAP = '/Game/Maps/M_Blockout01'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
OUT_DIR = os.path.join(ROOT, 'Docs', 'generated')
OUT_JSON = os.path.join(OUT_DIR, 'level_transforms.json')
UMAP_PATH = os.path.join(ROOT, 'Content', 'Maps', 'M_Blockout01.umap')


def L(msg):
    text = '[LEVELDUMP] ' + str(msg)
    try:
        unreal.log(text)
    except Exception:
        pass
    try:
        print(text)
    except Exception:
        pass


def r3(v):
    try:
        return [round(float(v.x), 3), round(float(v.y), 3), round(float(v.z), 3)]
    except Exception:
        try:
            return [round(float(x), 3) for x in v]
        except Exception:
            return [0.0, 0.0, 0.0]


def group_of(name, label, cls):
    s = ('%s|%s|%s' % (name, label, cls)).upper()
    for pref in ('ENC_', 'PU_', 'WP_'):
        if pref in s:
            return pref[:-1]
    for key, tag in (('LIGHT', 'light'), ('SKY', 'sky'), ('FOG', 'fog'),
                     ('PIT', 'pit'), ('RAMP', 'ramp'), ('PLATFORM', 'platform'),
                     ('COVER', 'cover'), ('PILLAR', 'pillar'), ('COLUMN', 'pillar'),
                     ('WALL', 'wall'), ('PLAYERSTART', 'playerstart'),
                     ('FLOOR', 'floor')):
        if key in s:
            return tag
    return 'other'


def size_on_disk():
    try:
        return os.path.getsize(UMAP_PATH)
    except Exception:
        return -1


def gather():
    found = {}
    counts = {}

    def add(lst, tag):
        try:
            items = list(lst or [])
        except Exception as exc:
            counts[tag] = 'ERROR %r' % (exc,)
            return
        counts[tag] = len(items)
        for a in items:
            try:
                found[a.get_name()] = a
            except Exception:
                pass

    try:
        add(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors(),
            'A_EditorActorSubsystem')
    except Exception as exc:
        counts['A_EditorActorSubsystem'] = 'ERROR %r' % (exc,)
    try:
        add(unreal.EditorLevelLibrary.get_all_level_actors(), 'B_EditorLevelLibrary')
    except Exception as exc:
        counts['B_EditorLevelLibrary'] = 'ERROR %r' % (exc,)
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        try:
            L('editor world: %s' % world.get_path_name())
        except Exception:
            pass
        try:
            levels = list(world.get_levels())
            per = []
            for lv in levels:
                try:
                    per.append(len(list(lv.actors)))
                except Exception:
                    per.append(0)
            counts['C_world_levels'] = '%d levels %s' % (len(levels), per)
            for lv in levels:
                try:
                    add(lv.actors, 'C_world_levels')
                except Exception:
                    pass
        except Exception as exc:
            counts['C_world_levels'] = 'ERROR %r' % (exc,)
        try:
            add(world.get_current_level().actors, 'D_current_level')
        except Exception as exc:
            counts['D_current_level'] = 'ERROR %r' % (exc,)
    except Exception as exc:
        counts['C_D_world'] = 'ERROR %r' % (exc,)
    return found, counts


def light_info(actor):
    comp = None
    try:
        comps = actor.get_components_by_class(unreal.LightComponent)
        comp = comps[0] if comps else None
    except Exception:
        comp = None
    if comp is None:
        try:
            comp = actor.light_component
        except Exception:
            comp = None
    col = None
    inten = None
    if comp is not None:
        try:
            c = comp.get_editor_property('light_color')
            col = [round(float(c.r), 3), round(float(c.g), 3), round(float(c.b), 3)]
        except Exception:
            col = None
        try:
            inten = round(float(comp.get_editor_property('intensity')), 3)
        except Exception:
            inten = None
    return col, inten


def main():
    size_before = size_on_disk()
    L('package %s exists=%s' % (MAP, unreal.EditorAssetLibrary.does_asset_exist(MAP)))
    L('on-disk umap before: %s bytes (%s)' % (size_before, UMAP_PATH))
    L('READ-ONLY: no save_map / save_asset / save_dirty_packages will be called')

    L('loading map ' + MAP)
    try:
        unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    except Exception as exc:
        L('load_map FAILED: %r' % (exc,))

    for _ in range(20):
        try:
            unreal.SystemLibrary.delay(0.05)
        except Exception:
            try:
                time.sleep(0.05)
            except Exception:
                pass
    L('world tick window elapsed (20 x 0.05s)')

    actors, counts = gather()
    for tag in sorted(counts):
        L('strategy %s -> %s' % (tag, counts[tag]))
    L('union actor count: %d' % len(actors))

    for name in sorted(actors):
        a = actors[name]
        try:
            cls = a.get_class().get_name()
        except Exception:
            cls = 'Unknown'
        try:
            lab = a.get_actor_label()
        except Exception:
            lab = ''
        L('ACTOR name=%s class=%s label=%s' % (name, cls, lab))

    records = []
    for name in sorted(actors):
        actor = actors[name]
        try:
            label = actor.get_actor_label()
        except Exception:
            label = ''
        try:
            cls = actor.get_class().get_name()
        except Exception:
            cls = 'Unknown'

        loc = [0.0, 0.0, 0.0]
        rot = {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0}
        scale = [1.0, 1.0, 1.0]
        try:
            tr = actor.get_actor_transform()
            loc = r3(tr.location)
            rot = {'pitch': round(float(tr.rotation.pitch), 3),
                   'yaw': round(float(tr.rotation.yaw), 3),
                   'roll': round(float(tr.rotation.roll), 3)}
            scale = r3(tr.scale3d)
        except Exception:
            try:
                loc = r3(actor.get_actor_location())
                rr = actor.get_actor_rotation()
                rot = {'pitch': round(float(rr.pitch), 3),
                       'yaw': round(float(rr.yaw), 3),
                       'roll': round(float(rr.roll), 3)}
                scale = r3(actor.get_actor_scale3d())
            except Exception:
                pass

        mesh = ''
        sm = None
        try:
            sm = actor.static_mesh_component.get_static_mesh()
        except Exception:
            sm = None
        if sm is None:
            try:
                sm = actor.get_editor_property('static_mesh')
            except Exception:
                sm = None
        if sm is None:
            try:
                sm = actor.static_mesh
            except Exception:
                sm = None
        if sm is not None:
            try:
                mesh = sm.get_name()
            except Exception:
                mesh = ''

        lcol, linten = (None, None)
        if 'Light' in cls:
            lcol, linten = light_info(actor)

        rec = {'name': name, 'label': label, 'class': cls, 'loc': loc,
               'rot': rot, 'scale': scale, 'mesh': mesh,
               'group': group_of(name, label, cls), 'source': 'map'}
        if lcol is not None:
            rec['light_color'] = lcol
        if linten is not None:
            rec['light_intensity'] = linten
        # Ramp end points in world space, measured from the live actor. The renderer builds
        # ramps from THESE, not from a guessed Euler convention that may not match the engine.
        if 'ramp' in str(label).lower():
            try:
                _r = actor.get_actor_right_vector()
                _s = actor.get_actor_scale3d()
                _half = abs(float(_s.y)) * 50.0
                _c = actor.get_actor_location()
                rec['ends'] = [[round(_c.x + _r.x * _half, 2), round(_c.y + _r.y * _half, 2), round(_c.z + _r.z * _half, 2)],
                               [round(_c.x - _r.x * _half, 2), round(_c.y - _r.y * _half, 2), round(_c.z - _r.z * _half, 2)]]
            except Exception as _exc:
                L('end point probe failed for %s: %r' % (label, _exc))
        records.append(rec)
        L('name=%s class=%s loc=%s rot=%s scale=%s mesh=%s group=%s'
          % (name, cls, loc, rot, scale, mesh or '-', rec['group']))

    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(OUT_JSON, 'w') as fh:
            json.dump(records, fh, indent=1)
        L('wrote %s (%d bytes)' % (OUT_JSON, os.path.getsize(OUT_JSON)))
    except Exception as exc:
        L('json write FAILED: %r' % (exc,))

    size_after = size_on_disk()
    L('on-disk umap after: %s bytes (unchanged=%s)' % (size_after, size_after == size_before))
    L('TOTAL=%d' % len(records))
    L('MAP_UNSAVED_READONLY_OK')


main()
