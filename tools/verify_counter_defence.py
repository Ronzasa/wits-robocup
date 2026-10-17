"""Instrumented native TITAN-12B invariants; not promotion timing evidence.

A frozen v10.0 shadow receives the same observations. All pre-existing policy
state, kicks, keeper/chaser actions and live receiver actions must match. Only
defensive movement is permitted to differ. Snapshot checks occur in this
instrumented diagnostic, never in the strength runner or submission.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'student-sdk'))
from soccer import play_match,runner


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.Guardiola2011


def existing_state(c):
    return {k:v for k,v in vars(c).items() if not k.startswith('_counter_')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources',type=Path,nargs='+',required=True)
    p.add_argument('--styles',nargs='+',default=['v10-counter','v10-press','v9.1','v10-compact'])
    p.add_argument('--seeds',type=int,nargs='+',required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():p.error('Preserve previous evidence; use a new directory.')
    args.out.mkdir(parents=True)
    opponents={}
    with zipfile.ZipFile(ROOT/'tests/fixtures/titan-12b-opponents.zip') as z:
        for style in args.styles:
            path=args.out.resolve()/'opponents'/style/'team.py';path.parent.mkdir(parents=True)
            path.write_bytes(z.read(style+'/team.py'));opponents[style]=path
    baseline=load('counter_native_champion',ROOT/'champions/v10.0/team.py')
    original_decide=runner._decide
    records=[];cases=[];total=0
    try:
        for index,path in enumerate(args.sources):
            cls=load('counter_native_'+str(index),path)
            for style,opponent in opponents.items():
                for seed in args.seeds:
                    for side in (0,1):
                        for kickoff in (True,False):
                            driven,shadow=cls(),baseline();shadow.reset(seed)
                            count=0;changed_count=0;doubles=0;threat_ticks=0;receiver_ticks=0
                            captured=None;examples=0
                            method=driven._counter_defence
                            def inspect(obs,friends,enemies,chaser,races,enemy_eta,targets,receive_target,protected):
                                nonlocal captured,changed_count,doubles,threat_ticks,receiver_ticks,examples
                                before=dict(targets)
                                episode_before={k:getattr(driven,k) for k in ('_counter_score','_counter_tick',
                                    '_counter_double_until','_counter_double_latched')}
                                method(obs,friends,enemies,chaser,races,enemy_eta,targets,receive_target,protected)
                                changed={i for i in targets if targets[i]!=before[i]}
                                locked={0,chaser[0]}
                                if receive_target is not None:locked.add(receive_target[0]);receiver_ticks+=1
                                assert not changed&locked,('Protected role overwritten',obs.tick,changed,locked)
                                assert changed.issubset(set(driven._counter_trace['defenders']))
                                assert len(changed)<=2
                                assert not protected or not changed
                                if len(driven._counter_trace['defenders'])==2:
                                    assert len(friends)-len({0,chaser[0],*driven._counter_trace['defenders']})>=1
                                    doubles+=1
                                threat_ticks+=bool(driven._counter_trace['threats'])
                                changed_count+=bool(changed)
                                captured=(chaser[0],receive_target)
                                if changed and examples<2:
                                    cases.append({'source':str(path),'style':style,'seed':seed,'side':side,'kickoff':kickoff,
                                        'tick':obs.tick,'score':list(obs.score),'ball':[*obs.ball.position,*obs.ball.velocity],
                                        'holder':obs.ball.controlling_player,'touch':obs.ball.last_touch,
                                        'ready':[p[0] for p in friends if obs.can_kick(p[0])],
                                        'friends':friends,'opponents':enemies,'chaser':chaser,'races':races,'enemy_eta':enemy_eta,
                                        'press_owner':driven._press_contact_owner,'own_contact_tick':driven._press_own_contact_tick,
                                        'friend_cooldowns':dict(driven._friend_cooldowns),
                                        'enemy_cooldowns':dict(driven._enemy_cooldowns),'episode_before':episode_before,
                                        'public_field':{k:getattr(obs.field,k) for k in ('simulation_hz','max_speed',
                                            'acceleration','ball_friction','kick_impulse','kick_range','my_goal','opponent_goal',
                                            'height','goal_width','centre_circle_radius','player_radius','ball_radius')},
                                        'guard':driven._shape_cover_id,'receiver':receive_target,'protected':protected,
                                        'before':before,'after':dict(targets),'trace':dict(driven._counter_trace)})
                                    examples+=1
                            driven._counter_defence=inspect
                            def compare(c,obs):
                                nonlocal count
                                actual=original_decide(c,obs)
                                if c is driven:
                                    expected=original_decide(shadow,obs)
                                    assert actual[2] is None and expected[2] is None,(obs.tick,actual[2],expected[2])
                                    assert existing_state(driven)==existing_state(shadow),('Non-defensive state changed',path,obs.tick)
                                    da,sa=actual[0],expected[0]
                                    assert da.debug==sa.debug
                                    for pid,action in da.players.items():
                                        other=sa.players[pid]
                                        assert action.kick_direction==other.kick_direction and action.kick_power==other.kick_power,('Kick changed',obs.tick,pid)
                                    for pid in {0,captured[0],*([] if captured[1] is None else [captured[1][0]])}:
                                        assert da.players[pid].as_dict()==sa.players[pid].as_dict(),('Locked action changed',obs.tick,pid)
                                    if not driven.COUNTER_COVER and not driven.COUNTER_DOUBLE:
                                        assert {i:a.as_dict() for i,a in da.players.items()}=={i:a.as_dict() for i,a in sa.players.items()}
                                    count+=1
                                return actual
                            runner._decide=compare
                            teams=[driven,str(opponent)] if side==0 else [str(opponent),driven]
                            result=play_match(*teams,seed=seed,kickoff_team=side if kickoff else 1-side,
                                config_path=str(ROOT/'configs/default.toml'),max_ticks=2400,per_decision_timeout_ms=20.).result
                            assert count==2400 and result['ticks']==2400
                            assert not any(s['policy_errors'] for s in result['stats'])
                            records.append({'source':str(path),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                                'style':style,'seed':seed,'side':side,'kickoff':kickoff,'decisions':count,
                                'changed_target_ticks':changed_count,'threat_ticks':threat_ticks,'double_ticks':doubles,
                                'live_receiver_ticks':receiver_ticks,'result':result})
                            total+=count
                            print(path.parent.name,style,side,kickoff,'verified',count,'changes',changed_count,'double',doubles,flush=True)
    finally:
        runner._decide=original_decide
        (args.out/'native-audit.json').write_text(json.dumps({'scope':__doc__,'compared_decisions':total,'records':records},indent=2)+'\n')
        (args.out/'native-cases.json').write_text(json.dumps(cases,indent=2)+'\n')

if __name__=='__main__':main()
