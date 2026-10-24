"""Probe 3b: relentless end-wall bombardment. Nearest outfielder chases the ball and kicks it at the
end-wall point (+x edge, y=TY) at POWER whenever it can kick. Rebounds repeatedly pass defenders."""
import math, os
from soccer import PlayerAction, TeamAction, TeamController
TY = float(os.environ.get("OG_TY", "0")); POWER = float(os.environ.get("OG_POWER", "1.0"))
class WallBomb(TeamController):
    name = "wall_bomb"; version = "1"
    def initial_formation(self, field):
        r = field.centre_circle_radius + 1.0
        return [(field.my_goal[0] + 3.0, 0.0), (-r, -6.0), (-r, 6.0), (-r - 3.0, -12.0), (-r - 3.0, 12.0)]
    def act(self, obs):
        a = TeamAction(); bx, by = obs.ball.position
        mine = sorted(obs.my_players, key=lambda p: p.id)
        for p in mine: a.set(p.id, PlayerAction(movement=(0.0, 0.0)))
        k = min(mine[1:], key=lambda p: math.hypot(p.position[0]-bx, p.position[1]-by))
        wx = obs.field.width / 2.0
        if obs.can_kick(k.id):
            dx, dy = wx - k.position[0], TY - k.position[1]; d = math.hypot(dx, dy) or 1.0
            a.set(k.id, PlayerAction(movement=(0.0, 0.0), kick_direction=(dx/d, dy/d), kick_power=POWER))
        else:
            dx, dy = bx - k.position[0], by - k.position[1]; d = math.hypot(dx, dy) or 1.0
            a.set(k.id, PlayerAction(movement=(dx/d, dy/d)))
        return a
