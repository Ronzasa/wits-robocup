"""Regressions for public defender kicks before the ball's next movement."""
import math
import json
from pathlib import Path
import unittest
from test_hybrid_planner import controller


class ShotContactTests(unittest.TestCase):
    def test_three_reproduced_false_safe_shots_are_identified(self):
        data=json.loads((Path(__file__).parent/'fixtures/shot-contact-states.json').read_text())
        for case in data['cases']:
            with self.subTest(tick=case['tick']):
                c=controller()
                c._enemy_cooldowns={int(k):v for k,v in case['enemy_cooldowns'].items()}
                self.assertGreater(case['old_margin'],0.)
                self.assertLess(c._shot_contact_margin(*case['ball'][:2],case['launch'],
                                case['opponents'],case['goal_time']),-.02)

    def test_threatened_shot_can_be_replaced_with_a_reachable_pass(self):
        data=json.loads((Path(__file__).parent/'fixtures/shot-contact-states.json').read_text())
        case=next(v for v in data['cases'] if v['tick']==297)
        c=controller()
        c._enemy_cooldowns={int(k):v for k,v in case['enemy_cooldowns'].items()}
        kick=c._choose_kick(case['player'],*case['ball'],case['friends'],case['opponents'])
        self.assertIsNotNone(kick)
        self.assertIsNotNone(c._pass_plan)
        self.assertEqual(c._pass_plan[0],1)
        launch=c._carrier_contact(case['player'],*case['ball'][:2],
                                 *c._requested_velocity(*case['ball'][2:],kick),c._touch_movement)
        self.assertGreater(c._shot_contact_margin(*case['ball'][:2],launch,case['opponents'],.15),0.)

    def test_defensive_clearances_preserve_the_frozen_v7_actions(self):
        friends=[(0,-48.,0.,0.,0.),(1,-33.7,22.,0.,0.),(2,-25.,-6.,0.,0.),
                 (3,-18.,10.,0.,0.),(4,-8.,0.,0.,0.)]
        opponents=[(5,47.,0.,0.,0.),(6,-30.,22.2,0.,0.),(7,-20.,0.,0.,0.),
                   (8,0.,-10.,0.,0.),(9,5.,10.,0.,0.)]
        for player,ball,expected in [
                (friends[0],(-46.3,0.,-20.,0.),((.960110640096723,.27962038332900735),1.)),
                (friends[1],(-32.,22.,-4.,0.),((.7606690445506744,-.6491398960642953),1.))]:
            c=controller()
            kick=c._choose_kick(player,*ball,friends,opponents)
            self.assertIsNotNone(kick)
            self.assertAlmostEqual(kick[0][0],expected[0][0])
            self.assertAlmostEqual(kick[0][1],expected[0][1])
            self.assertAlmostEqual(kick[1],expected[1])

    def test_ready_defender_can_kick_before_ball_advances_past_it(self):
        c=controller()
        p=(3,18.3,0.,0.,0.)
        enemy=(6,22.,2.,0.,0.)
        move=c._move(p,(20.3,0.))
        launch=c._carrier_contact(p,20.,0.,22.,0.,move)
        # The ball has not physically hit this body in its first tick.
        self.assertGreater(math.dist(launch[:2],enemy[1:3]),c._contact)
        self.assertLess(c._shot_contact_margin(20.,0.,launch,[enemy],.15),-.02)
        self.assertIsNone(c._shot_option(p,20.,0.,0.,0.,[enemy],0.))

    def test_cooldown_prevents_kick_but_preserves_body_obstruction(self):
        c=controller()
        p=(3,18.3,0.,0.,0.)
        c._enemy_cooldowns={6:20}
        self.assertIsNotNone(c._shot_option(p,20.,0.,0.,0.,[(6,22.,2.,0.,0.)],0.))
        self.assertIsNone(c._shot_option(p,20.,0.,0.,0.,[(6,21.1,0.,0.,0.)],0.))

    def test_first_tick_already_contested_is_not_labelled_clear(self):
        c=controller()
        launch=(21.1,0.,21.67,0.)
        q=(6,19.2,1.,0.,0.)
        self.assertLess(c._shot_contact_margin(20.,0.,launch,[q],.15),-.02)
        c._enemy_cooldowns={6:20}
        self.assertGreater(c._shot_contact_margin(20.,0.,launch,[q],.15),0.)

    def test_moving_defender_contact_is_mirrored_on_both_wings(self):
        c=controller()
        margin=[]
        for sign in (-1.,1.):
            launch=(35.547486,sign*4.378979,22.415309,sign*3.134527)
            q=(7,36.203613,sign*2.098585,.634711,sign*3.479356)
            margin.append(c._shot_contact_margin(34.409653,sign*4.219866,launch,[q],.15))
        self.assertTrue(all(x<-.02 for x in margin))
        self.assertAlmostEqual(*margin)

    def test_unobstructed_shot_retains_legal_full_power(self):
        c=controller()
        p=(3,28.3,0.,0.,0.)
        shot=c._shot_option(p,30.,0.,0.,0.,[(5,47.,25.,0.,0.)],0.)
        self.assertIsNotNone(shot)
        self.assertGreater(shot[1][1],0.)
        self.assertLessEqual(shot[1][1],1.)
        launch=c._carrier_contact(p,30.,0.,*c._requested_velocity(0.,0.,shot[1]),shot[2])
        self.assertGreater(c._shot_contact_margin(30.,0.,launch,[(5,47.,25.,0.,0.)],.25),0.)

    def test_shot_that_scores_first_is_not_rejected_for_later_contact(self):
        c=controller()
        # Goal crossing is in the first tick. A later kick cannot undo it.
        launch=(50.1,0.,20.,0.)
        c._enemy_cooldowns={6:2}
        q=(6,49.,1.8,0.,0.)
        self.assertGreater(c._shot_contact_margin(49.1,0.,launch,[q],.04),0.)

    def test_defender_can_kick_just_before_next_step_would_score(self):
        c=controller()
        # The next free ball step crosses the line, but the defender is
        # already able to kick the pre-step ball. Scoring is not assured.
        launch=(48.5,0.,21.67,0.)
        q=(6,49.,2.,0.,0.)
        self.assertLess(c._shot_contact_margin(47.4,0.,launch,[q],.1),-.02)


if __name__=='__main__':
    unittest.main()
