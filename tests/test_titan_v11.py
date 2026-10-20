"""Independent support/cover authority and frozen-physics regressions."""
import ast
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace as S
import unittest
from unittest.mock import patch
from test_special_tactics import observation, tuples, BASE, FLAGS as OLD_FLAGS
from test_hybrid_planner import FIELD, ROOT


def load(name):
    spec=importlib.util.spec_from_file_location('v11_'+name,ROOT/'experiments'/('titan-v11-'+name)/'team.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m


def controller(name='off'):
    c=load(name).Guardiola2011();c._setup(FIELD)
    return c


class TitanV11Tests(unittest.TestCase):
    def test_frozen_champion_and_independent_flags(self):
        self.assertEqual(hashlib.sha256((ROOT/'my-team/team.py').read_bytes()).hexdigest(),
                         '5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6')
        for name,flags in [('off',(False,False)),('architect',(True,False)),('firewall',(False,True))]:
            c=controller(name)
            self.assertEqual((c.PASSING_LANE_ARCHITECT,c.COUNTERATTACK_FIREWALL),flags)
            self.assertFalse(any(getattr(c,f,False) for f in OLD_FLAGS))

    def test_all_off_commands_debug_and_plans_equal_v10(self):
        a=BASE.Guardiola2011();b=controller()
        for tick in range(50):
            obs=observation(tick=tick,ball=(12.+tick*.1,5.,4.,-1.),own=0)
            self.assertEqual(a.act(obs),b.act(obs))
            self.assertEqual(a._receive_plan,b._receive_plan)
            self.assertEqual(a._receive_aim,b._receive_aim)

    def test_every_original_method_except_single_act_hook_is_identical(self):
        def methods(path):
            tree=ast.parse(path.read_text())
            cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
            return {n.name:ast.dump(n,include_attributes=False) for n in cls.body if isinstance(n,ast.FunctionDef)}
        base=methods(ROOT/'my-team/team.py')
        for name in ('off','architect','firewall'):
            new=methods(ROOT/'experiments'/('titan-v11-'+name)/'team.py')
            for method,value in base.items():
                if method!='act':self.assertEqual(new[method],value,(name,method))

    def test_architect_never_reassigns_keeper_carrier_chaser_cover_or_receiver(self):
        c=controller('architect');obs=observation()
        friends,enemies=tuples(obs)
        c._shape_cover_id=1;c._cover_id=1;c._transition_active=False
        c._receive_plan=(4,3,obs.tick+20)
        targets={p[0]:p[1:3] for p in friends};old=dict(targets)
        action=S(debug={})
        with patch.object(c,'_v11_lane',return_value=(9.,(20.,15.))) as lane:
            c._v11_targets(obs,friends,enemies,friends[3],targets,False,(4,(35.,6.)),action)
            self.assertEqual([call.args[2][0] for call in lane.call_args_list],[2])
        for pid in (0,1,3,4):self.assertEqual(targets[pid],old[pid])

    def test_restart_and_transition_support_keep_priority(self):
        c=controller('architect');obs=observation();friends,enemies=tuples(obs)
        c._shape_cover_id=1;c._transition_active=True
        for protected in (True,False):
            targets={p[0]:p[1:3] for p in friends};old=dict(targets)
            with patch.object(c,'_v11_lane') as lane:
                c._v11_targets(obs,friends,enemies,friends[3],targets,protected,None,S(debug={}))
                lane.assert_not_called()
            self.assertEqual(targets,old)

    def test_firewall_changes_only_existing_cover_and_never_advances_it(self):
        c=controller('firewall');obs=observation();friends,enemies=tuples(obs)
        c._shape_cover_id=1
        targets={p[0]:p[1:3] for p in friends};old=dict(targets)
        c._v11_targets(obs,friends,enemies,friends[3],targets,False,None,S(debug={}))
        for pid in (0,2,3,4):self.assertEqual(targets[pid],old[pid])
        self.assertLessEqual(targets[1][0],old[1][0])
        self.assertNotEqual(targets[1],old[1])

    def test_firewall_excludes_cover_receiving_live_pass(self):
        c=controller('firewall');obs=observation();friends,enemies=tuples(obs)
        c._shape_cover_id=1;c._receive_plan=(1,3,obs.tick+30)
        targets={p[0]:p[1:3] for p in friends};old=dict(targets)
        c._v11_targets(obs,friends,enemies,friends[3],targets,False,(1,(-28.,0.)),S(debug={}))
        self.assertEqual(targets,old)

    def test_opponent_touch_releases_firewall_despite_stale_own_control(self):
        c=controller('firewall');obs=observation(last=6);friends,enemies=tuples(obs)
        c._v11_was_own=True;c._shape_cover_id=1
        targets={p[0]:p[1:3] for p in friends};old=dict(targets);a=S(debug={})
        c._v11_targets(obs,friends,enemies,friends[3],targets,False,None,a)
        self.assertEqual(targets,old)
        self.assertEqual(a.debug['titan_v11'],('firewall_loss_release',))

    def test_unsafe_lane_is_rejected_and_speculative_state_restored(self):
        c=controller('architect');obs=observation();friends,enemies=tuples(obs)
        c._next_receive_aim=(91.,92.)
        with patch.object(c,'_link_option',return_value=None):
            self.assertIsNone(c._v11_lane(obs,friends[3],friends[4],friends,enemies,(36.,6.)))
        self.assertEqual(c._next_receive_aim,(91.,92.))

    def test_only_surviving_actual_commands_count_as_executions(self):
        c=controller('architect');c._v11_proposals={2:('architect_support',(1.,0.)),4:('architect_support',(0.,1.))}
        a=S(debug={},players={2:S(movement=(1.,0.),kick_direction=None),4:S(movement=(-1.,0.),kick_direction=None)})
        c._v11_executions(a)
        self.assertEqual(a.debug['titan_v11'],('architect_support',))
        self.assertEqual(a.debug['titan_v11_players'],(('architect_support',2),))

    def test_existing_physics_finds_executable_support_lane(self):
        c=controller('architect');obs=observation();friends,enemies=tuples(obs)
        c._next_receive_aim=(91.,92.)
        option=c._v11_lane(obs,friends[3],friends[4],friends,enemies,(36.,6.))
        self.assertIsNotNone(option)
        self.assertGreater(option[0],0.)
        self.assertGreater(option[1][0],obs.ball.position[0])
        self.assertEqual(c._next_receive_aim,(91.,92.))

    def test_firewall_prediction_responds_to_opponent_velocity(self):
        c=controller('firewall');obs=observation();friends,enemies=tuples(obs)
        a=c._v11_firewall(obs,friends[1],enemies,(-28.,0.))
        moving=[(q[0],q[1],q[2],-4.,-4.) for q in enemies]
        b=c._v11_firewall(obs,friends[1],moving,(-28.,0.))
        self.assertIsNotNone(a);self.assertIsNotNone(b)
        self.assertNotEqual(a,b)
        self.assertLessEqual(b[0],-28.)

    def test_stale_team_control_without_friendly_holder_keeps_defensive_safeguards(self):
        c=controller('firewall');obs=observation();friends,enemies=tuples(obs)
        obs.ball.controlling_player=None
        c._shape_cover_id=1
        targets={p[0]:p[1:3] for p in friends};old=dict(targets)
        with patch.object(c,'_v11_firewall') as screen:
            c._v11_targets(obs,friends,enemies,friends[3],targets,False,None,S(debug={}))
            screen.assert_not_called()
        self.assertEqual(targets,old)
