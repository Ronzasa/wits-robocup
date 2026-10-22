"""TITAN physics serial paired experiments with preserved raw deadline records.

Run from the repository root with --protocol and a new --out directory.
Frozen sources and opponents are hashed before and after the run. Every
fixture uses the official SDK, 2,400 ticks and the native 20 ms deadline.
"""
import argparse
import gc
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys
import time
import zipfile

from benchmark import aggregate, run_fixture

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from physics_tactics.telemetry import Telemetry


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cpu_stat():
    path = Path('/sys/fs/cgroup/cpu.stat')
    if not path.exists():
        return {}
    return {k: int(v) for k, v in (line.split() for line in path.read_text().splitlines())}


def delta(before, after):
    return {k: after[k] - before[k] for k in before if k in after}


def interrupted(row):
    return any(s.get('policy_timeouts', 0) for s in row['result']['stats'])


def errors(row):
    return any(s.get('policy_errors', 0) for s in row['result']['stats'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--protocol', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        p.error('Use a new output directory; never overwrite prior evidence.')
    protocol = json.loads(args.protocol.read_text())
    seeds = [(split, seed) for split, values in protocol['seeds'].items() for seed in values]
    assert seeds and len(seeds) == len({seed for _, seed in seeds})
    assert 2 <= len(protocol['sources']) <= 12
    sys.path.insert(0, str(ROOT / 'student-sdk'))
    sys.path.insert(0, str(ROOT / 'tools'))
    from soccer import SoccerEnv
    from soccer import runner
    from soccer.validate import validate
    from evaluator import submissions
    with SoccerEnv(config_path=str(ROOT / 'configs/default.toml')) as env:
        assert env.engine_version == protocol['engine_version']
        assert env.config_hash == protocol['config_hash']
    out = args.out.resolve()
    out.mkdir(parents=True)
    archive_path = ROOT / protocol['opponents_archive']
    assert digest(archive_path) == protocol['opponents_archive_sha256']
    opponents = {}
    with zipfile.ZipFile(archive_path) as archive:
        manifest = json.loads(archive.read('manifest.json'))
        assert set(archive.namelist()) == {'manifest.json', *(x['path'] for x in manifest)}
        for row in manifest:
            name = row['style']
            if name not in protocol['opponents']:
                continue
            assert name and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789._-' for c in name)
            assert row['path'] == name + '/team.py'
            code = archive.read(row['path'])
            assert hashlib.sha256(code).hexdigest() == row['sha256']
            dest = out / 'opponents' / name / 'team.py'
            dest.parent.mkdir(parents=True)
            dest.write_bytes(code)
            opponents[name] = str(dest)
    assert set(opponents) == set(protocol['opponents'])
    names = list(protocol['sources'])
    sources, originals = {}, {}
    for name, spec in protocol['sources'].items():
        path = ROOT / spec['path']
        assert digest(path) == spec['sha256']
        originals[name] = path
        folder = submissions.inspect(path.parent)
        assert not folder.errors, folder.errors
        dest = out / 'sources' / name / 'team.py'
        dest.parent.mkdir(parents=True)
        shutil.copy2(path, dest)
        sources[name] = str(dest)
        report = validate(str(dest), ticks=400)
        validation = {'ok': report.ok, 'errors': report.errors, 'warnings': report.warnings,
            'stats': report.stats, 'folder_errors': folder.errors,
            'folder_warnings': folder.warnings, 'static_review_flags': folder.flags}
        (dest.parent.parent.parent / (name + '-validation.json')).write_text(json.dumps(validation, indent=2) + '\n')
        # A failed intake stays recorded and makes a source ineligible for
        # promotion. Still measure legal, importable training policies rather
        # than silently retrying or dropping their native outcomes.
        assert report.stats['decisions'] == 2000 and not folder.errors, validation
    fixtures = [(style, split, seed, side, kickoff)
        for style in sorted(opponents) for split, seed in seeds
        for side in (0, 1) for kickoff in (True, False)]
    random.Random(protocol['fixture_order_seed']).shuffle(fixtures)
    assert len(fixtures) == len(opponents) * len(seeds) * 4
    metadata = {'started_utc': datetime.now(timezone.utc).isoformat(), 'protocol': protocol,
        'protocol_sha256': digest(args.protocol), 'runner_sha256': digest(Path(__file__)),
        'workers': 1, 'source_order': 'rotating source order on each shuffled matched configuration',
        'sources': sources, 'original_sources': {k: str(v) for k, v in originals.items()},
        'opponents': manifest, 'deadline_ms': 20., 'ticks': 2400}
    (out / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    raw = {name: [] for name in names}
    clean = {name: [] for name in names}
    for name in names:
        (out / 'raw' / name).mkdir(parents=True)
        (out / 'accepted' / name).mkdir(parents=True)
    handles = {name: (out / 'raw' / name / 'matches.jsonl').open('w') for name in names}
    accepted_handles = {name: (out / 'accepted' / name / 'matches.jsonl').open('w') for name in names}
    repeat_handle = (out / 'timing-repeats.jsonl').open('w')
    environment_handle = (out / 'environment.jsonl').open('w')
    slow_handle = (out / 'slow-decisions.jsonl').open('w')
    started_stat = cpu_stat()
    histograms = {name: {} for name in names}
    original_decide = runner._decide
    try:
        for index, (style, split, seed, side, kickoff) in enumerate(fixtures):
            offset = index % len(names)
            order = names[offset:] + names[:offset]
            for name in order:
                fixture = {'team': sources[name], 'opponent': opponents[style], 'seed': seed,
                    'candidate_slot': side, 'candidate_takes_kickoff': kickoff,
                    'config_path': str(ROOT / 'configs/default.toml'),
                    'config_hash': protocol['config_hash'], 'split': split}
                before = cpu_stat()
                wall, cpu = time.perf_counter(), time.process_time()
                call_index = 0
                telemetry = Telemetry()
                gc_events=[];gc_starts={}
                def observed_gc(phase,info):
                    generation=info['generation']
                    if phase=='start':gc_starts[generation]=(time.perf_counter_ns(),time.thread_time_ns())
                    else:
                        end=time.perf_counter_ns();cpu_end=time.thread_time_ns()
                        start,cpu_start=gc_starts.pop(generation,(end,cpu_end))
                        gc_events.append({'generation':generation,'start_ns':start,'end_ns':end,
                            'wall_ms':(end-start)*1e-6,'thread_cpu_ms':(cpu_end-cpu_start)*1e-6})
                def measured(controller, observation):
                    nonlocal call_index
                    slot = call_index % 2
                    call_index += 1
                    start=time.perf_counter_ns();cpu_start=time.thread_time_ns();gc_index=len(gc_events)
                    answer = original_decide(controller, observation)
                    elapsed_cpu=(time.thread_time_ns()-cpu_start)*1e-6
                    if slot == side:
                        telemetry.observe(observation,answer,controller)
                        bucket = int(answer[1] / .025)
                        hist = histograms[name]
                        hist[bucket] = hist.get(bucket, 0) + 1
                        if answer[1]>=5.:
                            end=time.perf_counter_ns()
                            slow_handle.write(json.dumps({'source':name,'opponent':style,'seed':seed,'side':side,'kickoff':kickoff,
                                'tick':observation.tick,'sdk_wall_ms':answer[1],'thread_cpu_ms':elapsed_cpu,
                                'gc_overlap':[e for e in gc_events[gc_index:] if e['end_ns']>=start and e['start_ns']<=end]})+'\n')
                            slow_handle.flush()
                    return answer
                runner._decide = measured
                gc.callbacks.append(observed_gc)
                try:
                    row = run_fixture(fixture)
                finally:
                    runner._decide = original_decide
                    gc.callbacks.remove(observed_gc)
                after = cpu_stat()
                row['physics_tactics'] = telemetry.result()
                environment_handle.write(json.dumps({'source': name, 'fixture_id': row['fixture_id'],
                    'wall_s': time.perf_counter() - wall, 'cpu_s': time.process_time() - cpu,
                    'cgroup_delta': delta(before, after)}) + '\n')
                raw[name].append(row)
                handles[name].write(json.dumps(row) + '\n')
                handles[name].flush()
                assert not errors(row), ('Policy exception', name, row['fixture_id'])
                accepted = row
                for attempt in range(1, 4):
                    if not interrupted(accepted):
                        break
                    accepted = run_fixture(fixture)
                    repeat_handle.write(json.dumps({'source': name, 'attempt': attempt,
                        'original_fixture_id': row['fixture_id'], 'result': accepted}) + '\n')
                    repeat_handle.flush()
                    assert not errors(accepted), ('Policy exception on exact repeat', name)
                assert not interrupted(accepted), ('Repeated deadline failures', name, row['fixture_id'])
                clean[name].append(accepted)
                accepted_handles[name].write(json.dumps(accepted) + '\n')
                accepted_handles[name].flush()
            if (index + 1) % 20 == 0:
                print('Paired fixtures complete:', index + 1, '/', len(fixtures), flush=True)
    finally:
        runner._decide = original_decide
        for handle in [*handles.values(), *accepted_handles.values(), repeat_handle, environment_handle,slow_handle]:
            handle.close()
    for name in names:
        assert digest(originals[name]) == digest(Path(sources[name])) == protocol['sources'][name]['sha256']
        for label, data in [('raw', raw[name]), ('accepted', clean[name])]:
            assert len(data) == len(fixtures)
            summary = {'all': aggregate(data), 'by_opponent': {style: aggregate([r for r in data if r['opponent'] == opponents[style]]) for style in opponents}}
            (out / label / name / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (out / 'decision-histograms.json').write_text(json.dumps({'bin_width_ms': .025, 'raw_only': True, 'histograms': histograms}, indent=2) + '\n')
    metadata['finished_utc'] = datetime.now(timezone.utc).isoformat()
    metadata['cgroup_delta'] = delta(started_stat, cpu_stat())
    (out / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print('Completed raw and accepted paired records; no outcome-based repeats.', flush=True)


if __name__ == '__main__':
    main()
