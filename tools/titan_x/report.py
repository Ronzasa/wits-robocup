"""Render actual registered outcomes and package all native evidence."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/tactics'
WORK=Path('/workspace/work/titan-x-run')

def read(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def same_games(folder,name):
    def rows(path):
        return {r['fixture_id']:r for r in map(json.loads,path.read_text().splitlines())}
    a=rows(folder/'raw/v10/matches.jsonl');b=rows(folder/'raw'/name/'matches.jsonl')
    def gameplay(row):
        return {'score':row['result']['score'],'stats':[{k:v for k,v in q.items()
            if k not in ('decision_time_ms','validation')} for q in row['result']['stats']]}
    return {'identical':sum(gameplay(a[k])==gameplay(v) for k,v in b.items()),'total':len(b)}

def slow_analysis(folder):
    rows=[json.loads(s) for s in (folder/'slow-decisions.jsonl').read_text().splitlines()]
    deadlines=[r for r in rows if r['sdk_wall_ms']>=20.]
    return {'raw_deadline_calls':deadlines,
            'gc_overlap_count':sum(bool(r['gc_overlap']) for r in deadlines),
            'wall_cpu_gap_over_5ms':sum(r['sdk_wall_ms']-r['thread_cpu_ms']>5. for r in deadlines),
            'misses_by_source':dict(Counter(r['source'] for r in deadlines))}

def archive():
    dest=ROOT/'tests/fixtures/titan-x-native-evidence.zip'
    assert not dest.exists()
    manifest=[]
    with zipfile.ZipFile(dest,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(WORK.rglob('*')):
            if not p.is_file() or p.suffix not in ('.json','.jsonl','.log','.py','.rep'):
                continue
            name=str(p.relative_to(WORK))
            data=p.read_bytes()
            manifest.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
            z.writestr(name,data)
        z.writestr('evidence-manifest.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for row in manifest:
            assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
    result={'path':str(dest.relative_to(ROOT)),'sha256':sha(dest),'bytes':dest.stat().st_size,'files':len(manifest)}
    (DOC/'evidence.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def main():
    q=read(DOC/'qualification-results.json');decision=read(DOC/'decision.json');selection=read(DOC/'selection.json')
    consistency={n:{stage:same_games(WORK/('targeted-'+n if stage=='targeted' else 'development'),n)
                    for stage in ('targeted','development')} for n in ('power','trap','pinball','ambush')}
    timing=slow_analysis(WORK/'qualification')
    (DOC/'gameplay-consistency.json').write_text(json.dumps(consistency,indent=2)+'\n')
    (DOC/'timing-analysis.json').write_text(json.dumps(timing,indent=2)+'\n')
    evidence=archive()
    lines=['# TITAN-X validation — four special-tactic experiments','',
           '**Decision: '+decision['status']+'. The active v10.0 champion and main are unchanged.**','',
           'The four tactics were implemented as independently switchable additions to the frozen Guardiola/Klopp controller. '
           'All four flags are false in the initial manager. Four standalone one-flag sources, bounded physics checks, '
           '120 regressions, targeted native tests, an independent common development set, and a frozen 768-pair qualification were completed.','',
           '## Independent targeted native tests','',
           'Each tactic played 16 complete fixtures, paired with v10, against its two registered relevant styles. '
           'Both pitch assignments and both kickoff arrangements were included. No match was shortened or initialized with a fabricated late-game score.','',
           '| Tactic | v10 points | Tactic points | v10 GF–GA | Tactic GF–GA | Actual command episodes |',
           '|---|---:|---:|---:|---:|---|']
    for n in ('power','trap','pinball','ambush'):
        r=read(DOC/('targeted-'+n+'-results.json'));b,c=r['baseline'],r['challenger']
        lines.append(f"| {n} | {b['points']} | {c['points']} | {b['goals_for']}–{b['goals_against']} | {c['goals_for']}–{c['goals_against']} | {r['tactics']['episodes']} |")
    lines+=['','## Independent common development set','',
            'Each one-flag candidate played the identical 96 configurations: six fixed styles × four development seeds × both sides × both kickoffs. '
            'One shared v10 result per configuration was paired with each candidate. Source order rotated in one serial worker. '
            'No threshold or flag was tuned from these outcomes.','',
            '| Tactic | v10 points | Tactic points | Paired PPM change [95% seed interval] | GF–GA | Raw misses v10 / tactic | Episodes |',
            '|---|---:|---:|---|---:|---:|---|']
    for n in ('power','trap','pinball','ambush'):
        r=read(DOC/('development-'+n+'-results.json'));b,c=r['baseline'],r['challenger']
        ci=r['paired_seed_block_bootstrap_95']
        lines.append(f"| {n} | {b['points']} | {c['points']} | {r['points_per_match_difference']:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}] | {c['goals_for']}–{c['goals_against']} | {r['raw_baseline']['policy_timeouts']} / {r['raw_challenger']['policy_timeouts']} | {r['tactics']['episodes']} |")
    lines+=['',f"Selection: **{selection['selected']}**. Independently promising tactics: `{selection['promising_independent_tactics']}`. "
             f"Integration justified: `{selection['integration_justified']}`. Best-failure qualification only: `{selection['best_failure_only']}`.",
            '','Inactive tactics are not carried forward merely for passing unit tests. The selection file states the preregistered rule and exact source hash. '
            'If development produced no supported tactic, the strongest failed standalone still underwent the requested fresh qualification; it was not silently declared a new champion.','',
            '## Frozen fresh qualification','',
            '768 matched configurations per source: 12 fixed styles × 16 fresh seed blocks × both sides × both kickoffs, '
            '2,400 ticks each under the original native 20 ms deadline. Whole-seed bootstrap uses 5,000 resamples, fixed bootstrap seed 719331. '
            'Qualification outcomes were not used to change the source, choose flags, or extend the cohort.','',
            '| Metric | v10.0 | Selected TITAN-X |','|---|---:|---:|']
    for label,key in [('Points','points'),('Wins','wins'),('Draws','draws'),('Losses','losses'),('Goals scored','goals_for'),
                      ('Goals conceded','goals_against'),('Passes attempted','passes_attempted'),('Passes completed','passes_completed'),
                      ('Pass completion','pass_completion'),('Uncollected passes (derived)','passes_uncollected_derived'),
                      ('Turnovers','turnovers'),('Accepted mean ms','decision_mean_ms')]:
        b,c=q['baseline'][key],q['challenger'][key]
        lines.append(f'| {label} | {b:.6f} | {c:.6f} |' if isinstance(b,float) else f'| {label} | {b} | {c} |')
    for label,key in [('Raw deadline misses','policy_timeouts'),('Raw policy exceptions','policy_errors'),('Raw maximum ms','decision_max_ms')]:
        lines.append(f"| {label} | {q['raw_baseline'][key]} | {q['raw_challenger'][key]} |")
    lines+=['',f"Paired points-per-match change **{q['points_per_match_difference']:+.6f}**, 95% interval **{q['paired_seed_block_bootstrap_95']}**.",
            f"Extra raw misses per 1,000 fixtures: **{q['extra_raw_misses_per_1000']:.6f}** (maximum 2). "
            f"Accepted mean ceiling: **{q['mean_runtime_ceiling_ms']:.6f} ms** (v10 × 1.35 + 0.04 ms).",'',
            '| Gate | Result |','|---|---|']
    lines += [f"| {key} | {'PASS' if value else 'FAIL'} |" for key,value in q['gates'].items()]
    lines+=['','## Qualification matchups','',
            '| Opponent | v10 points | TITAN-X points | PPM change |','|---|---:|---:|---:|']
    for name,r in q['by_opponent'].items():
        lines.append(f"| {Path(name).parent.name} | {r['baseline']['points']} | {r['challenger']['points']} | {r['points_per_match_difference']:+.4f} |")
    lines+=['','## Mechanical verification and timing','',
            'Focused regressions cover power eligibility, recovery and cooldown; observed keeper commitment; successful trap passing; '
            'post-side-wall collection; full-route cooldown body blocks and teammate interference; unreachable and moving receivers; '
            'cooldown challenge success/cancellation; bounded legal commands; unchanged champion hash; unchanged physics/shooting/keeper/cover ASTs; '
            'and all-off action/plan equivalence. The original 95 regressions also pass. All official five-public-seed intake records are retained.','',
            f"Raw deadline diagnostics: {len(timing['raw_deadline_calls'])} candidate-side misses across both sources; "
            f"{timing['gc_overlap_count']} overlap a GC callback; {timing['wall_cpu_gap_over_5ms']} show a wall-minus-thread-CPU gap above 5 ms. "
            'External observers do not replace SDK timings. No raw miss is waived as environmental noise. The archive includes exact-repeat rows, '
            'slow calls, raw timing histograms and cgroup deltas. Reproducible candidate deadline failures: '
            f"{q['repeated_candidate_deadline_failures']}.",'',
            'Telemetry counts accepted commands under 20 ms, grouped into episodes. A run/challenge is not proof of collection. '
            'Goals and turnovers within five seconds of commands are associations, not causal goals-created estimates. '
            'Game-level engine outcomes and matched v10 comparisons are the performance evidence. Inactive tactics have no claimed incremental opportunities.','',
            '## Reproduction and retained evidence','',
            '`python -m unittest discover -s tests -q` runs regressions. `python tools/titan_x/build.py` reproduces the five initial standalone sources '
            'from frozen v10 and the fragment. Each protocol freezes exact source/opponent hashes before play. '
            '`python tools/benchmarks/run_titan_x.py --protocol docs/tactics/qualification-protocol.json --out /new/output/path` replays qualification '
            'in a fresh directory with the official engine installed. Run only one timed native worker.','',
            f"Full native evidence: `{evidence['path']}`, {evidence['bytes']:,} bytes, {evidence['files']} files; SHA-256 `{evidence['sha256']}`. "
            'Every archived file has a SHA-256 entry in `evidence-manifest.json`; archive CRC and each entry were verified. '
            'All original raw results, first-clean exact repeats, validations, source snapshots, opponents, metadata and stage logs are preserved.','',
            'These are local fixed-opponent tests, not access to private league sources or proof of standings improvement. '
            'No main, active submission, champion, SDK, engine or competition configuration file was changed.']
    (DOC/'titan-x-validation.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(decision,indent=2))

if __name__=='__main__':
    main()
