import sys, multiprocessing as mp, json, collections
sys.path.insert(0,'/home/claude/wits-robocup/experiments/tactics/harness')
import common; from common import soccer
T,O=sys.argv[1],sys.argv[2]; s0,s1=int(sys.argv[3]),int(sys.argv[4]); tag=sys.argv[5]
def u(a):
    seed,side=a; p=f'rp/{tag}_{seed}_{side}.json.gz'
    x,y=(T,O) if side==0 else (O,T)
    m=soccer.play_match(x,y,seed=seed,kickoff_team=side,max_ticks=2400,record_replay=p)
    r=soccer.read_replay(p); me=side
    g=[(e['tick'],'us' if e['team']==me else 'them') for e in r['events'] if e['kind']=='goal']
    return seed,side,[m.score[me],m.score[1-me]],g
if __name__=='__main__':
    with mp.Pool(2) as p: R=p.map(u,[(s,d) for s in range(s0,s1) for d in (0,1)])
    json.dump(R,open(f'scan_{tag}.json','w'))
    first=collections.Counter(); out=collections.Counter()
    for seed,side,sc,g in R:
        res='W' if sc[0]>sc[1] else 'L' if sc[0]<sc[1] else 'D'
        f=g[0][1] if g else 'none'; first[(f,res)]+=1
    print('first scorer, result:',sorted(first.items()))
    print('W/D/L',collections.Counter('W' if r[2][0]>r[2][1] else 'L' if r[2][0]<r[2][1] else 'D' for r in R))
