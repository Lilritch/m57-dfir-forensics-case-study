#!/usr/bin/env bash
# Default: tools for evidence verification and filesystem inventory.
# --full: also install timeline, recovery, scanning, and memory tools.
set -euo pipefail
if [[ $# -gt 1 || ( $# -eq 1 && "$1" != "--full" ) ]]; then
  echo "Usage: $0 [--full]" >&2
  exit 1
fi
if ! command -v brew >/dev/null; then
  echo "Homebrew is required: https://brew.sh" >&2
  exit 1
fi
brew install sleuthkit libewf
commands=(mmls fsstat fls icat tsk_recover ewfinfo ewfverify)
if [[ "${1:-}" == "--full" ]]; then
  brew install exiftool testdisk bulk_extractor pipx
  pipx install plaso
  pipx install volatility3
  commands+=(exiftool photorec bulk_extractor log2timeline.py psort.py vol)
fi
missing=0
for tool in "${commands[@]}"; do
  if command -v "$tool" >/dev/null; then
    printf '[OK] %s\n' "$tool"
  else
    printf '[MISSING] %s\n' "$tool" >&2
    missing=1
  fi
done
exit "$missing"
