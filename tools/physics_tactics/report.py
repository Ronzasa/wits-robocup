"""Publish raw native results, execution evidence and all rejection gates."""
import argparse,hashlib,json,math,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/physics-tactics'


def read(path):return json.loads(path.read_text())
def rows(path):return [json.loads(s) for s in path.read_text().splitlines()]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def fmt(x):return f'{x:.6f}' if isinstance(x,float) else str(x)


def archive(work):
    path=ROOT/'tests/fixtures/physics-tactics-native-evidence.zip'
    files={str(p.relative_to(work)):p for p in work.rglob('*')
           if p.is_file() and p.suffix in ('.json','.jsonl','.py','.log')}
    if not path.exists():
        manifest=[]
        with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED) as z:
            for name,p in sorted(files.items()):
                data=p.read_bytes();z.writestr(name,data)
                manifest.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
            z.writestr('evidence-manifest.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('evidence-manifest.json'))
        assert set(z.namelist())=={r['path'] for r in manifest}|{'evidence-manifest.json'}
        assert set(files)=={r['path'] for r in manifest},'Evidence changed; preserve the existing archive.'
        for r in manifest:
            data=z.read(r['path'])
            assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
            assert data==files[r['path']].read_bytes(),'Never overwrite an earlier evidence archive.'
    return {'path':str(path.relative_to(ROOT)),'sha256':sha(path),'bytes':path.stat().st_size,'files':len(manifest)}


def tails(work):
    h=read(work/'qualification/decision-histograms.json');result={}
    for name,bins in h['histograms'].items():
        bins=sorted((int(k),v) for k,v in bins.items());n=sum(v for _,v in bins)
        q={}
        for label,fraction in (('p95',.95),('p99',.99),('p999',.999)):
            total=0
            for index,count in bins:
                total+=count
                if total>=math.ceil(n*fraction):q[label]=(index+1)*h['bin_width_ms'];break
        result[name]=q
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True)
    args=p.parse_args();work=args.work.resolve()
    reg=read(DOC/'registration.json');dev=read(DOC/'development-results.json')
    qual=read(DOC/'qualification-results.json');decision=read(DOC/'decision.json')
    protocol=read(DOC/'qualification-protocol.json')
    for name,s in protocol['sources'].items():assert sha(ROOT/s['path'])==s['sha256']
    assert sha(ROOT/reg['active']['path'])==reg['active']['sha256']
    assert sha(ROOT/reg['baseline']['path'])==reg['baseline']['sha256']
    evidence=archive(work);latency=tails(work)
    (DOC/'latency-tails.json').write_text(json.dumps(latency,indent=2)+'\n')
    count=sum(len(rows(path)) for path in work.glob('*/raw/*/matches.jsonl'))
    repeats=sum(len(rows(path)) for path in work.glob('*/timing-repeats.jsonl'))
    fixtures=[{'path':str(path.relative_to(ROOT)),'sha256':sha(path),'bytes':path.stat().st_size}
              for path in sorted((ROOT/'tests/fixtures').glob('physics-*.json'))]
    (DOC/'evidence.json').write_text(json.dumps({'native':evidence,'scheduled_full_matches':count,
        'exact_timeout_fixture_repeats':repeats,'physics_and_execution_fixtures':fixtures},indent=2)+'\n')
    lines=['# TITAN Physics Tactics: actual results','',
      '**Experimental branch only. Main and the active Elite Replay Cutback champion are unchanged.**','',
      'All three tactics were implemented independently from frozen v10. No combinations were tested or deployed. '
      'The decision is governed by raw native match points, statistical significance, actual executions and reliability. '
      'A theoretical forecast, successful first touch or higher mean score alone cannot qualify a tactic.','',
      '## Qualification decision','',
      '| Tactic | Qualified against frozen v10 | Failed gates |','|---|---|---|']
    if not any(d['qualified'] for d in decision['decisions'].values()):
        lines[4:4]=['**Recommendation: keep the active Cutback champion. All three physics tactics are rejected for deployment.** '
                    'Ambush did not show a significant points gain and exceeded the deadline limit; Wall-Brake lost points; '
                    'Rebound Shot did not change points and failed reliability. The active reference earned 1,553 points in this fresh comparison.','']
    for name,d in decision['decisions'].items():
        lines.append(f"| {name} | {'YES, experiment only' if d['qualified'] else 'NO'} | {', '.join(d['failed']) or 'none'} |")
    lines+=['','Passing these gates would qualify an experiment against v10, not authorize replacing the current champion. '
            'The active Cutback reference is reported separately below.','',
      f'The campaign completed **{count:,} scheduled full native matches**, plus **{repeats} identical timeout-fixture repeats**. '
      'Legal native physics fixtures and diagnostic execution replays are separate; they are not pooled into league points.','',
      '## Development and single revision','',
      '64 matched configurations per source, with two fresh seeds, eight frozen styles, both pitch assignments and both kickoff arrangements. '
      'These are the original R0 development sources. The final R1 sources are evaluated on untouched qualification seeds.','',
      '| Tactic | v10 points | Active points | R0 points | GF–GA | Raw misses |','|---|---:|---:|---:|---:|---:|']
    for name,comp in dev.items():
        r=comp['v10'];b=r['challenger']
        lines.append(f"| {name} | {r['baseline']['points']} | {comp['active']['baseline']['points']} | {b['points']} | {b['goals_for']}–{b['goals_against']} | {b['policy_timeouts']} |")
    lines+=['','The [development review](development-review.md) records the native failures, bounded revision and their regressions. '
      'The [revision manifest](revision.json) preserves original and final source hashes. '
      'No qualification result selected another implementation, changed a threshold, added seeds or extended the cohort.','',
      '## Frozen fresh qualification','',
      '768 matched configurations per source: 12 styles × 16 unused seed blocks × both sides × both kickoff arrangements. '
      'All sources and the protocol were committed before this cohort was opened. Each fixture uses the stock native engine, '
      '2,400 ticks and the official 20 ms deadline, with one timed worker and rotating source order.','',
      '**All points, goals, pass metrics and deadline counts below are raw native results.** '
      'Exact clean repeats diagnose interrupted fixtures and do not replace raw outcomes in any gate.','']
    stats={'v10':qual['ambush']['v10']['baseline'],'active':qual['ambush']['active']['baseline'],
           **{name:comp['v10']['challenger'] for name,comp in qual.items()}}
    names=list(stats)
    lines+=['| Metric | '+' | '.join(names)+' |','|---|'+'---:|'*len(names)]
    for label,key in [('Points','points'),('Wins','wins'),('Draws','draws'),('Losses','losses'),
        ('Goals scored','goals_for'),('Goals conceded','goals_against'),('Passes attempted','passes_attempted'),
        ('Passes completed','passes_completed'),('Pass completion fraction','pass_completion'),
        ('Uncollected passes, derived','passes_uncollected_derived'),('Turnovers','turnovers'),
        ('Policy exceptions','policy_errors'),('Raw deadline misses','policy_timeouts'),
        ('Mean decision ms','decision_mean_ms'),('Maximum decision ms','decision_max_ms')]:
        lines.append('| '+label+' | '+' | '.join(fmt(stats[n][key]) for n in names)+' |')
    for q in ('p95','p99','p999'):
        lines.append('| Raw '+q+' bin upper ms | '+' | '.join(f'{latency[n][q]:.3f}' for n in names)+' |')
    lines+=['','### Actual tactic executions','',
      'Counts below come from raw native observations. Plans and movement commands are reported separately from native wall contacts and receptions. '
      'A post-wall contact is a real first touch; immediate controlled possession is a separate measurement. '
      'A kick reception can immediately send the ball onward. Wall-Brake collection requires the named receiver; a passer re-kick does not count. '
      'A rebound-shot goal requires a confirmed native kick, verified native wall reflection and an uninterrupted goal by that shooter.','',
      '| Tactic | Plans | Ambush movement steps | Native launch kicks | Native bounces | Post-wall contacts | Immediate control | Rebound-shot goals | Open at whistle |',
      '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,comp in qual.items():
        c=comp['v10']['tactic_counts']
        suffixes=['plans','native_movement_steps','native_kicks','native_bounces','postwall_contacts','controlled_receptions','rebound_goals']
        values=[]
        for s in suffixes:
            applicable=(s!='native_movement_steps' or name=='ambush') and (s!='native_kicks' or name!='ambush')
            applicable=applicable and (s!='rebound_goals' or name=='rebound-shot')
            applicable=applicable and (s not in ('postwall_contacts','controlled_receptions') or name!='rebound-shot')
            values.append(str(c.get(name+'_'+s,0)) if applicable else '—')
        values.append(str(sum(r['physics_tactics']['open_at_end'] for r in rows(work/'qualification/raw'/name/'matches.jsonl'))))
        lines.append('| '+name+' | '+' | '.join(values)+' |')
    lines+=['','Complete execution counters, including interrupted or uncollected episodes, remain in the qualification result JSON and raw archive. '
      'Native goal/concession totals measure the whole independently modified controller; they are not all attributed to a single tactical episode.','',
      '### Paired significance and reliability','',
      'Ordinary paired 95% intervals use the unchanged comparison tool. The registered familywise test uses 20,000 whole-seed bootstrap resamples '
      'and a 98.333333% two-sided Bonferroni interval for the three comparisons against v10. Its lower bound must be strictly positive. '
      'This describes variation across local seeds against fixed opponents, not a probability of winning the school league.','']
    for name,comp in qual.items():
        r=comp['v10'];other=comp['active']
        lines += [f'#### {name}','',
          f"Versus v10: points per match delta **{r['points_per_match_difference']:+.6f}**, ordinary 95% interval **{r['paired_seed_block_bootstrap_95']}**, "
          f"familywise interval **{r['bonferroni98_333333_interval']}**. "
          f"Additional raw misses/1,000: **{r['extra_raw_misses_per_1000']:+.6f}**. Own deadline failures on exact repeats: **{r['reproduced_own_deadlines']}**.",'',
          f"Versus active Cutback, context only: points per match delta **{other['points_per_match_difference']:+.6f}**, "
          f"ordinary 95% interval **{other['paired_seed_block_bootstrap_95']}**.",'',
          '| Registered gate vs v10 | Result |','|---|---|']
        lines += [f"| {k} | {'PASS' if v else 'FAIL'} |" for k,v in r['gates'].items()]
        lines+=['']
    lines+=['### Opponent breakdown','',
      '| Opponent | v10 points | Active points | Ambush | Wall-Brake | Rebound Shot |','|---|---:|---:|---:|---:|---:|']
    for path,r in qual['ambush']['v10']['by_opponent'].items():
        values=[r['baseline']['points'],qual['ambush']['active']['by_opponent'][path]['baseline']['points']]
        values += [qual[n]['v10']['by_opponent'][path]['challenger']['points'] for n in ('ambush','wall-brake','rebound-shot')]
        lines.append('| '+Path(path).parent.name+' | '+' | '.join(map(str,values))+' |')
    slow=[r for r in rows(work/'qualification/slow-decisions.jsonl') if r['sdk_wall_ms']>=20.]
    lines += ['',f"There were {len(slow)} source-side raw deadline calls in the slow-call log; "
      f"{sum(bool(r['gc_overlap']) for r in slow)} overlapped a recorded GC event and "
      f"{sum(r['sdk_wall_ms']-r['thread_cpu_ms']>5 for r in slow)} had a wall-minus-thread-CPU gap above 5 ms. "
      'These observations do not remove any deadline miss from a gate.','',
      '## Physics and execution evidence','',
      'The native flight fixture uses legal formations and normal player commands with the stock configuration. '
      'Upper/lower side walls, an oblique rebound and an end-wall rebound each provide 81 native position/velocity samples. '
      'The maximum forecast error is below 0.00002 units. No native state, friction, restitution, engine or configuration is injected or edited.','',
      'The development execution records include the first clean Ambush collection and the first failed Wall-Brake attempt. '
      'They reproduce their original scores with zero exceptions and deadline misses. The failed Wall-Brake case is evidence of passer interference, '
      'not a successful reception. Diagnostic R1 replays, when present, remain separate from qualification points.','',
      'The [fresh R1 execution records](../../tests/fixtures/physics-qualification-executions.json) replay the first clean native success for each tactic. '
      'All three reproduced their original scores with zero exceptions and deadline misses. '
      'The unfinished rebound-shot episode began with 21 ticks left in the match and is reported as open at the whistle, not a goal.','',
      'Original v10 movement, interception, receiver rollout, shot/bank geometry, goalkeeper and cover functions are reused. '
      'Two optional captures expose existing path velocities and the already-computed post-kick player state; default physics outputs are unchanged. '
      'The all-off build preserves v10 commands on real native observations. Regression fixtures cover strict opponent races, '
      'protected roles, wall exits, slow reception, a real exact-bounce state, redundant chase suppression, safe-shot feasibility and identical contact arithmetic. '
      'All 112 final regressions passed before source freeze. Their exact logs are retained in the native archive.','',
      '## Reproduction','',
      '`python -m unittest discover -s tests -q` runs the regressions. '
      '`python tools/physics_tactics/build.py` rebuilds the isolated source files from frozen v10. '
      'Run a frozen protocol into a new directory with '
      '`python tools/benchmarks/run_physics_tactics.py --protocol PATH --out NEW_DIRECTORY`. '
      'Use one timed worker and the bundled stock engine. Never overwrite old runs.','',
      f"Native archive: `{evidence['path']}`, {evidence['bytes']:,} bytes, SHA-256 `{evidence['sha256']}`. "
      'Its CRC, exact file list and every manifest SHA-256 were verified against the preserved original files. '
      'Fixture hashes are in [evidence.json](evidence.json).','',
      'The depth14 proxy is a known local controller testing an observed keeper-position idea. '
      'No source or result is represented as either actual league leader. The active champion, existing champion archives, SDK and competition configuration remain unchanged.']
    (DOC/'results.md').write_text('\n'.join(lines)+'\n')
    index=['# TITAN Physics Tactics','',
      '**Experimental only. Main and the active champion are unchanged.**','',
      '- [Actual points, native executions, confidence intervals and all gates](results.md)',
      '- [Registered experiment](registration.json)',
      '- [Development review and bounded revision](development-review.md)',
      '- [Final decision](decision.json)','',
      '| Independent controller | File |','|---|---|',
      '| Rebound Ambush — priority | [team.py](../../experiments/physics-ambush/team.py) |',
      '| Wall-Brake Pass | [team.py](../../experiments/physics-wall-brake/team.py) |',
      '| Precision Rebound Shot | [team.py](../../experiments/physics-rebound-shot/team.py) |','',
      'Each source is a complete single-file controller. None replaces `my-team/team.py`.','']
    if not any(d['qualified'] for d in decision['decisions'].values()):
        index[4:4]=['**All three failed the registered qualification gates. Keep the current active champion.**','']
    (DOC/'README.md').write_text('\n'.join(index))
    print(json.dumps(decision,indent=2))


if __name__=='__main__':main()
