"""Complete experimental tactics tested using public observations."""
import importlib.util
import math
from types import SimpleNamespace as S
import unittest

from test_hybrid_planner import FIELD, ROOT

spec = importlib.util.spec_from_file_location('experimental_tactics', ROOT / 'experiments/v8-full/team.py')
tactics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tactics)


def controller():
    c = tactics.Guardiola2011()
    c._setup(FIELD)
    c._enemy_cooldowns = {}
    return c


FRIENDS = [(0, -47.8, 0., 0., 0.), (1, -20., 0., 0., 0.),
           (2, -8., 12., 0., 0.), (3, -2., -8., 0., 0.), (4, 8., 0., 0., 0.)]
ENEMIES = [(5, 47., 0., 0., 0.), (6, -12., 0., 0., 0.),
           (7, 0., 20., 0., 0.), (8, 20., -10., 0., 0.), (9, 25., 10., 0., 0.)]


def observation(ball=(0., 5., 0., 0.), friends=FRIENDS, enemies=ENEMIES,
                score=(0, 0), tick=100, last=6, holder=None, kickers=()):
    def player(p):
        return S(id=p[0], position=p[1:3], velocity=p[3:5], kick_cooldown_ticks=0)
    return S(tick=tick, score=score, field=FIELD,
             my_players=[player(p) for p in friends], opponents=[player(p) for p in enemies],
             can_kick=lambda pid: pid in kickers,
             ball=S(position=ball[:2], velocity=ball[2:], last_touch=last,
                    controlling_player=holder, controlling_team=None if holder is None else int(holder >= 5)))


class MatchTacticsTests(unittest.TestCase):
    def test_shield_enters_at_two_goals_and_exits_immediately_below_two(self):
        c = controller()
        for tick, score, active in ((100, (1, 0), False), (101, (2, 0), True),
                                    (102, (3, 1), True), (103, (3, 2), False)):
            action = c.act(observation(score=score, tick=tick))
            self.assertEqual(c._shield_active, active)
            self.assertEqual(len(c._guard_ids), 5 if active else 0)
            self.assertEqual(set(action.players), set(range(5)))

    def test_five_guard_slots_cover_goal_and_respect_pitch(self):
        c = controller()
        targets = {}
        c._shield_positions(FRIENDS, targets)
        positions = sorted(targets.values(), key=lambda p: p[1])
        for x, y in positions:
            self.assertGreaterEqual(x, FIELD.my_goal[0] + FIELD.player_radius)
            self.assertLess(x, FIELD.my_goal[0] + 5.)
            self.assertLessEqual(abs(y), FIELD.goal_width / 2.)
        # The ball and player radii close the spaces between a flat wall's bodies.
        if c.SHIELD_SHAPE == 'flat':
            for a, b in zip(positions, positions[1:]):
                self.assertLess(math.dist(a, b), 2.*(FIELD.player_radius + FIELD.ball_radius))

    def test_keeper_tracks_a_wide_shot_until_other_guards_are_in_position(self):
        c = controller()
        c.act(observation(ball=(-35., 5., -20., 0.), score=(2, 0)))
        self.assertEqual(len(c._guard_ids), 5)
        self.assertGreater(c._tactical_targets[0][1], 4.)
        slots = {}
        c._shield_positions(FRIENDS, slots)
        settled = [(pid, *slots[pid], 0., 0.) for pid in range(5)]
        c.act(observation(ball=(-35., 5., -20., 0.), friends=settled, score=(2, 0), tick=101))
        self.assertAlmostEqual(c._tactical_targets[0][1], 0.)

    def test_guard_does_not_chase_when_next_tick_kick_range_is_too_small(self):
        c = controller()
        slots = {}
        c._shield_positions(FRIENDS, slots)
        x = slots[0][0]
        friends = [(pid, *slots[pid], 0., 0.) for pid in range(5)]
        # In current range, but not within the conservative range required to kick.
        o = observation(ball=(x+2.19, 0., 0., 0.), friends=friends,
                        score=(2, 0), kickers=(0,))
        a = c.act(o).players[0]
        self.assertAlmostEqual(a.movement[0], 0.)
        self.assertAlmostEqual(a.movement[1], 0.)
        self.assertIsNone(a.kick_direction)

    def test_unrelated_own_ball_and_loose_ball_do_not_arm_rebound(self):
        c = controller()
        c._tactics_observe(observation(ball=(-35., 0., -12., 0.), last=1), FRIENDS, ENEMIES)
        self.assertLess(c._incoming_until, 100)
        self.assertLess(c._rebound_until, 100)
        c._shape_cover_id = 1
        races = {p[0]: (.1, (-35., 0.)) for p in FRIENDS[1:]}
        o = observation(ball=(-35., 0., 8., 0.), last=1, score=(2, 0))
        self.assertEqual(c._rebound_break(o, FRIENDS, ENEMIES, races, 3., False), ())

    def test_saved_enemy_shot_arms_rebound_and_new_enemy_touch_clears_it(self):
        c = controller()
        c._tactics_observe(observation(ball=(-35., 0., -16., 0.), last=6, score=(2, 0)), FRIENDS, ENEMIES)
        c._tactics_observe(observation(ball=(-42., 0., 10., 0.), last=0, score=(2, 0), tick=101), FRIENDS, ENEMIES)
        self.assertGreater(c._rebound_until, 101)
        c._tactics_observe(observation(ball=(-40., 0., 8., 0.), last=7, score=(2, 0), tick=102), FRIENDS, ENEMIES)
        self.assertLess(c._rebound_until, 102)

    def test_safe_rebound_releases_two_and_retains_three_guards(self):
        c = controller()
        c._shield_active = True
        c._rebound_until = 130
        c._shape_cover_id = 1
        friends = [(0, -48., 0., 0., 0.), (1, -42., -5., 0., 0.),
                   (2, -39., 2., 0., 0.), (3, -43., 5., 0., 0.), (4, -44., -2., 0., 0.)]
        enemies = [(5, 47., 20., 0., 0.), (6, 10., 20., 0., 0.)]
        races = {p[0]: (.1 if p[0] == 2 else 1., (-39., 2.)) for p in friends[1:]}
        o = observation(ball=(-39., 2., 8., 0.), friends=friends, enemies=enemies,
                        last=0, score=(2, 0))
        targets = {}
        c._tactics_targets(o, friends, enemies, friends[2], races, 3., targets, False)
        self.assertEqual(len(c._break_ids), 2)
        self.assertEqual(len(c._guard_ids), 3)
        self.assertTrue(set(c._break_ids).isdisjoint(c._guard_ids))

    def test_opponent_control_or_lost_race_cancels_counter_without_restart(self):
        for holder, enemy_eta in ((6, 3.), (None, .01)):
            c = controller()
            c._rebound_until = 130
            c._break_until = 140
            c._break_ids = (2, 4)
            races = {p[0]: (.5, (-10., 0.)) for p in FRIENDS[1:]}
            o = observation(ball=(-10., 0., 8., 0.), last=0, holder=holder)
            self.assertEqual(c._rebound_break(o, FRIENDS, ENEMIES, races, enemy_eta, False), ())
            self.assertEqual(c._break_ids, ())

    def test_goals_and_reset_clear_transient_plans(self):
        c = controller()
        c._tactics_observe(observation(score=(2, 0)), FRIENDS, ENEMIES)
        c._break_ids = (2, 4)
        c._break_until = c._rebound_until = 200
        c._tiki_outlet = (2, 3, 4, 10., 0., 200)
        c._tactics_observe(observation(score=(2, 1), tick=101), FRIENDS, ENEMIES)
        self.assertEqual(c._break_ids, ())
        self.assertIsNone(c._tiki_outlet)
        self.assertLess(c._rebound_until, 101)
        c.reset(999)
        self.assertIsNone(c._striker_id)
        self.assertFalse(c._shield_active)

    def test_striker_mark_is_goal_side_and_never_steals_keeper_or_chaser(self):
        c = controller()
        c._shape_cover_id = 1
        races = {p[0]: (.5, (0., 5.)) for p in FRIENDS[1:]}
        targets = {p[0]: p[1:3] for p in FRIENDS}
        c._shadow_striker(observation(), FRIENDS, ENEMIES, FRIENDS[2], races, .2, targets)
        striker = next(q for q in ENEMIES if q[0] == c._striker_id)
        self.assertEqual(c._striker_id, 6)
        self.assertNotIn(c._striker_marker, (0, 2))
        self.assertLess(targets[c._striker_marker][0], striker[1])
        self.assertEqual(targets[0], FRIENDS[0][1:3])
        self.assertEqual(targets[2], FRIENDS[2][1:3])

    def test_open_long_shot_uses_legal_power_and_blocked_shot_is_rejected(self):
        c = controller()
        p = (2, 18.3, 0., 0., 0.)
        open_shot = c._special_finish(p, 20., 0., 8., 0., [(5, 40., 25., 0., 0.)])
        self.assertIsNotNone(open_shot)
        self.assertGreater(open_shot[1][1], 0.)
        self.assertLessEqual(open_shot[1][1], 1.)
        self.assertIsNone(c._special_finish(p, 20., 0., 8., 0., [(6, 21., 0., 0., 0.)]))
        self.assertEqual(c._speed, FIELD.max_speed)
        self.assertEqual(c._impulse, FIELD.kick_impulse)

    def test_third_man_runs_require_an_open_forward_lane(self):
        c = controller()
        c._shape_cover_id = c._striker_marker = 1
        p = (2, -1.7, 0., 0., 0.)
        friends = [FRIENDS[0], FRIENDS[1], p, (3, 8., 0., 0., 0.), (4, 16., 8., 0., 0.)]
        option = c._link_option(p, 0., 0., 0., 0., friends[3], [(5, 47., 25., 0., 0.)], 8., 0., 12.)
        self.assertIsNotNone(option)
        third = c._third_man(p, option, friends, [(5, 47., 25., 0., 0.)])
        self.assertIsNotNone(third)
        self.assertEqual(third[1], 4)
        self.assertIsNone(c._third_man(p, option, friends, [(6, 13., 4., 0., 0.)]))

    def test_short_link_selects_named_receiver_and_third_man(self):
        c = controller()
        c._shape_cover_id = c._striker_marker = 1
        passer = (2, -1.7, 0., 0., 0.)
        friends = [(0, -47., 0., 0., 0.), (1, -20., -5., 0., 0.), passer,
                   (3, 5.8, -2.1, 0., 0.), (4, 11., -6.4, 0., 0.)]
        enemies = [(5, 47., 0., 0., 0.), (6, 16.5, -8.9, 0., 0.)]
        option = c._search_links(passer, 0., 0., 0., 0., friends, enemies)
        self.assertIsNotNone(option)
        self.assertEqual(option[3][0], 3)
        self.assertIsNotNone(c._tiki_next)
        self.assertEqual(c._tiki_next[:2], (3, 4))
        self.assertGreater(c._tiki_next[2], option[3][1])
        c._tactic_tick = 100
        kick = c._choose_kick(passer, 0., 0., 0., 0., friends, enemies)
        self.assertIsNotNone(kick)
        self.assertEqual(c._pass_plan[0], 3)
        self.assertEqual(c._tiki_outlet[:3], (2, 3, 4))
        self.assertGreater(c._tiki_outlet[-1], 100)

    def test_rebound_counter_rejects_blocked_forward_lane(self):
        c = controller()
        c._rebound_until = 130
        c._shape_cover_id = 1
        friends = [(0, -48., 0., 0., 0.), (1, -42., -5., 0., 0.),
                   (2, -39., 2., 0., 0.), (3, -43., 5., 0., 0.), (4, -44., -2., 0., 0.)]
        enemies = [(5, 47., 20., 0., 0.), (6, -34., 1.7, 0., 0.)]
        races = {p[0]: (.1, (-39., 2.)) for p in friends[1:]}
        o = observation(ball=(-39., 2., 8., 0.), friends=friends, enemies=enemies,
                        last=0, score=(2, 0))
        self.assertEqual(c._rebound_break(o, friends, enemies, races, 3., False), ())

    def test_wall_collection_and_outlet_are_mirrored(self):
        plans = []
        for sign in (-1., 1.):
            c = controller()
            c._shape_cover_id = c._striker_marker = 1
            friends = [FRIENDS[0], FRIENDS[1], (2, 0., 25.*sign, 0., 0.),
                       (3, 2., 15.*sign, 0., 0.), (4, 8., 10.*sign, 0., 0.)]
            enemies = [(5, 47., 0., 0., 0.), (6, 30., -20.*sign, 0., 0.)]
            races = {p[0]: (.5, (0., 25.*sign)) for p in friends[1:]}
            targets = {}
            o = observation(ball=(0., 27.*sign, 0., 20.*sign), friends=friends, enemies=enemies)
            c._wall_collection(o, friends, enemies, friends[2], races, 3., targets)
            self.assertIsNotNone(c._bounce_plan)
            self.assertNotEqual(c._bounce_plan[0], c._bounce_plan[1])
            self.assertNotIn(c._bounce_plan[1], (1, c._bounce_plan[0]))
            plans.append(c._bounce_plan)
        self.assertEqual(plans[0][:2], plans[1][:2])
        self.assertAlmostEqual(plans[0][2][0], plans[1][2][0])
        self.assertAlmostEqual(plans[0][2][1], -plans[1][2][1])

    def test_goal_mouth_is_not_treated_as_an_end_wall(self):
        c = controller()
        c._shape_cover_id = c._striker_marker = 1
        races = {p[0]: (2., (-48., 0.)) for p in FRIENDS[1:]}
        targets = {p[0]: p[1:3] for p in FRIENDS}
        before = dict(targets)
        c._wall_collection(observation(ball=(-45., 0., -20., 0.)), FRIENDS,
                           ENEMIES, FRIENDS[2], races, 3., targets)
        self.assertIsNone(c._bounce_plan)
        self.assertEqual(targets, before)


if __name__ == '__main__':
    unittest.main()
