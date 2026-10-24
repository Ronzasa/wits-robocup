"""For each goal we concede, print the preceding ~2 s: ball path, last kicks, our keeper and nearest defenders."""
import importlib.util, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "harness"))
import common; from common import soccer
sp = importlib.util.spec_from_file_location("b", os.path.join(HERE, "..", "baseline", "team.py")); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
cls = [v for v in vars(m).values() if isinstance(v, type) and hasattr(v, "_wall_break")][0]
opp = sys.argv[1]; seeds = range(int(sys.argv[2]), int(sys.argv[3]))
class T(cls):
    def reset(self, seed):
        super().reset(seed); self.hist = collections.deque(maxlen=50); self.out = []
    def act(self, obs):
        keeper = min(obs.my_players, key=lambda p: p.id)
        self.hist.append((obs.tick, tuple(round(x, 1) for x in obs.ball.position), tuple(round(x, 1) for x in keeper.position),
                          sum(1 for q in obs.opponents if q.position[0] < obs.my_goal[0] + 20)))
        for e in obs.events:
            if getattr(e, "type", "") == "goal" or "goal" in str(e)[:40].lower():
                T.LOG.append((obs.tick, str(e)[:120], list(self.hist)[::10]))
        return super().act(obs)
T.LOG = []
for seed in seeds:
    for side in (0, 1):
        T.LOG.clear()
        a, b = (T(), common.spec(opp)) if side == 0 else (common.spec(opp), T())
        r = soccer.play_match(a, b, seed=seed, kickoff_team=side, max_ticks=2400)
        print("seed", seed, "side", side, "score", r.score, flush=True)
        for g in T.LOG: print("   ", g)
