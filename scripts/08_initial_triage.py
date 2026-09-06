#!/usr/bin/env python3
"""Create an initial, read-only inventory after successful evidence verification."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
import time

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'analysis'
IMAGE = BASE / 'evidence/nps-2008-jean.E01'

def run_to_file(command, name):
    print('Running: ' + ' '.join(map(str, command)), flush=True)
    target = OUT / name
    temporary = target.with_suffix(target.suffix + '.partial')
    with temporary.open('w') as stream:
        subprocess.run(list(map(str, command)), stdout=stream, check=True)
    temporary.replace(target)
    return target

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wait-for-acquisition', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.wait_for_acquisition:
        deadline = time.monotonic() + 7200
        while True:
            log = OUT / 'acquisition.log'
            status = log.read_text() if log.exists() else ''
            if 'EWF verification complete.' in status:
                break
            if 'Traceback (most recent call last)' in status:
                raise SystemExit('Acquisition failed. Review analysis/acquisition.log; triage not started.')
            if time.monotonic() > deadline:
                raise SystemExit('Acquisition wait expired. Rerun after downloading and verifying evidence.')
            time.sleep(15)
    # Independently verify the current evidence before reading it for triage.
    subprocess.run(['bash', str(BASE / 'scripts/01_verify_evidence.sh'), str(IMAGE)], check=True)
    run_to_file(['ewfverify', IMAGE], 'ewf_verification_triage.txt')
    run_to_file(['ewfinfo', '-d', 'iso8601', IMAGE], 'ewf_info.txt')
    table = run_to_file(['mmls', IMAGE], 'partition_table.txt').read_text()
    offsets = re.findall(r'^\d+:\s+\d+:\d+\s+(\d+)\s+\d+\s+\d+\s+.*NTFS', table, re.MULTILINE)
    if len(offsets) != 1:
        raise SystemExit('Partition table saved. Select a filesystem manually; no unique NTFS candidate.')
    offset = str(int(offsets[0]))
    stats = run_to_file(['fsstat', '-o', offset, IMAGE], 'fs_inventory.txt').read_text()
    if not re.search(r'File System Type:\s+NTFS', stats):
        raise SystemExit('Candidate filesystem is not confirmed NTFS. Review fs_inventory.txt.')
    (OUT / 'partition_offset.txt').write_text(offset + '\n')
    listing = run_to_file(['fls', '-o', offset, '-r', '-p', IMAGE], 'full_file_listing.txt')
    deleted = run_to_file(['fls', '-o', offset, '-r', '-p', '-d', IMAGE], 'deleted_entries.txt')
    body = run_to_file(['fls', '-o', offset, '-r', '-m', '/', IMAGE], 'filesystem.body')
    run_to_file(['mactime', '-b', body, '-z', 'UTC', '-d'], 'filesystem_timeline.csv')
    candidates = re.compile(r'salary|salaries|payroll|\.xls[x]?($|\s)|\.pst($|\s)|\.dbx($|\s)|\.eml($|\s)', re.I)
    lines = listing.read_text(errors='replace').splitlines()
    hits = [line for line in lines if candidates.search(line)]
    (OUT / 'filename_leads.txt').write_text('\n'.join(hits) + '\n')
    timestamp = datetime.now(timezone.utc).isoformat()
    summary = (
        '# Initial filesystem triage\n\n'
        f'- Completed (UTC): {timestamp}\n'
        '- Evidence: nps-2008-jean.E01 and E02. Local hash comparison and EWF internal verification passed.\n'
        f'- NTFS partition start: {offset} sectors (see partition_table.txt for sector size).\n'
        f'- File-listing entries: {len(lines)}\n'
        f'- Deleted listing entries: {len(deleted.read_text().splitlines())}\n'
        f'- Filename leads: {len(hits)} (review filename_leads.txt).\n'
        '- Timeline: filesystem_timeline.csv, rendered in UTC. This is a filesystem timestamp timeline, not a Plaso application timeline.\n'
        '- Filename matches are investigative leads, not proof of disclosure. File contents and correlated artifacts still require review.\n'
    )
    (OUT / 'initial_triage.md').write_text(summary)
    with (BASE / 'case-management/case_notes.md').open('a') as stream:
        stream.write('\n' + summary.replace('# Initial filesystem triage', '## Initial filesystem triage'))
    subprocess.run(['bash', str(BASE / 'scripts/01_verify_evidence.sh'), str(IMAGE)], check=True)
    print('Initial triage complete. See analysis/initial_triage.md.', flush=True)

if __name__ == '__main__':
    main()
