"""Bunker-Striker v2. Same evidence-based idea as v1 (goal-line wall, tap-then-drive corner shot, lock the lead) with the
weaknesses v1 showed fixed:
  * several attackers (NUM_ATT) instead of one: the nearest ones win the ball with moving-ball interception,
  * the wall only forms when it is needed (opponent holds the ball in our half, we lead, or we are 2+ behind),
  * a fast fallback: when the opponent controls the ball inside FALL_X, attackers drop to the wall immediately,
  * support players hold midfield cover outside the centre circle; wall players clear loose balls to the far flank.
Only math and the official SDK; O(players) per decision."""
import math
from soccer import PlayerAction, TeamAction, TeamController


def _unit(x, y):
    n = math.hypot(x, y)
    return (x / n, y / n) if n > 1e-9 else (0.0, 0.0)


class BunkerStriker(TeamController):
    name = "bunker_striker"
    version = "2"
    WALL_YS = (0.0, -2.9, 2.9, -5.9, 5.9)
    WALL_X = 1.8
    SHOT_X = 28.0
    TAP = 0.15
    NUM_ATT = 2
    FALL_X = -12.0
    CLEAR_X = -22.0

    def initial_formation(self, field):
        x = field.my_goal[0] + self.WALL_X
        return [(x, 0.0), (x, -2.9), (x, 2.9), (-11.0, -6.0), (-11.0, 6.0)]

    def _go(self, p, tx, ty, slow=1.5):
        dx, dy = tx - p.position[0], ty - p.position[1]
        d = math.hypot(dx, dy)
        if d < 1e-6:
            return (0.0, 0.0)
        s = 1.0 if d > slow else d / slow
        return (dx / d * s, dy / d * s)

    def act(self, obs):
        a = TeamAction()
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        lead = obs.score[0] - obs.score[1]
        mine = sorted(obs.my_players, key=lambda p: p.id)
        gx = obs.my_goal[0] + self.WALL_X
        goal = obs.opponent_goal[0]
        opp_ball = obs.ball.controlling_team == 1
        full_wall = lead >= 1 or lead <= -2
        danger = opp_ball and bx < self.FALL_X
        wall_mode = full_wall or danger
        keeper, out = mine[0], mine[1:]
        # wall slots: keeper is the centre; the four outfield players take the rest
        slots = {p.id: self.WALL_YS[1 + i] for i, p in enumerate(out)}
        if wall_mode:
            for p in mine:
                ty = 0.0 if p.id == keeper.id else slots[p.id]
                mv = self._go(p, gx, ty)
                if obs.can_kick(p.id):
                    side = 18.0 if by <= 0 else -18.0
                    dx, dy = _unit(goal - p.position[0], side - p.position[1])
                    a.set(p.id, PlayerAction(movement=mv, kick_direction=(dx, dy), kick_power=1.0))
                else:
                    a.set(p.id, PlayerAction(movement=mv))
            return a
        # open play: keeper on the line, nearest NUM_ATT outfielders attack, the rest hold cover
        a.set(keeper.id, PlayerAction(movement=self._go(keeper, gx, max(-2.5, min(2.5, by * 0.15)))))
        if obs.can_kick(keeper.id):
            dx, dy = _unit(goal - keeper.position[0], (18.0 if by <= 0 else -18.0) - keeper.position[1])
            a.set(keeper.id, PlayerAction(movement=(0.0, 0.0), kick_direction=(dx, dy), kick_power=1.0))
        ranked = sorted(out, key=lambda p: math.hypot(p.position[0] - bx, p.position[1] - by))
        att, rest = ranked[:self.NUM_ATT], ranked[self.NUM_ATT:]
        for i, p in enumerate(att):
            if i == 0:
                if obs.can_kick(p.id):
                    if bx >= self.SHOT_X:
                        ty = 6.3 if by >= 0 else -6.3
                        dx, dy = _unit(goal - bx, ty - by)
                        a.set(p.id, PlayerAction(movement=(0.0, 0.0), kick_direction=(dx, dy), kick_power=1.0))
                    elif bx < self.CLEAR_X:
                        dx, dy = _unit(goal - bx, (18.0 if by <= 0 else -18.0) - by)
                        a.set(p.id, PlayerAction(movement=(0.0, 0.0), kick_direction=(dx, dy), kick_power=1.0))
                    else:
                        dx, dy = _unit(goal - bx, -by * 0.25)
                        a.set(p.id, PlayerAction(movement=(1.0, 0.0), kick_direction=(dx, dy), kick_power=self.TAP))
                else:
                    d = math.hypot(bx - p.position[0], by - p.position[1])
                    t = min(d / 8.0, 1.2)
                    a.set(p.id, PlayerAction(movement=self._go(p, bx + vx * t, by + vy * t, 0.5)))
            else:                                       # supporting attacker: wide and slightly ahead of the ball
                tx = min(bx + 6.0, goal - 8.0)
                ty = -8.0 if by >= 0 else 8.0
                a.set(p.id, PlayerAction(movement=self._go(p, tx, ty, 1.0)))
        for i, p in enumerate(rest):                   # cover just outside the centre circle on our side
            a.set(p.id, PlayerAction(movement=self._go(p, -11.0, -6.0 if i % 2 == 0 else 6.0, 1.0)))
        return a
