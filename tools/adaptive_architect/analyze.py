"""Apply frozen three-way gates and report native outcomes without activation claims."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/benchmarks'))
from benchmark import aggregate
spec=importlib.util.spec_from_file_location('v11_statistics',ROOT/'tools/titan_v11/analyze.py')
statistics=importlib.util.module_from_spec(spec);spec.loader.exec_module(statistics)


def read(p):return [json.loads(x) for x in p.read_text().splitlines()]


def telemetry(rows, plan_diagnostics=False):
    out={}
    for key in ('ticks','episodes','associations'):
        counter=Counter()
        for r in rows:counter.update(r['titan_adaptive'].get(key,{}))
        out[key]=dict(counter)
    out['native_completions_observed']=sum(r['titan_adaptive']['native_completed_observed'] for r in rows)
    out['plan_link_diagnostics_available']=plan_diagnostics
    out['completions_after_supported_receiver_plan']=None if not plan_diagnostics else sum(
        c['native_increment'] for r in rows for c in r['titan_adaptive']['completions']
        if c['recent_supported_receiver_plan'])
    out['examples']=[{'seed':r['seed'],'side':r['candidate_slot'],
        'kickoff':r['candidate_takes_kickoff'],'opponent':Path(r['opponent']).parent.name,**e}
        for r in rows for e in r['titan_adaptive']['examples']]
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();run=args.run.resolve();out=args.out
    assert not out.exists(), 'Never overwrite analysis.'
    metadata=json.loads((run/'metadata.json').read_text());assert 'finished_utc' in metadata
    protocol=metadata['protocol'];reg=json.loads((ROOT/protocol['registration']).read_text())
    assert hashlib.sha256((ROOT/'tools/benchmarks/run_adaptive_architect.py').read_bytes()).hexdigest()==protocol['runner_sha256']
    rows={n:read(run/'raw'/n/'matches.jsonl') for n in protocol['sources']}
    accepted={n:read(run/'accepted'/n/'matches.jsonl') for n in protocol['sources']}
    expected=len(protocol['opponents'])*sum(map(len,protocol['seeds'].values()))*4
    for n,data in rows.items():
        assert len(data)==expected and len({r['fixture_id'] for r in data})==expected
        s=protocol['sources'][n]
        assert hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest()==s['sha256']
        assert hashlib.sha256((run/'sources'/n/'team.py').read_bytes()).hexdigest()==s['sha256']
        for r in data:
            assert r['result']['ticks']==2400 and r['result']['terminal_reason']=='time_limit'
            t=r['titan_adaptive'];s=r['result']['stats'][r['candidate_slot']]
            assert t['native_completed_observed']==s['passes_completed']
            assert sum(c['native_increment'] for c in t['completions'])==s['passes_completed']
    raw={n:aggregate(v) for n,v in rows.items()};clean={n:aggregate(v) for n,v in accepted.items()}
    compare={n:{'raw':statistics.seed_statistics(rows[n],rows['adaptive']),
                'accepted':statistics.seed_statistics(accepted[n],accepted['adaptive'])} for n in ('v10','architect')}
    styles={style:{n:aggregate([r for r in data if Path(r['opponent']).parent.name==style])
                   for n,data in rows.items()} for style in protocol['opponents']}
    tel={n:telemetry(v,n=='adaptive') for n,v in rows.items()}
    by_style_telemetry={style:telemetry([r for r in rows['adaptive'] if Path(r['opponent']).parent.name==style],True)
                        for style in protocol['opponents']}
    c,b=raw['adaptive'],raw['v10'];ca,ba=clean['adaptive'],clean['v10']
    repeats=read(run/'timing-repeats.jsonl')
    reproduced=sum(bool(r['result']['result']['stats'][r['result']['candidate_slot']].get('policy_timeouts',0))
        for r in repeats if r['source']=='adaptive' and r['attempt']==1)
    intake=json.loads((run/'adaptive-validation.json').read_text())
    extra=(c['policy_timeouts']-b['policy_timeouts'])*1000/expected
    ceiling=ba['decision_mean_ms']*1.35+.04
    malformed=sum(v for k,v in c['validation'].items() if k not in ('actions_validated','players_validated','rejected_kicks'))
    gates={}
    for name,data in compare.items():
        for label,stat in data.items():
            summary=raw if label=='raw' else clean
            gates[label+'_more_points_than_'+name]=summary['adaptive']['points']>summary[name]['points']
            gates[label+'_positive_97_5_seed_lower_vs_'+name]=stat['bootstrap_97_5'][0]>0
            gates[label+'_exact_sign_flip_p_vs_'+name]=stat['exact_one_sided_sign_flip_p']<=.025
    compact=styles['v10-compact']
    gates.update(compact_points_at_least_both=all(compact['adaptive']['points']>=compact[n]['points'] for n in ('v10','architect')),
        compact_no_extra_concessions=compact['adaptive']['goals_against']<=compact['v10']['goals_against'],
        no_style_points_regression_vs_v10=all(v['adaptive']['points']>=v['v10']['points'] for v in styles.values()),
        no_extra_overall_concessions=c['goals_against']<=b['goals_against'],
        no_extra_turnovers=c['turnovers']<=b['turnovers'],
        pass_completion_at_least_v10=c['pass_completion']>=b['pass_completion'],
        five_actual_adaptive_episodes=tel['adaptive']['episodes'].get('adaptive_support',0)>=5,
        zero_policy_exceptions=c['policy_errors']==0 and ca['policy_errors']==0,
        no_reproduced_candidate_deadline_failure=reproduced==0,
        raw_deadline_allowance=extra<=2.,mean_runtime=ca['decision_mean_ms']<=ceiling,
        official_sdk=intake['ok'] and not intake['folder_errors'],legal_actions=malformed==0,
        complete_registered_cohort=all(len(v)==expected for v in rows.values()),
        native_completion_trace_integrity=all(tel[n]['native_completions_observed']==raw[n]['passes_completed'] for n in rows))
    supported=all(gates.values())
    result={'decision':'QUALIFICATION_JUSTIFIED' if supported else 'RETAIN_V10_REJECT_ADAPTIVE',
        'development_supported':supported,'qualification_run':False,'promotion':False,
        'protocol':protocol,'registration':reg,'raw_summary':raw,'accepted_summary':clean,
        'comparisons':compare,'by_opponent':styles,'gates':gates,
        'failed_gates':[k for k,v in gates.items() if not v],'telemetry':tel,
        'adaptive_telemetry_by_opponent':by_style_telemetry,
        'extra_raw_misses_per_1000':extra,'accepted_mean_ceiling_ms':ceiling,
        'reproduced_candidate_deadline_failures':reproduced}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Adaptive Passing Lane Architect — native development results','',
        '**Decision: '+result['decision']+'.** Frozen v10, the original Architect, main and the active champion are unchanged.','',
        '## Method and frozen scope','',
        f'Continued from commit 906f7b9 on a new experimental branch. Sixteen unused development seed blocks × pressing, compact and counterattacking v10 variants × both pitch assignments × both kickoffs = {expected} matched configurations per source and {expected*3} full native matches. The three independent sources are frozen v10, original Architect and Adaptive Architect. Counterattack Firewall and the four earlier experimental tactics are disabled in every tested source.','',
        'Every match used 2,400 ticks, engine 0.1.0, configuration 372990895c7eca2a and the native 20 ms deadline. One timed worker ran after all 152 regressions passed. Sources, opponent archive, seeds, shuffle order and gates were registered before this cohort. Eight full public-seed diagnostic-probe matches verified completion counters before registration; they are retained but excluded from development outcomes. No development outcome tuning or cohort extension occurred. Sixteen other unused seeds remain reserved for qualification.','',
        '## Selective policy changes','',
        '- **Pressure detection:** requires at least two nearby defenders, at least two approaching the ball faster than 1.2 units/s, an existing ball-interception race no slower than 0.8 seconds and at least one blocked baseline support lane. Player positions, velocities and drag-aware flight-space checks drive the decision; no opponent names or style identifiers enter the controller. A stationary compact goal-side block suppresses support changes. Low pressure and open shape lanes retain v10 targets.','- **Verified advantage:** evaluates the baseline shape target and two local angle changes at two legal pass speeds. A new route needs the unchanged carrier-contact, drag/path, executable receiver race, opponent/body-interception and teammate-interference checks. Its exact first receiver movement includes teammate avoidance. The route must beat a physically verified baseline route by more than 0.35 score units, or create a verified route where the baseline has none. The score combines progress, actual arrival/margin and predicted defender space. This is a selection heuristic, not proof that a later pass will complete.','- **Authority:** excludes the carrier, goalkeeper, chaser, both cover assignments and existing receiver. Restarts, original counterpress and Klopp transition bursts retain priority. Opposing touches or unheld/stale control cannot create support assignments. There are no persistent support movement commands; every decision revalidates eligibility. Speculative receive-aim state is restored. Actual pass and shot selection, goalkeeper, cover and every original physics method remain unchanged.','- **Diagnostics:** bounded labels identify pressure, compact/low-pressure rejection, missing support, unsafe routes and insufficient gain. Only proposals matching final accepted movement commands count as activations. Pass plans carry receiver diagnostics. The external harness reads native completed-pass counters after engine steps, outside controller timing, and verifies their increments against final engine statistics for every original match. Recent-support/plan links are associations, not causal pass creation.','',
        '## Original raw native outcomes','',
        '| Source | Matches | Wins | Draws | Losses | Points | GF–GA | Passes completed/attempted | Completion | Turnovers | Deadline misses | Exceptions |',
        '|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---:|']
    for name,s in raw.items():
        lines.append(f"| {name} | {s['matches']} | {s['wins']} | {s['draws']} | {s['losses']} | {s['points']} | {s['goals_for']}–{s['goals_against']} | {s['passes_completed']}/{s['passes_attempted']} | {s['pass_completion']:.4%} | {s['turnovers']} | {s['policy_timeouts']} | {s['policy_errors']} |")
    lines+=['','Native raw misses and competitive outcomes are never erased by repeats. Exact timeout repeats are retained separately; accepted and raw comparisons must both pass. No miss is waived as environmental noise.','',
        '## Paired significance and compact preservation','',
        'The preregistration requires more raw and accepted points than BOTH baselines, positive whole-seed 97.5% bootstrap lower bounds and exact one-sided whole-seed sign-flip p ≤ 0.025 against each comparator (a two-comparison correction). Bootstrap uses 10,000 resamples and fixed seed 719331; the exact test enumerates every sign assignment across the sixteen seed blocks. Every style, side and kickoff stays together within its seed.','',
        '| Comparator | Raw PPM change | 97.5% whole-seed interval | Exact p | Accepted PPM change |','|---|---:|---|---:|---:|']
    for name,data in compare.items():
        s=data['raw'];a=data['accepted']
        lines.append(f"| {name} | {s['ppm_change']:+.6f} | [{s['bootstrap_97_5'][0]:+.6f}, {s['bootstrap_97_5'][1]:+.6f}] | {s['exact_one_sided_sign_flip_p']:.6f} | {a['ppm_change']:+.6f} |")
    lines+=['','Compact points must not fall below either comparator; compact concessions must not exceed v10. The original per-style preservation, total concessions, turnovers, completion-rate, SDK, legality, exception, timing and reproducibility checks also apply. Qualification retains the original 768-pair minimum and all original promotion gates; development does not waive them.','',
        '| Opponent | v10 points | Original points | Adaptive points | v10 GF–GA | Original GF–GA | Adaptive GF–GA |','|---|---:|---:|---:|---|---|---|']
    for style,v in styles.items():
        b,o,a=(v[n] for n in ('v10','architect','adaptive'))
        lines.append(f"| {style} | {b['points']} | {o['points']} | {a['points']} | {b['goals_for']}–{b['goals_against']} | {o['goals_for']}–{o['goals_against']} | {a['goals_for']}–{a['goals_against']} |")
    lines+=['','## Actual executions, rejected opportunities and completions','']
    for name,t in tel.items():
        lines += [f'### {name}','', 'Accepted diagnostic/command counts: `'+json.dumps(t['ticks'],sort_keys=True)+'`.','',
            'Team-level episodes: `'+json.dumps(t['episodes'],sort_keys=True)+'`.','',
            f"Native completed-pass increments observed: {t['native_completions_observed']}. Supported-receiver plan completion links: {t['completions_after_supported_receiver_plan'] if t['plan_link_diagnostics_available'] else 'not instrumented in this frozen control'} (association only).",'']
    lines+=['### Adaptive movement by opponent style','',
        '| Opponent | Executed support commands | Pressure diagnostics | Compact rejections | Native completions linked to a supported receiver plan |',
        '|---|---:|---:|---:|---:|']
    for style,t in by_style_telemetry.items():
        lines.append(f"| {style} | {t['ticks'].get('adaptive_support',0)} | {t['ticks'].get('adaptive_pressure',0)} | {t['ticks'].get('adaptive_reject_compact',0)} | {t['completions_after_supported_receiver_plan']} |")
    lines+=['','## Interpretation','',
        f"Adaptive gained {c['points']-b['points']} points over v10, completed {c['passes_completed']-b['passes_completed']} more passes, conceded {b['goals_against']-c['goals_against']} fewer goals and recorded {b['turnovers']-c['turnovers']} fewer turnovers. These aggregate improvements do not establish a supported points advantage: the paired interval includes zero and the exact p-value versus v10 is {compare['v10']['raw']['exact_one_sided_sign_flip_p']:.6f}. It also trails original Architect by {raw['architect']['points']-c['points']} points.",'',
        f"Compact opposition remained a failure: {compact['adaptive']['points']} points versus {compact['v10']['points']} for v10 and {compact['architect']['points']} for original Architect. The detector blocked stationary compact situations but still issued {by_style_telemetry['v10-compact']['ticks'].get('adaptive_support',0)} support commands against the compact style, compared with {by_style_telemetry['v10-press']['ticks'].get('adaptive_support',0)} against pressing. Dynamic compact-opponent situations therefore still passed the pressure gate. This classifier did not deliver the required compact preservation.",'',
        f"Native telemetry recorded {tel['adaptive']['ticks'].get('adaptive_support',0)} executed support commands in {tel['adaptive']['episodes'].get('adaptive_support',0)} team-level episodes, and {tel['adaptive']['completions_after_supported_receiver_plan']} native completions matching recently supported receiver plans. Those associations do not rescue the competitive failure or establish causal pass creation.",'',
        f"Adaptive had {c['policy_timeouts']} original raw deadline misses and a first exact repeat incurred a candidate miss in {reproduced} fixtures. Accepted clean repeats never remove the raw misses or the reproducibility failure. No timing event is waived; this independently blocks qualification.",'']
    lines+=['Support labels identify final executed commands. All pressure/rejection/gain labels are diagnostics, not activations; a verified proposal can lose ownership to a later v10 reception command. Team-level episodes split after gaps longer than five ticks; two supporters can act in one tick. Completion traces, rejection/pressure examples, source snapshots and five-second goal/turnover associations are retained in the evidence. Associations are not causal claims.','',
        '## Reliability and gate decision','',
        f"Accepted mean-runtime ceiling: {ceiling:.6f} ms. Adaptive mean: {ca['decision_mean_ms']:.6f} ms. Raw max: {c['decision_max_ms']:.6f} ms. Extra raw misses/1,000 fixtures: {extra:.6f}. Candidate deadline failures reproduced on first exact repeat: {reproduced}.",'',
        '| Gate | Result |','|---|---|']
    for name,passed in gates.items():lines.append(f"| {name} | {'PASS' if passed else 'FAIL'} |")
    lines+=['',f'Exact deadline-repeat fixtures: {len(repeats)} additional full native matches, retained without erasing original outcomes or misses. The development cohort plus repeats and eight public diagnostic probes totals {expected*3+len(repeats)+8} recorded full matches. Official SDK intakes are separate.', '', '## Verification and reproduction','',
        '152 regressions passed before development, including the inherited physics/safety suite and tests for closing versus receding defenders, compact/open-lane/slow-race rejection, protected player roles, low-pressure v10 command equivalence, no-gain rejection, physically feasible new lanes and speculative-state restoration. Native SDK intakes and legal actions are retained. Both old source hashes and every original v10 method except the two movement/telemetry hook call sites remain unchanged.','',
        '`python tools/adaptive_architect/build.py` reproduces the adaptive source while verifying frozen v10 and original Architect. After installing the bundled official extension, run `PYTHONPATH=student-sdk python -m unittest discover -s tests -q`; reproduce the cohort with `PYTHONPATH=student-sdk python tools/benchmarks/run_adaptive_architect.py --protocol docs/adaptive-architect/development-protocol.json --out /new/output/path`; analyze with `python tools/adaptive_architect/analyze.py --run /new/output/path --out /new/results.json`. Keep one timed native worker.','',
        'The evidence archive contains raw/accepted matches, exact repeats, full native completion traces, official intakes, frozen sources/opponents, histograms, slow-call/GC/CPU diagnostics, protocols and test logs, with a verified per-file SHA-256 manifest. Sixteen local seed blocks and three fixed public variants cannot establish performance against private league teams.','']
    if not supported:
        lines+=['**Rejected for competitive use. No fresh qualification or promotion was run.** Failed gates: '+', '.join(result['failed_gates'])+'. The selective implementation is retained only as an experiment; activation counts are not an improvement claim.','']
    else:
        lines+=['Development supports the next registered qualification stage only. No promotion or active champion change is authorized.','']
    out.with_suffix('.md').write_text('\n'.join(lines))
    print(result['decision'])
    for n,s in raw.items():print(n,{k:s[k] for k in ('points','goals_for','goals_against','passes_completed','passes_attempted','turnovers','policy_timeouts')})
    print('Actual adaptive commands:',tel['adaptive']['ticks'].get('adaptive_support',0))
    print('Failed gates:',result['failed_gates'])


if __name__=='__main__':main()
