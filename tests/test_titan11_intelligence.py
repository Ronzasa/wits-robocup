"""TITAN-11 subsystem regressions, including frozen native observation replay."""
import ast,gzip,hashlib,importlib.util,json,math,random,sys,types,unittest
from pathlib import Path
from types import SimpleNamespace as S
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/titan11'))
from build import build,CHAMPION,FLAGS
from test_hybrid_planner import FIELD
from test_match_tactics import FRIENDS,ENEMIES,observation

def module(flags=(),params=None,runtime=True):
    m=types.ModuleType('titan11_test');exec(compile(build(flags,params,runtime),'team.py','exec'),m.__dict__);return m

def controller(flags=(),params=None):
    c=module(flags,params).Guardiola2011();c._setup(FIELD);return c

class IntelligenceTests(unittest.TestCase):
    def test_explicit_reduced_power_shots_are_legal_distinct_and_contact_checked(self):
        c=controller(['finishing'],{'finishing_revision':2});c._ti_options=[]
        c._ti_finesse((2,28.3,0.,0.,0.),30.,0.,0.,0.,[])
        powers=[n[1][1][1] for n in c._ti_options]
        self.assertEqual(len(powers),2)
        self.assertTrue(all(0.<power<1. for power in powers))
        self.assertNotEqual(powers[0],powers[1])
        c._ti_options=[]
        c._ti_finesse((2,-20.,0.,0.,0.),30.,0.,0.,0.,[])
        self.assertEqual(c._ti_options,[])

    def test_third_man_runs_before_verified_receiver_has_collected(self):
        c=controller(['coordinated'],{'coordination_revision':2})
        o=observation(ball=(0.,5.,15.,0.),holder=None,last=2,tick=101)
        c._ti_observe(o);c._shape_cover_id=1;c._receive_plan=(3,2,140)
        targets={p[0]:(p[1],p[2]) for p in FRIENDS};before=dict(targets)
        c._ti_targets(o,False,FRIENDS,ENEMIES,FRIENDS[2],targets,True)
        self.assertFalse(c._ti_secure)
        self.assertIsNotNone(c._ti_third)
        self.assertNotEqual(targets[4],before[4])
        for pid in (0,1,2,3):self.assertEqual(targets[pid],before[pid])

    def test_wall_playbook_collects_after_bounce_and_rejects_early_body_block(self):
        c=controller(['playbooks'])
        passer=(2,-1.7,20.,0.,0.);receiver=(4,12.,20.,0.,0.)
        friends=[(0,-47.,0.,0.,0.),passer,receiver];opponents=[(5,47.,-20.,0.,0.)]
        option=c._ti_wall(passer,0.,20.,0.,0.,friends,opponents)
        self.assertIsNotNone(option)
        launch=c._carrier_contact(passer,0.,20.,*c._requested_velocity(0.,0.,option[1]),option[2])
        _,bounce=c._bank_path(*launch)
        race=c._pass_race(receiver,c._pass_path(launch,(0.,20.),2.),opponents,.16,bounce+c._dt,2.)
        self.assertIsNotNone(race)
        self.assertGreater(race[0][0],bounce)
        c._enemy_cooldowns={6:999}
        self.assertIsNone(c._ti_wall(passer,0.,20.,0.,0.,friends,[*opponents,(6,2.,23.,0.,0.)]))

    def test_byte_frozen_champion(self):
        for p in ('my-team/team.py','champions/v10.0/team.py'):
            self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),CHAMPION)

    def test_standalone_single_controller_and_imports(self):
        tree=ast.parse(build(FLAGS));classes=[n for n in tree.body if isinstance(n,ast.ClassDef)]
        self.assertEqual(len(classes),1)
        self.assertEqual(classes[0].bases[0].id,'TeamController')
        imports=[n.module if isinstance(n,ast.ImportFrom) else n.names[0].name for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
        self.assertEqual(imports,['math','soccer'])
        self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('open','exec','eval','__import__') for n in ast.walk(tree)))

    def test_all_features_independent(self):
        for flag in FLAGS:
            c=controller([flag]);self.assertEqual([f for f in FLAGS if getattr(c,'TI_'+f.upper())],[flag])
            a=c.act(observation(kickers=(2,),holder=2,last=2))
            self.assertEqual(len(a.players),5)
            for command in a.players.values():self.assertLessEqual(math.hypot(*command.movement),1.000001)

    def test_predictive_budget(self):
        c=controller(['predictive','finishing','learning']);c.act(observation(ball=(15.,0.,0.,0.),friends=[(0,-47.,0.,0.,0.),(1,-10.,0.,0.,0.),(2,13.3,0.,0.,0.),(3,26.,-8.,0.,0.),(4,29.,5.,0.,0.)],kickers=(2,),holder=2,last=2))
        self.assertLessEqual(c._ti_rollouts,3);self.assertLessEqual(c._ti_shot_checks,2)

    def test_strict_unavailable_reception_stays_infeasible(self):
        c=controller(['predictive']);c._ti_options=[]
        q=(3,25.,0.,-8.,0.)
        o=c._link_option((2,-1.7,0.,0.,0.),0.,0.,0.,0.,q,[(6,3.,0.,0.,0.)],25.,0.,26.)
        self.assertIsNone(o);self.assertEqual(c._ti_options,[])

    def test_execution_checked_for_moving_receiver(self):
        c=controller(['predictive']);c._ti_options=[]
        option=c._link_option((2,-1.7,0.,0.,0.),0.,0.,0.,0.,(3,10.,0.,4.,0.),[(5,47.,25.,0.,0.)],12.,0.,14.)
        self.assertIsNotNone(option)
        node=c._ti_options[0];self.assertIsNotNone(node[2]);self.assertIsNotNone(node[3])
        route=c._receiver_rollout((3,10.,0.,4.,0.),node[2],node[3],0,.05,1.8)
        self.assertIsNotNone(route)

    def test_wall_forecast_has_both_legs_and_dense_steps(self):
        c=controller(['playbooks']);path=c._pass_path((0.,27.,12.,15.),(0.,26.),2.)
        ys=[s[2] for s in path]
        self.assertTrue(any(b<a for a,b in zip(ys,ys[1:])))
        self.assertTrue(all(abs(b[0]-a[0]-.05)<1e-8 for a,b in zip(path,path[1:])))
        c._enemy_cooldowns={6:999}
        self.assertIsNotNone(c._verified_intercept((6,0.,26.,0.,0.),path,999))

    def test_keeper_response_momentum_cooldown_and_body(self):
        c=controller(['finishing']);path=[(i*.05,40.+i*.5,0.) for i in range(20)]
        keeper=(5,47.,0.,0.,0.)
        self.assertTrue(math.isfinite(c._ti_keeper_response(keeper,path)))
        c._enemy_cooldowns={5:999}
        body=c._ti_keeper_response(keeper,path)
        self.assertTrue(math.isfinite(body))

    def test_far_keeper_does_not_get_heuristic_contact(self):
        c=controller(['finishing']);path=[(i*.05,44.+i*.5,0.) for i in range(10)]
        self.assertEqual(c._ti_keeper_response((5,47.,28.,0.,0.),path),math.inf)

    def test_shot_requires_actual_launch(self):
        c=controller(['finishing']);c._ti_rollouts=0
        node=('shot',(8.,((1.,0.),1.),(0.,0.),None),None,None)
        self.assertIsNone(c._ti_evaluate(node,(2,-20.,0.,0.,0.),20.,0.,0.,0.,FRIENDS,ENEMIES))

    def test_coordination_preserves_keeper_chaser_receiver_cover(self):
        c=controller(['coordinated']);o=observation(holder=2,last=2,kickers=(2,));c._ti_observe(o);c._shape_cover_id=1;c._receive_plan=(3,2,150)
        targets={p[0]:(p[1]+1.,p[2]) for p in FRIENDS};before=dict(targets)
        c._ti_targets(o,False,FRIENDS,ENEMIES,FRIENDS[2],targets,True)
        for pid in (0,1,2,3):self.assertEqual(targets[pid],before[pid])

    def test_coordination_triangle_keeps_spacing(self):
        c=controller(['coordinated']);o=observation(holder=2,last=2,kickers=(2,));c._ti_observe(o);c._shape_cover_id=1
        targets={p[0]:(p[1],p[2]) for p in FRIENDS}
        c._ti_targets(o,False,FRIENDS,ENEMIES,FRIENDS[2],targets,True)
        self.assertGreaterEqual(math.dist(targets[3],targets[4]),7.)

    def test_third_man_run_is_bounded_and_resets_on_goal(self):
        c=controller(['coordinated']);o=observation(holder=2,last=2,kickers=(2,));c._ti_observe(o);c._ti_third=(4,3,120)
        c._ti_observe(observation(score=(1,0),tick=101));self.assertIsNone(c._ti_third)

    def test_secured_possession_immediately_disables_defence(self):
        c=controller(['defence']);o=observation(holder=2,last=2,kickers=(2,));c._ti_observe(o);c._shape_cover_id=1
        targets={p[0]:(p[1],p[2]) for p in FRIENDS};before=dict(targets)
        c._ti_targets(o,False,FRIENDS,ENEMIES,FRIENDS[2],targets,False)
        self.assertEqual(targets,before);self.assertEqual(c._ti_defence_ids,())

    def test_emergency_double_defence_reserves_outlet_and_locked_roles(self):
        c=controller(['defence']);friends=[(0,-47.,0.,0.,0.),(1,-25.,0.,0.,0.),(2,-19.,0.,0.,0.),(3,-27.,8.,0.,0.),(4,0.,-5.,0.,0.)]
        enemies=[(5,47.,0.,0.,0.),(6,-20.,0.,-6.,0.),(7,-28.,8.,-6.,0.),(8,-28.,-8.,-6.,0.),(9,0.,20.,0.,0.)]
        o=observation(ball=(-20.,0.,0.,0.),friends=friends,enemies=enemies,holder=6,last=6)
        c._ti_observe(o);c._ti_loss=99;c._shape_cover_id=1
        targets={p[0]:(p[1],p[2]) for p in friends};before=dict(targets)
        c._ti_targets(o,False,friends,enemies,friends[2],targets,False)
        self.assertLessEqual(len(c._ti_defence_ids),2)
        self.assertTrue(set(c._ti_defence_ids).isdisjoint((0,2)))
        self.assertGreaterEqual(len(set(range(1,5))-{2}-set(c._ti_defence_ids)),1)
        self.assertEqual(targets[0],before[0]);self.assertEqual(targets[2],before[2])

    def test_imminent_goalbound_shot_preserves_v10_cover(self):
        c=controller(['defence']);o=observation(ball=(-35.,0.,-20.,0.),holder=None,last=6);c._ti_observe(o);c._shape_cover_id=1
        targets={p[0]:(p[1],p[2]) for p in FRIENDS};before=dict(targets)
        c._ti_targets(o,False,FRIENDS,ENEMIES,FRIENDS[2],targets,False);self.assertEqual(targets,before)

    def test_protected_opponent_restart_does_not_override_targets(self):
        c=controller(FLAGS);o=observation(holder=6,last=6);c._ti_observe(o)
        targets={p[0]:(p[1],p[2]) for p in FRIENDS};before=dict(targets)
        c._ti_targets(o,True,FRIENDS,ENEMIES,FRIENDS[2],targets,False);self.assertEqual(targets,before)

    def test_legal_formation_outside_centre_circle(self):
        for flag in FLAGS:
            f=controller([flag]).initial_formation(S(**vars(FIELD),width=100.))
            for x,y in f:self.assertGreaterEqual(math.hypot(x,y),FIELD.centre_circle_radius+1.)

    def test_learning_is_compact_and_finite(self):
        c=controller(['learning'],{'value_weights':[.1]*8,'shot_weights':[.2]*6})
        self.assertTrue(math.isfinite(c._ti_future_value(10.,3.,8.,FRIENDS,ENEMIES,True)))
        self.assertGreater(c._ti_sigmoid(100.),.99);self.assertLess(c._ti_sigmoid(-100.),.01)

    def test_reach_runtime_preserves_original_queries(self):
        a=controller([],{});b=module([],runtime=False).Guardiola2011();b._setup(FIELD)
        rng=random.Random(7183)
        for _ in range(3000):
            p=(2,rng.uniform(-48,48),rng.uniform(-28,28),rng.uniform(-8,8),rng.uniform(-8,8))
            x,y=rng.uniform(-49,49),rng.uniform(-29,29);n=rng.randrange(81);r=rng.choice([1.45,2.2])
            self.assertEqual(a._pass_reachable(p,x,y,n,r),b._pass_reachable(p,x,y,n,r))

if __name__=='__main__':unittest.main()
