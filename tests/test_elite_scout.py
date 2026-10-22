"""Safety and execution regressions for independently observed hypotheses."""
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace as S
import unittest
from unittest.mock import patch
from test_hybrid_planner import FIELD,ROOT

def load(name):
    p=ROOT/'experiments'/('elite-scout-'+name)/'team.py'
    s=importlib.util.spec_from_file_location('scout_'+name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    c=m.Guardiola2011();c._setup(FIELD);return c

def obs(ball=(0.,0.,0.,0.),own=None,tick=100):
    ps=[(0,-47.8,0.,0.,0.),(1,-15.,0.,0.,0.),(2,-4.,-10.,0.,0.),(3,0.,8.,0.,0.),(4,10.,17.,0.,0.)]
    es=[(5,47.,0.,0.,0.),(6,10.,-15.,0.,0.),(7,5.,10.,0.,0.),(8,15.,20.,0.,0.),(9,12.,-20.,0.,0.)]
    def pv(p):return S(id=p[0],position=p[1:3],velocity=p[3:],kick_cooldown_ticks=0)
    return S(field=FIELD,tick=tick,max_ticks=2400,score=(0,0),my_players=[pv(p) for p in ps],opponents=[pv(p) for p in es],
        can_kick=lambda pid:False,ball=S(position=ball[:2],velocity=ball[2:],controlling_team=own,
        controlling_player=None,last_touch=None))

def support(c,o):
    friends=[(p.id,*p.position,*p.velocity) for p in o.my_players]
    enemies=[(p.id,*p.position,*p.velocity) for p in o.opponents]
    c._shape_cover_id=1
    targets={0:(-47.8,0.),1:(-18.,0.),2:(-12.,-17.),3:(*o.ball.position,),4:(-8.,17.)}
    races={p[0]:(1.,p[1:3]) for p in friends}
    return friends,enemies,friends[3],races,2.,targets

class EliteScoutTests(unittest.TestCase):
    def test_off_has_identical_actions_and_plans_to_frozen_trap(self):
        a,b=load('baseline'),load('off')
        for tick in range(100,130):
            o=obs((12.+(tick-100)*.1,8.,5.,1.),tick=tick)
            aa,bb=a.act(o),b.act(o)
            self.assertEqual(aa.players,bb.players)
            self.assertEqual(aa.debug,bb.debug)
            self.assertEqual(a._receive_plan,b._receive_plan)

    def test_keeper_depth_shrinks_with_distance_and_never_passes_the_ball(self):
        c=load('keeper14')
        for bx in (-45.,-30.,0.,35.):
            x=c._scout_keeper_x(obs((bx,0.,0.,0.)),(0,-40.,0.,0.,0.))
            self.assertLess(x,bx)
            self.assertGreaterEqual(x,-47.8)
            self.assertLessEqual(x,-36.)
        self.assertLess(c._scout_keeper_x(obs((-30.,0.,0.,0.)),(0,-40.,0.,0.,0.)),-40.)

    def test_original_line_save_has_priority_when_advanced_route_is_unreachable(self):
        c=load('keeper14');o=obs((-30.,2.,-25.,0.))
        with patch.object(c,'_keeper_reaches',side_effect=(True,False)) as save:
            self.assertEqual(c._scout_keeper_x(o,(0,-47.,0.,0.,0.)),-47.8)
        self.assertEqual(save.call_count,2)
        self.assertEqual(c._scout_keeper_limit(o),c._mouth)

    def test_cooldown_is_used_when_comparing_real_keeper_save_paths(self):
        c=load('keeper10');o=obs((-30.,2.,-25.,0.));o.my_players[0].kick_cooldown_ticks=4
        with patch.object(c,'_keeper_reaches',return_value=True) as save:
            c._scout_keeper_x(o,(0,-40.,0.,0.,0.))
        self.assertTrue(all(call.args[-1]==4 for call in save.call_args_list))

    def test_cutback_provides_central_angle_and_preserves_cover_and_chaser(self):
        c=load('cutback');o=obs((35.,20.,0.,0.),own=0);f,e,ch,r,eta,t=support(c,o);old=t.copy()
        c._scout_support(o,f,e,ch,r,eta,t,False)
        changed=[k for k in t if t[k]!=old[k]]
        self.assertEqual(len(changed),1)
        self.assertNotIn(changed[0],(0,1,3))
        self.assertEqual(t[changed[0]],(29.,2.4))

    def test_goal_bound_horizon_uses_the_signed_position_and_positive_boundary(self):
        c=load('keeper14')
        self.assertFalse(c._scout_goal_bound(obs((0.,0.,-22.,0.))))
        self.assertTrue(c._scout_goal_bound(obs((-35.,0.,-22.,0.))))
        self.assertFalse(c._scout_goal_bound(obs((-35.,20.,-22.,0.))))

    def test_verified_receiver_cannot_be_reassigned(self):
        for name in ('cutback','outlet'):
            c=load(name);o=obs((35.,20.,0.,0.) if name=='cutback' else (-10.,4.,0.,0.),own=0 if name=='cutback' else None)
            f,e,ch,r,eta,t=support(c,o);old=t.copy();c._receive_plan=(2,3,200)
            c._scout_support(o,f,e,ch,r,eta,t,False)
            self.assertEqual(t,old)

    def test_outlet_stays_wide_and_ahead_without_changing_core_defenders(self):
        c=load('outlet');o=obs((-10.,5.,0.,0.));f,e,ch,r,eta,t=support(c,o);old=t.copy()
        c._scout_support(o,f,e,ch,r,eta,t,False)
        changed=[k for k in t if t[k]!=old[k]]
        self.assertEqual(len(changed),1)
        self.assertNotIn(changed[0],(0,1,3))
        self.assertEqual(t[changed[0]],(12.,-17.))
        self.assertEqual(c._scout_outlet[0],changed[0])

    def test_outlet_cancels_on_a_fast_goalward_ball(self):
        c=load('outlet');o=obs((-10.,5.,-22.,0.));f,e,ch,r,eta,t=support(c,o);old=t.copy()
        c._scout_support(o,f,e,ch,r,eta,t,False)
        self.assertEqual(t,old)
        self.assertIsNone(c._scout_outlet)

    def test_actions_obey_official_bounds_in_each_isolated_variant(self):
        for name in ('keeper6','keeper10','keeper14','outlet','cutback'):
            c=load(name)
            for x in (-30.,0.,30.):
                a=c.act(obs((x,17.,3.,-2.)))
                self.assertEqual(set(a.players),set(range(5)))
                for p in a.players.values():
                    self.assertTrue(all(math.isfinite(v) for v in p.movement))
                    self.assertLessEqual(math.hypot(*p.movement),1.00000001)
                    self.assertTrue(0<=p.kick_power<=1)

if __name__=='__main__':unittest.main()
