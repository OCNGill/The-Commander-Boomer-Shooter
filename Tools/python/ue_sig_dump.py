"""Print the REAL UE 5.8 Python signatures. No guessing after this."""

import unreal


def L(m):
    unreal.log('[SIG] ' + str(m))


def show(label, obj):
    try:
        L('=== %s ===' % label)
        L(str(obj.__doc__))
    except Exception as e:
        L('=== %s === FAILED %r' % (label, e))


show('Actor.set_actor_location', unreal.Actor.set_actor_location)
show('Actor.set_actor_rotation', unreal.Actor.set_actor_rotation)
show('Actor.set_actor_scale3d', unreal.Actor.set_actor_scale3d)
show('Actor.get_components_by_class', unreal.Actor.get_components_by_class)
show('SceneCaptureComponent2D.set_editor_property? -> capture_source',
     getattr(unreal.SceneCaptureComponent2D, 'capture_source', None))
show('EditorLoadingAndSavingUtils.load_map',
     getattr(getattr(unreal, 'EditorLoadingAndSavingUtils', None),
             'load_map', None))
show('EditorLevelLibrary.load_level',
     getattr(getattr(unreal, 'EditorLevelLibrary', None), 'load_level', None))
show('EditorActorSubsystem.spawn_actor_from_class',
     unreal.EditorActorSubsystem.spawn_actor_from_class)
show('EditorActorSubsystem.get_all_level_actors',
     unreal.EditorActorSubsystem.get_all_level_actors)
show('EditorActorSubsystem.destroy_actor',
     unreal.EditorActorSubsystem.destroy_actor)
show('RenderingLibrary.create_render_target2d',
     unreal.RenderingLibrary.create_render_target2d)
show('RenderingLibrary.export_render_target',
     unreal.RenderingLibrary.export_render_target)
show('StaticMesh.get_bounds', unreal.StaticMesh.get_bounds)
show('StaticMeshActor.static_mesh_component',
     getattr(unreal.StaticMeshActor, 'static_mesh_component', None))
show('SceneCapture2D.capture_component2d',
     getattr(unreal.SceneCapture2D, 'capture_component2d', None))

L('=== dir(unreal) Editor*Subsystem ===')
L(str([n for n in dir(unreal) if 'Editor' in n and 'Subsystem' in n]))
L('=== dir(unreal) Loading/LevelLibrary ===')
L(str([n for n in dir(unreal) if 'Loading' in n or 'LevelLibrary' in n]))

# light component classes + their tunable properties
for cn in ('SpotLightComponent', 'PointLightComponent',
           'DirectionalLightComponent', 'SkyLightComponent'):
    c = getattr(unreal, cn, None)
    if c is None:
        L('=== %s === ABSENT' % cn)
        continue
    props = [p for p in dir(c) if p in (
        'intensity', 'light_color', 'cast_shadows', 'source_radius',
        'inner_cone_angle', 'outer_cone_angle', 'temperature',
        'attenuation_radius', 'bAffectsWorld', 'bCastCloudShadows',
        'light_function', 'reverseculling')]
    L('=== %s props === %s' % (cn, props))
    for p in props:
        try:
            L('   %s doc: %s' % (p, str(getattr(c, p).__doc__)[:200]))
        except Exception as e:
            L('   %s doc failed %r' % (p, e))

# scene capture component properties
for p in ('capture_source', 'primitive_render_mode', 'fov_angle',
          'texture_target', 'show_flag_settings', 'post_process_settings',
          'capture_every_frame', 'bAlwaysPersistRenderingState'):
    try:
        L('=== SceneCaptureComponent2D.%s === %s'
          % (p, str(getattr(unreal.SceneCaptureComponent2D, p).__doc__)[:260]))
    except Exception as e:
        L('=== SceneCaptureComponent2D.%s === FAILED %r' % (p, e))

# what is actually in the parity folder
L('=== /Game/Tests/UEParity contents ===')
try:
    for a in unreal.EditorAssetLibrary.list_assets('/Game/Tests/UEParity',
                                                    recursive=True):
        L('   ' + str(a))
except Exception as e:
    L('   list failed %r' % (e,))
L('=== /Game/Tests contents ===')
try:
    for a in unreal.EditorAssetLibrary.list_assets('/Game/Tests',
                                                    recursive=True):
        L('   ' + str(a))
except Exception as e:
    L('   list failed %r' % (e,))
L('=== /Game/Enemies/XCOM contents ===')
try:
    for a in unreal.EditorAssetLibrary.list_assets('/Game/Enemies/XCOM',
                                                    recursive=True):
        L('   ' + str(a))
except Exception as e:
    L('   list failed %r' % (e,))

L('SIGDUMP COMPLETE')
