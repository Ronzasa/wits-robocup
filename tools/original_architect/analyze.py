"""Analyze the sealed stage with unchanged source and conservative safety gates."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools/benchmarks'),str(Path(__file__).parent)]
from benchmark import aggregate
from paired_statistics import paired


def read(p):return [json.loads(x) for x in p.read_text().splitlines()]


def render(result):
    stage=result['stage'];protocol=result['protocol'];raw=result['raw_summary'];clean=result['accepted_summary']
    baseline,candidate=raw['v10'],raw['architect']
    interval='bootstrap_97_5' if stage=='development' else 'bootstrap_95'
    lines=['# Unchanged Original Architect — '+stage,'',
        '**Decision: '+result['decision']+'. v10 remains champion.**','',
        f"Frozen sources from 906f7b9; {result['paired_configurations']} paired configurations across {result['seed_blocks']} fresh seed blocks and {len(protocol['opponents'])} styles, both sides and both kickoffs. There are {result['paired_configurations']*2} original full native matches. Every game uses 2400 ticks, engine 0.1.0, configuration 372990895c7eca2a and the native 20 ms deadline. One worker; no policy, SDK, physics or configuration changes.",'',
        '## Original raw outcomes','',
        '| Source | Matches | W–D–L | Points | GF–GA | Completed/attempted passes | Completion | Turnovers | Raw misses | Exceptions |',
        '|---|---:|---|---:|---|---|---:|---:|---:|---:|']
    for name,s in raw.items():lines.append(f"| {name} | {s['matches']} | {s['wins']}–{s['draws']}–{s['losses']} | {s['points']} | {s['goals_for']}–{s['goals_against']} | {s['passes_completed']}/{s['passes_attempted']} | {s['pass_completion']:.4%} | {s['turnovers']} | {s['policy_timeouts']} | {s['policy_errors']} |")
    lines+=['',f"Repeat-selection status: {result['unresolved_selected_rows']} selected rows still contain a timeout after the three-repeat cap. The `accepted/` directory is the retained repeat-selected tier: first clean if available, otherwise the last unresolved attempt. Unresolved rows are diagnostic only and always disqualifying; they are not described as deadline-clean evidence.",'', 'Every original row and miss is retained. Exact timeout repeats take the first clean run regardless of score; they never erase raw outcomes or reliability failures. Both raw and accepted comparisons must pass.','',
        '## Whole-seed statistics','',
        '| Records | PPM change | Selection interval | Exact one-sided p |','|---|---:|---|---:|']
    for label,s in result['statistics'].items():lines.append(f"| {label} | {s['ppm_change']:+.6f} | [{s[interval][0]:+.6f}, {s[interval][1]:+.6f}] | {s['exact_one_sided_sign_flip_p']:.6f} |")
    lines+=['','Balanced integer whole-seed point sums preserve all styles/sides/kickoffs and avoid floating-point zero drift. Development retains the previous 97.5% positive-lower-bound/exact-p ≤ 0.025 criteria, with 10,000 bootstrap resamples, RNG 719331. Qualification requires the original 95% positive lower bound, 5,000 resamples and exact-p ≤ 0.05. Qualification is a separate 16-seed, 12-style, 768-pair cohort; development is never reused as qualification.','',
        '| Opponent | v10 points | Architect points | v10 GF–GA | Architect GF–GA |','|---|---:|---:|---|---|']
    for style,v in result['by_opponent'].items():
        sb,sc=v['v10'],v['architect']
        lines.append(f"| {style} | {sb['points']} | {sc['points']} | {sb['goals_for']}–{sb['goals_against']} | {sc['goals_for']}–{sc['goals_against']} |")
    lines+=['','## Executions and runtime','',
        f"Executed Architect support commands: {result['telemetry']['commands'].get('architect_support',0)}; team-level episodes: {result['telemetry']['episodes'].get('architect_support',0)}. Only matching final commands accepted under 20 ms count. A movement is not proof of a completed pass or a caused goal; the native match metrics establish outcomes.",'',
        f"Accepted mean ms: v10 {clean['v10']['decision_mean_ms']:.6f}, Architect {clean['architect']['decision_mean_ms']:.6f}; ceiling {result['accepted_mean_ceiling_ms']:.6f}. Architect raw max {candidate['decision_max_ms']:.6f}ms. Extra raw misses/1000: {result['extra_raw_misses_per_1000']:.6f}. Additional full exact repeats: {result['timing_repeat_full_matches']}.",'',
        f"First exact repeats with candidate misses: {len(result['first_repeat_candidate_miss_fixtures'])}; same public-input miss recurrence: {result['same_public_input_recurrence_count']}. All raw and repeat calls have the same wall/thread CPU/GC tracing and slow-call public-input hashes. Whole-fixture recurrence does not prove a deterministic code hotspot. Any first-repeat candidate miss still fails the conservative gate; unresolved repeats also disqualify. No miss is waived.",'',
        '## Registered gates','', '| Gate | Result |','|---|---|']
    for k,v in result['gates'].items():lines.append(f"| {k} | {'PASS' if v else 'FAIL'} |")
    lines+=['','## Interpretation','',
        f"Whole-cohort changes: points {candidate['points']-baseline['points']:+d}; goals scored {candidate['goals_for']-baseline['goals_for']:+d}; conceded {candidate['goals_against']-baseline['goals_against']:+d}; completed passes {candidate['passes_completed']-baseline['passes_completed']:+d}; turnovers {candidate['turnovers']-baseline['turnovers']:+d}. Opponent subtotals never replace these totals. Failed gates: {', '.join(result['failed_gates']) or 'none'}.",'',
        'Only a complete development pass authorizes the registered qualification. Even a full qualification pass permits a recommendation, not promotion. Main and the active champion require explicit user approval. Fixed public local opponents cannot prove private league standings.','',
        '## Reproduction','',
        f"`PYTHONPATH=student-sdk python tools/original_architect/run.py --protocol docs/original-architect/{stage}-protocol.json --out /new/run/path`; then `python tools/original_architect/analyze.py --run /new/run/path --out /new/results.json`. Use one timed worker. Frozen sources/opponents, original and repeat matches, SDK intakes, wall/CPU/GC/input traces, per-match histograms and cgroup diagnostics are retained.",'']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();run=args.run.resolve();out=args.out;assert not out.exists()
    meta=json.loads((run/'metadata.json').read_text());assert 'finished_utc' in meta
    protocol=meta['protocol'];stage=protocol['stage'];assert stage in ('development','qualification')
    expected=len(protocol['opponents'])*sum(map(len,protocol['seeds'].values()))*4
    rawrows={n:read(run/'raw'/n/'matches.jsonl') for n in ('v10','architect')}
    cleanrows={n:read(run/'accepted'/n/'matches.jsonl') for n in ('v10','architect')}
    for name,data in rawrows.items():
        assert len(data)==expected
        s=protocol['sources'][name]
        for path in (ROOT/s['path'],run/'sources'/name/'team.py'):assert hashlib.sha256(path.read_bytes()).hexdigest()==s['sha256']
        assert all(r['result']['ticks']==2400 and r['result']['terminal_reason']=='time_limit' for r in data)
    raw={n:aggregate(v) for n,v in rawrows.items()};clean={n:aggregate(v) for n,v in cleanrows.items()}
    stats={label:paired(data['v10'],data['architect'],10000 if stage=='development' else 5000) for label,data in (('raw',rawrows),('accepted',cleanrows))}
    repeats=read(run/'timing-repeats.jsonl');by_id={r['fixture_id']:r for r in rawrows['architect']};recurrences=[]
    for r in repeats:
        if r['source']!='architect' or r['attempt']!=1:continue
        new=r['result'];side=new['candidate_slot'];old=by_id[r['original_fixture_id']]
        if not new['result']['stats'][side].get('policy_timeouts',0):continue
        first=old['architect_evaluation']['candidate_miss_calls'];second=new['architect_evaluation']['candidate_miss_calls']
        same={x['public_input_sha256'] for x in first}&{x['public_input_sha256'] for x in second}
        recurrences.append({'fixture_id':old['fixture_id'],'original_candidate_miss':old['result']['stats'][side].get('policy_timeouts',0)>0,
            'same_tick_public_input_recurrence':bool(same),'original_miss_calls':first,'first_repeat_miss_calls':second})
    commands=Counter();episodes=Counter()
    for r in rawrows['architect']:commands.update(r['architect_evaluation']['ticks']);episodes.update(r['architect_evaluation']['episodes'])
    styles={style:{n:aggregate([r for r in data if Path(r['opponent']).parent.name==style]) for n,data in rawrows.items()} for style in protocol['opponents']}
    baseline,candidate=raw['v10'],raw['architect'];ab,ac=clean['v10'],clean['architect']
    intake=json.loads((run/'architect-validation.json').read_text());extra=(candidate['policy_timeouts']-baseline['policy_timeouts'])*1000/expected;ceiling=ab['decision_mean_ms']*1.35+.04
    malformed=sum(v for k,v in candidate['validation'].items() if k not in ('actions_validated','players_validated','rejected_kicks'))
    interval='bootstrap_97_5' if stage=='development' else 'bootstrap_95';alpha=.025 if stage=='development' else .05;gates={}
    for label,s in stats.items():
        data=raw if label=='raw' else clean
        gates[label+'_more_points']=data['architect']['points']>data['v10']['points']
        gates[label+'_positive_seed_lower']=s[interval][0]>0
        gates[label+'_exact_significance']=s['exact_one_sided_sign_flip_p']<=alpha
    gates.update(zero_policy_exceptions=candidate['policy_errors']==0 and ac['policy_errors']==0,
        no_candidate_timeout_on_first_exact_repeat=not recurrences,
        all_exact_repeats_resolved=all(all(s.get('policy_timeouts',0)==0 for s in r['result']['stats']) for data in cleanrows.values() for r in data),
        raw_deadline_allowance=extra<=2.,accepted_mean_runtime=ac['decision_mean_ms']<=ceiling,
        official_sdk=intake['ok'] and not intake['folder_errors'],legal_actions=malformed==0,
        complete_registered_cohort=all(len(v)==expected for v in (*rawrows.values(),*cleanrows.values())))
    if stage=='development':gates.update(no_style_points_regression=all(v['architect']['points']>=v['v10']['points'] for v in styles.values()),
        more_completed_passes=candidate['passes_completed']>baseline['passes_completed'],no_extra_turnovers=candidate['turnovers']<=baseline['turnovers'],
        five_executed_support_episodes=episodes.get('architect_support',0)>=5)
    else:gates['required_768_fresh_pairs']=expected==768
    passed=all(gates.values());decision=('QUALIFICATION_JUSTIFIED' if stage=='development' else 'QUALIFICATION_PASSED_AWAITING_USER_APPROVAL') if passed else 'RETAIN_V10'
    result={'stage':stage,'decision':decision,'passed':passed,'promotion':False,'protocol':protocol,
        'paired_configurations':expected,'seed_blocks':stats['raw']['seed_blocks'],'raw_summary':raw,'accepted_summary':clean,
        'statistics':stats,'by_opponent':styles,'telemetry':{'commands':dict(commands),'episodes':dict(episodes)},
        'unresolved_selected_rows':sum(any(s.get('policy_timeouts',0) for s in r['result']['stats']) for data in cleanrows.values() for r in data),
        'gates':gates,'failed_gates':[k for k,v in gates.items() if not v],
        'first_repeat_candidate_miss_fixtures':recurrences,'same_public_input_recurrence_count':sum(x['same_tick_public_input_recurrence'] for x in recurrences),
        'extra_raw_misses_per_1000':extra,'accepted_mean_ceiling_ms':ceiling,'timing_repeat_full_matches':len(repeats)}
    out.write_text(json.dumps(result,indent=2)+'\n');out.with_suffix('.md').write_text(render(result))
    print(stage,decision,'v10 points',baseline['points'],'Architect points',candidate['points'],'failed',result['failed_gates'])


if __name__=='__main__':main()
