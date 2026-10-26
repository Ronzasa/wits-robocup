import sys, multiprocessing as mp, statistics as S, collections
sys.path.insert(0,'/home/claude/wits-robocup/experiments/tactics/harness')
import common; from common import soccer
def u(a):
    t,opp,seed,side=a; x,y=(t,opp) if side==0 else (opp,t)
    m=soccer.play_match(x,y,seed=seed,kickoff_team=side,max_ticks=2400); me,th=(0,1) if side==0 else (1,0)
    st=m.result['stats'][me]
    return m.score[me],m.score[th],st['fouls'],st['policy_timeouts']
if __name__=='__main__':
    s0,s1=int(sys.argv[1]),int(sys.argv[2]); opps=sys.argv[3].split(','); teams=sys.argv[4:]
    with mp.Pool(2) as p:
        for o in opps:
            for t in teams:
                R=p.map(u,[(t,o,s,d) for s in range(s0,s1) for d in (0,1)])
                g=[r[0] for r in R]
                print(o.split('/')[-1],'|',t.split('/')[-1],'n',len(R),'goals/match',round(S.mean(g),2),'P(>=1)',round(sum(x>=1 for x in g)/len(g),2),'P(>=2)',round(sum(x>=2 for x in g)/len(g),2),'conceded',round(S.mean(r[1] for r in R),2),'fouls',sum(r[2] for r in R),'timeouts',sum(r[3] for r in R),flush=True)
