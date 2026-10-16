"""Focused public-physics regressions; run with python -m unittest discover -s tests."""
from pathlib import Path
from types import SimpleNamespace as S
import importlib.util
import os
import sys
import unittest

ROOT = Path(os.environ.get('ROBOCUP_REPO', Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / 'student-sdk'))
TEAM = Path(os.environ.get('ROBOCUP_TEAM_PATH', ROOT / 'my-team/team.py'))
spec = importlib.util.spec_from_file_location('tested_team', TEAM)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

FIELD = S(simulation_hz=20, max_speed=8., acceleration=20., ball_friction=.985,
          kick_impulse=22., kick_range=2.2, my_goal=(-50., 0.), opponent_goal=(50., 0.),
          height=60., goal_width=14., centre_circle_radius=9., player_radius=1., ball_radius=.45)

def controller():
    c = module.Guardiola2011()
    c._setup(FIELD)
    c._enemy_cooldowns = {}
    return c

class HybridPlannerTests(unittest.TestCase):
    def test_drag_stops_a_ball_that_cannot_reach_goal(self):
        c = controller()
        self.assertIsNone(c._goal_path((20., 0., 5., 0.)))
        self.assertIsNone(c._goal_path((45., 20., 20., 0.)))
        path, goal = c._goal_path((45., 0., 20., 0.))
        self.assertAlmostEqual(goal[1], 0.)
        self.assertLess(goal[0], .35)
        self.assertGreater(goal[2], 15.)

    def test_shot_rejected_when_own_body_reverses_it(self):
        c = controller()
        p = (3, 21.8, 0., 0., 0.)
        movement = c._move(p, (20.3, 0.))
        launch = c._carrier_contact(p, 20., 0., 22., 0., movement)
        self.assertLess(launch[2], 0.)
        opponents = [(5, 47., 24., 0., 0.)]
        self.assertIsNone(c._shot_option(p, 20., 0., 0., 0., opponents, 0.))

    def test_legal_impulse_cannot_cancel_excess_sideways_speed(self):
        c = controller()
        p = (3, 18.3, 0., 0., 0.)
        self.assertIsNone(c._shot_option(p, 20., 0., 0., 28., [], 0.))

    def test_nearby_receiver_gets_a_named_reachable_link(self):
        c = controller()
        passer = (2, -1.7, 0., 0., 0.)
        receiver = (3, 10., 0., 0., 0.)
        option = c._link_option(passer, 0., 0., 0., 0., receiver,
                                [(5, 47., 25., 0., 0.)], 10., 0., 14.)
        self.assertIsNotNone(option)
        self.assertEqual(option[3][0], receiver[0])
        self.assertGreater(option[3][1], 4.)
        self.assertLessEqual(option[1][1], 1.)

    def test_cooldown_does_not_remove_a_physical_body_block(self):
        c = controller()
        c._enemy_cooldowns = {6: 999}
        option = c._link_option((2, -1.7, 0., 0., 0.), 0., 0., 0., 0.,
                                (3, 10., 0., 0., 0.), [(6, 2., 0., 0., 0.)], 10., 0., 14.)
        self.assertIsNone(option)

    def test_mirrored_links_have_mirrored_kicks(self):
        c = controller()
        options = [c._link_option((2, -1.7, 0., 0., 0.), 0., 0., 0., 0.,
                    (3, 10., sign*4., 0., 0.), [(5, 47., sign*25., 0., 0.)],
                    10., sign*4., 14.) for sign in (-1, 1)]
        self.assertTrue(all(option is not None for option in options))
        self.assertAlmostEqual(options[0][1][0][0], options[1][1][0][0])
        self.assertAlmostEqual(options[0][1][0][1], -options[1][1][0][1])
        self.assertAlmostEqual(options[0][0], options[1][0])

    def test_existing_momentum_changes_the_interception_race(self):
        c = controller()
        path = [(1., 8.5, 0.)]
        stationary = c._intercept((1, 0., 0., 0., 0.), path)
        moving = c._intercept((1, 0., 0., 8., 0.), path)
        self.assertLess(moving[0], stationary[0])

    def test_endwall_cutback_names_a_receiver_on_both_wings(self):
        c = controller()
        options = []
        for sign in (-1, 1):
            p = (2, 33.3, sign*20., 0., 0.)
            friends = [(0, -47., 0., 0., 0.), p, (4, 43., sign*5., 0., 0.)]
            opponents = [(5, 47., -sign*20., 0., 0.), (6, -20., sign*10., 0., 0.)]
            option = c._endwall_link(p, 35., sign*20., 0., 0., friends, opponents)
            self.assertIsNotNone(option)
            self.assertEqual(option[3][0], 4)
            self.assertGreater(option[3][1], 35.)
            options.append(option)
        self.assertAlmostEqual(options[0][1][0][0], options[1][1][0][0])
        self.assertAlmostEqual(options[0][1][0][1], -options[1][1][0][1])

    def test_endwall_route_rejects_a_cooldown_body_on_first_leg(self):
        c = controller()
        c._enemy_cooldowns = {6: 999}
        p = (2, 33.3, 20., 0., 0.)
        friends = [(0, -47., 0., 0., 0.), p, (4, 43., 5., 0., 0.)]
        opponents = [(5, 47., -20., 0., 0.), (6, 36., 19.2, 0., 0.)]
        self.assertIsNone(c._endwall_link(p, 35., 20., 0., 0., friends, opponents))

if __name__ == '__main__':
    unittest.main()
