#!/usr/bin/env python3
"""
Fetch + verify the three vendored temporal-upscaler plugin bundles for
The Commander (Unreal Engine 5.8, Win64).

The plugin trees are NOT committed to git (multi-GB binaries). This script is
the reproducible source of truth: a fresh clone plus one run of this script
restores the exact working plugin set.

    python Tools/ue/fetch_upscaler_plugins.py            # fetch + verify + install
    python Tools/ue/fetch_upscaler_plugins.py --verify   # verify what is installed
    python Tools/ue/fetch_upscaler_plugins.py --clean    # remove installed trees

WHAT GETS INSTALLED (into <repo>/Plugins/):

  FSR   <- AMD FSR 4.1.1 Unreal bundle, tree FSR-580 (the Unreal 5.8 tree).
           One tree, THREE upscaler providers live inside the shipped
           amd_fidelityfx_upscaler_dx12.dll: ffxProvider_FSR4 (4.1.1),
           ffxProvider_FSR3Upscale (3.1.5) and ffxProvider_FSR2 (2.3.4).
           The FidelityFX loader picks the provider the running hardware
           actually supports, so the RDNA 2 Deck gets FSR 3.1.5 and never
           FSR 4.1.1 (which needs Shader Model 6.6 / RDNA 3+).
  DLSS  <- NVIDIA DLSS 4.5 plugin bundle for Unreal 5.8 (Plugins/ subtree).
  XeSS  <- Intel XeSS 3.2.0 plugin for Unreal 5.8 (root of the archive).

SHA-256 OF EVERY ARCHIVE IS PINNED BELOW. A hash mismatch aborts the install:
these bundles are replaced upstream from time to time, and an unpinned
download would silently change what ships.
"""

import argparse
import hashlib
import os
import shutil
import sys
import tempfile
import urllib.request
import zipfile

# --------------------------------------------------------------------------
# Pinned sources. Never loosen these to a "latest" URL.
# --------------------------------------------------------------------------
ARCHIVES = [
    {
        "name": "AMD FSR 4.1.1 (Unreal bundle, FSR-580 = UE 5.8 tree)",
        "filename": "UE-FSR-4_1_1.zip",
        "url": "https://gpuopen.com/download/UE-FSR-4_1_1.zip",
        "sha256": "9ce745e25c4b86bbc0974258045690c9c80d4e524cd48359e20005528ee722c5",
        "size": 2007843138,
        # 4.1.1 is the NEWEST REDISTRIBUTABLE AMD FSR artifact (verified
        # 2026-10-22 by full download + sha256sum of the live file).
        # FSR 4.1.2 is DRIVER-SIDE ONLY: it shipped 2026-10-20 inside
        # AMD Software: Adrenalin Edition 26.10.1 as an in-driver upscaler
        # and has NO redistributable package -- GPUOpen's plugin download
        # redirect (https://gpuopen.com/download-ue-fsr-plugin/) still
        # resolves to UE-FSR-4_1_1.zip, /download/UE-FSR-4_1_2.zip returns
        # HTTP 404, and FidelityFX-SDK has no v2.4.0 tag or pre-release
        # (latest release is v2.3.0, 2026-06-24).
        # RDNA 3.5 APU support for FSR 4.1 is UNDECIDED by AMD.
        # FSR 4.1 Vulkan support is NOT shipped; it awaits FSR SDK 2.4
        # (unreleased).
        "note": (
            "4.1.1 = newest redistributable FSR artifact. 4.1.2 (Adrenalin "
            "26.10.1, 2026-10-20) is driver-side only, no redistributable "
            "build exists; RDNA 3.5 APU support undecided by AMD; Vulkan "
            "FSR 4.1 awaits unreleased SDK 2.4."
        ),
        # source prefix -> destination folder under Plugins/
        "map": [
            ("UE-FSR-4_1_1/FSR-580/FSR/", "FSR/"),
        ],
    },
    {
        "name": "NVIDIA DLSS 4.5 (Unreal 5.8 plugin bundle)",
        "filename": "2026.10.16_ue5.8_dlss4.5plugin_v8.9.0.zip",
        "url": (
            "https://developer.nvidia.com/downloads/assets/gameworks/downloads/secure/dlss/"
            "ue-dlss-5.8/8.9.0/2026.10.16_ue5.8_dlss4.5plugin_v8.9.0.zip"
        ),
        "sha256": "adeeb59b9635794e05252438bf01307bf8a629769e8f0517237363f690bb380c",
        "size": 1166608575,
        "map": [
            ("Plugins/DLSS/", "DLSS/"),
            ("Plugins/DLSSMoviePipelineSupport/", "DLSSMoviePipelineSupport/"),
            ("Plugins/NIS/", "NIS/"),
            ("Plugins/StreamlineCore/", "StreamlineCore/"),
            ("Plugins/StreamlineDLSSG/", "StreamlineDLSSG/"),
            ("Plugins/StreamlineNGXCommon/", "StreamlineNGXCommon/"),
            ("Plugins/StreamlineReflex/", "StreamlineReflex/"),
        ],
    },
    {
        "name": "Intel XeSS 3.2.0 (Unreal 5.8 plugin)",
        "filename": "XeSS_UE5.8_Plugin_v3.2.0.zip",
        "url": (
            "https://github.com/GameTechDev/XeSSUnrealPlugin/releases/download/"
            "v3.2.0/XeSS_UE5.8_Plugin_v3.2.0.zip"
        ),
        "sha256": "f0bb482102f245b452a13f9e899708f0af86710667eb180cac4eb6d007bd80af",
        "size": 251334143,
        "map": [
            ("", "XeSS/"),
        ],
    },
]

CHUNK = 1024 * 1024


def repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))


def plugins_dir():
    return os.path.join(repo_root(), "Plugins")


def cache_dir():
    # Outside the repo so the multi-GB payloads never touch the git index.
    base = os.environ.get("UPSCALER_CACHE") or os.path.join(
        tempfile.gettempdir(), "upscalers"
    )
    os.makedirs(base, exist_ok=True)
    return base


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def download(url, dest):
    print("  downloading %s" % url)
    tmp = dest + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        got = 0
        while True:
            block = resp.read(CHUNK)
            if not block:
                break
            out.write(block)
            got += len(block)
            if total:
                pct = 100.0 * got / total
                print("    %6.1f%%  %d / %d bytes" % (pct, got, total), end="\r")
    if total:
        print()
    os.replace(tmp, dest)


def fetch_archive(spec, cache):
    path = os.path.join(cache, spec["filename"])
    if os.path.exists(path) and os.path.getsize(path) == spec["size"]:
        print("  cached %s" % spec["filename"])
    else:
        if os.path.exists(path):
            os.remove(path)
        download(spec["url"], path)

    size = os.path.getsize(path)
    if size != spec["size"]:
        raise SystemExit(
            "  SIZE MISMATCH for %s: expected %d, got %d"
            % (spec["filename"], spec["size"], size)
        )
    digest = sha256_file(path)
    if digest != spec["sha256"]:
        raise SystemExit(
            "  SHA-256 MISMATCH for %s\n  expected %s\n  actual   %s"
            % (spec["filename"], spec["sha256"], digest)
        )
    print("  verified %s  sha256=%s  %d bytes" % (spec["filename"], digest, size))
    return path


def extract(zip_path, spec, dest_root):
    """Copy the pinned subtrees out of the archive into Plugins/."""
    zf = zipfile.ZipFile(zip_path)
    names = zf.namelist()
    for src_prefix, dst_prefix in spec["map"]:
        if src_prefix:
            members = [n for n in names if n.startswith(src_prefix)]
        else:
            # whole archive root
            members = [
                n for n in names if not n.startswith("/") and n.count("/") >= 0
            ]
        if not members:
            raise SystemExit(
                "  archive %s has no entries under %r"
                % (spec["filename"], src_prefix or "<root>")
            )
        count = 0
        for name in members:
            if name.endswith("/"):
                continue
            rel = name[len(src_prefix):] if src_prefix else name
            if not rel:
                continue
            out_path = os.path.join(dest_root, dst_prefix, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with zf.open(name) as src, open(out_path, "wb") as dst:
                shutil.copyfileobj(src, dst, CHUNK)
            count += 1
        print("  installed %-26s %d files" % (dst_prefix, count))
    zf.close()


def verify_installed():
    """Check that every expected plugin is present with its descriptor."""
    root = plugins_dir()
    expected = {
        "FSR/FSR.uplugin": "4.1.1",
        "DLSS/DLSS.uplugin": None,
        "XeSS/XeSS.uplugin": "3.2.0",
    }
    ok = True
    for rel in sorted(expected):
        path = os.path.join(root, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("  MISSING  %s" % rel)
            ok = False
            continue
        print("  present  %s" % rel)
    # The FSR runtime DLL must carry all three providers.
    dll = os.path.join(
        root, "FSR", "Source", "fidelityfx-sdk", "Kits", "FidelityFX",
        "signedbin", "amd_fidelityfx_upscaler_dx12.dll",
    )
    if os.path.exists(dll):
        data = open(dll, "rb").read()
        for provider in (b"ffxProvider_FSR4", b"ffxProvider_FSR3Upscale", b"ffxProvider_FSR2"):
            if provider not in data:
                print("  FSR runtime DLL is missing provider %s" % provider.decode())
                ok = False
        print("  FSR runtime DLL carries FSR4 + FSR3Upscale + FSR2 providers")
    else:
        print("  MISSING  FSR signedbin/amd_fidelityfx_upscaler_dx12.dll")
        ok = False
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify", action="store_true", help="only verify what is installed")
    ap.add_argument("--clean", action="store_true", help="remove the installed plugin trees")
    args = ap.parse_args()

    if args.clean:
        for folder in ("FSR", "DLSS", "XeSS", "NIS", "StreamlineCore",
                       "StreamlineDLSSG", "StreamlineNGXCommon", "StreamlineReflex",
                       "DLSSMoviePipelineSupport"):
            path = os.path.join(plugins_dir(), folder)
            if os.path.isdir(path):
                print("removing Plugins/%s" % folder)
                shutil.rmtree(path)
        return 0

    if args.verify:
        print("verifying installed plugin set in %s" % plugins_dir())
        return 0 if verify_installed() else 1

    print("plugin destination: %s" % plugins_dir())
    print("archive cache     : %s" % cache_dir())
    cache = cache_dir()
    for spec in ARCHIVES:
        print("\n== %s" % spec["name"])
        zip_path = fetch_archive(spec, cache)
        extract(zip_path, spec, plugins_dir())

    print("\n== verifying installed plugin set")
    if not verify_installed():
        raise SystemExit("verification failed")
    print("\nOK: all three upscaler plugin trees installed and verified.")
    print("Next: enable the plugins in TheCommander.uproject and set the")
    print("per-node profile. See Docs/generated/PERFORMANCE_UPSCALER_PROFILE.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
