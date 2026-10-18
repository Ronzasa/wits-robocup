"""Losslessly export the exact native training labels/features used by train.py."""
import argparse,gzip,hashlib,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('traces',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('Preserve dataset.')
    games=json.load(gzip.open(a.traces,'rt'));samples=[];summaries=[]
    for g in games:
        thin=[]
        for r in g['trace']:
            if r['tick']%40==0 or r['shot_features'] is not None:
                thin.append({k:r[k] for k in ('tick','features','value_label','shot_features','shot_label') if k in r})
        samples.append({k:g[k] for k in ('seed','side','style','kickoff')}|{'trace':thin})
        summaries.append({k:g[k] for k in ('seed','side','style','kickoff','result')})
    payload={'original_trace_sha256':hashlib.sha256(a.traces.read_bytes()).hexdigest(),'scope':'Every exact feature/label used by native model fitting, retained without sampling beyond original train.py selection. Full public trace can be regenerated with diagnose.py --training.','games':samples,'native_results':summaries}
    with gzip.open(a.out,'wt') as f:json.dump(payload,f)
    print(str(a.out),hashlib.sha256(a.out.read_bytes()).hexdigest())
if __name__=='__main__':main()
