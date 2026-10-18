"""Investigate raw deadline fixtures with CPU/wall/GC traces; diagnostic only.

Does not change controller code, timer limits, GC policy, scheduling or physics.
Instrumented repetitions cannot erase or explain an original uninstrumented
failure; they only reveal whether a new event is CPU- or wall-time dominated.
"""
import argparse,gc,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'student-sdk'));sys.path.insert(0,str(ROOT/'tools/benchmarks'))
from soccer import runner
from benchmark import run_fixture

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('Preserve diagnostics.')
    a.out.mkdir(parents=True);cases=[]
    for stage in sorted(a.work.iterdir(),key=lambda x:('validation' not in x.name,x.name)):
        if not (stage/'metadata.json').exists():continue
        meta=json.loads((stage/'metadata.json').read_text())
        for name in meta['protocol']['sources']:
            for line in (stage/'raw'/name/'matches.jsonl').read_text().splitlines():
                row=json.loads(line);slot=row['candidate_slot'];stats=row['result']['stats'][slot]
                if stats['policy_timeouts']:
                    cases.append((stage.name,name,meta['sources'][name],row))
    cases=cases[:4];report=[];original=runner._decide
    for stage,name,source,row in cases:
        for repeat in range(2):
            events=[];starts={};durations=[];slow=[];index=0
            def on_gc(phase,info):
                generation=info['generation']
                if phase=='start':starts[generation]=(time.perf_counter_ns(),time.process_time_ns())
                else:
                    end=time.perf_counter_ns();cpu=time.process_time_ns();begin,begin_cpu=starts.pop(generation,(end,cpu))
                    events.append({'generation':generation,'start_ns':begin,'end_ns':end,'wall_ms':(end-begin)*1e-6,'cpu_ms':(cpu-begin_cpu)*1e-6})
            def decide(c,obs):
                nonlocal index
                slot=index%2;index+=1
                start=time.perf_counter_ns();cpu=time.process_time_ns();event_index=len(events)
                answer=original(c,obs)
                end=time.perf_counter_ns();elapsed_cpu=(time.process_time_ns()-cpu)*1e-6
                if slot==row['candidate_slot']:
                    durations.append((answer[1],elapsed_cpu))
                    if answer[1]>=5.:
                        overlap=[e for e in events[event_index:] if e['end_ns']>=start and e['start_ns']<=end]
                        slow.append({'tick':obs.tick,'wall_ms':answer[1],'cpu_ms':elapsed_cpu,'gc_overlap':overlap,'score':list(obs.score),'ball':[*obs.ball.position,*obs.ball.velocity]})
                return answer
            runner._decide=decide;gc.callbacks.append(on_gc)
            fixture={'team':source,'opponent':row['opponent'],'seed':row['seed'],'candidate_slot':row['candidate_slot'],'candidate_takes_kickoff':row['candidate_takes_kickoff'],'config_path':str(ROOT/'configs/default.toml'),'config_hash':'372990895c7eca2a','split':'latency-diagnostic'}
            try:result=run_fixture(fixture)
            finally:runner._decide=original;gc.callbacks.remove(on_gc)
            record={'original_stage':stage,'source':name,'source_sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest(),'original_fixture_id':row['fixture_id'],'original_raw_result':row,'diagnostic_repeat':repeat,'new_result':result,'slow_calls':slow,'gc_events':events,'mean_wall_ms':sum(w for w,c in durations)/len(durations),'mean_cpu_ms':sum(c for w,c in durations)/len(durations),'max_wall_ms':max(w for w,c in durations),'max_cpu_ms':max(c for w,c in durations),'interpretation':'Descriptive diagnostic. Original per-call trace absent; source of original wall-time spike remains unknown.'}
            (a.out/(str(len(report))+'.json')).write_text(json.dumps(record,indent=2)+'\n');report.append({k:v for k,v in record.items() if k not in ('original_raw_result','new_result','gc_events')})
    (a.out/'summary.json').write_text(json.dumps({'cases':report,'scope':__doc__},indent=2)+'\n');print('Completed diagnostic fixture repetitions:',len(report))
if __name__=='__main__':main()
