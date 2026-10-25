"""Descriptive report of a website replay: both teams' kick power, rejections, possession, shape, goals."""
import json, sys, collections, numpy as np
d = json.load(open(sys.argv[1])); h = d['header']; ev = d['events']; fr = d['frames']
print(h['team_ids'], 'seed', h['seed'], 'kickoff', h['kickoff_team'], 'final', d['recorded']['score'], d['recorded']['match_id'])
for t in (0, 1):
    k = [e for e in ev if e['kind'] == 'kick' and e['team'] == t]; r = [e for e in ev if e['kind'] == 'kick_rejected' and e['team'] == t]
    p = np.array([e['power'] for e in k]) if k else np.array([0.0])
    s = -1.0 if t == 1 else 1.0
    xs = np.array([[s * q['position']['x'] for q in f['players'][5 * t + 1:5 * t + 5]] for f in fr])
    poss = np.mean([f['possession_team'] == t for f in fr])
    mates = 0
    for e in k:
        f = fr[e['tick']]; pp = f['players'][e['player']]['position']; dx, dy = e['direction']['x'], e['direction']['y']
        for i, q in enumerate(f['players'][5 * t:5 * t + 5]):
            if 5 * t + i == e['player']: continue
            m = q['position']; a = abs(np.degrees(np.arctan2(dx * (m['y'] - pp['y']) - dy * (m['x'] - pp['x']), dx * (m['x'] - pp['x']) + dy * (m['y'] - pp['y']))))
            if a < 15: mates += 1; break
    print(f"team {t} {h['team_ids'][t]}: kicks {len(k)} rejected {len(r)} {dict(collections.Counter(e['reason'] for e in r))} | power median {np.median(p):.2f} full(>=.95) {np.mean(p >= .95):.2f} <0.5 {np.mean(p < .5):.2f} | aimed at teammate {mates/max(1,len(k)):.2f} | possession {poss:.2f} | outfield mean x (attack-rel) {xs.mean(0).round(1)} | goals {[e['scorer'] for e in ev if e['kind']=='goal' and e['team']==t]}")
for g in [e for e in ev if e['kind'] == 'goal']:
    f = fr[max(0, g['tick'] - 1)]; s = -1.0 if g['team'] == 1 else 1.0
    print('goal@', g['tick'], 'team', g['team'], 'scorer', g['scorer'], 'ball y', round(s * f['ball_position']['y'], 1), 'own', g['own_goal'])
