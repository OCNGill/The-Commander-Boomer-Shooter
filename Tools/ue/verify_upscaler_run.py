#!/usr/bin/env python3
"""
Verify an upscaler run log. HARD FAILS when the evidence is missing or wrong.

WHY THIS EXISTS
---------------
A cvar dump CANNOT show which FSR provider actually engaged. The provider
version lives only in the plugin's own initialization line:

    LogFSR: Successfully initialized FSR Upscaling provider using version '3.1.5'

A verification that only checked cvars would have passed while the Deck ran
FSR 2 the whole time. So the provider version is asserted from the
initialization line, and the cvar dump is asserted to be PRESENT at all --
a run whose dump never executed is a failure, not a pass.

Usage:
    python Tools/ue/verify_upscaler_run.py <logfile> --expect-provider 3.1.5
    python Tools/ue/verify_upscaler_run.py <logfile> --expect-provider any
"""

import argparse
import re
import sys

# The line that names the ACTIVE upscaler method (AMD's own plugin, LogFSR).
PROVIDER_RE = re.compile(
    r"Successfully initialized FSR Upscaling provider using version '([^']+)'")
FORCED_RE = re.compile(
    r"Forcing FSR Upscaling to version '([^']+)' because of "
    r"r\.FidelityFX\.FSR\.RequestProvider=(\d+)")
# The FFX SDK's own frame-time sanity warning.
FRAMETIME_RE = re.compile(r"frameTimeDelta is less than")
# FSR's own "I disabled myself" path.
DISABLED_RE = re.compile(r"Disable FSR as it could not be initialised")
NO_LEGAL_RE = re.compile(r"Could not find a legal FSR Upscaling provider")

# cvars the run must have dumped, and the value each must show.
REQUIRED_CVARS = [
    "r.FidelityFX.FSR.Enabled",
    "r.FidelityFX.FSR.RequestProvider",
    "r.FidelityFX.FSR.QualityMode",
    "r.ScreenPercentage",
    "r.AntiAliasingMethod",
    "r.TemporalAA.Upscaler",
    "r.BloomQuality",
]
CVAR_RE = re.compile(r'(\S+)\s*=\s*"([^"]*)"\s+LastSetBy:\s*(\S+)')
# The engine's log prefix is "[2026.10.21-14.36.24:107][  0]" - one or more
# bracketed groups before the message.
LOG_PREFIX_RE = re.compile(r'^(?:\s*\[[^\]]*\])+\s*')


def parse_cvar_dump(lines):
    """Map cvar name -> (value, last-set-by) from the engine's DumpCVars output."""
    dumped = {}
    for line in lines:
        if "LastSetBy:" not in line:
            continue
        body = LOG_PREFIX_RE.sub("", line)
        m = CVAR_RE.match(body)
        if m:
            dumped[m.group(1)] = (m.group(2), m.group(3))
    return dumped


def fail(msg, failures):
    failures.append(msg)
    print("  FAIL  %s" % msg)


def ok(msg):
    print("  ok    %s" % msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logfile")
    ap.add_argument("--expect-provider", default="any",
                    help="expected FSR provider version, e.g. 3.1.5, or 'any'")
    ap.add_argument("--expect-screen-percentage", default=None,
                    help="expected r.ScreenPercentage value")
    ap.add_argument("--expect-request-provider", default=None,
                    help="expected r.FidelityFX.FSR.RequestProvider value")
    ap.add_argument("--expect-shadow-resolution", default=None,
                    help="expected r.Shadow.MaxCSMResolution value")
    args = ap.parse_args()

    try:
        text = open(args.logfile, encoding="utf-8", errors="replace").read()
    except OSError as exc:
        print("  FAIL  cannot read log: %s" % exc)
        return 2
    lines = text.splitlines()

    failures = []
    print("Verifying %s" % args.logfile)

    # ---- 1. the cvar dump must have actually executed -------------------
    dumped = parse_cvar_dump(lines)
    missing = [c for c in REQUIRED_CVARS if c not in dumped]
    if missing:
        fail("cvar dump did not execute; missing: %s" % ", ".join(missing), failures)
    else:
        ok("cvar dump present (%d variables)" % len(dumped))

    # ---- 2. the ACTIVE provider must be named -------------------------
    providers = sorted(set(PROVIDER_RE.findall(text)))
    if not providers:
        fail("no 'Successfully initialized FSR Upscaling provider' line in log; "
             "the upscaler never engaged and the run proves nothing", failures)
    else:
        if len(providers) > 1:
            fail("log reports more than one provider version: %s" % providers,
                 failures)
        elif args.expect_provider != "any" and providers[0] != args.expect_provider:
            fail("active FSR provider is '%s', expected '%s'"
                 % (providers[0], args.expect_provider), failures)
        else:
            ok("active FSR provider = %s" % providers[0])

    # ---- 3. the forced selection, if any, must agree -------------------
    forced = FORCED_RE.findall(text)
    if forced:
        version, cvar_value = forced[0]
        if providers and version != providers[0]:
            fail("forced provider '%s' disagrees with active provider '%s'"
                 % (version, providers[0]), failures)
        else:
            ok("forced provider %s via RequestProvider=%s" % (version, cvar_value))
        if args.expect_request_provider is not None:
            if cvar_value != args.expect_request_provider:
                fail("RequestProvider=%s in log, expected %s"
                     % (cvar_value, args.expect_request_provider), failures)
    elif args.expect_request_provider not in (None, "0"):
        fail("expected RequestProvider=%s to be forced, but no forcing line"
             % args.expect_request_provider, failures)

    # ---- 4. expected effective cvar values ----------------------------
    # Compare NUMERICALLY. The engine's DumpCVars prints whatever the
    # variable's current string form is ("50", "66.666667", "512"), so a
    # literal string comparison would fail on formatting alone.
    def num(s):
        try:
            return float(s)
        except (TypeError, ValueError):
            return None

    def check_cvar(name, expected):
        got = dumped.get(name)
        if not got:
            fail("%s not dumped" % name, failures)
            return
        value, last_set_by = got
        want, have = num(expected), num(value)
        if want is not None and have is not None:
            if abs(want - have) > 1e-4:
                fail("%s = %s, expected %s" % (name, value, expected), failures)
            else:
                ok("%s = %s (LastSetBy %s)" % (name, value, last_set_by))
        elif value != expected:
            fail("%s = %s, expected %s" % (name, value, expected), failures)
        else:
            ok("%s = %s (LastSetBy %s)" % (name, value, last_set_by))

    if args.expect_screen_percentage is not None:
        check_cvar("r.ScreenPercentage", args.expect_screen_percentage)
    if args.expect_shadow_resolution is not None:
        check_cvar("r.Shadow.MaxCSMResolution", args.expect_shadow_resolution)

    # ---- 5. report the frame-time unit situation ----------------------
    ft = [l for l in lines if FRAMETIME_RE.search(l)]
    if ft:
        print("  note  %d frameTimeDelta unit warning(s) in log:" % len(ft))
        for l in ft[:3]:
            print("          %s" % l.strip()[:150])
    if DISABLED_RE.search(text):
        fail("FSR disabled itself ('Disable FSR as it could not be initialised')",
             failures)
    if NO_LEGAL_RE.search(text):
        fail("a forced FSR provider was not legal on this GPU", failures)

    print("")
    if failures:
        print("VERIFICATION FAILED (%d problem(s))" % len(failures))
        return 1
    print("VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
