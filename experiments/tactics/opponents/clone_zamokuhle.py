"""Behaviour clone of a tournament team, built ONLY from its published replay (positions + actions).
k-nearest-neighbour on the team-relative observation of each role. NOT the team's code. Data: replays/*.json.gz"""
import gzip, json, os
import numpy as np
from soccer import PlayerAction, TeamAction, TeamController

DATA = os.environ.get("CLONE_DATA", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "replays", "zamokuhle_maziya_vs_raquel_seed1000.json.gz"))
K = int(os.environ.get("CLONE_K", "5"))
SCALE = np.array([10, 10, 4, 4, 10, 10, 6, 6, 8, 8], dtype=float)

class Clone(TeamController):
    name = "clone"; version = "1"
    def __init__(self):
        with gzip.open(DATA, "rt") as g: d = json.load(g)
        self.F, self.M, self.Kk = {}, {}, {}
        for r, rows in d["rows"].items():
            A = np.array(rows, dtype=float)
            self.F[int(r)] = A[:, :10] / SCALE; self.M[int(r)] = A[:, 11:13]; self.Kk[int(r)] = A[:, 13:16]
        self.start = {r: tuple(np.array(d["rows"][str(r)])[0, :2]) for r in range(5)}
    def initial_formation(self, field):
        return [self.start[r] for r in range(5)]
    def act(self, obs):
        a = TeamAction(); bx, by = obs.ball.position; bvx, bvy = obs.ball.velocity
        for p in obs.my_players:
            r = p.id % 5
            if obs.opponents:
                q = min(obs.opponents, key=lambda o: (o.position[0] - p.position[0]) ** 2 + (o.position[1] - p.position[1]) ** 2)
                ox, oy = q.position[0] - p.position[0], q.position[1] - p.position[1]
            else:
                ox = oy = 0.0
            x = np.array([p.position[0], p.position[1], p.velocity[0], p.velocity[1], bx, by, bvx, bvy, ox, oy]) / SCALE
            dist = ((self.F[r] - x) ** 2).sum(1)
            idx = np.argpartition(dist, K)[:K]
            mv = self.M[r][idx].mean(0)
            kick = self.Kk[r][idx]
            if obs.can_kick(p.id) and (kick[:, 2] > 0).mean() >= 0.5:
                dx, dy = kick[:, 0].mean(), kick[:, 1].mean(); n = (dx * dx + dy * dy) ** 0.5 or 1.0
                a.set(p.id, PlayerAction(movement=(float(mv[0]), float(mv[1])), kick_direction=(dx / n, dy / n), kick_power=float(max(0.1, min(1.0, kick[:, 2].mean())))))
            else:
                a.set(p.id, PlayerAction(movement=(float(mv[0]), float(mv[1]))))
        return a
