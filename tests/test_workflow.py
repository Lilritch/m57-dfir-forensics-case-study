"""Exercise evidence tampering detection and timeline date boundaries in isolation."""
import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('scripts', 'analysis', 'case-management', 'evidence'):
            (self.root / name).mkdir()
        for name in ('verify_evidence.py', '07_generate_findings.py'):
            shutil.copy(SOURCE / 'scripts' / name, self.root / 'scripts' / name)

    def run_script(self, name, *args):
        return subprocess.run([sys.executable, str(self.root / 'scripts' / name), *map(str, args)], capture_output=True, text=True)

    def test_segments_tampering_and_missing_segment_preserve_baseline(self):
        first = self.root / 'evidence' / 'disk.E01'
        second = self.root / 'evidence' / 'disk.E02'
        first.write_bytes(b'first segment')
        second.write_bytes(b'second segment')
        self.assertEqual(self.run_script('verify_evidence.py', first).returncode, 0)
        baseline = self.root / 'analysis' / 'evidence_hashes.json'
        original = baseline.read_bytes()
        self.assertEqual(self.run_script('verify_evidence.py', first).returncode, 0)
        second.chmod(0o644)
        second.write_bytes(b'tampered')
        self.assertNotEqual(self.run_script('verify_evidence.py', first).returncode, 0)
        self.assertEqual(baseline.read_bytes(), original)
        second.unlink()
        self.assertNotEqual(self.run_script('verify_evidence.py', first).returncode, 0)
        self.assertEqual(baseline.read_bytes(), original)

    def test_date_filter_crosses_year_and_exports_rows(self):
        path = self.root / 'analysis' / 'super_timeline.csv'
        path.write_text('date,source,desc\n12/30/2008,FILE,before\n12/31/2008,FILE,start\n01/01/2009,WEB,end\n01/02/2009,FILE,after\n')
        result = self.run_script('07_generate_findings.py', '--start', '2008-12-31', '--end', '2009-01-01')
        self.assertEqual(result.returncode, 0, result.stderr)
        with (self.root / 'analysis' / 'filtered_timeline.csv').open() as stream:
            self.assertEqual([r['desc'] for r in csv.DictReader(stream)], ['start', 'end'])
        self.assertNotEqual(self.run_script('07_generate_findings.py', '--start', '2009-01-02', '--end', '2008-12-31').returncode, 0)

if __name__ == '__main__':
    unittest.main()
