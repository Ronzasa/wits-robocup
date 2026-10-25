"""Absolute quick score of one team file vs several opponents (no baseline pairing): points, GF, GA, fouls, timeouts."""
import os, sys, statistics as S
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common; from common import soccer
team, opps, s0, s1 = sys.argv[1], sys.argv[2].split(","), int(sys.argv[3]), int(sys.argv[4])
tot = []
for opp in opps:
    R = []
    for seed in range(s0, s1):
        for side in (0, 1):
            a, b = (team, common.spec(opp)) if side == 0 else (common.spec(opp), team)
            m = soccer.play_match(a, b, seed=seed, kickoff_team=side, max_ticks=2400)
            me, th = (0, 1) if side == 0 else (1, 0); st = m.result["stats"]
            R.append((common.points(m.score[me], m.score[th]), m.score[me], m.score[th], st[me]["fouls"], st[me]["policy_timeouts"]))
    tot += R
    print(f"{opp:18s} pts {S.mean(r[0] for r in R):.2f} GF {S.mean(r[1] for r in R):.2f} GA {S.mean(r[2] for r in R):.2f} fouls {sum(r[3] for r in R)}", flush=True)
print(f"ALL                pts {S.mean(r[0] for r in tot):.2f} GF {S.mean(r[1] for r in tot):.2f} GA {S.mean(r[2] for r in tot):.2f} fouls {sum(r[3] for r in tot)} timeouts {sum(r[4] for r in tot)}")
