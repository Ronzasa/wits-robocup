"""Audit both fixed holdout arms and report paired, seed-cluster changes."""
import json
import random
import statistics
from pathlib import Path
from lab import LAB, SPLITS, MONSTER_V1_SHA, protect, report, sha


def points(row):
    a,b = row['score']
    return 3 if a>b else int(a==b)


def paired(before,after):
    groups = {}
    for old,new in zip(before,after):
        assert old['seed']==new['seed']
        groups.setdefault(old['seed'],[]).append((points(new)-points(old),new['goal_difference']-old['goal_difference']))
    means = [tuple(statistics.mean(v[i] for v in values) for i in (0,1)) for values in groups.values()]
    rng = random.Random(291117)
    boot = [sorted(statistics.mean(v[i] for v in rng.choices(means,k=len(means))) for _ in range(3000)) for i in (0,1)]
    return {'matches':len(before),'seed_clusters':len(means),
            'points_per_match_change':statistics.mean(v[0] for v in means),
            'mean_gd_change':statistics.mean(v[1] for v in means),
            'points_change_seed_bootstrap95':[boot[0][75],boot[0][2924]],
            'gd_change_seed_bootstrap95':[boot[1][75],boot[1][2924]]}


def main():
    protect()
    selection = json.loads((LAB/'round2-selection.json').read_text())
    lock = json.loads((LAB/'round2-holdout-lock.json').read_text())
    selected_sha = selection['sha256']
    assert selected_sha==lock['sha256']==sha(LAB/selection['source'])
    assert MONSTER_V1_SHA==sha(LAB/selection['control'])
    expected = {(seed,side,kickoff) for seed in range(*SPLITS['round2-holdout']) for side in (0,1) for kickoff in (0,1)}
    key = lambda r:(r['seed'],r['candidate_side'],r['kickoff_team'])
    before_all,after_all,opponents = [],[],{}
    for name in ('titan','blue-c-combined','v21-close-outlet','v25-fast-post'):
        old_path = LAB/'results'/('r2-holdout-control-'+name+'.json')
        new_path = LAB/'results'/('r2-holdout-'+name+'.json')
        old_data,new_data = [json.loads(p.read_text()) for p in (old_path,new_path)]
        assert old_data['source_sha256']==MONSTER_V1_SHA and new_data['source_sha256']==selected_sha
        assert old_data['opponent']==new_data['opponent'] and old_data['opponent_sha256']==new_data['opponent_sha256']
        arms = []
        for data in (old_data,new_data):
            assert not data.get('instrumented_cpu_profile')
            assert sha(LAB/data['source_snapshot'])==data['source_sha256']
            rows = sorted(data['results'],key=key)
            assert len(rows)==len({key(r) for r in rows})==100
            assert {key(r) for r in rows}==expected
            for r in rows:
                assert r['ticks']==2400 and r['terminal_reason']=='time_limit'
                assert r['config_hash']=='372990895c7eca2a' and r['engine_version']=='0.1.0'
                assert r['score']==(r['absolute_score'][::-1] if r['candidate_side'] else r['absolute_score'])
                assert r['candidate_kickoff']==(r['candidate_side']==r['kickoff_team'])
                assert all(r['stats'][0]['validation'][k]==0 for k in ('missing_actions','invalid_player_ids','non_finite_values'))
            arms.append(rows)
        before,after = arms
        clean = [(old,new) for old,new in zip(before,after)
                 if all(s['policy_errors']==0 and s['policy_timeouts']==0 for r in (old,new) for s in r['stats'])]
        opponents[name] = {'before_file':str(old_path.relative_to(LAB)),'after_file':str(new_path.relative_to(LAB)),
                           'before':report(before),'after':report(after),'paired':paired(before,after),
                           'fault_free_paired':paired([p[0] for p in clean],[p[1] for p in clean]),
                           'fault_free_after':report([p[1] for p in clean])}
        before_all.extend(before)
        after_all.extend(after)
    result = {'protocol_checks_passed':True,'competitive_matches':len(before_all)+len(after_all),
              'selected_sha256':selected_sha,'control_sha256':MONSTER_V1_SHA,
              'current_monster_sha256':sha(LAB/'monster/team.py'),
              'opponents':opponents,'pooled_before':report(before_all),'pooled_after':report(after_all),
              'pooled_paired':paired(before_all,after_all),
              'uncertainty_note':'Each arm has 400 fixtures but 25 seed clusters. Paired bootstrap resamples seeds, not individual games. Timeout-filtered results are descriptive sensitivity only; all fixtures remain primary.'}
    gen_expected = {(seed,side,kickoff) for seed in range(780000,780005) for side in (0,1) for kickoff in (0,1)}
    generalization = {}
    for opponent in ('balanced','tactical','possession','structured_attack','man_marking','ball_chaser','titan-original','titan-buggy'):
        arms = []
        for version,digest in (('v25-fast-post',MONSTER_V1_SHA),('v51-stream-post',selected_sha)):
            path = LAB/'results'/f'r2-generalization-{version}-{opponent}.json'
            data = json.loads(path.read_text())
            assert data['source_sha256']==digest and not data.get('instrumented_cpu_profile')
            rows = sorted(data['results'],key=key)
            assert len(rows)==20 and {key(r) for r in rows}==gen_expected
            assert all(r['ticks']==2400 and r['terminal_reason']=='time_limit' and r['config_hash']=='372990895c7eca2a' for r in rows)
            assert all(r['stats'][0]['validation'][k]==0 for r in rows for k in ('missing_actions','invalid_player_ids','non_finite_values'))
            arms.append(report(rows))
        generalization[opponent] = {'before':arms[0],'after':arms[1]}
    result['generalization'] = generalization
    result['generalization_matches'] = 320
    (LAB/'ROUND2_AUDIT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    lines = ['# Second-generation MONSTER: locked holdout','',
             '100 full fixtures per opponent and policy; 25 seeds crossed with both sides and kickoff owners.',
             'Official engine 0.1.0, unchanged course config, 2,400 ticks, enforced 20 ms for both teams.','',
             '| Opponent | Old v25 W/D/L | New v51 W/D/L | Old goals | New goals | Paired points/game change (95% seed CI) |',
             '|---|---:|---:|---:|---:|---:|']
    def wdl(s):
        return f"{s['team_a_wins']}/{s['draws']}/{s['team_b_wins']}"
    def goals(s):
        return f"{s['goals'][0]}–{s['goals'][1]}"
    for name,o in opponents.items():
        b,a,p = o['before'],o['after'],o['paired']
        lo,hi = p['points_change_seed_bootstrap95']
        lines.append(f"| {name} | {wdl(b)} | {wdl(a)} | {goals(b)} | {goals(a)} | {p['points_per_match_change']:+.3f} [{lo:+.3f}, {hi:+.3f}] |")
    b,a,p = result['pooled_before'],result['pooled_after'],result['pooled_paired']
    lines += ['',f"Overall: old **{wdl(b)}, {goals(b)}**; new **{wdl(a)}, {goals(a)}**.",
              f"Pooled points/game change **{p['points_per_match_change']:+.3f}**, seed-bootstrap 95% CI **{p['points_change_seed_bootstrap95']}**.",
              '',f"New policy errors/timeouts: **{a['policy_errors'][0]}/{a['policy_timeouts'][0]}**.",
              f"New decision mean/max: **{a['team_stats'][0]['decision_mean_ms']:.3f}/{a['team_stats'][0]['decision_max_ms']:.3f} ms**.",
              '',result['uncertainty_note'],'',
              'Full metrics, per-opponent latency and fault-free sensitivity are in `ROUND2_AUDIT.json`.',
              'See `ROUND2.md` for rejected experiments and `ROUND2_REPORT.md` for interpretation.']
    (LAB/'ROUND2_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'protocol_checks_passed':True,'matches':result['competitive_matches'],
                      'generalization_matches':result['generalization_matches'],
                      'before_wdl':[b['team_a_wins'],b['draws'],b['team_b_wins']],
                      'after_wdl':[a['team_a_wins'],a['draws'],a['team_b_wins']],
                      'before_goals':b['goals'],'after_goals':a['goals'],'paired':p,
                      'after_errors_timeouts':[a['policy_errors'][0],a['policy_timeouts'][0]],
                      'after_mean_max_ms':[a['team_stats'][0]['decision_mean_ms'],a['team_stats'][0]['decision_max_ms']]}))


if __name__=='__main__':
    main()
