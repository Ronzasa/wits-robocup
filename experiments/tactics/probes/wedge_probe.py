"""Mechanism probe 2: goal-wall wedging with legal collisions.

N pusher players run straight into chosen defenders of a sealed wall (opponents/bus_wall.py).
The probe never touches the ball. Each tick we log the widest *clear gap* in the wall: the widest
interval between consecutive defender bodies (radius = player_radius) and the posts, measured
along the goal mouth. A shot lane needs a gap >= ball diameter (0.9) + margin (0.25) = 1.15.
Env: WEDGE_N (pushers, 0 = control), WEDGE_TARGET ('mid' or 'flank').
"""
import math, os
from soccer import PlayerAction, TeamAction, TeamController

N = int(os.environ.get("WEDGE_N", "3"))
TARGET = os.environ.get("WEDGE_TARGET", "mid")
LOG = []   # (tick, widest_gap, gap_centre_y, wall_count, mean_defender_x)

def widest_gap(opps, gx, hw, r):
    wall = sorted(q.position[1] for q in opps if abs(q.position[0] - gx) <= 3.0 and abs(q.position[1]) <= hw + 2.0)
    lo, best = -hw, (0.0, 0.0)
    for y in wall + [hw + r]:
        hi = min(y - r, hw)
        if hi - lo > best[0]:
            best = (hi - lo, 0.5 * (hi + lo))
        lo = max(lo, y + r)
    return best[0], best[1], len(wall)

class WedgeProbe(TeamController):
    name = "wedge_probe"
    version = "1"

    def reset(self, seed):
        LOG.clear()

    def initial_formation(self, field):
        r = field.centre_circle_radius + 1.0
        return [(field.my_goal[0] + 3.0, 0.0), (-r, -6.0), (-r, 0.0), (-r, 6.0), (-r - 3.0, 12.0)]

    def act(self, obs):
        gx = obs.opponent_goal[0]
        hw = obs.field.goal_width * 0.5
        r = obs.field.player_radius
        gap, cy, n = widest_gap(obs.opponents, gx, hw, r)
        wall = [q for q in obs.opponents if abs(q.position[0] - gx) <= 3.0]
        mx = sum(q.position[0] for q in wall) / len(wall) if wall else 0.0
        LOG.append((obs.tick, gap, cy, n, mx))
        a = TeamAction()
        mine = sorted(obs.my_players, key=lambda p: p.id)
        outfield = mine[1:]
        defenders = sorted(wall, key=lambda q: q.position[1])
        if TARGET == "mid":
            order = sorted(defenders, key=lambda q: abs(q.position[1]))
        else:
            order = sorted(defenders, key=lambda q: -abs(q.position[1]))
        pushers = sorted(outfield, key=lambda p: p.position[1])[:N]
        targets = sorted(order[:N], key=lambda q: q.position[1])
        for p in mine:
            a.set(p.id, PlayerAction(movement=(0.0, 0.0)))
        for p, q in zip(pushers, targets):
            dx, dy = q.position[0] - p.position[0], q.position[1] - p.position[1]
            d = math.hypot(dx, dy) or 1.0
            a.set(p.id, PlayerAction(movement=(dx / d, dy / d)))
        return a
