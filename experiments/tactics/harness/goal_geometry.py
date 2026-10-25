"""For each goal conceded by team DEF (index), describe the shot and whether DEF's keeper could physically save it.
Usage: goal_geometry.py replay.json DEF_TEAM_INDEX"""
import json, sys, numpy as np
d = json.load(open(sys.argv[1])); de = int(sys.argv[2]); at = 1 - de
fr = d['frames']; ev = d['events']; kicks = [e for e in ev if e['kind'] == 'kick']
s = 1.0 if de == 0 else -1.0     # attack-relative sign for the defending side (they defend -x after multiplying)
def reach(T):
    v = x = 0.0
    for _ in range(T): v = min(8.0, v + 1.0); x += v / 20.0
    return x
for g in [e for e in ev if e['kind'] == 'goal' and e['team'] == at]:
    t = g['tick']; last = [k for k in kicks if k['team'] == at and k['tick'] <= t][-1]; kt = last['tick']
    f = fr[kt]; pl = f['players']; kp = pl[last['player']]['position']; b = f['ball_position']
    keeper = pl[5 * de]['position']; kend = fr[t - 1]['players'][5 * de]['position']
    yb = fr[t]['ball_position']['y']; T = t - kt; need = abs(yb - keeper['y']) - 2.2
    dist = 50 + s * kp['x'] if False else 50 - abs(kp['x']) * 0 - (kp['x'] * s * -1 if False else 0)
    shooter_dist = 50.0 + s * kp['x'] * (-1.0) if False else 50.0 - (s * kp['x'])  # distance to our goal line along x for de=0: kp.x + 50
    defenders = [(round(s * q['position']['x'], 1), round(s * q['position']['y'], 1)) for q in pl[5 * de + 1:5 * de + 5]]
    print(f"goal@{t}: shooter {last['player']} x-dist to goal {abs(-50 * s - kp['x']):.0f} y {s*kp['y']:.1f} power {last['power']:.2f} kick->goal {T} ticks | ball y at line {s*yb:.1f} | keeper moved {abs(kend['y']-keeper['y']):.1f} need {max(0,need):.1f} max {reach(T):.1f} savable {need<=reach(T)} | our outfield (own-goal-relative x,y) {defenders}")
