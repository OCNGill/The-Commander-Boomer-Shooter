#!/usr/bin/env bash
# Serialized Blender turn on the HTPC. One Blender at a time, node-wide.
# RAM discipline: the HTPC has 11.3GB total / ~5GB free. A second concurrent
# Blender instance will OOM the node and take the fleet's inference with it.
#
# Usage:
#   ./blender_turn_htpc.sh <script.py> [extra blender args...]
#   ./blender_turn_htpc.sh xcom_enemies.py -- --out ~/gillsystems-swarm/out_xcom
#
# Exit codes: 0 = turn completed | 75 = lock busy (skipped, try another task)
set -uo pipefail

LOCK="${GILLSYSTEMS_BLENDER_LOCK:-/home/gillsystems-htpc/.blender.lock}"
BLENDER="${GILLSYSTEMS_BLENDER:-/home/gillsystems-htpc/blender-4.2.23-linux-x64/blender}"
SWARM_DIR="${GILLSYSTEMS_SWARM_DIR:-/home/gillsystems-htpc/gillsystems-swarm}"
WAIT="${GILLSYSTEMS_BLENDER_WAIT:-900}"

if [ "$#" -lt 1 ]; then
  echo "usage: $0 <script.py> [args...]" >&2
  exit 2
fi

SCRIPT="$1"; shift
[ -f "$SCRIPT" ] || SCRIPT="$SWARM_DIR/$1"
if [ ! -f "$SCRIPT" ]; then
  echo "SCRIPT NOT FOUND: $SCRIPT" >&2
  exit 2
fi
if [ ! -x "$BLENDER" ]; then
  echo "BLENDER NOT FOUND/EXEC: $BLENDER" >&2
  exit 2
fi

mkdir -p "$(dirname "$LOCK")" 2>/dev/null || true
# flock -w returns 1 when the lock cannot be taken in time -> we exit 75 (skip).
exec 9>"$LOCK" 2>/dev/null || true
if ! flock -w "$WAIT" 9; then
  echo "[BLENDER-TURN] LOCK BUSY after ${WAIT}s - skipping this turn (pick another task)" >&2
  exit 75
fi

echo "[BLENDER-TURN] lock acquired: $LOCK"
echo "[BLENDER-TURN] script: $SCRIPT"
# Renderless by default: headless Linux has no GPU context for EEVEE.
"$BLENDER" -b -noaudio -P "$SCRIPT" -- "$@"
RC=$?
echo "[BLENDER-TURN] blender exit=$RC"
exit $RC
