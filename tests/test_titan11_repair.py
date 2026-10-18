"""Execution regressions for the isolated TITAN-11 repair experiment."""
import ast
import importlib.util
import math
from pathlib import Path
import random
import sys
import types
import unittest
from unittest.mock import patch

from test_hybrid_planner import FIELD
from test_match_tactics import observation

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('repair_builder', ROOT/'tools/titan11r/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def controller(runtime=False, handoff=False):
    module = types.ModuleType('repair_test')
    exec(compile(builder.build(runtime, handoff), 'team.py', 'exec'), module.__dict__)
    c = module.Guardiola2011()
    c._setup(FIELD)
    return c


class RepairTests(unittest.TestCase):
    def test_deferred_heuristic_has_identical_answers_with_sparse_and_wall_paths(self):
        old, new = controller(), controller(runtime=True)
        rng = random.Random(111109)
        for _ in range(2500):
            p = (3, rng.uniform(-48,48), rng.uniform(-28,28),
                 rng.uniform(-8,8), rng.uniform(-8,8))
            path = old._trajectory(rng.uniform(-49,49),rng.uniform(-29,29),
                                   rng.uniform(-30,30),rng.uniform(-30,30))
            self.assertEqual(old._intercept(p,path),new._intercept(p,path))
        self.assertIsNone(new._intercept((3,0.,0.,0.,0.),[]))

    def test_early_feasible_sample_never_computes_unused_eta_fallback(self):
        old, new = controller(), controller(runtime=True)
        p = (3,0.,0.,0.,0.)
        path = [(0.,15.,0.),(1.,3.,0.)]
        with patch.object(old,'_eta',wraps=old._eta) as a, patch.object(new,'_eta',wraps=new._eta) as b:
            self.assertEqual(old._intercept(p,path),new._intercept(p,path))
            self.assertGreater(a.call_count,0)
            self.assertEqual(b.call_count,0)

    def test_verified_slow_pass_gets_the_receivers_executed_command(self):
        p, q = (2,-1.7,0.,0.,0.), (3,8.,0.,0.,0.)
        friends=[(0,-47.,0.,0.,0.),(1,-15.,8.,0.,0.),p,q,(4,20.,12.,0.,0.)]
        enemies=[(5,47.,25.,0.,0.)]
        for handoff in (False,True):
            c=controller(handoff=handoff)
            option=c._link_option(p,0.,0.,0.,0.,q,enemies,8.,0.,10.2)
            self.assertIsNotNone(option)
            def choose(*args):
                c._touch_movement=option[2];c._pass_plan=option[3];c._bank_plan=None
                return option[1]
            c._choose_kick=choose
            action=c.act(observation(ball=(0.,0.,0.,0.),friends=friends,enemies=enemies,
                                     kickers=(2,),holder=2,last=2))
            if handoff:
                self.assertEqual(c._receive_plan[0],3)
                self.assertEqual(action.players[3].movement,c._move(q,c._target(*c._receive_aim[1])))
            else:
                # Reproduce the frozen source's gap between pass approval
                # and act(): the named pass is kicked without a receiver plan.
                self.assertIsNone(c._receive_plan)

    def test_slowing_flight_keeps_only_an_executable_safe_reception(self):
        friends=[(0,-47.,0.,0.,0.),(1,-15.,8.,0.,0.),(2,-1.7,0.,0.,0.),
                 (3,8.,0.,0.,0.),(4,20.,12.,0.,0.)]
        for handoff in (False,True):
            c=controller(handoff=handoff);c._receive_plan=(3,2,150);c._receive_aim=(3,(5.,0.))
            c.act(observation(ball=(4.,0.,8.9,0.),friends=friends,
                              enemies=[(5,47.,25.,0.,0.)],last=2,tick=101))
            self.assertEqual(c._receive_plan is not None,handoff)
        c=controller(handoff=True);c._receive_plan=(3,2,150)
        c.act(observation(ball=(4.,0.,8.9,0.),friends=friends,
                          enemies=[(6,4.,0.,0.,0.)],last=2,tick=101))
        self.assertIsNone(c._receive_plan)

    def test_unrelated_physics_shooting_and_defence_methods_are_unchanged(self):
        def methods(source):
            cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef))
            return {n.name:ast.dump(n,include_attributes=False) for n in cls.body if isinstance(n,ast.FunctionDef)}
        original=methods((ROOT/'experiments/titan-11/team.py').read_text())
        repaired=methods(builder.build(True,True))
        changed={name for name in original if original[name]!=repaired[name]}
        self.assertEqual(changed,{'_intercept','act'})
        self.assertEqual(set(original),set(repaired))


if __name__ == '__main__':
    unittest.main()
