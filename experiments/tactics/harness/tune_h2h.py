"""Head-to-head coordinate descent: a challenger (the champion candidate with some constants overridden) plays the
champion candidate itself, treated as a top team. Score = mean league points + 0.25 * mean goal difference.
Development seeds only. Usage: tune_h2h.py OUT_DIR SEED0 SEED1"""
import json, multiprocessing as mp, os, re, statistics, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common; from common import soccer
CAND = os.path.join(common.TACTICS, "candidates", "champion_candidate.py")
SPACE = {
    "SHOOT_RANGE": [34.0, 28.0, 40.0, 46.0], "SHOT_MARGIN": [-0.04, -0.10, 0.0], "TRANSITION_SECONDS": [1.5, 1.0, 2.5],
    "TRANSITION_GAIN": [4.0, 2.5, 6.0], "OPTION_SWITCH_MARGIN": [0.15, 0.08, 0.25], "POST_AIM_INSET": [0.20, 0.5, 0.0],
    "RELAY_PRESSURE": [5.5, 3.5, 8.0], "LOCK_SPACING": [2.8, 2.6, 3.0], "TRAIL_WALL": [2, 1, 3],
    "DRIBBLE_SPEED": [8.0, 6.5], "COUNTERPRESS_SECONDS": [1.0, 2.0],
}
def make(path, params):
    s = open(CAND).read()
    for k, v in params.items():
        s, n = re.subn(rf"^(    {k} = ).*$", rf"\g<1>{v!r}", s, count=1, flags=re.M); assert n == 1, k
    open(path, "w").write(s)
def unit(a):
    team, seed, side = a
    t, o = (team, CAND) if side == 0 else (CAND, team)
    m = soccer.play_match(t, o, seed=seed, kickoff_team=side, max_ticks=2400)
    me, th = (0, 1) if side == 0 else (1, 0); st = m.result["stats"]
    return dict(gf=m.score[me], ga=m.score[th], err=st[me]["policy_errors"], fouls=st[me]["fouls"], to=st[me]["policy_timeouts"])
def pts(r): return 3 if r["gf"] > r["ga"] else 1 if r["gf"] == r["ga"] else 0
def score(rs): return statistics.mean(pts(r) for r in rs), statistics.mean(r["gf"] - r["ga"] for r in rs)
if __name__ == "__main__":
    out, s0, s1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); os.makedirs(out, exist_ok=True)
    units = [(s, d) for s in range(s0, s1) for d in (0, 1)]; pool = mp.Pool(2)
    def run(params):
        p = os.path.join(out, "trial.py"); make(p, params)
        return pool.map(unit, [(p, s, d) for s, d in units])
    cur = {k: v[0] for k, v in SPACE.items()}
    ref = run(cur); rp, rg = score(ref); best = rp + 0.25 * rg; print("self-play reference", rp, rg, flush=True)
    log = [dict(change=None, pts=rp, gd=rg, score=best)]
    for rnd in range(2):
        improved = False
        for k, vals in SPACE.items():
            for v in vals:
                if v == cur[k]: continue
                trial = dict(cur); trial[k] = v; t0 = time.time(); rs = run(trial); p_, g_ = score(rs); sc = p_ + 0.25 * g_
                bad = sum(r["err"] + r["fouls"] for r in rs)
                rec = dict(round=rnd, change={k: v}, pts=round(p_, 3), gd=round(g_, 3), score=round(sc, 3), bad=bad, secs=round(time.time() - t0)); log.append(rec); print(json.dumps(rec), flush=True)
                if sc > best + 0.30 and bad == 0: best, cur, improved = sc, trial, True; print("ACCEPT", k, v, flush=True)
        if not improved: break
    json.dump(dict(final=cur, best=best, log=log), open(os.path.join(out, "result.json"), "w"), indent=1)
    make(os.path.join(out, "tuned_challenger.py"), cur); print("FINAL", cur, best)
