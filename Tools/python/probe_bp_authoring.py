"""Headless probe: can this editor author Blueprint gameplay assets from Python?

READ-ONLY in spirit - it creates throwaway assets under /Game/_Probe and deletes
them at the end. It answers three questions that decide the architecture:

  Q1  Which authoring entry points exist (BlueprintEditorLibrary, EdGraph,
      K2Node_* classes, asset factories)?
  Q2  Can a Blueprint's CLASS DEFAULTS be set from Python (CDO edit) and do they
      survive a save/reload? This is how a GameMode gets its PlayerController and
      Pawn classes without hand-authoring a graph.
  Q3  Can a Blueprint EVENT GRAPH get nodes added and wired from Python? This is
      how a pawn would bind legacy axis/action names.

Writes probe_bp_authoring.json next to this script's scratch and logs a summary.
"""

import json
import os
import traceback

import unreal

SCRATCH = os.environ.get(
    "HERMES_SCRATCH", r"C:/Users/Gillsystems Laptop/AppData/Local/hermes/cache/scratch"
)
OUT = os.path.join(SCRATCH, "probe_bp_authoring.json")

R = {}


def log(msg):
    unreal.log("[BPPROBE] %s" % msg)


def members(obj_name):
    """List the Python-visible members of an unreal class."""
    cls = getattr(unreal, obj_name, None)
    if cls is None:
        return None
    names = [n for n in dir(cls) if not n.startswith("_")]
    return sorted(names)


# ---------------------------------------------------------------- Q1: surface
R["q1_present"] = {
    name: hasattr(unreal, name)
    for name in [
        "BlueprintEditorLibrary",
        "BlueprintFactory",
        "EdGraph",
        "EdGraphNode",
        "K2Node",
        "K2Node_CallFunction",
        "K2Node_CallMemberFunction",
        "K2Node_InputAxis",
        "K2Node_InputAction",
        "K2Node_InputActionEvent",
        "K2Node_EnhancedInputActionEvent",
        "K2Node_VariableSet",
        "K2Node_Event",
        "Blueprint",
        "BlueprintGeneratedClass",
        "InputAction",
        "InputAction_Factory",
        "InputMappingContext",
        "InputMappingContext_Factory",
        "EnhancedPlayerInput",
        "EnhancedInputComponent",
        "EnhancedInputLocalPlayerSubsystem",
        "EnhancedInputDeveloperSettings",
        "AssetToolsHelpers",
        "EditorAssetLibrary",
        "InputSettings",
        "PlayerController",
        "PlayerInput",
        "GameModeBase",
        "Character",
        "Pawn",
        "DefaultPawn",
        "PlayerStart",
        "WorldSettings",
        "AutomationLibrary",
        "EditorLevelLibrary",
        "EditorActorSubsystem",
        "GameplayStatics",
        "KismetSystemLibrary",
    ]
}
R["q1_blueprint_editor_library"] = members("BlueprintEditorLibrary")
R["q1_edgraph"] = members("EdGraph")
R["q1_edgraphnode"] = members("EdGraphNode")
R["q1_blueprint"] = members("Blueprint")
R["q1_k2node_callfunction"] = members("K2Node_CallFunction")
R["q1_editor_asset_library"] = members("EditorAssetLibrary")
R["q1_asset_tools"] = members("AssetToolsHelpers")
R["q1_input_settings"] = members("InputSettings")
R["q1_player_controller"] = members("PlayerController")
R["q1_player_input"] = members("PlayerInput")
R["q1_gamemodebase"] = members("GameModeBase")
R["q1_enhanced_developer_settings"] = members("EnhancedInputDeveloperSettings")

# ------------------------------------------------------- Q2: class defaults
R["q2"] = {}
try:
    bel = unreal.BlueprintEditorLibrary
    gm_path = "/Game/_Probe/BP_ProbeGameMode"
    unreal.EditorAssetLibrary.delete_directory("/Game/_Probe")

    made = bel.create_blueprint_asset_with_parent(
        unreal.GameModeBase, gm_path, unreal.BlueprintFactory()
    )
    R["q2"]["created"] = bool(made)
    R["q2"]["asset_name"] = made.get_name() if made else None

    gen = made.generated_class()
    R["q2"]["generated_class"] = gen.get_name() if gen else None
    cdo = unreal.get_default_object(gen)
    R["q2"]["cdo"] = cdo.get_name() if cdo else None

    # Set DefaultPawnClass / PlayerControllerClass on the CDO.
    pc_class = unreal.PlayerController
    pawn_class = unreal.DefaultPawn
    cdo.set_editor_property("default_pawn_class", pawn_class)
    cdo.set_editor_property("player_controller_class", pc_class)
    R["q2"]["set_ok"] = True

    unreal.EditorAssetLibrary.save_asset(gm_path)
    R["q2"]["saved"] = True

    # Reload from disk and re-read the CDO to prove persistence.
    del made
    reloaded = unreal.EditorAssetLibrary.load_asset(gm_path)
    R["q2"]["reloaded"] = bool(reloaded)
    re_cdo = unreal.get_default_object(reloaded.generated_class())
    R["q2"]["reloaded_default_pawn"] = (
        re_cdo.get_editor_property("default_pawn_class").get_name()
        if re_cdo.get_editor_property("default_pawn_class")
        else None
    )
    R["q2"]["reloaded_player_controller"] = (
        re_cdo.get_editor_property("player_controller_class").get_name()
        if re_cdo.get_editor_property("player_controller_class")
        else None
    )
except Exception:
    R["q2"]["error"] = traceback.format_exc()

# --------------------------------------------------- Q3: graph node authoring
R["q3"] = {}
try:
    bel = unreal.BlueprintEditorLibrary
    pawn_path = "/Game/_Probe/BP_ProbePawn"
    bp = bel.create_blueprint_asset_with_parent(
        unreal.Character, pawn_path, unreal.BlueprintFactory()
    )
    R["q3"]["created"] = bool(bp)
    eg = bel.find_event_graph(bp)
    R["q3"]["event_graph"] = eg.get_name() if eg else None
    R["q3"]["event_graph_class"] = eg.get_class().get_name() if eg else None

    if eg:
        R["q3"]["event_graph_members"] = sorted(
            [n for n in dir(eg) if not n.startswith("_")]
        )
        R["q3"]["event_graph_properties"] = sorted(
            [n for n in dir(eg.get_class()) if not n.startswith("_")]
        )
        # Can we instantiate a node and place it in the graph?
        node = unreal.new_object(unreal.K2Node_CallFunction, outer=eg)
        R["q3"]["node_created"] = node is not None
        if node:
            R["q3"]["node_class"] = node.get_class().get_name()
            R["q3"]["node_members"] = sorted(
                [n for n in dir(node) if not n.startswith("_")]
            )
            # try to add it to the graph
            added = False
            for attempt in ("add_node", "add_node_to_graph", "nodes"):
                if hasattr(eg, attempt):
                    try:
                        if attempt == "nodes":
                            nodes = eg.get_editor_property("nodes")
                            nodes.append(node)
                            eg.set_editor_property("nodes", nodes)
                        else:
                            getattr(eg, attempt)(node)
                        added = True
                        R["q3"]["add_method"] = attempt
                        break
                    except Exception as exc:
                        R["q3"].setdefault("add_attempts", []).append(
                            "%s: %s" % (attempt, exc)
                        )
            R["q3"]["node_added"] = added
    bel.compile_blueprint(bp)
    R["q3"]["compiled"] = str(bp.get_class())
except Exception:
    R["q3"]["error"] = traceback.format_exc()

# --------------------------------------------------------------- cleanup
try:
    unreal.EditorAssetLibrary.delete_directory("/Game/_Probe")
    R["cleanup"] = "ok"
except Exception:
    R["cleanup"] = traceback.format_exc()

try:
    os.makedirs(SCRATCH, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(R, fh, indent=1, default=str)
    log("BPPROBE wrote %s" % OUT)
except Exception:
    log("BPPROBE write failed: %s" % traceback.format_exc())

log(
    "BPPROBE summary q1_present=%s q2_saved=%s q3_node_added=%s"
    % (
        sum(1 for v in R["q1_present"].values() if v),
        R.get("q2", {}).get("saved"),
        R.get("q3", {}).get("node_added"),
    )
)
