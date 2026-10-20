"""Freeze a fresh three-way development cohort; never extend after outcomes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import random

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/adaptive-architect'


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def integers(v):
    if type(v) is int:yield v
    elif isinstance(v,dict):
        for q in v.values():yield from integers(q)
    elif isinstance(v,list):
        for q in v:yield from integers(q)


def main():
    assert not (DOC/'registration.json').exists()
    excluded=set(range(1000,1010));audit=[]
    for root in (Path('/workspace/wits-robocup/docs'),Path('/workspace/work'),Path('/workspace/titan')):
        for p in sorted(root.rglob('*.json')):
            if p.stat().st_size>4_000_000 or not any(s in p.name for s in ('protocol','registration','registry')):continue
            try:excluded.update(integers(json.loads(p.read_text())))
            except (ValueError,UnicodeDecodeError):continue
            audit.append({'path':str(p),'sha256':digest(p)})
    rng=random.Random(202610201705);seeds=[]
    while len(seeds)<32:
        n=rng.randrange(10_000_000,2_000_000_000)
        if n not in excluded and n not in seeds:seeds.append(n)
    old=json.loads((ROOT/'docs/titan-v11/development-protocol.json').read_text())
    sources={name:{'path':path,'sha256':digest(ROOT/path)} for name,path in {
        'v10':'my-team/team.py','architect':'experiments/titan-v11-architect/team.py',
        'adaptive':'experiments/titan-adaptive-architect/team.py'}.items()}
    rules={
      'development':'16 unused whole-seed blocks x3 frozen strong styles xboth sides xboth kickoffs =192 matched configurations; three separate sources =576 full native matches. No source/threshold tuning or cohort extension from these outcomes.',
      'statistics':'Adaptive must beat BOTH v10 and original Architect on raw AND accepted points, with positive 97.5% whole-seed bootstrap lower bound (10000 resamples, RNG719331) and exact one-sided whole-seed sign-flip p<=0.025 for each comparator. This preserves the previous two-comparison conservative significance threshold.',
      'compact':'No raw points regression against compact relative to either comparator; no extra compact goals conceded versus frozen v10.',
      'preservation':'No raw points regression against any style relative to v10. Adaptive raw overall goals conceded and turnovers <=v10, pass completion rate >=v10, with >=5 actual adaptive-support episodes.',
      'safety':'All original official-SDK, legal-action, zero-exception, no-reproducible-candidate-timeout gates. Extra raw deadline misses/1000 <=2; accepted mean <=v10*1.35+.04ms. Stock 20ms deadline,2400 ticks,one worker; preserve every original raw row and exact timeout repeat. No GC/affinity/physics/configuration controls.',
      'qualification':'Only if every development gate passes. Freeze candidate and run reserved16 unused qualification blocks x12 frozen styles xboth sides xboth kickoffs=768 pairs against v10. Preserve every original qualification gate. Never change main or active champion or promote without explicit approval.',
      'telemetry':'Accepted matching final movement commands identify executions. Pressure/rejection labels are diagnostics, not executions. Live native passes_completed counters identify actual completions; plan/recent-support links are associations, never causal goals/passes created. Telemetry does not affect policy decisions.'}
    reg={'project':'Adaptive Passing Lane Architect','base_commit':'906f7b9bb790707700c8e69e960d1e13f1b95911',
        'created_utc':datetime.now(timezone.utc).isoformat(),'sources':sources,'development':seeds[:16],
        'qualification_reserved':seeds[16:],'styles':['v10-press','v10-compact','v10-counter'],
        'qualification_styles':json.loads((ROOT/'docs/titan-v11/registration.json').read_text())['qualification_styles'],
        'excluded_values_sha256':hashlib.sha256(json.dumps(sorted(excluded)).encode()).hexdigest(),
        'excluded_sources':audit,'rules':rules,'original_promotion_gates':old['gates'],
        'disabled':['COUNTERATTACK_FIREWALL','KEEPER_POWER_PLAY','GOALKEEPER_TRAP','PINBALL_SLINGSHOT','COOLDOWN_AMBUSH']}
    p={k:old[k] for k in ('engine_version','config_hash','opponents_archive','opponents_archive_sha256','deadline_ms','ticks','gates')}
    p.update(sources=sources,seeds={'adaptive-development':seeds[:16]},opponents=reg['styles'],fixture_order_seed=2026102017,
             registration='docs/adaptive-architect/registration.json',runner_sha256=digest(ROOT/'tools/benchmarks/run_adaptive_architect.py'))
    DOC.mkdir(parents=True,exist_ok=True)
    (DOC/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
    (DOC/'development-protocol.json').write_text(json.dumps(p,indent=2)+'\n')
    print('Registered 16 unused development blocks,192 matched configurations,576 full native matches.')


if __name__=='__main__':main()
