#!/usr/bin/env bash
# 04_carve_deleted_files.sh <path-to-evidence-image>
# Recovers deleted files two ways:
#   1. tsk_recover — recovers files still referenced in filesystem metadata
#   2. photorec    — signature-based carving of unallocated space, for files
#                     whose metadata is already gone
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <path-to-evidence-image>"
  exit 1
fi

IMG="$1"
OUT="$(cd "$(dirname "$0")/.." && pwd)/analysis"
RECOVERED_TSK="$OUT/recovered_tsk"
RECOVERED_PHOTOREC="$OUT/recovered_photorec"
mkdir -p "$RECOVERED_TSK" "$RECOVERED_PHOTOREC"

read -rp "Enter the partition start offset (sector number), same as step 02: " OFFSET

echo "==> Recovering files via tsk_recover (metadata-based, includes deleted-but-intact files)"
tsk_recover -o "$OFFSET" "$IMG" "$RECOVERED_TSK"
echo "    Recovered $(find "$RECOVERED_TSK" -type f | wc -l) files to $RECOVERED_TSK"

echo ""
echo "==> Running photorec for signature-based carving of unallocated space"
echo "    photorec is interactive — select the image, choose 'Whole disk' or the"
echo "    partition matching offset $OFFSET, then destination: $RECOVERED_PHOTOREC"
photorec "$IMG"

echo ""
echo "==> Tagging recovered files with metadata via ExifTool for triage"
exiftool -r "$RECOVERED_TSK" "$RECOVERED_PHOTOREC" > "$OUT/recovered_files_metadata.txt" 2>/dev/null || true

echo ""
echo "==> Done. Review these for CV-worthy findings:"
echo "    $RECOVERED_TSK/            (metadata-recovered files)"
echo "    $RECOVERED_PHOTOREC/       (carved files from unallocated space)"
echo "    analysis/recovered_files_metadata.txt  (EXIF/metadata dump of everything recovered)"
echo ""
echo "For each interesting recovered file, note in case_notes.md: original path (if known),"
echo "recovery method, timestamp evidence, and why it's relevant to the leak."
