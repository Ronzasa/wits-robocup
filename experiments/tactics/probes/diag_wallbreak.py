"""Diagnose the baseline's built-in wall breaker vs bus_wall: how often does it activate, shoot, convert?"""
import importlib.util, json, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "harness"))
import common; from common import soccer
def load(path, name):
    sp = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
mod = load(os.path.join(HERE, "..", "baseline", "team.py"), "base")
cls = [v for v in vars(mod).values() if isinstance(v, type) and hasattr(v, "_wall_break")][0]
C = dict(ticks_wall=0, ticks_gap_ok=0, shots=0, ticks_ballfront=0, gap_and_can_kick=0)
class Diag(cls):
    def _wall_break(self, obs, actions):
        gx = obs.opponent_goal[0]
        wall = [q for q in obs.opponents if abs(q.position[0]-gx) <= 3.0 and abs(q.position[1]) <= 9.0]
        bx, by = obs.ball.position
        if len(wall) >= 4 and bx >= 0: C["ticks_wall"] += 1
        if len(wall) >= 4 and bx >= 0:
            r = obs.field.player_radius; hw = obs.field.goal_width*0.5
            ys = sorted(q.position[1] for q in wall); lo = -hw; best = 0.0
            for y in ys + [hw + r]:
                best = max(best, min(y-r, hw)-lo); lo = max(lo, y+r)
            if best >= 1.15:
                C["ticks_gap_ok"] += 1
                if any(obs.can_kick(p.id) for p in obs.my_players): C["gap_and_can_kick"] += 1
            if bx > gx - 12: C["ticks_ballfront"] += 1
        before = {p.id: actions.players[p.id].kick_direction for p in obs.my_players}
        super()._wall_break(obs, actions)
        for p in obs.my_players:
            if actions.players[p.id].kick_direction != before[p.id] and obs.can_kick(p.id): C["shots"] += 1
rows = []
for seed in range(30000, 30010):
    for side in (0, 1):
        for k in C: C[k] = 0
        a, b = (Diag(), common.spec("bus_wall")) if side == 0 else (common.spec("bus_wall"), Diag())
        m = soccer.play_match(a, b, seed=seed, kickoff_team=side, max_ticks=2400)
        f = m.score[side]
        rows.append(dict(seed=seed, side=side, gf=f, **C)); print(rows[-1], flush=True)
