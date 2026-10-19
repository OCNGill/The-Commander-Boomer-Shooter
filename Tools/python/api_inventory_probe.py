"""API inventory: which actor-listing path exists in this UE 5.8 build?"""
import unreal
def L(m): unreal.log('[APILIST] ' + str(m))

w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
L('world dir: ' + ', '.join(sorted(d for d in dir(w) if not d.startswith('_'))))
for cls_name, cls in (('EditorLevelLibrary', unreal.EditorLevelLibrary),
                      ('EditorActorSubsystem', unreal.get_editor_subsystem(unreal.EditorActorSubsystem)),
                      ('UnrealEditorSubsystem', unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem))):
    d = sorted(x for x in dir(cls) if not x.startswith('_'))
    hits = [x for x in d if 'actor' in x.lower() or 'level' in x.lower() or 'all' in x.lower()]
    L('%s: %s' % (cls_name, ', '.join(hits)))
# try the candidates we can see
for expr in ('unreal.EditorLevelLibrary.get_all_level_actors()',
             'unreal.GameplayStatics.get_all_actors_of_class(unreal.EditorLevelLibrary.get_editor_world() if hasattr(unreal.EditorLevelLibrary,"get_editor_world") else None, unreal.StaticMeshActor)'):
    try:
        r = eval(expr)
        L('TRY %s -> %r (len=%s)' % (expr, type(r), len(r) if r is not None else None))
    except Exception as e:
        L('TRY %s -> EXC %r' % (expr, e))
# world .actors variants
for attr in ('persistent_level', 'get_persistent_level', 'levels', 'get_levels', 'actor_iterator'):
    L('world has %s: %s' % (attr, hasattr(w, attr)))
unreal.log('[APILIST_DONE]')
