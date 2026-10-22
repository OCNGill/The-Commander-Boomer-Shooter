"""Probe 2 (read-only): what authoring surface exists for INPUT in UE 5.8 Python?

Questions:
  Q1  Can Blueprint graph nodes be inserted headlessly?
  Q2  Do Enhanced Input asset factories exist (UInputAction / UInputMappingContext)?
  Q3  What is the exact InputSettings / PlayerInput / PlayerController API surface?
  Q4  Can a key event be injected so a pawn can be observed reacting?

Writes: Saved/Probe2/probe2.json and prints [PROBE2] lines that the log will carry.
"""

import json
import os
import traceback

import unreal

OUT_DIR = os.path.join(unreal.Paths.project_saved_dir(), "Probe2")
os.makedirs(OUT_DIR, exist_ok=True)

R = {}


def cap(name, fn):
    try:
        R[name] = fn()
    except Exception as e:  # noqa
        R[name] = "ERR: %r" % (e,)


def d(cls, filt=None):
    try:
        names = dir(cls)
    except Exception as e:  # noqa
        return "ERR: %r" % (e,)
    if filt:
        names = [n for n in names if any(k in n.lower() for k in filt)]
    return sorted(names)


# ---------------------------------------------------------------- Q1 graph
cap("q1_edgraph_dir", lambda: d(unreal.EdGraph))
cap("q1_edgraph_add_node", lambda: [n for n in dir(unreal.EdGraph) if "node" in n.lower()])
cap("q1_bp_editor_library", lambda: d(unreal.BlueprintEditorLibrary))
cap("q1_k2node_input_axis", lambda: d(unreal.K2Node_InputAxis) if hasattr(unreal, "K2Node_InputAxis") else "MISSING")
cap("q1_k2node_input_action", lambda: d(unreal.K2Node_InputAction) if hasattr(unreal, "K2Node_InputAction") else "MISSING")
cap("q1_k2node_call_function", lambda: d(unreal.K2Node_CallFunction) if hasattr(unreal, "K2Node_CallFunction") else "MISSING")
cap("q1_k2node_enhanced_action", lambda: d(unreal.K2Node_EnhancedInputActionEvent)
      if hasattr(unreal, "K2Node_EnhancedInputActionEvent") else "MISSING")
cap("q1_graph_classes", lambda: sorted(n for n in dir(unreal)
                                       if "graph" in n.lower() or "pin" in n.lower() or "k2node" in n.lower()))
cap("q1_has_new_object", lambda: hasattr(unreal, "new_object"))
cap("q1_ed_graph_pin_lib", lambda: d(unreal.BlueprintGraphPinLibrary)
      if hasattr(unreal, "BlueprintGraphPinLibrary") else "MISSING")

# ---------------------------------------------------------------- Q2 enhanced input assets
cap("q2_input_action", lambda: d(unreal.InputAction) if hasattr(unreal, "InputAction") else "MISSING")
cap("q2_input_mapping_context", lambda: d(unreal.InputMappingContext)
      if hasattr(unreal, "InputMappingContext") else "MISSING")
cap("q2_factories", lambda: sorted(n for n in dir(unreal) if "factory" in n.lower()))
cap("q2_asset_tools", lambda: d(unreal.AssetToolsHelpers))
cap("q2_enhanced_dev_settings", lambda: d(unreal.EnhancedInputDeveloperSettings)
      if hasattr(unreal, "EnhancedInputDeveloperSettings") else "MISSING")
cap("q2_enhanced_subsystem", lambda: d(unreal.EnhancedInputLocalPlayerSubsystem)
      if hasattr(unreal, "EnhancedInputLocalPlayerSubsystem") else "MISSING")
cap("q2_ia_asset_paths", lambda: [
    p for p in unreal.EditorAssetLibrary.list_assets("/Game", recursive=True, include_folder=False)
    if p.lower().endswith(".uasset")][:200])
cap("q2_engine_content_input", lambda: [
    p for p in unreal.EditorAssetLibrary.list_assets("/Engine", recursive=True, include_folder=False)
    if ("/input" in p.lower() or "ia_" in p.lower() or "imc" in p.lower())
    and not p.lower().endswith(".uasset")][:80])

# ---------------------------------------------------------------- Q3 input api
cap("q3_input_settings", lambda: d(unreal.InputSettings))
cap("q3_player_input", lambda: d(unreal.PlayerInput))
cap("q3_enhanced_player_input", lambda: d(unreal.EnhancedPlayerInput)
      if hasattr(unreal, "EnhancedInputPlayerInput") else d(unreal.EnhancedPlayerInput))
cap("q3_player_controller_input", lambda: d(unreal.PlayerController, ("input", "key", "axis", "action")))
cap("q3_pawn_input", lambda: d(unreal.Pawn, ("input", "axis", "action", "rotation")))
cap("q3_default_pawn", lambda: d(unreal.DefaultPawn, ("input", "axis", "action", "move", "turn", "look")))
cap("q3_character", lambda: d(unreal.Character, ("input", "axis", "action", "jump")))
cap("q3_input_component", lambda: d(unreal.InputComponent, ("bind", "axis", "action", "key")))
cap("q3_input_settings_obj", lambda: {
    "axis_mappings": [str(m) for m in unreal.InputSettings.get_axis_mappings()],
    "action_mappings": [str(m) for m in unreal.InputSettings.get_action_mappings()],
    "default_player_input_class": str(unreal.InputSettings.get_default_player_input_class()),
    "default_input_component_class": str(unreal.InputSettings.get_default_input_component_class()),
})
cap("q3_default_game_mode_setting", lambda: {
    "global_default_game_mode": str(unreal.get_default_object(unreal.GameMapsSettings).get_editor_property("global_default_game_mode")),
    "game_default_map": str(unreal.get_default_object(unreal.GameMapsSettings).get_editor_property("game_default_map")),
    "project_game_maps_settings": str(unreal.get_default_object(unreal.GameMapsSettings).get_editor_property("project_game_maps_settings")),
})

# ---------------------------------------------------------------- Q4 injection
cap("q4_system_library", lambda: d(unreal.SystemLibrary, ("console", "command")))
cap("q4_player_controller_exec", lambda: d(unreal.PlayerController, ("exec", "console", "command")))
cap("q4_input_key_types", lambda: sorted(n for n in dir(unreal) if "key" in n.lower())[:120])

path = os.path.join(OUT_DIR, "probe2.json")
with open(path, "w") as fh:
    json.dump(R, fh, indent=1, default=str)

print("[PROBE2] wrote %s" % path)
for k in sorted(R):
    v = R[k]
    if isinstance(v, list):
        print("[PROBE2] %-28s list[%d] %s" % (k, len(v), v[:40]))
    elif isinstance(v, dict):
        print("[PROBE2] %-28s dict %s" % (k, json.dumps(v, default=str)[:1200]))
    else:
        s = str(v)
        print("[PROBE2] %-28s %s" % (k, s[:1200]))
print("[PROBE2] DONE")
