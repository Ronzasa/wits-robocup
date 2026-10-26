import math
from soccer import PlayerAction, TeamAction, TeamController

class Wall(TeamController):
    name = "wall"
    version = "1"
    X = (2.9, 1.0, 1.0, 1.0, 1.0)        # x offset from own goal line, per player id 0..4
    YS = (-5.8, -6.7, 1.15, 5.2, -2.9)      # y per player id 0..4
    RAMP = 1.5
    def initial_formation(self, field):
        return [(field.my_goal[0] + self.X[i], self.YS[i]) for i in range(5)]
    def act(self, obs):
        actions = TeamAction()
        for p in sorted(obs.my_players, key=lambda q: q.id):
            i = p.id % 5
            tx, ty = obs.my_goal[0] + self.X[i], self.YS[i]
            dx, dy = tx - p.position[0], ty - p.position[1]
            d = math.hypot(dx, dy)
            s = min(1.0, d / self.RAMP)
            mv = (dx / d * s, dy / d * s) if d > 1e-6 else (0.0, 0.0)
            kd = (1.0, 0.0) if obs.can_kick(p.id) else None
            actions.set(p.id, PlayerAction(movement=mv, kick_direction=kd, kick_power=1.0 if kd else 0.0))
        return actions
