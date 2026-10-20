"""Known exact distributions and paired-fixture integrity for selection gates."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v11_analysis',ROOT/'tools/titan_v11/analyze.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def rows():
    return [{'fixture_id':str(i),'seed':i,'candidate_slot':0,
             'candidate_takes_kickoff':True,'split':'test','opponent':'fixed',
             'result':{'engine_version':'0.1.0','config_hash':'fixed','ticks':2400,
                       'kickoff_team':0,'score':[0,0]}} for i in range(8)]


class SelectionStatisticsTests(unittest.TestCase):
    def test_eight_positive_seed_blocks_have_known_exact_probability(self):
        base=rows();candidate=copy.deepcopy(base)
        for row in candidate:row['result']['score']=[1,0]
        result=m.seed_statistics(base,candidate)
        self.assertEqual(result['exact_one_sided_sign_flip_p'],1/256)
        self.assertEqual(result['bootstrap_97_5'],[2.,2.])

    def test_zero_effect_cannot_pass_significance(self):
        base=rows();result=m.seed_statistics(base,copy.deepcopy(base))
        self.assertEqual(result['exact_one_sided_sign_flip_p'],1.)
        self.assertEqual(result['bootstrap_97_5'],[0.,0.])

    def test_duplicate_candidate_fixture_cannot_replace_missing_pair(self):
        base=rows();candidate=copy.deepcopy(base);candidate[-1]=copy.deepcopy(candidate[0])
        with self.assertRaises(AssertionError):m.seed_statistics(base,candidate)

    def test_engine_or_fixture_metadata_mismatch_is_rejected(self):
        base=rows();candidate=copy.deepcopy(base)
        candidate[0]['result']['config_hash']='changed'
        with self.assertRaises(AssertionError):m.seed_statistics(base,candidate)
