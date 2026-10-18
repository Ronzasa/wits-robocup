"""An isolated first-step opponent-response test before sealed qualification.

The completed population winner is the behavior reference. Test the single
response change on unused development seeds, then independently check it on
four more development seeds only if the screen helps. Existing sources and
the original population selection are preserved; no heldout result is used.
"""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from build import build,framework_for
from protocol import write,digest
from train import run,scores

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/nova-1'


def measure(work,label,sources,seeds,styles):
    protocol=DOC/(label+'-protocol.json');write(protocol,sources,seeds,styles,'development-response')
    out=work/label;run(protocol,out)
    before=scores(out,'reference');after=scores(out,'press-response')
    delta=after['paired_ppm']-before['paired_ppm']
    differences={style:after['style_deltas'][style]-before['style_deltas'][style] for style in styles}
    flags={'more_points':delta>0.,'worst_style':min(differences.values())>=-.5,
        'head_style':differences['v10']>=-.25,'intake':after['intake_ok'],'zero_errors':after['policy_errors']==0}
    return {'reference':before,'press_response':after,'delta_ppm':delta,'style_deltas':differences,
            'flags':flags,'eligible':all(flags.values()),'run':str(out)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args()
    registration=json.loads((DOC/'response-experiment-registration.json').read_text())
    original=json.loads((DOC/'selected-policy.json').read_text());base=original['selected']
    frame=base.get('framework') or framework_for(base['name'])
    assert base['intake_ok'],'The population winner must pass selection intake before this experiment.'
    result={'adopted':False,'population_policy':base['name'],'population_framework':frame,'no_heldout_feedback':True,
        'promotion_gates_unchanged':True,'screen':None,'check':None}
    if frame!='r7-pass':
        result['skipped']='The preregistered isolated variant starts from R7-pass; do not combine unrelated architecture changes.'
    else:
        # Verify the new physical model case before any native comparison.
        with (a.work/'response-regressions.log').open('x') as log:
            subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-q'],cwd=ROOT,
                           stdout=log,stderr=subprocess.STDOUT,check=True)
        vector=base['vector'];parameters={'config':vector[:8],'weights':vector[8:]+[.4],'framework':'r9-press'}
        source=ROOT/'experiments/nova-1-response/team.py';assert not source.exists();source.parent.mkdir(parents=True)
        source.write_text(build(parameters,True))
        assert digest(ROOT/base['source'])==original['candidate_sha256']
        sources={'v10':'my-team/team.py','reference':base['source'],'press-response':str(source.relative_to(ROOT))}
        screen=measure(a.work,'response-screen',sources,registration['screen_seeds'],registration['styles']);result['screen']=screen
        check=None
        if screen['eligible']:
            check=measure(a.work,'response-check',sources,registration['check_seeds'],registration['styles']);result['check']=check
        if screen['eligible'] and check is not None and check['eligible']:
            # Only fresh development evidence may replace this pointer. The
            # population controller and its exact original JSON stay intact.
            backup=ROOT/'experiments/nova-1-population-selected/team.py'
            assert not backup.exists();backup.parent.mkdir(parents=True)
            candidate=ROOT/original['candidate_path'];assert digest(candidate)==original['candidate_sha256']
            shutil.copyfile(candidate,backup)
            old_record=DOC/'population-selected-policy.json';assert not old_record.exists()
            shutil.copyfile(DOC/'selected-policy.json',old_record)
            shutil.copyfile(source,candidate)
            chosen={**base,**check['press_response'],'name':'r9-response','parent_policy':base['name'],
                'framework':'r9-press','source':str(source.relative_to(ROOT)),'sha256':digest(source),'selection_run':check['run']}
            updated={**original,'selected':chosen,'candidate_sha256':digest(candidate),
                'status':'Frozen after independent development response screen/check; before any unseen outcome.',
                'population_controller_backup':str(backup.relative_to(ROOT)),
                'population_selection_backup':str(old_record.relative_to(ROOT))}
            (DOC/'selected-policy.json').write_text(json.dumps(updated,indent=2)+'\n')
            result['adopted']=True
        result['source_sha256']=digest(source)
    dest=DOC/'response-results.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
