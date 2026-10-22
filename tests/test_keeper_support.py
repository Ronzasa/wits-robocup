"""Keeper possession uses witnessed receptions and preserves champion priorities."""
import importlib.util
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from test_hybrid_planner import FIELD, ROOT
from test_match_tactics import observation


def controller():
    spec=importlib.util.spec_from_file_location('keeper_support',ROOT/'experiments/keeper-support/team.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    c=module.Guardiola2011()
    c._setup(FIELD)
    return c


BACK_F=[(0,-47.8,0.,0.,0.),(1,-28.3,10.,0.,0.),(2,-5.,-12.,0.,0.),
        (3,0.,15.,0.,0.),(4,9.,0.,0.,0.)]
BACK_O=[(5,47.,0.,0.,0.),(6,-26.,10.,0.,0.),(7,10.,-12.,0.,0.),
        (8,18.,10.,0.,0.),(9,0.,24.,0.,0.)]
WALL_B=(-39.299902638138846,1.689980400744183,0.,0.)
WALL_F=[(0,-40.99990263813885,1.689980400744183,0.,0.),(1,-15.,0.,0.,0.),
        (2,-28.897765496495637,18.06759430794709,0.,0.),(3,6.,-10.,0.,0.),(4,16.,0.,0.,0.)]
WALL_O=[(5,47.,0.,0.,0.),(6,-10.,3.,0.,0.),(7,3.,-12.,0.,0.),
        (8,18.,10.,0.,0.),(9,25.,24.,0.,0.)]


class KeeperSupportTests(unittest.TestCase):
    def back(self,c,f=None,o=None):
        return c._keeper_back_option(BACK_F[1],-30.,10.,0.,0.,f or BACK_F,o or BACK_O)

    def test_pressed_backpass_has_executable_first_touch(self):
        c=controller();option=self.back(c)
        self.assertIsNotNone(option)
        self.assertEqual(option[3][0],0)
        launch=c._carrier_contact(BACK_F[1],-30.,10.,*c._requested_velocity(0.,0.,option[1]),option[2])
        c.FIRST_TOUCH=True
        path=c._pass_path(launch,(-30.,10.),2.6)
        race=c._pass_race(BACK_F[0],path,BACK_O,.15,c._dt,2.6)
        self.assertIsNotNone(race)
        self.assertGreater(race[0][1][0],FIELD.my_goal[0]+2.)

    def test_backpass_declines_keeper_cooldown(self):
        c=controller();c._friend_cooldowns[0]=5
        self.assertIsNone(self.back(c))

    def test_backpass_requires_pressure(self):
        c=controller()
        self.assertIsNone(self.back(c,o=[BACK_O[0],*BACK_O[2:]]))

    def test_backpass_rejects_opponent_on_route(self):
        c=controller()
        self.assertIsNone(self.back(c,o=[*BACK_O,(10,-37.,5.,0.,0.)]))

    def test_keeper_cannot_receive_far_upfield(self):
        c=controller()
        self.assertIsNone(self.back(c,f=[(0,-37.,0.,0.,0.),*BACK_F[1:]]))

    def test_theoretical_eta_cannot_replace_failed_collection(self):
        c=controller()
        with patch.object(c,'_x_collect',return_value=None):
            self.assertIsNone(self.back(c))

    def test_wall_counter_has_real_postbounce_collection(self):
        c=controller();option=c._keeper_wall_option(WALL_F[0],*WALL_B,WALL_F,WALL_O)
        self.assertIsNotNone(option)
        launch=c._carrier_contact(WALL_F[0],*WALL_B[:2],*c._requested_velocity(*WALL_B[2:],option[1]),option[2])
        _,bounce=c._bank_path(*launch)
        self.assertIsNotNone(bounce)
        c.FIRST_TOUCH=True
        path=c._pass_path(launch,WALL_B[:2],2.6)
        race=c._pass_race(WALL_F[2],path,WALL_O,.15,bounce+c._dt,2.6)
        self.assertIsNotNone(race)
        self.assertGreater(race[0][0],bounce)

    def test_opponent_before_bounce_invalidates_wall_counter(self):
        c=controller()
        # Every route from this keeper must pass within the nearby presser's reach.
        opponents=[*WALL_O,(10,WALL_B[0]+1.,WALL_B[1],0.,0.)]
        self.assertIsNone(c._keeper_wall_option(WALL_F[0],*WALL_B,WALL_F,opponents))

    def test_wall_launch_count_is_bounded(self):
        c=controller()
        with patch.object(c,'_carrier_contact',wraps=c._carrier_contact) as contact:
            c._keeper_wall_option(WALL_F[0],*WALL_B,WALL_F,WALL_O)
        self.assertLessEqual(contact.call_count,4)

    def test_wall_counter_reflects_y_symmetrically(self):
        c=controller();options=[]
        for sign in (1.,-1.):
            flip=lambda rows:[(p[0],p[1],p[2]*sign,p[3],p[4]*sign) for p in rows]
            f,o=flip(WALL_F),flip(WALL_O)
            options.append(c._keeper_wall_option(f[0],WALL_B[0],WALL_B[1]*sign,0.,0.,f,o))
        self.assertTrue(all(x is not None for x in options))
        self.assertAlmostEqual(options[0][1][0][0],options[1][1][0][0])
        self.assertAlmostEqual(options[0][1][0][1],-options[1][1][0][1])

    def test_existing_progressive_pass_retains_priority(self):
        c=controller();kick=((1.,0.),.7)
        def fallback(*args):
            c._pass_plan=(3,-20.,10.)
            return kick
        with patch.object(c,'_keeper_base_kick',side_effect=fallback),patch.object(c,'_keeper_back_option') as candidate:
            self.assertEqual(c._choose_kick(BACK_F[1],-30.,10.,0.,0.,BACK_F,BACK_O),kick)
        candidate.assert_not_called()

    def test_accepted_backpass_is_followed_by_actual_keeper_command(self):
        c=controller()
        def fallback(*args):
            c._pass_plan=c._bank_plan=None;c._touch_movement=None
            return ((1.,0.),.2)
        with patch.object(c,'_keeper_base_kick',side_effect=fallback):
            action=c.act(observation(ball=(-30.,10.,0.,0.),friends=BACK_F,enemies=BACK_O,
                                     last=1,holder=1,kickers=(1,)))
        self.assertIsNotNone(c._receive_plan)
        self.assertEqual(c._receive_plan[0],0)
        self.assertIn('keeper_backpass',action.debug['titan_x'])
        self.assertEqual(tuple(action.players[0].movement),c._move(BACK_F[0],c._target(*c._receive_aim[1])))

    def test_opponent_touch_cancels_keeper_reception(self):
        c=controller()
        c._receive_plan=(0,1,140);c._x_reception=(0,1,140,(-42.,2.))
        c.act(observation(ball=(-30.,10.,-12.,0.),friends=BACK_F,enemies=BACK_O,
                          last=6,holder=6,kickers=()))
        self.assertIsNone(c._receive_plan)
        self.assertIsNone(c._x_reception)

    def test_disabled_features_leave_kick_and_actions_unchanged(self):
        spec=importlib.util.spec_from_file_location('keeper_baseline',ROOT/'my-team/team.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        c=controller();c.KEEPER_BACKPASS=c.KEEPER_WALL_COUNTER=False
        baseline=module.Guardiola2011()
        for tick in range(100,110):
            obs=observation(ball=(-30.,10.,0.,0.),friends=BACK_F,enemies=BACK_O,
                            tick=tick,last=1,holder=1,kickers=(1,))
            a,b=c.act(obs),baseline.act(obs)
            self.assertEqual(a,b)


if __name__=='__main__':
    unittest.main()
