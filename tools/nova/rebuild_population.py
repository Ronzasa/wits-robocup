"""Rebuild every frozen policy snapshot; do not overwrite original evidence."""
import argparse,hashlib,json
from pathlib import Path
from build import build
ROOT=Path(__file__).resolve().parents[2]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    assert not a.out.exists();a.out.mkdir(parents=True)
    total=0
    for path in sorted((ROOT/'docs/nova-1').glob('generation-*-registration.json')):
        rows=json.loads(path.read_text())['population']
        for q in rows:
            v=q['vector'];params={'config':v[:8],'weights':v[8:]+[.4],
                'framework':'r4' if q['name'].startswith('g00-') else 'r5' if q['name'].startswith('g01-') else 'r6'}
            code=build(params,True);assert hashlib.sha256(code.encode()).hexdigest()==q['sha256'],q['name']
            dest=a.out/q['name']/'team.py';dest.parent.mkdir();dest.write_text(code);total+=1
    print('Reconstructed and hash-verified',total,'standalone policies.')
if __name__=='__main__':main()
