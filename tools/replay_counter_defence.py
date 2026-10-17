"""Capture public counterattack/goal context in a native development replay.

This instrumented diagnostic does not supply promotion timing evidence. It
never changes actions, physics, deadlines or controller tactics.
"""
import argparse
from collections import deque
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'student-sdk'))
from soccer import play_match,runner


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--team',type=Path,required=True)
    p.add_argument('--style',required=True)
    p.add_argument('--seed',type=int,required=True)
    p.add_argument('--side',type=int,choices=(0,1),required=True)
    p.add_argument('--kickoff',action=argparse.BooleanOptionalAction,default=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():p.error('Preserve previous evidence.')
    args.out.mkdir(parents=True)
    opponent=args.out.resolve()/'opponent'/'team.py';opponent.parent.mkdir()
    with zipfile.ZipFile(ROOT/'tests/fixtures/titan-12b-opponents.zip') as z:
        opponent.write_bytes(z.read(args.style+'/team.py'))
    spec=importlib.util.spec_from_file_location('counter_replay',args.team)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    driven=mod.Guardiola2011()
    target_info=None
    if hasattr(driven,'_counter_defence'):
        method=driven._counter_defence
        def capture(obs,friends,enemies,chaser,races,enemy_eta,targets,receiver,protected):
            nonlocal target_info
            before=dict(targets)
            method(obs,friends,enemies,chaser,races,enemy_eta,targets,receiver,protected)
            target_info={'before':before,'after':dict(targets),'trace':dict(driven._counter_trace)}
        driven._counter_defence=capture
    original=runner._decide;buffer=deque(maxlen=60);goals=[];changes=[];score=(0,0)
    def observe(c,obs):
        nonlocal score
        answer=original(c,obs)
        if c is driven:
            frame={'tick':obs.tick,'score':list(obs.score),'ball':[*obs.ball.position,*obs.ball.velocity],
                'holder':obs.ball.controlling_player,'touch':obs.ball.last_touch,
                'friends':[[q.id,*q.position,*q.velocity] for q in obs.my_players],
                'opponents':[[q.id,*q.position,*q.velocity] for q in obs.opponents],
                'chaser':driven._chaser,'guard':driven._shape_cover_id,'target_info':target_info,
                'actions':{} if answer[0] is None else {k:v.as_dict() for k,v in answer[0].players.items()}}
            if tuple(obs.score)!=score:
                goals.append({'tick':obs.tick,'score':list(obs.score),'previous':list(score),'context':list(buffer)})
                score=tuple(obs.score)
            buffer.append(frame)
            if target_info and target_info['before']!=target_info['after']:changes.append(frame)
        return answer
    runner._decide=observe
    try:
        teams=[driven,str(opponent)] if args.side==0 else [str(opponent),driven]
        result=play_match(*teams,seed=args.seed,kickoff_team=args.side if args.kickoff else 1-args.side,
            config_path=str(ROOT/'configs/default.toml'),max_ticks=2400,per_decision_timeout_ms=20.).result
    finally:runner._decide=original
    (args.out/'replay.json').write_text(json.dumps({'scope':__doc__,'team':str(args.team),'style':args.style,
        'seed':args.seed,'side':args.side,'kickoff':args.kickoff,'result':result,'goals':goals,'changes':changes},indent=2)+'\n')
    assert not any(s['policy_errors'] or s['policy_timeouts'] for s in result['stats'])
    print('Unaltered replay:',result['score'],'change ticks',len(changes),'goal ticks',[g['tick'] for g in goals])

if __name__=='__main__':main()
