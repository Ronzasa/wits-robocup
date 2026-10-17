"""Pass feasibility regressions, independent of the v9 champion's policy."""
import ast
import importlib.util
import math
import os
from pathlib import Path
import random
import unittest
from unittest.mock import patch

from test_hybrid_planner import FIELD, ROOT
from test_match_tactics import observation

TEAM = Path(os.environ.get('STRICT_TEAM_PATH', ROOT/'experiments/strict-interceptions/team.py'))
spec = importlib.util.spec_from_file_location('strict_pass_candidate', TEAM)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def controller():
    c = module.Guardiola2011()
    c._setup(FIELD)
    return c


class VerifiedPassTests(unittest.TestCase):
    def test_movement_fallback_survives_but_is_not_a_pass_interception(self):
        c = controller()
        p = (3, -30., -20., 0., 0.)
        path = [(0., 10., 20.), (.1, 12., 20.)]
        self.assertTrue(math.isfinite(c._intercept(p, path)[0]))
        self.assertIsNone(c._verified_intercept(p, path))
        self.assertIsNone(c._pass_race(p, path, []))
        self.assertIsNone(c._verified_intercept(p, []))

    def test_dense_pass_forecast_recovers_a_window_between_sparse_samples(self):
        c = controller()
        p = (3, 3., 1.8, 0., 0.)
        path = c._pass_path((0., 0., 30., 0.))
        sparse = [path[n] for n in (0, 4, 8, 12, 16)]
        self.assertIsNone(c._verified_intercept(p, sparse))
        race = c._verified_intercept(p, path)
        self.assertIsNotNone(race)
        self.assertLessEqual(race[0], .15)

    def test_carrier_launch_time_is_counted_once_and_drag_matches_each_step(self):
        c = controller()
        full = c._pass_path((0., 0., 20., 3.))
        launched = c._pass_path((1., .15, 19.7, 2.955), (0., 0.))
        for a, b in zip(full, launched):
            for x, y in zip(a, b):
                self.assertAlmostEqual(x, y)

    def test_dense_wall_forecast_matches_stepped_public_physics(self):
        c = controller()
        x,y,vx,vy = 40.,22.,18.,14.
        path = c._pass_path((x,y,vx,vy))
        for n,tup in enumerate(path):
            if n:
                x,y = x+vx*.05,y+vy*.05
                if abs(y)>29.55:
                    side=math.copysign(1.,y);y=side*59.1-y;vy=-side*abs(vy)*.75
                if abs(x)>49.55:
                    self.assertGreater(abs(y),7.)
                    side=math.copysign(1.,x);x=side*99.1-x;vx=-side*abs(vx)*.75
                vx,vy=vx*.985,vy*.985
            self.assertAlmostEqual(tup[0],n*.05)
            self.assertAlmostEqual(tup[1],x)
            self.assertAlmostEqual(tup[2],y)

    def test_bad_momentum_cannot_be_substituted_with_an_eta(self):
        c = controller()
        p=(3,0.,0.,-8.,0.)
        self.assertFalse(c._pass_reachable(p,2.3,0.,4,c._contact-.02))
        self.assertIsNone(c._verified_intercept(p,[(.2,2.3,0.)]))
        self.assertTrue(c._pass_reachable((3,0.,0.,8.,0.),2.3,0.,4,c._contact-.02))

    def test_no_witness_is_possible_outside_the_speed_cap(self):
        c=controller();rng=random.Random(7103)
        for _ in range(200):
            n=rng.randrange(1,61);angle=rng.uniform(-math.pi,math.pi)
            p=(3,0.,0.,8.*math.cos(angle),8.*math.sin(angle))
            radius=c._range-.08
            far=c._speed*n*c._dt+radius+.01
            self.assertFalse(c._pass_reachable(p,far*math.cos(angle),far*math.sin(angle),n,radius))

    def test_movement_model_matches_native_acceleration_drag_and_speed_cap(self):
        from soccer import SoccerEnv, PlayerAction, TeamAction
        c=controller()
        with SoccerEnv(config_path=str(ROOT/'configs/default.toml'),max_ticks=30) as env:
            env.set_formation(0,[(-45.,22.),(-30.,-22.),(-20.,20.),(-15.,-14.),(-12.,0.)])
            obs=env.reset(seed=317144,kickoff_team=0)['team_a']
            p=obs.my_players[1]
            x,y=p.position;vx,vy=p.velocity
            for n in range(24):
                action=TeamAction({1:PlayerAction(movement=(.6,.8))})
                observations,_=env.step({'team_a':action,'team_b':TeamAction()})
                vx,vy=vx*.9+.6,vy*.9+.8
                speed=math.hypot(vx,vy)
                if speed>8.:vx,vy=vx*8./speed,vy*8./speed
                x,y=x+vx*.05,y+vy*.05
                actual=observations['team_a'].my_players[1]
                # The native engine stores single-precision coordinates.
                self.assertAlmostEqual(actual.position[0],x,delta=5e-5)
                self.assertAlmostEqual(actual.position[1],y,delta=5e-5)
                self.assertAlmostEqual(actual.velocity[0],vx,delta=5e-5)
                self.assertAlmostEqual(actual.velocity[1],vy,delta=5e-5)

    def test_pre_step_kick_and_cooldown_body_are_separate_opportunities(self):
        c=controller();p=(6,0.,0.,0.,0.)
        # It can play the old ball after moving, but cannot body-block the
        # ball three units away once that ball has advanced.
        path=[(0.,2.,0.),(.05,3.,0.)]
        self.assertIsNotNone(c._verified_intercept(p,path,after=.05))
        self.assertIsNone(c._verified_intercept(p,path,cooldown=2,after=.05))
        self.assertIsNotNone(c._verified_intercept(p,[(0.,2.,0.),(.05,1.,0.)],cooldown=999,after=.05))

    def test_current_kick_range_is_not_a_future_kick_witness(self):
        c=controller()
        # Already moving away too fast to play the pre-step ball after the
        # engine's mandatory movement step; being in range now is insufficient.
        p=(6,0.,0.,-8.,0.)
        self.assertLess(math.dist(p[1:3],(2.1,0.)),c._range)
        self.assertIsNone(c._verified_intercept(p,[(0.,2.1,0.),(.05,3.1,0.)]))

    def test_receiver_cooldown_is_used_in_pass_approval(self):
        c=controller();p=(4,0.,0.,0.,0.);path=[(0.,2.,0.),(.05,3.,0.)]
        self.assertIsNotNone(c._pass_race(p,path,[],after=.05))
        c._friend_cooldowns[4]=2
        self.assertIsNone(c._pass_race(p,path,[],after=.05))

    def test_full_physical_contact_radii_are_used_for_opponents(self):
        c=controller()
        # A legal post-movement kick at 2.19 units must not disappear behind
        # a receiver-control buffer of 2.12 units.
        path=[(0.,0.,0.),(.05,0.,1.5)]
        enemy=(6,2.24,0.,0.,0.)
        self.assertIsNotNone(c._verified_intercept(enemy,path))
        self.assertIsNone(c._pass_race((4,0.,1.6,0.,0.),path,[enemy],after=.05))
        # On cooldown, a legal body obstruction also uses the full radius.
        self.assertIsNotNone(c._verified_intercept((6,1.49,0.,0.,0.),
                              [(0.,0.,-1.5),(.05,0.,0.)],cooldown=999))

    def test_above_cap_initial_velocity_requires_the_stepped_witness(self):
        c=controller()
        # Large collision-like velocity cannot be used as uncapped coasting.
        # This target passes the loose speed/disk bounds and the final-speed
        # test of an uncapped constant input, but its intermediate speeds are
        # illegal. The capped pursuit cannot verify the contact.
        self.assertFalse(c._pass_reachable((4,0.,0.,12.,0.),2.4,1.9,5,c._contact))

    def test_a_goal_terminates_the_pass_route(self):
        c=controller()
        path=c._pass_path((49.,0.,22.,0.))
        self.assertEqual(len(path),1)
        self.assertIsNone(c._verified_intercept((4,20.,0.,0.,0.),path))

    def test_opponent_without_interception_has_infinite_arrival_not_eta(self):
        c=controller();receiver=(3,20.,0.,0.,0.);opponent=(6,-30.,-20.,0.,0.)
        path=[(.1,20.,0.),(.15,21.,0.)]
        with patch.object(c,'_intercept',side_effect=AssertionError('heuristic used for pass')):
            own,enemy=c._pass_race(receiver,path,[opponent])
        self.assertEqual(own[0],.1)
        self.assertTrue(math.isinf(enemy))

    def test_earlier_opponent_or_tied_arrival_rejects_pass(self):
        c=controller();path=c._pass_path((0.,0.,20.,0.))
        self.assertIsNone(c._pass_race((3,12.,0.,0.,0.),path,[(6,4.,0.,0.,0.)],.1))
        self.assertIsNone(c._pass_race((3,12.,0.,0.,0.),path,[(6,12.,0.,0.,0.)]))

    def test_links_and_transition_never_consult_movement_fallback(self):
        c=controller();p=(2,-1.7,0.,0.,0.);r=(3,10.,0.,0.,0.);enemies=[(5,47.,25.,0.,0.)]
        c._transition_active=True
        with patch.object(c,'_intercept',side_effect=AssertionError('heuristic used for pass')):
            self.assertIsNotNone(c._link_option(p,0.,0.,0.,0.,r,enemies,10.,0.,14.))
            self.assertIsNotNone(c._search_links(p,0.,0.,0.,0.,[p,r],enemies))
            self.assertIsNotNone(c._transition_release(p,0.,0.,0.,0.,[p,r],enemies))
        with patch.object(c,'_verified_intercept',return_value=None):
            self.assertIsNone(c._search_links(p,0.,0.,0.,0.,[p,r],enemies))
            self.assertIsNone(c._transition_release(p,0.,0.,0.,0.,[p,r],enemies))

    def test_endwall_requires_post_bounce_witness_and_checks_first_leg(self):
        c=controller();p=(2,33.3,20.,0.,0.);r=(4,43.,5.,0.,0.)
        friends=[(0,-47.,0.,0.,0.),p,r];enemies=[(5,47.,-20.,0.,0.)]
        with patch.object(c,'_intercept',side_effect=AssertionError('heuristic used for pass')):
            self.assertIsNotNone(c._endwall_link(p,35.,20.,0.,0.,friends,enemies))
        original=c._verified_intercept
        def unreachable(q,*args,**kwargs):
            return None if q[0]==4 else original(q,*args,**kwargs)
        with patch.object(c,'_verified_intercept',side_effect=unreachable):
            self.assertIsNone(c._endwall_link(p,35.,20.,0.,0.,friends,enemies))
        c._enemy_cooldowns={6:999}
        self.assertIsNone(c._endwall_link(p,35.,20.,0.,0.,friends,enemies+[(6,36.,19.2,0.,0.)]))

    def test_sidewall_requires_receiver_and_opponent_checks_on_both_legs(self):
        c=controller();p=(2,-11.7,22.,0.,0.);r=(4,8.,10.,0.,0.)
        friends=[(0,-47.,0.,0.,0.),p,r];enemies=[(5,47.,-25.,0.,0.),(6,-2.,16.,0.,0.)]
        with patch.object(c,'_intercept',side_effect=AssertionError('heuristic used for pass')):
            option=c._bank_release(p,-10.,22.,0.,0.,friends,enemies)
        self.assertIsNotNone(option)
        sx,sy=c._requested_velocity(0.,0.,option[1])
        launch=c._carrier_contact(p,-10.,22.,sx,sy,option[2])
        _,bounce=c._bank_path(*launch)
        path=c._pass_path(launch,(-10.,22.))
        race=c._pass_race(r,path,enemies,c.BANK_MARGIN,bounce+c._dt,2.2)
        self.assertIsNotNone(race)
        self.assertGreater(race[0][0],bounce)
        # A cooldown body on the outbound or return leg defeats this route.
        for t in (.2,bounce+.2):
            _,x,y=min(path,key=lambda s:abs(s[0]-t))
            c._enemy_cooldowns[7]=999
            self.assertIsNone(c._pass_race(r,path,enemies+[(7,x,y,0.,0.)],c.BANK_MARGIN,bounce+c._dt,2.2))
        original=c._verified_intercept
        with patch.object(c,'_verified_intercept',side_effect=lambda q,*a,**k: None if q[0]==4 else original(q,*a,**k)):
            self.assertIsNone(c._bank_release(p,-10.,22.,0.,0.,friends,enemies))

    def test_unsafe_legacy_pass_does_not_keep_a_reception_plan(self):
        c=controller();c.WALL_PASSING=False;p=(2,-1.7,0.,0.,0.);r=(3,-45.,25.,0.,0.)
        def legacy(*args):
            c._pass_plan=(3,-45.,25.)
            return ((1.,0.),1.)
        with patch.object(c,'_legacy_choose_kick',side_effect=legacy):
            self.assertIsNotNone(c._legacy_policy_kick(p,0.,0.,0.,0.,[p,r],[]))
        self.assertIsNone(c._pass_plan)

    def test_verified_legacy_direct_pass_keeps_its_actual_kick(self):
        c=controller();p=(2,-1.7,0.,0.,0.);r=(3,10.,0.,0.,0.);kick=((1.,0.),1.)
        def legacy(*args):
            c._pass_plan=(3,10.,0.)
            return kick
        with patch.object(c,'_legacy_choose_kick',side_effect=legacy),patch.object(c,'_intercept',side_effect=AssertionError('heuristic pass ETA')):
            self.assertEqual(c._legacy_policy_kick(p,0.,0.,0.,0.,[p,r],[]),kick)
        self.assertEqual(c._pass_plan[0],3)

    def test_live_unreachable_or_contested_plan_is_cancelled_for_both_types(self):
        for bank in (False,True):
            c=controller();c._receive_plan=(4,2,150)
            if bank:c._bank_receive=(4,2,(8.,0.))
            with patch.object(c,'_pass_race',return_value=None) as strict:
                c.act(observation(ball=(0.,5.,12.,0.),last=2))
            self.assertTrue(strict.called)
            self.assertIsNone(c._receive_plan)
            self.assertIsNone(c._bank_receive)

    def test_new_direct_and_bank_plans_require_actual_launch_verification(self):
        friends=[(0,-47.,0.,0.,0.),(1,-20.,-10.,0.,0.),(2,-1.7,0.,0.,0.),
                 (3,-10.,20.,0.,0.),(4,40.,25.,0.,0.)]
        for bank in (False,True):
            c=controller()
            def choose(*args):
                c._pass_plan=(4,40.,25.)
                c._bank_plan=c._pass_plan if bank else None
                return ((1.,0.),1.)
            with patch.object(c,'_choose_kick',side_effect=choose):
                action=c.act(observation(ball=(0.,0.,0.,0.),friends=friends,enemies=[],last=2,kickers=(2,)))
            self.assertIsNotNone(action.players[2].kick_direction)
            self.assertIsNone(c._receive_plan)
            self.assertIsNone(c._bank_receive)

    def test_live_feasible_plan_is_maintained(self):
        friends=[(0,-47.,0.,0.,0.),(1,-20.,-10.,0.,0.),(2,-5.,0.,0.,0.),
                 (3,-10.,20.,0.,0.),(4,10.,5.,0.,0.)]
        for bank in (False,True):
            c=controller();c._receive_plan=(4,2,150)
            if bank:c._bank_receive=(4,2,(-40.,-20.))
            c.act(observation(ball=(0.,5.,14.,0.),friends=friends,enemies=[],last=2))
            self.assertEqual(c._receive_plan,(4,2,150))
            if bank:self.assertNotEqual(c._bank_receive[2],(-40.,-20.))

    def test_live_plan_is_cancelled_when_an_opponent_arrives_first(self):
        c=controller();c._receive_plan=(4,2,150)
        friends=[(0,-47.,0.,0.,0.),(1,-20.,-10.,0.,0.),(2,-5.,0.,0.,0.),
                 (3,-10.,20.,0.,0.),(4,20.,5.,0.,0.)]
        c.act(observation(ball=(0.,5.,14.,0.),friends=friends,enemies=[(6,10.,5.,0.,0.)],last=2))
        self.assertIsNone(c._receive_plan)

    def test_movement_shots_and_keeper_helpers_are_identical_to_champion(self):
        champion=ROOT/'champions/v9.0/team.py'
        if not champion.exists():champion=ROOT/'my-team/team.py'
        def methods(path):
            cls=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef))
            return {n.name:ast.dump(n,include_attributes=False) for n in cls.body if isinstance(n,ast.FunctionDef)}
        old,new=methods(champion),methods(TEAM)
        for name in ('_intercept','_eta','_trajectory','_move','_cover_shape','_keeper_reaches',
                     '_shot_option','_shot_velocity','_shot_contact_margin','_goal_path'):
            self.assertEqual(old[name],new[name],name)


if __name__=='__main__':
    unittest.main()
