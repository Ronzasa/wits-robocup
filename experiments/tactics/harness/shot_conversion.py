"""Count on-target shots (kick toward the goal mouth from <=26 units, power>=0.9) per attacking team and how many scored."""
import json, sys
d = json.load(open(sys.argv[1])); fr = d['frames']; ev = d['events']
goals = [e for e in ev if e['kind'] == 'goal']
for at in (0, 1):
    de = 1 - at; gx = 50.0 if at == 0 else -50.0
    n = sc = 0
    for e in ev:
        if e['kind'] != 'kick' or e['team'] != at or e['power'] < 0.9: continue
        f = fr[e['tick']]; b = f['ball_position']; dx, dy = e['direction']['x'], e['direction']['y']
        if dx * (gx - b['x']) <= 0 or abs(gx - b['x']) > 26: continue
        yl = b['y'] + dy / dx * (gx - b['x']) if abs(dx) > 1e-6 else 99
        if abs(yl) > 7.5: continue
        n += 1
        if any(g['team'] == at and 0 < g['tick'] - e['tick'] <= 30 for g in goals): sc += 1
    print(f"{d['header']['team_ids'][at]:28s} on-target power shots <=26u: {n}, followed by a goal within 30 ticks: {sc}")
