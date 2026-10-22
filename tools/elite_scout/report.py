"""Publish observed-video findings separately from actual native outcomes."""
from pathlib import Path
from collections import Counter
import hashlib,json,math,zipfile
ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/elite-scout';WORK=Path('/workspace/work/elite-scout-run')
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(s) for s in p.read_text().splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def evidence():
    dest=ROOT/'tests/fixtures/elite-scout-native-evidence.zip';assert not dest.exists();manifest=[]
    with zipfile.ZipFile(dest,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(WORK.rglob('*')):
            if not p.is_file() or p.suffix not in ('.json','.jsonl','.log','.py'):continue
            data=p.read_bytes();name=str(p.relative_to(WORK));z.writestr(name,data)
            manifest.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        z.writestr('evidence-manifest.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for r in manifest:assert hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256']
    return {'path':str(dest.relative_to(ROOT)),'sha256':sha(dest),'bytes':dest.stat().st_size,'files':len(manifest)}

def table(r):
    a=r['trap']['accepted'];b=r['v10']['accepted'];c=a['challenger']
    return [str(a['baseline']['points']),str(b['baseline']['points']),str(c['points']),
            f"{c['goals_for']}–{c['goals_against']}",
            f"{r['trap']['raw']['challenger']['policy_timeouts']}",
            f"{c['decision_mean_ms']:.4f}"]
def timing(stage):
    p=WORK/stage/'decision-histograms.json'
    if not p.exists():return {}
    h=read(p);result={}
    for name,bins in h['histograms'].items():
        vals=sorted((int(k),v) for k,v in bins.items());count=sum(v for _,v in vals);q={}
        for label,frac in (('p95',.95),('p99',.99),('p999',.999)):
            total=0
            for bucket,n in vals:
                total+=n
                if total>=math.ceil(count*frac):q[label]=(bucket+1)*h['bin_width_ms'];break
        result[name]=q
    return result

def main():
    screen=read(DOC/'screen-results.json');confirm=read(DOC/'confirmation-results.json');selection=read(DOC/'final-selection.json');decision=read(DOC/'decision.json')
    archive=evidence();analysis=ROOT/'tests/fixtures/elite-scout-video-analysis.zip'
    raw_count=sum(len(rows(p)) for p in WORK.glob('*/raw/*/matches.jsonl'))
    repeat_count=sum(len(rows(p)) for p in WORK.glob('*/timing-repeats.jsonl'))
    (DOC/'evidence.json').write_text(json.dumps({'native':archive,'video_analysis':{'path':str(analysis.relative_to(ROOT)),'sha256':sha(analysis),'bytes':analysis.stat().st_size},'scheduled_full_matches':raw_count,'exact_full_repeats':repeat_count},indent=2)+'\n')
    lines=['# Replay-led controller validation','',
        '**Decision: '+decision['status']+'. Main, active v10.0 and frozen TITAN-X Trap are unchanged.**','',
        'The footage review is in [replay-analysis.md](replay-analysis.md), with a result table for all ten games and annotated evidence for all 17 visible goals. '
        'The two opponents played one another, so the supplied videos do not measure our controller against them. '
        'Local native tests below evaluate observed tactical ideas against frozen, known local opponents. No result is presented as a match against the actual leaders.','',
        f'The campaign completed **{raw_count:,} scheduled full native matches**, plus **{repeat_count} identical timeout-fixture repeats**. '
        'All matches use 2,400 ticks and the official 20 ms deadline; intake validation uses the SDK public seeds. '
        'Points, goals and pass metrics use the first clean exact run, independent of score; raw points are also shown for qualification. '
        'Raw rows and all repeats are retained separately. Every original deadline miss remains in the reliability gate.','',
        '## Independent screen','',
        'Five variants played 48 matched configurations each, alongside frozen Trap and v10: six styles, two seeds, both sides and both kickoffs. '
        'The keeper cap is the only difference among the three keeper variants. Outlet and cutback variants change only their selected support target.','',
        '| Variant | Trap points | v10 points | Variant points | GF–GA | Raw misses | Mean ms |','|---|---:|---:|---:|---:|---:|---:|']
    if any('positive_ci' in failures for failures in decision.get('failed',{}).values()):
        lines[4:4]=['The selected source improved total points, but the paired confidence intervals included zero. '
                    'It failed the registered positive-lower-bound gate, so retain the existing controllers. '
                    'The experiment remains available for inspection; it is not a promoted champion.','']
    for name,r in screen.items():lines.append('| '+name+' | '+' | '.join(table(r))+' |')
    lines+=['','The cap-10 keeper is excluded by its raw deadline regression. '
            'Independent results justified testing the cap-14 keeper, outlet and cutback, plus their combination, on new configurations. '
            'The outlet screen improved points while conceding more goals: winning matches, rather than pass volume or a single defensive statistic, controls selection.','',
            '## Fresh development confirmation','',
            '128 unused matched configurations per source: eight styles × four seeds × both pitch assignments × both kickoffs. '
            'No source or parameter was changed from this stage’s outcomes.','',
            '| Variant | Trap points | v10 points | Variant points | GF–GA | Raw misses | Mean ms |','|---|---:|---:|---:|---:|---:|---:|']
    for name,r in confirm.items():lines.append('| '+name+' | '+' | '.join(table(r))+' |')
    lines+=['',f"Selected source: `{selection['path']}`; SHA-256 `{selection['sha256']}`. "
            f"Eligible for registered qualification: `{selection['ready_for_qualification']}`.",'']
    selected=confirm[selection['name']]
    lines+=['### Selected-source development matchups','',
            'These development results explain the selection; they are not the untouched qualification result.','',
            '| Opponent | Trap points | v10 points | Selected points |','|---|---:|---:|---:|']
    for name,r in selected['trap']['accepted']['by_opponent'].items():
        v=selected['v10']['accepted']['by_opponent'][name]
        lines.append(f"| {Path(name).parent.name} | {r['baseline']['points']} | {v['baseline']['points']} | {r['challenger']['points']} |")
    lines+=['']
    if (DOC/'qualification-results.json').exists():
        qual=read(DOC/'qualification-results.json');r=qual['trap'];a=r['accepted'];c=a['challenger'];b=a['baseline'];v=qual['v10']['accepted']['baseline'];tails=timing('qualification')
        (DOC/'latency-tails.json').write_text(json.dumps(tails,indent=2)+'\n')
        lines+=['## Frozen fresh qualification','',
            '768 paired configurations per source: 12 styles × 16 unused seed blocks × both sides × both kickoffs. '
            'The source and protocol were committed before these seeds were opened. '
            'Paired confidence intervals use 5,000 whole-seed bootstrap resamples with seed 719331. '
            'Qualification results did not select a different source, change thresholds or extend the cohort.','',
            '| Metric | Frozen Trap | v10.0 | Challenger |','|---|---:|---:|---:|']
        for label,key in [('Points','points'),('Wins','wins'),('Draws','draws'),('Losses','losses'),('Goals for','goals_for'),('Goals against','goals_against'),
                          ('Passes attempted','passes_attempted'),('Passes completed','passes_completed'),('Pass completion','pass_completion'),
                          ('Uncollected passes (derived)','passes_uncollected_derived'),('Turnovers','turnovers'),('Mean decision ms','decision_mean_ms')]:
            values=[b[key],v[key],c[key]];lines.append('| '+label+' | '+' | '.join(f'{x:.6f}' if isinstance(x,float) else str(x) for x in values)+' |')
        for label,key in [('Raw points','points'),('Raw deadline misses','policy_timeouts'),('Raw exceptions','policy_errors'),('Raw max ms','decision_max_ms')]:
            values=[qual['trap']['raw']['baseline'][key],qual['v10']['raw']['baseline'][key],qual['trap']['raw']['challenger'][key]]
            lines.append('| '+label+' | '+' | '.join(f'{x:.4f}' if isinstance(x,float) else str(x) for x in values)+' |')
        for label in ('p95','p99','p999'):
            lines.append('| Raw '+label+' bin upper ms | '+' | '.join(f'{tails[n][label]:.3f}' for n in ('trap','v10','scout'))+' |')
        for base,r in qual.items():
            a=r['accepted'];lines+=['',f"Versus **{base}**: points-per-match delta **{a['points_per_match_difference']:+.6f}**, paired 95% interval **{a['paired_seed_block_bootstrap_95']}**. "
                f"Additional raw misses/1,000: **{r['extra_raw_misses_per_1000']:.6f}**. Reproduced candidate deadline failures: **{r['repeated_timeouts']}**.",'',
                '| Gate | Result |','|---|---|']
            lines += [f"| {key} | {'PASS' if val else 'FAIL'} |" for key,val in r['flags'].items()]
        lines+=['','### Qualification matchups','',
                '| Opponent | Trap points | v10 points | Challenger points |','|---|---:|---:|---:|']
        for name,r in qual['trap']['accepted']['by_opponent'].items():
            vv=qual['v10']['accepted']['by_opponent'][name]
            lines.append(f"| {Path(name).parent.name} | {r['baseline']['points']} | {vv['baseline']['points']} | {r['challenger']['points']} |")
        slow=[x for x in rows(WORK/'qualification/slow-decisions.jsonl') if x['sdk_wall_ms']>=20]
        lines+=['',f"Slow-call diagnostics retain {len(slow)} source-side raw deadline calls across the three sources. "
                f"GC overlaps: {sum(bool(x['gc_overlap']) for x in slow)}; wall-minus-thread-CPU gaps above 5 ms: "
                f"{sum(x['sdk_wall_ms']-x['thread_cpu_ms']>5 for x in slow)}. These observations do not remove raw misses from any gate.",'']
    else:
        lines+=['No qualification seeds were opened because the selected development winner failed the registered eligibility condition. '
                'A development gain is not a promoted controller. The unused cohort remains untouched.','']
    lines+=['## Engineering and reproducibility','',
        'Each controller is a standalone `team.py`, with one controller class, math and official soccer imports only. '
        'Existing shooting, movement physics, strict reception races, first-touch model, defensive-cover and trap helpers retain identical ASTs. '
        'The [function integrity record](function-integrity.json) checks every existing controller method. '
        'The changed targets sit inside the original role/keeper decision process. '
        'Tests include all-off command equivalence, protected receivers, keeper-depth bounds, actual cooldown-aware saving paths, '
        'a real momentum-limited case where the home save must win, support-role preservation and legal actions. '
        'Regression logs in the native archive give the exact test counts.','',
        'The native harness freezes source and opponent hashes, checks SDK intake, rotates source order within each configuration, '
        'runs one serial worker and preserves all raw timing records. Repeats are identical and accepted only as the first clean result, independent of score. '
        'Official engine, config, current submission and frozen sources were not edited. No clock, GC, affinity or deadline control exists inside the controller.','',
        'Reproduce regressions with `python -m unittest discover -s tests -q`. '
        'Build the five initial ablations with `python tools/elite_scout/build.py`. '
        'Replay any frozen native protocol with `python tools/benchmarks/run_elite_scout.py --protocol PATH --out NEW_DIRECTORY` '
        'using the official engine and one timed worker.','',
        f"Native evidence: `{archive['path']}`, SHA-256 `{archive['sha256']}`, {archive['files']} files. "
        'Its CRC and every entry in the SHA-256 manifest were checked. '
        'The video-analysis archive holds detection candidates and analysis scripts; cropped goal evidence is linked from the scouting report. '
        'The original recordings remain outside the repository.','',
        'The `depth14-proxy` opponent tests a known local controller with the observed keeper-depth idea. '
        'It is not either league leader. Improvement in this local opponent set is evidence for a candidate; live league standings are a separate observation.']
    (DOC/'validation.md').write_text('\n'.join(lines)+'\n')
    readme=['# Elite replay study','',
        '- [Ten-game tactical analysis and all goal sequences](replay-analysis.md)',
        '- [Actual native results and recommendation](validation.md)',
        '- [Registered experiment](registration.json)',
        '- [Decision](decision.json)','',
        'Selected experimental controller: [team.py](../../'+selection['path']+').',
        'The active `my-team/team.py` remains unchanged.','']
    (DOC/'README.md').write_text('\n'.join(readme))
    print(json.dumps(decision,indent=2))
if __name__=='__main__':main()
