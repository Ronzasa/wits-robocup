"""Recovery, recycling and keeper commitment regressions for the second trial."""
from test_special_tactics import controller, observation, tuples
import unittest


class GoalkeeperR2Tests(unittest.TestCase):
    def active(self, obs):
        c = controller(KEEPER_POWER_PLAY=True)
        c._x_power_state = 'active'
        c._x_power_cover = 1
        c._x_power_deadline = obs.tick + 160
        return c

    def test_held_backward_recycle_does_not_reapply_entry_guards(self):
        obs = observation(ball=(8., 0., -9., 0.))
        c = self.active(obs)
        c._x_power_observe(obs, *tuples(obs))
        self.assertEqual(c._x_power_state, 'active')

    def test_verified_return_flight_is_retained_but_loose_ball_aborts(self):
        obs = observation(ball=(8., 0., -9., 0.), own=None, last=3)
        c = self.active(obs)
        c._receive_plan = (0, 3, obs.tick + 30)
        c._x_power_observe(obs, *tuples(obs))
        self.assertEqual(c._x_power_state, 'active')
        c._receive_plan = None
        c._x_power_observe(obs, *tuples(obs))
        self.assertEqual(c._x_power_state, 'recover')

    def test_opponent_touch_overrides_existing_return_plan(self):
        obs = observation(ball=(8., 0., -9., 0.), own=1, last=6)
        c = self.active(obs)
        c._receive_plan = (0, 3, obs.tick + 30)
        c._x_power_observe(obs, *tuples(obs))
        self.assertEqual(c._x_power_state, 'recover')

    def test_ball_behind_keeper_triggers_recovery_even_with_possession(self):
        obs = observation(ball=(-31., 0., 0., 0.))
        c = self.active(obs)
        c._x_power_observe(obs, *tuples(obs))
        self.assertEqual(c._x_power_state, 'recover')

    def test_braking_advanced_keeper_remains_exploitable(self):
        c = controller(GOALKEEPER_TRAP=True)
        c._x_prepare(observation(enemies=[(5, 32., 0., -4., 0.)]))
        c._x_prepare(observation(tick=1901, enemies=[(5, 31.9, 0., 0., 0.)]))
        self.assertTrue(c._x_rush)
        c._x_prepare(observation(tick=1902, enemies=[(5, 47., 0., 0., 0.)]))
        self.assertFalse(c._x_rush)

    def test_discontinuous_observation_does_not_confirm_stranded_keeper(self):
        c = controller(GOALKEEPER_TRAP=True)
        c._x_prepare(observation(enemies=[(5, 32., 0., -4., 0.)]))
        c._x_prepare(observation(tick=1910, enemies=[(5, 31.9, 0., 0., 0.)]))
        self.assertFalse(c._x_rush)
