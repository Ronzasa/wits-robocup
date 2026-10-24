"""Profile a team's possession / passing / defending stats vs several opponents (both sides)."""
import os, sys, json, statistics as S
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "harness"))
import common; from common import soccer
team = sys.argv[1]; opps = sys.argv[2].split(","); s0, s1 = int(sys.argv[3]), int(sys.argv[4])
for opp in opps:
    R = []
    for seed in range(s0, s1):
        for side in (0, 1):
            a, b = (team, common.spec(opp)) if side == 0 else (common.spec(opp), team)
            m = soccer.play_match(a, b, seed=seed, kickoff_team=side, max_ticks=2400)
            me, th = (0, 1) if side == 0 else (1, 0); st = m.result["stats"]
            R.append(dict(gf=m.score[me], ga=m.score[th], ctl=st[me]["controlled_ticks"] / 2400, ctl_o=st[th]["controlled_ticks"] / 2400,
                          terr=st[me]["territory_ticks"] / 2400, passes=st[me]["passes_completed"], shots=st[me]["shots"], shots_o=st[th]["shots"],
                          pts=common.points(m.score[me], m.score[th]), kicks=st[me]["kicks"]))
    f = lambda k: S.mean(r[k] for r in R)
    print(f"{opp:18s} pts {f('pts'):.2f} GF {f('gf'):.2f} GA {f('ga'):.2f} ctl {f('ctl'):.1%} (opp {f('ctl_o'):.1%}) terr {f('terr'):.1%} passes {f('passes'):.1f} shots {f('shots'):.1f} (opp {f('shots_o'):.1f})", flush=True)
