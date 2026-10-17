"""Compare TITAN-10B-R with frozen TITAN-10B on shared native observations.

This is an instrumented behavior diagnostic, not tournament evidence. The
official runner measures each act separately at the normal 20 ms deadline.
Every movement, kick, debug field and non-cache controller state must match.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'student-sdk'))
from soccer import play_match, runner


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Guardiola2011


def action(value):
    return {k: v.as_dict() for k, v in value.players.items()}, value.debug


def state(controller):
    return {k: v for k, v in vars(controller).items() if not k.startswith('_runtime_')}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--challenger', type=Path, default=ROOT / 'experiments/titan-10b-r/team.py')
    p.add_argument('--against', nargs='+', default=[str(ROOT / 'champions/v9.1/team.py')])
    p.add_argument('--seeds', nargs='+', type=int, default=[1239849544])
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        p.error('Preserve prior results; choose a new output file.')
    paths = [ROOT / 'experiments/titan-10b/team.py', args.challenger.resolve()]
    classes = [load('behavior_original', paths[0]), load('behavior_runtime', paths[1])]
    original_decide = runner._decide
    records = []
    total = 0
    try:
        for opponent in args.against:
            for seed in args.seeds:
                for side in (0, 1):
                    for kickoff in (True, False):
                        driven_index = len(records) % 2
                        driven = classes[driven_index]()
                        shadow = classes[1 - driven_index]()
                        shadow.reset(seed)
                        count = 0
                        errors = []

                        def compare(controller, observation):
                            nonlocal count
                            actual = original_decide(controller, observation)
                            if controller is driven:
                                expected = original_decide(shadow, observation)
                                if actual[2] or expected[2]:
                                    raise AssertionError(('Policy exception', observation.tick, actual[2], expected[2]))
                                if action(actual[0]) != action(expected[0]) or state(driven) != state(shadow):
                                    raise AssertionError(('Behavior mismatch', opponent, seed, side, kickoff, observation.tick))
                                if expected[1] > 20.:
                                    errors.append({'tick': observation.tick, 'shadow_elapsed_ms': expected[1]})
                                count += 1
                            return actual

                        runner._decide = compare
                        teams = [driven, opponent] if side == 0 else [opponent, driven]
                        result = play_match(*teams, seed=seed,
                            kickoff_team=side if kickoff else 1 - side,
                            config_path=str(ROOT / 'configs/default.toml'),
                            max_ticks=2400, per_decision_timeout_ms=20.).result
                        assert count == 2400 and result['ticks'] == 2400
                        assert not any(s['policy_errors'] for s in result['stats'])
                        records.append({'opponent': opponent, 'seed': seed, 'candidate_side': side,
                            'candidate_kickoff': kickoff, 'driven_source': driven_index,
                            'compared_decisions': count, 'shadow_overruns': errors, 'result': result})
                        total += count
                        print('Exact actions and non-cache state:', len(records), 'fixtures,', total, 'observations', flush=True)
    finally:
        runner._decide = original_decide
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({'scope': __doc__, 'complete': total == len(args.against) * len(args.seeds) * 4 * 2400,
            'sources': [{'path': str(x), 'sha256': hashlib.sha256(x.read_bytes()).hexdigest()} for x in paths],
            'matched_decisions': total, 'records': records}, indent=2) + '\n')


if __name__ == '__main__':
    main()
