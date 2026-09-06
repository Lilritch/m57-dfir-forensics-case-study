# Digital Forensics Incident Report

**Case:** M57.biz — Confidential Salary Spreadsheet Disclosure
**Case number:** DFIR-P7-001
**Prepared by:** [Your name], DFIR Analyst
**Date of report:**
**Classification:** Confidential

---

## 1. Executive Summary
_(2–3 sentences: what happened, what you found, what you recommend. Written last, read first.)_

## 2. Scope of Engagement
- Evidence provided:
- Custodian(s):
- Objective:
- Limitations (e.g. single-disk scope, no network capture available):

## 3. Methodology
Briefly describe the process, referencing tools used:
1. Evidence acquisition verification (SHA-256 hash logging)
2. Partition and filesystem inventory (The Sleuth Kit)
3. Super-timeline construction (Plaso)
4. Deleted file recovery (tsk_recover, photorec)
5. Keyword/IOC scanning (bulk_extractor)
6. (If applicable) Memory analysis (Volatility3)

## 4. Timeline of Events
_(Pull directly from analysis/findings_summary.txt and your case notes. Present as a table.)_

| Timestamp | Event | Source artifact | Significance |
|---|---|---|---|
| | | | |

## 5. Findings
### 5.1 Recovered Evidence
_(Files recovered via carving, their content, and relevance)_

### 5.2 Correlated Indicators
_(Emails, URLs, or other IOCs tied to the timeline)_

### 5.3 Attribution
_(What the evidence supports about who did what, when — stay within what's provable)_

## 6. Conclusion
_(Direct answer to the original question: what happened to the confidential file?)_

## 7. Recommendations
- Technical controls:
- Policy/process changes:
- Follow-up investigation needed (if any):

## 8. Appendices
- Appendix A: Full chain of custody log
- Appendix B: Full recovered file listing
- Appendix C: Full timeline export (reference to `analysis/super_timeline.csv`)
- Appendix D: Tool versions used
