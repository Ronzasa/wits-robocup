"""Freeze independent cohorts, source hashes and gates before native play."""
import hashlib
import json
from pathlib import Path
import random
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/titan-v11'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def integers(value):
    if type(value) is int:
        yield value
    elif isinstance(value,dict):
        for v in value.values():yield from integers(v)
    elif isinstance(value,list):
        for v in value:yield from integers(v)


def main():
    dest=DOC/'registration.json'
    assert not dest.exists(), 'Never overwrite a registered experiment.'
    excluded=set(range(1000,1010)); evidence=[]
    for root in (Path('/workspace/wits-robocup/docs'),Path('/workspace/work'),Path('/workspace/titan')):
        for path in sorted(root.rglob('*.json')):
            if path.stat().st_size>4_000_000 or not any(s in path.name for s in ('protocol','registration','registry')):
                continue
            try:
                values=set(integers(json.loads(path.read_text())))
            except (ValueError,UnicodeDecodeError):continue
            excluded.update(values)
            evidence.append({'path':str(path),'sha256':digest(path)})
    rng=random.Random(202610201106)
    seeds=[]
    while len(seeds)<32:
        n=rng.randrange(10_000_000,2_000_000_000)
        if n not in excluded and n not in seeds:seeds.append(n)
    old=json.loads((ROOT/'docs/tactics/development-protocol.json').read_text())
    spec={name:{'path':path,'sha256':digest(ROOT/path)} for name,path in {
        'v10':'my-team/team.py','architect':'experiments/titan-v11-architect/team.py',
        'firewall':'experiments/titan-v11-firewall/team.py'}.items()}
    rules={
        'analysis':'Paired full-fixture differences, blocked by seed across all three styles, sides and kickoffs. 10000 whole-seed bootstrap resamples, RNG 719331; require strictly positive two-sided 97.5% lower bound (Bonferroni for two independent candidates), plus exact one-sided sign-flip p<=0.025 over whole-seed mean points deltas.',
        'competitive':'More raw and accepted league points than v10, no lower raw points against any individual registered style, and at least five executed tactic episodes.',
        'architect_intent':'More raw completed passes with no increase in raw turnovers.',
        'firewall_intent':'Fewer raw goals conceded.',
        'combination':'Only if BOTH standalone candidates pass every independent development gate. Build a fresh combined source and test against v10 on the eight reserved integration seeds, same three styles; require positive 95% whole-seed interval, more points, no extra concessions or turnovers, and all runtime/safety gates before qualification.',
        'qualification':'Only a candidate passing its development gates may be qualified. Freeze source and use 16 untouched qualification seeds x12 frozen styles xboth sides xboth kickoffs=768 pairs. All original qualification gates apply. No best-failure qualification; no main or active champion changes, even after a pass.',
        'timing':'One serial native worker, stock 20ms SDK deadline, 2400 ticks. Record every raw timeout and policy error. Repeat timeout fixtures identically at most three times, first clean regardless of score. Reproducible candidate timeout on first exact repeat is disqualifying. No affinity, GC, deadline or physics changes.',
        'attribution':'Command labels count only matching final movement commands accepted under deadline. Episodes split after gaps >5 ticks. Movement is not proof of completed passes, blocks or causal goals. Engine match statistics and matched v10 scores establish outcomes.',
        'no_tuning':'Sources and seeds frozen before play; no changes from this cohort. Fresh future development requires new protocol and unused seeds.'}
    registration={'project':'TITAN v11 tactics 05 and 06','created_utc':datetime.now(timezone.utc).isoformat(),
        'base_commit':'1fc486672b565e9edabe5286cdd1bc124061e575','champion_sha256':spec['v10']['sha256'],
        'sources':spec,'development':seeds[:8],'integration_reserved':seeds[8:16],
        'qualification_reserved':seeds[16:32],'development_styles':['v10-press','v10-compact','v10-counter'],
        'qualification_styles':json.loads((ROOT/'docs/tactics/registration.json').read_text())['qualification_styles'],
        'excluded_values_sha256':hashlib.sha256(json.dumps(sorted(excluded)).encode()).hexdigest(),
        'excluded_sources':evidence,'gates':old['gates'],'rules':rules,
        'preserved':['frozen v10 source','goalkeeper','carrier kick selection','defensive cover safeguards','counterpress','receiver/pass/contact/shot physics','competition config'],
        'inactive':['KEEPER_POWER_PLAY','GOALKEEPER_TRAP','PINBALL_SLINGSHOT','COOLDOWN_AMBUSH']}
    protocol={k:old[k] for k in ('engine_version','config_hash','opponents_archive','opponents_archive_sha256','deadline_ms','ticks','gates')}
    protocol.update(sources=spec,seeds={'v11-development':seeds[:8]},opponents=registration['development_styles'],fixture_order_seed=20261020,
        registration='docs/titan-v11/registration.json',runner_sha256=digest(ROOT/'tools/benchmarks/run_titan_v11.py'))
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(registration,indent=2)+'\n')
    (DOC/'development-protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    print('Frozen 8 unused development seed blocks, 96 paired fixtures per candidate, 288 native full matches.')


if __name__=='__main__':main()
