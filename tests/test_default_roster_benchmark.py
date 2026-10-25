"""Prevent the observed custom-formation mismatch in course replay comparisons."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/benchmarks'))
sys.path.append(str(ROOT / 'student-sdk'))
from default_roster import native_match


class ReplayRosterParity(unittest.TestCase):
    def test_native_driver_matches_external_course_rosters(self):
        fixtures = json.loads((ROOT / 'tests/fixtures/replay-default-rosters.json').read_text())['fixtures']
        # This valid, deliberately different formation catches accidental
        # reuse of play_match's optional formation hook.
        controller = '''from soccer import TeamController
class Passive(TeamController):
    name = "roster-parity"
    version = "test"
    def initial_formation(self, field):
        return [(-47.,0.),(-26.,0.),(-15.,-7.8),(-15.,12.),(-11.8,0.)]
    def act(self, obs):
        return self.idle(obs)
'''
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'team.py'
            source.write_text(controller)
            for fixture in fixtures:
                with self.subTest(seed=fixture['seed']):
                    result, _, positions = native_match(
                        str(source), str(source), fixture['seed'], 0, fixture['kickoff'] == 0,
                        dict(config_path=str(ROOT / 'configs/default.toml'),
                             config_hash=fixture['config_hash'], engine_version='0.1.0'))
                    self.assertEqual(len(positions), 10)
                    for actual, expected in zip(positions, fixture['positions']):
                        for a, b in zip(actual, expected):
                            self.assertAlmostEqual(a, b, delta=3e-6)
                    self.assertEqual(result['ticks'], 2400)
                    self.assertEqual(result['score'], [0, 0])
                    self.assertEqual([s['policy_errors'] for s in result['stats']], [0, 0])


if __name__ == '__main__':
    unittest.main()
