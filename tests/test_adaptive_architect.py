"""Pressure discrimination, role authority, verified advantage and frozen physics."""
import ast
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace as S
import unittest
from unittest.mock import patch
from test_special_tactics import observation,tuples,BASE
from test_hybrid_planner import FIELD,ROOT

spec=importlib.util.spec_from_file_location('adaptive_team',ROOT/'experiments/titan-adaptive-architect/team.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def controller():
    c=m.Guardiola2011();c._setup(FIELD)
    return c


def pressing(tick=1900):
    return observation(tick=tick,enemies=[(5,47.,0.,0.,0.),(6,28.,1.,-4.,-1.),
        (7,24.,7.,1.,-4.),(8,42.,-20.,0.,0.),(9,44.,20.,0.,0.)])


def setup(c,obs):
    f,e=tuples(obs);c._shape_cover_id=1;c._cover_id=1;c._transition_active=False
    targets={p[0]:p[1:3] for p in f};targets[2]=(31.,-8.);targets[4]=(38.,6.)
    return f,e,targets


class AdaptiveArchitectTests(unittest.TestCase):
    def test_original_champion_and_architect_hashes_unchanged(self):
        import json
        r=json.loads((ROOT/'docs/titan-v11/registration.json').read_text())
        for name in ('v10','architect'):
            s=r['sources'][name]
            self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])

    def test_firewall_and_prior_tactics_disabled(self):
        c=controller()
        self.assertTrue(c.PASSING_LANE_ARCHITECT);self.assertTrue(c.ADAPTIVE_ARCHITECT)
        for flag in ('COUNTERATTACK_FIREWALL','KEEPER_POWER_PLAY','GOALKEEPER_TRAP','PINBALL_SLINGSHOT','COOLDOWN_AMBUSH'):
            self.assertFalse(getattr(c,flag,False))

    def test_existing_physics_methods_ast_identical(self):
        def methods(path):
            cls=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef))
            return {n.name:ast.dump(n,include_attributes=False) for n in cls.body if isinstance(n,ast.FunctionDef)}
        a=methods(ROOT/'my-team/team.py');b=methods(ROOT/'experiments/titan-adaptive-architect/team.py')
        for name,value in a.items():
            if name!='act':self.assertEqual(b[name],value,name)

    def test_closing_multi_player_press_requires_tight_lane_and_interception_race(self):
        c=controller();obs=pressing();f,e,t=setup(c,obs)
        active,reason,data=c._adaptive_pressure(obs,f,e,[f[2],f[4]],t)
        self.assertTrue(active);self.assertEqual(reason,'adaptive_pressure')
        self.assertGreaterEqual(data['closing_defenders'],2)
        self.assertLessEqual(data['enemy_race_seconds'],.8)
        self.assertGreaterEqual(data['blocked_shape_lanes'],1)

    def test_static_compact_shape_suppresses_architect(self):
        c=controller();obs=observation(enemies=[(5,47.,0.,0.,0.),(6,32.,-8.,0.,0.),
            (7,34.,0.,0.,0.),(8,36.,8.,0.,0.),(9,10.,20.,0.,0.)])
        f,e,t=setup(c,obs);old=dict(t);a=S(debug={})
        with patch.object(c,'_adaptive_lane') as lane:
            c._v11_targets(obs,f,e,f[3],t,False,None,a)
            lane.assert_not_called()
        self.assertEqual(t,old)
        self.assertIn('adaptive_reject_compact',a.debug['titan_v11'])

    def test_receding_defenders_do_not_count_as_pressure(self):
        c=controller();obs=pressing();f,e,t=setup(c,obs)
        e=[(q[0],q[1],q[2],-q[3],-q[4]) for q in e]
        self.assertFalse(c._adaptive_pressure(obs,f,e,[f[2],f[4]],t)[0])

    def test_open_shape_lanes_suppress_unnecessary_movement(self):
        c=controller();obs=pressing();f,e,t=setup(c,obs)
        with patch.object(c,'_lane',return_value=8.):
            active,reason,_=c._adaptive_pressure(obs,f,e,[f[2],f[4]],t)
        self.assertFalse(active);self.assertEqual(reason,'adaptive_reject_low_pressure')

    def test_slow_enemy_interception_race_suppresses_pressure(self):
        c=controller();obs=pressing();f,e,t=setup(c,obs)
        with patch.object(c,'_intercept',return_value=(2.,(25.,0.))):
            self.assertFalse(c._adaptive_pressure(obs,f,e,[f[2],f[4]],t)[0])

    def test_only_free_supporters_are_considered_under_pressure(self):
        c=controller();obs=pressing();f,e,t=setup(c,obs);old=dict(t)
        c._receive_plan=(4,3,obs.tick+20)
        with patch.object(c,'_adaptive_pressure',return_value=(True,'adaptive_pressure',{})),patch.object(c,'_adaptive_lane',return_value=((9.,(20.,15.),1.),'adaptive_verified_gain')) as lane:
            c._v11_targets(obs,f,e,f[3],t,False,(4,(35.,6.)),S(debug={}))
            self.assertEqual([call.args[2][0] for call in lane.call_args_list],[2])
        for pid in (0,1,3,4):self.assertEqual(t[pid],old[pid])

    def test_no_verified_opportunity_preserves_all_targets_and_aim_state(self):
        c=controller();obs=pressing();f,e,t=setup(c,obs);old=dict(t)
        c._next_receive_aim=(91.,92.)
        with patch.object(c,'_link_option',return_value=None):
            c._v11_targets(obs,f,e,f[3],t,False,None,S(debug={}))
        self.assertEqual(t,old);self.assertEqual(c._next_receive_aim,(91.,92.))

    def test_no_pressure_matches_v10_player_commands(self):
        a=BASE.Guardiola2011();b=controller()
        for tick in range(50):
            obs=observation(tick=tick,ball=(12.+tick*.1,5.,4.,-1.),own=0,
                enemies=[(5,48.,0.,0.,0.),(6,40.,20.,0.,0.),(7,40.,-20.,0.,0.),(8,45.,15.,0.,0.),(9,45.,-15.,0.,0.)])
            self.assertEqual(a.act(obs).players,b.act(obs).players)
            self.assertEqual(a._receive_plan,b._receive_plan)

    def test_opponent_touch_or_unheld_control_stops_new_support(self):
        for last,holder in ((6,3),(3,None)):
            c=controller();obs=pressing();obs.ball.last_touch=last;obs.ball.controlling_player=holder
            f,e,t=setup(c,obs);old=dict(t)
            with patch.object(c,'_adaptive_pressure') as pressure:
                c._v11_targets(obs,f,e,f[3],t,False,None,S(debug={}))
                pressure.assert_not_called()
            self.assertEqual(t,old)

    def test_rejected_final_movement_is_not_counted_as_activation(self):
        c=controller();obs=pressing();f,e,t=setup(c,obs)
        c._adaptive_obs=obs;c._adaptive_recent={}
        c._v11_proposals={2:('adaptive_support',(1.,0.))}
        action=S(debug={},players={2:S(movement=(-1.,0.),kick_direction=None)})
        c._v11_executions(action)
        self.assertFalse(c._adaptive_recent)
        self.assertNotIn('titan_v11_players',action.debug)

    def test_real_verified_route_without_baseline_alternative_is_accepted(self):
        c=controller();obs=observation();f,e=tuples(obs)
        c._next_receive_aim=(91.,92.)
        option,reason=c._adaptive_lane(obs,f[3],f[4],f,e,(-40.,0.))
        self.assertIsNotNone(option);self.assertEqual(reason,'adaptive_verified_gain')
        self.assertGreater(option[0],0.)
        self.assertEqual(c._next_receive_aim,(91.,92.))

    def test_real_verified_lane_without_advantage_is_rejected(self):
        c=controller();obs=observation();f,e=tuples(obs)
        option,reason=c._adaptive_lane(obs,f[3],f[4],f,e,(36.,6.))
        self.assertIsNone(option);self.assertEqual(reason,'adaptive_reject_no_gain')
