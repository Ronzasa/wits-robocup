"""Bunker-Striker: a small controller built from the tournament evidence (standings, replays).
Idea: the table's bunker teams score about one goal and concede ~0.15. So:
  * defend as a goal-line wall (five bodies across the mouth, ~2.9 apart; the keeper in the middle),
  * keep ONE striker as the counter-attacker: tap-dribble the ball forward at low power, then drive one full-power
    shot into the post-side corner (|y| ~ 6.3) from ~18-24 units, as every goal in the replays did,
  * after we lead, everyone is in the wall (lock the lead); when two or more goals behind, same wall (limit the damage),
  * when the ball is dead in our half a wall player clears it at full power toward the far flank.
Only math and the official SDK are used; decisions are O(players)."""
import math
from soccer import PlayerAction, TeamAction, TeamController


def _unit(x, y):
    n = math.hypot(x, y)
    return (x / n, y / n) if n > 1e-9 else (0.0, 0.0)


class BunkerStriker(TeamController):
    name = "bunker_striker"
    version = "1"
    WALL_YS = (0.0, -2.9, 2.9, -5.9, 5.9)      # keeper takes 0.0; outfield fill the rest
    WALL_X = 1.8                                 # distance from our goal line
    SHOT_X = 28.0                                # ball x (attack-relative) where the striker drives
    TAP = 0.15
    STRIKER = 4

    def initial_formation(self, field):
        x = field.my_goal[0] + self.WALL_X
        return [(x, 0.0), (x, -2.9), (x, 2.9), (x, -5.9), (-11.0, 0.0)]

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
        lead = obs.score[0] - obs.score[1]
        mine = {p.id: p for p in obs.my_players}
        gx = obs.my_goal[0] + self.WALL_X
        full_wall = lead >= 1 or lead <= -2
        for pid, p in mine.items():
            if pid == self.STRIKER and not full_wall:
                continue
            idx = pid if pid != self.STRIKER else 4
            ty = self.WALL_YS[idx % 5]
            mv = self._go(p, gx, ty)
            if obs.can_kick(pid):
                side = 18.0 if by <= 0 else -18.0
                dx, dy = _unit(obs.opponent_goal[0] - p.position[0], side - p.position[1])
                a.set(pid, PlayerAction(movement=mv, kick_direction=(dx, dy), kick_power=1.0))
            else:
                a.set(pid, PlayerAction(movement=mv))
        if not full_wall:
            s = mine[self.STRIKER]
            danger = bx < -25.0 and obs.ball.controlling_team == 1
            if danger:                                   # fast fallback: join the wall
                mv = self._go(s, gx, 5.9)
                a.set(self.STRIKER, PlayerAction(movement=mv))
            elif obs.can_kick(self.STRIKER):
                if bx >= self.SHOT_X:
                    ty = 6.3 if by >= 0 else -6.3
                    dx, dy = _unit(obs.opponent_goal[0] - bx, ty - by)
                    a.set(self.STRIKER, PlayerAction(movement=(0.0, 0.0), kick_direction=(dx, dy), kick_power=1.0))
                else:
                    dx, dy = _unit(obs.opponent_goal[0] - bx, -by * 0.25)
                    a.set(self.STRIKER, PlayerAction(movement=(1.0, 0.0), kick_direction=(dx, dy), kick_power=self.TAP))
            else:
                vx, vy = obs.ball.velocity
                chase = bx > -10.0 or vx > 2.0 or obs.ball.controlling_team != 1
                if chase and not (bx < -25.0):
                    tx, ty = bx + vx * 0.4, by + vy * 0.4        # lead a moving ball a little
                else:
                    tx, ty = -11.0, by * 0.5                     # wait outside the centre circle
                a.set(self.STRIKER, PlayerAction(movement=self._go(s, tx, ty, 0.5)))
        return a
