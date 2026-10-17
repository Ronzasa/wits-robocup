"""Replay frozen public observations or captured slow decisions for CPU diagnosis.

Not tournament evidence: the replay follows recorded observations, not actions.
Use: python tools/profile_titan11.py SOURCE --out NEW.json [--profile] [--worst]
The native equivalence check is tools/verify_passing_runtime.py --baseline ... .
"""
import argparse
import cProfile
import gc
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import pstats
import sys
import time
from types import SimpleNamespace as S

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'student-sdk'))


def decode(row, field):
    kickers = frozenset(row['kickers'])
    return S(tick=row['tick'], score=row['score'], ball=S(**row['ball']),
             my_players=[S(**p) for p in row['my_players']],
             opponents=[S(**p) for p in row['opponents']], field=field,
             can_kick=kickers.__contains__)


def restore(value):
    if isinstance(value, list):
        return tuple(restore(v) for v in value)
    if isinstance(value, dict):
        return {(int(k) if k.lstrip('-').isdigit() else k): restore(v)
                for k, v in value.items()}
    return value


def timing(values):
    values = sorted(values)
    return {'mean': sum(values)/len(values), 'p95': values[int((len(values)-1)*.95)],
            'p99': values[int((len(values)-1)*.99)], 'p999': values[int((len(values)-1)*.999)],
            'max': values[-1], 'over20': sum(v > 20. for v in values)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--profile', action='store_true')
    p.add_argument('--worst', action='store_true')
    args = p.parse_args()
    if args.out.exists():
        p.error('Preserve previous evidence; choose a new output.')
    spec = importlib.util.spec_from_file_location('profiled_titan11', args.source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixture = 'titan-11-worst.json.gz' if args.worst else 'titan-11-observations.json.gz'
    with gzip.open(ROOT / 'tests/fixtures' / fixture, 'rt') as f:
        rows = json.load(f)
    wall, cpu, gc_events, gc_start = [], [], [], {}
    fingerprint = hashlib.sha256()
    profiler = cProfile.Profile(timer=time.process_time) if args.profile else None

    def observe_gc(phase, info):
        gen = info['generation']
        if phase == 'start':
            gc_start[gen] = time.perf_counter_ns()
        else:
            gc_events.append({'generation': gen,
                'ms': (time.perf_counter_ns()-gc_start.pop(gen, time.perf_counter_ns()))*1e-6})

    def run(c, obs):
        if profiler:
            profiler.enable()
        start_cpu, start_wall = time.process_time_ns(), time.perf_counter_ns()
        action = c.act(obs)
        wall.append((time.perf_counter_ns()-start_wall)*1e-6)
        cpu.append((time.process_time_ns()-start_cpu)*1e-6)
        if profiler:
            profiler.disable()
        value = {'players': {str(k): v.as_dict() for k, v in action.players.items()}, 'debug': action.debug}
        fingerprint.update(json.dumps(value, sort_keys=True).encode())

    gc.callbacks.append(observe_gc)
    try:
        for row in rows:
            field = S(**row['field'])
            if args.worst:
                for _ in range(20):
                    c = module.Guardiola2011()
                    c.__dict__.update(restore(row['state_before']))
                    obs = decode(row['observation'], field)
                    obs.score = tuple(obs.score)
                    run(c, obs)
            else:
                c = module.Guardiola2011()
                c.reset(row['seed'])
                for raw in row['observations']:
                    run(c, decode(raw, field))
    finally:
        gc.callbacks.remove(observe_gc)
    report = {'source': str(args.source), 'sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
              'scope': __doc__, 'fixture': fixture, 'profiled': args.profile,
              'decisions': len(wall), 'wall_ms': timing(wall), 'cpu_ms': timing(cpu),
              'actions_sha256': fingerprint.hexdigest(), 'gc_events': gc_events}
    if profiler:
        profiler.dump_stats(str(args.out)+'.pstats')
        stats = pstats.Stats(profiler)
        report['profile_top'] = [{'method': k[2], 'calls': v[1], 'self_cpu_s': v[2],
                                 'cumulative_cpu_s': v[3]}
            for k,v in sorted(stats.stats.items(), key=lambda x:x[1][3], reverse=True)[:40]]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('gc_events','profile_top')}, indent=2))


if __name__ == '__main__':
    main()
