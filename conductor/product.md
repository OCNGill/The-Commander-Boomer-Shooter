# The Commander Boomer Shooter — Product Definition

## What
Boomer shooter (retro FPS) built in Unreal Engine 5.8 with Blender for asset creation. The Commander's personal game project.

## Why
"Ship the games" — Commander's directive. Demonstrates sovereign game dev pipeline: UE5 + Blender + local AI (Blender-MCP, llama.cpp for code assist).

## Architecture
```
The_Commander_Boomer_Shooter/
├── UE5 project (blueprints)
├── Blender assets (via blender-mcp)
├── conductor/
└── CHANGELOG.md
```

## Quick Start
1. Open .uproject in UE 5.8
2. Blender assets via blender-mcp skill
3. Local inference for code assist (Main node Qwen3.8-27B)

## Node Map
| Host | Role |
|------|------|
| Main (10.0.0.164, 7900 XTX 24GB) | UE5 dev + local inference |
| HTPC (10.0.0.42, RX 7600) | Blender rendering |
| GitHub | Version control |
