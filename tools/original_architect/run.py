"""Serial paired native full matches; never replace original raw outcomes."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys
import time
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'student-sdk'),str(ROOT/'tools'),str(ROOT/'tools/benchmarks'),str(Path(__file__).parent)]
from benchmark import aggregate
from timing import observed_fixture


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def cpu_stat():
    p=Path('/sys/fs/cgroup/cpu.stat')
    return {k:int(v) for k,v in (line.split() for line in p.read_text().splitlines())} if p.exists() else {}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--protocol',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();out=args.out.resolve();assert not out.exists();protocol=json.loads(args.protocol.read_text())
    from soccer import SoccerEnv
    from soccer.validate import validate
    from evaluator import submissions
    for rel,h in protocol['runner_hashes'].items():assert digest(ROOT/rel)==h
    with SoccerEnv(config_path=str(ROOT/'configs/default.toml')) as env:
        assert env.engine_version==protocol['engine_version'] and env.config_hash==protocol['config_hash']
    out.mkdir(parents=True);sources={};opponents={}
    for name,s in protocol['sources'].items():
        path=ROOT/s['path'];assert digest(path)==s['sha256']
        inspection=submissions.inspect(path.parent);assert not inspection.errors
        dest=out/'sources'/name/'team.py';dest.parent.mkdir(parents=True);shutil.copy2(path,dest);sources[name]=str(dest)
        report=validate(str(dest),ticks=400)
        intake={'ok':report.ok,'errors':report.errors,'warnings':report.warnings,'stats':report.stats,
            'folder_errors':inspection.errors,'folder_warnings':inspection.warnings,'flags':inspection.flags}
        (out/(name+'-validation.json')).write_text(json.dumps(intake,indent=2)+'\n')
        assert report.stats['decisions']==2000 and not inspection.errors
    archive=ROOT/protocol['opponents_archive'];assert digest(archive)==protocol['opponents_archive_sha256']
    with zipfile.ZipFile(archive) as z:
        manifest=json.loads(z.read('manifest.json'))
        for row in manifest:
            if row['style'] not in protocol['opponents']:continue
            data=z.read(row['path']);assert hashlib.sha256(data).hexdigest()==row['sha256']
            dest=out/'opponents'/row['style']/'team.py';dest.parent.mkdir(parents=True);dest.write_bytes(data);opponents[row['style']]=str(dest)
    assert set(opponents)==set(protocol['opponents'])
    fixtures=[(style,split,seed,side,kick) for style in sorted(opponents)
        for split,seeds in protocol['seeds'].items() for seed in seeds for side in (0,1) for kick in (True,False)]
    random.Random(protocol['fixture_order_seed']).shuffle(fixtures)
    meta={'started_utc':datetime.now(timezone.utc).isoformat(),'protocol':protocol,'protocol_sha256':digest(args.protocol),
        'workers':1,'sources':sources,'opponents_manifest':manifest,'trace':'Identical wall/thread CPU/GC/public-input tracing on raw and every exact repeat.'}
    (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    raw={n:[] for n in sources};accepted={n:[] for n in sources}
    for label in ('raw','accepted'):
        for n in sources:(out/label/n).mkdir(parents=True)
    names=list(sources)
    with (out/'slow-decisions.jsonl').open('w') as slow,(out/'timing-repeats.jsonl').open('w') as repeats,(out/'environment.jsonl').open('w') as environment:
        for i,(style,split,seed,side,kick) in enumerate(fixtures):
            order=names[i%len(names):]+names[:i%len(names)]
            for name in order:
                fixture={'team':sources[name],'opponent':opponents[style],'seed':seed,'candidate_slot':side,
                    'candidate_takes_kickoff':kick,'split':split,'config_path':str(ROOT/'configs/default.toml'),'config_hash':protocol['config_hash']}
                start=time.perf_counter();before=cpu_stat()
                row=observed_fixture(fixture,name,0,slow);raw[name].append(row)
                with (out/'raw'/name/'matches.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
                assert not any(s.get('policy_errors',0) for s in row['result']['stats'])
                clean=row
                for attempt in range(1,4):
                    if not any(s.get('policy_timeouts',0) for s in clean['result']['stats']):break
                    clean=observed_fixture(fixture,name,attempt,slow)
                    repeats.write(json.dumps({'source':name,'attempt':attempt,'original_fixture_id':row['fixture_id'],'result':clean})+'\n');repeats.flush()
                    assert not any(s.get('policy_errors',0) for s in clean['result']['stats'])
                # A repeated fixture is retained even if it never becomes clean;
                # it is explicitly disqualified by analysis, never dropped.
                accepted[name].append(clean)
                with (out/'accepted'/name/'matches.jsonl').open('a') as f:f.write(json.dumps(clean)+'\n')
                after=cpu_stat();environment.write(json.dumps({'source':name,'fixture_id':row['fixture_id'],
                    'wall_s':time.perf_counter()-start,'cgroup_delta':{k:after[k]-before[k] for k in before if k in after}})+'\n');environment.flush()
            if (i+1)%16==0:print('Paired configurations:',i+1,'/',len(fixtures),flush=True)
    for name,s in protocol['sources'].items():
        assert digest(ROOT/s['path'])==digest(Path(sources[name]))==s['sha256']
        for label,rows in (('raw',raw[name]),('accepted',accepted[name])):
            (out/label/name/'summary.json').write_text(json.dumps(aggregate(rows),indent=2)+'\n')
    meta['finished_utc']=datetime.now(timezone.utc).isoformat();meta['paired_configurations']=len(fixtures)
    (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('Completed raw and exact-repeat records; no outcome-based replacements.',flush=True)


if __name__=='__main__':main()
