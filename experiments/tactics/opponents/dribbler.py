import math
from soccer import PlayerAction, TeamAction, TeamController


class Dribbler(TeamController):
    name = "dribbler"
    version = "1"
    TAP = 0.34          # kick power used to push the ball ahead
    SHOOT = 30.0        # shoot when this close to the goal
    PRESS_ROW = 10.0    # kickoff line just outside the circle

    def initial_formation(self, field):
        gx = field.my_goal[0] + 3.0
        r = field.centre_circle_radius + 1.0
        return [(gx, 0.0), (-r, -4.5), (-r, 4.5), (-r - 7.0, -9.0), (-r - 7.0, 9.0)]

    def act(self, obs):
        a = TeamAction()
        bx, by = obs.ball.position
        bvx, bvy = obs.ball.velocity
        gx, gy = obs.opponent_goal
        mine = sorted(obs.my_players, key=lambda p: p.id)
        out = mine[1:]
        dist = lambda p: math.hypot(p.position[0] - bx, p.position[1] - by)
        chaser = min(out, key=dist)
        # keeper: track the ball's y on the line
        k = mine[0]
        ky = max(-5.5, min(5.5, by * 0.35))
        kx = obs.my_goal[0] + 2.2
        dx, dy = kx - k.position[0], ky - k.position[1]
        d = math.hypot(dx, dy) or 1.0
        s = min(1.0, d / 1.5)
        mv = (dx / d * s, dy / d * s)
        kd = None
        if obs.can_kick(k.id) and math.hypot(bx - k.position[0], by - k.position[1]) < 2.0:
            kd = (1.0, 0.0)
        a.set(k.id, PlayerAction(movement=mv, kick_direction=kd, kick_power=1.0 if kd else 0.0))
        for p in out:
            if p.id == chaser.id:
                px, py = p.position
                if obs.can_kick(p.id):
                    dg = math.hypot(gx - px, gy - py)
                    if dg < self.SHOOT:
                        keeper = min(obs.opponents, key=lambda q: abs(q.position[0] - gx))
                        ty = 5.2 if keeper.position[1] < 0 else -5.2
                        kx_, ky_ = gx - px, ty - py
                        n = math.hypot(kx_, ky_) or 1.0
                        a.set(p.id, PlayerAction(movement=(kx_ / n, ky_ / n), kick_direction=(kx_ / n, ky_ / n), kick_power=1.0))
                    else:
                        kx_, ky_ = gx - px, gy - py
                        n = math.hypot(kx_, ky_) or 1.0
                        a.set(p.id, PlayerAction(movement=(kx_ / n, ky_ / n), kick_direction=(kx_ / n, ky_ / n), kick_power=self.TAP))
                else:
                    lead = 3
                    tx, ty = bx + bvx * lead * 0.05, by + bvy * lead * 0.05
                    dx, dy = tx - px, ty - py
                    n = math.hypot(dx, dy) or 1.0
                    a.set(p.id, PlayerAction(movement=(dx / n, dy / n)))
            else:
                # support: hold an attacking shape ahead of the ball, spread wide
                idx = [q.id for q in out].index(p.id)
                tx = max(-15.0, min(30.0, bx + 8.0))
                ty = (-14.0, -5.0, 5.0, 14.0)[idx]
                dx, dy = tx - p.position[0], ty - p.position[1]
                n = math.hypot(dx, dy) or 1.0
                s = min(1.0, n / 2.0)
                a.set(p.id, PlayerAction(movement=(dx / n * s, dy / n * s)))
        return a
