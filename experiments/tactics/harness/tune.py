"""Coordinate-descent tuner for the lab controller. Development seeds only (never 40000+).
Each trial = lab/team.py with some class constants overridden, played paired against cached baseline results
on (opponent, seed, side) units. Objective (guidance only): d(points) + 0.25 * d(goal difference).
Usage: tune.py OUT_DIR SEED0 SEED1   (params and pool defined below)"""
import json, multiprocessing as mp, os, re, statistics, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common; from common import soccer
LAB = os.path.join(common.TACTICS, "lab", "team.py"); BASE = os.path.join(common.TACTICS, "baseline", "team.py")
POOL = os.environ.get("TUNE_POOL", "champion_original,press_formation,lock_no_breaker,possession,balanced").split(",")
SPACE = {  # name: candidate values (first = current default in lab/team.py)
    "CONTAIN_ON": [0, 1], "CONTAIN_DIST": [3.5, 2.5, 5.0], "CONTAIN_X": [25.0, 10.0, 40.0], "CONTAIN_MARK": [0, 1],
    "HPRESS_N": [0, 1, 2], "HPRESS_X": [5.0, 0.0, 20.0],
    "TRANSITION_SECONDS": [1.5, 1.0, 2.5], "TRANSITION_GAIN": [4.0, 2.5, 6.0], "SHOOT_RANGE": [34.0, 28.0, 40.0],
}
def make(path, params):
    s = open(LAB).read()
    for k, v in params.items():
        s, n = re.subn(rf"^(    {k} = ).*$", rf"\g<1>{v!r}", s, count=1, flags=re.M)
        assert n == 1, k
    open(path, "w").write(s)
def unit(a):
    team, opp, seed, side = a
    t, o = (team, common.spec(opp)) if side == 0 else (common.spec(opp), team)
    m = soccer.play_match(t, o, seed=seed, kickoff_team=side, max_ticks=2400)
    me, th = (0, 1) if side == 0 else (1, 0); st = m.result["stats"]
    return dict(gf=m.score[me], ga=m.score[th], err=st[me]["policy_errors"], to=st[me]["policy_timeouts"], fouls=st[me]["fouls"])
def evaluate(pool, path, units):
    return pool.map(unit, [(path, o, s, d) for o, s, d in units])
def pts(r): return 3 if r["gf"] > r["ga"] else 1 if r["gf"] == r["ga"] else 0
def score(base, cand):
    dp = statistics.mean(pts(c) - pts(b) for b, c in zip(base, cand))
    dg = statistics.mean((c["gf"] - c["ga"]) - (b["gf"] - b["ga"]) for b, c in zip(base, cand))
    return dp, dg, dp + 0.25 * dg
if __name__ == "__main__":
    out, s0, s1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); os.makedirs(out, exist_ok=True)
    units = [(o, s, d) for o in POOL for s in range(s0, s1) for d in (0, 1)]
    pool = mp.Pool(2)
    cache = os.path.join(out, "baseline.json")
    if os.path.exists(cache): base = json.load(open(cache))
    else:
        base = evaluate(pool, BASE, units); json.dump(base, open(cache, "w"))
    cur = {k: v[0] for k, v in SPACE.items()}; best = 0.0; log = []
    for rnd in range(2):
        improved = False
        for k, vals in SPACE.items():
            for v in vals:
                if v == cur[k]: continue
                trial = dict(cur); trial[k] = v
                if k in ("CONTAIN_DIST", "CONTAIN_X", "CONTAIN_MARK") and not trial["CONTAIN_ON"]: continue
                if k in ("HPRESS_X",) and not trial["HPRESS_N"]: continue
                p = os.path.join(out, "trial.py"); make(p, trial)
                t0 = time.time(); r = evaluate(pool, p, units); dp, dg, sc = score(base, r)
                bad = sum(x["err"] for x in r) + sum(x["fouls"] for x in r)
                rec = dict(round=rnd, change={k: v}, params=trial, dPts=dp, dGD=dg, score=sc, errors_fouls=bad, to=sum(x["to"] for x in r), secs=round(time.time() - t0))
                log.append(rec); print(json.dumps(rec), flush=True)
                if sc > best + 0.05 and bad == 0: best, cur, improved = sc, trial, True
        if not improved: break
    json.dump(dict(final=cur, best=best, log=log), open(os.path.join(out, "tune_result.json"), "w"), indent=1)
    make(os.path.join(out, "tuned_team.py"), cur); print("FINAL", cur, best)
