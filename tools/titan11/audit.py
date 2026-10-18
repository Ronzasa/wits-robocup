"""Final independent source, intake, test and evidence checks, after timed matches."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'student-sdk'));sys.path.insert(0,str(ROOT/'tools'))
from soccer import validate as validation_module
from soccer.validate import validate
from evaluator import submissions

CHAMPION='5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('Preserve audit.')
    active=ROOT/'my-team/team.py';candidate=ROOT/'experiments/titan-11/team.py';assert digest(active)==digest(ROOT/'champions/v10.0/team.py')==CHAMPION
    protected=['my-team','champions/v9.1','experiments/titan-10b','experiments/titan-10b-r','experiments/strict-interceptions','experiments/v8-full','engine','student-sdk','configs','VERSION']
    changes=subprocess.check_output(['git','diff','origin/main','--name-only','--',*protected],cwd=ROOT,text=True);assert not changes,changes
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='titan-11-tactical-intelligence'
    folder=submissions.inspect(candidate.parent);assert not folder.errors and not folder.flags,(folder.errors,folder.flags)
    report=validate(str(candidate),ticks=400);assert report.ok and report.stats['decisions']==2000
    log=a.out.with_suffix('.tests.log')
    with log.open('w') as f:result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-q'],cwd=ROOT,env={**os.environ,'ROBOCUP_TEAM_PATH':str(candidate)},stdout=f,stderr=subprocess.STDOUT)
    assert result.returncode==0,log.read_text()
    selection=json.loads((ROOT/'docs/titan-11-intelligence/final-selection.json').read_text());assert selection['candidate_sha256']==digest(candidate)
    protocol=json.loads((ROOT/'docs/titan-11-intelligence/validation-protocol.json').read_text());assert protocol['sources']['titan11']['sha256']==digest(candidate)
    source_records={}
    for proto in (ROOT/'docs/titan-11-intelligence').glob('*protocol.json'):
        for n,spec in json.loads(proto.read_text())['sources'].items():
            path=ROOT/spec['path'];assert digest(path)==spec['sha256'],path;source_records[spec['path']]=spec['sha256']
    data={'candidate_sha256':digest(candidate),'champion_sha256':digest(active),'active_submission_modified':False,'all_registered_sources_still_frozen':True,'registered_sources':source_records,
        'protected_paths_unchanged_from_main':protected,'folder_errors':folder.errors,'folder_flags':folder.flags,'intake':{'ok':report.ok,'errors':report.errors,'warnings':report.warnings,'stats':report.stats},'regressions_exit_code':result.returncode,'test_log':str(log),'test_summary':log.read_text().strip(),'branch':'titan-11-tactical-intelligence'}
    a.out.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({k:v for k,v in data.items() if k not in ('registered_sources',)},indent=2))
if __name__=='__main__':main()
