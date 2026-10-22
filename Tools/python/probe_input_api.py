"""Probe the live UE 5.8 Python API surface for the input-stack lane.

READ-ONLY. Touches no project asset. Answers:
  1. Can a Blueprint be authored headlessly (graph nodes)?
  2. What input readback / injection APIs exist?
  3. What does the demo map actually contain (PlayerStart, WorldSettings GameMode)?
  4. Is EnhancedInput reachable from Python?

Writes the full dump to the scratch dir; prints a compact summary to the log.
"""

import json
import os

import unreal

SCRATCH = r'C:/Users/Gillsystems Laptop/AppData/Local/hermes/cache/scratch'
MAP = '/Game/Maps/M_Blockout01'
OUT = os.path.join(SCRATCH, 'probe_input_api.json')

L = []


def log(msg):
    text = '[INPPROBE] ' + str(msg)
    unreal.log(text)
    L.append(text)


def members(name):
    cls = getattr(unreal, name, None)
    if cls is None:
        return None
    try:
        return sorted([d for d in dir(cls) if not d.startswith('_')])
    except Exception as e:
        return ['ERR ' + repr(e)]


data = {}
names = dir(unreal)

# --- 1. graph authoring surface -----------------------------------------
data['k2node_classes'] = [n for n in names if 'K2Node' in n]
data['edgraph_classes'] = [n for n in names if 'EdGraph' in n]
data['blueprint_classes'] = [n for n in names if 'Blueprint' in n]
data['input_asset_classes'] = [n for n in names if 'Input' in n and (
    'Action' in n or 'Mapping' in n or 'Enhanced' in n or 'Factory' in n)]
data['subsystems'] = [n for n in names if 'Subsystem' in n]

# --- 2. members of the classes the proof needs --------------------------
for c in ['PlayerInput', 'PlayerController', 'InputComponent',
          'EnhancedPlayerInput', 'EnhancedInputComponent', 'InputSettings',
          'EnhancedInputDeveloperSettings', 'BlueprintFactory',
          'BlueprintEditorLibrary', 'LevelEditorSubsystem',
          'EditorLevelLibrary', 'UnrealEditorSubsystem', 'EditorActorSubsystem',
          'AutomationLibrary', 'EditorAssetLibrary', 'World', 'WorldSettings',
          'GameplayStatics', 'KismetSystemLibrary', 'Pawn', 'Character',
          'DefaultPawn', 'GameModeBase', 'PlayerStart']:
    data['m_' + c] = members(c)

# --- 3. the demo map: actors + world settings ---------------------------
try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    log('loaded map ' + MAP)
except Exception as e:
    log('load_map failed: %r' % e)

try:
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = sub.get_all_level_actors()
    rows = []
    for a in actors:
        rows.append({'label': a.get_actor_label(),
                     'class': a.get_class().get_name()})
    data['map_actors'] = rows
    data['map_actor_count'] = len(rows)
    log('map actors=%d' % len(rows))
    for r in rows:
        log('  actor %-24s %s' % (r['label'], r['class']))
except Exception as e:
    data['map_actors'] = []
    log('actor enumeration failed: %r' % e)

try:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    data['world_name'] = world.get_name() if world else None
    ws = world.get_world_settings() if world else None
    if ws:
        data['world_settings_class'] = ws.get_class().get_name()
        gm = ws.get_editor_property('default_game_mode')
        data['world_default_game_mode'] = str(gm)
        log('WorldSettings.default_game_mode = %r' % gm)
    else:
        log('no world settings')
except Exception as e:
    log('world settings read failed: %r' % e)

# --- 4. current input settings -----------------------------------------
try:
    s = unreal.get_default_object(unreal.InputSettings)
    data['input_settings_class'] = s.get_class().get_name()
    for prop in ['axis_mappings', 'action_mappings']:
        try:
            v = s.get_editor_property(prop)
            data['input_' + prop] = str(v)
            log('InputSettings.%s = %s' % (prop, v))
        except Exception as e:
            data['input_' + prop] = 'ERR %r' % e
    for prop in ['default_player_input_class', 'default_input_component_class',
                 'b_enable_mouse_smoothing', 'b_use_mouse_for_touch',
                 'default_touch_interface']:
        try:
            v = s.get_editor_property(prop)
            data['input_' + prop] = str(v)
            log('InputSettings.%s = %s' % (prop, v))
        except Exception as e:
            data['input_' + prop] = 'ERR %r' % e
except Exception as e:
    log('InputSettings read failed: %r' % e)

# --- 5. Enhanced Input assets reachable? --------------------------------
for c in ['InputAction', 'InputMappingContext', 'EnhancedActionKeyMapping',
          'InputActionFactoryNew', 'InputMappingContextFactoryNew']:
    log('class %-30s present=%s' % (c, getattr(unreal, c, None) is not None))

try:
    dev = unreal.get_default_object(unreal.EnhancedInputDeveloperSettings)
    dmc = dev.get_editor_property('default_mapping_contexts')
    data['enhanced_default_mapping_contexts'] = str(dmc)
    data['enhanced_bEnableDefaultMappingContexts'] = str(
        dev.get_editor_property('b_enable_default_mapping_contexts'))
    log('EnhancedInputDeveloperSettings.default_mapping_contexts = %s' % dmc)
    log('EnhancedInputDeveloperSettings.bEnableDefaultMappingContexts = %s' % dev.get_editor_property('b_enable_default_mapping_contexts'))
except Exception as e:
    log('EnhancedInputDeveloperSettings read failed: %r' % e)

with open(OUT, 'w') as f:
    json.dump(data, f, indent=1, sort_keys=True, default=str)

log('WROTE ' + OUT)
log('DONE')
