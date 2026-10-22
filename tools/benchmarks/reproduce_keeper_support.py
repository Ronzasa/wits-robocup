"""Replay a successful native keeper reception and check disabled equivalence."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'student-sdk'))
from soccer import play_match, runner
from soccer.helpers import load_controller


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():
        p.error('Use a new output file.')
    rows=[json.loads(s) for s in (args.run/'raw/backpass/matches.jsonl').read_text().splitlines()]
    row=next(r for r in rows if r['physics_tactics']['counts'].get('backpass_collected',0)>0
             and all(s['policy_errors']==s['policy_timeouts']==0 for s in r['result']['stats']))
    source=args.run/'sources/backpass/team.py'
    candidate=load_controller(str(source))
    decisions=[];original=runner._decide
    def observed(controller,obs):
        answer=original(controller,obs)
        if controller is candidate and 450<=obs.tick<=550:
            action,elapsed,error=answer
            player=lambda x:{'id':x.id,'position':x.position,'velocity':x.velocity,
                             'kick_cooldown_ticks':x.kick_cooldown_ticks}
            decisions.append({'tick':obs.tick,'ball':{
                'position':obs.ball.position,'velocity':obs.ball.velocity,
                'last_touch':obs.ball.last_touch,'controlling_player':obs.ball.controlling_player,
                'controlling_team':obs.ball.controlling_team},
                'friends':[player(x) for x in obs.my_players],
                'opponents':[player(x) for x in obs.opponents],
                'events':list(obs.events),'actions':asdict(action),
                'plan':controller._receive_plan,'elapsed_ms':elapsed,'error':error})
        return answer
    def match(controller):
        teams=[controller,row['opponent']]
        slot=row['candidate_slot']
        if slot:teams.reverse()
        return play_match(*teams,seed=row['seed'],kickoff_team=slot if row['candidate_takes_kickoff'] else 1-slot,
            config_path=str(ROOT/'configs/default.toml'),max_ticks=2400,per_decision_timeout_ms=20.).result
    runner._decide=observed
    try:
        replay=match(candidate)
    finally:
        runner._decide=original
    assert replay['score']==row['result']['score']
    assert all(s['policy_errors']==s['policy_timeouts']==0 for s in replay['stats'])
    # Candidate receives identical public observations but its decisions are
    # never sent to the engine. This is an untimed diagnostic, not tournament
    # evidence about runtime or a change to the native decision timer.
    champion=load_controller(str(ROOT/'my-team/team.py'))
    disabled=load_controller(str(ROOT/'experiments/keeper-support/team.py'))
    disabled.KEEPER_BACKPASS=disabled.KEEPER_WALL_COUNTER=False
    disabled.reset(row['seed'])
    checked=0
    def compared(controller,obs):
        nonlocal checked
        answer=original(controller,obs)
        if controller is champion:
            assert disabled.act(obs)==answer[0],('Behavior changed with both features disabled',obs.tick)
            checked+=1
        return answer
    runner._decide=compared
    try:
        diagnostic=match(champion)
    finally:
        runner._decide=original
    assert checked==2400
    assert all(s['policy_errors']==s['policy_timeouts']==0 for s in diagnostic['stats'])
    report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'fixture':{k:row[k] for k in ('opponent','seed','candidate_slot','candidate_takes_kickoff')},
        'original_score':row['result']['score'],'replayed_result':replay,'trace':decisions,
        'disabled_equivalence':{'native_observations_checked':checked,'exact_actions_and_debug_equal':True,
                                'result':diagnostic,'timing_scope':'Untimed shadow comparison; excluded from all tournament runtime metrics.'}}
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print('Successful reception replay: identical score; zero exceptions/deadline misses.')
    print('Disabled features: exact equality on',checked,'native decisions.')


if __name__=='__main__':
    main()
