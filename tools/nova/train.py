"""Native-outcome cross-entropy policy optimization with frozen generations.

No heldout styles or qualification/confirmation seeds are read or played.
All sources are standalone and frozen before each common native batch.
"""
import argparse,hashlib,json,math,os,random,shutil,statistics,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nova'));sys.path.insert(0,str(ROOT/'tools/benchmarks'))
from build import build,DEFAULT_CONFIG,DEFAULT_WEIGHTS,framework_for
from protocol import write,digest
from benchmark import candidate_score,points
DOC=ROOT/'docs/nova-1'
BOUNDS=[(6.,20.),(3.,18.),(2.,22.),(1.,6.),(1.6,4.5),(.03,.18),(0.,1.8),(0.,2.5),
        (1.,12.),(0.,5.),(-1.,3.),(0.,3.),(0.,2.),(-2.,1.),(-3.,1.),(-1.,3.),(-5.,0.),(-.5,2.),(-4.,0.)]

def dump(path,value):
    assert not path.exists(),path;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')
def pack(v):return {'config':v[:8],'weights':v[8:]+[.4]}
def normalize(v):return [(x-lo)/(hi-lo) for x,(lo,hi) in zip(v,BOUNDS)]
def unnormalize(v):return [round(lo+max(0.,min(1.,x))*(hi-lo),6) for x,(lo,hi) in zip(v,BOUNDS)]
def run(protocol,out):
    assert not out.exists()
    with (out.parent/(out.name+'.log')).open('w') as log:
        result=subprocess.run([sys.executable,'tools/benchmarks/run_nova.py','--protocol',str(protocol),'--out',str(out)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError('Native stage stopped; original evidence preserved: '+str(out))
    return json.loads((out/'metadata.json').read_text())
def scores(out,name):
    rows=[json.loads(q) for q in (out/'accepted'/name/'matches.jsonl').read_text().splitlines()]
    old=[json.loads(q) for q in (out/'accepted'/'v10'/'matches.jsonl').read_text().splitlines()]
    styles={}
    for n,source in [('candidate',rows),('baseline',old)]:
        for r in source:styles.setdefault(Path(r['opponent']).parent.name,{'candidate':[],'baseline':[]})[n].append(points(r))
    delta={style:statistics.mean(q['candidate'])-statistics.mean(q['baseline']) for style,q in styles.items()}
    mean=statistics.mean(points(r) for r in rows)-statistics.mean(points(r) for r in old)
    worst=min(delta.values());bottom=statistics.mean(sorted(delta.values())[:2])
    # Real league points and matchup fragility, never pass volume/geometry.
    objective=mean+.25*worst+.15*bottom
    summary=json.loads((out/'accepted'/name/'summary.json').read_text())['all']
    intake=json.loads((out/(name+'-validation.json')).read_text())
    raw=json.loads((out/'raw'/name/'summary.json').read_text())['all']
    return {'objective':objective,'paired_ppm':mean,'worst_style_ppm':worst,'style_deltas':delta,
            'points':summary['points'],'baseline_points':sum(points(r) for r in old),'goal_difference':summary['goal_difference'],
            'policy_errors':raw['policy_errors'],'raw_deadlines':raw['policy_timeouts'],
            'mean_ms':summary['decision_mean_ms'],'intake_ok':intake['ok']}
def make_source(name,vector,joint=True):
    path=ROOT/'experiments/nova-1-population'/name/'team.py';assert not path.exists();path.parent.mkdir(parents=True)
    parameters=pack(vector)
    parameters['framework']=framework_for(name)
    path.write_text(build(parameters,joint));return str(path.relative_to(ROOT))

def generation(g,mean,sigma,elites,work,reg,rng):
    candidates=[]
    for i in range(24):
        z=elites[i]['normalized'] if i<len(elites) and i<2 else mean if i==0 else [max(0.,min(1.,rng.gauss(m,s))) for m,s in zip(mean,sigma)]
        vector=unnormalize(z);name=f'g{g:02d}-p{i:02d}';source=make_source(name,vector)
        candidates.append({'name':name,'vector':vector,'normalized':normalize(vector),'source':source,'sha256':digest(ROOT/source)})
    styles=['v10','v9.1']+[reg['training_styles'][2:][(g*4+i)%10] for i in range(4)]
    # Fresh development seed per generation, never a qualification seed.
    seed=reg['development'][2+g]
    dump(DOC/f'generation-{g:02d}-registration.json',{'population':candidates,'styles':styles,'seed':seed,'mean':mean,'sigma':sigma,'fixed_budget':24})
    ranked=[]
    for offset in range(0,24,6):
        group=candidates[offset:offset+6];label=f'g{g:02d}-batch{offset//6:02d}'
        protocol=DOC/(label+'-protocol.json');write(protocol,{'v10':'my-team/team.py',**{q['name']:q['source'] for q in group}},[seed],styles,'development-learning')
        out=work/label;run(protocol,out)
        for q in group:ranked.append({**q,**scores(out,q['name']),'run':str(out)})
        print('Completed',label,'native policies',len(ranked),'/24',flush=True)
    ranked.sort(key=lambda q:(q['objective'],q['points'],q['goal_difference'],-q['mean_ms']),reverse=True)
    dump(DOC/f'generation-{g:02d}-results.json',ranked)
    chosen=ranked[:6]
    new_mean=[.3*m+.7*statistics.mean(q['normalized'][j] for q in chosen) for j,m in enumerate(mean)]
    new_sigma=[max(.06,min(.35,statistics.pstdev(q['normalized'][j] for q in chosen)*1.2)) for j in range(len(mean))]
    print('Generation',g,'best objective',ranked[0]['objective'],'points',ranked[0]['points'],'baseline',ranked[0]['baseline_points'],flush=True)
    return ranked,new_mean,new_sigma

def shortlist(pool,work,reg,label,seeds):
    unique=[];seen=set();failed_intake_hashes={q['sha256'] for q in pool if not q['intake_ok']}
    for q in sorted(pool,key=lambda q:(q['objective'],q['points'],q['goal_difference']),reverse=True):
        if q['sha256'] in seen or q['sha256'] in failed_intake_hashes:continue
        seen.add(q['sha256']);unique.append(q)
        if len(unique)==8:break
    assert unique,'No legal complete policies to select.'
    sources={'v10':'my-team/team.py',**{q['name']:q['source'] for q in unique}}
    protocol=DOC/(label+'-protocol.json');write(protocol,sources,seeds,reg['qualification_styles'][:8],'development-selection')
    out=work/label;run(protocol,out)
    result=[{**q,**scores(out,q['name']),'selection_run':str(out)} for q in unique]
    # Prefer a robust winner. A weaker source is still reported/qualified;
    # it never becomes a champion by renaming it.
    result.sort(key=lambda q:(q['objective'],q['points'],q['goal_difference'],-q['mean_ms']),reverse=True)
    dump(DOC/(label+'-results.json'),result)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();work=a.work;work.mkdir(parents=True,exist_ok=True)
    reg=json.loads((DOC/'registration.json').read_text());rng=random.Random(9011009)
    mean=normalize(DEFAULT_CONFIG+DEFAULT_WEIGHTS[:11]);sigma=[.25]*len(mean);elites=[];pool=[]
    dump(DOC/'optimizer-registration.json',{'bounds':BOUNDS,'dimensions':19,'population':24,'generations':4,'elite_count':6,'retained_elites':2,'seed':9011009,
        'objective':'paired points per match + .25 worst-style delta + .15 mean of two worst-style deltas','sigma_initial':.25,'sigma_min':.06,'no_unseen_styles_or_final_seeds':True})
    for g in range(4):
        ranked,mean,sigma=generation(g,mean,sigma,elites,work,reg,rng);elites=ranked[:2];pool.extend(ranked)
    selected=shortlist(pool,work,reg,'selection-0',reg['development'][8:12])
    best=selected[0]
    if best['paired_ppm']<=0. or best['worst_style_ppm']<-.35:
        print('Development remains weaker/fragile; continuing registered development-only refinement.',flush=True)
        mean=best['normalized'];sigma=[.22]*len(mean);elites=selected[:2]
        for g in range(4,6):
            ranked,mean,sigma=generation(g,mean,sigma,elites,work,reg,rng);elites=ranked[:2];pool.extend(ranked)
        selected=shortlist(pool,work,reg,'selection-1',reg['development'][12:16]);best=selected[0]
    dest=ROOT/'experiments/nova-1/team.py';assert not dest.exists();dest.parent.mkdir(parents=True);shutil.copyfile(ROOT/best['source'],dest)
    dump(DOC/'selected-policy.json',{'selected':best,'candidate_path':str(dest.relative_to(ROOT)),'candidate_sha256':digest(dest),
        'total_evaluated_variants':len(pool),'unique_parameter_sources':len({q['sha256'] for q in pool}),
        'status':'FROZEN before unseen styles or qualification; not promoted','all_development_variants':[{k:q[k] for k in ('name','source','sha256','objective','paired_ppm','points','baseline_points')} for q in pool]})
    print('Selected frozen policy',best['name'],digest(dest),flush=True)
if __name__=='__main__':main()
