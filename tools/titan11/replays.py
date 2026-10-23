"""Native development replays with public tactical diagnostics; never strength evidence."""
import argparse,gzip,hashlib,importlib.util,json,math,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'student-sdk'));sys.path.insert(0,str(ROOT/'tools/benchmarks'))
from soccer import play_match
from benchmark import points,candidate_score

def load(path):
    spec=importlib.util.spec_from_file_location('replayed_titan',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def replay(source,row,out,label):
    module=load(source);frames=[];counts=Counter();episodes=[];last_owner=None;loss=-10000;receptions=[];pending=None
    class Trace(module.Guardiola2011):
        def act(self,obs):
            nonlocal last_owner,loss,pending
            before=self._receive_plan;a=super().act(obs)
            holder=obs.ball.controlling_team
            if holder is not None and holder!=last_owner:
                if holder==1 and last_owner==0:loss=obs.tick
                last_owner=holder
            for e in obs.events:
                counts[e['kind']]+=1
                if e['kind']=='goal' and e.get('team')==1:
                    counts['counter_goal_within_80_ticks_of_control_loss']+=obs.tick-loss<=80
                    episodes.append({'reason':'goal conceded','tick':obs.tick,'counter_proxy':obs.tick-loss<=80,'frames':frames[-40:]})
            if pending is not None:
                receiver,passer,start,origin=pending
                if obs.ball.last_touch==receiver:
                    receptions.append({'start':start,'end':obs.tick,'receiver':receiver,'outcome':'collected','origin':origin});pending=None
                elif obs.ball.last_touch not in (None,passer) or obs.tick-start>52:
                    receptions.append({'start':start,'end':obs.tick,'receiver':receiver,'outcome':'opponent' if obs.ball.last_touch is not None and obs.ball.last_touch>=5 else 'uncollected','origin':origin});pending=None
            if self._receive_plan is not None and self._receive_plan!=before:
                receiver,passer,_=self._receive_plan
                if pending is None:pending=(receiver,passer,obs.tick,list(obs.ball.position))
            native_shot=None
            for p in obs.my_players:
                command=a.players[p.id]
                if command.kick_direction is None:continue
                v=self._requested_velocity(*obs.ball.velocity,(command.kick_direction,command.kick_power))
                launch=self._carrier_contact((p.id,*p.position,*p.velocity),*obs.ball.position,*v,command.movement)
                goal=self._goal_path(launch) if launch is not None else None
                if goal is not None and self._pass_plan is None and self._bank_plan is None:
                    native_shot={'flight':goal[1][0],'goal_y':goal[1][1],'end_speed':goal[1][2]};counts['forecast_goalbound_shots']+=1
            x,y=obs.ball.position
            frame={'tick':obs.tick,'score':list(obs.score),'ball':[*obs.ball.position,*obs.ball.velocity],'holder':obs.ball.controlling_player,'last_touch':obs.ball.last_touch,
                'friends':[[p.id,*p.position,*p.velocity,p.kick_cooldown_ticks] for p in obs.my_players],'opponents':[[p.id,*p.position,*p.velocity,p.kick_cooldown_ticks] for p in obs.opponents],
                'actions':{str(k):v.as_dict() for k,v in a.players.items()},'plan_before':before,'plan_after':self._receive_plan,'selected':getattr(self,'_ti_selected','v10'),'defenders':getattr(self,'_ti_defence_ids',()),'shot':native_shot,'events':[dict(e) for e in obs.events]}
            if getattr(self,'_ti_selected','v10')!='v10':counts['selected_'+self._ti_selected]+=1
            if abs(y)>obs.field.height/2-4:counts['boundary_ticks']+=1
            if x< -25 and any(math.dist(p.position,obs.ball.position)<obs.field.kick_range for p in obs.opponents):counts['opponent_danger_contact_ticks']+=1
            frames.append(frame);return a
    c=Trace();side=row['candidate_slot'];teams=[c,row['opponent']]
    if side:teams.reverse()
    result=play_match(*teams,seed=row['seed'],kickoff_team=side if row['candidate_takes_kickoff'] else 1-side,config_path=str(ROOT/'configs/default.toml'),max_ticks=2400,per_decision_timeout_ms=20.,record_replay=str(out/(label+'.native.json')),record_debug=True).result
    # Label shot conversion from subsequent publicly observed score changes.
    shots=[]
    for i,f in enumerate(frames):
        if f['shot'] is not None:shots.append({**f['shot'],'tick':f['tick'],'goal_within_two_seconds':any(q['score'][0]>f['score'][0] for q in frames[i+1:i+41])})
    report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'original_fixture':row,'result':result,'counts':dict(counts),'receptions':receptions,'shots':shots,'episodes':episodes,
        'scope':'Instrumented development reproduction. Counter goal = observed opposing goal <=80 ticks after observed control loss; this is a proxy, not official attribution. Shot quality = documented flight/end speed/goal aperture, not calibrated xG.'}
    with gzip.open(out/(label+'.frames.json.gz'),'wt') as f:json.dump(frames,f)
    (out/(label+'.report.json')).write_text(json.dumps(report,indent=2)+'\n')
    native=out/(label+'.native.json')
    if native.exists():
        with gzip.open(str(native)+'.gz','wb') as f:f.write(native.read_bytes())
        native.unlink() # Exact lossless compressed native replay retained.
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--name',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('Preserve replays.')
    a.out.mkdir(parents=True);meta=json.loads((a.run/'metadata.json').read_text());source=Path(meta['original_sources'][a.name]);
    def rows(n):return {r['fixture_id']:r for r in [json.loads(s) for s in (a.run/'accepted'/n/'matches.jsonl').read_text().splitlines()]}
    b,c=rows('v10'),rows(a.name);paired=[(points(c[k])-points(b[k]),sum(candidate_score(c[k]))-sum(candidate_score(b[k])),k) for k in sorted(c)]
    keys=[max(paired)[2],min(paired)[2]]
    summary=[]
    for i,key in enumerate(dict.fromkeys(keys)):
        for name,path,row in [('baseline',ROOT/'my-team/team.py',b[key]),('challenger',source,c[key])]:
            label=str(i)+'-'+name;report=replay(path,row,a.out,label)
            summary.append({'label':label,'fixture_id':key,'counts':report['counts'],'score':report['result']['score'],'original_score':row['result']['score'],'receptions':Counter(x['outcome'] for x in report['receptions']),'shots':len(report['shots']),'two_second_shot_goals':sum(x['goal_within_two_seconds'] for x in report['shots'])})
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
