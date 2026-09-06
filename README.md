# M57 DFIR Forensics Case Study

A reproducible digital forensics and incident response investigation of the
[M57-Jean scenario](https://digitalcorpora.org/corpora/scenarios/m57-jean/) from
Digital Corpora.

The scenario concerns a confidential employee spreadsheet that appeared on a
competitor's website. The only known copy belonged to Jean, an M57.biz executive
who said that her laptop had been compromised. This project examines the supplied
disk image to determine how the document left the computer and which conclusions
the available evidence supports.

## Investigation objectives

- Preserve and verify the supplied forensic image.
- Identify the disk layout and active filesystem.
- Locate the confidential spreadsheet and related artifacts.
- Reconstruct relevant activity using filesystem and application timestamps.
- Review email, browser, shortcut, and deleted-file evidence.
- Distinguish supported findings from assumptions and unsupported attribution.
- Produce an incident report with evidence references and recommendations.

## Scope

The primary evidence is a 10 GiB Windows XP disk distributed as a two-segment
EnCase Expert Witness Format image:

```text
nps-2008-jean.E01
nps-2008-jean.E02
```

Both segments must be present in the same directory. The evidence files are not
included in this repository. They are downloaded from Digital Corpora and excluded
from version control.

This project is a command-line forensic workflow. It produces text reports, CSV
timelines, hashes, and extracted artifacts. It does not include a web application
or graphical interface.

## Methodology

The workflow follows an evidence-first process:

1. Download both EWF segments from the official source.
2. Validate HTTP byte ranges and expected segment sizes.
3. Establish a local SHA-256 baseline for each segment.
4. Verify the EWF container against its embedded integrity hash.
5. Identify the partition table and NTFS filesystem.
6. Inventory allocated and deleted filesystem entries.
7. Generate a filesystem timeline in UTC.
8. Extract and review relevant documents, mail, browser data, and shortcuts.
9. Correlate independent artifacts before forming conclusions.
10. Record findings, limitations, and remediation recommendations.

The original evidence is treated as read-only. Analysis output is written under
`analysis/`, and evidence handling is recorded under `case-management/`.

## Tools

| Tool | Purpose |
|---|---|
| The Sleuth Kit | Disk, partition, filesystem, and deleted-entry analysis |
| `mmls` | Display the partition table and sector offsets |
| `fsstat` | Report filesystem metadata and structure |
| `fls` | Recursively list allocated and deleted filesystem entries |
| `mactime` | Convert filesystem metadata into a chronological timeline |
| `tsk_recover` | Recover files referenced by filesystem metadata |
| libewf | Read segmented EnCase EWF evidence images |
| `ewfinfo` | Report EWF acquisition and media metadata |
| `ewfverify` | Verify the EWF image against its embedded integrity hash |
| bulk_extractor | Scan raw data for email addresses, URLs, domains, and other features |
| ExifTool | Extract metadata from recovered documents and media |
| TestDisk / PhotoRec | Filesystem recovery and signature-based file carving |
| Plaso | Create a cross-artifact super-timeline when installed |
| Volatility 3 | Optional memory analysis for scenarios that include RAM images |
| Python 3 | Evidence acquisition, validation, triage, tests, and summaries |

## Repository structure

```text
m57-dfir-forensics-case-study/
├── README.md
├── .gitignore
├── evidence/                         # downloaded evidence; excluded from Git
├── analysis/                         # generated results; excluded from Git
├── case-management/
│   ├── case_notes.md
│   └── chain_of_custody.md
├── report/
│   └── incident_report_template.md
├── scripts/
│   ├── 00_download_evidence.sh
│   ├── 00_setup_macos.sh
│   ├── 01_verify_evidence.sh
│   ├── 02_partition_and_fs_inventory.sh
│   ├── 03_build_timeline.sh
│   ├── 04_carve_deleted_files.sh
│   ├── 05_keyword_ioc_scan.sh
│   ├── 06_memory_analysis.sh
│   ├── 07_generate_findings.py
│   ├── 08_initial_triage.py
│   ├── download_evidence.py
│   └── verify_evidence.py
└── tests/
    ├── test_acquisition.py
    └── test_workflow.py
```

## Requirements

- macOS on Apple Silicon or Intel
- Homebrew
- Python 3
- Approximately 15 GiB of free space for evidence, temporary download chunks,
  extracted data, and analysis output

Install the core tools:

```bash
bash scripts/00_setup_macos.sh
```

Install the extended toolset:

```bash
bash scripts/00_setup_macos.sh --full
```

## Evidence acquisition

Download both official EWF segments, preserve a local SHA-256 baseline, and run
EWF integrity verification:

```bash
bash scripts/00_download_evidence.sh
```

The downloader resumes interrupted transfers, validates each `Content-Range`
response, checks final segment sizes, records SHA-256 values in
`analysis/evidence_hashes.json`, and writes the EWF verification output to
`analysis/ewf_verification.txt`.

The first SHA-256 calculation establishes a local baseline. It is an integrity
reference for later comparisons and is not presented as a publisher-supplied hash.

Recheck evidence integrity at any time:

```bash
bash scripts/01_verify_evidence.sh evidence/nps-2008-jean.E01
```

## Initial triage

Run the automated read-only inventory:

```bash
python3 scripts/08_initial_triage.py
```

The triage script verifies the evidence, records EWF metadata, maps the partition
table, identifies a unique NTFS candidate, lists allocated and deleted entries,
and creates a filesystem timeline. It stops for manual review when partition
selection is ambiguous.

Important outputs include:

| Output | Description |
|---|---|
| `analysis/initial_triage.md` | Initial inventory summary |
| `analysis/partition_table.txt` | Partition map and sector offsets |
| `analysis/fs_inventory.txt` | NTFS filesystem metadata |
| `analysis/full_file_listing.txt` | Recursive filesystem listing |
| `analysis/deleted_entries.txt` | Deleted filesystem entries |
| `analysis/filesystem_timeline.csv` | Filesystem timeline normalized to UTC |
| `analysis/filename_leads.txt` | Filenames matching initial investigation terms |

## Extended analysis

Build a Plaso super-timeline:

```bash
bash scripts/03_build_timeline.sh evidence/nps-2008-jean.E01
```

Recover deleted files:

```bash
bash scripts/04_carve_deleted_files.sh evidence/nps-2008-jean.E01
```

Run feature and IOC extraction:

```bash
bash scripts/05_keyword_ioc_scan.sh evidence/nps-2008-jean.E01
```

Generate timeline summary statistics:

```bash
python3 scripts/07_generate_findings.py
```

Filter a specific UTC date range:

```bash
python3 scripts/07_generate_findings.py --start 2008-07-19 --end 2008-07-21
```

Filtered events are written to `analysis/filtered_timeline.csv`. Statistical
activity and filename matches are leads, not findings, until the underlying
artifacts have been reviewed and correlated.

## Findings summary

The examined evidence supports an email-based social-engineering disclosure. The
key artifact sequence is:

1. A legitimate internal message requested a private employee spreadsheet.
2. An external Gmail account impersonated the apparent requester and added urgency.
3. The spreadsheet was created or saved on Jean's desktop shortly afterward.
4. A sent-mail artifact contains the spreadsheet as an attachment in the deceptive
   email thread.
5. The attached copy matches the desktop spreadsheet by SHA-256.
6. A later message from the external account acknowledged receipt.

This supports the conclusion that Jean sent the document after being deceived by an
impersonating email. The disk alone does not identify the person controlling the
external account, prove how the file was later posted publicly, or exclude every
possible additional access path. Those questions require mail-server logs, provider
records, network telemetry, and evidence from other relevant systems.

The detailed working assessment remains in the locally generated
`analysis/preliminary_findings.md` and should be reviewed against source artifacts
before completing the final report.

## Validation

Run the project tests with:

```bash
python3 -m unittest discover -s tests -v
```

The tests cover segmented-evidence verification, changed or missing evidence,
exact HTTP byte-range validation, ambiguous partition selection, and timeline date
filtering across calendar-year boundaries.

## Reporting

The incident-report template covers the executive summary, scope, methodology,
timeline, evidence, attribution boundaries, conclusion, recommendations, and
appendices.

Do not include employee Social Security numbers or other unnecessary sensitive data
in a public report. Reference artifacts with paths, message identifiers, timestamps,
hashes, and tool output sufficient for another analyst to reproduce the finding.

## Limitations

- The scenario provides a disk image, not complete enterprise telemetry.
- A filesystem timeline does not include every application event.
- Deleted data may be incomplete, overwritten, or lack original metadata.
- Timestamp interpretation depends on artifact semantics and time-zone handling.
- An email address identifies an account, not necessarily its operator.
- The Homebrew build of bulk_extractor may lack direct E01 support; a verified raw
  working copy or EWF-capable build is required for the raw scan.
- Memory analysis is outside this scenario because no RAM image is supplied.

## Evidence and privacy

The following material must remain outside the public repository:

- E01/E02 evidence segments;
- raw disk exports;
- recovered mailboxes and attachments;
- spreadsheets containing personal information;
- generated analysis directories; and
- temporary download chunks.

The included `.gitignore` excludes `evidence/`, `analysis/`, Python bytecode, and
macOS metadata. Always inspect staged files before publishing:

```bash
git status --short
git status --short --ignored
```

## Source

Digital Corpora, M57-Jean scenario:
https://digitalcorpora.org/corpora/scenarios/m57-jean/

The scenario is intended for forensic education and self-study. Follow the source
site's terms when downloading, analyzing, or redistributing materials.
