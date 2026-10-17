"""Package unaltered TITAN-11 evidence and a per-file SHA256 manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('work',type=Path)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():p.error('Do not overwrite prior evidence.')
    records=[]
    # Full native records, including failures and first-clean repeats. Duplicate
    # controller copies are already frozen in the repository and hash manifests.
    paths=[x for x in args.work.rglob('*') if x.is_file()
           and x.suffix in ('.json','.jsonl','.log','.pstats')
           and not any(k in x.relative_to(args.work).parts for k in ('opponents','sources','strong-opponents','reference-opponents'))
           and x.name!='worst-decisions.json']
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in sorted(paths):
            name=path.relative_to(args.work).as_posix()
            data=path.read_bytes()
            records.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
            z.writestr(name,data)
        z.writestr('MANIFEST.json',json.dumps(records,indent=2)+'\n')
    print('Saved',len(records),'records;',args.out.stat().st_size,'bytes;',hashlib.sha256(args.out.read_bytes()).hexdigest())


if __name__=='__main__':main()
