"""Archive immutable native evidence and verify every retained byte."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[2]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True)
    args=p.parse_args();work=args.work.resolve()
    doc=ROOT/'docs/titan-v11'
    assert (doc/'results.json').exists()
    archive=ROOT/'tests/fixtures/titan-v11-native-evidence.zip'
    assert not archive.exists(), 'Never replace evidence.'
    data={}
    for stage in ('development','interrupted-development'):
        source=work/stage
        if not source.exists():continue
        for f in sorted(source.rglob('*')):
            if f.is_file():data[stage+'/'+str(f.relative_to(source))]=f.read_bytes()
    for f in sorted(work.glob('*.log')):data['logs/'+f.name]=f.read_bytes()
    for f in sorted(doc.glob('*.json')):data['docs/'+f.name]=f.read_bytes()
    for f in sorted(doc.glob('*.md')):data['docs/'+f.name]=f.read_bytes()
    # Include the exact assembly fragment and tools used for independent review.
    paths=[ROOT/'tools/titan_v11/build.py',ROOT/'tools/titan_v11/tactics.pyfrag',
           ROOT/'tools/titan_v11/register.py',ROOT/'tools/titan_v11/analyze.py',
           ROOT/'tools/benchmarks/run_titan_v11.py',ROOT/'tests/test_titan_v11.py',ROOT/'tests/test_titan_v11_statistics.py']
    for f in paths:data['tools/'+str(f.relative_to(ROOT))]=f.read_bytes()
    manifest={name:hashlib.sha256(value).hexdigest() for name,value in data.items()}
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for name,value in data.items():z.writestr(name,value)
        z.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(manifest)|{'manifest.json'}
        for name,digest in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
    index={'archive':str(archive.relative_to(ROOT)),
           'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
           'bytes':archive.stat().st_size,'files':len(manifest),
           'verified':'Archive CRC and every SHA-256 manifest entry.'}
    (doc/'evidence.json').write_text(json.dumps(index,indent=2)+'\n')
    print(json.dumps(index))


if __name__=='__main__':main()
