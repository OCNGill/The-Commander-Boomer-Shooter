# SWARM LEDGER — one line per completed task

TASK-ID | slot | artifact | result | timestamp
EBERT-01 | Hermes-session | CommandCenter/outputs/ebert/EBERT_ENEMY_VERDICT.md | 3.33 REJECT | 2026-10-21T00:52:17.938394-04:00
HTPC-BLENDER-01 | Hermes-session | Tools/blender/out_xcom/*.fbx (5 FBX) | HTPC flock-serialized Blender turn verified: lock acquired, 5 X-COM enemies built FBX-only, 2864/3712/1980/2520/2536 tris, RAM held 3.2GB free | 2026-10-21T00:55:15-04:00
EBERT-01 | Hermes-session | CommandCenter/outputs/ebert/EBERT_ENEMY_VERDICT.md | X-COM enemy kit scored 3.33/7.0 ITERATE (bar 6.2) - 5 PNGs viewed with vision_analyze; axis bar defined for level design, background textures, lighting, main character | 2026-10-21T00:59:35-04:00
FIXLIST-01 | Hermes-session | CommandCenter/briefs/XCOM_ENEMY_V2_FIXLIST.md | Independent vision review of v1 renders converted into 9 engineering fix groups (grounding, reveal rig + Glare, faces, anatomy, material logic, surface story, gear, pose, camera) | 2026-10-21T00:59:35-04:00
LEVEL-01 | Hermes-session | Content/Maps/M_Blockout01.umap | BASE ARENA WAS NEVER IN THE MAP - blockout_map.py used the dead spawn_actor_from_object path, so the 23 base actors never spawned; committed map held only 18 encounters in an empty void. ensure_base_geometry.py rebuilt the arena with spawn_actor_from_class + set_static_mesh. Dump now 46 actors (21 geometry + 18 spawns + lights) | 2026-10-21T01:05:09-04:00
PIT-01 | Hermes-session | Tools/python/fix_pit_and_ramp.py | Floor had NO hole (pit+pickups unreachable under the plane); BO_Ramp_NE buried inside the platform footprint. New script cuts a real hole, rebuilds the rim, re-places the ramp | 2026-10-21T02:12:55-04:00
VERIFY-01 | Hermes-session | Content/Maps/M_Blockout01.umap | Commit 0a2e558 enshrined a REVERTED map (blob 50,181B / 25 actors). Blob size inside the commit is now mandatory proof - a dump proves nothing about disk | 2026-10-21T02:12:55-04:00
