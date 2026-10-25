"""Stand-in modelled on the replays of the top teams: three attackers chase the ball as a group; the one who can kick
either taps the ball forward at low power (dribble) or, once the ball is inside SHOT_X, drives a full-power shot at the
post-side corner (|y| 6.3, on the side the ball is on). Defender (id 1) holds x=-8; keeper holds the line."""
import math
from soccer import PlayerAction, TeamAction, TeamController
SHOT_X = 28.0

class TapDrive(TeamController):
    name = "tap_drive"; version = "1"
    def initial_formation(self, field):
        return [(-48.0, 0.0), (-8.0, 0.0), (-1.2, -6.0), (-1.2, 6.0), (-1.2, 0.0)]
    def act(self, obs):
        a = TeamAction(); bx, by = obs.ball.position
        mine = {p.id: p for p in obs.my_players}
        for pid, (tx, ty) in {0: (-48.0, 0.0), 1: (-8.0, by * 0.3)}.items():
            p = mine[pid]; dx, dy = tx - p.position[0], ty - p.position[1]; d = math.hypot(dx, dy)
            a.set(pid, PlayerAction(movement=(dx / d, dy / d) if d > 1.0 else (0.0, 0.0)))
        for pid in (2, 3, 4):
            p = mine[pid]
            if obs.can_kick(pid):
                if bx >= SHOT_X:
                    ty = 6.3 if by >= 0 else -6.3
                    dx, dy = 50.0 - bx, ty - by; n = math.hypot(dx, dy)
                    a.set(pid, PlayerAction(movement=(0.0, 0.0), kick_direction=(dx / n, dy / n), kick_power=1.0))
                else:
                    dx, dy = 50.0 - bx, -by * 0.25; n = math.hypot(dx, dy)
                    a.set(pid, PlayerAction(movement=(1.0, 0.0), kick_direction=(dx / n, dy / n), kick_power=0.15))
            else:
                # chase the ball, staggered: the nearest goes at it, the others hold ~6 units behind/beside
                dist = math.hypot(bx - p.position[0], by - p.position[1])
                near = min((q for q in (2, 3, 4)), key=lambda i: math.hypot(bx - mine[i].position[0], by - mine[i].position[1]))
                if pid == near:
                    tx, ty = bx, by
                else:
                    tx, ty = bx - 6.0, by + (-6.0 if pid == 2 else 6.0 if pid == 3 else 0.0)
                dx, dy = tx - p.position[0], ty - p.position[1]; d = math.hypot(dx, dy)
                a.set(pid, PlayerAction(movement=(dx / d, dy / d) if d > 0.5 else (0.0, 0.0)))
        return a
