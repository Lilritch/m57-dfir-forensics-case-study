#!/usr/bin/env python3
"""Establish or check a SHA-256 baseline; E01 input includes sibling segments."""
import argparse
import getpass
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    args = parser.parse_args()
    paths = set()
    for image in args.images:
        image = image.resolve()
        if image.suffix.upper() == ".E01":
            paths.update(image.parent.glob(image.stem + ".E[0-9][0-9]"))
        paths.add(image)
    current = {}
    for path in sorted(paths):
        if not path.is_file():
            parser.error(f"Missing evidence: {path}")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                digest.update(chunk)
        current[str(path)] = {"sha256": digest.hexdigest(), "size": path.stat().st_size}
    output = BASE / "analysis"
    output.mkdir(exist_ok=True)
    baseline = output / "evidence_hashes.json"
    if baseline.exists():
        expected = json.loads(baseline.read_text())
        valid = expected == current
        action = "Integrity check PASS" if valid else "Integrity check FAIL (hash, size, or evidence set changed)"
    else:
        with baseline.open("x") as stream:
            json.dump(current, stream, indent=2)
            stream.write("\n")
        valid = True
        action = "Initial local baseline recorded (not publisher-verified)"
    timestamp = datetime.now(timezone.utc).isoformat()
    log = BASE / "case-management" / "chain_of_custody.md"
    with log.open("a") as stream:
        stream.write(f"\n### {timestamp} — {action}\nAnalyst account: {getpass.getuser()}\n\n")
        for name, entry in current.items():
            stream.write(f"- `{name}` — {entry['size']} bytes — SHA-256 `{entry['sha256']}`\n")
    print(action)
    for name, entry in current.items():
        print(entry["sha256"], name)
    if not valid:
        raise SystemExit("STOP: evidence differs from the preserved baseline. Investigate before analysis.")
    for path in paths:
        path.chmod(path.stat().st_mode & ~0o222)

if __name__ == "__main__":
    main()
