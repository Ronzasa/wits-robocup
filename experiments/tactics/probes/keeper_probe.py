"""Keeper-only save test: our outfield is frozen (no movement, no kicks); the corner_shooter stand-in dribbles and drives
full-power shots at the far corner from ball x >= SHOT_X (attack-relative; goal at 50). Reports shots on target and goals conceded."""
import importlib.util, os, sys, statistics as S
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "harness"))
import common; from common import soccer
from soccer import PlayerAction, TeamAction
def load(path, name):
    sp = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
cs = load(os.path.join(HERE, "..", "opponents", "corner_shooter.py"), "cs")
def keeper_only(team_path):
    m = load(team_path, "t" + str(abs(hash(team_path))))
    cls = [v for v in vars(m).values() if isinstance(v, type) and hasattr(v, "_wall_break")][0]
    class K(cls):
        def act(self, obs):
            a = super().act(obs)
            for p in obs.my_players:
                if p.id != 0: a.set(p.id, PlayerAction(movement=(0.0, 0.0)))
            return a
    return K()
def run(team_path, shot_x, seeds, mode='far'):
    cs.SHOT_X = shot_x; cs.MODE = mode; R = []
    for seed in seeds:
        for side in (0, 1):
            t = keeper_only(team_path); o = cs.CornerShooter()
            a, b = (t, o) if side == 0 else (o, t)
            r = soccer.play_match(a, b, seed=seed, kickoff_team=side, max_ticks=1200)
            me, th = (0, 1) if side == 0 else (1, 0); st = r.result["stats"]
            R.append((st[th]["shots"], r.score[th]))
    return sum(x[0] for x in R), sum(x[1] for x in R), len(R)
if __name__ == "__main__":
    team = sys.argv[1]
    for mode in ('far', 'near'):
        for sx in (30.0, 20.0):
            sh, g, n = run(team, sx, range(30000, 30010), mode)
            print(f"{os.path.basename(team)} mode={mode} SHOT_X={sx}: matches {n} shots {sh} goals conceded {g} ({g/max(1,sh):.2f} per shot)", flush=True)
