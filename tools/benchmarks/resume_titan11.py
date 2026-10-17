"""Resume a TITAN-11 native schedule interrupted by an execution-environment restart.

Completed raw fixtures are immutable and never replayed for a better score.
Reconstruct the registered shuffled schedule, complete its first missing source,
then continue with the same rotation, native deadline and first-clean policy.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import random
import sys
import time

from benchmark import aggregate,run_fixture
from run_titan11 import ROOT,cpu_stat,delta,digest,errors,interrupted


def read(path):
    if not path.exists():return []
    values=[]
    for line in path.read_text().splitlines():
        # A partial write must be investigated, never silently dropped.
        values.append(json.loads(line))
    return values


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);args=p.parse_args()
    out=args.run.resolve();meta=json.loads((out/'metadata.json').read_text())
    if meta.get('finished_utc'):p.error('Run already complete; do not resample it.')
    protocol=meta['protocol'];names=list(protocol['sources']);sources=meta['sources']
    sys.path.insert(0,str(ROOT/'student-sdk'))
    from soccer import SoccerEnv,runner
    with SoccerEnv(config_path=str(ROOT/'configs/default.toml')) as env:
        assert env.engine_version==protocol['engine_version'] and env.config_hash==protocol['config_hash']
    opponents={style:str(out/'opponents'/style/'team.py') for style in protocol['opponents']}
    for row in meta['opponents']:
        if row['style'] in opponents:assert digest(Path(opponents[row['style']]))==row['sha256']
    for name in names:
        assert digest(Path(sources[name]))==protocol['sources'][name]['sha256']
        assert digest(ROOT/protocol['sources'][name]['path'])==protocol['sources'][name]['sha256']
        assert json.loads((out/(name+'-validation.json')).read_text())['ok']
    fixtures=[(style,split,seed,side,kickoff) for style in sorted(opponents)
        for split,seeds in protocol['seeds'].items() for seed in seeds
        for side in (0,1) for kickoff in (True,False)]
    random.Random(protocol['fixture_order_seed']).shuffle(fixtures)
    raw={n:read(out/'raw'/n/'matches.jsonl') for n in names}
    clean={n:read(out/'accepted'/n/'matches.jsonl') for n in names}
    indexed={n:{r['fixture_id']:r for r in raw[n]} for n in names}
    accepted={n:{r['fixture_id']:r for r in clean[n]} for n in names}
    prior_repeats=read(out/'timing-repeats.jsonl')
    for n in names:assert len(indexed[n])==len(raw[n]) and len(accepted[n])==len(clean[n])
    resume={'started_utc':datetime.now(timezone.utc).isoformat(),'resume_runner_sha256':digest(Path(__file__)),
        'original_runner_sha256':meta['runner_sha256'],'previous_raw_counts':{n:len(raw[n]) for n in names},
        'note':'Completed native results retained. In-flight fixture without a returned result resumed from the same registered source/seed/side/kickoff. Prior fine-grained timing histogram was in memory and unavailable; full native per-fixture mean/max/buckets remain preserved.'}
    record=out/('resume-'+str(len(list(out.glob('resume-*.json')))+1)+'.json')
    record.write_text(json.dumps(resume,indent=2)+'\n')
    hist={n:{} for n in names};original_decide=runner._decide
    raw_handles={n:(out/'raw'/n/'matches.jsonl').open('a') for n in names}
    clean_handles={n:(out/'accepted'/n/'matches.jsonl').open('a') for n in names}
    repeat_handle=(out/'timing-repeats.jsonl').open('a');env_handle=(out/'environment.jsonl').open('a')
    journal=(out/'resume-journal.jsonl').open('a');before_stage=cpu_stat()
    try:
        for index,(style,split,seed,side,kickoff) in enumerate(fixtures):
            offset=index%len(names)
            for name in names[offset:]+names[:offset]:
                fixture={'team':sources[name],'opponent':opponents[style],'seed':seed,'candidate_slot':side,
                    'candidate_takes_kickoff':kickoff,'config_path':str(ROOT/'configs/default.toml'),
                    'config_hash':protocol['config_hash'],'split':split}
                fid='{}-{}-{}-side{}-kick{}'.format(split,opponents[style],seed,side,int(kickoff))
                if fid in accepted[name]:continue
                if fid in indexed[name]:row=indexed[name][fid]
                else:
                    journal.write(json.dumps({'source':name,'fixture_id':fid,'started_utc':datetime.now(timezone.utc).isoformat()})+'\n');journal.flush()
                    count=0
                    def measured(controller,obs):
                        nonlocal count
                        slot=count%2;count+=1
                        answer=original_decide(controller,obs)
                        if slot==side:
                            bucket=int(answer[1]/.025);hist[name][bucket]=hist[name].get(bucket,0)+1
                        return answer
                    before=cpu_stat();wall,cpu=time.perf_counter(),time.process_time()
                    runner._decide=measured
                    try:row=run_fixture(fixture)
                    finally:runner._decide=original_decide
                    env_handle.write(json.dumps({'source':name,'fixture_id':fid,'resumed':True,
                        'wall_s':time.perf_counter()-wall,'cpu_s':time.process_time()-cpu,
                        'cgroup_delta':delta(before,cpu_stat())})+'\n');env_handle.flush()
                    raw[name].append(row);indexed[name][fid]=row
                    raw_handles[name].write(json.dumps(row)+'\n');raw_handles[name].flush()
                assert not errors(row),('Policy exception',name,fid)
                chosen=row;attempt=0
                for repeat in prior_repeats:
                    if repeat['source']==name and repeat['original_fixture_id']==fid:
                        assert interrupted(chosen),'Repeat after a clean result'
                        chosen=repeat['result'];attempt=repeat['attempt']
                        assert not errors(chosen)
                while interrupted(chosen) and attempt<3:
                    chosen=run_fixture(fixture);attempt+=1
                    repeat_handle.write(json.dumps({'source':name,'attempt':attempt,'original_fixture_id':fid,'result':chosen})+'\n');repeat_handle.flush()
                    assert not errors(chosen)
                assert not interrupted(chosen),('Repeated deadline failure',name,fid)
                accepted[name][fid]=chosen;clean[name].append(chosen)
                clean_handles[name].write(json.dumps(chosen)+'\n');clean_handles[name].flush()
            if (index+1)%20==0:print('Resumed paired schedule:',index+1,'/',len(fixtures),flush=True)
    finally:
        runner._decide=original_decide
        for h in [*raw_handles.values(),*clean_handles.values(),repeat_handle,env_handle,journal]:h.close()
    for name in names:
        assert len(raw[name])==len(clean[name])==len(fixtures)
        assert digest(Path(sources[name]))==protocol['sources'][name]['sha256']
        for label,data in [('raw',raw[name]),('accepted',clean[name])]:
            summary={'all':aggregate(data),'by_opponent':{style:aggregate([r for r in data if r['opponent']==path]) for style,path in opponents.items()}}
            (out/label/name/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'decision-histograms.json').write_text(json.dumps({'bin_width_ms':.025,'raw_only':True,
        'coverage':'resumed fixtures only; earlier detailed histogram lost during environment restart',
        'histograms':hist},indent=2)+'\n')
    meta['finished_utc']=datetime.now(timezone.utc).isoformat();meta['resume_runner_sha256']=digest(Path(__file__))
    meta['resumed_cgroup_delta']=delta(before_stage,cpu_stat())
    (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    resume['finished_utc']=meta['finished_utc'];record.write_text(json.dumps(resume,indent=2)+'\n')
    print('Completed without replaying any previously accepted fixture.',flush=True)


if __name__=='__main__':main()
