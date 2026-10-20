"""One unchanged native fixture with identical tracing for raw and repeat runs."""
from collections import Counter
import gc
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'student-sdk'),str(ROOT/'tools/benchmarks')]
from benchmark import run_fixture
from soccer import runner


def observed_fixture(fixture,source,attempt,slow_handle):
    original=runner._decide;call=0;events=Counter();episodes=Counter();recent={};slow=[]
    gc_history=[];starts={};hist=Counter();examples=[]
    side=fixture['candidate_slot']
    def observed_gc(phase,info):
        if phase=='start':starts[info['generation']]=time.perf_counter_ns()
        else:
            end=time.perf_counter_ns();start=starts.pop(info['generation'],end)
            gc_history.append({'generation':info['generation'],'start_ns':start,'end_ns':end,'wall_ms':(end-start)/1e6})
    def measured(controller,obs):
        nonlocal call
        slot=call%2;call+=1
        start=time.perf_counter_ns();cpu=time.thread_time_ns();gci=len(gc_history)
        answer=original(controller,obs)
        cpu_ms=(time.thread_time_ns()-cpu)/1e6;end=time.perf_counter_ns()
        if slot==side:
            hist[int(answer[1]/.025)]+=1
            if answer[2] is None and answer[1]<20.:
                debug=getattr(answer[0],'debug',None) or {}
                for label in debug.get('titan_v11',()):
                    events[label]+=1
                    if obs.tick-recent.get(label,-10000)>5:
                        episodes[label]+=1
                        if len(examples)<12:examples.append({'tick':obs.tick,'event':label,'score':list(obs.score),'players':debug.get('titan_v11_players',())})
                    recent[label]=obs.tick
        if answer[1]>=5.:
            public={'tick':obs.tick,'score':list(obs.score),
                'ball':[list(obs.ball.position),list(obs.ball.velocity),obs.ball.last_touch,obs.ball.controlling_player,obs.ball.controlling_team],
                'players':[(p.id,*p.position,*p.velocity,p.kick_cooldown_ticks) for p in (*obs.my_players,*obs.opponents)]}
            entry={'source':source,'attempt':attempt,'seed':fixture['seed'],
                'opponent':Path(fixture['opponent']).parent.name,'side':side,
                'kickoff':fixture['candidate_takes_kickoff'],'slot':slot,'candidate':slot==side,
                'tick':obs.tick,'sdk_wall_ms':answer[1],'thread_cpu_ms':cpu_ms,
                'wall_minus_thread_cpu_ms':answer[1]-cpu_ms,'error':answer[2],
                'gc_overlap':[x for x in gc_history[gci:] if x['start_ns']<=end and x['end_ns']>=start],
                'post_receive_plan':getattr(controller,'_receive_plan',None),
                'public_input_sha256':hashlib.sha256(json.dumps(public,sort_keys=True).encode()).hexdigest(),'public_input':public}
            slow.append(entry);slow_handle.write(json.dumps(entry)+'\n');slow_handle.flush()
        return answer
    runner._decide=measured;gc.callbacks.append(observed_gc)
    try:row=run_fixture(fixture)
    finally:runner._decide=original;gc.callbacks.remove(observed_gc)
    row['architect_evaluation']={'ticks':dict(events),'episodes':dict(episodes),'examples':examples,
        'candidate_miss_calls':[x for x in slow if x['candidate'] and x['sdk_wall_ms']>=20.],
        'histogram_bin_width_ms':.025,'decision_histogram':dict(hist)}
    return row
