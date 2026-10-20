"""Known whole-seed randomization probabilities and balanced pair safeguards."""
import copy
import importlib.util
from pathlib import Path
import unittest
from test_titan_v11_statistics import rows

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('original_statistics',ROOT/'tools/original_architect/paired_statistics.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class OriginalArchitectStatisticsTests(unittest.TestCase):
    def test_known_exact_probability_and_no_floating_zero_drift(self):
        b=rows();a=copy.deepcopy(b)
        for r in a:r['result']['score']=[1,0]
        result=m.paired(b,a)
        self.assertEqual(result['exact_one_sided_sign_flip_p'],1/256)
        self.assertEqual(result['bootstrap_95'],[2.,2.])
        zero=m.paired(b,copy.deepcopy(b))
        self.assertEqual(zero['bootstrap_97_5'],[0.,0.])
        self.assertEqual(zero['exact_one_sided_sign_flip_p'],1.)

    def test_incomplete_or_duplicate_pair_cannot_enter_analysis(self):
        b=rows();a=copy.deepcopy(b);a[-1]=copy.deepcopy(a[0])
        with self.assertRaises(AssertionError):m.paired(b,a)
