"""Register an unchanged Original Architect and disjoint broader fresh cohorts."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import json
import random

ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/original-architect'


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
            if p.stat().st_size>4_000_000 or not any(k in p.name for k in ('protocol','registration','registry')):continue
            try:excluded.update(integers(json.loads(p.read_text())))
            except (ValueError,UnicodeDecodeError):continue
            audit.append({'path':str(p),'sha256':digest(p)})
    rng=random.Random(202610202115);seeds=[]
    while len(seeds)<28:
        n=rng.randrange(10_000_000,2_000_000_000)
        if n not in excluded and n not in seeds:seeds.append(n)
    old=json.loads((ROOT/'docs/titan-v11/registration.json').read_text())
    sources={n:old['sources'][n] for n in ('v10','architect')}
    for s in sources.values():assert digest(ROOT/s['path'])==s['sha256']
    styles=['v10','v10-press','v10-compact','v10-counter','v10-long','v9.1','tight_links','wide_switch']
    rules={
      'development_cohort':'12 fresh blocks x8 styles xboth sides xboth kickoffs=384 pairs,768 original full native matches. Frozen sources. No outcome-driven tuning, opponent selection, seed extension or replacement.',
      'development_competitive':'Preserve the previous Original Architect development criteria: more raw and accepted points; positive raw and accepted 97.5% whole-seed bootstrap lower bounds and exact one-sided sign-flip p<=0.025; no raw points regression in any registered style; >=5 executed Architect support episodes; more raw completed passes with no extra raw turnovers.',
      'statistics':'Balanced integer whole-seed point differences. 10000 bootstrap resamples for development; RNG719331; preserve all styles/sides/kickoffs in each resampled seed. Exact sign-flip enumeration. No floating-point near-zero promoted as positive.',
      'runtime':'Original official SDK/legality/zero-exception gates; no candidate timeout on a first exact repeat; no unresolved timeout after3 exact repeats; extra raw deadline misses/1000<=2; accepted mean<=v10*1.35+.04ms. Stock native20ms and2400ticks,one worker,no GC/affinity/physics changes. Raw outcomes immutable; repeats retained separately, first clean regardless of score.',
      'repeat_diagnostics':'Raw and every repeat use identical SDK wall/thread CPU/GC tracing and public-input hashes for slow calls. Distinguish whole-fixture recurrence, same-tick/public-input recurrence and a new miss on repeat. Conservative gate counts every candidate timeout on first repeat; do not silently waive misses.',
      'qualification':'Only if ALL development gates pass:16 separate unused seed blocks x12 frozen styles xboth sides xboth kickoffs=768 pairs,1536 original full native matches. Require original more-points and strictly-positive95% whole-seed interval plus exact p<=.05, all original SDK/action/exception/runtime/reproducibility gates and768pairs. 5000 bootstrap resamples,RNG719331. Never reuse development or forensic seeds.',
      'promotion':'No automatic promotion. Main,my-team/team.py,frozen v10 and Original Architect sources stay unchanged even if qualification passes. A concrete recommendation with evidence must precede explicit user approval.',
      'forensics':'Historical Adaptive misses and20 forensic full matches are diagnosis only, never part of fresh selection. Adaptive remains unchanged and ineligible in this evaluation.'}
    reg={'project':'Unchanged Original Architect independent evaluation','base_commit':'c85f896797d991de32cd0018d04225dbcd497bdc',
        'created_utc':datetime.now(timezone.utc).isoformat(),'sources':sources,'development':seeds[:12],
        'qualification_reserved':seeds[12:],'development_styles':styles,'qualification_styles':old['qualification_styles'],
        'rules':rules,'excluded_values_sha256':hashlib.sha256(json.dumps(sorted(excluded)).encode()).hexdigest(),'excluded_sources':audit,
        'original_promotion_gates':old['gates'],'disabled':['COUNTERATTACK_FIREWALL','KEEPER_POWER_PLAY','GOALKEEPER_TRAP','PINBALL_SLINGSHOT','COOLDOWN_AMBUSH','ADAPTIVE_ARCHITECT']}
    template=json.loads((ROOT/'docs/titan-v11/development-protocol.json').read_text())
    runner_hashes={rel:digest(ROOT/rel) for rel in ('tools/original_architect/run.py','tools/original_architect/timing.py','tools/original_architect/paired_statistics.py')}
    for stage,values,opponents,shuffle in [('development',seeds[:12],styles,202610202115),('qualification',seeds[12:],old['qualification_styles'],202610202116)]:
        p={k:template[k] for k in ('engine_version','config_hash','opponents_archive','opponents_archive_sha256','ticks','deadline_ms','gates')}
        p.update(stage=stage,sources=sources,seeds={stage:values},opponents=opponents,fixture_order_seed=shuffle,
                 runner_hashes=runner_hashes,registration='docs/original-architect/registration.json')
        (DOC/(stage+'-protocol.json')).write_text(json.dumps(p,indent=2)+'\n')
    (DOC/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
    print('Sealed12 fresh development blocks/8 styles,384 pairs; reserved16 separate qualification blocks/12 styles,768 pairs.')


if __name__=='__main__':main()
