"""Focused tactical regressions; run with python tools/test_titan.py."""
import importlib.util
import math
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import bootstrap
bootstrap.ensure_engine(ROOT)
from soccer import SoccerEnv, TeamAction


def load(path):
    spec = importlib.util.spec_from_file_location("titan_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


titan = load(ROOT / "my-team/team.py")


class TacticalRegressions(unittest.TestCase):
    def setUp(self):
        self.env = SoccerEnv()
        self.policy = titan._FallbackPolicy()
        self.policy._setup(self.env.field)

    def tearDown(self):
        self.env.close()

    def test_wall_only_protects_positive_lead(self):
        normal, wall = TeamAction(), TeamAction()
        self.policy._act_normal = lambda obs: normal
        self.policy._lock_wall = lambda obs: wall
        self.policy._wall_break = lambda obs, actions: None
        for score in [(0, 0), (0, 1), (0, 2), (1, 3), (0, 5), (3, 3)]:
            for remaining in [1.0, 0.5, 0.01]:
                with self.subTest(score=score, remaining=remaining):
                    obs = SimpleNamespace(score=score, time_remaining=remaining)
                    self.assertIs(self.policy.act(obs), normal)
        for score in [(1, 0), (2, 0), (4, 3)]:
            self.assertIs(self.policy.act(SimpleNamespace(score=score, time_remaining=0.1)), wall)

    def test_original_two_goal_retreat_is_reproduced_and_removed(self):
        old = load(ROOT / "experiments/titan-original/team.py")._FallbackPolicy()
        # This is the sole difference in the downloaded broadwall_stiff file.
        old.TRAIL_WALL = 2
        normal, wall = TeamAction(), TeamAction()
        for policy in (old, self.policy):
            policy._act_normal = lambda obs: normal
            policy._lock_wall = lambda obs: wall
            policy._wall_break = lambda obs, actions: None
            policy.TRAIL_WALL = 2
        for score in [(0, 2), (1, 3), (2, 5)]:
            obs = SimpleNamespace(score=score, time_remaining=0.5)
            self.assertIs(old.act(obs), wall)
            self.assertIs(self.policy.act(obs), normal)

    def test_specialist_does_not_bait_wall_while_trailing(self):
        policy = titan._SpecialistPolicy()
        expected = TeamAction()
        policy._bait_counter_act = lambda obs: expected
        for score in [(0, 2), (1, 3), (0, 5)]:
            obs = SimpleNamespace(score=score, opponents=[], opponent_goal=(50.0, 0.0))
            self.assertIs(policy.act(obs), expected)

    def test_initial_formation_is_legal(self):
        formation = self.policy.initial_formation(self.env.field)
        self.assertEqual(len(formation), 5)
        self.assertEqual(self.env.set_formation(0, formation), 0)

    def test_all_players_get_finite_actions_after_reset(self):
        team = titan.AdaptiveChampion()
        for seed in (1001, 1005):
            team.reset(seed)
            obs = self.env.reset(seed=seed)["team_a"]
            actions = team.act(obs)
            self.assertEqual(set(actions.players), set(range(5)))
            for action in actions.players.values():
                self.assertTrue(all(math.isfinite(v) for v in action.movement))

    def test_expired_search_returns_safely(self):
        self.policy._decision_deadline = 0.0
        p = (4, 20.0, 0.0, 0.0, 0.0)
        self.assertIsNone(self.policy._shot_option(p, 21.0, 0.0, 0.0, 0.0, [], 0.0))
        self.assertIsNone(self.policy._search_links(p, 21.0, 0.0, 0.0, 0.0, [p], []))

    def test_zero_search_budget_still_returns_complete_legal_actions(self):
        team = titan.AdaptiveChampion()
        team._fallback.SEARCH_BUDGET_SECONDS = 0.0
        self.env.use_baseline(1, "tactical")
        team.reset(1001)
        observations = self.env.reset(seed=1001)
        for _ in range(120):
            action = team.act(observations["team_a"])
            self.assertEqual(set(action.players), set(range(5)))
            for player_action in action.players.values():
                self.assertTrue(all(math.isfinite(v) for v in player_action.movement))
                self.assertTrue(math.isfinite(player_action.kick_power))
            observations, _ = self.env.step({"team_a": action})
        validation = self.env.result()["stats"][0]["validation"]
        self.assertEqual(validation["missing_actions"], 0)
        self.assertEqual(validation["non_finite_values"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
