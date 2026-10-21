#!/usr/bin/env python3
"""
Launch UnrealEditor-Cmd.exe for this project, capture the log, and VERIFY it.

Runs through Python's subprocess with an ARGUMENT LIST on purpose: MSYS/Git
Bash mangles Windows paths passed to native executables, so the editor is
always launched from Python, never from the shell.

The run is only reported as a pass when verify_upscaler_run.py confirms the
evidence is actually in the log. A run whose dump never executed is a
FAILURE, not a silent success.

Usage:
    python Tools/ue/run_editor.py --benchmark 8          # -game benchmark, D3D12
    python Tools/ue/run_editor.py --benchmark 8 --vulkan
    python Tools/ue/run_editor.py --commandlet ResavePackages
    python Tools/ue/run_editor.py --benchmark 8 --device-profile CommanderDeckRDNA2
    python Tools/ue/run_editor.py --benchmark 8 --device-profile CommanderDeckRDNA2 \
        --expect-provider 3.1.5 --expect-screen-percentage 50 \
        --expect-request-provider 3 --expect-shadow-resolution 512

    --expect-* options are extracted from argv BEFORE argparse runs, so they
    work in any position (including after --extra). --extra must still be
    the last option if used.
"""

import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
# The project root is the parent of Tools/ue/ - derived from this file so
# the launcher keeps working if the tree is moved or checked out elsewhere.
PROJECT = os.path.dirname(os.path.dirname(HERE))
UPROJECT = os.path.join(PROJECT, "TheCommander.uproject")
EDITOR = r"D:\Unreal_Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
LOG_DIR = os.path.join(PROJECT, "Saved", "Logs")
# The engine's own Entry map: renders a real frame without touching any
# project content, so no project .umap is ever opened or written.
ENTRY_MAP = "/Engine/Maps/Entry"


def editor_running():
    out = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"],
        capture_output=True, text=True, errors="replace",
    ).stdout
    return [ln for ln in out.splitlines() if "UnrealEditor" in ln]


def main():
    # ---- pre-pass: pull the --expect-* options out of argv -------------
    # argparse.REMAINDER (used by --extra) swallows every token that
    # follows it, including --expect-provider. That silently turned the
    # expectation into an unknown engine argument and left the verifier
    # running on its permissive default, i.e. a check that looked present
    # but asserted nothing. Extract the expectations FIRST, wherever they
    # appear on the command line, then let argparse see what is left.
    argv = sys.argv[1:]
    expect = {"--expect-provider": "any",
              "--expect-screen-percentage": None,
              "--expect-request-provider": None,
              "--expect-shadow-resolution": None}
    cleaned = []
    i = 0
    while i < len(argv):
        tok = argv[i]
        matched = False
        for opt in expect:
            if tok == opt:
                if i + 1 >= len(argv):
                    raise SystemExit("%s needs a value" % opt)
                expect[opt] = argv[i + 1]
                i += 2
                matched = True
                break
            if tok.startswith(opt + "="):
                expect[opt] = tok[len(opt) + 1:]
                i += 1
                matched = True
                break
        if not matched:
            cleaned.append(tok)
            i += 1
    argv = cleaned

    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", type=int, default=0,
                    help="run a -game benchmark for N seconds and exit")
    ap.add_argument("--commandlet", default="",
                    help="run a commandlet instead of a game")
    ap.add_argument("--vulkan", action="store_true", help="use Vulkan, not D3D12")
    ap.add_argument("--map", default=None,
                    help="map to load (must be the first token after the "
                         "project file); defaults to the engine's Entry map")
    ap.add_argument("--device-profile", default=None,
                    help="device profile to launch with, e.g. CommanderDeckRDNA2 "
                         "(equivalent to -DP=<name>)")
    ap.add_argument("--extra", nargs=argparse.REMAINDER, default=[],
                    help="extra engine args passed straight through; MUST be the "
                         "last option on the command line")
    args = ap.parse_args(argv)
    expect_provider = expect["--expect-provider"]
    expect_screen_percentage = expect["--expect-screen-percentage"]
    expect_request_provider = expect["--expect-request-provider"]
    expect_shadow_resolution = expect["--expect-shadow-resolution"]

    running = editor_running()
    if running:
        print("REFUSING: an Unreal editor is already running:")
        for ln in running:
            print("   ", ln)
        return 2

    os.makedirs(LOG_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(LOG_DIR, "upscaler-verify-%s.log" % stamp)

    cmd = [EDITOR, UPROJECT]

    if args.commandlet:
        cmd += ["-run=%s" % args.commandlet]
    else:
        # The map argument must be the FIRST token after the project and must
        # not start with '-', otherwise the engine falls back to
        # GameDefaultMap (UnrealEngine.cpp:14047-14053). That is why an
        # earlier run loaded the engine's OpenWorld template instead of the
        # map that was asked for.
        cmd += [args.map or ENTRY_MAP, "-game", "-benchmark", "-fps=60",
                "-seconds=%d" % max(1, args.benchmark), "-ResX=1280",
                "-ResY=720", "-unattended", "-nosplash", "-NoSound",
                "-log", "-stdout", "-FullStdOutLogOutput"]
        cmd += ["-vulkan"] if args.vulkan else ["-d3d12"]
        # NOTE 1: -ExecCmds splits on COMMAS (ParseExecCommands.cpp:28), not
        # semicolons - a semicolon makes the whole string one bad command.
        # NOTE 2: -logcmds needs a value CONTAINING SPACES (the category and
        # the verbosity are separate words). FParse::Value stops an unquoted
        # value at whitespace (Parse.cpp:299), so the value has to reach the
        # engine as ONE quoted token. Passing "-logcmds" and its value as
        # two separate argv entries leaves the value unquoted, the engine then
        # tries to resolve the leftover text as a package name ("Can't Find
        # URL") and the verbosity never applies. Keeping "-logcmds=..." in a
        # single argv element is what makes the quotes survive.
        cmd += ["-logcmds=LogFSR VeryVerbose,LogRHI Verbose,"
                "LogConsoleManager Log,LogDeviceProfileManager Log"]
        # Engine-native proof dump: DumpCVars prints each variable, its value
        # and the priority it was last set by. Deferred to the first tick,
        # after the renderer is up and the upscaler has claimed its slot.
        cmd += ["-ExecCmds=DumpCVars r.FidelityFX,"
                "DumpCVars r.ScreenPercentage,"
                "DumpCVars r.AntiAliasingMethod,"
                "DumpCVars r.TemporalAA.Upscaler,"
                "DumpCVars r.BloomQuality,"
                "DumpCVars r.Shadow.MaxCSMResolution"]

    cmd += [a for a in args.extra if a != "--"]
    if args.device_profile:
        cmd += ["-DP=%s" % args.device_profile]

    print("LAUNCH: %s" % " ".join(cmd))
    print("LOG  : %s" % log_path)
    with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
        proc = subprocess.Popen(cmd, cwd=PROJECT, stdout=fh,
                                stderr=subprocess.STDOUT)
        code = proc.wait()
    print("EXIT  : %s" % code)
    print("LOG   : %s" % log_path)

    # ---- the gate: the run only passes if the evidence is in the log ----
    # A run whose cvar dump never executed, or whose provider line is
    # missing, is a FAILURE - not a silent success.
    verify = [sys.executable, os.path.join(HERE, "verify_upscaler_run.py"),
              log_path, "--expect-provider", expect_provider]
    if expect_screen_percentage is not None:
        verify += ["--expect-screen-percentage", expect_screen_percentage]
    if expect_request_provider is not None:
        verify += ["--expect-request-provider", expect_request_provider]
    if expect_shadow_resolution is not None:
        verify += ["--expect-shadow-resolution", expect_shadow_resolution]
    print("")
    rc = subprocess.call(verify)
    if rc != 0:
        print("")
        print("RUN VERIFICATION FAILED - see %s" % log_path)
        return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
