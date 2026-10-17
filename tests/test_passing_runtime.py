"""TITAN-10B-R must preserve the frozen challenger's passing decisions."""
import ast
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import unittest
from unittest.mock import patch

from test_hybrid_planner import FIELD, ROOT


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OLD = load('frozen_titan10b', ROOT / 'experiments/titan-10b/team.py')
NEW_PATH = Path(os.environ.get('TITAN10BR_TEAM_PATH', ROOT / 'experiments/titan-10b-r/team.py'))
NEW = load('runtime_titan10br', NEW_PATH)


def pair():
    cs = OLD.Guardiola2011(), NEW.Guardiola2011()
    for c in cs:
        c._setup(FIELD)
    return cs


class PassingRuntimeTests(unittest.TestCase):
    def test_archived_sources_are_the_exact_behavior_and_competition_baselines(self):
        for path, expected in (
            ('champions/v9.1/team.py', 'c7fce081f12f283b9c9f9ee200f0dcc33769339a60bf535fc3446613612fabf6'),
            ('experiments/titan-10b/team.py', '269a24fe3f826500b3d6c1aad76f8770f0084f5a3ad81258cd7c2f50fba36108'),
        ):
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected)

    def test_scalar_rollout_is_exact_for_motion_cooldown_and_wall_flights(self):
        old, new = pair()
        rng = random.Random(101017)
        for _ in range(1500):
            p = (4, rng.uniform(-46, 46), rng.uniform(-27, 27), rng.uniform(-10, 10), rng.uniform(-10, 10))
            launch = (p[1] + rng.uniform(-12, 12), p[2] + rng.uniform(-12, 12), rng.uniform(-30, 30), rng.uniform(-30, 30))
            path = old._pass_path(launch, until=2.4)
            aim = (rng.uniform(-55, 55), rng.uniform(-35, 35))
            cooldown, after = rng.randrange(20), rng.choice((0., .05, .2, .7))
            first = None if rng.randrange(2) else (rng.uniform(-1, 1), rng.uniform(-1, 1))
            args = p, path, aim, cooldown, after, 2.4, first
            self.assertEqual(old._receiver_rollout(*args), new._receiver_rollout(*args))
            self.assertEqual(old._receiver_rollout(*args), new._receiver_rollout(*args, steps=new._pass_steps(path)))

    def test_scalar_rollout_keeps_the_original_small_gap_normalization(self):
        old, new = pair()
        for gap in (0., math.nextafter(1e-8, 0.), 1e-8, math.nextafter(1e-8, math.inf), 1e-7):
            for velocity in ((0., 0.), (8., 0.), (0., -8.)):
                p = (4, 0., 0., *velocity)
                path = [(0., 3., 0.), (.05, 1.3, 0.)]
                args = p, path, (gap, 0.), 3, 0., .05
                self.assertEqual(old._receiver_rollout(*args), new._receiver_rollout(*args))

    def test_sparse_rollouts_are_rejected_without_filling_in_a_witness(self):
        old, new = pair()
        p = (4, 0., 0., 0., 0.)
        path = [(0., 4., 0.), (.1, 1.4, 0.)]
        self.assertIsNone(old._receiver_rollout(p, path, (1., 0.)))
        self.assertIsNone(new._receiver_rollout(p, path, (1., 0.), steps=new._pass_steps(path)))

    def test_pass_race_matches_under_repeated_cooldown_and_movement_updates(self):
        old, new = pair()
        rng = random.Random(101018)
        for _ in range(200):
            launch = (rng.uniform(-40, 40), rng.uniform(-27, 27), rng.uniform(-30, 30), rng.uniform(-30, 30))
            path = old._pass_path(launch, until=2.6)
            receiver = (4, launch[0] + rng.uniform(-10, 10), launch[1] + rng.uniform(-8, 8), rng.uniform(-8, 8), rng.uniform(-8, 8))
            opponents = [(i, launch[0] + rng.uniform(-20, 20), launch[1] + rng.uniform(-20, 20), rng.uniform(-8, 8), rng.uniform(-8, 8)) for i in range(5, 10)]
            for cooldown, margin in ((0, 0.), (8, .1), (1, .12)):
                for c in (old, new):
                    c._friend_cooldowns = {4: cooldown}
                    c._enemy_cooldowns = {i: cooldown for i in range(5, 10)}
                for first in (None, (-.6, .8)):
                    kwargs = dict(margin=margin, after=.05, until=2.6, first_move=first)
                    self.assertEqual(old._pass_race(receiver, path, opponents, **kwargs), new._pass_race(receiver, path, opponents, **kwargs))
                    self.assertEqual(old._next_receive_aim, new._next_receive_aim)

    def test_saved_receptions_keep_every_route_and_first_touch_choice(self):
        data = json.loads((ROOT / 'tests/fixtures/execution-reception-cases.json').read_text())
        for case in data['cases']:
            row = case['start']
            receiver = next(tuple(p) for p in row['friends'] if p[0] == row['plan_after'][0])
            opponents = [tuple(p) for p in row['opponents']]
            for touch_filter in (False, True):
                old, new = pair()
                for c in (old, new):
                    c.FIRST_TOUCH = touch_filter
                    c._friend_cooldowns = {int(k): v for k, v in row['friend_cooldowns'].items()}
                    c._enemy_cooldowns = {int(k): v for k, v in row['enemy_cooldowns'].items()}
                paths = [c._pass_path(case['launch'], row['ball'][:2], 2.6) for c in (old, new)]
                for first in (None, (.8, -.6)):
                    results = [c._pass_race(receiver, p, opponents, .1, .05, 2.6, first) for c, p in zip((old, new), paths)]
                    self.assertEqual(results[0], results[1])
                    self.assertEqual(old._next_receive_aim, new._next_receive_aim)

    def test_metadata_reuses_only_the_identical_internal_flight(self):
        _, c = pair()
        path = c._pass_path((0., 0., 20., 3.))
        prepared = c._pass_steps(path)
        self.assertIs(c._pass_steps(path), prepared)
        other = list(path)
        self.assertIsNot(c._pass_steps(other), prepared)
        self.assertIs(c._runtime_path, other)
        self.assertEqual(c._pass_steps(other), prepared)

    def test_unavailable_interception_is_cached_as_none(self):
        _, c = pair()
        path = c._pass_path((0., 0., 25., 0.))
        with patch.object(c, '_verified_intercept', return_value=None) as query:
            for _ in range(2):
                self.assertIsNone(c._runtime_intercept((4, -45., -27., 0., 0.), path))
        self.assertEqual(query.call_count, 1)

    def test_interception_cache_keys_cover_every_query_input(self):
        old, c = pair()
        path = c._pass_path((0., 0., 25., 0.))
        for p in ((4, 3., 1., 0., 0.), (4, 3., 1., -8., 0.), (6, 3., 1., 0., 0.)):
            for cooldown in (0, 20):
                for after in (0., .3):
                    for until in (.1, 2.):
                        args = p, path, cooldown, after, until
                        self.assertEqual(c._runtime_intercept(*args), old._verified_intercept(*args))

    def test_saved_list_players_and_native_tuple_players_share_safe_keys(self):
        old, c = pair()
        path = c._pass_path((0., 0., 25., 0.))
        p = (4, 3., 1., 0., 0.)
        self.assertEqual(c._runtime_intercept(list(p), path), old._verified_intercept(p, path))
        self.assertEqual(c._runtime_intercept(p, path), old._verified_intercept(list(p), path))

    def test_query_storage_stays_bounded_and_resets_with_field_setup(self):
        _, c = pair()
        path = c._pass_path((0., 0., 25., 0.))
        for i in range(100):
            c._runtime_intercept((4, float(-i), 20., 0., 0.), path)
            self.assertLessEqual(len(c._runtime_queries), 32)
        c._setup(FIELD)
        self.assertIsNone(c._runtime_path)
        self.assertEqual(c._runtime_queries, {})
        c._pass_steps(path)
        c.reset(19)
        self.assertIsNone(c._runtime_path)
        self.assertIsNone(c._runtime_steps)
        self.assertEqual(c._runtime_queries, {})

    def test_explicit_foreign_steps_do_not_use_a_cached_result(self):
        old, c = pair()
        p = (4, 3., 1., 0., 0.)
        path = c._pass_path((0., 0., 25., 0.))
        c._runtime_intercept(p, path)
        foreign = [(0., 0, -40., -27., None)]
        self.assertEqual(c._runtime_intercept(p, path, steps=foreign), old._verified_intercept(p, path, steps=foreign))

    def test_successful_ordinary_aim_skips_all_alternative_scans(self):
        _, c = pair()
        class NoScan(list):
            def __iter__(self):
                raise AssertionError('Unnecessary alternative-target scan')
        path = NoScan([(0., 0., 0.), (.05, 1., 0.)])
        route = (.05, (1., 0.), (1., 0.), (4, 0., 0., 0., 0.), 'kick', 1, 1)
        with patch.object(c, '_runtime_intercept', return_value=(.05, (1., 0.))), patch.object(c, '_receiver_rollout', return_value=route) as rollout:
            self.assertEqual(c._receiver_route((4, 0., 0., 0., 0.), path, [], 0., 1., steps=[]), route)
        self.assertEqual(rollout.call_count, 1)

    def test_unrelated_methods_and_act_are_byte_for_byte_ast_equivalent(self):
        def methods(path):
            cls = next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.ClassDef))
            return {n.name: ast.dump(n, include_attributes=False) for n in cls.body if isinstance(n, ast.FunctionDef)}
        old, new = methods(ROOT / 'experiments/titan-10b/team.py'), methods(NEW_PATH)
        allowed = {'reset', '_setup', '_pass_steps', '_pass_race', '_receiver_rollout', '_receiver_route'}
        self.assertEqual({n for n in old if old[n] != new[n]}, allowed)


if __name__ == '__main__':
    unittest.main()
