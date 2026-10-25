"""Stand-in modelled on the replays: one striker dribbles with taps, then drives a full-power shot at the far corner
(y = -/+ 6.2, away from the keeper) once the ball is inside SHOT_X of the goal. Others hold decoy spots."""
import math
from soccer import PlayerAction, TeamAction, TeamController
SHOT_X = 18.0     # shoot when ball x >= this (attack-relative; goal at x=50)
MODE = 'far'      # 'far' = corner away from the keeper, 'near' = post on the ball's side (as in the replays)

class CornerShooter(TeamController):
    name = "corner_shooter"; version = "1"
    SHOTS = 0
    def initial_formation(self, field):
        return [(-48.0, 0.0), (-8.0, -12.0), (-8.0, 12.0), (8.0, -14.0), (-1.2, 0.0)]
    def act(self, obs):
        a = TeamAction(); bx, by = obs.ball.position
        mine = {p.id: p for p in obs.my_players}
        decoys = {1: (-8.0, -12.0), 2: (-8.0, 12.0), 3: (12.0, -14.0), 0: (-48.0, 0.0)}
        for pid, (tx, ty) in decoys.items():
            p = mine[pid]; dx, dy = tx - p.position[0], ty - p.position[1]; d = math.hypot(dx, dy)
            a.set(pid, PlayerAction(movement=(dx / d, dy / d) if d > 1.0 else (0.0, 0.0)))
        s = mine[4]; keeper = min(obs.opponents, key=lambda q: q.position[0] if False else -q.position[0])
        gy = (-6.2 if keeper.position[1] >= 0 else 6.2) if MODE == 'far' else (6.3 if by >= 0 else -6.3)
        if obs.can_kick(4):
            if bx >= SHOT_X:
                dx, dy = 50.0 - bx, gy - by; n = math.hypot(dx, dy)
                a.set(4, PlayerAction(movement=(0.0, 0.0), kick_direction=(dx / n, dy / n), kick_power=1.0)); CornerShooter.SHOTS += 1
            else:
                dx, dy = 50.0 - bx, -by * 0.3; n = math.hypot(dx, dy)
                a.set(4, PlayerAction(movement=(1.0, 0.0), kick_direction=(dx / n, dy / n), kick_power=0.3))
        else:
            dx, dy = bx - s.position[0], by - s.position[1]; d = math.hypot(dx, dy) or 1.0
            a.set(4, PlayerAction(movement=(dx / d, dy / d)))
        return a
