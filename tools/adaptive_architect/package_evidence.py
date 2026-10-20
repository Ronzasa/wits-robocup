"""Preserve the fresh cohort and public diagnostic probes with verified hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[2]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True)
    args=p.parse_args();work=args.work.resolve();doc=ROOT/'docs/adaptive-architect'
    assert (doc/'results.json').exists()
    archive=ROOT/'tests/fixtures/adaptive-architect-native-evidence.zip'
    assert not archive.exists()
    data={}
    for stage in ('development','diagnostic-probe','qualification'):
        source=work/stage
        if source.exists():
            for f in sorted(source.rglob('*')):
                if f.is_file():data[stage+'/'+str(f.relative_to(source))]=f.read_bytes()
    for pattern in ('*.log','*protocol.json'):
        for f in sorted(work.glob(pattern)):data['support/'+f.name]=f.read_bytes()
    for pattern in ('*.json','*.md'):
        for f in sorted(doc.glob(pattern)):data['docs/'+f.name]=f.read_bytes()
    for root in (ROOT/'tools/adaptive_architect',):
        for f in sorted(root.glob('*')):
            if f.is_file():data['tools/'+str(f.relative_to(ROOT))]=f.read_bytes()
    for f in (ROOT/'tools/benchmarks/run_adaptive_architect.py',ROOT/'tests/test_adaptive_architect.py'):
        data['tools/'+str(f.relative_to(ROOT))]=f.read_bytes()
    manifest={n:hashlib.sha256(v).hexdigest() for n,v in data.items()}
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for n,v in data.items():z.writestr(n,v)
        z.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(manifest)|{'manifest.json'}
        for n,h in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    index={'archive':str(archive.relative_to(ROOT)),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
           'bytes':archive.stat().st_size,'files':len(manifest),'verified':'Archive CRC and every SHA-256 entry.'}
    (doc/'evidence.json').write_text(json.dumps(index,indent=2)+'\n')
    print(json.dumps(index))


if __name__=='__main__':main()
