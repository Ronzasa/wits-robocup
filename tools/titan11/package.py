"""Preserve native evidence, diagnostic replays and exact data with a digest manifest."""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('Never replace an evidence archive.')
    entries={};excluded=[]
    for path in sorted(a.work.rglob('*')):
        if not path.is_file():continue
        relative=path.relative_to(a.work)
        if any(x in relative.parts for x in ('__pycache__','sources','opponents')):continue
        # Full 77MB training trace is reproducible; preserve its exact used
        # samples plus every native result and hash in the checked-in dataset.
        if relative==Path('training/traces.json.gz'):excluded.append({'path':str(relative),'reason':'Exact used features/labels and every native result exported without loss to checked-in training-sample artifact; full trace SHA in model-fit report.'});continue
        if relative==Path('previous-runtime.py'):continue
        if path.suffix not in ('.json','.jsonl','.log','.gz','.pstats','.csv','.md'):continue
        entries['work/'+relative.as_posix()]=path
    for path in sorted((ROOT/'docs/titan-11-intelligence').glob('*.json')):entries['docs/'+path.name]=path
    for name in ('titan-11-native-training-samples.json.gz','titan-11-intelligence-opponents.zip','titan-11-intelligence-training-league.zip'):
        path=ROOT/'tests/fixtures'/name;entries['fixtures/'+name]=path
    for path in sorted((ROOT/'experiments').glob('titan-11*/team.py')):entries['sources/'+path.parent.name+'/team.py']=path
    entries['sources/v10/team.py']=ROOT/'my-team/team.py'
    manifest={'schema':1,'scope':'Unaltered initial raw records, first-clean repeats, failed repeats, native timing/environment records and diagnostic evidence; no source re-execution or outcome filtering.','excluded':excluded,'files':{name:{'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size} for name,path in entries.items()}}
    with zipfile.ZipFile(a.out,'x',zipfile.ZIP_DEFLATED) as z:
        for name,path in entries.items():z.write(path,name)
        z.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(a.out) as z:
        assert z.testzip() is None
        for name,spec in manifest['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==spec['sha256'],name
        # Champion raw data from every formal stage must be present.
        for stage in sorted(a.work.iterdir()):
            if (stage/'raw/v10/matches.jsonl').exists():assert 'work/'+stage.name+'/raw/v10/matches.jsonl' in z.namelist()
    audit={'archive':str(a.out.relative_to(ROOT)),'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'bytes':a.out.stat().st_size,'files':len(entries),'all_manifest_digests_verified':True,'testzip_ok':True,'all_baseline_raw_records_present':True}
    (a.out.parent/'archive-audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
