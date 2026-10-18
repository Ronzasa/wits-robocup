"""Freeze one policy; qualify against sealed styles and confirm only on success."""
import argparse,hashlib,json,os,shutil,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nova'));sys.path.insert(0,str(ROOT/'tools/benchmarks'))
from protocol import write,digest
from train import run
DOC=ROOT/'docs/nova-1'

def save(path,value):
    assert not path.exists();path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')
def load_rows(path):return [json.loads(s) for s in path.read_text().splitlines()]
def comparison(before,after,out):
    assert not out.exists()
    subprocess.run([sys.executable,'tools/benchmarks/compare.py',str(before),str(after),'--out',str(out)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    return json.loads(out.read_text())
def assess(work):
    accepted=comparison(work/'accepted/v10',work/'accepted/nova',work/'paired-accepted.json')
    raw=comparison(work/'raw/v10',work/'raw/nova',work/'paired-raw.json')
    reg=json.loads((DOC/'registration.json').read_text());held=set(reg['unseen_styles'])
    for name in ('v10','nova'):
        rows=load_rows(work/'accepted'/name/'matches.jsonl')
        subset=[q for q in rows if Path(q['opponent']).parent.name in held]
        dest=work/'unseen'/name;dest.mkdir(parents=True)
        (dest/'matches.jsonl').write_text(''.join(json.dumps(q)+'\n' for q in subset))
    unseen=comparison(work/'unseen/v10',work/'unseen/nova',work/'paired-unseen.json')
    head=next(row for name,row in accepted['by_opponent'].items() if Path(name).parent.name=='v10')
    worst=min(row['points_per_match_difference'] for row in accepted['by_opponent'].values())
    b,c=raw['baseline'],raw['challenger'];extra=(c['policy_timeouts']-b['policy_timeouts'])*1000/accepted['paired_fixtures']
    intake=json.loads((work/'nova-validation.json').read_text())
    repeats=load_rows(work/'timing-repeats.jsonl')
    repeated=sum(bool(r['result']['result']['stats'][r['result']['candidate_slot']].get('policy_timeouts',0)) for r in repeats if r['source']=='nova')
    repeated_opponent=sum(bool(r['result']['result']['stats'][1-r['result']['candidate_slot']].get('policy_timeouts',0)) for r in repeats if r['source']=='nova')
    # Rejected kicks are a gameplay outcome, not malformed SDK actions.
    malformed=sum(v for k,v in c['validation'].items() if k not in ('actions_validated','players_validated','rejected_kicks'))
    source=json.loads((work/'metadata.json').read_text())['protocol']['sources']['nova']
    flags={'more_points':accepted['challenger']['points']>accepted['baseline']['points'],
        'positive_paired_95_lower':accepted['paired_seed_block_bootstrap_95'][0]>0.,
        'unseen_more_points':unseen['challenger']['points']>unseen['baseline']['points'],
        'unseen_no_material_regression':unseen['paired_seed_block_bootstrap_95'][0]>=-.10,
        'worst_style_no_collapse':worst>=-.35,
        'head_to_head_no_collapse':head['points_per_match_difference']>=-.15 and head['challenger']['points_per_match']>=1.25,
        'zero_policy_exceptions':c['policy_errors']==0 and accepted['challenger']['policy_errors']==0,
        'no_repeated_deadline_failure':repeated==0,
        'raw_deadlines':extra<=2.,'official_intake':intake['ok'] and not intake['folder_errors'],
        'valid_actions':malformed==0,'source_frozen':digest(ROOT/source['path'])==source['sha256'],
        'principal_fixture_count':accepted['paired_fixtures']>=768}
    result={'flags':flags,'all_gates_pass':all(flags.values()),'extra_raw_misses_per_1000':extra,
        'repeated_deadline_failures':repeated,'repeated_opponent_deadline_failures':repeated_opponent,'head_to_head':head,'worst_style_ppm_delta':worst,
        'accepted':accepted,'raw':raw,'unseen':unseen}
    save(work/'gates.json',result);return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args()
    reg=json.loads((DOC/'registration.json').read_text());selection=json.loads((DOC/'selected-policy.json').read_text())
    candidate=ROOT/selection['candidate_path'];assert digest(candidate)==selection['candidate_sha256']
    with (a.work/'selected-regressions.log').open('w') as log:
        subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-q'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    archive=ROOT/'tests/fixtures/nova-1-qualification.zip';assert not archive.exists()
    manifest=[]
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as out:
        for name,expected in [('nova-1-training.zip',reg['training_archive_sha256']),('nova-1-unseen.zip',reg['unseen_archive_sha256'])]:
            path=ROOT/'tests/fixtures'/name;assert digest(path)==expected
            with zipfile.ZipFile(path) as z:
                for row in json.loads(z.read('manifest.json')):
                    if row['style'] in reg['qualification_styles']:
                        manifest.append(row);out.writestr(row['path'],z.read(row['path']))
        assert len(manifest)==12
        out.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
    protocol=DOC/'qualification-protocol.json';write(protocol,{'v10':'my-team/team.py','nova':str(candidate.relative_to(ROOT))},reg['qualification'],reg['qualification_styles'],'qualification',archive,False)
    # Sources are already fixed; commit before exposing any unseen outcomes.
    subprocess.run(['git','add','tools/nova','tools/benchmarks/run_nova.py','docs/nova-1','tests/test_nova.py','tests/fixtures/nova-1-qualification.zip','experiments/nova-1'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m','Freeze learned NOVA-1 policy before sealed 768-pair qualification'],cwd=ROOT,check=True)
    print('Frozen NOVA',digest(candidate),'starting principal qualification',flush=True)
    run(protocol,a.work/'qualification');q=assess(a.work/'qualification');save(DOC/'qualification-gates.json',q)
    confirmation=None
    if q['all_gates_pass']:
        protocol=DOC/'confirmation-protocol.json';write(protocol,{'v10':'my-team/team.py','nova':str(candidate.relative_to(ROOT))},reg['confirmation'],reg['qualification_styles'],'confirmation',archive,False)
        subprocess.run(['git','add',str(protocol)],cwd=ROOT,check=True);subprocess.run(['git','commit','-m','Register untouched NOVA-1 confirmation fixtures'],cwd=ROOT,check=True)
        run(protocol,a.work/'confirmation');confirmation=assess(a.work/'confirmation');save(DOC/'confirmation-gates.json',confirmation)
    decision={'status':'QUALIFIED_PENDING_APPROVAL' if q['all_gates_pass'] and confirmation and confirmation['all_gates_pass'] else 'RETAIN_V10_0',
        'promoted':False,'candidate_sha256':digest(candidate),'qualification_failed':[k for k,v in q['flags'].items() if not v],
        'confirmation_run':confirmation is not None,'confirmation_failed':[k for k,v in confirmation['flags'].items() if not v] if confirmation else [],
        'confirmation_cohort_remains_untouched':confirmation is None}
    save(DOC/'decision.json',decision);print(json.dumps(decision,indent=2),flush=True)
if __name__=='__main__':main()
