import ast, math, unittest
from pathlib import Path
from types import SimpleNamespace as N
from soccer import SoccerEnv
from soccer.helpers import load_controller
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'experiments/three-player-push/team.py'
class Roles(unittest.TestCase):
 def setUp(self):
  self.c=load_controller(str(SOURCE));self.c.reset(71)
  with SoccerEnv(config_path=str(ROOT/'configs/default.toml')) as e:self.field=e.field
 def obs(self):
  def p(i,x,y):return N(id=i,position=(x,y),velocity=(0.,0.),kick_cooldown_ticks=0)
  return N(tick=100,score=(0,1),field=self.field,opponent_goal=self.field.opponent_goal,
    my_players=[p(0,-49,0),p(1,43,6),p(2,42,0),p(3,41,-5),p(4,44,5)],
    opponents=[p(i+5,49,y) for i,y in enumerate((-5.,-2.,1.,4.,6.))],
    ball=N(position=(44.,6.),velocity=(0.,0.),controlling_team=0),can_kick=lambda pid:False)
 def test_three_full_pushers_and_separate_keeper(self):
  o=self.obs();s=self.c._specialist;s._setup(self.field)
  a=s._siege_act(o,o.opponents)
  self.assertEqual(set(a.players),set(range(5)))
  self.assertGreaterEqual(sum(abs(math.hypot(*a.players[i].movement)-1)<1e-9 for i in range(1,5)),3)
  self.assertTrue(all(a.players[i].kick_direction is None for i in range(1,5)))
  self.assertFalse(s.SIEGE_PRESS is False)
  # Keeper retains the inherited independent goal safeguard.
  baseline=load_controller(str(ROOT/'my-team/team.py'));baseline.reset(71)
  baseline._specialist._setup(self.field)
  original=baseline._specialist._siege_act(o,o.opponents)
  self.assertEqual(a.players[0].movement,original.players[0].movement)
  self.assertEqual(a.players[0].kick_direction,original.players[0].kick_direction)
 def test_only_carrier_kicks_while_three_others_push(self):
  o=self.obs();o.can_kick=lambda pid:pid==1
  s=self.c._specialist;s._setup(self.field)
  a=s._siege_act(o,o.opponents)
  self.assertIsNotNone(a.players[1].kick_direction)
  for pid in (2,3,4):
   self.assertAlmostEqual(math.hypot(*a.players[pid].movement),1.)
   self.assertIsNone(a.players[pid].kick_direction)
 def test_broad_wall_requires_six_consecutive_ticks_and_reset(self):
  o=self.obs()
  for tick in range(100,105):o.tick=tick;self.c._observe_wall(o);self.assertFalse(self.c._wall_confirmed)
  o.tick=105;self.c._observe_wall(o);self.assertTrue(self.c._wall_confirmed)
  self.c.reset(71);self.assertFalse(self.c._wall_confirmed)
 def test_gap_resets_confirmation(self):
  o=self.obs();self.c._observe_wall(o);o.tick+=2;self.c._observe_wall(o)
  self.assertEqual(self.c._wall_ticks,1)
 def test_fallback_and_general_shooting_unchanged(self):
  a=ast.parse(SOURCE.read_text());b=ast.parse((ROOT/'my-team/team.py').read_text())
  def cls(t,n):return next(x for x in t.body if isinstance(x,ast.ClassDef) and x.name==n)
  self.assertEqual(ast.dump(cls(a,'_FallbackPolicy')),ast.dump(cls(b,'_FallbackPolicy')))
  sa,sb=cls(a,'_SpecialistPolicy'),cls(b,'_SpecialistPolicy')
  for n in ('_shot_option','_goal_path','_shot_contact_margin','_move','_opening_act'):
   f=lambda c:next(x for x in c.body if isinstance(x,ast.FunctionDef) and x.name==n)
   self.assertEqual(ast.dump(f(sa)),ast.dump(f(sb)))
if __name__=='__main__':unittest.main()
