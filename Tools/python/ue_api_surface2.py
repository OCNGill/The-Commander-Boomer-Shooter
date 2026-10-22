"""Probe 2: dump members of the real 5.8 Python classes we need.

Writes CommandCenter/outputs/ue_verify/_api_surface2.json
"""

import json
import os

import unreal

REPO = r'C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter'
OUT = os.path.join(REPO, 'CommandCenter', 'outputs', 'ue_verify')

CLASSES = [
    'RenderingLibrary', 'AutomationLibrary', 'AutomationUtilsBlueprintLibrary',
    'EditorAssetLibrary', 'EditorLevelLibrary', 'UnrealEditorSubsystem',
    'EditorActorSubsystem', 'StaticMeshActor', 'StaticMeshComponent',
    'SceneCapture2D', 'SceneCaptureComponent2D', 'TextureRenderTarget2D',
    'TextureRenderTarget2DFactoryNew', 'MaterialEditingLibrary',
    'MaterialFactoryNew', 'MaterialInstanceConstantFactoryNew',
    'MaterialExpressionConstant3Vector', 'MaterialExpressionTextureSample',
    'MaterialExpressionConstant', 'Material',
    'DirectionalLight', 'PointLight', 'SpotLight', 'SkyLight',
    'ExponentialHeightFog', 'SkyAtmosphere', 'VolumetricCloud',
    'PostProcessVolume', 'PostProcessSettings',
    'BlueprintMaterialTextureNodesBPLibrary', 'EditorLevelUtils',
    'EditorStaticMeshLibrary', 'StaticMeshEditorSubsystem',
    'LevelSequence', 'LevelSequenceActor', 'LevelSequenceEditorLibrary',
    'MovieRenderPipelineQueue', 'MovieRenderPipeline',
    'MovieRenderPipelineExecutor', 'MovieRenderPipelineEditorSubsystem',
    'MovieGraphQuickRenderSubsystem', 'MovieGraphQuickRenderSettings',
    'ImageWriteQueue', 'RenderTargetExporterPNG', 'AsyncImageExport',
    'TextureExporterPNG', 'FileHelper', 'EditorFileHelper',
    'ScreenshotFunctionalTest', 'AutomationScreenshotOptions',
    'CaptureResolution', 'World', 'Level', 'StaticMesh',
]


def members(name):
    cls = getattr(unreal, name, None)
    if cls is None:
        return None
    try:
        return sorted([d for d in dir(cls) if not d.startswith('_')])
    except Exception as e:
        return ['ERR ' + repr(e)]


data = {}
for c in CLASSES:
    data[c] = members(c)

if not os.path.isdir(OUT):
    os.makedirs(OUT)
with open(os.path.join(OUT, '_api_surface2.json'), 'w') as f:
    json.dump(data, f, indent=1, sort_keys=True)

unreal.log('[UEAPI2] RenderingLibrary present=%s' % (data.get('RenderingLibrary') is not None))
for c in CLASSES:
    m = data.get(c)
    if m is None:
        unreal.log('[UEAPI2] %-38s ABSENT' % c)
    else:
        unreal.log('[UEAPI2] %-38s n=%d' % (c, len(m)))
unreal.log('[UEAPI2] DONE')
