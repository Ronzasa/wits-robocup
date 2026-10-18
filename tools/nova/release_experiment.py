"""Independently test body-aware first commands on development fixtures.

The native scheduler is paused between full batches, never inside a decision.
No qualification or sealed style is used. Frozen population snapshots remain
unchanged; an adopted template applies only to uncreated generations 3+.
"""
import argparse, hashlib, json, shutil
from pathlib import Path
from build import build
from protocol import write, digest
from train import run, scores

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/nova-1'


def save(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, indent=2)+'\n')


def measure(work, label, sources, seeds, styles):
    protocol=DOC/(label+'-protocol.json')
    write(protocol,sources,seeds,styles,'development-release')
    out=work/label;run(protocol,out)
    result={name:scores(out,name) for name in sources if name!='v10'}
    reference=result['r6']
    for name,q in result.items():
        diffs={style:q['style_deltas'][style]-reference['style_deltas'][style] for style in styles}
        delta=q['paired_ppm']-reference['paired_ppm']
        q['relative_to_r6']={'ppm_delta':delta,'style_deltas':diffs,
            'worst_style_delta':min(diffs.values()),'objective':delta+.25*min(diffs.values())+.15*sum(sorted(diffs.values())[:2])*.5}
        q['eligible']=name!='r6' and delta>0. and min(diffs.values())>=-.5 and diffs['v10']>=-.25 and q['intake_ok'] and q['policy_errors']==0
    save(DOC/(label+'-results.json'),result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args()
    reg=json.loads((DOC/'release-experiment-registration.json').read_text())
    population=json.loads((DOC/'generation-02-registration.json').read_text())['population']
    reference=next(q for q in population if q['name']==reg['reference'])
    params={'config':reference['vector'][:8],'weights':reference['vector'][8:]+[.4]}
    sources={'v10':'my-team/team.py','r6':reference['source']}
    assert digest(ROOT/reference['source'])==reference['sha256']
    for name in ('r7-pass','r7-carry','r7-both'):
        dest=ROOT/'experiments/nova-1-release'/name/'team.py'
        assert not dest.exists();dest.parent.mkdir(parents=True)
        dest.write_text(build({**params,'framework':name},True));sources[name]=str(dest.relative_to(ROOT))
    first=measure(a.work,'release-independent',{k:v for k,v in sources.items() if k!='r7-both'},reg['independent_seeds'],reg['styles'])
    candidates=[name for name in ('r7-pass','r7-carry') if first[name]['eligible']]
    result=first;combined=False
    if len(candidates)==2:
        # Combine only after both independent improvements helped points.
        result=measure(a.work,'release-combined',sources,reg['combined_seeds'],reg['styles'])
        candidates=[name for name in ('r7-pass','r7-carry','r7-both') if result[name]['eligible']];combined=True
    choice=max(candidates,key=lambda name:(result[name]['relative_to_r6']['objective'],result[name]['points'])) if candidates else 'r6'
    decision={'framework':choice,'independent_results':first,'combined_test_run':combined,
        'selection_results':result,'new_framework_starts_generation':3,'no_existing_source_changed':True,
        'reason':'Native development points and matchup robustness; no heldout or qualification feedback.'}
    save(DOC/'release-experiment-decision.json',decision)
    assert not (DOC/'generation-03-registration.json').exists(), 'Do not rewrite a measured generation.'
    if choice!='r6':shutil.copyfile(ROOT/'tools/nova'/('framework-'+choice+'.pyfrag'),ROOT/'tools/nova/controller.pyfrag')
    save(DOC/'framework-schedule.json',{'0':'r4','1':'r5','2':'r6','3':choice,'4':choice,'5':choice})
    history=json.loads((DOC/'framework-history.json').read_text())
    history['generation_3_onward']={'framework':choice,'template_sha256':digest(ROOT/'tools/nova'/('framework-'+choice+'.pyfrag')),
        'reason':decision['reason'],'independent_experiment':'release-independent-protocol.json','combined_test_run':combined}
    (DOC/'framework-history.json').write_text(json.dumps(history,indent=2)+'\n')
    print(json.dumps({'framework':choice,'combined_test_run':combined,'independent_points':{k:q['points'] for k,q in first.items()}},indent=2),flush=True)


if __name__=='__main__':main()
