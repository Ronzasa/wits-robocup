"""Focused public-input reproductions for the uploaded wall postprocessor.

Synthetic observations isolate action arbitration. Native matches, intake and
runtime are evaluated separately; these fixtures are not native match results.
"""
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT/'student-sdk'))
from soccer import SoccerEnv, TeamAction, PlayerAction
from soccer.helpers import load_controller


class WallArbitration(unittest.TestCase):
    def setUp(self):
        self.old=load_controller(str(ROOT/'experiments/champion-candidate-review/uploaded/team.py'))
        self.guarded=load_controller(str(ROOT/'experiments/champion-candidate-review/guarded-wall-break/team.py'))
        self.unlocked=load_controller(str(ROOT/'experiments/champion-candidate-review/no-trailing-wall/team.py'))
        with SoccerEnv(config_path=str(ROOT/'configs/default.toml')) as env:
            self.field=env.field
        for c in (self.old,self.guarded,self.unlocked):
            c._setup(self.field)
            c._chaser=2
            c._shape_cover_id=1

    def observation(self, speed=0.0, wide_gap=False):
        def player(i,x,y):
            return NS(id=i,position=(x,y),velocity=(0.,0.),kick_cooldown_ticks=0)
        friends=[player(0,-49,0),player(1,8,-5),player(2,18.5,0),
                 player(3,15,6),player(4,12,-6)]
        ys=(-6.,-2.5,2.5,6.) if wide_gap else (-5.6,-2.8,0.,2.8,5.6)
        enemies=[player(i+5,49.,y) for i,y in enumerate(ys)]
        if wide_gap:enemies.append(player(9,-20.,20.))
        return NS(score=(0,0),time_remaining=.8,my_goal=self.field.my_goal,
                  opponent_goal=self.field.opponent_goal,field=self.field,
                  my_players=friends,opponents=enemies,
                  ball=NS(position=(20.,0.),velocity=(speed,0.),controlling_team=0),
                  can_kick=lambda pid:pid==2)

    def actions(self):
        return TeamAction({i:PlayerAction(movement=(0.,-1.)) for i in range(5)})

    def test_trailing_wall_bypasses_normal_play_but_single_flag_fix_does_not(self):
        obs=self.observation();obs.score=(0,2)
        for c,expected in ((self.old,'wall'),(self.unlocked,'normal')):
            c._act_normal=lambda obs:TeamAction(debug={'chosen':'normal'})
            c._lock_wall=lambda obs:TeamAction(debug={'chosen':'wall'})
            self.assertEqual(c.act(obs).debug['chosen'],expected)

    def test_requested_lead_lock_is_preserved_in_both_independent_changes(self):
        obs=self.observation();obs.score=(1,0)
        for c in (self.old,self.guarded,self.unlocked):
            c._act_normal=lambda obs:TeamAction(debug={'chosen':'normal'})
            c._lock_wall=lambda obs:TeamAction(debug={'chosen':'wall'})
            self.assertEqual(c.act(obs).debug['chosen'],'wall')

    def test_wall_break_must_not_retarget_a_live_receiver(self):
        obs=self.observation()
        for c in (self.old,self.guarded):c._receive_plan=(3,2,100)
        original=self.actions();fixed=self.actions()
        self.old._wall_break(obs,original);self.guarded._wall_break(obs,fixed)
        self.assertNotEqual(original.players[3].movement,(0.,-1.))
        self.assertEqual(fixed.players[3].movement,(0.,-1.))

    def test_cover_assignment_must_survive_wall_pressure(self):
        obs=self.observation();original=self.actions();fixed=self.actions()
        self.old._wall_break(obs,original);self.guarded._wall_break(obs,fixed)
        self.assertNotEqual(original.players[1].movement,(0.,-1.))
        self.assertEqual(fixed.players[1].movement,(0.,-1.))

    def test_wall_pressure_must_not_cancel_an_existing_kick(self):
        obs=self.observation();original=self.actions();fixed=self.actions()
        kick=PlayerAction(movement=(0.,-1.),kick_direction=(1.,0.),kick_power=.2)
        original.set(3,kick);fixed.set(3,kick)
        self.old._wall_break(obs,original);self.guarded._wall_break(obs,fixed)
        self.assertIsNone(original.players[3].kick_direction)
        self.assertIs(fixed.players[3],kick)

    def test_geometric_gap_does_not_prove_a_goal_against_ball_momentum(self):
        obs=self.observation(speed=-30.,wide_gap=True)
        original=self.actions();fixed=self.actions()
        self.old._wall_break(obs,original);self.guarded._wall_break(obs,fixed)
        oldkick=original.players[2]
        self.assertIsNotNone(oldkick.kick_direction)
        velocity=self.old._requested_velocity(-30.,0.,(oldkick.kick_direction,oldkick.kick_power))
        self.assertLess(velocity[0],0.)
        self.assertIsNone(self.old._goal_path((20.,0.,*velocity)))
        self.assertIsNone(fixed.players[2].kick_direction)


if __name__=='__main__':unittest.main()
