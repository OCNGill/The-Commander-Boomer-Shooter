"""Launch a UE 5.8 Python commandlet script safely.

  python Tools/python/ue_launch.py <script.py> [logname]

Rules enforced:
  - exactly ONE UnrealEditor-Cmd at a time (tasklist guard + wait/retry)
  - subprocess.run() with a LIST of args (never cmd /c, never shell=True)
  - -AllowCommandletRendering is ALWAYS passed so the RHI is real, not Null
  - success is judged by log markers + output artifacts, NOT by exit code
"""

import os
import subprocess
import sys
import time

UE = os.environ.get('UE_EDITOR', r'D:\Unreal_Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe')
REPO = os.environ.get('UE_REPO', r'C:\Users\Gillsystems Laptop\source\repos\OCNGill\The_Commander_Boomer_Shooter')
PROJECT = os.path.join(REPO, 'TheCommander.uproject')
# Optional project-descriptor override. The main descriptor can be in a state
# where its declared C++ modules are not compiled, which aborts the editor at
# project load ("The game module '...' could not be found"). Point this at a
# module-free descriptor sharing the same Content/ to run pure content scripts.
PROJECT_OVERRIDE = os.environ.get('UE_PROJECT_OVERRIDE', '')
if PROJECT_OVERRIDE:
    PROJECT = os.path.abspath(PROJECT_OVERRIDE)


def running_instances():
    try:
        out = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq UnrealEditor-Cmd.exe', '/NH'],
            capture_output=True, text=True, timeout=60).stdout
    except Exception as e:
        print('tasklist failed: %r' % (e,))
        return 0
    n = 0
    for line in out.splitlines():
        if 'UnrealEditor-Cmd.exe' in line and 'No tasks' not in line:
            n += 1
    return n


def wait_for_idle(max_wait=1800):
    waited = 0
    while running_instances() > 0:
        if waited == 0:
            print('[launch] an UnrealEditor-Cmd is already running - waiting...')
        time.sleep(15)
        waited += 15
        if waited >= max_wait:
            print('[launch] giving up waiting for the editor to free up')
            return False
    if waited:
        print('[launch] editor free after %ds' % waited)
    return True


def main():
    if len(sys.argv) < 2:
        print('usage: ue_launch.py <script.py> [logname] [--no-render]')
        return 2
    script = os.path.abspath(sys.argv[1])
    # UE's PythonScriptCommandlet parses -Script= with FParse::QuotedString,
    # which interprets backslash escape sequences -- "\r" in "source\repos"
    # is eaten as a carriage return and the path is mangled. Forward slashes
    # are not escape sequences, so the path survives intact.
    script_arg = script.replace('\\', '/')
    argv = sys.argv[2:]
    no_render = '--no-render' in argv
    # --render: real RHI for capture/export, but the upscaler plugins are
    # still disabled - their global shaders (FNISUpscaleCS et al) cost 10+
    # minutes each on a cold DDC and are not used by a render-target capture.
    do_render = '--render' in argv
    argv = [a for a in argv if not a.startswith('--')]
    logname = argv[0] if argv else 'ue_run'
    if not os.path.isfile(script):
        print('missing script: %s' % script)
        return 2
    if not wait_for_idle():
        return 3

    logdir = os.path.join(REPO, 'Saved', 'Logs')
    if not os.path.isdir(logdir):
        os.makedirs(logdir)
    logabs = os.path.join(logdir, logname + '.log')

    # A commandlet (-run=pythonscript) has NO render loop, so
    # SceneCapture2D::CaptureScene never produces a frame: the render
    # target comes back all-zero and every shot is rejected as
    # "BAD CAPTURE".  The editor runs a real render loop, so the
    # scene capture works there.
    editor_mode = '--editor' in argv or do_render
    args = [
        UE,
        PROJECT,
        '-unattended',
        '-nosplash',
        '-NoSound',
        '-stdout',
        '-FullStdOutLogOutput',
        '-abslog=' + logabs,
    ]
    if editor_mode:
        # -ExecutePythonScript RUNS the script and then exits the editor, so
        # a tick-driven script never gets the frames it needs.  -ExecCmds
        # runs the same code but leaves the editor alive, so the slate
        # post-tick callback keeps firing until the script quits it.
        # FORWARD SLASHES ONLY.  A Windows backslash in the embedded
        # Python source is read as an escape sequence, and 'F:\Gillsystems'
        # becomes a truncated \uXXXX unicode escape -> SyntaxError before
        # the script ever runs.
        script_abs = os.path.abspath(script_arg).replace('\\', '/')
        args.append("-ExecCmds=py exec(open(r'%s').read())" % script_abs)
        # Over SSH there is no interactive desktop session, so the editor
        # cannot create a D3D12 swapchain (DXGI_ERROR_NOT_CURRENTLY_AVAILABLE
        # in WindowsD3D12Viewport.cpp).  -RenderOffscreen renders without a
        # window, which is what a headless scene capture needs.
        args.append('-RenderOffscreen')
        args.append('-AllowCommandletRendering')
    else:
        args += ['-run=pythonscript', '-script=' + script_arg]
    if no_render:
        # Measurement only: no RHI needed, so no global shader compile.
        # The upscaler plugins are disabled too - their global shaders
        # (FNISUpscaleCS et al) cost 10+ minutes each on a cold DDC.
        print('[launch] MEASURE-ONLY mode (no -AllowCommandletRendering)')
        args.append('-nullrhi')
        args.append('-DisablePlugins=FSR,NIS,DLSS,XeSS,StreamlineCore,'
                    'StreamlineDLSSG,StreamlineNGXCommon,StreamlineReflex')
    else:
        args.append('-AllowCommandletRendering')
        if do_render:
            # Real RHI for scene capture, but no upscaler global shaders.
            print('[launch] RENDER mode (real RHI, upscalers disabled)')
            args.append('-DisablePlugins=FSR,NIS,DLSS,XeSS,StreamlineCore,'
                        'StreamlineDLSSG,StreamlineNGXCommon,StreamlineReflex')
    print('[launch] ' + ' '.join(args))
    env = dict(os.environ)
    if no_render:
        env['UEPARITY_MEASURE_ONLY'] = '1'
    t0 = time.time()
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=1800,
                              env=env)
        rc = proc.returncode
        so = proc.stdout or ''
        se = proc.stderr or ''
    except subprocess.TimeoutExpired as e:
        rc = -999
        so = (e.stdout or '') if isinstance(e.stdout, str) else ''
        se = 'TIMEOUT after 1800s'
    dt = time.time() - t0

    print('[launch] exit=%s elapsed=%.1fs' % (rc, dt))
    if so:
        print('--- stdout (tail 12000) ---')
        print(so[-12000:])
    if se:
        print('--- stderr (tail 4000) ---')
        print(se[-4000:])
    print('[launch] log: %s' % logabs)
    return 0


if __name__ == '__main__':
    sys.exit(main())
