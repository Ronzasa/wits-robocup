"""Publish auditable metrics from all completed native campaigns, without rerunning games."""
import argparse,ast,csv,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/benchmarks'))
from benchmark import aggregate,candidate_score,points
DOC=ROOT/'docs/titan-11-intelligence'

def read(path):return json.loads(path.read_text())
def rows(path):return [json.loads(s) for s in path.read_text().splitlines()]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def quantile(hist,q):
    n=sum(hist.values());rank=math.ceil(n*q);count=0
    for k,v in sorted((int(k),v) for k,v in hist.items()):
        count+=v
        if count>=rank:return [round(k*.025,6),round((k+1)*.025,6)]

def flags(path):
    cls=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef));result={}
    for n in cls.body:
        if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id.startswith('TI_'):
            result[n.targets[0].id]=ast.literal_eval(n.value)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args()
    if (DOC/'metrics.json').exists():p.error('Do not overwrite published metrics.')
    runs=sorted(x for x in a.work.iterdir() if x.is_dir() and (x/'metadata.json').exists() and (read(x/'metadata.json').get('finished_utc')))
    measurements={};allfixtures=[];sources={};misses=[];total=0
    for run in runs:
        meta=read(run/'metadata.json');hist=read(run/'decision-histograms.json');env={(r['source'],r['fixture_id']):r for r in rows(run/'environment.jsonl')}
        for name,source in meta['protocol']['sources'].items():
            key=run.name+'/'+name;raw=rows(run/'raw'/name/'matches.jsonl');clean=rows(run/'accepted'/name/'matches.jsonl');b=aggregate(raw);c=aggregate(clean)
            assert len(raw)==len(clean);total+=len(raw);rh=hist['histograms'][name];assert sum(rh.values())==b['decisions']
            state={'run':run.name,'name':name,'source':source,'features':flags(ROOT/source['path']),
                'raw':b,'accepted':c,'p99_raw_ms_bin':quantile(rh,.99),'p999_raw_ms_bin':quantile(rh,.999),
                'raw_histogram_count':sum(rh.values()),'by_opponent':{Path(style).parent.name:aggregate([r for r in clean if r['opponent']==style]) for style in sorted({r['opponent'] for r in clean})}}
            for stats in [state['raw'],state['accepted'],*state['by_opponent'].values()]:
                stats['native_goal_per_shot_ratio']=stats['goals_for']/stats['shots'] if stats['shots'] else None
                stats['shot_quality']='Native aggregate does not publish xG; diagnostic goalbound flight and end speed recorded separately.'
            measurements[key]=state;sources[source['path']]=source['sha256']
            for r,s in zip(raw,clean):
                assert r['fixture_id']==s['fixture_id'];slot=r['candidate_slot'];rs=r['result']['stats'][slot];cs=s['result']['stats'][slot]
                base={'stage':run.name,'source':name,'source_sha256':source['sha256'],'opponent':Path(r['opponent']).parent.name,'seed':r['seed'],'side':slot,'own_kickoff':r['candidate_takes_kickoff'],'fixture_id':r['fixture_id']}
                for label,value,st in [('raw',r,rs),('accepted',s,cs)]:
                    gf,ga=candidate_score(value)
                    base.update({label+'_points':points(value),label+'_gf':gf,label+'_ga':ga,label+'_errors':st['policy_errors'],label+'_misses':st['policy_timeouts'],label+'_mean_ms':st['decision_time_ms']['total_ms']/st['decision_time_ms']['count'],label+'_max_ms':st['decision_time_ms']['max_ms']})
                    for field in ('shots','passes_attempted','passes_completed','passes_intercepted','turnovers','possession_ticks','controlled_ticks'):base[label+'_'+field]=st.get(field,0)
                allfixtures.append(base)
                if any(st['policy_timeouts'] for st in r['result']['stats']):
                    misses.append({'stage':run.name,'source':name,'fixture_id':r['fixture_id'],'candidate_raw_misses':rs['policy_timeouts'],'opponent_raw_misses':r['result']['stats'][1-slot]['policy_timeouts'],'candidate_raw_max_ms':rs['decision_time_ms']['max_ms'],'environment':env[name,r['fixture_id']],
                        'cause':'Original per-call CPU/GC trace unavailable; do not attribute this wall-time event to the controller or environment from fixture totals alone.'})
    out={'formal_source_side_fixtures':total,'formal_source_side_decisions':sum(s['raw']['decisions'] for s in measurements.values()),'measurements':measurements,'sources':sources,'all_initial_candidate_raw_misses':sum(m['raw']['policy_timeouts'] for m in measurements.values()),'all_initial_candidate_errors':sum(m['raw']['policy_errors'] for m in measurements.values())}
    (DOC/'metrics.json').write_text(json.dumps(out,indent=2)+'\n');(DOC/'deadline-cases.json').write_text(json.dumps(misses,indent=2)+'\n')
    for name,data in [('per-fixture.csv',allfixtures),('metrics.csv',[{'stage':m['run'],'source':m['name'],'sha256':m['source']['sha256'],**{k:m['accepted'][k] for k in ('matches','wins','draws','losses','points','goals_for','goals_against','shots','passes_attempted','passes_completed','passes_intercepted','passes_uncollected_derived','pass_completion','turnovers','possession_fraction','control_fraction','decision_mean_ms','decision_max_ms')},'raw_misses':m['raw']['policy_timeouts'],'raw_errors':m['raw']['policy_errors'],'p99_low_ms':m['p99_raw_ms_bin'][0],'p99_high_ms':m['p99_raw_ms_bin'][1],'p999_low_ms':m['p999_raw_ms_bin'][0],'p999_high_ms':m['p999_raw_ms_bin'][1]} for m in measurements.values()])]:
        with (DOC/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
    final=read(DOC/'final-gates.json')['titan11'];selection=read(DOC/'final-selection.json');component=read(DOC/'component-selection.json');b=final['accepted']['baseline'];c=final['accepted']['challenger'];fresh=measurements['validation/titan11'];frbase=measurements['validation/v10']
    enabled=selection['active'];disabled={f:component['disabled'].get(f,['removed by integration/search selection']) for f in ('predictive','coordinated','finishing','defence','playbooks','learning') if f not in enabled}
    decision={'recommendation':'ELIGIBLE_FOR_EXPLICIT_APPROVAL' if final['all_gates_pass'] else 'RETAIN_V10_0','active_submission_modified':False,'main_modified':False,'candidate_sha256':digest(ROOT/'experiments/titan-11/team.py'),'frozen_v10_sha256':digest(ROOT/'my-team/team.py'),'enabled':enabled,'disabled':disabled,'failed_gates':[k for k,v in final['flags'].items() if not v],'formal_fixtures':total}
    (DOC/'decision.json').write_text(json.dumps(decision,indent=2)+'\n')
    def table_row(label,stats,m):
        return f"| {label} | {stats['points']} | {stats['wins']}/{stats['draws']}/{stats['losses']} | {stats['goals_for']}–{stats['goals_against']} | {stats['pass_completion']:.2%} | {stats['turnovers']} | {stats['decision_mean_ms']:.4f} | {m['raw']['policy_timeouts']} |"
    text=f'''# TITAN-11 tactical intelligence — independent validation

**{'All promotion gates passed; explicit approval still required.' if final['all_gates_pass'] else 'Retain v10.0: TITAN-11 did not pass every promotion gate.'}** The active `my-team/team.py` remains byte-for-byte v10.0. `main` was never modified. No local result is presented as an online league-ranking gain.

The standalone challenger is [`experiments/titan-11/team.py`](../experiments/titan-11/team.py), SHA-256 `{decision['candidate_sha256']}`. The exact champion is [`champions/v10.0/team.py`](../champions/v10.0/team.py), SHA-256 `{decision['frozen_v10_sha256']}`.

## Fresh competition result

768 paired fixtures, 16 previously untouched independent seed blocks, 12 frozen opponents, both pitch assignments and both kickoff arrangements. Every match ran 2,400 ticks with the unchanged native 20 ms deadline. The candidate and validation protocol were committed before independent play began. Primary football scores use first-clean exact repetitions; every initial raw result and failed repeat is retained and separately reported.

| Controller | Points | W/D/L | Goals for–against | Pass completion | Turnovers | Accepted mean ms | Initial raw misses |
|---|---:|---:|---:|---:|---:|---:|---:|
{table_row('v10.0',b,frbase)}
{table_row('TITAN-11',c,fresh)}

Paired points-per-match difference: **{final['accepted']['points_per_match_difference']:+.6f}**, whole-seed paired bootstrap 95% interval **{final['accepted']['paired_seed_block_bootstrap_95']}**. Raw points: {final['raw']['baseline']['points']} versus {final['raw']['challenger']['points']}; raw paired interval {final['raw']['paired_seed_block_bootstrap_95']}. Additional initial raw deadline misses per 1,000 fixtures: **{final['extra_raw_misses_per_1000']:.6f}**, allowed maximum 2. Zero-policy-exception gate: {final['flags']['zero_policy_exceptions']}.

Raw p99 timing bins: v10 {frbase['p99_raw_ms_bin']} ms; challenger {fresh['p99_raw_ms_bin']} ms. Raw p99.9 bins: v10 {frbase['p999_raw_ms_bin']} ms; challenger {fresh['p999_raw_ms_bin']} ms. Worst initial raw decision: v10 {frbase['raw']['decision_max_ms']:.6f} ms; challenger {fresh['raw']['decision_max_ms']:.6f} ms. Accepted-mean ceiling: {b['decision_mean_ms']*1.35+.04:.6f} ms.

Failed gates: **{', '.join(decision['failed_gates']) or 'none'}**. Final full gate inputs and per-opponent native statistics: [`final-gates.json`](titan-11-intelligence/final-gates.json). No failed cohort was pooled with another cohort to obtain significance, no fresh result was used to tune source, and no timeout was removed from the raw deadline calculation.

## Implemented systems and selection

All six systems have working standalone source variants and native ablations. The final enabled subset is **{', '.join(enabled) or 'none (runtime control only)'}**. Other components remain implemented and disabled; this is intentional rather than deploying every experiment regardless of evidence.

1. **Predictive planning:** original shot/link/wall/carry proposals plus two executable empty-space pass candidates; one baseline leaf plus at most two challenger leaves. Public acceleration, damping, cooldown, friction, actual first-tick carrier contact, receiver commands and opponent interception are reused. Scoring combines progression, retention, recovery support and counter exposure. The beam and action-family proposal retention have deterministic fixed caps.
2. **Five-player coordination:** dynamic two-outlet triangles, role-sensitive depth/width, verified-regain runs, joint pass/support evaluation, third-man runs during a verified pass in flight, rebound follow-up and retained cover. Existing goalkeeper, chaser and verified receiver commands remain protected in target planning. The original flight-inactive version is archived and its separate native result retained.
3. **Finishing:** two executed goalkeeper responses, momentum/cooldown, full-route physical defender checks, additional legal wall direction and two reduced-power trials. The fitted shot signal uses native two-second conversion labels; small calibration groups are poor, so it is not advertised as calibrated xG. Original direction-only and complete power variants are evaluated separately.
4. **Threat defence:** predicted opponent progression and central receiving danger, small deterministic guard assignment, selective extra pressure only after recent dangerous loss, protected primary roles and immediate restoration after regain. This is not a permanent deep formation. The football ablation, rather than geometry alone, decides whether it is enabled.
5. **Playbooks:** independently evaluated legal initial formation, own opening circulation, guarded second pass, abort-on-failed-execution conditions, goalkeeper distribution, restitution-aware wall switch and inherited verified end-wall recovery. Opponent protected-restart targets are not overridden. There is no hidden state, seed-specific tactic or physics change.
6. **Offline learning/self-play:** native-labelled compact linear value fit and logistic conversion signal, an archived champion/style league plus generated legal specialists and parent self-play, and four preregistered derivative-free parameter designs. Trained coefficients are embedded directly. Inference imports only `math` and the official SDK; no file/model reads, network, clocks or external dependency.

The conservative runtime reach bound preserves successful physical witnesses. It never substitutes heuristic ETA for pass feasibility. The ordinary heuristic `_intercept` and original movement/collision/reception mechanics are retained. Official `act` supplies the current public observation to each tactical decision.

Enabled/disabled details:

'''
    for f in ('predictive','coordinated','finishing','defence','playbooks','learning'):
        text+=f"- `{f}`: {'enabled after development ablation/integration selection' if f in enabled else 'disabled — '+', '.join(disabled[f])}.\n"
    text+='''
## Development and feature ablations

The complete initial screen, explicit power/flight refinement screen, all-feature and leave-one-feature-out integrations and finite self-play search are preserved. Development confidence intervals based on only two seed blocks are weak and were not treated as independent promotion evidence. The final cohort has 16 independent blocks. The registrations prohibit carrying an individually rejected component into the release and prohibit tuning on final results.

| Stage/source | Matches | Points | Goals for–against | Raw misses | Accepted mean ms |
|---|---:|---:|---:|---:|---:|
'''
    for key,m in measurements.items():
        if m['run']=='validation':continue
        s=m['accepted'];text+=f"| {key} | {s['matches']} | {s['points']} | {s['goals_for']}–{s['goals_against']} | {m['raw']['policy_timeouts']} | {s['decision_mean_ms']:.4f} |\n"
    text+='''
## Diagnostics, measurement limits and reproducibility

The diagnostic capture, exact model training samples/native results, original source hashes, all raw/first-clean match records, failed repeats, runtime histograms and CPU/wall/cgroup observations are archived with a digest manifest. Instrumented diagnostics and replays are excluded from strength and official latency inference. Original rare wall-time spikes have no per-call CPU/GC trace; repeat evidence alone cannot assign their cause to the environment or controller.

Per-fixture data: [`per-fixture.csv`](titan-11-intelligence/per-fixture.csv). Full aggregate/per-opponent native counters, pass accounting, conversion, possession and control: [`metrics.json`](titan-11-intelligence/metrics.json). Deadline cases: [`deadline-cases.json`](titan-11-intelligence/deadline-cases.json). Exact definitions and proxy limitations: [`measurement-notes.md`](titan-11-intelligence/measurement-notes.md). Model calibration: [`fit-report.json`](titan-11-intelligence/fit-report.json). Native diagnostic replay results are separately archived.

All original regressions and focused subsystem tests are run with the selected candidate. Official intake validates exactly one controller in a single `team.py` and five public seeds at 400 ticks each. Audit output records the exact test count, source hashes and validation result.

From the repository root (Python with the official SDK available):

```sh
python -m unittest discover -s tests -q
ROBOCUP_TEAM_PATH="$PWD/experiments/titan-11/team.py" python -m unittest discover -s tests -q
python tools/benchmarks/run_intelligence.py --protocol docs/titan-11-intelligence/validation-protocol.json --out /workspace/work/titan11-validation-reproduction
python tools/titan11/evaluate.py /workspace/work/titan11-validation-reproduction
python tools/titan11/train.py --traces tests/fixtures/titan-11-native-training-samples.json.gz --out /workspace/work/titan11-fit-reproduction
```

Use a new output directory every time. These reproduction fixtures have already been used and cannot serve as a new independent promotion cohort. `tools/titan11/build.py` can assemble another isolated challenger from explicit feature flags and JSON parameters; `campaign.py` is the archived finite tournament-selection pipeline. Offline fitting alone requires NumPy (`tools/titan11/requirements.txt`). Diagnostic replay generation uses `tools/titan11/replays.py`; decompress `.native.json.gz` losslessly for the SDK replay viewer.
'''
    (ROOT/'docs/titan-11-validation.md').write_text(text)
    print(json.dumps(decision,indent=2))
if __name__=='__main__':main()
