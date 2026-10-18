"""Publish unchanged-gate repair qualification, including every raw result."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/titan11'))
from evaluate import evaluate
from protocol import digest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True)
    a=p.parse_args();doc=ROOT/'docs/titan-11-repair';run=a.work/'validation'
    assert not (doc/'decision.json').exists()
    gates=json.loads((run/'gate-audit.json').read_text()) if (run/'gate-audit.json').exists() else evaluate(run)
    r=gates['repair'];b=r['accepted']['baseline'];c=r['accepted']['challenger']
    (doc/'final-gates.json').write_text(json.dumps(gates,indent=2)+'\n')
    selection=json.loads((doc/'selection.json').read_text())
    decision={'status':'QUALIFIED_PENDING_REVIEW' if r['all_gates_pass'] else 'RETAIN_V10_0',
        'promoted':False,'active_source':'my-team/team.py',
        'candidate_sha256':selection['candidate_sha256'],'flags':r['flags'],
        'points_delta':c['points']-b['points'],'paired_95_interval':r['accepted']['paired_seed_block_bootstrap_95'],
        'extra_raw_misses_per_1000':r['extra_raw_misses_per_1000'],
        'created_utc':datetime.now(timezone.utc).isoformat()}
    (doc/'decision.json').write_text(json.dumps(decision,indent=2)+'\n')
    # Every file already in the previous feature commit stays byte-for-byte
    # unchanged. A report link in README is the sole permitted old-file edit.
    changed=[]
    for line in subprocess.check_output(['git','ls-tree','-r','947b6c8'],cwd=ROOT,text=True).splitlines():
        info,name=line.split('\t',1)
        if name=='README.md':continue
        path=ROOT/name
        oid=info.split()[2]
        if not path.exists() or subprocess.check_output(['git','hash-object',str(path)],cwd=ROOT,text=True).strip()!=oid:changed.append(name)
    assert not changed,changed
    audit={'preexisting_files_unchanged':True,'preexisting_commit':'947b6c8',
        'active_sha256':digest(ROOT/'my-team/team.py'),
        'original_titan11_sha256':digest(ROOT/'experiments/titan-11/team.py'),
        'candidate_sha256':digest(ROOT/'experiments/titan-11-r/team.py'),
        'fresh_native_configs_per_source':r['accepted']['paired_fixtures'],
        'fresh_seed_blocks':r['accepted']['independent_seed_blocks'],
        'raw_timeout_gate_unchanged':2.,'deadline_ms':20.,
        'frozen_matches_protocol':digest(ROOT/'experiments/titan-11-r/team.py')==r['source']['sha256']}
    assert audit['active_sha256']=='5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6'
    assert audit['frozen_matches_protocol']
    (doc/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    for path in a.work.glob('*regressions.log'):
        (doc/path.name).write_bytes(path.read_bytes())
    stages={}
    for stage in ('development','validation'):
        data=a.work/stage
        meta=json.loads((data/'metadata.json').read_text())
        stages[stage]={}
        for name in meta['sources']:
            stages[stage][name]={kind:json.loads((data/kind/name/'summary.json').read_text()) for kind in ('raw','accepted')}
    (doc/'metrics.json').write_text(json.dumps(stages,indent=2)+'\n')
    failures=[k for k,v in r['flags'].items() if not v]
    def row(label,data):
        raw=data['raw']['all'];q=data['accepted']['all']
        return f"| {label} | {q['matches']} | {q['points']} | {q['wins']}/{q['draws']}/{q['losses']} | {q['goals_for']}–{q['goals_against']} | {100*q['pass_completion']:.2f}% | {q['turnovers']} | {q['decision_mean_ms']:.4f} | {raw['policy_timeouts']} |"
    table='| Version | Matches | Points | W/D/L | Goals for–against | Pass completion | Turnovers | Accepted mean ms | Initial raw misses |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'
    finaltable=table+'\n'.join(row(n,stages['validation'][n]) for n in ('v10','repair'))
    devtable=table+'\n'.join(row(n,stages['development'][n]) for n in ('v10','titan11','runtime','handoff','combined'))
    diagnostic=json.loads((a.work/'repair-reproduction/summary.json').read_text())
    latency=json.loads((a.work/'latency-diagnostics/summary.json').read_text())
    (doc/'latency-diagnostics.json').write_text(json.dumps(latency,indent=2)+'\n')
    latency_max=max(q['max_wall_ms'] for q in latency['cases'])
    latency_cpu_max=max(q['max_cpu_ms'] for q in latency['cases'])
    latency_new_misses=0
    for path in (a.work/'latency-diagnostics').glob('*.json'):
        if path.name=='summary.json':continue
        q=json.loads(path.read_text());slot=q['original_raw_result']['candidate_slot']
        latency_new_misses+=q['new_result']['result']['stats'][slot]['policy_timeouts']
    diagnostic_table='| Fixed replay | Ours–theirs | Slow named passes | Coordinated plans | Intended touches |\n|---|---:|---:|---:|---:|\n'+'\n'.join(
        f"| {q['label']} | {q['score'][0]}–{q['score'][1]} | {q['slow_passes']} | {q['coordinated']} | {q['intended_touches']} |" for q in diagnostic)
    style_table='| Opponent | v10.0 points | Repair points | Difference |\n|---|---:|---:|---:|\n'+'\n'.join(
        f"| {Path(name).parent.name} | {row['baseline']['points']} | {row['challenger']['points']} | {row['challenger']['points']-row['baseline']['points']:+d} |"
        for name,row in r['accepted']['by_opponent'].items())
    text=f'''# TITAN-11 reception and runtime repair

**{'The repair passes every registered local promotion gate and is ready for review. v10.0 remains active pending approval.' if r['all_gates_pass'] else 'Retain v10.0. The repair does not pass every registered promotion gate.'}**

Candidate: [`experiments/titan-11-r/team.py`](../experiments/titan-11-r/team.py), SHA-256 `{selection['candidate_sha256']}`. Active champion: [`my-team/team.py`](../my-team/team.py), SHA-256 `{audit['active_sha256']}`. No change to `main`, the active champion, archived versions, SDK, engine or competition configuration.

## What was fixed

Two old native diagnostic games reproduced approved passes at ticks 1821 and 1865 with actual launch speeds about 10.2 units/s. The planner had physically verified a named recipient, but `act()` required more than 10.5 units/s to establish a reception plan, and cancelled live plans below 9 units/s. Approval and execution disagreed.

The isolated handoff repair removes those speed-only gates for named passes. Every new and continuing plan still needs the original executable receiver rollout, safe first touch and strict full-route opponent race. Changed last touch, expiry, missing recipient or failed verification still cancel it. The kick-selection, shooting, keeper-safeguard and cover functions retain their original source; the resulting on-policy games can differ.

The independent runtime repair defers unused heuristic ETA calculations in `_intercept()` until its original reach tests find no sample. Its answer remains the same, including heuristic fallback, sparse samples and wall paths. It never substitutes heuristic ETA for verified pass feasibility. Exact replay matched 9,600 actions and reception states, avoiding 458,193 of 1,117,152 ETA calls. The patch changes only `_intercept()` and the two named-reception conditions in `act()`; all other method ASTs are identical. See [regression tests](../tests/test_titan11_repair.py), [exact comparison](titan-11-repair/runtime-equivalence.json) and [original failure inspection](titan-11-repair/failure-inspection.json).

### Native reproductions and limits

The two known development matches were replayed with both frozen and repaired controllers. Every repaired slow-pass plan commanded the verified receiver target. Outcomes were mixed:

{diagnostic_table}

Both original uncoordinated slow passes eventually reached their recipients through ordinary movement. The defect is a mismatch between approval and commanded coordination; these cases do **not** prove that the original receiver missed its collection. Repaired play follows different on-policy trajectories, so the two-versus-three pass samples are not a causal completion comparison. Scores did not improve in these two clips. They are excluded from qualification, and no code was changed in response. Full native paired tournaments, rather than these selected clips, determine eligibility.

## Registered development comparison

Four new seed blocks, eight fixed styles, both sides and kickoffs: 128 configurations per version. Runtime-only, handoff-only and combined were frozen before these results. No additional variants were created after observing outcomes.

{devtable}

Selection: **{selection['selected']}**. Runtime-only football matched frozen TITAN-11 on every clean native fixture; combined matched handoff-only. The handoff feature was {'eligible because it improved' if selection['handoff_points_improved_over_frozen_titan11'] else 'excluded because it did not improve'} development points over frozen TITAN-11. Passing a unit test alone did not make it a football improvement. Full selection and reliability checks: [selection.json](titan-11-repair/selection.json).

## New independent qualification

24 previously unused seed blocks, 12 frozen opponents, both pitch assignments and kickoff arrangements: **{r['accepted']['paired_fixtures']} paired configurations, {2*r['accepted']['paired_fixtures']} complete 2,400-tick native matches**. Candidate and protocol were committed before play. This cohort is not pooled with the earlier failed qualification. All opponent styles were previously known; these are fresh seeds, not evidence of new-style generalization.

{finaltable}

Paired points-per-match difference: **{r['accepted']['points_per_match_difference']:+.6f}**. Whole-seed paired bootstrap 95% interval: **{r['accepted']['paired_seed_block_bootstrap_95']}**. Additional initial raw deadline misses per 1,000 fixtures: **{r['extra_raw_misses_per_1000']:.6f}**, original maximum **2**. Failed gates: **{', '.join(failures) if failures else 'none'}**. Full inputs and per-opponent metrics: [final-gates.json](titan-11-repair/final-gates.json), [metrics.json](titan-11-repair/metrics.json).

Initial raw football points, including the actual consequences of failed decisions: **{r['raw']['baseline']['points']} → {r['raw']['challenger']['points']}**; raw paired 95% interval **{r['raw']['paired_seed_block_bootstrap_95']}**. Worst initial raw decision: v10.0 **{r['raw']['baseline']['decision_max_ms']:.3f} ms**, repair **{r['raw']['challenger']['decision_max_ms']:.3f} ms**. First-clean maximum: **{b['decision_max_ms']:.3f} → {c['decision_max_ms']:.3f} ms**. The accepted-mean ceiling is **{b['decision_mean_ms']*1.35+.04:.6f} ms**.

{style_table}

Per-opponent rows are descriptive, with equal weighting in this registered local pool. They are not separate promotion tests or estimates of the opponent frequencies in the school league.

The mean runtime reduction is real in this cohort, but neither previously failed promotion gate is repaired. Native pass completion improved while conceded goals and turnovers increased. Six of twelve styles yielded fewer points, including the direct v10.0 comparison. These mixed outcomes do not establish stronger retention or broad competitive superiority. No fresh result was used to create another variant or expand the registered cohort.

Original gates remain unchanged: positive fresh points difference and paired 95% lower bound, zero policy exceptions, no repeated deadline failure, accepted mean at most baseline×1.35+0.04 ms, at most two additional raw misses per 1,000 fixtures, passing untouched official public-seed intake and valid actions. Initial raw results, exact timing repeats and first-clean football records are all retained. Repeats never erase raw misses. Local results do not establish an online league-ranking gain.

Eight separately instrumented exact repetitions of two new repair timeout fixtures and two new baseline timeout fixtures recorded **{latency_new_misses} new source-side misses**, with a maximum wall time of **{latency_max:.3f} ms** and maximum measured process CPU time of **{latency_cpu_max:.3f} ms**. They record wall/CPU/GC overlap without disabling collection or changing scheduling. These repetitions do not erase any qualification miss or identify the original call's cause. See [latency-diagnostics.json](titan-11-repair/latency-diagnostics.json).

The old 69/127 ms spikes and the new raw spikes remain unexplained: their original per-call CPU/GC traces do not exist. Faster typical computation and a new raw-deadline result cannot prove that arbitrary environmental stalls or the school's historical reliability counter are fixed.

## Reproduction and evidence

123 regressions passed before development and again against the selected source before fresh qualification; both test logs are retained beside this report. The registered development and validation stages contain **2,944 complete native source-side matches and 7,065,600 source-side decisions**. Diagnostic repetitions, public intake and shared-state checks are separate. [audit.json](titan-11-repair/audit.json) verifies the active champion and every pre-existing repository file. [registration.json](titan-11-repair/registration.json) records disjoint cohorts and the finite selection rule.

```sh
ROBOCUP_TEAM_PATH="$PWD/experiments/titan-11-r/team.py" python -m unittest discover -s tests -q
python tools/benchmarks/run_intelligence.py --protocol docs/titan-11-repair/validation-protocol.json --out /workspace/work/titan11-repair-reproduction
python tools/titan11/evaluate.py /workspace/work/titan11-repair-reproduction
```

Use a new directory on every run. Reproducing these fixtures does not create another independent promotion cohort. [native-evidence.zip](titan-11-repair/native-evidence.zip) includes every raw/accepted fixture, timing repeat, environment record, histogram, official intake, source snapshot, test log and diagnostic repair reproduction. Its manifest verifies each entry. The original failed TITAN-11 report and evidence remain unchanged.
'''
    (ROOT/'docs/titan-11-repair-validation.md').write_text(text)
    archive=doc/'native-evidence.zip';assert not archive.exists();entries={}
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for stage in ('development','validation'):
            for path in sorted((a.work/stage).rglob('*')):
                if not path.is_file() or '__pycache__' in path.parts:continue
                data=path.read_bytes();key=str(Path(stage)/path.relative_to(a.work/stage));z.writestr(key,data)
                entries[key]=hashlib.sha256(data).hexdigest()
        for path in sorted(a.work.glob('*.log')):
            data=path.read_bytes();key='logs/'+path.name;z.writestr(key,data);entries[key]=hashlib.sha256(data).hexdigest()
        for dirname in ('repair-reproduction','latency-diagnostics'):
            for path in sorted((a.work/dirname).rglob('*')):
                if not path.is_file() or '__pycache__' in path.parts:continue
                data=path.read_bytes();key=str(Path(dirname)/path.relative_to(a.work/dirname));z.writestr(key,data);entries[key]=hashlib.sha256(data).hexdigest()
        z.writestr('manifest.json',json.dumps(entries,indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(k)).hexdigest()==v for k,v in entries.items())
    (doc/'archive-audit.json').write_text(json.dumps({'sha256':digest(archive),'bytes':archive.stat().st_size,'entries':len(entries),'manifest_verified':True},indent=2)+'\n')
    print(json.dumps(decision,indent=2))


if __name__=='__main__':main()
