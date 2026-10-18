"""Reconstruct recorded native decisions and profile only the offline policy.

This never feeds profiled timings into qualification. Field physics come from
the official SDK; recorded control/kick gates and minimal persistent policy
state are restored before each call. The original action is the comparison.
"""
import argparse, cProfile, hashlib, io, json, math, pstats, sys
from pathlib import Path
from types import SimpleNamespace as S

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'student-sdk'))
from soccer import SoccerEnv
from soccer import runner


def tuples(value):
    return tuple(tuples(x) for x in value) if isinstance(value,list) else value


def same_action(expected, actual):
    if set(expected)!=set(str(k) for k in actual.players):return False
    def close(a,b):
        if a is None or b is None:return a is b
        if isinstance(a,(list,tuple)):
            return isinstance(b,(list,tuple)) and len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))
        return abs(a-b)<=1e-10
    for pid,p in actual.players.items():
        old=expected[str(pid)]
        if not all(close(old[key],getattr(p,key)) for key in ('movement','kick_direction','kick_power')):return False
    return True


def profile(replays, destination):
    assert not destination.exists();destination.mkdir()
    selection=json.loads((ROOT/'docs/nova-1/selected-policy.json').read_text())
    path=ROOT/selection['candidate_path'];source_hash=hashlib.sha256(path.read_bytes()).hexdigest()
    assert source_hash==selection['candidate_sha256']
    controller=runner._resolve(str(path))
    names=('width','height','simulation_hz','max_speed','acceleration','ball_friction','kick_impulse',
           'kick_range','my_goal','opponent_goal','goal_width','centre_circle_radius','player_radius','ball_radius')
    with SoccerEnv(config_path=str(ROOT/'configs/default.toml')) as env:
        field=S(**{name:getattr(env.field,name) for name in names})
    profiler=cProfile.Profile();total=0;mismatches=[];max_plans=0;max_steps=0
    for replay in sorted(replays.glob('side*.json')):
        record=json.loads(replay.read_text());assert record['source_sha256']==source_hash
        for frame in record['timeline']:
            controller.reset(0);controller._setup(field)
            for name,value in frame['before_state'].items():setattr(controller,name,tuples(value))
            def player(p):return S(id=p[0],position=tuple(p[1:3]),velocity=tuple(p[3:5]),kick_cooldown_ticks=p[5])
            ball=frame['ball']
            obs=S(field=field,tick=frame['tick'],score=tuple(frame['score']),time_remaining=frame['time_remaining'],
                my_players=[player(p) for p in frame['friends']],opponents=[player(p) for p in frame['opponents']],
                can_kick=set(frame['can_kick']).__contains__,ball=S(position=tuple(ball[:2]),velocity=tuple(ball[2:]),
                    controlling_team=frame['controlling_team'],controlling_player=frame['controlling_player'],last_touch=frame['last_touch']))
            action=profiler.runcall(controller.act,obs);total+=1
            if not same_action(frame['actions'],action):
                mismatches.append({'replay':replay.name,'tick':frame['tick']})
            max_plans=max(max_plans,controller._plans_evaluated);max_steps=max(max_steps,controller._response_steps)
    stream=io.StringIO();stats=pstats.Stats(profiler,stream=stream).strip_dirs().sort_stats('cumulative');stats.print_stats(45)
    (destination/'function-profile.log').write_text(stream.getvalue())
    functions=[]
    for (filename,line,name),(primitive,calls,local,cumulative,callers) in stats.stats.items():
        if filename=='team.py':functions.append({'function':name,'line':line,'calls':calls,'primitive_calls':primitive,
                                                'self_ms':local*1000.,'cumulative_ms':cumulative*1000.})
    functions.sort(key=lambda q:q['cumulative_ms'],reverse=True)
    result={'source_sha256':source_hash,'native_frames_replayed':total,'action_mismatches':len(mismatches),
        'mismatch_frames':mismatches,'max_response_plans':max_plans,'max_model_steps':max_steps,'function_profile':functions,
        'not_deadline_evidence':True,'limits':'Offline cProfile adds overhead. Reconstructed observations use Python records, not native view accessors. Timing is for hotspot diagnosis, never official acceptance or reliability.'}
    (destination/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    assert total>=1900,total
    assert not mismatches, mismatches[:5]
    assert max_plans<=3 and max_steps<=60
    print(json.dumps({k:v for k,v in result.items() if k!='function_profile'},indent=2))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--replays',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    profile(a.replays,a.out)


if __name__=='__main__':main()
