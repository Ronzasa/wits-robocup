"""Counterattack-specific behaviour, role invariants and immediate recovery."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace as S
import unittest
from unittest.mock import patch

from test_hybrid_planner import FIELD, ROOT

FROZEN = '5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6'
MODES = ('detect','cover','double','refinement','route-detect','route-cover','route-double',
         'predictive-detect','predictive-cover','predictive-double','verified-cover','verified-double',
         'verified-combined')


def controller(mode='cover'):
    path=ROOT/'experiments'/('titan-12b-'+mode)/'team.py'
    spec=importlib.util.spec_from_file_location('counter_'+mode,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    c=mod.Guardiola2011();c._setup(FIELD)
    c._press_contact_owner=1;c._press_own_contact_tick=90;c._shape_cover_id=1
    return c


def observation(tick=100,holder=6,touch=6,position=(0.,0.),velocity=(-12.,0.),ready=()):
    return S(tick=tick,score=(0,0),field=FIELD,phase='DEFEND',
             ball=S(position=position,velocity=velocity,controlling_player=holder,
                    last_touch=touch,controlling_team=1),can_kick=lambda pid:pid in ready)


FRIENDS=[(0,-47.,0.,0.,0.),(1,-23.,2.,0.,0.),(2,5.,0.,0.,0.),
         (3,-23.,-7.,0.,0.),(4,15.,13.,0.,0.)]
OPPONENTS=[(5,47.,0.,0.,0.),(6,0.,0.,-3.,0.),(7,-22.,1.,-5.,0.),
           (8,-18.,-12.,-4.,0.),(9,25.,24.,0.,0.)]
RACES={1:(2.,(-10.,0.)),2:(1.,(0.,0.)),3:(2.,(-10.,0.)),4:(3.,(-10.,0.))}
TARGETS={0:(-47.8,0.),1:(-3.,0.),2:(0.,0.),3:(4.,-15.),4:(12.,15.)}
THREATS=[(3.,7,-23.,1.,1.,False),(2.5,8,-23.,-8.,1.,False)]


def hook(c,obs=None,receiver=None,protected=False,threats=THREATS,urgent=True):
    targets=dict(TARGETS)
    with patch.object(c,'_counter_threats',return_value=(list(threats),urgent)):
        c._counter_defence(obs or observation(),FRIENDS,OPPONENTS,FRIENDS[2],RACES,
                           .1,targets,receiver,protected)
    return targets


class Titan12BTests(unittest.TestCase):
    def test_active_and_frozen_champion_unchanged(self):
        for name in ('my-team/team.py','champions/v10.0/team.py'):
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),FROZEN)

    def test_one_file_and_controller_with_only_permitted_imports(self):
        for mode in MODES:
            p=ROOT/'experiments'/('titan-12b-'+mode)/'team.py'
            self.assertEqual(list(p.parent.glob('*.py')),[p])
            self.assertLess(p.stat().st_size,256*1024)
            t=ast.parse(p.read_text())
            classes=[n for n in t.body if isinstance(n,ast.ClassDef)]
            self.assertEqual(len(classes),1)
            self.assertEqual(classes[0].bases[0].id,'TeamController')
            imports={a.name for n in ast.walk(t) if isinstance(n,ast.Import) for a in n.names}
            imports|={n.module for n in ast.walk(t) if isinstance(n,ast.ImportFrom)}
            self.assertEqual(imports,{'math','soccer'})
            self.assertTrue(callable(controller(mode).act))

    def test_all_original_physics_and_tactics_methods_preserved(self):
        def methods(p):
            cl=next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.ClassDef))
            return {n.name:ast.dump(n,include_attributes=False) for n in cl.body if isinstance(n,ast.FunctionDef)}
        base=methods(ROOT/'champions/v10.0/team.py')
        for mode in MODES:
            new=methods(ROOT/'experiments'/('titan-12b-'+mode)/'team.py')
            self.assertEqual({n for n in base if base[n]!=new[n]},{'reset','act'})
            self.assertEqual(set(new)-set(base),{'_counter_threats','_counter_cover_target','_counter_defence'})

    def test_actual_loss_and_forward_runs_create_predictive_threats(self):
        c=controller();friends=[p if p[0]!=3 else (3,12.,-12.,0.,0.) for p in FRIENDS]
        threats,urgent=c._counter_threats(observation(),friends,OPPONENTS,FRIENDS[2],RACES,.1)
        self.assertTrue(urgent)
        threat=next(t for t in threats if t[1]==7)
        self.assertLess(threat[2],-22.)
        self.assertGreaterEqual(len(threats),2)

    def test_secured_possession_has_no_counter_mode(self):
        c=controller()
        self.assertEqual(c._counter_threats(observation(holder=2,touch=2),FRIENDS,OPPONENTS,FRIENDS[2],RACES,.1),([],False))

    def test_existing_ready_attacker_keeps_successful_decisions(self):
        c=controller()
        self.assertEqual(c._counter_threats(observation(ready=(3,)),FRIENDS,OPPONENTS,FRIENDS[2],RACES,.1),([],False))

    def test_a_favorable_existing_pass_keeps_its_shape(self):
        c=controller();r=dict(RACES);r[2]=(.01,(0.,0.))
        self.assertEqual(c._counter_threats(observation(holder=None,touch=3),FRIENDS,OPPONENTS,FRIENDS[2],r,1.),([],False))

    def test_stale_phase_and_team_label_cannot_invent_a_loss(self):
        c=controller();c._press_contact_owner=None
        self.assertEqual(c._counter_threats(observation(holder=None,touch=None,velocity=(0.,0.)),FRIENDS,OPPONENTS,FRIENDS[2],RACES,.1),([],False))

    def test_old_loss_does_not_keep_deep_cover_latched(self):
        c=controller();c._press_own_contact_tick=0
        self.assertEqual(c._counter_threats(observation(position=(10.,0.),velocity=(0.,0.)),FRIENDS,OPPONENTS,FRIENDS[2],RACES,.1),([],False))

    def test_goal_side_existing_marker_prevents_duplicate_cover(self):
        c=controller();friends=[p if p[0]!=3 else (3,-26.,1.,0.,0.) for p in FRIENDS]
        ts,_=c._counter_threats(observation(),friends,OPPONENTS,FRIENDS[2],RACES,.1)
        self.assertNotIn(7,[t[1] for t in ts])

    def test_wide_or_backward_opponent_is_not_a_dangerous_outlet(self):
        c=controller();opps=[OPPONENTS[0],(6,0.,0.,0.,0.),(7,-20.,27.,0.,0.),(8,20.,0.,0.,0.)]
        ts,_=c._counter_threats(observation(),FRIENDS,opps,FRIENDS[2],RACES,.1)
        self.assertFalse(ts)

    def test_unreachable_deep_mark_does_not_pull_an_attacker_away(self):
        c=controller()
        self.assertIsNone(c._counter_cover_target((4,25.,20.,0.,0.),THREATS[0],0.,0.))

    def test_local_mark_is_goal_side_and_mirror_symmetric(self):
        c=controller();a=c._counter_cover_target(FRIENDS[1],THREATS[0],0.,0.)
        p=(1,-23.,-2.,0.,0.);q=(3.,7,-23.,-1.,1.,False)
        b=c._counter_cover_target(p,q,0.,0.)
        self.assertLess(a[0],-23.)
        self.assertAlmostEqual(a[0],b[0]);self.assertAlmostEqual(a[1],-b[1])

    def test_cover_changes_only_designated_defender(self):
        c=controller();t=hook(c)
        self.assertEqual([i for i in t if t[i]!=TARGETS[i]],[1])
        self.assertEqual(c._counter_trace['defenders'],(1,))

    def test_verified_receiver_even_if_guard_is_never_overridden(self):
        c=controller();t=hook(c,receiver=(1,(-10.,4.)))
        self.assertEqual(t,TARGETS)

    def test_keeper_and_primary_chaser_cannot_be_selected_as_guard(self):
        for guard in (0,2):
            c=controller();c._shape_cover_id=guard
            self.assertEqual(hook(c),TARGETS)

    def test_detector_has_no_action_side_effect(self):
        c=controller('detect');self.assertEqual(hook(c),TARGETS)
        self.assertTrue(c._counter_trace['threats'])

    def test_emergency_changes_only_one_additional_defender_and_keeps_outlet(self):
        c=controller('double');t=hook(c)
        self.assertEqual([i for i in t if t[i]!=TARGETS[i]],[3])
        self.assertEqual(c._counter_trace['defenders'],(1,3))
        for pid in (0,1,2,4):self.assertEqual(t[pid],TARGETS[pid])

    def test_two_outlets_requirement_disables_infeasible_extra_defender(self):
        c=controller('double');c.EMERGENCY_OUTLETS=2
        self.assertEqual(hook(c),TARGETS)

    def test_verified_receiver_is_the_protected_emergency_outlet(self):
        c=controller('double');t=hook(c,receiver=(4,(12.,15.)))
        self.assertEqual(t[4],TARGETS[4]);self.assertNotEqual(t[3],TARGETS[3])

    def test_single_threat_is_insufficient_for_double_defence(self):
        c=controller('double');self.assertEqual(hook(c,threats=THREATS[:1]),TARGETS)

    def test_emergency_window_does_not_extend_or_rearm_on_risk_flicker(self):
        c=controller('double');hook(c);self.assertEqual(c._counter_double_until,112)
        hook(c,observation(tick=105),urgent=False)
        hook(c,observation(tick=110));self.assertEqual(c._counter_double_until,112)
        self.assertEqual(hook(c,observation(tick=112)),TARGETS)
        self.assertEqual(hook(c,observation(tick=115)),TARGETS)

    def test_recovery_is_immediate_after_secure_possession(self):
        c=controller('double');hook(c)
        t=dict(TARGETS)
        c._counter_defence(observation(tick=101,holder=2,touch=2),FRIENDS,OPPONENTS,FRIENDS[2],RACES,.1,t,None,False)
        self.assertEqual(t,TARGETS);self.assertFalse(c._counter_double_latched)
        self.assertFalse(c._counter_trace['threats'])

    def test_disappearing_threat_releases_and_rearms_for_new_counter(self):
        c=controller('double');hook(c)
        self.assertEqual(hook(c,observation(tick=101),threats=[]),TARGETS)
        self.assertFalse(c._counter_double_latched)
        hook(c,observation(tick=103));self.assertEqual(c._counter_double_until,115)

    def test_protected_restart_does_not_change_targets(self):
        c=controller('double');self.assertEqual(hook(c,protected=True),TARGETS)

    def test_reset_clears_all_counter_state(self):
        c=controller('double');hook(c);c.reset(123)
        self.assertFalse(c._counter_double_latched);self.assertEqual(c._counter_double_until,-1)
        self.assertEqual(c._counter_trace,{})

    def test_saved_native_counter_situations_reproduce_targets(self):
        data=json.loads((ROOT/'tests/fixtures/titan-12b-counter-cases.json').read_text())
        self.assertTrue(any(row['mode']=='double' for row in data['cases']))
        for row in data['cases']:
            with self.subTest(mode=row['mode'],tick=row['tick'],style=row['style']):
                c=controller(row['mode'])
                # Native public field values include float32 roundoff; retain
                # those exact values rather than the hand-written test FIELD.
                c._setup(S(**data['public_field']))
                c._press_contact_owner=row['press_owner']
                c._press_own_contact_tick=row['own_contact_tick']
                c._shape_cover_id=row['guard']
                obs=observation(row['tick'],row['holder'],row['touch'],
                                row['ball'][:2],row['ball'][2:],row['ready'])
                obs.score=tuple(row['score'])
                targets={int(k):tuple(v) for k,v in row['before'].items()}
                c._counter_defence(obs,row['friends'],row['opponents'],row['chaser'],
                    {int(k):v for k,v in row['races'].items()},row['enemy_eta'],targets,
                    row['receiver'],row['protected'])
                self.assertEqual(json.loads(json.dumps(targets)),row['after'])
                self.assertEqual(json.loads(json.dumps(c._counter_trace)),row['trace'])

    def test_refinement_preserves_v10_cover_during_a_committed_incoming_flight(self):
        obs=observation(holder=None,touch=7,position=(-32.7,3.7),velocity=(-24.5,3.8))
        friends=[(0,-47.8,.3,0.,.8),(1,-35.1,-8.2,-7.9,-1.2),
                 (2,-35.1,.9,-.5,2.1),(3,-37.1,-3.3,-5.1,-3.4),(4,-25.2,-3.,-5.,2.5)]
        enemies=[(5,47.8,.1,0.,0.),(6,-27.8,.6,-.1,7.6),
                 (7,-31.,2.1,-2.3,6.1),(8,-44.,-12.3,-1.9,2.3),(9,-34.6,2.8,-3.6,3.4)]
        original,refined=controller(),controller('refinement')
        for c in (original,refined):c._shape_cover_id=3
        self.assertTrue(original._counter_threats(obs,friends,enemies,friends[2],RACES,.1)[0])
        self.assertEqual(refined._counter_threats(obs,friends,enemies,friends[2],RACES,.1),([],False))

    def test_refinement_keeps_controlled_opponent_options_and_all_other_coefficients(self):
        original,refined=controller(),controller('refinement')
        obs=observation(holder=6,touch=6,position=(-20.,0.),velocity=(-12.,0.))
        self.assertEqual(original._counter_threats(obs,FRIENDS,OPPONENTS,FRIENDS[2],RACES,.1),
                         refined._counter_threats(obs,FRIENDS,OPPONENTS,FRIENDS[2],RACES,.1))
        def methods(mode):
            tree=ast.parse((ROOT/'experiments'/('titan-12b-'+mode)/'team.py').read_text())
            cl=next(n for n in tree.body if isinstance(n,ast.ClassDef))
            return {n.name:ast.dump(n,include_attributes=False) for n in cl.body if isinstance(n,ast.FunctionDef)}
        before,after=methods('cover'),methods('refinement')
        self.assertEqual({name for name in before if before[name]!=after[name]},{'_counter_threats'})

    def test_route_detector_never_substitutes_eta_for_unavailable_contact(self):
        c=controller('route-cover')
        obs=observation(holder=None,position=(-5.,15.),velocity=(-20.,-2.))
        with patch.object(c,'_verified_intercept',return_value=None), patch.object(c,'_eta',side_effect=AssertionError('ETA fallback')):
            self.assertEqual(c._counter_threats(obs,FRIENDS,OPPONENTS,FRIENDS[2],RACES,.1),([],False))

    def test_route_detector_preserves_existing_goal_bound_shot_response(self):
        c=controller('route-cover')
        obs=observation(holder=None,position=(-32.7,3.7),velocity=(-24.5,3.8))
        with patch.object(c,'_verified_intercept') as verify:
            self.assertEqual(c._counter_threats(obs,FRIENDS,OPPONENTS,FRIENDS[2],RACES,.1),([],False))
            verify.assert_not_called()

    def test_route_detector_preserves_terminal_goalkeeper_area(self):
        c=controller('route-cover');obs=observation(holder=None,position=(-5.,15.),velocity=(-20.,-2.))
        with patch.object(c,'_verified_intercept',return_value=(.8,(-42.,0.))):
            self.assertEqual(c._counter_threats(obs,FRIENDS,OPPONENTS,FRIENDS[2],RACES,.1),([],False))

    def test_route_detector_keeps_a_verified_earlier_primary_chaser(self):
        c=controller('route-cover');obs=observation(holder=None,position=(-5.,15.),velocity=(-20.,-2.))
        def contact(p,*args,**kwargs):return (.4,(-12.,14.)) if p[0]==2 else (.8,(-19.,13.))
        with patch.object(c,'_verified_intercept',side_effect=contact):
            self.assertEqual(c._counter_threats(obs,FRIENDS,OPPONENTS,FRIENDS[2],RACES,.1),([],False))

    def test_route_detector_has_no_heavy_verification_during_an_existing_kick(self):
        c=controller('route-cover');obs=observation(holder=None,ready=(2,),position=(-5.,15.),velocity=(-20.,-2.))
        with patch.object(c,'_pass_path') as forecast:
            self.assertEqual(c._counter_threats(obs,FRIENDS,OPPONENTS,FRIENDS[2],RACES,.1),([],False))
            forecast.assert_not_called()

    def test_real_direct_and_wall_counterpasses_have_verified_receivers_without_cache_mutation(self):
        friends=[(0,-47.,0.,0.,0.),(1,15.,0.,0.,0.),(2,12.,-20.,0.,0.),
                 (3,15.,-20.,0.,0.),(4,30.,-20.,0.,0.)]
        for wall in (False,True):
            c=controller('route-cover');c._enemy_cooldowns={6:5}
            if wall:
                obs=observation(holder=None,position=(-5.,26.),velocity=(-20.,20.))
                opp=[(5,47.,0.,0.,0.),(6,-3.,26.,0.,0.),(7,-25.,15.,0.,0.),(8,25.,-20.,0.,0.),(9,30.,-20.,0.,0.)]
            else:
                obs=observation(holder=None,position=(-5.,15.),velocity=(-20.,-2.))
                opp=[(5,47.,0.,0.,0.),(6,-3.,15.,0.,0.),(7,-22.,12.,0.,0.),(8,25.,-20.,0.,0.),(9,30.,-20.,0.,0.)]
            sentinel=[];c._runtime_path=sentinel;c._runtime_steps=sentinel
            c._runtime_queries={'keep':7};c._next_receive_aim=(8.,9.)
            threats,urgent=c._counter_threats(obs,friends,opp,friends[2],RACES,.1)
            self.assertTrue(threats,(wall,threats))
            self.assertEqual(threats[0][1],7)
            self.assertGreaterEqual(threats[0][4],.2)
            self.assertLessEqual(threats[0][4],1.25)
            self.assertIs(c._runtime_path,sentinel);self.assertIs(c._runtime_steps,sentinel)
            self.assertEqual(c._runtime_queries,{'keep':7});self.assertEqual(c._next_receive_aim,(8.,9.))

    def test_predictive_components_use_independent_action_flags(self):
        for name,expected in [('predictive-detect',(False,False)),('predictive-cover',(True,False)),('predictive-double',(False,True))]:
            c=controller(name);self.assertEqual((c.COUNTER_COVER,c.COUNTER_DOUBLE),expected)

    def test_real_controlled_enemy_releases_have_bounded_legal_negative_launches(self):
        c=controller('predictive-cover')
        obs=observation(holder=6,touch=6,position=(5.,18.),velocity=(0.,0.))
        friends=[(0,-47.,0.,0.,0.),(1,-14.,10.,0.,0.),(2,15.,-20.,0.,0.),(3,20.,-20.,0.,0.),(4,30.,0.,0.,0.)]
        opponents=[(5,47.,0.,0.,0.),(6,6.7,18.,0.,0.),(7,-12.,14.,0.,0.),(8,-20.,-7.,0.,0.),(9,25.,15.,0.,0.)]
        with patch.object(c,'_pass_path',wraps=c._pass_path) as forecast:
            threats,urgent=c._counter_threats(obs,friends,opponents,friends[2],RACES,.1)
            self.assertTrue(threats)
            self.assertTrue(urgent)
            self.assertGreater(forecast.call_count,0);self.assertLessEqual(forecast.call_count,2)
            for call in forecast.call_args_list:self.assertLess(call.args[0][2],-6.0)

    def test_predictive_release_never_ignores_cooldown_or_central_shot_safeguards(self):
        c=controller('predictive-cover');c._enemy_cooldowns={6:5}
        obs=observation(holder=6,position=(5.,18.),velocity=(0.,0.))
        with patch.object(c,'_pass_path') as forecast:
            self.assertEqual(c._counter_threats(obs,FRIENDS,OPPONENTS,FRIENDS[2],RACES,.1),([],False))
            forecast.assert_not_called()
        c._enemy_cooldowns={}
        obs=observation(holder=6,position=(-10.,0.),velocity=(0.,0.))
        with patch.object(c,'_pass_path') as forecast:
            self.assertEqual(c._counter_threats(obs,FRIENDS,OPPONENTS,FRIENDS[2],RACES,.1),([],False))
            forecast.assert_not_called()

    def test_verified_integration_isolates_the_new_detector_from_original_cover_timing(self):
        def methods(mode):
            tree=ast.parse((ROOT/'experiments'/('titan-12b-'+mode)/'team.py').read_text())
            cl=next(n for n in tree.body if isinstance(n,ast.ClassDef))
            return {n.name:ast.dump(n,include_attributes=False) for n in cl.body if isinstance(n,ast.FunctionDef)}
        old,predictive,final=methods('cover'),methods('predictive-cover'),methods('verified-cover')
        self.assertEqual(old['_counter_cover_target'],final['_counter_cover_target'])
        self.assertEqual(old['_counter_defence'],final['_counter_defence'])
        self.assertEqual(predictive['_counter_threats'],final['_counter_threats'])
        self.assertEqual((controller('verified-cover').COUNTER_COVER,controller('verified-cover').COUNTER_DOUBLE),(True,False))
        self.assertEqual((controller('verified-double').COUNTER_COVER,controller('verified-double').COUNTER_DOUBLE),(False,True))

    def test_combination_changes_flags_and_reuses_identical_independent_methods(self):
        def methods(mode):
            t=ast.parse((ROOT/'experiments'/('titan-12b-'+mode)/'team.py').read_text())
            c=next(n for n in t.body if isinstance(n,ast.ClassDef))
            return {n.name:ast.dump(n,include_attributes=False) for n in c.body if isinstance(n,ast.FunctionDef)}
        self.assertEqual(methods('verified-cover'),methods('verified-combined'))
        self.assertEqual(methods('verified-double'),methods('verified-combined'))
        combined=controller('verified-combined')
        self.assertEqual((combined.COUNTER_COVER,combined.COUNTER_DOUBLE),(True,True))

if __name__=='__main__':unittest.main()
