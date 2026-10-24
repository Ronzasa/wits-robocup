"""Run the kickoff-bait mechanism probe. Writes results/bait_probe.json.

For every opponent and delay, we kick off (kickoff_team=0) on fixed seeds; the match is cut at
200 ticks (10 s) because the mechanism only concerns the first restart.
"""
import importlib.util, json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "harness"))
import common
from common import soccer

spec_ = importlib.util.spec_from_file_location("bait_probe", os.path.join(os.path.dirname(os.path.abspath(__file__)), "bait_probe.py"))
bp = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(bp)

CONFIGS = [("fast", True, 0), ("d0", False, 0), ("d45", False, 45), ("d55", False, 55)]
SEEDS = list(range(100, 140))
opponents = common.BUILTINS + list(common.OPPONENTS)
out = {"engine_sha256": common.engine_hash(), "configs": [c[0] for c in CONFIGS], "seeds": [SEEDS[0], SEEDS[-1]], "rows": []}
t0 = time.time()
for opp in opponents:
    for label, fast, d in CONFIGS:
        bp.DELAY = d
        bp.FAST = fast
        n = fouls = hit = 0
        first_foul, moves, unmoved = [], [], 0
        for seed in SEEDS:
            ctl = bp.BaitProbe()
            o = soccer.play_match(ctl, common.spec(opp), seed=seed, kickoff_team=0, max_ticks=200)
            n += 1
            f = o.result["stats"][1]["fouls"]
            fouls += f
            hit += 1 if f else 0
            ours = [t for t, team, pl in bp.LOG if team == 1]
            if ours: first_foul.append(min(ours))
            if bp.MOVE: moves.append(bp.MOVE[0])
            else: unmoved += 1
        row = {"opponent": opp, "config": label, "delay": d, "matches": n, "opp_fouls": fouls, "matches_with_foul": hit,
               "mean_first_foul_tick": (sum(first_foul) / len(first_foul)) if first_foul else None,
               "mean_ball_first_moves_tick": (sum(moves) / len(moves)) if moves else None,
               "never_moved_in_200_ticks": unmoved}
        out["rows"].append(row)
        print(f"{opp:18s} {label:5s} fouls {fouls:3d} in {hit:2d}/{n} matches  first foul tick {row['mean_first_foul_tick']}  ball moved at {row['mean_ball_first_moves_tick']}  unmoved {unmoved}", flush=True)
os.makedirs(common.RESULTS, exist_ok=True)
json.dump(out, open(os.path.join(common.RESULTS, "bait_probe.json"), "w"), indent=1)
print("done in %.0fs" % (time.time() - t0))
