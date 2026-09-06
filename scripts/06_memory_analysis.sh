#!/usr/bin/env bash
# 06_memory_analysis.sh <path-to-memory-image>
# OPTIONAL — only relevant if you're using the M57-Patents scenario, which
# includes RAM captures alongside disk images. Runs a standard Volatility3
# triage pass: process list, network connections, and command history.
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <path-to-memory-image>"
  echo "(Skip this step entirely if you're only using M57-Jean — no memory image included.)"
  exit 1
fi

MEM="$1"
OUT="$(cd "$(dirname "$0")/.." && pwd)/analysis/memory"
mkdir -p "$OUT"

echo "==> Identifying OS profile"
vol -f "$MEM" windows.info 2>/dev/null | tee "$OUT/os_info.txt" || \
vol -f "$MEM" mac.info 2>/dev/null | tee "$OUT/os_info.txt" || \
echo "Could not auto-detect OS type — check Volatility3 symbol tables for this image."

echo ""
echo "==> Process list"
vol -f "$MEM" windows.pslist 2>/dev/null | tee "$OUT/pslist.txt" || \
vol -f "$MEM" mac.pslist 2>/dev/null | tee "$OUT/pslist.txt"

echo ""
echo "==> Network connections at time of capture"
vol -f "$MEM" windows.netscan 2>/dev/null | tee "$OUT/netscan.txt" || \
vol -f "$MEM" mac.netstat 2>/dev/null | tee "$OUT/netscan.txt"

echo ""
echo "==> Command history / bash history (if applicable)"
vol -f "$MEM" windows.cmdline 2>/dev/null | tee "$OUT/cmdline.txt" || true

echo ""
echo "==> Done. Review $OUT/ for processes and connections active during the leak window"
echo "    identified in your timeline (step 03) — this is strong corroborating evidence."
