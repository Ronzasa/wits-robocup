import sys, multiprocessing as mp, statistics as S, json
sys.path.insert(0,'/home/claude/wits-robocup/experiments/tactics/harness')
import common; from common import soccer
H='/home/claude/wits-robocup/experiments/tactics/opponents/'; D='/home/claude/sandbox/'
OPP={'champion_original':common.OPPONENTS['champion_original'],'lock_no_breaker':common.OPPONENTS['lock_no_breaker'],'press_formation':common.OPPONENTS['press_formation'],
 'dribbler':common.OPPONENTS['dribbler'],'ball_chaser':'ball_chaser','structured_attack':'structured_attack','balanced':'balanced','man_marking':'man_marking','possession':'possession','tactical':'tactical',
 'candidate':D+'champion_candidate.py','challenger':D+'challenger_stiff_wall.py','bunker_kc':D+'bunker_kc.py','bunker_shot':D+'bunker_shot.py','team12':D+'team12_clean_broadwall_stiff.py',
 'tap_drive':H+'tap_drive.py','corner_shooter':H+'corner_shooter.py'}
def u(a):
    t,name,seed,side=a; o=OPP[name]; x,y=(t,o) if side==0 else (o,t)
    m=soccer.play_match(x,y,seed=seed,kickoff_team=side,max_ticks=2400); me,th=(0,1) if side==0 else (1,0)
    st=m.result['stats'][me]
    return name,common.points(m.score[me],m.score[th]),m.score[me],m.score[th],st['fouls'],st['policy_timeouts'],st['policy_errors']
if __name__=='__main__':
    t=sys.argv[1]; s0,s1=int(sys.argv[2]),int(sys.argv[3]); out=sys.argv[4]; names=sys.argv[5].split(',') if len(sys.argv)>5 else list(OPP)
    jobs=[(t,n,s,d) for n in names for s in range(s0,s1) for d in (0,1)]
    with mp.Pool(2) as p: R=p.map(u,jobs,chunksize=1)
    json.dump(R,open(out,'w'))
    tot=[]
    for n in names:
        r=[x for x in R if x[0]==n]; tot+=[x[1] for x in r]
        print(f'{n:18s} n={len(r):3d} pts {S.mean(x[1] for x in r):.2f} GF {S.mean(x[2] for x in r):.2f} GA {S.mean(x[3] for x in r):.2f} W/D/L {sum(x[1]==3 for x in r)}/{sum(x[1]==1 for x in r)}/{sum(x[1]==0 for x in r)} fouls {sum(x[4] for x in r)} TO {sum(x[5] for x in r)} err {sum(x[6] for x in r)}')
    print('ALL pts',round(S.mean(tot),3),'n',len(tot))
