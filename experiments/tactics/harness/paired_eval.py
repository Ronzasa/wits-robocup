"""Paired evaluation. Units = (opponent, seed, our side). Each unit played for baseline and candidate.
Usage: paired_eval.py CAND OPP[,OPP..] SEED0 SEED1 [out.json]. Records goals, points, own stats, timeouts, errors, decision time."""
import json, math, os, random, statistics, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common; from common import soccer
BASE = os.path.join(common.TACTICS, "baseline", "team.py")
def play(team, opp, seed, side):
    a, b = (team, common.spec(opp)) if side == 0 else (common.spec(opp), team)
    m = soccer.play_match(a, b, seed=seed, kickoff_team=side, max_ticks=2400)
    me, th = (0, 1) if side == 0 else (1, 0)
    st = m.result["stats"]
    f, g = m.score[me], m.score[th]
    return dict(gf=f, ga=g, pts=common.points(f, g), fouls=st[me]["fouls"], errors=st[me]["policy_errors"],
                timeouts=st[me]["policy_timeouts"], mean_ms=st[me]["decision_time_ms"]["total_ms"] / max(1, st[me]["decision_time_ms"]["count"]),
                max_ms=st[me]["decision_time_ms"]["max_ms"])
def ci(d):
    n = len(d); m = statistics.mean(d)
    if n < 2: return m, m, m
    se = statistics.stdev(d) / math.sqrt(n); h = 1.96 * se
    return m, m - h, m + h
def boot(d, B=2000):
    rnd = random.Random(1); n = len(d)
    ms = sorted(sum(rnd.choice(d) for _ in range(n)) / n for _ in range(B)); return ms[int(.025 * B)], ms[int(.975 * B)]
if __name__ == "__main__":
    cand, opps, s0, s1 = sys.argv[1], sys.argv[2].split(","), int(sys.argv[3]), int(sys.argv[4])
    out = sys.argv[5] if len(sys.argv) > 5 else None
    rows = []
    for opp in opps:
        for seed in range(s0, s1):
            for side in (0, 1):
                b = play(BASE, opp, seed, side); c = play(cand, opp, seed, side)
                rows.append(dict(opp=opp, seed=seed, side=side, base=b, cand=c))
    for opp in opps + ["ALL"]:
        r = [x for x in rows if opp == "ALL" or x["opp"] == opp]
        d = [x["cand"]["pts"] - x["base"]["pts"] for x in r]
        m, lo, hi = ci(d); bl, bh = boot(d)
        agg = lambda k, w: statistics.mean(x[w][k] for x in r)
        print(f"{opp:18s} n={len(r):3d} dPts={m:+.3f} CI[{lo:+.3f},{hi:+.3f}] boot[{bl:+.3f},{bh:+.3f}] "
              f"GF {agg('gf','base'):.2f}->{agg('gf','cand'):.2f} GA {agg('ga','base'):.2f}->{agg('ga','cand'):.2f} "
              f"TO/match {agg('timeouts','base'):.4f}->{agg('timeouts','cand'):.4f} err {sum(x['cand']['errors'] for x in r)} fouls {sum(x['cand']['fouls'] for x in r)} "
              f"ms {agg('mean_ms','cand'):.2f} max {max(x['cand']['max_ms'] for x in r):.1f}")
    if out: json.dump(rows, open(out, "w"))
