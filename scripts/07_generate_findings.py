#!/usr/bin/env python3
"""
07_generate_findings.py

Parses the Plaso super-timeline CSV and produces a quick statistical summary:
event counts by day, by source type, and a filtered view around a date range
you specify — meant to jump-start the "Findings" section of your report
instead of scrolling a 500,000-row CSV by hand.

Usage:
    python3 07_generate_findings.py [--start YYYY-MM-DD] [--end YYYY-MM-DD]

Reads:  analysis/super_timeline.csv  (produced by 03_build_timeline.sh)
Writes: analysis/findings_summary.txt
"""

import argparse
import csv
import sys
from collections import Counter
from datetime import datetime, date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TIMELINE_CSV = BASE / "analysis" / "super_timeline.csv"
OUT_FILE = BASE / "analysis" / "findings_summary.txt"


def parse_args():
    p = argparse.ArgumentParser(description="Summarize a Plaso l2tcsv timeline")
    p.add_argument("--start", help="Filter start date, YYYY-MM-DD", default=None)
    p.add_argument("--end", help="Filter end date, YYYY-MM-DD", default=None)
    args = p.parse_args()
    try:
        args.start = date.fromisoformat(args.start) if args.start else None
        args.end = date.fromisoformat(args.end) if args.end else None
    except ValueError:
        p.error("Dates must use YYYY-MM-DD.")
    if args.start and args.end and args.start > args.end:
        p.error("Start date must not be after end date.")
    return args


def main():
    args = parse_args()

    if not TIMELINE_CSV.exists():
        print(f"Timeline not found at {TIMELINE_CSV}. Run scripts/03_build_timeline.sh first.")
        sys.exit(1)

    by_day = Counter()
    by_source = Counter()
    filtered_rows = []
    total = 0

    with open(TIMELINE_CSV, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            # l2tcsv format includes a 'date' column like MM/DD/YYYY
            date_str = row.get("date", "")
            source = row.get("source", "unknown")
            by_source[source] += 1
            if date_str:
                by_day[date_str] += 1

            if args.start or args.end:
                try:
                    event_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                except ValueError:
                    raise SystemExit(f"Invalid timeline date at record {total}: {date_str!r}")
                if args.start and event_date < args.start:
                    continue
                if args.end and event_date > args.end:
                    continue
                filtered_rows.append(row)

    if args.start or args.end:
        filtered_path = BASE / "analysis" / "filtered_timeline.csv"
        with filtered_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=reader.fieldnames or [])
            writer.writeheader()
            writer.writerows(filtered_rows)

    with open(OUT_FILE, "w") as out:
        out.write("DFIR TIMELINE FINDINGS SUMMARY\n")
        out.write("=" * 40 + "\n\n")
        out.write(f"Total events parsed: {total}\n\n")

        out.write("Events by source type:\n")
        for source, count in by_source.most_common():
            out.write(f"  {source:20s} {count}\n")
        out.write("\n")

        out.write("Top 15 busiest days (possible activity spikes):\n")
        for day, count in by_day.most_common(15):
            out.write(f"  {day:15s} {count} events\n")
        out.write("\n")

        if args.start or args.end:
            out.write(f"Filtered window {args.start or '...'} to {args.end or '...'}: "
                      f"{len(filtered_rows)} events\n")
            out.write("(Review analysis/filtered_timeline.csv — this is your leak-window candidate set.)\n")

    print(f"Findings summary written to {OUT_FILE}")
    print("Use the 'busiest days' list to zero in on the suspected leak window, then")
    print("re-run this script with --start/--end to isolate just that window for your report.")


if __name__ == "__main__":
    main()
