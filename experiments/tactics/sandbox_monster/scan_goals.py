import sys, multiprocessing as mp, json, collections
sys.path.insert(0,'/home/claude/wits-robocup/experiments/tactics/harness')
import common; from common import soccer
T=sys.argv[1]; O=sys.argv[2]; s0,s1=int(sys.argv[3]),int(sys.argv[4]); tag=sys.argv[5]
def u(a):
    seed,side=a; p=f'rp/{tag}_{seed}_{side}.json.gz'
    x,y=(T,O) if side==0 else (O,T)
    m=soccer.play_match(x,y,seed=seed,kickoff_team=side,max_ticks=2400,record_replay=p)
    return seed,side,[m.score[side],m.score[1-side]]
if __name__=='__main__':
    with mp.Pool(2) as p: R=p.map(u,[(s,d) for s in range(s0,s1) for d in (0,1)])
    json.dump(R,open(f'scan_{tag}.json','w')); print(len(R),'matches; pts', sum(3 if r[2][0]>r[2][1] else 1 if r[2][0]==r[2][1] else 0 for r in R)/len(R))
