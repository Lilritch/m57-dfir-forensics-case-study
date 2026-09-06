#!/usr/bin/env bash
# Resumable acquisition, local baseline, and EWF integrity verification.
set -euo pipefail
CASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$CASE_DIR/scripts/download_evidence.py" "$@"
