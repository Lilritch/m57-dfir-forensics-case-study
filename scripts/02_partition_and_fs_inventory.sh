#!/usr/bin/env bash
# 02_partition_and_fs_inventory.sh <path-to-evidence-image>
# Maps the partition table and filesystem, and dumps a full file listing.
# Uses The Sleuth Kit — read-only, non-destructive against the image.
set -euo pipefail

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  echo "Usage: $0 <path-to-evidence-image> [start-sector]"
  exit 1
fi

IMG="$1"
OUT="$(cd "$(dirname "$0")/.." && pwd)/analysis"
mkdir -p "$OUT"

echo "==> Partition table (mmls)"
mmls "$IMG" | tee "$OUT/partition_table.txt"

echo ""
echo "==> Reading partition table to find the offset of the main filesystem..."
echo "    Look at partition_table.txt above. Note the 'Start' sector of the partition"
echo "    that holds the OS (usually the largest NTFS/HFS+/ext partition)."
OFFSET="${2:-}"
if [ -z "$OFFSET" ]; then
  read -rp "Enter the partition start offset (sector number) to inspect: " OFFSET
fi
if ! [[ "$OFFSET" =~ ^[0-9]+$ ]]; then
  echo "Offset must be a non-negative sector number." >&2
  exit 1
fi
printf '%s\n' "$OFFSET" > "$OUT/partition_offset.txt"

echo "==> Filesystem details (fsstat) at offset $OFFSET"
fsstat -o "$OFFSET" "$IMG" | tee "$OUT/fs_inventory.txt"

echo ""
echo "==> Full recursive file listing (fls), including deleted entries"
fls -o "$OFFSET" -r -p "$IMG" | tee "$OUT/full_file_listing.txt"

echo ""
echo "==> Isolating deleted entries specifically (marked '*' in fls output)"
fls -o "$OFFSET" -r -p -d "$IMG" > "$OUT/deleted_entries.txt"
echo "    Found $(wc -l < "$OUT/deleted_entries.txt") deleted filesystem entries."
echo "    See analysis/deleted_entries.txt — these are your carving/recovery targets."

echo ""
echo "==> Done. Key outputs:"
echo "    analysis/partition_table.txt"
echo "    analysis/fs_inventory.txt"
echo "    analysis/full_file_listing.txt"
echo "    analysis/deleted_entries.txt"
