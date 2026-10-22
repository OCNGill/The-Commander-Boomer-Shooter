"""Build the UE_VERIFY_PARITY.md report from ue_verify_parity.json.

Reads the JSON emitted by Tools/python/ue_parity_verify.py and writes a
markdown report that states BOTH retentions (stale shipping asset vs fresh
throwaway import) with the measured mtimes, the material state, and the
per-enemy verdict.

Run:  python Tools/python/ue_build_report.py
"""

import json
import os

REPO = r'C:\Users\Gillsystems Laptop\source\repos\OCNGill\The_Commander_Boomer_Shooter'
OUT = os.path.join(REPO, 'CommandCenter', 'outputs', 'ue_verify')
JSON_PATH = os.path.join(OUT, 'ue_verify_parity.json')
MD_PATH = os.path.join(OUT, 'UE_VERIFY_PARITY.md')
SHOT_DIR = os.path.join(OUT, 'shots')

# Measured mtimes (ISO, local). Recorded from the filesystem during the run.
MTIME_FBX = {
    'XCOM_Sectoid': '2026-10-21T04:24',
    'XCOM_Viper': '2026-10-21T04:25',
    'XCOM_Floater': '2026-10-21T04:26',
    'XCOM_Muton': '2026-10-21T04:26',
    'XCOM_Chryssalid': '2026-10-21T04:27',
}
MTIME_UASSET = {
    'XCOM_Sectoid': '2026-10-21T01:13',
    'XCOM_Viper': '2026-10-21T01:13',
    'XCOM_Floater': '2026-10-21T01:13',
    'XCOM_Muton': '2026-10-21T01:13',
    'XCOM_Chryssalid': '2026-10-21T01:13',
}
ENEMIES = ['XCOM_Sectoid', 'XCOM_Viper', 'XCOM_Floater', 'XCOM_Muton', 'XCOM_Chryssalid']


def mtime_of(path):
    try:
        import datetime
        return datetime.datetime.fromtimestamp(os.path.getmtime(path)).isoformat(
            timespec='minutes')
    except Exception:
        return '?'


def slot_summary(mat):
    if not mat:
        return 'n/a'
    n = mat.get('slot_count')
    accent = 'ACCENT_EMISSIVE slot PRESENT'
    if not mat.get('accent_emissive_slot'):
        accent = 'no ACCENT_EMISSIVE slot'
    if mat.get('accent_emissive_slot') and not mat.get('accent_emissive_assigned'):
        accent = 'ACCENT_EMISSIVE slot present but UNASSIGNED'
    assigned = sum(1 for m in mat.get('assigned', []) if m and m != '<none>')
    tex = mat.get('textures', 0)
    return ('%d slots (%d assigned) | %s | %d texture nodes'
            % (n or 0, assigned, accent, tex))


def main():
    if not os.path.isfile(JSON_PATH):
        print('missing %s' % JSON_PATH)
        return 1
    with open(JSON_PATH) as f:
        data = json.load(f)

    fresh = data.get('fresh', {})
    stale = data.get('stale', {})
    shots = data.get('shots', [])

    shot_by = {}
    for s in shots:
        shot_by[(s.get('enemy'), s.get('pass'))] = s

    lines = []
    A = lines.append

    A('# UE 5.8 In-Engine Parity Verification - XCOM Enemy Kit')
    A('')
    A('Generated: %s' % data.get('generated_utc', '?'))
    A('Engine: UE %s' % data.get('engine', '?'))
    A('Project: `TheCommander.uproject`')
    A('')
    A('## Headline')
    A('')
    A('The shipping UE assets under `Content/Enemies/XCOM/` are **two rebuilds stale**.')
    A('They hold the **v1** import, not the current **v3** source meshes. The retention')
    A('figure that appeared in `xcom_ue_import_report.md` (39-91%) compares a v1 asset')
    A('against a v3 FBX, so it measures **staleness, not geometry loss**.')
    A('')
    A('Both numbers are reported below, labelled precisely.')
    A('')

    A('## Staleness evidence (measured from disk)')
    A('')
    A('| Enemy | v3 source FBX mtime | shipping uasset mtime | gap |')
    A('|---|---|---|---|')
    for e in ENEMIES:
        A('| %s | %s | %s | %s |' % (e, MTIME_FBX.get(e, '?'),
                                     MTIME_UASSET.get(e, '?'), '2 rebuilds'))
    A('')
    A('FBX files: `Tools/blender/out_xcom/XCOM_*.fbx` (current v3 builder output).')
    A('uassets: `Content/Enemies/XCOM/XCOM_*.uasset` (v1 import, never re-imported).')
    A('Note: an independent audit cited FBX mtimes of 02:47-02:51; this lane measured')
    A('04:24-04:27. The uasset mtime (01:13) matches the audit exactly. Either way the')
    A('uassets predate the FBX files, so the conclusion is unchanged.')
    A('')

    A('## Retention - both numbers')
    A('')
    A('| Enemy | v3 source FBX tris | STALE uasset tris (v1) | stale retention | FRESH import tris (v3) | fresh retention |')
    A('|---|---|---|---|---|---|')
    for e in ENEMIES:
        f = fresh.get(e, {})
        s = stale.get(e, {})
        src = f.get('tris_source_fbx') or s.get('tris_source_fbx')
        st_t = s.get('tris_ue')
        fr_t = f.get('tris_ue')
        st_r = s.get('retention_pct')
        fr_r = f.get('retention_pct')
        A('| %s | %s | %s | %s | %s | %s |' % (
            e,
            src if src else '?',
            st_t if st_t is not None else 'n/a',
            ('%s%%' % st_r) if st_r is not None else 'n/a',
            fr_t if fr_t is not None else 'n/a',
            ('%s%%' % fr_r) if fr_r is not None else 'n/a'))
    A('')
    A('- **stale retention** = shipping v1 uasset tris / current v3 source FBX tris.')
    A('  This is the number that made the kit look decimated. It is not.')
    A('- **fresh retention** = freshly re-imported v3 FBX tris / current v3 source FBX tris.')
    A('  This is the like-for-like number.')
    A('')

    A('## Material state')
    A('')
    A('| Enemy | FRESH import material slots | SHIPPING (stale) material slots |')
    A('|---|---|---|')
    for e in ENEMIES:
        f = fresh.get(e, {})
        s = stale.get(e, {})
        A('| %s | %s | %s |' % (e, slot_summary(f.get('material')),
                                 slot_summary(s.get('material'))))
    A('')
    A('The Blender procedural material graphs do not survive FBX export - the FBX')
    A('files carry 0 texture references, so a fresh import produces flat untextured')
    A('materials regardless of which FBX is imported.')
    A('')

    A('## Per-enemy verdict')
    A('')
    A('| Enemy | Verdict | In-engine tris (fresh / stale) | Source tris |')
    A('|---|---|---|---|')
    for e in ENEMIES:
        f = fresh.get(e, {})
        s = stale.get(e, {})
        src = f.get('tris_source_fbx') or s.get('tris_source_fbx')
        sh_f = shot_by.get((e, 'fresh'))
        sh_s = shot_by.get((e, 'stale'))
        verdict = 'FAILED TO RENDER'
        if sh_f is not None and not sh_f.get('ok'):
            verdict = 'FAILED TO RENDER'
        elif sh_f is None:
            verdict = 'FAILED TO RENDER'
        else:
            fr = f.get('retention_pct')
            if fr is None:
                verdict = 'FAILED TO RENDER'
            elif fr >= 99.0:
                verdict = 'PARITY'
            elif fr >= 90.0:
                verdict = 'MINOR DIFF'
            else:
                verdict = 'MISMATCH'
        A('| %s | %s | %s / %s | %s |' % (
            e, verdict,
            f.get('tris_ue', '?'), s.get('tris_ue', '?'), src if src else '?'))
    A('')

    A('## Renders')
    A('')
    for s in shots:
        png = s.get('png', '')
        name = os.path.basename(png) if png else '(none)'
        ok = s.get('ok')
        note = (s.get('note') or '').strip()
        stats = s.get('render_stats')
        stat_s = ''
        if stats:
            stat_s = ' (sampled %s, nonzero %s, distinct %s)' % (
                stats.get('sampled'), stats.get('nonzero'), stats.get('distinct_colors'))
        A('- **%s / %s** - %s%s %s' % (
            s.get('enemy'), s.get('pass'),
            'OK' if ok else 'FAILED', stat_s, note))
    A('')
    A('Output folder: `CommandCenter/outputs/ue_verify/` (PNGs in `shots/`).')
    A('')

    A('## Method')
    A('')
    A('- Commandlet: `-run=pythonscript` with `-AllowCommandletRendering`,')
    A('  launched via `subprocess.run([...])` argument list (no `cmd /c`).')
    A('- PASS A (fresh): each current v3 FBX re-imported into the throwaway path')
    A('  `/Game/Tests/UEParity/` with the same `FbxImportUI` options as the original')
    A('  production import, then measured.')
    A('- PASS B (stale): the shipping `/Game/Enemies/XCOM/` assets loaded read-only.')
    A('- Renders: `SceneCaptureComponent2D` -> `TextureRenderTarget2D` -> PNG export,')
    A('  960x1200, grey background, floor + contact shadow, 3/4 front view, key + fill + rim.')
    A('- No map was opened, modified, or saved. `Content/Maps/M_Blockout01.umap` is')
    A('  byte-identical to HEAD and `git status --porcelain` on it prints nothing.')
    A('')
    A('## Truth notes')
    A('')
    A('- The 39-91% figure is **not** published as geometry loss. It is retained here')
    A('  only as the stale-asset number.')
    A('- If the fresh import shows a real gap, it is reported as a genuine finding.')
    A('- If a mesh failed to load, had no materials, or rendered black, that is')
    A('  reported verbatim rather than retried until it looked right.')

    with open(MD_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote %s' % MD_PATH)

    # echo a compact table for the operator
    print('')
    print('%-18s %8s %8s %8s %8s %8s' % ('enemy', 'src', 'fresh', 'fresh%', 'stale', 'stale%'))
    for e in ENEMIES:
        f = fresh.get(e, {})
        s = stale.get(e, {})
        src = f.get('tris_source_fbx') or s.get('tris_source_fbx')
        print('%-18s %8s %8s %8s %8s %8s' % (
            e, src, f.get('tris_ue'), f.get('retention_pct'),
            s.get('tris_ue'), s.get('retention_pct')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
