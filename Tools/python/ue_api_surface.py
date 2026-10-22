"""Throwaway probe: dump the UE 5.8 Python API surface we need for rendering.

Writes the full dir(unreal) listing plus per-class members to
CommandCenter/outputs/ue_verify/_api_surface.json so we can grep it
offline instead of guessing.

No RHI, no map, no writes outside CommandCenter/outputs/ue_verify/.
"""

import json
import os

import unreal

REPO = r'C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter'
OUT = os.path.join(REPO, 'CommandCenter', 'outputs', 'ue_verify')

TOP = sorted(dir(unreal))

CANDIDATE_CLASSES = [
    'KismetRenderingLibrary', 'SceneCapture2D', 'SceneCaptureComponent2D',
    'TextureRenderTarget2D', 'RenderTarget2D', 'RenderTargetPool',
    'ImageWriteQueue', 'ImageWriteTask', 'AutomationLibrary',
    'EditorLevelLibrary', 'EditorActorSubsystem', 'UnrealEditorSubsystem',
    'StaticMeshActor', 'StaticMeshComponent', 'DirectionalLight',
    'PointLight', 'SkyLight', 'ExponentialHeightFog', 'SkyAtmosphere',
    'Material', 'MaterialInstanceConstant', 'MaterialExpressionTextureSample',
    'Texture2D', 'EditorStaticMeshLibrary', 'StaticMeshEditorSubsystem',
    'MovieRenderPipeline', 'MovieRenderPipelineConfig',
    'MovieRenderPipelineExecutor', 'MovieRenderPipelineQueue',
    'MovieRenderPipelineSubsystem', 'LevelSequence', 'LevelSequenceActor',
    'ScreenshotRequest', 'Buffer', 'Canvas', 'WidgetBlueprintLibrary',
    'EditorValidatorSubsystem', 'Object',
]


def members(name):
    cls = getattr(unreal, name, None)
    if cls is None:
        return None
    try:
        return sorted([d for d in dir(cls) if not d.startswith('_')])
    except Exception as e:
        return ['ERR ' + repr(e)]


data = {
    'unreal_top_count': len(TOP),
    'unreal_top': TOP,
    'candidates': {},
}

for c in CANDIDATE_CLASSES:
    data['candidates'][c] = members(c)

# name-based search across the whole unreal namespace
for needle in ('render_target', 'rendertexture', 'screenshot', 'image_write',
               'imagewrite', 'capture', 'kismet', 'png', 'export', 'savetexture',
               'texture2d'):
    data['candidates']['__search__' + needle] = [
        n for n in TOP if needle in n.lower()]

if not os.path.isdir(OUT):
    os.makedirs(OUT)
with open(os.path.join(OUT, '_api_surface.json'), 'w') as f:
    json.dump(data, f, indent=1, sort_keys=True)

unreal.log('[UEAPI] dumped %d top-level unreal names' % len(TOP))
for k in ('render_target', 'screenshot', 'image_write', 'capture', 'kismet',
          'png', 'export'):
    hits = data['candidates']['__search__' + k]
    unreal.log('[UEAPI] %s -> %s' % (k, hits[:25]))
unreal.log('[UEAPI] DONE')
