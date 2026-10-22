"""Run independent development and preregistered fresh qualification."""
import argparse,json,random,subprocess,sys
from pathlib import Path
from register import DOC,ROOT,save,sha


def read(path):return json.loads(path.read_text())
def rows(path):return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=('development','qualification'))
    p.add_argument('--work',type=Path,required=True)
    args=p.parse_args();reg=read(DOC/'registration.json');stage=args.stage
    sources={name:{'path':path,'sha256':sha(ROOT/path)} for name,path in reg['sources'].items()}
    assert sources['v10']==reg['baseline'] and sources['active']==reg['active']
    proto={'engine_version':'0.1.0','config_hash':'372990895c7eca2a',
      'opponents_archive':reg['opponents_archive'],'opponents_archive_sha256':reg['opponents_archive_sha256'],
      'sources':sources,'seeds':{stage:reg[stage+'_seeds']},'opponents':reg[stage+'_styles'],
      'fixture_order_seed':10229391,'deadline_ms':20.,'ticks':2400}
    protocol=DOC/(stage+'-protocol.json');save(protocol,proto)
    subprocess.run(['git','add','tools/physics_tactics','tools/benchmarks/run_physics_tactics.py',
      'experiments/physics-ambush','experiments/physics-wall-brake','experiments/physics-rebound-shot','experiments/physics-off',
      'tests/test_physics_tactics.py','tests/fixtures/physics-synthetic-cases.json','tests/fixtures/physics-tactics-opponents.zip','docs/physics-tactics'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m','Freeze independent physics tactics before '+stage+' native cohort'],cwd=ROOT,check=True)
    folder=args.work.resolve()/stage
    subprocess.run([sys.executable,'tools/benchmarks/run_physics_tactics.py','--protocol',str(protocol),'--out',str(folder)],cwd=ROOT,check=True)
    results={}
    for name in ('ambush','wall-brake','rebound-shot'):
        comps={}
        for baseline in ('v10','active'):
            dest=folder/(name+'-vs-'+baseline+'.json')
            subprocess.run([sys.executable,'tools/benchmarks/compare.py',str(folder/'raw'/baseline),str(folder/'raw'/name),'--out',str(dest)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
            r=read(dest);a,b=r['baseline'],r['challenger']
            count=r['paired_fixtures'];extra=(b['policy_timeouts']-a['policy_timeouts'])*1000/count
            intake=read(folder/(name+'-validation.json'))
            repeated=sum(bool(x['result']['result']['stats'][x['result']['candidate_slot']]['policy_timeouts'])
                for x in rows(folder/'timing-repeats.jsonl') if x['source']==name)
            counters={}
            for x in rows(folder/'raw'/name/'matches.jsonl'):
                for key,value in x['physics_tactics']['counts'].items():counters[key]=counters.get(key,0)+value
            metric='rebound-shot_rebound_goals' if name=='rebound-shot' else name+'_collected'
            before={x['fixture_id']:x for x in rows(folder/'raw'/baseline/'matches.jsonl')}
            def points(row):
                i=row['candidate_slot'];sc=row['result']['score'];return 3 if sc[i]>sc[1-i] else 1 if sc[i]==sc[1-i] else 0
            blocks={}
            for x in rows(folder/'raw'/name/'matches.jsonl'):
                blocks.setdefault(x['seed'],[]).append(points(x)-points(before[x['fixture_id']]))
            means=[sum(v)/len(v) for v in blocks.values()];rng=random.Random(719331)
            boot=sorted(sum(rng.choices(means,k=len(means)))/len(means) for _ in range(20_000))
            adjusted=[boot[int(20_000*.05/6)],boot[int(20_000*(1-.05/6))-1]]
            malformed=sum(v for k,v in b['validation'].items() if k not in ('actions_validated','players_validated','rejected_kicks'))
            r.update({'bonferroni98_333333_interval':adjusted,'extra_raw_misses_per_1000':extra,
                'reproduced_own_deadlines':repeated,'tactic_counts':counters,
                'gates':{'more_raw_points':b['points']>a['points'],'positive_paired95_lower':r['paired_seed_block_bootstrap_95'][0]>0,
                  'positive_familywise_lower':adjusted[0]>0,'zero_exceptions':b['policy_errors']==0,
                  'no_reproduced_deadline':repeated==0,'raw_deadlines':extra<=2.,
                  'mean_runtime':b['decision_mean_ms']<=a['decision_mean_ms']*1.35+.04,
                  'sdk_intake':intake['ok'],'legal_actions':malformed==0,'fixture_count':count>=768,
                  'actual_native_success':counters.get(metric,0)>0}})
            comps[baseline]=r
        results[name]=comps
    save(DOC/(stage+'-results.json'),results)
    if stage=='qualification':
        save(DOC/'decision.json',{'main_modified':False,'active_champion_modified':False,'promoted':False,
          'primary_baseline':'v10','decisions':{name:{'qualified':all(comp['v10']['gates'].values()),
            'failed':[k for k,v in comp['v10']['gates'].items() if not v]} for name,comp in results.items()}})
        print(json.dumps(read(DOC/'decision.json'),indent=2),flush=True)


if __name__=='__main__':main()
