"""Fit compact native-outcome value and shot models; report held-out-seed calibration."""
import argparse,gzip,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]

def sigmoid(x):return 1/(1+np.exp(-np.clip(x,-30,30)))

def fit(x,y,logistic=False):
    reg=np.eye(x.shape[1])*.5;reg[0,0]=.02
    if not logistic:return np.linalg.solve(x.T@x+reg,x.T@y)
    w=np.zeros(x.shape[1])
    for _ in range(40):
        p=sigmoid(x@w);v=np.maximum(p*(1-p),.001)
        step=np.linalg.solve(x.T@(x*v[:,None])+reg,x.T@(y-p)-reg@w)
        w+=step
        if np.linalg.norm(step)<1e-8:break
    return w

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--traces',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('Preserve training evidence.')
    a.out.mkdir(parents=True);games=json.load(gzip.open(a.traces,'rt'));seeds=sorted({g['seed'] for g in games});assert len(seeds)>=2
    records={'value':[],'shot':[]}
    for game in games:
        for r in game['trace']:
            if r['tick']%40==0:records['value'].append((game['seed'],r['features'],r['value_label']))
            if r['shot_features'] is not None:records['shot'].append((game['seed'],r['shot_features'],r['shot_label']))
    report={'trace_sha256':hashlib.sha256(a.traces.read_bytes()).hexdigest(),'train_seed':seeds[0],'heldout_calibration_seeds':seeds[1:],
        'scope':'Native labels on public v10 states. Shot label = goal within next 40 observations, a two-second conversion proxy, not official xG. Held-out calibration is descriptive; do not claim general calibrated probability. Policy selection uses separate native matches.'}
    params={}
    for name,rows in records.items():
        train=[r for r in rows if r[0]==seeds[0]];test=[r for r in rows if r[0]!=seeds[0]]
        assert train and test,(name,len(train),len(test))
        x=np.asarray([r[1] for r in train]);y=np.asarray([r[2] for r in train]);tx=np.asarray([r[1] for r in test]);ty=np.asarray([r[2] for r in test]);log=name=='shot'
        w=fit(x,y,log);pred=sigmoid(tx@w) if log else np.clip(tx@w,0,3)
        report[name]={'train_samples':len(train),'heldout_samples':len(test),'heldout_mse_or_brier':float(np.mean((pred-ty)**2)),
            'constant_train_mean_mse_or_brier':float(np.mean((np.mean(y)-ty)**2)),'heldout_label_mean':float(np.mean(ty)),'predicted_mean':float(np.mean(pred)),
            'bins':[{'low':low,'high':high,'n':int(np.sum((pred>=low)&(pred<high))),'predicted':float(np.mean(pred[(pred>=low)&(pred<high)])) if np.any((pred>=low)&(pred<high)) else None,'observed':float(np.mean(ty[(pred>=low)&(pred<high)])) if np.any((pred>=low)&(pred<high)) else None} for low,high in ([(0,.25),(.25,.5),(.5,.75),(.75,1.01)] if log else [(0,1),(1,2),(2,3.01)])]}
        # Deployment fit uses all development training labels only, including
        # calibration subset; the final competition seeds remain untouched.
        w=fit(np.asarray([r[1] for r in rows]),np.asarray([r[2] for r in rows]),log)
        params[name+'_weights']=[round(float(v),9) for v in w]
    (a.out/'parameters.json').write_text(json.dumps(params,indent=2)+'\n');(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
