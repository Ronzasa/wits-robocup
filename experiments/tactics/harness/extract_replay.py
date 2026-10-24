"""Turn a website replay JSON (format v4) into a compact behaviour dataset for one team, in the team-relative
frame the controllers see (team 1 is rotated 180 degrees). Usage: extract_replay.py replay.json TEAM_INDEX out.json.gz"""
import json, gzip, sys, numpy as np
src, team, dst = sys.argv[1], int(sys.argv[2]), sys.argv[3]
d = json.load(open(src)); s = -1.0 if team == 1 else 1.0
rows = {r: [] for r in range(5)}
for fr in d['frames']:
    bp, bv = fr['ball_position'], fr['ball_velocity']
    bx, by, bvx, bvy = s * bp['x'], s * bp['y'], s * bv['x'], s * bv['y']
    pl = fr['players']; mine = pl[5 * team:5 * team + 5]; opp = pl[5 * (1 - team):5 * (1 - team) + 5]
    for r, p in enumerate(mine):
        a = p.get('action')
        if not a: continue
        px, py = s * p['position']['x'], s * p['position']['y']; vx, vy = s * p['velocity']['x'], s * p['velocity']['y']
        o = min(opp, key=lambda q: (s * q['position']['x'] - px) ** 2 + (s * q['position']['y'] - py) ** 2)
        ox, oy = s * o['position']['x'] - px, s * o['position']['y'] - py
        mv = a['movement']; kd = a['kick_direction']
        kx, ky = (s * kd['x'], s * kd['y']) if kd else (0.0, 0.0)
        rows[r].append([px, py, vx, vy, bx, by, bvx, bvy, ox, oy, p['kick_cooldown_ticks'], s * mv['x'], s * mv['y'], kx, ky, a['kick_power'] if kd else 0.0])
out = {'team_id': d['header']['team_ids'][team], 'match': d['recorded']['match_id'], 'final': d['recorded']['score'],
       'cols': 'px,py,vx,vy,bx,by,bvx,bvy,ox,oy,cd,mx,my,kx,ky,kp', 'rows': {str(r): np.round(np.array(v), 3).tolist() for r, v in rows.items()}}
with gzip.open(dst, 'wt') as g: json.dump(out, g)
for r in range(5):
    A = np.array(rows[r]); print('role', r, 'rows', len(A), 'mean pos', A[:, 0].mean().round(1), A[:, 1].mean().round(1), 'kicks', int((A[:, 15] > 0).sum()), 'mean|move|', np.hypot(A[:, 11], A[:, 12]).mean().round(2))
