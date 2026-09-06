#!/usr/bin/env bash
# 05_keyword_ioc_scan.sh <path-to-evidence-image>
# Runs bulk_extractor directly against the raw image — no filesystem parsing
# needed, so it also catches data in deleted space, slack space, and swap.
# Pulls out emails, URLs, search terms, credit-card-pattern hits, and more.
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <path-to-evidence-image>"
  exit 1
fi

IMG="$1"
OUT="$(cd "$(dirname "$0")/.." && pwd)/analysis/bulk_extractor_output"
mkdir -p "$(dirname "$OUT")"

echo "==> Running bulk_extractor (this scans the entire raw image, can take a while)"
bulk_extractor -o "$OUT" "$IMG"

echo ""
echo "==> Key output files to review:"
for f in email.txt url.txt domain.txt ccn.txt exif.txt; do
  if [ -f "$OUT/$f" ]; then
    COUNT=$(wc -l < "$OUT/$f")
    echo "    $f — $COUNT lines"
  fi
done

echo ""
echo "==> Cross-reference hits here against your timeline (step 03) and recovered"
echo "    files (step 04) — an email address or URL appearing near the leak window"
echo "    is exactly the kind of correlated evidence a real IR report needs."
echo "    Full output directory: $OUT"
