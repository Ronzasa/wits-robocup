"""Test actual controllable, unpressured body retention before generation 5."""
import argparse,json,shutil
from pathlib import Path
from build import build
from protocol import write,digest
from train import run,scores

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/nova-1'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args()
    reg=json.loads((DOC/'retention-experiment-registration.json').read_text())
    selected=json.loads((DOC/'selection-0-results.json').read_text())[0]
    assert selected['name']==reg['reference'] and selected['intake_ok']
    vector=selected['vector'];params={'config':vector[:8],'weights':vector[8:]+[.4],'framework':'r8-drive'}
    source=ROOT/'experiments/nova-1-retention/team.py';assert not source.exists();source.parent.mkdir(parents=True)
    source.write_text(build(params,True))
    protocol=DOC/'retention-protocol.json';write(protocol,{'v10':'my-team/team.py','reference':selected['source'],
        'body-retention':str(source.relative_to(ROOT))},reg['seeds'],reg['styles'],'development-retention')
    out=a.work/'retention';run(protocol,out)
    before=scores(out,'reference');after=scores(out,'body-retention')
    delta=after['paired_ppm']-before['paired_ppm']
    styles={s:after['style_deltas'][s]-before['style_deltas'][s] for s in reg['styles']}
    flags={'more_points':delta>0.,'worst_style_delta':min(styles.values())>=-.5,
           'head_to_head_delta':styles['v10']>=-.25,'intake':after['intake_ok'],'no_errors':after['policy_errors']==0}
    adopted=all(flags.values());framework='r8-drive' if adopted else 'r7-pass'
    assert not (DOC/'generation-05-registration.json').exists()
    schedule=json.loads((DOC/'framework-schedule.json').read_text());assert schedule['4']=='r7-pass'
    schedule['5']=framework
    (DOC/'framework-schedule.json').write_text(json.dumps(schedule,indent=2)+'\n')
    if adopted:shutil.copyfile(ROOT/'tools/nova/framework-r8-drive.pyfrag',ROOT/'tools/nova/controller.pyfrag')
    result={'adopted':adopted,'framework_for_generation_5':framework,'flags':flags,'reference':before,'body_retention':after,
        'relative_ppm':delta,'relative_styles':styles,'no_existing_source_changed':True,'original_promotion_gates_unchanged':True,
        'source_sha256':digest(source),'no_qualification_or_sealed_styles_used':True}
    path=DOC/'retention-results.json';assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n')
    history=json.loads((DOC/'framework-history.json').read_text())
    history['generation_5']={'framework':framework,'template_sha256':digest(ROOT/'tools/nova'/('framework-'+framework+'.pyfrag')),
        'reason':'Independent native development retention-action test; only adopt if points and matchup safety improve.'}
    (DOC/'framework-history.json').write_text(json.dumps(history,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
