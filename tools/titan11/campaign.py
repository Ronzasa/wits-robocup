"""Registered serial ablations -> finite self-play search -> frozen validation.

No controller or source already measured is edited. Native timed workers run
serially. Every new source is a standalone file and frozen in its own folder.
All training/selection precedes the sole independent validation cohort.
"""
import argparse,hashlib,json,os,shutil,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/titan11'))
from build import build,FLAGS
from evaluate import evaluate
from protocol import write,digest
DOC=ROOT/'docs/titan-11-intelligence'

def save(path,value):
    assert not path.exists(),path;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')

def source(folder,flags,params):
    path=ROOT/'experiments'/('titan-11-'+folder)/'team.py';assert not path.exists(),path
    path.parent.mkdir(parents=True);path.write_text(build(flags,params));return str(path.relative_to(ROOT))

def run(protocol,out):
    assert not out.exists()
    with (out.parent/(out.name+'.log')).open('w') as log:
        subprocess.run([sys.executable,str(ROOT/'tools/benchmarks/run_intelligence.py'),'--protocol',str(protocol),'--out',str(out)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    return evaluate(out)

def ranking(item):
    name,row=item;c=row['accepted']['challenger'];return (c['points'],c['goal_difference'],-c['decision_mean_ms'],name)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();work=a.work
    reg=json.loads((DOC/'registration.json').read_text());params=json.loads((DOC/'fitted-parameters.json').read_text());params['finishing_revision']=2;params['coordination_revision']=2
    screen=work/'ablations';assert (screen/'metadata.json').exists()
    gates=json.loads((screen/'gate-audit.json').read_text()) if (screen/'gate-audit.json').exists() else evaluate(screen)
    # Complete finishing power trials have their own independent screen.
    # The original finishing implementation/results remain archived.
    with (work/'power-regressions.log').open('w') as log:
        subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-q'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    protocol=DOC/'finishing-power-protocol.json'
    write(protocol,{'v10':'my-team/team.py','finishing':'experiments/titan-11-finishing-power/team.py','coordinated':'experiments/titan-11-coordinated-flight/team.py'},reg['development'][:2],reg['training_pool'],'development')
    power=run(protocol,work/'finishing-power')
    original_finishing=gates['finishing'];gates['finishing']=power['finishing']
    original_coordinated=gates['coordinated'];gates['coordinated']=power['coordinated']
    eligible=[f for f in FLAGS if gates[f]['development_eligible']]
    save(DOC/'component-selection.json',{'original_finishing':original_finishing,'original_coordinated':original_coordinated,'eligible':eligible,'disabled':{f:[k for k,v in gates[f]['flags'].items() if not v] for f in FLAGS if f not in eligible},'gate_audit':gates})
    print('Independent components eligible:',eligible,flush=True)
    # All-feature and leave-one-out integration ablations remain available
    # even if an individual component fails. Such combinations cannot become
    # the final challenger while containing a rejected component.
    sources={'v10':'my-team/team.py'};flags_by_name={}; seen={}
    for name,flags in [('all',FLAGS),*[(f'all-minus-{f}',[x for x in FLAGS if x!=f]) for f in FLAGS],('selected',eligible),*[(f'selected-minus-{f}',[x for x in eligible if x!=f]) for f in eligible]]:
        key=tuple(flags)
        if key in seen:continue
        seen[key]=name;flags_by_name[name]=flags;sources[name]=source('integration-'+name,flags,params)
    # At most 12 sources including champion; split diagnostic and eligible
    # integrations if the set is larger (same seeds and fresh timing records).
    integration=[]
    names=list(flags_by_name)
    for part in range(0,len(names),11):
        group=names[part:part+11];protocol=DOC/('integration-'+str(part//11)+'-protocol.json')
        write(protocol,{'v10':sources['v10'],**{n:sources[n] for n in group}},reg['development'][:2],reg['training_pool'],'development')
        result=run(protocol,work/('integration-'+str(part//11)));integration.extend((n,r,flags_by_name[n]) for n,r in result.items())
    allowed=[(n,r,fs) for n,r,fs in integration if set(fs)<=set(eligible) and r['development_eligible']]
    if allowed:
        name,row,active=max(allowed,key=lambda t:ranking((t[0],t[1])));parent=sources[name]
    else:
        independently=[(f,gates[f]) for f in eligible]
        if independently:
            name,row=max(independently,key=ranking);active=[name];parent=row['source']['path']
        else:name='runtime';active=[];parent='experiments/titan-11-runtime-control/team.py'
    save(DOC/'integration-selection.json',{'selected_name':name,'active':active,'source':parent,'reason':'Best eligible development points, then goal difference, then mean runtime; rejected features prohibited.'})
    print('Integration selected:',name,active,flush=True)
    # Native self-play league contains archived champions, generated legal
    # wall/possession/pressing specialists and the selected archived parent.
    archive=ROOT/'tests/fixtures/titan-11-intelligence-training-league.zip';manifest=[]
    with zipfile.ZipFile(ROOT/'tests/fixtures/titan-11-intelligence-opponents.zip') as old,zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as new:
        for r in json.loads(old.read('manifest.json')):
            manifest.append(r);new.writestr(r['path'],old.read(r['path']))
        for style,code in [('titan11-self',(ROOT/parent).read_text()),('wall-specialist',build(['playbooks'],{**params,'open_width':.23})),('generated-press',build(['defence'],{**params,'pressure':.8})),('generated-possession',build(['coordinated','learning'],{**params,'risk':1.3,'width':10.}))]:
            data=code.encode();r={'style':style,'path':style+'/team.py','sha256':hashlib.sha256(data).hexdigest()};manifest.append(r);new.writestr(r['path'],data)
        new.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
    # Fixed four-point derivative-free design, registered before optimization.
    designs=[{'risk':.8,'width':10.,'through_lead':.8,'shoot_bias':-.25,'shot_scale':.9,'pressure':.9,'transition_aggression':.85,'rest_gap':3.,'space_gain':.08,'open_width':.15,'switch':.25,'value_scale':.35},
        {'risk':1.2,'width':14.,'through_lead':1.2,'shoot_bias':.25,'shot_scale':1.1,'pressure':1.1,'transition_aggression':1.15,'rest_gap':5.,'space_gain':.05,'open_width':.23,'switch':.12,'value_scale':.6},
        {'risk':.8,'width':14.,'through_lead':1.2,'shoot_bias':-.25,'shot_scale':1.1,'pressure':.9,'transition_aggression':1.15,'rest_gap':5.,'space_gain':.08,'open_width':.23,'switch':.12,'value_scale':.35},
        {'risk':1.2,'width':10.,'through_lead':.8,'shoot_bias':.25,'shot_scale':.9,'pressure':1.1,'transition_aggression':.85,'rest_gap':3.,'space_gain':.05,'open_width':.15,'switch':.25,'value_scale':.6}]
    optimized={'v10':'my-team/team.py','parent':parent};parameters={'parent':params}
    for i,d in enumerate(designs):
        n='search-'+str(i);parameters[n]={**params,**d};optimized[n]=source(n,active,parameters[n])
    save(DOC/'optimization-registration.json',{'features':active,'designs':designs,'training_opponents':['v10','v9.1','v10-press','v10-counter','titan11-self','wall-specialist','generated-press','generated-possession'],'seeds':reg['optimization'][:2],'objective':'points; tie goal difference; tie lower mean runtime; only reliable candidate eligible','fixed_budget':4,'training_league_sha256':digest(archive)})
    protocol=DOC/'optimization-protocol.json';write(protocol,optimized,reg['optimization'][:2],['v10','v9.1','v10-press','v10-counter','titan11-self','wall-specialist','generated-press','generated-possession'],'optimization')
    value=json.loads(protocol.read_text());value['opponents_archive']=str(archive.relative_to(ROOT));value['opponents_archive_sha256']=digest(archive);protocol.write_text(json.dumps(value,indent=2)+'\n')
    optimized_gates=run(protocol,work/'optimization')
    pool=[(n,r) for n,r in optimized_gates.items() if r['development_eligible']]
    if pool:
        selected,row=max(pool,key=ranking);chosen=optimized[selected];chosen_params=parameters[selected]
    else:selected='parent';chosen=parent;chosen_params=params
    dest=ROOT/'experiments/titan-11/team.py';assert not dest.exists();shutil.copyfile(ROOT/chosen,dest)
    selection={'selected':selected,'active':active,'parameters':chosen_params,'source':chosen,'candidate_sha256':digest(dest),'status':'FROZEN before independent validation; active submission unchanged','optimization':optimized_gates}
    save(DOC/'final-selection.json',selection)
    # Intake and regressions occur BEFORE timed independent validation.
    with (work/'final-regressions.log').open('w') as log:
        subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-q'],cwd=ROOT,env={**os.environ,'ROBOCUP_TEAM_PATH':str(dest)},stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run(['git','add','experiments','docs/titan-11-intelligence','tests/fixtures/titan-11-intelligence-training-league.zip','tools/titan11'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m','Freeze selected TITAN-11 challenger before independent 768-pair validation'],cwd=ROOT,check=True)
    protocol=DOC/'validation-protocol.json';write(protocol,{'v10':'my-team/team.py','titan11':'experiments/titan-11/team.py'},reg['validation'],reg['training_pool']+reg['heldout_styles'],'validation')
    # Commit protocol before exposing any independent result.
    subprocess.run(['git','add',str(protocol)],cwd=ROOT,check=True);subprocess.run(['git','commit','-m','Register untouched TITAN-11 final validation fixtures'],cwd=ROOT,check=True)
    print('Frozen final candidate',selection['candidate_sha256'],'starting independent validation',flush=True)
    final=run(protocol,work/'validation');save(DOC/'final-gates.json',final)
    print('Final gates',json.dumps({n:r['flags'] for n,r in final.items()}),flush=True)
if __name__=='__main__':main()
