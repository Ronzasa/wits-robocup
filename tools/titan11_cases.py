"""Capture changed pass choices and actual native collection outcomes.

Instrumented development diagnosis, not tournament or timing evidence. The
baseline is evaluated on the same public state *after* the native timer, so its
alternative is a local comparison, not a counterfactual match result.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'student-sdk'))
from soccer import play_match,runner

FIELDS='width height my_goal opponent_goal centre_circle_radius simulation_hz max_speed acceleration ball_friction kick_impulse kick_range goal_width ball_radius player_radius'.split()


def load(label,path):
    spec=importlib.util.spec_from_file_location(label,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.Guardiola2011


def encode(obs):
    return {'tick':obs.tick,'score':list(obs.score),
        'ball':{k:getattr(obs.ball,k) for k in ('position','velocity','last_touch','controlling_player','controlling_team')},
        'my_players':[{k:getattr(p,k) for k in ('id','position','velocity','kick_cooldown_ticks')} for p in obs.my_players],
        'opponents':[{k:getattr(p,k) for k in ('id','position','velocity','kick_cooldown_ticks')} for p in obs.opponents],
        'kickers':[p.id for p in obs.my_players if obs.can_kick(p.id)]}


def kick(action,pid):
    p=action.players.get(pid)
    return None if p is None or p.kick_direction is None else (tuple(p.kick_direction),p.kick_power)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--team',type=Path,required=True)
    p.add_argument('--opponent',type=Path,default=ROOT/'champions/v10.0/team.py')
    p.add_argument('--seeds',type=int,nargs='+',required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--follow-ticks',type=int,default=0,help='Observe possession after first teammate collection; diagnostic only.')
    args=p.parse_args()
    if args.out.exists():p.error('Choose a new evidence path.')
    original=runner._decide
    baseline=load('case_baseline',ROOT/'champions/v10.0/team.py')
    candidate=load('case_candidate',args.team)
    all_cases=[];records=[]
    try:
        for seed in args.seeds:
            for side in (0,1):
                for kickoff in (True,False):
                    driven=candidate();pending=[];following=[];cases=[]
                    def traced(c,obs):
                        if c is not driven:return original(c,obs)
                        for row in list(following):
                            elapsed=obs.tick-row['outcome_tick']
                            follow=row['post_touch']
                            if tuple(obs.score)!=tuple(row['collection_score']):
                                follow['goal_change']=list(obs.score);following.remove(row);continue
                            follow['observations'].append({'tick':obs.tick,'last_touch':obs.ball.last_touch,
                                'holder':obs.ball.controlling_player,'controlling_team':obs.ball.controlling_team,'position':list(obs.ball.position),'velocity':list(obs.ball.velocity)})
                            if obs.ball.last_touch is not None and obs.ball.last_touch>=5 and follow['opponent_touch_tick'] is None:
                                follow['opponent_touch_tick']=obs.tick
                            if elapsed>=args.follow_ticks:following.remove(row)
                        for row in list(pending):
                            touch=obs.ball.last_touch
                            elapsed=obs.tick-row['tick']
                            if touch not in (None,row['passer']):
                                row['outcome']='receiver_touch' if touch==row['receiver'] else 'opponent_interception' if touch>=5 else 'other_teammate_touch'
                                row['outcome_tick']=obs.tick;row['touch_player']=touch;pending.remove(row)
                                if args.follow_ticks>0 and touch<5:
                                    row['collection_snapshot']=encode(obs);row['collection_score']=list(obs.score)
                                    row['post_touch']={'opponent_touch_tick':None,'goal_change':None,'observations':[]}
                                    following.append(row)
                            elif elapsed>100 or obs.score!=tuple(row['observation']['score']):
                                row['outcome']='uncollected_or_goal_reset';row['outcome_tick']=obs.tick;pending.remove(row)
                        before={k:(v.copy() if isinstance(v,dict) else v) for k,v in vars(c).items() if not k.startswith('_runtime_')}
                        old_plan=c._receive_plan
                        actual=original(c,obs)
                        plan=c._receive_plan
                        if plan is not None and plan!=old_plan and len(cases)<32 and kick(actual[0],plan[1]) is not None:
                            shadow=baseline();shadow.__dict__.update(before)
                            alternative=shadow.act(obs)
                            if kick(actual[0],plan[1])!=kick(alternative,plan[1]):
                                row={'seed':seed,'side':side,'kickoff':kickoff,'tick':obs.tick,
                                    'passer':plan[1],'receiver':plan[0],'observation':encode(obs),
                                    'field':{k:getattr(obs.field,k) for k in FIELDS},
                                    'planned_aim':c._receive_aim,'pass_plan':c._pass_plan,'bank_plan':c._bank_plan,
                                    'candidate_actions':{str(k):v.as_dict() for k,v in actual[0].players.items()},
                                    'baseline_actions_same_state':{str(k):v.as_dict() for k,v in alternative.players.items()},
                                    'baseline_plan_same_state':shadow._pass_plan,'outcome':'pending'}
                                cases.append(row);pending.append(row)
                        return actual
                    runner._decide=traced
                    teams=[driven,str(args.opponent)]
                    if side:teams.reverse()
                    result=play_match(*teams,seed=seed,kickoff_team=side if kickoff else 1-side,
                        config_path=str(ROOT/'configs/default.toml'),max_ticks=2400,per_decision_timeout_ms=20.).result
                    for row in pending:row['outcome']='match_ended'
                    all_cases.extend(cases)
                    records.append({'seed':seed,'side':side,'kickoff':kickoff,'result':result,'changed_passes':len(cases)})
                    print(seed,side,kickoff,'changed passes',len(cases),flush=True)
    finally:
        runner._decide=original
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps({'scope':__doc__,'source':str(args.team),
            'source_sha256':hashlib.sha256(args.team.read_bytes()).hexdigest(),
            'records':records,'cases':all_cases},indent=2)+'\n')


if __name__=='__main__':main()
