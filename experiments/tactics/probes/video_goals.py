"""Describe how the top team scored in the 4 ron videos (positions from per-frame colour tracking).
Input: scratchpad fr/ron_track.pkl + ron_events.pkl (pitch coords x in [-50,50], y in [-30,30])."""
import pickle, numpy as np, math, sys
T = pickle.load(open("fr/ron_track.pkl", "rb")); E = pickle.load(open("fr/ron_events.pkl", "rb"))
def ball(fr):
    o = fr["orange"]; return (o[0][0], o[0][1]) if o else None
rows = []
for n in (1, 2, 3, 4):
    fr = T[n]
    for team, g in E[n]["events"]:
        opp = "red" if team == "blue" else "blue"
        # ball position shortly before the goal tells which goal
        bs = [ball(fr[i]) for i in range(max(0, g - 12), g) if ball(fr[i])]
        if not bs: continue
        gx = 1.0 if np.mean([b[0] for b in bs]) > 0 else -1.0     # scorer attacks +x if ball ended at +x
        def feats(i):
            att = [p for p in fr[i][team]]; dfn = [p for p in fr[i][opp]]
            adv = sum(1 for p in att if p[0] * gx > 10)          # scorers well into attacking half
            box = sum(1 for p in att if p[0] * gx > 30)
            dbox = sum(1 for p in dfn if p[0] * gx > 30)
            return adv, box, dbox, len(att), len(dfn)
        i0 = max(0, g - 40)
        path = [ball(fr[i]) for i in range(max(0, g - 80), g) if ball(fr[i])]
        start = path[0] if path else None
        # ball control changes: count direction changes > 50 deg as touches/passes
        turns = 0
        for a, b, c in zip(path, path[1:], path[2:]):
            v1 = (b[0]-a[0], b[1]-a[1]); v2 = (c[0]-b[0], c[1]-b[1])
            n1, n2 = math.hypot(*v1), math.hypot(*v2)
            if n1 > .4 and n2 > .4 and (v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2) < .64: turns += 1
        f0, f1 = feats(i0), feats(max(0, g - 6))
        rows.append((n, team, g, round(gx), start and (round(start[0]*gx), round(start[1])), turns, f0, f1,
                     round(np.mean([abs(b[1]) for b in bs]), 1)))
print("vid scorer frame dir  ball@-80f(x toward goal,y)  touches  [adv,box,defbox,n_att,n_def]@-40f  @-6f  |y| at goal")
for r in rows: print(r)
import statistics as S
print("mean attackers beyond +10 at -6f", S.mean(r[7][0] for r in rows), " in final third", S.mean(r[7][1] for r in rows),
      " defenders in final third", S.mean(r[7][2] for r in rows), " mean turns", S.mean(r[5] for r in rows),
      " mean |y| at goal", S.mean(r[8] for r in rows))
