"""Replay the first clean success, or first native launch if none succeeded."""
import argparse,hashlib,json,sys
from collections import deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'student-sdk'))
sys.path.insert(0,str(ROOT/'tools/benchmarks'))
sys.path.insert(0,str(ROOT/'tools'))
from soccer import runner
from benchmark import run_fixture
from physics_tactics.telemetry import Telemetry


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();stage=a.stage.resolve();proofs={}
    for name in ('ambush','wall-brake','rebound-shot'):
        metric='rebound-shot_rebound_goals' if name=='rebound-shot' else name+'_collected'
        success_metric=metric;selection='first clean success'
        candidates=[]
        for line in (stage/'raw'/name/'matches.jsonl').read_text().splitlines():
            row=json.loads(line)
            if row['physics_tactics']['counts'].get(metric,0) and all(s['policy_errors']==s['policy_timeouts']==0 for s in row['result']['stats']):
                candidates.append(row)
        if not candidates:
            for line in (stage/'raw'/name/'matches.jsonl').read_text().splitlines():
                row=json.loads(line)
                if row['physics_tactics']['counts'].get(name+'_native_kicks',0) and all(s['policy_errors']==s['policy_timeouts']==0 for s in row['result']['stats']):
                    candidates.append(row)
            selection='first clean native launch attempt'
        if not candidates:
            proofs[name]={'available':False,'reason':'No observed clean native success in this stage.'}
            continue
        row=candidates[0]
        source=stage/'sources'/name/'team.py'
        fixture={k:row[k] for k in ('opponent','seed','candidate_slot','candidate_takes_kickoff','split')}
        fixture.update({'team':str(source),'opponent':str(stage/'opponents'/Path(row['opponent']).parent.name/'team.py'),
                        'config_path':str(ROOT/'configs/default.toml'),'config_hash':'372990895c7eca2a'})
        attempts=[]
        for attempt in (1,2):
            telemetry=Telemetry();history=deque(maxlen=60);window=None;after=0;index=0
            original=runner._decide
            def observed(controller,obs):
                nonlocal index,window,after
                slot=index%2;index+=1
                old=getattr(controller,'_physics_ambush',None)
                answer=original(controller,obs)
                if slot==fixture['candidate_slot']:
                    telemetry.observe(obs,answer,controller)
                    frame={'tick':obs.tick,'ball':[*obs.ball.position,*obs.ball.velocity],
                      'last_touch':obs.ball.last_touch,'holder':obs.ball.controlling_player,
                      'score':list(obs.score),'friends':[[p.id,*p.position,*p.velocity] for p in obs.my_players],
                      'opponents':[[p.id,*p.position,*p.velocity] for p in obs.opponents],
                      'friend_cooldowns':{p.id:p.kick_cooldown_ticks for p in obs.my_players},
                      'enemy_cooldowns':{p.id:p.kick_cooldown_ticks for p in obs.opponents},
                      'can_kick':[p.id for p in obs.my_players if obs.can_kick(p.id)],
                      'old_ambush':old,'shape_cover':controller._shape_cover_id,
                      'chaser':controller._chaser,
                      'receive_plan':controller._receive_plan,'targets':controller._physics_targets,
                      'intents':(answer[0].debug or {}).get('physics_tactics',[]),
                      'actions':{pid:act.as_dict() for pid,act in answer[0].players.items()}}
                    history.append(frame)
                    resolved=sum(telemetry.counts.get(name+'_'+reason,0) for reason in
                        ('collected','new_kick','opponent_touch','other_touch','uncollected','goal_ended','rebound_goals','superseded'))
                    trigger=telemetry.counts.get(success_metric,0) if selection=='first clean success' else resolved
                    if window is None and trigger:
                        window=list(history);after=10
                    elif window is not None and after>0:
                        window.append(frame);after-=1
                return answer
            runner._decide=observed
            try:replay=run_fixture(fixture)
            finally:runner._decide=original
            if window is None and telemetry.pending:
                # A late attempted flight can still be in progress at the
                # final whistle. Preserve it without calling it a success.
                window=list(history)
            clean=all(s['policy_errors']==s['policy_timeouts']==0 for s in replay['result']['stats'])
            attempts.append({'result':replay,'clean':clean,'same_score':row['result']['score']==replay['result']['score'],
                'telemetry':telemetry.result(),'window':window})
            if clean:break
        proofs[name]={'available':bool(window),'selection':selection,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'original_fixture_id':row['fixture_id'],'fixture':fixture,'original_score':row['result']['score'],'attempts':attempts}
        print(name,'native execution replayed; clean',clean,'same score',attempts[-1]['same_score'])
    assert not a.out.exists()
    a.out.write_text(json.dumps({'scope':'First clean native success in recorded order, or the first native launch attempt when no success exists; diagnostic repetitions are separate from tournament gates. Policies, formations, engine and configuration are unchanged.',
      'proofs':proofs},indent=2)+'\n')


if __name__=='__main__':main()
