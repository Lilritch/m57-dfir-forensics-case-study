#!/usr/bin/env bash
# Hash every supplied segment and compare against the preserved case baseline.
set -euo pipefail
CASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$CASE_DIR/scripts/verify_evidence.py" "$@"
