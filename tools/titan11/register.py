"""Preregister disjoint development/validation seeds and unchanged promotion gates."""
import hashlib,json,random,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/titan-11-intelligence'

def integers(value):
    if type(value) is int: yield value
    elif isinstance(value,dict):
        for v in value.values(): yield from integers(v)
    elif isinstance(value,list):
        for v in value: yield from integers(v)

def main():
    out=OUT/'registration.json'
    if out.exists(): raise SystemExit('Registration already exists; never overwrite.')
    used=set(range(1000,1010)); files=[]
    for root in (ROOT/'docs',Path('/workspace/work')):
        for p in root.rglob('*.json'):
            if p.stat().st_size>4_000_000 or not any(x in p.name for x in ('protocol','registry','registration','fresh','screen','seed-audit')): continue
            try: used.update(integers(json.loads(p.read_text())));files.append(str(p))
            except (ValueError,OSError): continue
    for branch in ('titan-11-championship','titan-12b-counter-defence'):
        for p in subprocess.check_output(['git','ls-tree','-r','--name-only',branch,'docs'],cwd=ROOT,text=True).splitlines():
            if any(x in p for x in ('seed-registry','seed-audit','protocol.json')):
                data=subprocess.check_output(['git','show',branch+':'+p],cwd=ROOT)
                used.update(integers(json.loads(data)));files.append(branch+':'+p)
    rng=random.Random(1100182026); chosen=[]
    while len(chosen)<28:
        x=rng.randrange(10000,2**31-1)
        if x not in used and x not in chosen: chosen.append(x)
    record={'project':'TITAN-11 Tactical Intelligence','base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'baseline_sha256':hashlib.sha256((ROOT/'my-team/team.py').read_bytes()).hexdigest(),
        'development':chosen[:4],'optimization':chosen[4:8],'validation':chosen[8:24],'reserve':chosen[24:],
        'excluded_integer_values':len(used),'excluded_sources':files,'excluded_values_sha256':hashlib.sha256(json.dumps(sorted(used)).encode()).hexdigest(),
        'selection':'Independent feature screen on development only. Enable only positive points delta with no repeat failure and acceptable mean/raw misses. Search fixed finite parameter grid on optimization cohort; select by mean points, tie goal difference then lowest work. Integrate selected features, compare full integration and leave-one-feature-out on development. Freeze best development candidate before any validation. No held-out tuning.',
        'validation_fixtures':768,'validation_seed_blocks':16,'fixture_variants':'both sides x both kickoff arrangements',
        'gates':{'points_delta_gt':0,'seed_block_paired_bootstrap_lower_gt':0,'policy_exceptions':0,'repeat_deadline_failure':False,'mean_ratio':1.35,'mean_allowance_ms':.04,'extra_raw_misses_per_1000_max':2.,'deadline_ms':20.,'ticks':2400},
        'training_pool':['v10','v9.1','v9.0','v10-press','v10-counter','v10-compact','v10-long','tight_links'],
        'heldout_styles':['v10-linekeeper','v10-mark','long_shooter','wide_switch'],
        'uncertainty':'Fixed opponent pool, seed-block inference; local results do not establish online ranking.'}
    assert len(set(chosen)&used)==0
    OUT.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(record,indent=2)+'\n')
    print({k:v for k,v in record.items() if k not in ('excluded_sources',)})
if __name__=='__main__':main()
