"""Test that transport validation and partition selection fail closed."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'

def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class AcquisitionTests(unittest.TestCase):
    def test_rejects_wrong_range_even_when_size_matches(self):
        module = load('download_evidence')
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / 'segment.chunk'
            def wrong_range(command, **kwargs):
                Path(command[command.index('--output') + 1]).write_bytes(b'data')
                Path(command[command.index('--dump-header') + 1]).write_text('HTTP/1.1 206 Partial Content\nContent-Range: bytes 4-7/8\n')
                return subprocess.CompletedProcess(command, 0, '', '')
            with patch.object(module.subprocess, 'run', side_effect=wrong_range), patch.object(module.time, 'sleep'):
                with self.assertRaises(RuntimeError):
                    module.fetch(('E01', 0, 3, 8, destination))
            self.assertFalse(destination.exists())

    def test_accepts_exact_range_and_size(self):
        module = load('download_evidence')
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / 'segment.chunk'
            def exact_range(command, **kwargs):
                Path(command[command.index('--output') + 1]).write_bytes(b'data')
                Path(command[command.index('--dump-header') + 1]).write_text('HTTP/1.1 206 Partial Content\nContent-Range: bytes 0-3/8\n')
                return subprocess.CompletedProcess(command, 0, '', '')
            with patch.object(module.subprocess, 'run', side_effect=exact_range):
                self.assertEqual(module.fetch(('E01', 0, 3, 8, destination)), 4)
            self.assertEqual(destination.read_bytes(), b'data')

    def test_ambiguous_partitions_require_manual_selection(self):
        module = load('08_initial_triage')
        with tempfile.TemporaryDirectory() as temporary:
            module.OUT = Path(temporary)
            table = module.OUT / 'table.txt'
            table.write_text('002: 000:000 0000063 0000999 0000937 NTFS / exFAT (0x07)\n003: 000:001 0001000 0001999 0001000 NTFS / exFAT (0x07)\n')
            with patch('sys.argv', ['triage']), patch.object(module.subprocess, 'run'), patch.object(module, 'run_to_file', return_value=table) as calls:
                with self.assertRaisesRegex(SystemExit, 'no unique NTFS'):
                    module.main()
            self.assertFalse(any(call.args[0][0] == 'fsstat' for call in calls.call_args_list))

if __name__ == '__main__':
    unittest.main()
