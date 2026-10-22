"""Executable collection and physics regressions for the isolated tactics."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace as S
import unittest

from test_hybrid_planner import FIELD, ROOT
from soccer import PlayerAction, SoccerEnv, TeamAction


def load(name):
    p=ROOT/'champions/v10.0/team.py' if name=='v10' else ROOT/'experiments'/('physics-'+name)/'team.py'
    spec=importlib.util.spec_from_file_location('physics_test_'+name,p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    c=m.Guardiola2011();c._setup(FIELD)
    return c


def case(name):
    return json.loads((ROOT/'tests/fixtures/physics-synthetic-cases.json').read_text())[name]


def setup(name):
    row=case(name);c=load(name)
    f=[tuple(p) for p in row['friends']];e=[tuple(p) for p in row['opponents']]
    c._friend_cooldowns={p[0]:0 for p in f};c._enemy_cooldowns={p[0]:0 for p in e}
    c._shape_cover_id=1;c._chaser=3;c._physics_targets={p[0]:p[1:3] for p in f}
    bx,by,vx,vy=row['ball']
    o=S(field=FIELD,tick=100,max_ticks=2400,score=(0,0),events=[],
        ball=S(position=(bx,by),velocity=(vx,vy),last_touch=6,controlling_player=None,
               controlling_team=None,height=0.,vertical_velocity=0.),can_kick=lambda pid:False)
    return c,row,f,e,o


class PhysicsTacticsTests(unittest.TestCase):
    def test_frozen_v10_and_active_champion_remain_exact(self):
        for path,sha in [('champions/v10.0/team.py','5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6'),
                         ('my-team/team.py','553bcd85a537d57a43c16e4498fab402fbbabb940e15cb8c5aa110d4c6fa9a5e')]:
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),sha)

    def test_all_off_preserves_v10_commands_on_real_native_observations(self):
        a,b=load('v10'),load('off')
        with SoccerEnv(max_ticks=160) as env:
            env.use_baseline(1,'balanced');observations=env.reset(seed=1001)
            while not env.finished:
                obs=observations['team_a'];aa,bb=a.act(obs),b.act(obs)
                self.assertEqual(aa.players,bb.players)
                self.assertEqual(aa.debug,bb.debug)
                self.assertEqual(a._receive_plan,b._receive_plan)
                observations,_=env.step({'team_a':aa})

    def test_motion_capture_preserves_original_dense_positions(self):
        a,b=load('v10'),load('off')
        for launch in ((0.,27.,5.,20.),(40.,20.,22.,5.),(-43.,18.,-20.,10.),(0.,0.,0.,0.)):
            expected=a._pass_path(launch,until=2.)
            actual=b._pass_path(launch,until=2.,capture_motion=True)
            self.assertEqual(expected,actual)
            self.assertEqual(len(actual),len(b._last_pass_motion[1]))

    def test_wall_window_distinguishes_goals_from_solid_walls(self):
        c=load('ambush')
        self.assertIsNone(c._physics_wall((47.,0.,20.,0.)))
        self.assertEqual(c._physics_wall((47.,20.,20.,0.))[1],'x')
        self.assertEqual(c._physics_wall((0.,27.,0.,20.))[1],'y')
        self.assertEqual(c._physics_wall((0.,-27.,0.,-20.))[1],'y')

    def test_ambush_issues_the_physically_verified_command(self):
        c,row,f,e,o=setup('ambush');a=TeamAction()
        c._physics_ambush_move(o,a,f,e)
        self.assertTrue(c._physics_events)
        event=c._physics_events[0]
        self.assertGreater(event['arrival_in'],event['bounce_in'])
        p=next(p for p in f if p[0]==event['player'])
        self.assertEqual(a.players[p[0]].movement,c._move(p,event['aim']))
        self.assertNotIn(p[0],(0,1))

    def test_ambush_rejects_own_balls_airborne_balls_and_protected_restarts(self):
        for mode in ('own','air','restart'):
            c,row,f,e,o=setup('ambush')
            if mode=='own':o.ball.last_touch=3
            if mode=='air':o.ball.height=.5
            if mode=='restart':c._restart_until=110;c._restart_owner=1
            a=TeamAction();c._physics_ambush_move(o,a,f,e)
            self.assertFalse(a.players)

    def test_ambush_preserves_a_verified_receiver(self):
        c,row,f,e,o=setup('ambush');a=TeamAction()
        c._physics_ambush_move(o,a,f,e);pid=c._physics_events[0]['player']
        c._receive_plan=(pid,2,130);c._physics_events=[];a=TeamAction()
        c._physics_ambush_move(o,a,f,e)
        self.assertNotIn(pid,a.players)

    def test_postwall_race_rejects_an_opponent_at_the_prebounce_ball(self):
        c,row,f,e,o=setup('ambush');a=TeamAction()
        e=[(6,*o.ball.position,0.,0.)]
        c._enemy_cooldowns={6:0}
        c._physics_ambush_move(o,a,f,e)
        self.assertFalse(a.players)

    def test_wall_brake_has_a_real_slow_postwall_reception(self):
        c,row,f,e,o=setup('wall-brake');p=next(p for p in f if p[0]==3)
        option=c._physics_wall_brake(p,*row['ball'],f,e)
        self.assertIsNotNone(option)
        self.assertGreater(option[6],option[5])
        self.assertLessEqual(option[7],9.)
        self.assertLess(option[3][1],row['ball'][0]+4.)

    def test_wall_brake_first_tick_does_not_cancel_on_its_own_passer(self):
        c,row,f,e,o=setup('wall-brake');p=next(p for p in f if p[0]==3)
        option=c._physics_wall_brake(p,*row['ball'],f,e);rid=option[3][0]
        c._physics_pending={'kind':'wall-brake','phase':'launch','player':3,'recipient':rid,
            'aim':option[4],'bounce_in':option[5],'arrival_in':option[6],'speed':option[7]}
        o.can_kick=lambda pid:pid==3
        a=TeamAction();a.set(3,PlayerAction(movement=option[2],kick_direction=option[1][0],kick_power=option[1][1]))
        c._physics_follow(o,a,f,e)
        self.assertIsNotNone(c._physics_receive)
        self.assertIn(rid,a.players)

    def test_rebound_shot_uses_a_wall_before_reaching_the_goal(self):
        c,row,f,e,o=setup('rebound-shot');p=next(p for p in f if p[0]==3)
        option=c._physics_rebound_shot(p,*row['ball'],f,e)
        self.assertIsNotNone(option)
        self.assertLess(option[4],option[5])
        self.assertGreaterEqual(option[6],8.)

    def test_rebound_shot_rejects_a_verified_blocker(self):
        c,row,f,e,o=setup('rebound-shot');p=next(p for p in f if p[0]==3)
        blocker=(6,*o.ball.position,0.,0.)
        self.assertIsNone(c._physics_rebound_shot(p,*row['ball'],[p],[blocker]))

    def test_existing_physics_and_other_tactics_are_not_duplicated_or_changed(self):
        def methods(path):
            cls=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef))
            return {n.name:ast.dump(n,include_attributes=False) for n in cls.body if isinstance(n,ast.FunctionDef)}
        old=methods(ROOT/'champions/v10.0/team.py')
        for name in ('ambush','wall-brake','rebound-shot'):
            new=methods(ROOT/'experiments'/('physics-'+name)/'team.py')
            for method in ('_trajectory','_move','_receiver_rollout','_verified_intercept','_pass_race',
                           '_carrier_contact','_shot_option','_bank_release','_endwall_link','_goal_path',
                           '_keeper_reaches','_cover_shape'):
                self.assertEqual(old[method],new[method],(name,method))


if __name__=='__main__':unittest.main()
