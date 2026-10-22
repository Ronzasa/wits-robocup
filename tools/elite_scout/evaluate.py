"""Finite independent development and optional fresh 768-pair qualification."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,random,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/elite-scout'
sys.path.insert(0,str(ROOT/'tools/elite_scout'))
from build import build,VARIANTS

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(p,x):
    assert not p.exists(),p
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(s) for s in p.read_text().splitlines()]
def ints(v):
    if type(v) is int:yield v
    elif isinstance(v,dict):
        for x in v.values():yield from ints(x)
    elif isinstance(v,list):
        for x in v:yield from ints(x)

def register():
    used=set(range(1000,1010))
    for root in (Path('/workspace/work'),Path('/workspace/wits-robocup/docs')):
        for p in root.rglob('*.json'):
            if p.stat().st_size>4_000_000 or not any(k in p.name for k in ('protocol','registration','registry')):continue
            try:used.update(ints(read(p)))
            except (ValueError,UnicodeDecodeError):pass
    rng=random.Random(10222026);seeds=[]
    while len(seeds)<22:
        s=rng.randrange(10_000_000,2_000_000_000)
        if s not in used and s not in seeds:seeds.append(s)
    original=ROOT/'tests/fixtures/elite-scout-opponents.zip'
    with zipfile.ZipFile(original) as z:
        manifest=read_zip=json.loads(z.read('manifest.json'));content={r['path']:z.read(r['path']) for r in manifest}
    for name,path in [('titan-x-trap','experiments/elite-scout-baseline/team.py'),('depth14-proxy','experiments/elite-scout-keeper14/team.py')]:
        code=(ROOT/path).read_bytes();r={'style':name,'path':name+'/team.py','sha256':hashlib.sha256(code).hexdigest()}
        manifest.append(r);content[r['path']]=code
    with zipfile.ZipFile(original,'w',zipfile.ZIP_DEFLATED) as z:
        for k,v in content.items():z.writestr(k,v)
        z.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
    record={'base_commit':'0a7a3aeba3950eb1b2ed0deeb7a06f2f9b3563e5',
        'started_utc':datetime.now(timezone.utc).isoformat(),
        'baseline':'experiments/elite-scout-baseline/team.py','baseline_sha256':sha(ROOT/'experiments/elite-scout-baseline/team.py'),
        'champion':'my-team/team.py','champion_sha256':sha(ROOT/'my-team/team.py'),
        'archive':str(original.relative_to(ROOT)),'archive_sha256':sha(original),
        'screen_seeds':seeds[:2],'confirmation_seeds':seeds[2:6],'qualification_seeds':seeds[6:],
        'screen_styles':['v10','v10-compact','v10-counter','v10-press','quick_wall','depth14-proxy'],
        'confirmation_styles':['v10','v9.1','v10-compact','v10-counter','v10-press','quick_wall','tight_links','depth14-proxy'],
        'qualification_styles':['v10','v9.1','v10-compact','v10-counter','v10-press','quick_wall','tight_links','wide_switch','long_shooter','aggressive-keeper','titan-x-trap','depth14-proxy'],
        'hypotheses':VARIANTS,'source_hashes':{n:sha(ROOT/('experiments/elite-scout-'+n+'/team.py')) for n in VARIANTS},
        'selection':'Five isolated variants on identical48 configurations. Promising means more points than both frozen Trap and v10, no exceptions or reproduced deadlines, acceptable mean, <=2 additional raw misses/1000 relative to Trap. Choose best keeper cap by points, then goal difference, then smaller cap. Combine only promising independent feature families. Confirm promising singletons and justified combination on128 unused configurations. If none promising, confirm the highest-points failed singleton for diagnosis only. Choose confirmation winner by points then goal difference then fewer features. Qualification only if winner beats both baselines in points and passes reliability gates in confirmation. No changes or selection from qualification outcomes.',
        'gates':{'paired_points_more_than_both_baselines':True,'strict_whole_seed_bootstrap95_lower_gt_zero_both':True,
                 'zero_policy_exceptions':True,'no_reproduced_deadline_failure':True,'extra_raw_misses_per_1000_max':2.,
                 'mean_limit':'baseline*1.35+.04ms','official_sdk':True,'valid_actions':True,'qualification_pairs':768},
        'native':'20ms,2400ticks,stock engine/config;serial worker;rotating source order;both sides and kickoffs. Preserve all raw rows. Exact timeout repeats at most3, first clean independent of score. No clock/GC/affinity/deadline changes inside controller.',
        'limitations':'The supplied videos contain no user-team match and reveal no source code/cooldowns. depth14-proxy copies one observed goalkeeper-position idea into known local code; it is not Gabriel Behane or Zamokuhle Maziya. Scores against proxies are not scores against the actual leaders.',
        'excluded_values_sha256':hashlib.sha256(json.dumps(sorted(used)).encode()).hexdigest()}
    save(DOC/'registration.json',record);return record

def protocol(label,sources,seeds,styles):
    reg=read(DOC/'registration.json')
    p=DOC/(label+'-protocol.json')
    save(p,{'engine_version':'0.1.0','config_hash':'372990895c7eca2a','opponents_archive':reg['archive'],
        'opponents_archive_sha256':reg['archive_sha256'],'sources':{n:{'path':v,'sha256':sha(ROOT/v)} for n,v in sources.items()},
        'seeds':{label:seeds},'opponents':styles,'fixture_order_seed':10222026,'deadline_ms':20.,'ticks':2400})
    return p
def run(p,out):
    subprocess.run([sys.executable,'tools/benchmarks/run_elite_scout.py','--protocol',str(p),'--out',str(out)],cwd=ROOT,check=True)
def compare(folder,base,candidate):
    value={}
    for label in ('accepted','raw'):
        dest=folder/(candidate+'-vs-'+base+'-'+label+'.json')
        subprocess.run([sys.executable,'tools/benchmarks/compare.py',str(folder/label/base),str(folder/label/candidate),'--out',str(dest)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        value[label]=read(dest)
    a,b=value['raw']['baseline'],value['raw']['challenger'];ac,bc=value['accepted']['baseline'],value['accepted']['challenger']
    extra=(b['policy_timeouts']-a['policy_timeouts'])*1000/value['accepted']['paired_fixtures']
    repeated=sum(bool(r['result']['result']['stats'][r['result']['candidate_slot']]['policy_timeouts']) for r in rows(folder/'timing-repeats.jsonl') if r['source']==candidate)
    intake=read(folder/(candidate+'-validation.json'))
    malformed=sum(v for k,v in b['validation'].items() if k not in ('actions_validated','players_validated','rejected_kicks'))
    value['flags']={'more_points':bc['points']>ac['points'],'positive_ci':value['accepted']['paired_seed_block_bootstrap_95'][0]>0,
        'zero_errors':b['policy_errors']==0,'no_repeated_timeout':repeated==0,'raw_deadlines':extra<=2,
        'mean_runtime':bc['decision_mean_ms']<=ac['decision_mean_ms']*1.35+.04,'sdk':intake['ok'],
        'legal_actions':malformed==0,'fixture_count':value['accepted']['paired_fixtures']>=768}
    value['extra_raw_misses_per_1000']=extra;value['repeated_timeouts']=repeated
    save(folder/(candidate+'-vs-'+base+'-gates.json'),value);return value
def eligible(r):return r['flags']['more_points'] and all(v for k,v in r['flags'].items() if k not in ('positive_ci','fixture_count'))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=('register','screen','confirm','qualify'));p.add_argument('--work',type=Path,required=True);a=p.parse_args();work=a.work.resolve();work.mkdir(parents=True,exist_ok=True)
    if a.stage=='register':register();return
    reg=read(DOC/'registration.json');bases={'trap':reg['baseline'],'v10':reg['champion']}
    if a.stage=='screen':
        sources={**bases,**{n:'experiments/elite-scout-'+n+'/team.py' for n in VARIANTS}}
        q=protocol('screen',sources,reg['screen_seeds'],reg['screen_styles']);run(q,work/'screen')
        result={n:{b:compare(work/'screen',b,n) for b in bases} for n in VARIANTS}
        save(DOC/'screen-results.json',result)
    elif a.stage=='confirm':
        result=read(DOC/'screen-results.json');promising=[n for n in VARIANTS if all(eligible(r) for r in result[n].values())]
        key=lambda n:(result[n]['trap']['accepted']['challenger']['points'],result[n]['trap']['accepted']['challenger']['goal_difference'],-(VARIANTS[n][0] or 1))
        keepers=[n for n in promising if n.startswith('keeper')]
        chosen=([max(keepers,key=key)] if keepers else [])+[n for n in promising if not n.startswith('keeper')]
        if not chosen:chosen=[max(VARIANTS,key=key)]
        sources={**bases,**{n:'experiments/elite-scout-'+n+'/team.py' for n in chosen}}
        settings=None
        if len(chosen)>1:
            settings=tuple(max(VARIANTS[n][i] for n in chosen) for i in range(3));build('combined',settings)
            sources['combined']='experiments/elite-scout-combined/team.py'
        save(DOC/'development-selection.json',{'independently_promising':promising,'confirm':chosen,'combined_settings':settings})
        q=protocol('confirmation',sources,reg['confirmation_seeds'],reg['confirmation_styles']);run(q,work/'confirmation')
        results={n:{b:compare(work/'confirmation',b,n) for b in bases} for n in sources if n not in bases}
        save(DOC/'confirmation-results.json',results)
        rank=lambda n:(results[n]['trap']['accepted']['challenger']['points'],results[n]['trap']['accepted']['challenger']['goal_difference'],n!='combined')
        winner=max(results,key=rank);ready=all(eligible(r) for r in results[winner].values())
        save(DOC/'final-selection.json',{'name':winner,'path':sources[winner],'sha256':sha(ROOT/sources[winner]),'ready_for_qualification':ready})
        print('Confirmation winner:',winner,'ready:',ready,flush=True)
    else:
        selection=read(DOC/'final-selection.json')
        if not selection['ready_for_qualification']:
            save(DOC/'decision.json',{'promoted':False,'status':'RETAIN_BASELINES','reason':'No confirmation winner beats both baselines with acceptable reliability.','selected':selection});return
        assert sha(ROOT/selection['path'])==selection['sha256']
        q=protocol('qualification',{**bases,'scout':selection['path']},reg['qualification_seeds'],reg['qualification_styles'])
        subprocess.run(['git','add','tools/elite_scout','tools/benchmarks/run_elite_scout.py','docs/elite-scout','tests/test_elite_scout.py','tests/fixtures/elite-scout-opponents.zip','experiments'],cwd=ROOT,check=True)
        subprocess.run(['git','commit','-m','Freeze replay-led challenger before untouched 768-pair qualification'],cwd=ROOT,check=True)
        run(q,work/'qualification');result={b:compare(work/'qualification',b,'scout') for b in bases}
        save(DOC/'qualification-results.json',result)
        passed=all(all(r['flags'].values()) for r in result.values())
        save(DOC/'decision.json',{'promoted':False,'status':'QUALIFIED_EXPERIMENT_ONLY' if passed else 'RETAIN_BASELINES','selected':selection,
            'failed':{b:[k for k,v in r['flags'].items() if not v] for b,r in result.items()}})
        print(json.dumps(read(DOC/'decision.json'),indent=2),flush=True)
if __name__=='__main__':main()
