"""Trace unchanged policies in full native repeats, then profile frozen inputs offline."""
import argparse
import cProfile
import copy
import gc
import hashlib
import io
import json
from pathlib import Path
import pstats
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'student-sdk'),str(ROOT/'tools/benchmarks')]
from benchmark import run_fixture
from soccer import runner

CASES=[{'seed':1010963236,'candidate_slot':0,'candidate_takes_kickoff':False,'style':'v10-counter','target_tick':391},
       {'seed':1866751028,'candidate_slot':1,'candidate_takes_kickoff':False,'style':'v10-press','target_tick':290}]
SOURCES={'v10':'my-team/team.py','architect':'experiments/titan-v11-architect/team.py',
         'adaptive':'experiments/titan-adaptive-architect/team.py'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();out=args.out;assert not out.exists();out.mkdir(parents=True)
    old_decide=runner._decide
    records=[];offline=[]
    def fixture(case,name):
        return {'team':str(ROOT/SOURCES[name]),'opponent':str(ROOT/'work/prior/opponents'/case['style']/'team.py'),
                'seed':case['seed'],'candidate_slot':case['candidate_slot'],
                'candidate_takes_kickoff':case['candidate_takes_kickoff'],
                'config_path':str(ROOT/'configs/default.toml'),'config_hash':'372990895c7eca2a','split':'deadline-forensic'}
    def timed_match(case,name,index,capture=False):
        call=0;slow=[];snapshots=[];gc_history=[];starts={}
        def observed_gc(phase,info):
            if phase=='start':starts[info['generation']]=time.perf_counter_ns()
            else:
                end=time.perf_counter_ns();begin=starts.pop(info['generation'],end)
                gc_history.append((begin,end,info['generation']))
        def measured(controller,obs):
            nonlocal call
            slot=call%2;call+=1
            if capture and slot==case['candidate_slot'] and obs.tick==case['target_tick']:
                # Outside SDK timing; never used as competitive/runtime evidence.
                state=copy.deepcopy({k:v for k,v in controller.__dict__.items() if k!='_adaptive_obs'})
                snapshots.append((type(controller),state,obs))
            start=time.perf_counter_ns();cpu=time.thread_time_ns();gci=len(gc_history)
            answer=old_decide(controller,obs)
            thread_ms=(time.thread_time_ns()-cpu)/1e6;end=time.perf_counter_ns()
            if answer[1]>=5. or (slot==case['candidate_slot'] and obs.tick==case['target_tick']):
                slow.append({'tick':obs.tick,'slot':slot,'candidate':slot==case['candidate_slot'],
                    'sdk_wall_ms':answer[1],'thread_cpu_ms':thread_ms,
                    'wall_minus_cpu_ms':answer[1]-thread_ms,'error':answer[2],
                    'gc_overlaps':[x for x in gc_history[gci:] if x[0]<=end and x[1]>=start]})
            return answer
        runner._decide=measured;gc.callbacks.append(observed_gc)
        try:row=run_fixture(fixture(case,name))
        finally:runner._decide=old_decide;gc.callbacks.remove(observed_gc)
        data={'case':case,'source':name,'repeat':index,'capture_run_not_timing_evidence':capture,
              'row':row,'slow_and_target_calls':slow}
        records.append(data)
        with (out/'full-matches.jsonl').open('a') as f:f.write(json.dumps(data)+'\n')
        return snapshots
    for index in range(3):
        for case in CASES:
            names=list(SOURCES);names=names[index:]+names[:index]
            for name in names:timed_match(case,name,index)
        print('Completed forensic native block',index+1,'/3',flush=True)
    for case in CASES:
        snapshots=timed_match(case,'adaptive','capture',True)
        assert len(snapshots)==1
        cls,state,obs=snapshots[0]
        calls=[]
        for _ in range(20):
            c=cls();c.__dict__.update(copy.deepcopy(state))
            start=time.perf_counter_ns();cpu=time.thread_time_ns()
            c.act(obs)
            calls.append({'wall_ms':(time.perf_counter_ns()-start)/1e6,'thread_cpu_ms':(time.thread_time_ns()-cpu)/1e6})
        c=cls();c.__dict__.update(copy.deepcopy(state));profile=cProfile.Profile()
        profile.runcall(c.act,obs)
        stream=io.StringIO();pstats.Stats(profile,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(30)
        filename=f"profile-{case['seed']}-tick{case['target_tick']}.txt"
        (out/filename).write_text(stream.getvalue())
        offline.append({'case':case,'sample_count':20,'samples':calls,
            'median_wall_ms':statistics.median(x['wall_ms'] for x in calls),
            'max_wall_ms':max(x['wall_ms'] for x in calls),
            'median_thread_cpu_ms':statistics.median(x['thread_cpu_ms'] for x in calls),
            'profile':filename,'limitations':'Same public tick from a new full replay; earlier native timeouts may change the reached state. Offline cloned-state profiling is diagnostic only, not match timing or gate evidence.'})
    summary={'sources':{n:{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for n,p in SOURCES.items()},
        'forensic_full_matches':len(records),'timed_full_matches':18,'capture_full_matches':2,
        'cases':CASES,'offline_inputs':offline,'match_summary':[
            {'source':r['source'],'seed':r['case']['seed'],'repeat':r['repeat'],
             'capture':r['capture_run_not_timing_evidence'],
             'candidate_timeouts':r['row']['result']['stats'][r['case']['candidate_slot']]['policy_timeouts'],
             'candidate_miss_ticks':[x['tick'] for x in r['slow_and_target_calls'] if x['candidate'] and x['sdk_wall_ms']>=20]}
            for r in records]}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Forensic runs complete; no policy source changed.',flush=True)


if __name__=='__main__':main()
