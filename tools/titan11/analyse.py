"""Public-trace tactical accounting for fixed diagnostic matches, not tournament inference."""
import argparse,gzip,json,math
from collections import Counter
from pathlib import Path

def analyse(game):
    trace=game['trace'];counts=Counter();pending=[];plans=[];loss=-100000;owner=None;restarts=[0];bounces=[];shots=[]
    for i,r in enumerate(trace):
        tick=r['tick'];x,y,vx,vy=r['ball'];team=0 if r['features'][3] else 1 if r['features'][4] else None
        if team is not None and team!=owner:
            if team==1 and owner==0:loss=tick
            owner=team
        for e in r['events']:
            if e['kind']=='goal':
                counts['goals_for' if e.get('team')==0 else 'goals_against']+=1
                if e.get('team')==1 and tick-loss<=80:counts['counter_concession_proxy']+=1
        if i and r['score']!=trace[i-1]['score']:restarts.append(i);owner=None
        if x<-25 and any(math.dist(q[1:3],(x,y))<=2.2 for q in r['opponents']):counts['opponent_danger_contact_ticks']+=1
        if r['shot_features'] is not None:
            shots.append({'tick':tick,'features':r['shot_features'],'goal_within_40_ticks':r.get('shot_label',0)})
        for entry in list(pending):
            recipient,passer,start=entry;outcome=None
            if r['last_touch']==recipient:outcome='intended_receiver_touch'
            elif r['last_touch'] is not None and r['last_touch']>=5:outcome='opponent_touch'
            elif any(e['kind']=='goal' for e in r['events']):outcome='goal_before_collection'
            elif r['last_touch'] not in (None,passer):outcome='other_teammate_touch'
            elif tick-start>52:outcome='no_touch_within_52_ticks'
            if outcome:plans.append({'start_tick':start,'end_tick':tick,'recipient':recipient,'outcome':outcome});counts['planned_'+outcome]+=1;pending.remove(entry)
        if r['plan_after'] is not None and r['plan_after']!=r['plan_before']:
            recipient,passer,_=r['plan_after'];pending.append((recipient,passer,tick));counts['planned_releases']+=1
        if i:
            previous=trace[i-1];px,py,pvx,pvy=previous['ball']
            for axis,pos,old,new in [('side',y,pvy,vy),('end',x,pvx,vx)]:
                bound=29.55 if axis=='side' else 49.55
                if abs(pos)>bound-2. and old*new<0. and abs(old)>3. and abs(abs(new/old)-.75)<.035 and r['last_touch']==previous['last_touch']:
                    future=trace[i+1:i+53];touch=next((q for q in future if q['last_touch']!=r['last_touch'] and q['last_touch'] is not None),None)
                    ours=r['last_touch'] is not None and r['last_touch']<5
                    own_recovery=touch is not None and touch['last_touch']<5
                    counts['wall_reflection_proxy']+=1
                    if ours:counts['own_wall_recovery_proxy']+=own_recovery;counts['own_wall_routes_proxy']+=1
                    bounces.append({'tick':tick,'axis':axis,'last_touch':r['last_touch'],'first_new_touch':None if touch is None else touch['last_touch'],'own_recovery_within_52_ticks':own_recovery if ours else None})
    counts['planned_pending_at_trace_end']=len(pending)
    restarts_out=[]
    for index in restarts:
        start=trace[index];window=trace[index:min(len(trace),index+121)]
        first=next((e for r in window for e in r['events'] if e['kind']=='kick'),None)
        restarts_out.append({'tick':start['tick'],'first_kick_team':None if first is None else first.get('team'),'goals_for_within_120_ticks':max((r['score'][0]-start['score'][0] for r in window),default=0),'goals_against_within_120_ticks':max((r['score'][1]-start['score'][1] for r in window),default=0),'control_fraction_120_ticks':sum(r['features'][3] for r in window)/len(window)})
    counts['restart_sequences']=len(restarts_out);counts['forecast_goalbound_shots']=len(shots);counts['forecast_shot_goals_within_40_ticks']=sum(s['goal_within_40_ticks'] for s in shots)
    return {'style':game['style'],'seed':game['seed'],'side':game['side'],'kickoff':game['kickoff'],'counts':dict(counts),'planned_receptions':plans,'restarts':restarts_out,'walls':bounces,'shots':shots,'native_result':game['result']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--challenger',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('Preserve analysis.')
    data={}
    for name,path in [('v10',a.baseline),('titan11',a.challenger)]:
        games=json.load(gzip.open(path,'rt'));records=[analyse(g) for g in games];total=Counter()
        for r in records:total.update(r['counts'])
        data[name]={'matches':len(records),'totals':dict(total),'per_fixture':records}
    output={'scope':'Fixed paired diagnostic public traces. Counter/danger, kickoff-window and wall-reflection counters are explicit proxies, not full-cohort native statistics or causal labels. Reflections require boundary proximity, unchanged last touch and approximately 0.75 normal restitution; body contacts can still confound this inference. No result used for source tuning.','data':data}
    a.out.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({k:v['totals'] for k,v in data.items()},indent=2))
if __name__=='__main__':main()
