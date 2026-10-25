import sys, multiprocessing as mp, statistics as S
sys.path.insert(0,'/home/claude/wits-robocup/experiments/tactics/harness')
import common; from common import soccer
C='/home/claude/wits-robocup/experiments/tactics/candidates/champion_candidate.py'
def u(a):
    t,seed,side=a; x,y=(t,C) if side==0 else (C,t)
    m=soccer.play_match(x,y,seed=seed,kickoff_team=side,max_ticks=2400); me,th=(0,1) if side==0 else (1,0)
    return common.points(m.score[me],m.score[th]), m.score[me]-m.score[th], m.result['stats'][me]['fouls'], m.result['stats'][me]['policy_timeouts']
if __name__=='__main__':
    s0,s1=int(sys.argv[1]),int(sys.argv[2]); files=sys.argv[3:]
    with mp.Pool(2) as p:
        ref=None
        for f in files:
            R=p.map(u,[(f,s,d) for s in range(s0,s1) for d in (0,1)])
            pts=[r[0] for r in R]
            print(f.split('/')[-1],'n',len(R),'pts',round(S.mean(pts),3),'GD',round(S.mean(r[1] for r in R),3),'fouls',sum(r[2] for r in R),'timeouts',sum(r[3] for r in R),flush=True)
            if ref is None: ref=pts
            else:
                d=[a-b for a,b in zip(pts,ref)]; m=S.mean(d); se=S.stdev(d)/len(d)**.5
                print('   paired vs first file: d',round(m,3),'95% CI',round(m-1.96*se,3),round(m+1.96*se,3))
