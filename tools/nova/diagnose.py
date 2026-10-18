"""Development replay of executed NOVA plans; not a timing qualification.

Only the external harness observes selected plans. The standalone controller
file remains byte-frozen. Recorded native first steps show when collisions
or adversarial input invalidate the isolated launch prediction.
"""
import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'student-sdk'))
from soccer import play_match
from soccer import runner


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--source', type=Path)
    p.add_argument('--label', default='execution-replays')
    p.add_argument('--development-seed-index', type=int, default=18)
    a = p.parse_args()
    reg = json.loads((ROOT / 'docs/nova-1/registration.json').read_text())
    if a.source:
        source = a.source.resolve()
    else:
        selected = json.loads((ROOT / 'docs/nova-1/selected-policy.json').read_text())
        source = ROOT / selected['candidate_path']
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    assert 0 <= a.development_seed_index < len(reg['development'])
    seed = reg['development'][a.development_seed_index]
    assert a.label and '/' not in a.label and a.label != '..'
    folder = a.work / a.label;assert not folder.exists();folder.mkdir()
    original = runner._decide
    rows = []
    try:
        for side in (0, 1):
            for kickoff in (True, False):
                controller = runner._resolve(str(source))
                select = controller._select
                def selected_plan(*args, **kwargs):
                    plan = select(*args, **kwargs)
                    controller._observed_plan = plan
                    return plan
                controller._select = selected_plan
                controller._observed_plan = None
                pending = None;events = [];active = None;timeline = []
                def observed(c, obs):
                    nonlocal pending, active
                    if c is not controller:return original(c, obs)
                    before = controller._receive
                    controller._observed_plan = None
                    answer = original(c, obs)
                    plan = controller._observed_plan
                    ball = (*obs.ball.position, *obs.ball.velocity)
                    if obs.tick % 5 == 0:
                        timeline.append({'tick': obs.tick, 'score': obs.score, 'ball': ball,
                            'last_touch': obs.ball.last_touch, 'receive': controller._receive,
                            'chaser': controller._chaser_id, 'cover': controller._cover_id,
                            'friends': [(p.id, *p.position, *p.velocity, p.kick_cooldown_ticks) for p in obs.my_players],
                            'opponents': [(p.id, *p.position, *p.velocity, p.kick_cooldown_ticks) for p in obs.opponents]})
                    if pending is not None:
                        pending['actual_next_ball'] = ball
                        pending['next_score'] = obs.score
                        pending['score_changed'] = pending['score'] != obs.score
                        predicted = pending['predicted_launch']
                        pending['first_step_position_error'] = ((ball[0]-predicted[0])**2+(ball[1]-predicted[1])**2)**.5
                        pending = None
                    if active is not None:
                        pid = active['receiver']
                        touch = obs.ball.last_touch
                        if touch == pid:
                            active['outcome'] = 'receiver touched';active['end_tick'] = obs.tick;active = None
                        elif touch is not None and touch not in (active['carrier'], pid):
                            active['outcome'] = 'other player touched';active['other_touch'] = touch;active['end_tick'] = obs.tick;active = None
                        elif obs.tick > active['tick'] + 50:
                            active['outcome'] = 'no receiver touch in 50 ticks';active['end_tick'] = obs.tick;active = None
                    if before is not None and controller._receive is None:
                        events.append({'type': 'reception_plan_ended', 'tick': obs.tick, 'last_touch': obs.ball.last_touch,
                                       'can_kick_receiver': obs.can_kick(before[0]), 'old_plan': before})
                    if plan is not None:
                        event = {'type': 'selected', 'tick': obs.tick, 'score': obs.score, 'ball': ball,
                                 'kind': plan['kind'], 'carrier': plan['carrier'], 'receive': plan['receive'],
                                 'features': plan['features'], 'value': plan['value'], 'predicted_launch': plan['launch'],
                                 'movements': plan['movements'], 'sdk_wall_ms': answer[1]}
                        events.append(event);pending = event
                        if plan['receive'] is not None:
                            if active is not None:active['outcome'] = 'superseded by next pass'
                            active = {'type': 'reception_outcome', 'tick': obs.tick, 'carrier': plan['carrier'],
                                      'receiver': plan['receive'][0], 'initial_aim': plan['receive'][1],
                                      'collection': plan['receive'][2], 'outcome': 'unfinished at match end'}
                            events.append(active)
                    return answer
                runner._decide = observed
                teams = [controller, str(ROOT / 'my-team/team.py')]
                if side:teams.reverse()
                outcome = play_match(*teams, seed=seed, kickoff_team=side if kickoff else 1-side,
                    config_path=str(ROOT / 'configs/default.toml'), max_ticks=2400, per_decision_timeout_ms=20.,
                    record_replay=str(folder / f'side{side}-kick{int(kickoff)}.rep'))
                (folder / f'side{side}-kick{int(kickoff)}.json').write_text(json.dumps({'diagnostic_not_timing_gate': True,
                    'seed': seed, 'side': side, 'kickoff': kickoff, 'source_sha256': source_hash,
                    'result': outcome.result, 'events': events, 'timeline': timeline}, indent=2) + '\n')
                rows.extend(events)
    finally:
        runner._decide = original
    outcomes = {}
    for row in rows:
        if row['type'] == 'reception_outcome':outcomes[row['outcome']] = outcomes.get(row['outcome'], 0) + 1
    launches = [q for q in rows if q['type'] == 'selected' and 'first_step_position_error' in q and not q['score_changed']]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    result = {'seed': seed, 'fixtures': 4, 'source_sha256': source_hash,
              'diagnostic_not_timing_gate': True, 'reception_outcomes': outcomes,
              'launches': len(launches), 'launch_position_error_gt_half_unit': sum(q['first_step_position_error'] > .5 for q in launches),
              'limits': 'Native touches describe contact, not controlled possession. Other-player contacts can be friendly or opposing. Harness instrumentation changes timing; no reliability gate uses these runs.'}
    (folder / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
