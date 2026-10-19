# Track Registry — The Commander Boomer Shooter

## Active Tracks
| # | Name | Status | Phase | Description |
|---|------|--------|-------|-------------|
| 1 | UE5 Project Initialization | **COMPLETE** | **Deploy ✓** | UE 5.8 blueprint project + design brief (commit cef143e) |
| 2 | Headless content pipeline (UE commandlets) | **COMPLETE** | **Deploy ✓** | PythonScriptPlugin enabled; blockout_map.py generates M_Blockout01 (23 actors) via UnrealEditor-Cmd, verified on disk |
| 3 | Blender asset pipeline (blender -b, no MCP needed) | **ACTIVE** | Build | weapon_blockouts.py + import_weapons_fbx.py authored; Blender 4.2 portable en route (download.blender.org Cloudflare-blocks curl → mirror mirrors.dotsrc.org) |
| 4 | Core combat loop | **ACTIVE** | Spec | weapons_enemies_v1.json (Main qwen3.8-27b local pass): 6 weapons + 6 Plymouth enemies |

## Future Tracks
| # | Name | Description |
|---|------|-------------|
| 1 | Blender asset pipeline (blender-mcp) | Weapons, enemies, levels via blender-mcp |
| 2 | Core combat loop | Movement, shooting, enemy AI |
| 3 | Level design | Plymouth MA themed levels |
| 4 | Local AI integration | Qwen3.8-27B for Blueprint assist |
| 5 | itch.io/Steam release | Sovereign deployment |
