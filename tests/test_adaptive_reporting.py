"""Regenerate prose from immutable evidence and compare it with native totals."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('adaptive_report',ROOT/'tools/adaptive_architect/analyze.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class AdaptiveReportingTests(unittest.TestCase):
    def test_narrative_uses_global_totals_not_last_style_subtotal(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);run=root/'run';out=root/'corrected.json'
            with zipfile.ZipFile(ROOT/'tests/fixtures/adaptive-architect-native-evidence.zip') as z:
                for name in z.namelist():
                    if not name.startswith('development/'):continue
                    dest=run/name.removeprefix('development/')
                    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
            with patch('sys.argv',['analyze','--run',str(run),'--out',str(out)]),contextlib.redirect_stdout(io.StringIO()):
                m.main()
            text=out.with_suffix('.md').read_text()
            self.assertIn('gained 6 points over v10, completed 110 more passes, conceded 13 fewer goals and recorded 24 fewer turnovers',text)
            self.assertNotIn('gained 152 points',text)
            published=json.loads((ROOT/'docs/adaptive-architect/results.json').read_text())
            corrected=json.loads(out.read_text())
            for key in ('raw_summary','accepted_summary','comparisons','gates','decision'):
                self.assertEqual(published[key],corrected[key],key)
