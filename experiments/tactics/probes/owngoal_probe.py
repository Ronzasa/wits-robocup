"""Mechanism probe 3: end-wall rebound into a defender -> own goal.

We kick off and send one full-power kick from the centre spot at angle ANGLE (deg, toward the
opponent end wall) with power POWER. After the kick our team does nothing. Opponent: bus_wall
(defenders pinned in front of goal, constantly trying to kick => their kick cooldown cycles).
Logs every goal event seen in obs.events (scorer, own_goal) and the ticks of defender kicks.
"""
import math, os
from soccer import PlayerAction, TeamAction, TeamController

ANGLE = float(os.environ.get("OG_ANGLE", "0"))
POWER = float(os.environ.get("OG_POWER", "1.0"))
GOALS = []

class OwnGoalProbe(TeamController):
    name = "owngoal_probe"
    version = "1"
    def reset(self, seed):
        GOALS.clear(); self.fired = False

    def initial_formation(self, field):
        r = field.centre_circle_radius + 1.0
        return [(field.my_goal[0] + 3.0, 0.0), (-r, -6.0), (-r, 6.0), (-r - 3.0, -12.0), (-r - 3.0, 12.0)]

    def act(self, obs):
        for e in obs.events:
            if getattr(e, "type", None) == "goal" or (isinstance(e, dict) and e.get("type") == "goal"):
                GOALS.append((obs.tick, e))
        a = TeamAction()
        mine = sorted(obs.my_players, key=lambda p: p.id)
        for p in mine:
            a.set(p.id, PlayerAction(movement=(0.0, 0.0)))
        if not self.fired:
            k = min(mine[1:], key=lambda p: math.hypot(*obs.ball.position and (p.position[0]-obs.ball.position[0], p.position[1]-obs.ball.position[1])))
            bx, by = obs.ball.position
            dx, dy = bx - k.position[0], by - k.position[1]
            d = math.hypot(dx, dy) or 1.0
            if obs.can_kick(k.id):
                t = math.radians(ANGLE)
                a.set(k.id, PlayerAction(movement=(0.0, 0.0), kick_direction=(math.cos(t), math.sin(t)), kick_power=POWER))
                self.fired = True
            else:
                a.set(k.id, PlayerAction(movement=(dx / d, dy / d)))
        return a
