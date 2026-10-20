"""Archive fresh evaluation, forensic diagnostics and report correction evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[2]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True)
    args=p.parse_args();work=args.work.resolve();doc=ROOT/'docs/original-architect'
    assert (doc/'decision.json').exists()
    archive=ROOT/'tests/fixtures/original-architect-evaluation-evidence.zip';assert not archive.exists()
    data={}
    for name in ('development','qualification','deadline-audit','harness-check'):
        source=work/name
        if source.exists():
            for f in sorted(source.rglob('*')):
                if f.is_file():data[name+'/'+str(f.relative_to(source))]=f.read_bytes()
    for pattern in ('*.log','*protocol.json','*before-fix.md'):
        for f in sorted(work.glob(pattern)):data['support/'+f.name]=f.read_bytes()
    for f in sorted(doc.iterdir()):
        if f.is_file():data['docs/'+f.name]=f.read_bytes()
    for f in sorted((ROOT/'tools/original_architect').glob('*')):
        if f.is_file():data['tools/'+str(f.relative_to(ROOT))]=f.read_bytes()
    for rel in ('tools/adaptive_architect/analyze.py','docs/adaptive-architect/results.md','tests/test_adaptive_reporting.py','tests/test_original_architect_statistics.py'):
        data['correction/'+rel]=(ROOT/rel).read_bytes()
    historical=ROOT/'tests/fixtures/adaptive-architect-native-evidence.zip'
    data['historical-archive-reference.json']=json.dumps({'path':str(historical.relative_to(ROOT)),
        'sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'immutable':True,'embedded_report_superseded_by_documented_live_correction':True},indent=2).encode()
    manifest={n:hashlib.sha256(v).hexdigest() for n,v in data.items()}
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for n,v in data.items():z.writestr(n,v)
        z.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,h in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    index={'archive':str(archive.relative_to(ROOT)),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'files':len(manifest),'bytes':archive.stat().st_size,'verified':'Archive CRC and all per-file SHA-256 entries.'}
    (doc/'evidence.json').write_text(json.dumps(index,indent=2)+'\n');print(json.dumps(index))


if __name__=='__main__':main()
