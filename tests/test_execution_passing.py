"""Executable reception cases, separate from the unchanged v9.1 champion."""
import ast
import importlib.util
import json
import math
import os
from pathlib import Path
from types import SimpleNamespace as S
import unittest
from unittest.mock import patch

from test_hybrid_planner import FIELD,ROOT

TEAM=Path(os.environ.get('TITAN10B_TEAM_PATH',ROOT/'experiments/titan-10b/team.py'))
spec=importlib.util.spec_from_file_location('execution_passing_candidate',TEAM)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def controller(**flags):
    c=module.Guardiola2011();c._setup(FIELD)
    for key,val in flags.items():setattr(c,key,val)
    return c

def cases():
    return json.loads((Path(__file__).parent/'fixtures/execution-reception-cases.json').read_text())['cases']

def setup_case(c,x):
    row=x['start'];rid=row['plan_after'][0]
    c._friend_cooldowns={int(k):v for k,v in row['friend_cooldowns'].items()}
    c._enemy_cooldowns={int(k):v for k,v in row['enemy_cooldowns'].items()}
    receiver=next(p for p in row['friends'] if p[0]==rid)
    path=c._pass_path(tuple(x['launch']),tuple(row['ball'][:2]),2.6)
    return row,receiver,path

def observation(row,kickers=None):
    def player(p,cd):return S(id=p[0],position=p[1:3],velocity=p[3:],kick_cooldown_ticks=cd.get(str(p[0]),cd.get(p[0],0)))
    friends=[player(p,row['friend_cooldowns']) for p in row['friends']]
    enemies=[player(p,row['enemy_cooldowns']) for p in row['opponents']]
    can=lambda pid:next(p for p in friends if p.id==pid).kick_cooldown_ticks==0 and math.dist(next(p for p in friends if p.id==pid).position,row['ball'][:2])<=2.2
    return S(field=FIELD,tick=row['tick'],score=tuple(row['score']),my_players=friends,opponents=enemies,
             can_kick=can if kickers is None else lambda pid:pid in kickers,
             ball=S(position=row['ball'][:2],velocity=row['ball'][2:],last_touch=row['last_touch'],
                    controlling_player=row['holder'],controlling_team=None if row['holder'] is None else int(row['holder']>=5)))


class ExecutionPassingTests(unittest.TestCase):
    def test_reproduced_native_miss_is_real_and_not_a_sampling_fallback(self):
        data=json.loads((Path(__file__).parent/'fixtures/execution-reception-cases.json').read_text())
        self.assertTrue(data['primary_reproduced_twice'])
        self.assertEqual(data['primary_second_match_reliability'],[[0,0],[0,0]])
        x=data['cases'][0];c=controller();row,p,path=setup_case(c,x)
        old=c._verified_intercept(p,path,after=.05,until=2.6)
        self.assertAlmostEqual(old[0],.4)
        self.assertGreater(x['minimum_gap_through_prediction'],2.35)
        self.assertEqual(x['outcome'],'unresolved')

    def test_native_counterfactual_collects_with_only_the_receivers_run_changed(self):
        data=json.loads((Path(__file__).parent/'fixtures/execution-reception-cases.json').read_text())
        proof=data['execution_counterfactual']
        self.assertEqual(proof['collected_tick'],1507)
        self.assertTrue(all(s['policy_errors']==s['policy_timeouts']==0 for s in proof['result']['stats']))
        first=next(x for x in proof['trace'] if x['last_touch']==2)
        self.assertEqual(first['tick'],1507)

    def test_execute_before_moving_gate_cannot_be_replaced_with_native_range(self):
        c=controller()
        # It can reach the pre-step ball after moving, but act() would not
        # request a kick because the observation is initially out of range.
        p=(4,0.,0.,8.,0.);path=[(0.,2.4,0.),(.05,3.5,0.)]
        self.assertIsNotNone(c._verified_intercept(p,path,after=.05))
        self.assertIsNone(c._receiver_rollout(p,path,(3.5,0.),after=.05))

    def test_later_aim_recovers_the_reproduced_moving_receiver(self):
        x=cases()[0];c=controller(EXECUTE_RECEIVER=True);row,p,path=setup_case(c,x)
        route=c._receiver_route(p,path,row['opponents'],.05,2.6)
        self.assertIsNotNone(route)
        self.assertAlmostEqual(route[0],.5)
        self.assertGreater(route[2][0],x['predicted'][1][0]+1.)
        self.assertIsNotNone(c._pass_race(p,path,row['opponents'],after=.05,until=2.6))

    def test_uncollectable_theoretical_link_is_declined(self):
        x=next(x for x in cases() if x['start']['tick']==60)
        c=controller(EXECUTE_RECEIVER=True);row,p,path=setup_case(c,x)
        self.assertIsNotNone(c._verified_intercept(p,path,after=.05,until=2.6))
        self.assertIsNone(c._receiver_route(p,path,row['opponents'],.05,2.6))

    def test_predicted_legal_kick_obeys_cooldown_and_conservative_range(self):
        c=controller();p=(4,0.,0.,0.,0.)
        path=[(0.,1.9,0.),(.05,3.2,0.)]
        self.assertEqual(c._receiver_rollout(p,path,(3.2,0.))[4],'kick')
        self.assertIsNone(c._receiver_rollout(p,path,(3.2,0.),cooldown=2))

    def test_a_new_pass_cannot_assign_the_carriers_first_tick_kick_to_receiver(self):
        c=controller();p=(4,0.,0.,0.,0.)
        path=[(0.,1.9,0.),(.05,3.2,0.)]
        self.assertIsNone(c._receiver_rollout(p,path,(3.2,0.),after=.05))

    def test_actual_launch_commands_use_the_rollout_aim(self):
        x=cases()[0];c=controller(EXECUTE_RECEIVER=True);row,p,path=setup_case(c,x)
        route=c._receiver_route(p,path,row['opponents'],.05,2.6)
        rid,pid,_=row['plan_after'];action=row['actions'][str(pid)]
        def choose(*args):
            c._pass_plan=(rid,*x['predicted'][1]);c._bank_plan=None
            c._touch_movement=tuple(action['movement'])
            return tuple(action['kick_direction']),action['kick_power']
        with patch.object(c,'_choose_kick',side_effect=choose):a=c.act(observation(row))
        expected=c._move(p,c._target(*route[2]))
        # The captured native field stores friction in single precision;
        # FIELD uses its documented decimal value when rebuilding the kick.
        for actual,wanted in zip(a.players[rid].movement,expected):
            self.assertAlmostEqual(actual,wanted,delta=1e-6)
        self.assertNotEqual(tuple(a.players[rid].movement),tuple(row['actions'][str(rid)]['movement']))

    def test_live_receiver_issues_pure_predicted_movement_after_cover(self):
        x=cases()[0];row=x['trace'][0];rid,pid,expiry=row['plan_after']
        p=next(p for p in row['friends'] if p[0]==rid);point=(-27.,-10.)
        c=controller(FOLLOW_RECEIVER=True);c._receive_plan=(rid,pid,expiry)
        with patch.object(c,'_pass_race',return_value=((.5,point),math.inf)):
            a=c.act(observation(row,kickers=()))
        self.assertEqual(tuple(a.players[rid].movement),c._move(p,c._target(*point)))

    def test_following_a_receiver_does_not_change_other_players_commands(self):
        x=cases()[0];row=x['trace'][0];rid,pid,expiry=row['plan_after'];aa=[]
        for enabled in (False,True):
            c=controller(FOLLOW_RECEIVER=enabled);c._receive_plan=(rid,pid,expiry)
            with patch.object(c,'_pass_race',return_value=((.5,(-27.,-10.)),math.inf)):
                aa.append(c.act(observation(row,kickers=())))
        for p in row['friends']:
            if p[0]!=rid:self.assertEqual(aa[0].players[p[0]],aa[1].players[p[0]])

    def test_actual_first_command_cannot_claim_an_unrequested_kick(self):
        c=module.Guardiola2011();c._setup(FIELD)
        p=(4,0.,0.,0.,0.);path=[(0.,1.9,0.),(.05,3.2,0.)]
        self.assertIsNotNone(c._receiver_rollout(p,path,(3.2,0.)))
        self.assertIsNone(c._receiver_rollout(p,path,(3.2,0.),first_move=(-1.,0.)))

    def test_post_role_validation_cancels_plan_without_changing_commands(self):
        x=cases()[0];row=x['trace'][0];rid,pid,expiry=row['plan_after']
        c=module.Guardiola2011();c._setup(FIELD);c._receive_plan=(rid,pid,expiry)
        actual=[]
        def verify(*args,**kwargs):
            if kwargs.get('first_move') is not None:
                actual.append(tuple(kwargs['first_move']));return None
            return (.5,(-27.,-10.)),math.inf
        with patch.object(c,'_pass_race',side_effect=verify):a=c.act(observation(row,kickers=()))
        self.assertEqual(actual,[tuple(a.players[rid].movement)])
        self.assertIsNone(c._receive_plan)
        sp=importlib.util.spec_from_file_location('original_reception_champion',ROOT/'champions/v9.1/team.py')
        old=importlib.util.module_from_spec(sp);sp.loader.exec_module(old)
        baseline=old.Guardiola2011();baseline._setup(FIELD);baseline._receive_plan=(rid,pid,expiry)
        with patch.object(baseline,'_pass_race',return_value=((.5,(-27.,-10.)),math.inf)):
            b=baseline.act(observation(row,kickers=()))
        self.assertEqual(a.players,b.players)

    def test_new_pass_is_not_cancelled_using_the_superseded_live_trajectory(self):
        x=cases()[0];row=x['start'];rid,pid,_=row['plan_after']
        c=module.Guardiola2011();c._setup(FIELD)
        c._receive_plan=(rid,pid,row['tick']+20)
        action=row['actions'][str(pid)]
        def choose(*args):
            c._pass_plan=(rid,*x['predicted'][1]);c._bank_plan=None
            c._touch_movement=tuple(action['movement'])
            return tuple(action['kick_direction']),action['kick_power']
        def race(*args,**kwargs):
            if kwargs.get('first_move') is not None:return None
            return (.5,tuple(x['predicted'][1])),math.inf
        with patch.object(c,'_choose_kick',side_effect=choose),patch.object(c,'_pass_race',side_effect=race):
            c.act(observation(row,kickers=(pid,)))
        self.assertIsNotNone(c._receive_plan)
        self.assertEqual(c._receive_plan[:2],(rid,pid))

    def test_stability_retains_a_still_executable_aim(self):
        x=cases()[0];c=controller(HOLD_RECEPTION=True,EXECUTE_RECEIVER=True)
        row,p,path=setup_case(c,x);route=c._receiver_route(p,path,row['opponents'],.05,2.6)
        c._receive_aim=(p[0],route[2]);live=c._pass_path(tuple(row['ball']))
        preferred=c._receiver_route(p,path,row['opponents'],0.,2.6)
        self.assertEqual(preferred[2],route[2])

    def test_invalid_held_target_is_replanned_or_cancelled(self):
        x=cases()[0];c=controller(HOLD_RECEPTION=True,EXECUTE_RECEIVER=True)
        row,p,path=setup_case(c,x);c._receive_aim=(p[0],(48.,28.))
        route=c._receiver_route(p,path,row['opponents'],0.,2.6)
        self.assertTrue(route is None or route[2]!=(48.,28.))

    def test_opponent_on_the_route_still_defeats_execution_verified_receiver(self):
        x=cases()[0];c=controller(EXECUTE_RECEIVER=True);row,p,path=setup_case(c,x)
        q=(6,path[3][1],path[3][2],0.,0.)
        self.assertIsNone(c._pass_race(p,path,[q],after=.05,until=2.6))

    def test_endwall_routes_collect_after_the_real_bounce_on_both_wings(self):
        options=[]
        for sign in (-1,1):
            c=controller(EXECUTE_RECEIVER=True)
            p=(2,33.3,sign*20.,0.,0.);receiver=(4,43.,sign*5.,0.,0.)
            friends=[(0,-47.,0.,0.,0.),p,receiver]
            option=c._endwall_link(p,35.,sign*20.,0.,0.,friends,[(5,47.,-sign*20.,0.,0.)])
            self.assertIsNotNone(option);options.append(option)
            launch=c._carrier_contact(p,35.,sign*20.,*c._requested_velocity(0.,0.,option[1]),option[2])
            path=c._pass_path(launch,(35.,sign*20.))
            bounce=(c._crossing_ticks(launch[0],launch[2],c._right-c._ball_radius)+1)*c._dt
            route=c._receiver_route(receiver,path,[],bounce+c._dt,2.4)
            self.assertIsNotNone(route);self.assertGreater(route[0],bounce)
        self.assertAlmostEqual(options[0][1][0][0],options[1][1][0][0])
        self.assertAlmostEqual(options[0][1][0][1],-options[1][1][0][1])

    def test_head_on_body_restitution_can_produce_control_on_cooldown(self):
        c=controller(FIRST_TOUCH=True);path=[(0.,2.,0.),(.05,1.45,0.)]
        route=(.05,(1.45,0.),(0.,0.),(4,0.,0.,0.,0.),'body',1,1)
        c._last_pass_motion=(path,[(-22.,0.),(-22.,0.)])
        self.assertTrue(c._first_touch_safe(route,path,[],999))

    def test_fast_glancing_first_touch_requires_a_safe_ready_recovery(self):
        c=controller(FIRST_TOUCH=True);path=[(0.,2.,0.),(.05,1.45,0.)]
        route=(.05,(1.45,0.),(0.,0.),(4,0.,0.,0.,0.),'body',1,1)
        c._last_pass_motion=(path,[(-1.,20.),(-1.,20.)])
        self.assertFalse(c._first_touch_safe(route,path,[],999))
        self.assertTrue(c._first_touch_safe(route,path,[],0))
        self.assertFalse(c._first_touch_safe(route,path,[(6,2.,0.,0.,0.)],0))

    def test_wall_velocity_cache_includes_restitution_and_drag(self):
        c=controller(FIRST_TOUCH=True)
        path=c._pass_path((0.,29.4,0.,10.),until=.1)
        self.assertIs(c._last_pass_motion[0],path)
        self.assertAlmostEqual(c._last_pass_motion[1][1][1],-7.5*.985)

    def test_general_movement_shots_keeper_cover_and_touch_physics_are_unchanged(self):
        champion=ROOT/'champions/v9.1/team.py'
        if not champion.exists():champion=ROOT/'my-team/team.py'
        def methods(path):
            cls=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef))
            return {n.name:ast.dump(n,include_attributes=False) for n in cls.body if isinstance(n,ast.FunctionDef)}
        old,new=methods(champion),methods(TEAM)
        for name in ('_move','_intercept','_eta','_trajectory','_pass_reachable','_verified_intercept',
                     '_cover_shape','_keeper_reaches','_shot_option','_shot_contact_margin',
                     '_goal_path','_carrier_contact','_touch_path'):
            self.assertEqual(old[name],new[name],name)


if __name__=='__main__':unittest.main()
