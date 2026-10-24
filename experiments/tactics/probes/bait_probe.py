"""Mechanism probe 1: kickoff foul bait.

When this team owns a restart (ball dead at the centre, ours), it holds its first kick for
BAIT_DELAY ticks (read from the environment at import time so worker processes see it),
then kicks the ball forward at half power. Everything else is deliberately dull so that any
opponent foul is attributable to the delay alone.
"""
import math, os
from soccer import PlayerAction, TeamAction, TeamController

DELAY = int(os.environ.get("BAIT_DELAY", "0"))
FAST = os.environ.get("BAIT_FAST", "0") == "1"   # control: rush the ball and kick at the first legal tick
LOG = []   # (tick, team, player) for foul events seen this match
MOVE = []  # tick at which the ball first left the centre spot

class BaitProbe(TeamController):
    name = "bait_probe"
    version = "1"

    def reset(self, seed):
        self._held = 0
        LOG.clear()
        MOVE.clear()

    def initial_formation(self, field):
        r = field.centre_circle_radius + 1.0
        return [(field.my_goal[0] + 3.0, 0.0), (-r, 0.0), (-r - 8.0, -8.0), (-r - 8.0, 8.0), (-r - 14.0, 0.0)]

    def act(self, obs):
        for e in obs.events:
            if e.get("kind") == "foul":
                LOG.append((obs.tick, e["team"], e["player"]))
        a = TeamAction()
        bx, by = obs.ball.position
        if not MOVE and obs.tick > 0 and (abs(bx) > 0.05 or abs(by) > 0.05):
            MOVE.append(obs.tick)
        dead = abs(bx) < 0.05 and abs(by) < 0.05 and abs(obs.ball.velocity[0]) + abs(obs.ball.velocity[1]) < 0.01
        ours = dead and obs.ball.controlling_team == 0
        held = getattr(self, "_held", 0)
        self._held = held + 1 if ours else 0
        mine = sorted(obs.my_players, key=lambda p: p.id)
        kicker = min(mine[1:], key=lambda p: math.hypot(p.position[0] - bx, p.position[1] - by))
        for p in mine:
            if p.id == kicker.id and ours:
                dx, dy = bx - p.position[0], by - p.position[1]
                d = math.hypot(dx, dy) or 1.0
                # stop short of body contact (player 1.0 + ball 0.45): running into the ball starts the restart
                # a player coasts ~0.45 * speed after a zero command (damping 0.9/tick at 20 Hz):
                # stop commanding once the coasting point would be inside 1.95 (kick range is 2.2, body contact 1.45)
                vt = (p.velocity[0] * dx + p.velocity[1] * dy) / d
                mv = (dx / d, dy / d) if (FAST or d - 0.45 * max(vt, 0.0) > 1.95) else (0.0, 0.0)
                if self._held > DELAY and obs.can_kick(p.id):
                    a.set(p.id, PlayerAction(movement=mv, kick_direction=(1.0, 0.0), kick_power=0.5))
                else:
                    a.set(p.id, PlayerAction(movement=mv))
            elif p.id == kicker.id:
                dx, dy = bx - p.position[0], by - p.position[1]
                d = math.hypot(dx, dy) or 1.0
                a.set(p.id, PlayerAction(movement=(dx / d, dy / d), kick_direction=(1.0, 0.0) if obs.can_kick(p.id) else None,
                                         kick_power=0.5 if obs.can_kick(p.id) else 0.0))
            else:
                a.set(p.id, PlayerAction(movement=(0.0, 0.0)))
        return a
