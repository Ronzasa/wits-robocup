"""Public-observation diagnostics and native-outcome learning traces (not timing evidence)."""
import argparse,cProfile,gzip,hashlib,importlib.util,json,math,pstats,sys,zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'student-sdk'))
from soccer import play_match

def load(path):
    spec=importlib.util.spec_from_file_location('diagnostic_policy',path); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def features(obs):
    x,y=obs.ball.position; ours=obs.ball.controlling_team==0;theirs=obs.ball.controlling_team==1
    near=lambda ps: min((math.dist(p.position,(x,y)) for p in ps),default=100.)
    return [1.,x/50.,abs(y)/30.,float(ours),float(theirs),min(20.,near(obs.opponents))/20.,min(20.,near(obs.my_players))/20.,sum(p.position[0]<x-4 for p in obs.my_players[1:])/4.]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=ROOT/'my-team/team.py');p.add_argument('--out',type=Path,required=True);p.add_argument('--training',action='store_true');args=p.parse_args()
    if args.out.exists():p.error('Preserve evidence; choose a fresh output directory.')
    args.out.mkdir(parents=True);reg=json.loads((ROOT/'docs/titan-11-intelligence/registration.json').read_text())
    archive=ROOT/'tests/fixtures/titan-11-intelligence-opponents.zip'
    with zipfile.ZipFile(archive) as z:
        for style in reg['training_pool']:
            dest=args.out/'opponents'/style/'team.py';dest.parent.mkdir(parents=True);dest.write_bytes(z.read(style+'/team.py'))
    module=load(args.source);allrows=[];summary=[];events=Counter();cases=[]
    games=[(style,seed,side,kick) for style in (reg['training_pool'] if args.training else ['v10-press','v10-counter']) for seed in reg['development'][:(2 if args.training else 1)] for side in (0,1) for kick in ((0,1) if args.training else (0,))]
    profiler=cProfile.Profile()
    for index,(style,seed,side,kick) in enumerate(games):
        class Trace(module.Guardiola2011):
            def act(self,obs):
                before=self._receive_plan; action=super().act(obs)
                ev=[dict(e) for e in obs.events]
                for e in ev:events[e.get('kind','?')]+=1
                shot=None
                for q in obs.my_players:
                    a=action.players[q.id]
                    if a.kick_direction is None:continue
                    v=self._requested_velocity(*obs.ball.velocity,(a.kick_direction,a.kick_power))
                    launch=self._carrier_contact((q.id,*q.position,*q.velocity),*obs.ball.position,*v,a.movement)
                    goal=self._goal_path(launch) if launch else None
                    if goal and self._pass_plan is None and self._bank_plan is None:
                        flight,gy,speed=goal[1];keeper=obs.opponents[0]
                        shot=[1.,flight/2.,abs(gy)/6.,math.dist(keeper.position,(49.55,gy))/15.,(keeper.velocity[1]*(gy-keeper.position[1]))/60.,speed/30.]
                row={'tick':obs.tick,'score':list(obs.score),'ball':[*obs.ball.position,*obs.ball.velocity],'holder':obs.ball.controlling_player,'last_touch':obs.ball.last_touch,
                    'friends':[[q.id,*q.position,*q.velocity,q.kick_cooldown_ticks] for q in obs.my_players],
                    'opponents':[[q.id,*q.position,*q.velocity,q.kick_cooldown_ticks] for q in obs.opponents],
                    'kickers':[q.id for q in obs.my_players if obs.can_kick(q.id)],'events':ev,'features':features(obs),
                    'actions':{str(k):v.as_dict() for k,v in action.players.items()},'plan_before':before,'plan_after':self._receive_plan,'shot_features':shot}
                trace.append(row);return action
        trace=[];c=Trace(); teams=[c,str(args.out/'opponents'/style/'team.py')]
        if side:teams.reverse()
        # Profile only the first diagnostic fixture; never use its timings for gates.
        if index==0:profiler.enable()
        result=play_match(*teams,seed=seed,kickoff_team=side if kick==0 else 1-side,config_path=str(ROOT/'configs/default.toml'),max_ticks=2400,per_decision_timeout_ms=20.).result
        if index==0:profiler.disable()
        score=result['score'];target=3. if score[side]>score[1-side] else 1. if score[side]==score[1-side] else 0.
        for i,row in enumerate(trace):
            row['value_label']=target
            if row['shot_features'] is not None:
                future=trace[i+1:min(len(trace),i+41)]
                row['shot_label']=int(any(r['score'][0]>row['score'][0] for r in future))
            if row['plan_before'] and row['plan_after'] is None and row['last_touch']!=row['plan_before'][0] and len(cases)<24:
                cases.append({'style':style,'seed':seed,'side':side,'kickoff':kick,'reason':'reception plan cancelled before intended touch','frames':trace[max(0,i-4):i+1]})
        allrows.append({'style':style,'seed':seed,'side':side,'kickoff':kick,'result':result,'trace':trace})
        summary.append({'style':style,'seed':seed,'side':side,'kickoff':kick,'points':target,'result':result})
        if (index+1)%4==0:print('Diagnostic fixtures',index+1,'/',len(games),flush=True)
    profiler.dump_stats(str(args.out/'diagnostic.pstats'));stats=pstats.Stats(profiler)
    report={'source':str(args.source),'sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'scope':'instrumented public diagnostics; overhead included, never reliability gate evidence','fixtures':summary,'event_counts':dict(events),'reception_cancellation_cases':cases,
        'profile_top':[{'method':k[2],'calls':v[1],'self_s':v[2],'cumulative_s':v[3]} for k,v in sorted(stats.stats.items(),key=lambda x:x[1][3],reverse=True)[:30]]}
    with gzip.open(args.out/'traces.json.gz','wt') as f:json.dump(allrows,f)
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'events':dict(events),'cancelled_cases':len(cases),'matches':len(summary)}),flush=True)
if __name__=='__main__':main()
