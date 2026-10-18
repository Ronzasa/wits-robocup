"""Focused public-physics and protected-v10 regressions for TITAN-X."""
import ast
import hashlib
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace as S
import unittest
from unittest.mock import patch

from test_hybrid_planner import FIELD, ROOT

FLAGS = ('KEEPER_POWER_PLAY','GOALKEEPER_TRAP','PINBALL_SLINGSHOT','COOLDOWN_AMBUSH')

def load(name):
    path = ROOT/name/'team.py'
    spec = importlib.util.spec_from_file_location('special_'+name.replace('/','_'),path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

M = load('experiments/titan-x')
BASE = load('my-team')

def controller(**flags):
    c = M.Guardiola2011()
    c._setup(FIELD)
    for flag,value in flags.items():
        setattr(c,flag,value)
    return c

def observation(tick=1900,score=(0,1),ball=(25.,0.,0.,0.),own=0,last=3,
                friends=None,enemies=None,cooldowns=None):
    friends = friends or [(0,-25.,0.,0.,0.),(1,-28.,0.,0.,0.),(2,10.,-8.,0.,0.),
                          (3,23.3,0.,0.,0.),(4,35.,6.,0.,0.)]
    enemies = enemies or [(5,47.,0.,0.,0.),(6,34.,18.,0.,0.),(7,8.,22.,0.,0.),
                          (8,10.,-23.,0.,0.),(9,40.,-19.,0.,0.)]
    cooldowns = cooldowns or {}
    def player(p):
        return S(id=p[0],position=p[1:3],velocity=p[3:],kick_cooldown_ticks=cooldowns.get(p[0],0))
    return S(field=FIELD,tick=tick,max_ticks=2400,time_remaining=1-tick/2400,
        score=score,my_players=[player(p) for p in friends],opponents=[player(p) for p in enemies],
        ball=S(position=ball[:2],velocity=ball[2:],controlling_team=own,
               controlling_player=last if own is not None else None,last_touch=last),
        can_kick=lambda pid:cooldowns.get(pid,0)==0 and next((math.dist(p[1:3],ball[:2])<=2.2 for p in friends if p[0]==pid),False))

def tuples(obs):
    return ([(p.id,*p.position,*p.velocity) for p in obs.my_players],
            [(p.id,*p.position,*p.velocity) for p in obs.opponents])

class SpecialTacticsTests(unittest.TestCase):
    def test_champion_unchanged(self):
        self.assertEqual(hashlib.sha256((ROOT/'my-team/team.py').read_bytes()).hexdigest(),
                         '5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6')

    def test_four_standalone_flags_and_one_controller(self):
        for folder,flag in zip(('power','trap','pinball','ambush'),FLAGS):
            path=ROOT/('experiments/titan-x-'+folder)/'team.py'
            module=load('experiments/titan-x-'+folder)
            c=module.Guardiola2011()
            self.assertEqual([k for k in FLAGS if getattr(c,k)],[flag])
            tree=ast.parse(path.read_text())
            self.assertEqual(len([n for n in tree.body if isinstance(n,ast.ClassDef)]),1)
            self.assertEqual({n.names[0].name for n in tree.body if isinstance(n,ast.Import)},{'math'})

    def test_default_flags_all_false(self):
        self.assertFalse(any(getattr(controller(),f) for f in FLAGS))

    def test_disabled_manager_preserves_commands_and_debug(self):
        a=BASE.Guardiola2011();b=controller()
        for tick in range(0,40):
            obs=observation(tick=tick,ball=(12.+tick*.1,5.,4.,-1.),own=0)
            aa=a.act(obs);bb=b.act(obs)
            self.assertEqual(aa.players,bb.players)
            self.assertEqual(aa.debug,bb.debug)
            self.assertEqual(a._receive_plan,b._receive_plan)

    def test_power_activation_and_immediate_recovery_on_loss(self):
        c=controller(KEEPER_POWER_PLAY=True);obs=observation()
        friends,enemies=tuples(obs)
        c._x_power_observe(obs,friends,enemies)
        self.assertEqual(c._x_power_state,'advance')
        self.assertEqual(c._x_power_cover,1)
        obs.ball.controlling_team=1
        c._x_power_observe(obs,friends,enemies)
        self.assertEqual(c._x_power_state,'recover')

    def test_power_respects_score_window_and_danger(self):
        for obs in (observation(score=(1,1)),observation(tick=100),
                    observation(ball=(25.,0.,-12.,0.)),observation(own=1)):
            c=controller(KEEPER_POWER_PLAY=True)
            c._x_power_observe(obs,*tuples(obs))
            self.assertEqual(c._x_power_state,'idle')

    def test_power_does_not_activate_without_recovery_and_cover_time(self):
        c=controller(KEEPER_POWER_PLAY=True)
        obs=observation(friends=[(0,-49.,-20.,0.,0.),(1,24.,23.,0.,0.),(2,25.,-20.,0.,0.),
                                 (3,23.3,0.,0.,0.),(4,35.,6.,0.,0.)])
        c._x_power_observe(obs,*tuples(obs))
        self.assertEqual(c._x_power_state,'idle')

    def test_power_recovery_has_cooldown_and_cannot_reactivate_immediately(self):
        c=controller(KEEPER_POWER_PLAY=True);c._x_power_state='recover'
        obs=observation(friends=[(0,-47.,0.,0.,0.),(1,-28.,0.,0.,0.)])
        c._x_power_observe(obs,*tuples(obs))
        self.assertEqual(c._x_power_state,'cooldown')
        c._x_power_observe(obs,*tuples(obs))
        self.assertEqual(c._x_power_state,'cooldown')

    def test_power_recovery_preserves_base_goalkeeper_command(self):
        c=controller(KEEPER_POWER_PLAY=True);base=BASE.Guardiola2011()
        obs=observation(own=1,last=6,ball=(-10.,4.,-15.,-1.))
        c._x_last_tick=obs.tick-1;c._x_power_state='recover'
        expected=base.act(obs).players[0]
        self.assertEqual(c.act(obs).players[0],expected)

    def test_goalkeeper_rush_requires_observed_commitment(self):
        c=controller(GOALKEEPER_TRAP=True)
        obs=observation(enemies=[(5,38.,0.,-4.,0.)])
        c._x_prepare(obs)
        self.assertFalse(c._x_rush)
        obs=observation(tick=1901,enemies=[(5,37.8,0.,-4.,0.)])
        c._x_prepare(obs)
        self.assertTrue(c._x_rush)
        obs=observation(tick=1902,enemies=[(5,47.,0.,0.,0.)])
        c._x_prepare(obs)
        self.assertFalse(c._x_rush)

    def test_trap_aborts_when_keeper_stays_home(self):
        c=controller(GOALKEEPER_TRAP=True)
        self.assertIsNone(c._x_trap((3,23.3,0.,0.,0.),25.,0.,0.,0.,[],[(5,47.,0.,0.,0.)]))

    def test_trap_has_a_verified_finish_beyond_rushing_keeper(self):
        c=controller(GOALKEEPER_TRAP=True);c._x_rush=True
        bx,by=28.72259926973003,-8.927497399941494
        p=(3,bx-1.7,by,0.,0.)
        q=(4,40.072594324986625,-3.094850453997598,3.981841673630939,1.0574074182965782)
        enemies=[(5,bx+4.,-by*.5,-4.,0.)]
        result=c._x_trap(p,bx,by,0.,0.,[p,q],enemies)
        self.assertIsNotNone(result)
        self.assertGreater(result[3][1],enemies[0][1]+1.)

    def test_pinball_collects_after_side_rebound_and_rejects_a_blocker(self):
        c=controller(PINBALL_SLINGSHOT=True)
        bx,by,vx,vy=23.201874395893917,27.526110358188596,2.6802042757707083,5.869036502232929
        p=(3,bx-1.7,by,0.,0.)
        q=(4,45.770700777515344,9.753033796579489,4.275890015376666,-2.8829813705366436)
        result=c._x_pinball(p,bx,by,vx,vy,[p,q],[])
        self.assertIsNotNone(result)
        launch=c._carrier_contact(p,bx,by,*c._requested_velocity(vx,vy,result[1]),result[2])
        _,bounce=c._bank_path(*launch)
        self.assertIsNotNone(bounce)
        self.assertGreater(result[3][1],bx+4.)
        self.assertLess(abs(result[3][2]),13.)
        blocker=(6,bx+.6,by+1.8,0.,0.)
        c._enemy_cooldowns={6:99}
        self.assertIsNone(c._x_pinball(p,bx,by,vx,vy,[p,q],[blocker]))

    def test_ambush_collects_before_cooldown_expires_and_cancels_on_escape(self):
        c=controller(COOLDOWN_AMBUSH=True)
        bx,by,vx,vy=-6.158521230904781,6.204034842977585,10.587649807493246,1.093175752114222
        q=(2,-3.775057506971322,6.208198669605159,-1.6678517588552666,.18245532478266657)
        obs=observation(own=None,last=6,ball=(bx,by,vx,vy),cooldowns={6:4},
                        friends=[(0,-47.,0.,0.,0.),(1,bx-13.,0.,0.,0.),q],
                        enemies=[(5,47.,0.,0.,0.),(6,bx-2.,by,0.,0.)])
        c._x_prepare(obs);c._shape_cover_id=1
        actions=M.TeamAction({p.id:M.PlayerAction() for p in obs.my_players},debug={})
        c._x_ambush(obs,*tuples(obs),actions,None)
        self.assertIn('ambush_challenge',c._x_events)
        self.assertEqual(actions.players[0],M.PlayerAction())
        obs.ball.position=(bx+20.,by);c._x_events=[]
        c._x_ambush(obs,*tuples(obs),actions,None)
        self.assertEqual(c._x_events,[])

    def test_unrelated_v10_physics_and_safeguards_have_identical_asts(self):
        def methods(path):
            tree=ast.parse(path.read_text())
            cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
            return {n.name:ast.dump(n,include_attributes=False) for n in cls.body if isinstance(n,ast.FunctionDef)}
        base=methods(ROOT/'my-team/team.py');new=methods(ROOT/'experiments/titan-x/team.py')
        for method in ('_move','_intercept','_verified_intercept','_pass_race','_receiver_rollout',
                       '_shot_option','_keeper_reaches','_cover_shape','_counterpress_targets','_carrier_contact'):
            self.assertEqual(base[method],new[method],method)

    def test_no_new_tactic_displaces_a_v10_shot(self):
        c=controller(GOALKEEPER_TRAP=True,PINBALL_SLINGSHOT=True,KEEPER_POWER_PLAY=True)
        obs=observation(ball=(43.,0.,0.,0.),friends=[(0,-47.,0.,0.,0.),(3,41.3,0.,0.,0.)],
                        enemies=[(5,30.,20.,0.,0.)])
        friends,enemies=tuples(obs);c._x_prepare(obs)
        with patch.object(c,'_x_trap',side_effect=AssertionError('must preserve shot')):
            c._choose_kick(friends[1],43.,0.,0.,0.,friends,enemies)
        self.assertIsNone(c._x_proposal)

    def test_first_touch_validation_restores_v10_flags(self):
        c=controller();p=(3,-1.7,0.,0.,0.);q=(4,10.,0.,0.,0.)
        option=c._x_direct(p,0.,0.,0.,0.,q,[p,q],[(5,47.,25.,0.,0.)],10.,0.,14.)
        self.assertIsNotNone(option)
        self.assertFalse(c.FIRST_TOUCH)
        self.assertEqual(option[3][0],4)

    def test_cooldown_body_block_still_rejects_tactical_pass(self):
        c=controller();c._enemy_cooldowns={6:99}
        p=(3,-1.7,0.,0.,0.);q=(4,10.,0.,0.,0.)
        self.assertIsNone(c._x_direct(p,0.,0.,0.,0.,q,[p,q],[(6,2.,0.,0.,0.)],10.,0.,14.))

    def test_teammate_collision_rejects_new_trajectory(self):
        c=controller();p=(3,-1.7,0.,0.,0.);q=(4,12.,0.,0.,0.)
        self.assertIsNone(c._x_direct(p,0.,0.,0.,0.,q,[p,q,(2,4.,0.,0.,0.)],[],12.,0.,14.))

    def test_unreachable_receiver_has_no_eta_fallback(self):
        c=controller();p=(3,-1.7,0.,0.,0.);q=(4,-40.,-25.,-8.,0.)
        self.assertIsNone(c._x_direct(p,0.,0.,0.,0.,q,[p,q],[],20.,10.,22.))

    def test_ambush_never_removes_cover_or_goalkeeper(self):
        c=controller(COOLDOWN_AMBUSH=True)
        obs=observation(ball=(0.,0.,8.,0.),own=1,last=6,cooldowns={6:4},
                        friends=[(0,-47.,0.,0.,0.),(1,0.,0.,0.,0.),(2,20.,10.,0.,0.)],
                        enemies=[(5,47.,0.,0.,0.),(6,-2.,0.,0.,0.)])
        c._x_prepare(obs);c._shape_cover_id=1
        actions=M.TeamAction({p.id:M.PlayerAction() for p in obs.my_players},debug={})
        original=dict(actions.players)
        c._x_ambush(obs,*tuples(obs),actions,None)
        self.assertEqual(actions.players,original)

    def test_ambush_cancels_if_another_opponent_can_kick(self):
        c=controller(COOLDOWN_AMBUSH=True)
        obs=observation(ball=(0.,0.,8.,0.),own=1,last=6,cooldowns={6:4},
            friends=[(0,-47.,0.,0.,0.),(1,-12.,0.,0.,0.),(2,1.9,0.,0.,0.)],
            enemies=[(5,47.,0.,0.,0.),(6,-2.,0.,0.,0.),(7,0.,1.8,0.,0.)])
        c._x_prepare(obs);c._shape_cover_id=1
        actions=M.TeamAction({p.id:M.PlayerAction() for p in obs.my_players},debug={})
        c._x_ambush(obs,*tuples(obs),actions,None)
        self.assertNotIn('ambush_challenge',c._x_events)

    def test_enabled_actions_are_finite_and_bounded(self):
        for flag in FLAGS:
            c=controller(**{flag:True})
            for tick in range(1896,1905):
                actions=c.act(observation(tick=tick))
                for action in actions.players.values():
                    self.assertTrue(all(math.isfinite(v) for v in action.movement))
                    self.assertLessEqual(math.hypot(*action.movement),1.00000001)
                    self.assertTrue(0. <= action.kick_power <= 1.)

    def test_tactical_launch_issues_the_first_touch_checked_receiver_command(self):
        c=controller(GOALKEEPER_TRAP=True)
        bx,by=28.72259926973003,-8.927497399941494
        p=(3,bx-1.7,by,0.,0.)
        q=(4,40.072594324986625,-3.094850453997598,3.981841673630939,1.0574074182965782)
        enemies=[(5,bx+4.,-by*.5,-4.,0.)]
        c._x_rush=True
        option=c._x_trap(p,bx,by,0.,0.,[p,q],enemies)
        self.assertIsNotNone(option)
        obs=observation(ball=(bx,by,0.,0.),friends=[(0,-47.,0.,0.,0.),p,q],enemies=enemies)
        # A vertical clearance is the fallback; force the already physically
        # checked special option through the real v10 launch/planning path.
        with patch.object(c,'_v10_choose_kick',return_value=((0.,1.),1.)),patch.object(c,'_x_trap',return_value=option):
            actions=c.act(obs)
        self.assertIsNotNone(c._receive_plan)
        self.assertEqual(c._receive_plan[0],q[0])
        self.assertEqual(actions.players[q[0]].movement,c._move(q,c._target(*option[4])))
        self.assertIn('trap_pass',c._x_events)

    def test_reset_clears_special_reception_and_power_state(self):
        c=controller();c._x_power_state='active';c._x_reception=(4,3,2000,(38.,0.))
        c._x_keeper_history=(1900,30.,0.)
        c.reset(19)
        self.assertEqual(c._x_power_state,'idle')
        self.assertIsNone(c._x_reception)
        self.assertIsNone(c._x_keeper_history)

if __name__ == '__main__':
    unittest.main()
