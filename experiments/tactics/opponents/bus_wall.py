import math
from soccer import PlayerAction, TeamAction, TeamController


class Bus(TeamController):
    name = "bus"
    version = "1"
    YS = (-5.6, -2.8, 0.0, 2.8, 5.6)

    def initial_formation(self, field):
        x = field.my_goal[0] + field.player_radius + 0.2
        return [(x, y) for y in self.YS]

    def act(self, obs):
        actions = TeamAction()
        gx = obs.my_goal[0] + 1.2
        for i, p in enumerate(sorted(obs.my_players, key=lambda q: q.id)):
            tx, ty = gx, self.YS[i % 5]
            dx, dy = tx - p.position[0], ty - p.position[1]
            d = math.hypot(dx, dy)
            s = min(1.0, d / 1.5)
            mv = (dx / d * s, dy / d * s) if d > 1e-6 else (0.0, 0.0)
            kd = None
            if obs.can_kick(p.id):
                kd = (1.0, 0.0)
            actions.set(p.id, PlayerAction(movement=mv, kick_direction=kd, kick_power=1.0 if kd else 0.0))
        return actions
