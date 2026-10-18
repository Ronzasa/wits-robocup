"""Independent NOVA policy contracts and reused physics equivalence."""
import ast,hashlib,importlib.util,json,math,random,sys,types,unittest
from pathlib import Path
from types import SimpleNamespace as S
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'student-sdk'))
spec=importlib.util.spec_from_file_location('nova_builder',ROOT/'tools/nova/build.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
FIELD=S(width=100.,height=60.,simulation_hz=20,max_speed=8.,acceleration=20.,ball_friction=.985,
    kick_impulse=22.,kick_range=2.2,my_goal=(-50.,0.),opponent_goal=(50.,0.),goal_width=14.,
    centre_circle_radius=9.,player_radius=1.,ball_radius=.45)

def load(code):
    m=types.ModuleType('nova_test');exec(compile(code,'team.py','exec'),m.__dict__);return m
def controller(joint=True,params=None):
    c=load(builder.build(params,joint)).NovaController();c._setup(FIELD);return c
def observation(ball=(0.,0.,0.,0.),friends=None,enemies=None,kickers=(),tick=100,score=(0,0),holder=None,last=None):
    friends=friends or [(0,-47.,0.,0.,0.),(1,-15.,9.,0.,0.),(2,-1.7,0.,0.,0.),(3,10.,0.,0.,0.),(4,20.,-12.,0.,0.)]
    enemies=enemies or [(5,47.,24.,0.,0.),(6,35.,25.,0.,0.),(7,35.,-25.,0.,0.),(8,40.,15.,0.,0.),(9,40.,-15.,0.,0.)]
    def p(q):return S(id=q[0],position=q[1:3],velocity=q[3:5],kick_cooldown_ticks=0)
    return S(field=FIELD,tick=tick,score=score,time_remaining=.5,my_players=[p(q) for q in friends],opponents=[p(q) for q in enemies],can_kick=set(kickers).__contains__,
        ball=S(position=ball[:2],velocity=ball[2:],controlling_team=holder,controlling_player=None,last_touch=last))

class NovaTests(unittest.TestCase):
    def test_independent_architecture_and_permitted_standalone_module(self):
        text=builder.build(joint=True);tree=ast.parse(text);classes=[n for n in tree.body if isinstance(n,ast.ClassDef)]
        self.assertEqual(len(classes),1);self.assertEqual(classes[0].name,'NovaController')
        self.assertEqual(classes[0].bases[0].id,'TeamController')
        self.assertFalse(any('_legacy' in n.name or '_choose_kick'==n.name or '_cover_shape'==n.name for n in classes[0].body if isinstance(n,ast.FunctionDef)))
        imports=[n.module if isinstance(n,ast.ImportFrom) else n.names[0].name for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
        self.assertEqual(imports,['math','soccer'])
        self.assertEqual(hashlib.sha256((ROOT/'my-team/team.py').read_bytes()).hexdigest(),builder.CHAMPION)

    def test_reused_methods_have_exactly_the_frozen_physics_source(self):
        old=builder.methods((ROOT/'my-team/team.py').read_text());new=builder.methods(builder.build(joint=True))
        shared=[k for k in old if k in new]
        self.assertEqual(set(shared),set(builder.PHYSICS)|{'act','reset','__init__','initial_formation','_setup'})
        for name in builder.PHYSICS:self.assertEqual(old[name],new[name],name)

    def test_physical_witnesses_movement_and_contact_equivalence(self):
        old=load((ROOT/'my-team/team.py').read_text()).Guardiola2011();old._setup(FIELD)
        new=controller();rng=random.Random(901106)
        for _ in range(2000):
            p=(3,rng.uniform(-48,48),rng.uniform(-28,28),rng.uniform(-8,8),rng.uniform(-8,8))
            x,y=rng.uniform(-49,49),rng.uniform(-29,29);n=rng.randrange(81);radius=rng.choice((1.45,2.2))
            self.assertEqual(old._pass_reachable(p,x,y,n,radius),new._pass_reachable(p,x,y,n,radius))
            self.assertEqual(old._move(p,(x,y)),new._move(p,(x,y)))
            v=(rng.uniform(-30,30),rng.uniform(-30,30));move=new._move(p,(x,y))
            self.assertEqual(old._carrier_contact(p,x,y,*v,move),new._carrier_contact(p,x,y,*v,move))

    def test_actual_receiver_rollout_and_dense_wall_forecast_equivalence(self):
        old=load((ROOT/'my-team/team.py').read_text()).Guardiola2011();old._setup(FIELD);old.FIRST_TOUCH=True
        new=controller()
        for launch,origin in [((0.,27.,12.,15.),(0.,26.)),((.7,0.,14.,0.),(0.,0.)),((32.,22.,23.,18.),(31.,21.))]:
            a=old._pass_path(launch,origin,2.2);b=new._pass_path(launch,origin,2.2);self.assertEqual(a,b)
            p=(3,10.,20.,-3.,2.)
            for cooldown in (0,3,20):
                self.assertEqual(old._verified_intercept(p,a,cooldown),new._verified_intercept(p,b,cooldown))
                self.assertEqual(old._receiver_rollout(p,a,(12.,24.),cooldown),new._receiver_rollout(p,b,(12.,24.),cooldown))

    def test_live_ball_at_conservative_goal_aperture_never_indexes_empty_path(self):
        c=controller();ball=(49.95082473754883,5.589890003204346,23.063844680786133,.7747848033905029)
        self.assertEqual(c._pass_path(ball),[])
        action=c.act(observation(ball=ball,tick=1352))
        self.assertEqual(len(action.players),5)

    def test_heuristic_chase_cannot_be_used_to_approve_a_pass(self):
        c=controller();c._estimate_chase=lambda *args:(_ for _ in ()).throw(AssertionError('heuristic pass'))
        path=c._pass_path((.7,0.,14.,0.),(0.,0.),2.2)
        self.assertIsNotNone(c._collect((3,10.,0.,0.,0.),path,[(5,47.,25.,0.,0.)]))
        c._enemy_cooldowns={6:999}
        self.assertIsNone(c._collect((3,10.,0.,0.,0.),path,[(6,2.,0.,0.,0.)]))

    def test_unavailable_or_sparse_receiving_opportunity_is_infeasible(self):
        c=controller();p=(3,40.,25.,-8.,0.)
        self.assertIsNone(c._collect(p,[(0.,0.,0.),(.05,1.,0.)],[]))
        self.assertIsNone(c._verified_intercept((3,0.,0.,0.,0.),[(1.,10.,0.)]))

    def test_compatible_named_reception_locks_receiver_and_preserves_another_cover(self):
        c=controller(params={'weights':[0.,1.,30.,1.,1.,0.,0.,-10.,-2.,.2,-1.,0.]})
        obs=observation(kickers=(2,),holder=0,last=2)
        action=c.act(obs)
        self.assertIsNotNone(c._receive)
        pid,passer,aim,expiry=c._receive
        self.assertNotEqual(pid,c._cover_id);self.assertNotEqual(pid,passer)
        p=next(p for p in obs.my_players if p.id==pid)
        self.assertEqual(action.players[pid].movement,c._move((p.id,*p.position,*p.velocity),aim))
        self.assertLessEqual(c._plans_evaluated,3);self.assertLessEqual(c._response_steps,60)

    def test_every_parameterized_command_is_finite_and_bounded(self):
        for joint in (False,True):
            c=controller(joint);a=c.act(observation(ball=(15.,0.,0.,0.),friends=[(0,-47.,0.,0.,0.),(1,-4.,0.,0.,0.),(2,13.3,0.,0.,0.),(3,25.,-9.,0.,0.),(4,27.,12.,0.,0.)],kickers=(2,),holder=0,last=2))
            self.assertEqual(set(a.players),set(range(5)))
            for p in a.players.values():
                self.assertTrue(all(math.isfinite(v) for v in p.movement));self.assertLessEqual(math.hypot(*p.movement),1.000001)
                if p.kick_direction is not None:self.assertTrue(0.<=p.kick_power<=1.)

    def test_restart_respects_the_protected_centre_circle(self):
        c=controller();a=c.act(observation(holder=1,tick=0))
        for p in a.players.values():self.assertIsNone(p.kick_direction)
        self.assertEqual(len(a.players),5)

    def test_expired_or_opponent_intercepted_plan_is_cancelled(self):
        c=controller();c._previous_score=(0,0);c._receive=(3,2,(8.,0.),150)
        c.act(observation(ball=(4.,0.,12.,0.),last=6,tick=120))
        self.assertIsNone(c._receive)

    def test_opponent_control_is_not_overridden_by_a_tied_chase_estimate(self):
        c=controller();seen=[];original=c._shape
        def observed(*args,**kwargs):
            seen.append(args[5]);return original(*args,**kwargs)
        c._shape=observed
        c.act(observation(holder=1,kickers=()))
        self.assertEqual(seen,[False])

    def test_distilled_parameters_are_actually_embedded(self):
        c=controller(params={'config':[9.,5.,8.,2.,2.1,.07,.2,.5],'weights':[1.]*12})
        self.assertEqual(c.CONFIG[0],9.);self.assertEqual(c.WEIGHTS,(1.,)*12)

    def test_keeper_never_selects_a_carry_it_will_not_follow_next_tick(self):
        friends=[(0,-47.7,0.,0.,0.),(1,-8.,10.,0.,0.),(2,-8.,-10.,0.,0.),(3,0.,15.,0.,0.),(4,0.,-15.,0.,0.)]
        obs=observation(ball=(-46.,0.,0.,0.),friends=friends,kickers=(0,),holder=0,last=0)
        old=controller(params={'framework':'r4'});new=controller()
        a=old.act(obs);b=new.act(obs)
        self.assertIsNotNone(a.players[0].kick_direction);self.assertIsNotNone(b.players[0].kick_direction)
        self.assertLess(a.players[0].kick_power,.5)
        self.assertGreater(b.players[0].kick_power,.9)

    def test_support_keeps_the_future_reception_point_while_ball_is_in_flight(self):
        c=controller();c._previous_score=(0,0);c._receive=(3,2,(7.,0.),150)
        seen=[];original=c._shape
        def observed(*args,**kwargs):
            seen.append(args[7] if len(args)>7 else kwargs.get('future'));return original(*args,**kwargs)
        c._shape=observed;c.act(observation(ball=(4.,0.,10.,0.),last=2,tick=110))
        self.assertIsNotNone(c._receive);self.assertIsNotNone(seen[0])
        self.assertGreater(seen[0][0],4.)

    def test_modeled_carrier_follows_the_moving_ball_instead_of_old_kick_origin(self):
        c=controller();o=observation(kickers=(2,),holder=0,last=2)
        friends=[(p.id,*p.position,*p.velocity) for p in o.my_players]
        enemies=[(p.id,*p.position,*p.velocity) for p in o.opponents]
        path=c._pass_path((0.,0.,0.,0.));targets,_=c._shape(friends,enemies,(0.,0.,0.,0.),path,friends[2],True)
        node=next(n for n in c._proposals(friends[2],friends,enemies,(0.,0.,0.,0.),targets) if n['kind']=='carry')
        calls=[];original=c._move
        def moved(p,target,*args):
            if p[0]==2:calls.append(target)
            return original(p,target,*args)
        c._move=moved;c._response(node,friends,enemies,(0.,0.,0.,0.),0)
        self.assertGreater(len(calls),1)
        self.assertGreater(calls[0][0],.3)
        self.assertNotEqual(calls[0],calls[-1])

    def test_response_beam_does_not_starve_a_distinct_feasible_action_family(self):
        c=controller();seen=[]
        nodes=[{'kind':'pass','value':v,'kick':((1.,0.),v/10.),'features':[0.]*12} for v in (4.,3.,2.)]
        nodes.append({'kind':'shot','value':1.,'kick':((0.,1.),1.),'features':[0.]*12})
        c._proposals=lambda *args:nodes
        def response(node,*args):seen.append(node['kind']);return (10. if node['kind']=='shot' else 0.),0
        c._response=response
        chosen=c._select((2,0.,0.,0.,0.),[],[],(0.,0.,0.,0.),{},(0,0),1.)
        self.assertIn('shot',seen);self.assertEqual(chosen['kind'],'shot')
        self.assertLessEqual(c._plans_evaluated,3)

    def test_registered_population_sources_reconstruct_exactly(self):
        for path in sorted((ROOT/'docs/nova-1').glob('generation-*-registration.json')):
            for row in json.loads(path.read_text())['population']:
                v=row['vector'];framework=builder.framework_for(row['name'])
                code=builder.build({'config':v[:8],'weights':v[8:]+[.4],'framework':framework},True)
                self.assertEqual(hashlib.sha256(code.encode()).hexdigest(),row['sha256'],row['name'])

    def test_body_aware_release_preserves_a_forward_kick_when_braking_is_executable(self):
        # Native development frame 495: moving back into a forward kick
        # rebounds it toward our goal; a legal brake avoids that contact.
        c=controller(params={'framework':'r7-pass'})
        p=(3,-27.50908851623535,1.678697109222412,-7.894841194152832,1.2928566932678223)
        ball=(-29.600231170654297,2.02117657661438,15.737109184265137,-5.779429912567139)
        u=(9./math.hypot(9.,-6.),-6./math.hypot(9.,-6.));desired=(u[0]*7.5,u[1]*7.5)
        kick=c._kick_to_velocity(*ball[2:],*desired)
        self.assertIsNotNone(kick)
        move=c._move(p,(ball[0]+.3,ball[1]));brake=tuple(-v/math.hypot(*p[3:]) for v in p[3:])
        old=c._carrier_contact(p,*ball[:2],*c._requested_velocity(*ball[2:],kick),move)
        release=c._release_step(p,ball,kick,[move,brake],desired)
        self.assertLess(old[2],0.);self.assertGreater(release[1][2],0.)
        self.assertEqual(release[0],brake);self.assertLessEqual(math.hypot(*release[0]),1.000001)

    def test_selected_source_is_the_measured_frozen_policy(self):
        path=ROOT/'docs/nova-1/selected-policy.json'
        if not path.exists():self.skipTest('Native development selection is not complete.')
        record=json.loads(path.read_text());row=record['selected'];v=row['vector']
        framework=builder.framework_for(row['name'])
        code=builder.build({'config':v[:8],'weights':v[8:]+[.4],'framework':framework},True)
        self.assertEqual(hashlib.sha256(code.encode()).hexdigest(),record['candidate_sha256'])
        self.assertEqual((ROOT/record['candidate_path']).read_text(),code)
        self.assertTrue(row['intake_ok'])
        c=load(code).NovaController();c._setup(FIELD)
        obs=observation(kickers=(2,),holder=0,last=2)
        a=c.act(obs)
        self.assertEqual(len(a.players),5)
        self.assertLessEqual(c._plans_evaluated,3);self.assertLessEqual(c._response_steps,60)
        self.assertTrue(all(math.isfinite(x) for p in a.players.values() for x in p.movement))

if __name__=='__main__':unittest.main()
