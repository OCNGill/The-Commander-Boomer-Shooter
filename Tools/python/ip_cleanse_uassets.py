# UE 5.8 commandlet Python — IP-cleanse D1.2b: rename Content/Enemies/BESTIARY + Tests/UEParity assets
# off XCOM_* names to BESTIARY_* (bestiary vocabulary), reference-aware.
# Run: UnrealEditor-Cmd.exe <proj> -run=pythonscript -script=Tools/python/ip_cleanse_uassets.py -unattended -nullrhi
#       -ScriptArg=dry   (list plan + referrers only, default)
#       -ScriptArg=do    (actor-label sweep -> asset rename -> map save -> dependency check)
import sys

import unreal

TOKENS = {
    "XCOM_Sectoid": "BESTIARY_Graytide",
    "XCOM_Viper": "BESTIARY_Ratline",
    "XCOM_Floater": "BESTIARY_Drifter",
    "XCOM_Muton": "BESTIARY_Bulwark",
    "XCOM_Chryssalid": "BESTIARY_Harrower",
}
MAPS = (r"/Game/Maps/M_Blockout01", r"/Game/Tests/M_Proof_Blockout")

arg = None
for a in sys.argv:
    if a.startswith("-ScriptArg="):
        arg = a.split("=", 1)[1]
do = arg == "do"
unreal.log("=== IP_CLEANSE_D1.2b mode=%s ===" % ("DO" if do else "DRY"))

eal = unreal.EditorAssetLibrary
registry = unreal.AssetRegistryHelpers.get_asset_registry()

# 1) discover every asset under the two trees that carries a token in its name
targets = []
for root in (r"/Game/Enemies/BESTIARY", r"/Game/Tests/UEParity"):
    if not eal.does_directory_exist(root):
        unreal.log("MISSING DIR %s" % root)
        continue
    for path in eal.list_assets(root, recursive=True):
        base = path.split("/")[-1]
        for tok, new in TOKENS.items():
            if base.startswith(tok):
                newpath = path[: -len(base)] + new + base[len(tok):]
                targets.append((path, newpath))
                break

unreal.log("TARGET COUNT: %d" % len(targets))

# 2) actor-label sweep (DO only, BEFORE renames so map refs are still intact)
if do:
    ell = unreal.EditorLevelLibrary
    for mappath in MAPS:
        try:
            ell.load_level(mappath)
        except Exception as e:
            unreal.log("MAP LOAD FAIL %s: %s" % (mappath, e))
            continue
        renamed_actors = 0
        for actor in ell.get_all_level_actors():
            label = actor.get_actor_label()
            for tok, new in TOKENS.items():
                if tok in label:
                    actor.set_actor_label(label.replace(tok, new))
                    renamed_actors += 1
                    break
        unreal.log("MAP %s actor-label renames: %d" % (mappath, renamed_actors))
        ell.save_current_level()

# 3) referrer discovery + rename (UE 5.8: get_referencers(asset, reference_options) — reference_options is REQUIRED positional)
failed = 0
ref_opts_enum = getattr(unreal, "ReferenceOptions", None)
ref_arg = ref_opts_enum.include_unreachable if ref_opts_enum is not None else None
for old, new in targets:
    if do:
        try:
            refs = registry.get_referencers(old, ref_arg) if ref_arg is not None else registry.get_referencers(old)
        except TypeError:
            # no enum available — skip ref count, rename anyway
            refs = []
        if not refs:
            unreal.log("REFS UNKNOWN for %s (enum missing) — renaming anyway" % old)
        if eal.rename_asset(old, new):
            unreal.log("RENAMED %s -> %s (refs=%d)" % (old, new, len(refs)))
            failed += 1
        else:
            unreal.log("RENAME FAILED: %s" % old)
            failed += 2
    else:
        unreal.log("DRY %s -> %s  (refs unknown: enum missing)" % (old, new))

if do:
    # 4) dependency integrity check (best-effort)
    broken = 0
    try:
        for a in registry.get_all_assets():
            try:
                deps = registry.get_dependencies(a.package_name)
            except Exception:
                continue
            for o in deps:
                if not o.asset_name:
                    broken += 1
                    if broken <= 10:
                        unreal.log("  BROKEN? %s -> %s" % (a.package_name, str(o)))
    except Exception as e:
        unreal.log("DEP CHECK SKIPPED: %s" % e)
    unreal.log("DEPENDENCY CHECK: %d suspicious refs" % broken)
    eal.save_dirty_packages(include_unloaded=True)
    unreal.log("SAVED. IP_CLEANSE_D1.2b DONE failed_renames=%d" % failed)
else:
    unreal.log("DRY RUN COMPLETE — re-run with -ScriptArg=do to execute")
