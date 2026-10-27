import sys,json,collections,math
sys.path.insert(0,'/home/claude/wits-robocup/experiments/tactics/harness')
import common; from common import soccer
tag=sys.argv[1]; R=json.load(open(f'scan_{tag}.json'))
rows=[]; cls=collections.Counter()
for seed,side,sc in R:
    r=soccer.read_replay(f'rp/{tag}_{seed}_{side}.json.gz',include_frames=True); fr=r['frames']; sg=1 if side==0 else -1
    me=side; ev=r['events']
    for e in ev:
        if e['kind']!='goal' or e['team']==me: continue          # conceded goals only
        t=e['tick']; og=e['own_goal']
        ks=[k for k in ev if k['kind']=='kick' and k['team']!=me and k['tick']<=t and k['tick']>=t-60]
        last=ks[-1] if ks else None
        mk=[k for k in ev if k['kind']=='kick' and k['team']==me and t-12<=k['tick']<=t]
        if last is None: rows.append((seed,side,t,'no attacker kick in 60 ticks',og)); cls['no kick']+=1; continue
        f=fr[last['tick']]; b=f['ball_position']; bx,by=b['x']*sg,b['y']*sg
        dx,dy=last['direction']['x']*sg,last['direction']['y']*sg
        # where does the line cross the goal line x=-50 ?
        gy=None
        if dx<-0.05: gy=by+dy*(-50-bx)/dx
        dist=math.hypot(bx+50,0)
        wall=sorted(round(fr[last['tick']]['players'][i]['position']['y']*1,1) for i in range(5*me+0,5*me+4))
        kind='own-goal deflection' if og else ('point-blank (<=8 from line)' if bx<-42 else 'mid-range shot' if bx<-30 else 'long shot')
        if not og and abs(by)>7 and dx<-0.05 and abs(gy or 0)<7: kind+=' from the wing'
        cls[kind]+=1
        rows.append((seed,side,t,kind,og,round(bx,1),round(by,1),round(gy,1) if gy is not None else None,round(last['power'],2),len(mk)))
print(len(rows),'conceded goals in',len(R),'matches'); 
for k,v in cls.most_common(): print(' ',v,k)
ys=[r[7] for r in rows if len(r)>7 and r[7] is not None and not r[4]]
print('goal-line crossing y of shots (abs) histogram:',collections.Counter(min(int(abs(y)),9) for y in ys))
print('seconds of the match when conceded:',collections.Counter(r[2]//480 for r in rows))
print('MONSTER touched ball within 12 ticks before goal:',sum(1 for r in rows if len(r)>9 and r[9]>0),'of',len(rows))
for r in rows[:14]: print(r)
