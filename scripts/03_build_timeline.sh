#!/usr/bin/env bash
# 03_build_timeline.sh <path-to-evidence-image>
# Builds a cross-artifact super-timeline with Plaso (log2timeline + psort).
# This is the single most valuable deliverable in the whole project — it
# correlates filesystem timestamps, registry/plist activity, browser history,
# and more into one chronological view.
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <path-to-evidence-image>"
  exit 1
fi

IMG="$1"
OUT="$(cd "$(dirname "$0")/.." && pwd)/analysis"
mkdir -p "$OUT"

PLASO_STORAGE="$OUT/timeline.plaso"
TIMELINE_CSV="$OUT/super_timeline.csv"

echo "==> Running log2timeline.py against the image (this is the slow step)..."
log2timeline.py --status_view none "$PLASO_STORAGE" "$IMG"

echo ""
echo "==> Extracting to a sorted CSV timeline with psort.py..."
psort.py -o l2tcsv -w "$TIMELINE_CSV" "$PLASO_STORAGE"

echo ""
echo "==> Timeline written to $TIMELINE_CSV"
echo "==> Quick stats:"
echo "    Total events: $(($(wc -l < "$TIMELINE_CSV") - 1))"
echo ""
echo "Next: open $TIMELINE_CSV in a spreadsheet or 'less', filter to the suspected"
echo "leak window, and note anything relevant (file access, USB insertion, browser"
echo "uploads, email activity) in case-management/case_notes.md with exact timestamps."
