# Track Registry — The Commander Boomer Shooter

## Active Tracks
| # | Name | Status | Phase | Description |
|---|------|--------|-------|-------------|
| 1 | UE5 Project Initialization | **COMPLETE** | **Deploy ✓** | UE 5.8 blueprint project + design brief (commit cef143e) |
| 2 | Headless content pipeline (UE commandlets) | **COMPLETE** | **Deploy ✓** | PythonScriptPlugin enabled; blockout_map.py generates M_Blockout01 (23 actors) via UnrealEditor-Cmd, verified on disk |
| 3 | Blender asset pipeline (blender -b, no MCP needed) | **COMPLETE** | **Deploy ✓** | 14 FBX blockouts (3 weapons, 5 pickups/keycards, 6 enemy proxies) → headless import into /Game/Weapons (14/14, 0 errors). Blender 4.2.23 portable at D:\Blender |
| 4 | Core combat loop | **READY TO BUILD** | Spec | weapons_enemies_v1.json + blueprint_build_spec.md (19.8K node-by-node) + level1_bible.md — waiting on interactive editor session (Commander at keyboard) |
| 5 | Encounter layout (map population) | **COMPLETE** | **Deploy ✓** | 18 encounter actors + 4 horror lights + fog populated into M_Blockout01 (run5: 18/18, scaled from real bounds, 0 errors) |

## Future Tracks
| # | Name | Description |
|---|------|-------------|
| 1 | Blender asset pipeline (blender-mcp) | Weapons, enemies, levels via blender-mcp |
| 2 | Core combat loop | Movement, shooting, enemy AI |
| 3 | Level design | Plymouth MA themed levels |
| 4 | Local AI integration | Qwen3.8-27B for Blueprint assist |
| 5 | itch.io/Steam release | Sovereign deployment |
