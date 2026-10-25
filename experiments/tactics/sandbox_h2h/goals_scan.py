import sys, multiprocessing as mp, collections, json, gzip, os
sys.path.insert(0,'/home/claude/wits-robocup/experiments/tactics/harness')
import common; from common import soccer
C='/home/claude/wits-robocup/experiments/tactics/candidates/champion_candidate.py'
def load(p):
    return soccer.read_replay(p)
def u(a):
    seed,ko=a; p=f'rp/c_{seed}_{ko}.json.gz'
    m=soccer.play_match(C,C,seed=seed,kickoff_team=ko,max_ticks=2400,record_replay=p)
    d=load(p); d=d if isinstance(d,dict) else d.__dict__; ev=[e for e in d['events'] if e['kind'] not in ('kick',)]
    return seed,ko,tuple(m.score),ev
if __name__=='__main__':
    with mp.Pool(2) as p: R=p.map(u,[(s,k) for s in range(30500,30530) for k in (0,1)])
    kinds=collections.Counter(e['kind'] for r in R for e in r[3]); print(kinds)
    json.dump(R,open('goals_scan.json','w'))
