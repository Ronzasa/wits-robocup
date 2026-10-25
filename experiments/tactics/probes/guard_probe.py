"""Post-guard mechanism test. Our outfield is frozen where it starts EXCEPT that the lab's post guard may move defenders.
The corner_shooter stand-in dribbles with taps and drives a full-power shot at the corner on the ball's side
(mode 'near', like the replays) once ball x >= SHOT_X. Reports shots on target and goals conceded per variant."""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "harness"))
import common; from common import soccer
from soccer import PlayerAction, TeamAction
def load(path, name):
    sp = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
cs = load(os.path.join(HERE, "..", "opponents", "corner_shooter.py"), "cs")
def build(path, n, gx):
    m = load(path, "t%d" % abs(hash((path, n, gx))))
    cls = [v for v in vars(m).values() if isinstance(v, type) and hasattr(v, "_wall_break")][0]
    class K(cls):
        GUARD_N = n; GUARD_X = gx
        def act(self, obs):
            base = super().act(obs)
            a = TeamAction()
            for p in obs.my_players:
                a.set(p.id, base.players[p.id] if p.id == 0 else PlayerAction(movement=(0.0, 0.0)))
            if self.GUARD_N:
                self._post_guard(obs, a)
            return a
    return K()
def run(path, n, gx, shot_x, seeds):
    cs.SHOT_X = shot_x; cs.MODE = "near"; sh = g = k = 0
    for seed in seeds:
        for side in (0, 1):
            t = build(path, n, gx); o = cs.CornerShooter()
            a, b = (t, o) if side == 0 else (o, t)
            r = soccer.play_match(a, b, seed=seed, kickoff_team=side, max_ticks=1200)
            th = 1 if side == 0 else 0; sh += r.result["stats"][th]["shots"]; g += r.score[th]; k += 1
    return sh, g, k
if __name__ == "__main__":
    lab = os.path.join(HERE, "..", "lab", "team.py")
    for sx in (28.0, 20.0):
        for n, gx in ((0, -25.0), (2, -25.0), (3, -25.0), (2, -15.0), (3, -10.0)):
            sh, g, k = run(lab, n, gx, sx, range(30060, 30070))
            print(f"SHOT_X={sx} GUARD_N={n} GUARD_X={gx}: matches {k} shots {sh} goals {g} ({g/max(1,sh):.2f} per shot)", flush=True)
