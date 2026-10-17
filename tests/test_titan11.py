"""TITAN-11 isolation, equivalent movement forecasts and legal pass regressions."""
import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import unittest
from unittest.mock import patch

from test_hybrid_planner import FIELD, ROOT


def controller(label):
    path = ROOT / ('champions/v10.0/team.py' if label == 'champion'
                   else 'experiments/titan-11-' + label + '/team.py')
    spec = importlib.util.spec_from_file_location('titan11_' + label, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    c = module.Guardiola2011()
    c._setup(FIELD)
    return c


def methods(label):
    path = ROOT / ('champions/v10.0/team.py' if label == 'champion'
                   else 'experiments/titan-11-' + label + '/team.py')
    cls = next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.ClassDef))
    return {n.name: ast.dump(n, include_attributes=False) for n in cls.body
            if isinstance(n, ast.FunctionDef)}


class Titan11Tests(unittest.TestCase):
    def test_frozen_v10_is_exact(self):
        self.assertEqual(hashlib.sha256((ROOT / 'champions/v10.0/team.py').read_bytes()).hexdigest(),
                         '5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6')

    def test_all_candidates_are_single_file_single_controller(self):
        for label in ('runtime-inline', 'runtime-samples', 'runtime', 'passing',
                      'movement', 'cover', 'finishing', 'lookahead', 'passing-r', 'cover-r',
                      'reach-local', 'reach-bound', 'reach-runtime', 'reach-step-bound'):
            path = ROOT / 'experiments' / ('titan-11-' + label) / 'team.py'
            self.assertEqual(list(path.parent.glob('*.py')), [path])
            self.assertLess(path.stat().st_size, 256 * 1024)
            tree = ast.parse(path.read_text())
            classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
            self.assertEqual(len(classes), 1)
            self.assertTrue(any(isinstance(b, ast.Name) and b.id == 'TeamController' for b in classes[0].bases))
            self.assertTrue(callable(controller(label).act))
            imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            imports.update(a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names)
            self.assertEqual(imports, {'math', 'soccer'})

    def test_runtime_changes_only_setup_reset_and_heuristic_intercept(self):
        before, after = methods('champion'), methods('runtime')
        self.assertEqual({n for n in before if before[n] != after[n]}, {'reset', '_setup', '_intercept'})

    def test_independent_features_change_only_their_own_hooks(self):
        baseline = methods('runtime')
        allowed = {
            'passing': {'_link_option', '_search_links', '_transition_release'},
            'movement': {'_role_support', 'act'},
            'cover': {'_cover_shape'},
            'finishing': {'_shot_option', '_before_endwall'},
            'lookahead': {'_touch_path'},
        }
        for label, expected in allowed.items():
            after = methods(label)
            self.assertEqual({n for n in baseline if after[n] != baseline[n]}, expected, label)

    def test_runtime_qualified_passing_preserves_every_tactical_method(self):
        old,new=methods('passing'),methods('passing-r')
        self.assertEqual(set(old),set(new))
        self.assertEqual({n for n in old if old[n]!=new[n]},{'_pass_reachable'})
        def settings(label):
            path=ROOT/'experiments'/('titan-11-'+label)/'team.py'
            cls=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef))
            return {n.targets[0].id:ast.dump(n.value,include_attributes=False)
                for n in cls.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)
                and n.targets[0].id!='version'}
        self.assertEqual(settings('passing'),settings('passing-r'))

    def test_both_runtime_ablations_and_combination_preserve_chasing(self):
        rng = random.Random(730171)
        old = controller('champion')
        challengers = [controller(n) for n in ('runtime-inline', 'runtime-samples', 'runtime')]
        for _ in range(1000):
            p = (3, rng.uniform(-48,48), rng.uniform(-28,28), rng.uniform(-8,8), rng.uniform(-8,8))
            path = old._trajectory(rng.uniform(-48,48), rng.uniform(-28,28),
                                   rng.uniform(-30,30), rng.uniform(-30,30))
            expected = old._intercept(p,path)
            for c in challengers:
                self.assertEqual(c._intercept(p,path), expected)

    def test_tiny_distance_zero_and_ties_preserve_eta_fallback(self):
        old, new = controller('champion'), controller('runtime')
        for d in (0., 1e-8, math.nextafter(1e-6,0.), 1e-6, 30.):
            for velocity in ((0.,0.), (8.,0.), (-8.,0.), (0.,8.)):
                p = (2,0.,0.,*velocity)
                for path in ([(0.,d,0.)], [(.05,d,0.),(.5,40.,0.)], [(0.,40.,0.),(0.,-40.,0.)]):
                    self.assertEqual(old._intercept(p,path),new._intercept(p,path))

    def test_cache_retains_object_and_only_one_forecast(self):
        c = controller('runtime')
        class Forecast(list):
            def __iter__(self):
                if getattr(self,'used',False):raise AssertionError('Repeat conversion')
                self.used=True
                return super().__iter__()
        first = Forecast([(0.,0.,0.), (.1,2.,0.)])
        c._intercept((1,-10.,0.,0.,0.),first)
        c._intercept((2,10.,0.,0.,0.),first)
        self.assertIs(c._runtime_chase_path,first)
        second = [(0.,40.,20.)]
        self.assertEqual(c._intercept((1,-10.,0.,0.,0.),second),
                         controller('champion')._intercept((1,-10.,0.,0.,0.),second))
        self.assertIs(c._runtime_chase_path,second)
        self.assertEqual(len(c._runtime_chase_steps),1)

    def test_forecast_cache_resets_for_new_match_and_field(self):
        c = controller('runtime')
        for operation in (lambda:c.reset(1001), lambda:c._setup(FIELD)):
            c._intercept((1,-10.,0.,0.,0.),[(0.,0.,0.),(.1,2.,0.)])
            operation()
            self.assertIsNone(c._runtime_chase_path)
            self.assertIsNone(c._runtime_chase_steps)

    def test_all_new_progressive_options_still_require_actual_receiver_race(self):
        c = controller('passing')
        passer, receiver = (2,-1.7,0.,0.,0.), (4,25.,3.,4.,0.)
        with patch.object(c,'_pass_race',return_value=None) as race:
            self.assertIsNone(c._search_links(passer,0.,0.,0.,0.,[passer,receiver],[]))
            self.assertGreaterEqual(race.call_count,3)
        c._transition_active=True
        with patch.object(c,'_pass_race',return_value=None) as race:
            self.assertIsNone(c._transition_release(passer,0.,0.,0.,0.,[passer,receiver],[]))
            self.assertGreater(race.call_count,0)

    def test_new_passes_reject_distant_receiver_and_first_leg_body(self):
        c = controller('passing')
        passer=(2,-1.7,0.,0.,0.)
        self.assertIsNone(c._link_option(passer,0.,0.,0.,0.,(4,-45.,-27.,-8.,0.),[],35.,0.,30.))
        c._enemy_cooldowns={6:999}
        self.assertIsNone(c._link_option(passer,0.,0.,0.,0.,(4,25.,0.,0.,0.),
                                        [(6,2.,0.,0.,0.)],28.,0.,30.))

    def test_movement_search_preserves_nominal_without_opponents(self):
        old, new = controller('champion'), controller('movement')
        for role in (1,2,3,4):
            p=(role,0.,0.,0.,0.)
            self.assertEqual(old._role_support(p,0.,10.,-15.),new._role_support(p,0.,10.,-15.))

    def test_space_search_avoids_a_guarded_nominal_target(self):
        c=controller('movement');p=(4,10.,0.,4.,0.)
        nominal=c._nominal_support(p,0.,0.,0.)
        target=c._role_support(p,0.,0.,0.,[(6,*nominal,0.,0.)],[p])
        self.assertNotEqual(target,nominal)
        self.assertGreater(math.hypot(target[0]-nominal[0],target[1]-nominal[1]),2.)

    def test_preventive_cover_moves_only_assigned_guard(self):
        from types import SimpleNamespace as S
        c=controller('cover');c._shape_cover_id=1
        friends=[(0,-47.,0.,0.,0.),(1,10.,10.,0.,0.),(3,20.,20.,0.,0.),(4,35.,0.,0.,0.)]
        opponents=[(5,47.,0.,0.,0.),(6,-10.,4.,-4.,0.)]
        obs=S(ball=S(position=(20.,20.),controlling_player=3,last_touch=3))
        targets={0:(-47.,1.),1:(18.,20.),3:(20.,20.),4:(40.,0.)};original=targets.copy()
        c._cover_shape(obs,friends,opponents,friends[2],{3:(.1,(20.,20.))},1.,targets)
        self.assertLess(targets[1][0],opponents[1][1])
        for pid in (0,3,4):self.assertEqual(targets[pid],original[pid])

    def test_refined_cover_preserves_a_verified_reception_target(self):
        from types import SimpleNamespace as S
        c=controller('cover-r');c._shape_cover_id=1;c._receive_plan=(1,3,100)
        friends=[(0,-47.,0.,0.,0.),(1,5.,15.,0.,0.),(3,10.,20.,0.,0.)]
        obs=S(ball=S(position=(10.,20.),controlling_player=None,last_touch=3))
        targets={0:(-47.,1.),1:(15.,20.),3:(10.,20.)};before=targets.copy()
        c._cover_shape(obs,friends,[(6,11.,20.,0.,0.)],friends[2],{3:(.2,(10.,20.))},.1,targets)
        self.assertEqual(targets,before)

    def test_refined_cover_preserves_unpressured_secure_shape(self):
        from types import SimpleNamespace as S
        c=controller('cover-r');c._shape_cover_id=1
        friends=[(0,-47.,0.,0.,0.),(1,5.,10.,0.,0.),(3,10.,20.,0.,0.)]
        obs=S(ball=S(position=(10.,20.),controlling_player=3,last_touch=3))
        targets={0:(-47.,1.),1:(8.,20.),3:(10.,20.)};before=targets.copy()
        c._cover_shape(obs,friends,[(6,-20.,0.,0.,0.)],friends[2],{3:(.1,(10.,20.))},1.,targets)
        self.assertEqual(targets,before)

    def test_refined_cover_changes_only_one_guard_under_pressure(self):
        from types import SimpleNamespace as S
        c=controller('cover-r');c._shape_cover_id=1
        friends=[(0,-47.,0.,0.,0.),(1,5.,10.,0.,0.),(3,10.,20.,0.,0.),(4,25.,-12.,0.,0.)]
        obs=S(ball=S(position=(10.,20.),controlling_player=6,last_touch=6))
        targets={0:(-47.,1.),1:(8.,20.),3:(10.,20.),4:(25.,-12.)};before=targets.copy()
        c._cover_shape(obs,friends,[(6,11.,20.,0.,0.)],friends[2],{3:(.3,(10.,20.))},.1,targets)
        self.assertNotEqual(targets[1],before[1])
        for pid in (0,3,4):self.assertEqual(targets[pid],before[pid])
        old,new=methods('reach-step-bound'),methods('cover-r')
        self.assertEqual({n for n in old if old[n]!=new[n]},{'_cover_shape'})

    def test_finishing_default_power_is_exact_and_slow_options_are_legal(self):
        old,new=controller('champion'),controller('finishing')
        p=(3,28.3,0.,0.,0.)
        for y in (-6.1,-4.5,0.,4.5,6.1):
            args=p,30.,0.,0.,0.,[],y
            self.assertEqual(old._shot_option(*args),new._shot_option(*args))
            option=new._shot_option(*args,speed_scale=.85)
            if option is not None:
                self.assertGreaterEqual(option[1][1],0.)
                self.assertLessEqual(option[1][1],1.)
                sx,sy=new._requested_velocity(0.,0.,option[1])
                self.assertLessEqual(math.hypot(sx,sy),new._impulse+1e-9)

    def test_projection_bound_and_local_rollout_bindings_preserve_physical_reachability(self):
        old=controller('runtime')
        challengers=[controller(n) for n in ('reach-local','reach-bound','reach-runtime','reach-step-bound')]
        rng=random.Random(141715927)
        for _ in range(1500):
            vx,vy=rng.uniform(-8.,8.),rng.uniform(-8.,8.)
            speed=math.hypot(vx,vy)
            if speed>8.:vx,vy=vx*8./speed,vy*8./speed
            p=(4,rng.uniform(-49.,49.),rng.uniform(-29.,29.),vx,vy)
            args=p,rng.uniform(-50.,50.),rng.uniform(-30.,30.),rng.randrange(81),rng.choice((1.45,2.2))
            expected=old._pass_reachable(*args)
            for c in challengers:self.assertEqual(c._pass_reachable(*args),expected)
        baseline=methods('runtime')
        for label in ('reach-local','reach-bound','reach-runtime','reach-step-bound'):
            after=methods(label)
            self.assertEqual({n for n in baseline if after[n]!=baseline[n]},{'_pass_reachable'})

    def test_recorded_moving_wall_and_missed_collections_keep_execution_verification(self):
        data=json.loads((ROOT/'tests/fixtures/execution-reception-cases.json').read_text())
        for case in data['cases']:
            row=case['start'];rid=row['plan_after'][0]
            receiver=next(tuple(p) for p in row['friends'] if p[0]==rid)
            enemies=[tuple(q) for q in row['opponents']]
            expected=None
            for label in ('champion','passing','movement','cover','finishing','lookahead'):
                c=controller(label)
                c._friend_cooldowns={int(k):v for k,v in row['friend_cooldowns'].items()}
                c._enemy_cooldowns={int(k):v for k,v in row['enemy_cooldowns'].items()}
                path=c._pass_path(tuple(case['launch']),tuple(row['ball'][:2]),2.6)
                actual=c._pass_race(receiver,path,enemies,.1,.05,2.6)
                value=(actual,c._next_receive_aim)
                if label=='champion':expected=value
                else:self.assertEqual(value,expected,label)

    def test_lookahead_does_not_change_verified_passes_or_shot_acceptance(self):
        old,new=methods('champion'),methods('lookahead')
        for name in ('_pass_race','_verified_intercept','_receiver_rollout','_shot_option','_keeper_reaches'):
            self.assertEqual(old[name],new[name])


if __name__=='__main__':unittest.main()
