"""Registered serial native stages; qualification never selects/tunes flags."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/tactics'
sys.path.insert(0,str(ROOT/'tools/benchmarks'))

NAMES=('power','trap','pinball','ambush')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path,value):
    assert not path.exists(),path
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')

def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]

def protocol(name,sources,seeds,styles):
    reg=json.loads((DOC/'registration.json').read_text())
    data={'engine_version':'0.1.0','config_hash':'372990895c7eca2a',
          'opponents_archive':reg['opponents_archive'],'opponents_archive_sha256':reg['opponents_archive_sha256'],
          'sources':{k:{'path':v,'sha256':digest(ROOT/v)} for k,v in sources.items()},
          'seeds':{name:seeds},'opponents':styles,'fixture_order_seed':10182026,
          'deadline_ms':20.,'ticks':2400,'gates':reg['gates']}
    path=DOC/(name+'-protocol.json');save(path,data)
    return path

def run(path,out):
    subprocess.run([sys.executable,'tools/benchmarks/run_titan_x.py','--protocol',str(path),'--out',str(out)],cwd=ROOT,check=True)

def counts(folder,name):
    allrows=rows(folder/'raw'/name/'matches.jsonl')
    result={}
    for key in ('ticks','episodes','associations'):
        counter=Counter()
        for row in allrows:
            counter.update(row.get('titan_x',{}).get(key,{}))
        result[key]=dict(counter)
    result['examples']=[{'seed':r['seed'],'side':r['candidate_slot'],'kickoff':r['candidate_takes_kickoff'],
                         'opponent':Path(r['opponent']).parent.name,**e}
                        for r in allrows for e in r.get('titan_x',{}).get('examples',[])]
    return result

def comparison(folder,name):
    for label in ('accepted','raw'):
        subprocess.run([sys.executable,'tools/benchmarks/compare.py',str(folder/label/'v10'),str(folder/label/name),
                        '--out',str(folder/(name+'-'+label+'-paired.json'))],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    result=json.loads((folder/(name+'-accepted-paired.json')).read_text())
    raw=json.loads((folder/(name+'-raw-paired.json')).read_text())
    result['raw_baseline']=raw['baseline'];result['raw_challenger']=raw['challenger']
    b,c=raw['baseline'],raw['challenger']
    extra=(c['policy_timeouts']-b['policy_timeouts'])*1000/result['paired_fixtures']
    limit=result['baseline']['decision_mean_ms']*1.35+.04
    repeats=rows(folder/'timing-repeats.jsonl')
    reproduced=sum(bool(r['result']['result']['stats'][r['result']['candidate_slot']].get('policy_timeouts',0))
                   for r in repeats if r['source']==name)
    intake=json.loads((folder/(name+'-validation.json')).read_text())
    malformed=sum(v for k,v in c['validation'].items() if k not in ('actions_validated','players_validated','rejected_kicks'))
    result['gates']={'more_points':result['challenger']['points']>result['baseline']['points'],
        'positive_whole_seed_95_lower':result['paired_seed_block_bootstrap_95'][0]>0.,
        'zero_policy_exceptions':c['policy_errors']==0 and result['challenger']['policy_errors']==0,
        'no_reproducible_deadline_failure':reproduced==0,
        'raw_deadline_allowance':extra<=2.,'mean_runtime':result['challenger']['decision_mean_ms']<=limit,
        'official_sdk':intake['ok'] and not intake['folder_errors'],'legal_actions':malformed==0,
        'fresh_fixture_count':result['paired_fixtures']>=768}
    result['extra_raw_misses_per_1000']=extra;result['mean_runtime_ceiling_ms']=limit
    result['repeated_candidate_deadline_failures']=reproduced
    result['tactics']=counts(folder,name)
    result['qualified']=all(result['gates'].values())
    save(folder/(name+'-comparison.json'),result)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=('targeted','development','select','qualify'))
    p.add_argument('--work',type=Path,required=True)
    args=p.parse_args();work=args.work.resolve();work.mkdir(parents=True,exist_ok=True)
    reg=json.loads((DOC/'registration.json').read_text())
    if args.stage=='targeted':
        for name in NAMES:
            path=protocol('targeted-'+name,{'v10':'my-team/team.py',name:'experiments/titan-x-'+name+'/team.py'},
                          reg['targeted'],reg['targeted_styles'][name])
            run(path,work/('targeted-'+name))
            result=comparison(work/('targeted-'+name),name)
            save(DOC/('targeted-'+name+'-results.json'),result)
    elif args.stage=='development':
        sources={'v10':'my-team/team.py',**{n:'experiments/titan-x-'+n+'/team.py' for n in NAMES}}
        path=protocol('development',sources,reg['development'],reg['development_styles'])
        run(path,work/'development')
        for name in NAMES:
            save(DOC/('development-'+name+'-results.json'),comparison(work/'development',name))
    elif args.stage=='select':
        results={n:json.loads((DOC/('development-'+n+'-results.json')).read_text()) for n in NAMES}
        promising=[];episodes={}
        for name,r in results.items():
            target=json.loads((DOC/('targeted-'+name+'-results.json')).read_text())
            keys={'power':('power_start',),'trap':('trap_run','trap_pass'),
                  'pinball':('pinball_pass',),'ambush':('ambush_challenge',)}[name]
            episodes[name]=sum(s['tactics']['episodes'].get(k,0) for s in (r,target) for k in keys)
            if (r['gates']['more_points'] and r['challenger']['goal_difference']>r['baseline']['goal_difference']
                    and episodes[name]>=5 and all(r['gates'][k] for k in ('zero_policy_exceptions','raw_deadline_allowance','mean_runtime'))):
                promising.append(name)
        if len(promising)>1:
            from build import build,FLAGS
            enabled=[FLAGS[NAMES.index(n)] for n in promising]
            build('titan-x-combined',enabled)
            sources={'v10':'my-team/team.py','combined':'experiments/titan-x-combined/team.py',
                     **{n:'experiments/titan-x-'+n+'/team.py' for n in promising}}
            path=protocol('interaction',sources,reg['reserve_unused'],reg['development_styles'])
            run(path,work/'interaction')
            interaction={n:comparison(work/'interaction',n) for n in ('combined',*promising)}
            # Score on this pre-registered interaction cohort, fewer flags
            # breaks ties. No combination is selected just for its novelty.
            chosen=max(interaction,key=lambda n:(interaction[n]['challenger']['points'],n!='combined'))
            path='experiments/titan-x-'+chosen+'/team.py'
        else:
            chosen=promising[0] if promising else max(NAMES,key=lambda n:(results[n]['challenger']['points'],results[n]['challenger']['goal_difference'],-NAMES.index(n)))
            path='experiments/titan-x-'+chosen+'/team.py'
        save(DOC/'selection.json',{'selected':chosen,'path':path,'sha256':digest(ROOT/path),
            'promising_independent_tactics':promising,'integration_justified':len(promising)>1,
            'executed_episodes':episodes,'best_failure_only':not promising,
            'rule':reg['selection']})
        print('Selected',chosen,'promising independently:',promising,flush=True)
    elif args.stage=='qualify':
        selection=json.loads((DOC/'selection.json').read_text());source=ROOT/selection['path']
        assert digest(source)==selection['sha256']
        path=protocol('qualification',{'v10':'my-team/team.py','titan-x':selection['path']},
                      reg['qualification'],reg['qualification_styles'])
        subprocess.run(['git','add','tools/titan_x','tools/benchmarks/run_titan_x.py','tests/test_special_tactics.py',
                        'tests/fixtures/titan-x-opponents.zip','docs/tactics','experiments/titan-x',
                        *['experiments/titan-x-'+n for n in NAMES]],cwd=ROOT,check=True)
        if (ROOT/'experiments/titan-x-combined').exists():
            subprocess.run(['git','add','experiments/titan-x-combined'],cwd=ROOT,check=True)
        subprocess.run(['git','commit','-m','Freeze TITAN-X selection and 768-pair qualification protocol'],cwd=ROOT,check=True)
        run(path,work/'qualification')
        result=comparison(work/'qualification','titan-x')
        save(DOC/'qualification-results.json',result)
        save(DOC/'decision.json',{'status':'QUALIFIED_EXPERIMENT_ONLY' if result['qualified'] else 'RETAIN_V10_0',
              'promoted':False,'selected':selection['selected'],'sha256':selection['sha256'],
              'failed_gates':[k for k,v in result['gates'].items() if not v],
              'main_and_champion_unchanged':True})
        print(json.dumps(json.loads((DOC/'decision.json').read_text()),indent=2),flush=True)

if __name__=='__main__':
    main()
