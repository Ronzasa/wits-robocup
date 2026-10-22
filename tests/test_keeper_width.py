"""Spacing, clock boundaries and protected reception invariants."""
import importlib.util
import math
import os
from pathlib import Path
from types import SimpleNamespace as S
import unittest

from test_hybrid_planner import FIELD, ROOT
from test_match_tactics import observation


def controller():
    path=Path(os.environ.get('ROBOCUP_WIDTH_TEAM_PATH',ROOT/'experiments/keeper-width-attack/team.py'))
    spec=importlib.util.spec_from_file_location('keeper_width',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    c=module.Guardiola2011();c._setup(FIELD)
    return c


FRIENDS=[(0,-47.8,0.,0.,0.),(1,-3.,0.,0.,0.),(2,-1.,0.,0.,0.),
         (3,8.,-4.,0.,0.),(4,13.,4.,0.,0.)]
ENEMIES=[(5,47.,0.,0.,0.),(6,-15.,20.,0.,0.),(7,0.,-25.,0.,0.),
         (8,25.,-20.,0.,0.),(9,25.,20.,0.,0.)]
BASE_TARGETS={0:(-47.8,0.),1:(-3.,0.),2:(0.,0.),3:(8.,-8.),4:(13.,4.5)}


def scenario(c,tick=100,holder=2,last=2,ball=(0.,0.,0.,0.),protected=False):
    obs=observation(ball=ball,friends=FRIENDS,enemies=ENEMIES,tick=tick,
                    last=last,holder=holder,kickers=(2,) if holder==2 else ())
    obs.max_ticks=2400
    c._observe_attacking_phase(obs)
    c._shape_cover_id=1
    targets=dict(BASE_TARGETS)
    c._space_support(obs,FRIENDS,ENEMIES,FRIENDS[2],{2:(.1,(0.,0.))},1.,targets,protected)
    return obs,targets


class KeeperWidthTests(unittest.TestCase):
    def test_backpass_is_included_and_untested_wall_counter_stays_off(self):
        c=controller()
        self.assertTrue(c.KEEPER_BACKPASS)
        self.assertFalse(c.KEEPER_WALL_COUNTER)

    def test_exact_standard_clock_boundaries(self):
        c=controller()
        for tick,phase in [(0,0),(1199,0),(1200,1),(1799,1),(1800,2),(2399,2)]:
            scenario(c,tick)
            self.assertEqual(c._spacing_phase,phase)

    def test_clock_uses_actual_length_and_simulation_rate(self):
        c=controller()
        for tick,phase in [(1799,0),(1800,1),(2999,1),(3000,2)]:
            obs=S(tick=tick,max_ticks=3600,field=FIELD,score=(0,0))
            c._observe_attacking_phase(obs)
            self.assertEqual(c._spacing_phase,phase)
        field=S(simulation_hz=10)
        c._observe_attacking_phase(S(tick=900,max_ticks=1200,field=field,score=(0,0)))
        self.assertEqual(c._spacing_phase,2)

    def test_short_matches_still_keep_the_first_half_normal(self):
        c=controller()
        for tick,phase in [(0,0),(199,0),(200,2),(399,2)]:
            c._observe_attacking_phase(S(tick=tick,max_ticks=400,field=FIELD,score=(0,0)))
            self.assertEqual(c._spacing_phase,phase)

    def test_schedule_applies_when_leading_as_requested(self):
        c=controller()
        c._observe_attacking_phase(S(tick=1800,max_ticks=2400,field=FIELD,score=(5,0)))
        self.assertEqual(c._spacing_phase,2)

    def test_support_is_wider_and_distant_from_carrier(self):
        c=controller();_,targets=scenario(c)
        self.assertGreater(abs(targets[3][1]-targets[4][1]),20.)
        for pid in (3,4):
            self.assertGreaterEqual(math.hypot(*targets[pid]),7.5)
        self.assertEqual(targets[0],BASE_TARGETS[0])
        if getattr(c,'POSSESSION_TRIANGLE',False):
            self.assertLess(targets[1][0],-5.)
            self.assertGreaterEqual(math.hypot(*targets[1]),7.5)
        else:
            self.assertEqual(targets[1],BASE_TARGETS[1])
        self.assertEqual(targets[2],BASE_TARGETS[2])

    def test_targets_retain_space_from_each_other(self):
        c=controller();_,targets=scenario(c)
        for pid in (3,4):
            for other,point in targets.items():
                if other!=pid:self.assertGreaterEqual(math.dist(targets[pid],point),6.)

    def test_ultra_support_advances_beyond_normal_support(self):
        c=controller();_,normal=scenario(c,100)
        _,moderate=scenario(c,1200)
        _,ultra=scenario(c,1800)
        self.assertGreaterEqual(sum(moderate[p][0] for p in (3,4)),sum(normal[p][0] for p in (3,4)))
        self.assertGreater(sum(ultra[p][0] for p in (3,4)),sum(normal[p][0] for p in (3,4)))

    def test_existing_receiver_plan_is_never_retargeted(self):
        c=controller();c._receive_plan=(3,2,200)
        _,targets=scenario(c)
        self.assertEqual(targets[3],BASE_TARGETS[3])

    def test_restart_protection_keeps_all_existing_targets(self):
        c=controller();_,targets=scenario(c,1800,protected=True)
        self.assertEqual(targets,BASE_TARGETS)

    def test_first_half_defending_preserves_markers(self):
        c=controller();_,targets=scenario(c,100,holder=6,last=6)
        self.assertEqual(targets,BASE_TARGETS)

    def test_urgent_shot_keeps_existing_defence(self):
        c=controller();_,targets=scenario(c,1800,holder=6,last=6,ball=(-35.,0.,-20.,0.))
        self.assertEqual(targets,BASE_TARGETS)

    def test_late_counter_outlet_preserves_other_marker(self):
        c=controller();_,targets=scenario(c,1800,holder=6,last=6,ball=(8.,0.,0.,0.))
        changed=[p for p in targets if targets[p]!=BASE_TARGETS[p]]
        self.assertEqual(changed,[4])

    def test_brief_counterpress_is_not_overridden(self):
        c=controller();c._press_until=1820
        _,targets=scenario(c,1800)
        self.assertEqual(targets,BASE_TARGETS)

    def test_targets_stay_inside_the_pitch(self):
        c=controller();_,targets=scenario(c,1800,ball=(44.,26.,0.,0.))
        for x,y in targets.values():
            self.assertLessEqual(abs(x),48.)
            self.assertLessEqual(abs(y),28.)

    def test_width_holds_a_safe_target_briefly(self):
        c=controller();_,a=scenario(c,100);_,b=scenario(c,101)
        self.assertEqual(a,b)

    def test_phase_change_discards_old_support_hold(self):
        c=controller();scenario(c,1199)
        self.assertTrue(c._spacing_targets)
        c._observe_attacking_phase(S(tick=1200,max_ticks=2400,field=FIELD,score=(0,0)))
        self.assertEqual(c._spacing_targets,{})

    def test_reset_removes_all_old_spacing_state(self):
        c=controller();scenario(c,1800);c.reset(7)
        self.assertEqual(c._spacing_targets,{})
        self.assertEqual(c._spacing_phase,0)
        self.assertEqual(c._spacing_tick,-1)

    def test_phase_only_does_not_change_first_half_support(self):
        c=controller();c.WIDE_SUPPORT=False
        _,targets=scenario(c,1199)
        self.assertEqual(targets,BASE_TARGETS)

    def test_stale_team_possession_does_not_spread_during_opponent_touch(self):
        c=controller()
        if not getattr(c,'POSSESSION_TRIANGLE',False):self.skipTest('R2 possession refinement')
        obs=observation(ball=(0.,0.,0.,0.),friends=FRIENDS,enemies=ENEMIES,
                        tick=100,last=6,holder=None,kickers=())
        obs.ball.controlling_team=0;obs.max_ticks=2400
        c._observe_attacking_phase(obs);c._shape_cover_id=1
        targets=dict(BASE_TARGETS)
        c._space_support(obs,FRIENDS,ENEMIES,FRIENDS[2],{2:(1.0,(0.,0.))},.1,targets,False)
        self.assertEqual(targets,BASE_TARGETS)

    def test_possession_triangle_never_changes_a_live_pass_plan(self):
        c=controller();c._receive_plan=(3,2,200)
        _,targets=scenario(c)
        self.assertEqual(targets[1],BASE_TARGETS[1])


if __name__=='__main__':unittest.main()
