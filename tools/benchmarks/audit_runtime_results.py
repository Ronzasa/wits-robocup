"""Independently recompute the published TITAN-10B-R CSV and promotion gate."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[2]


def main():
    evidence = json.loads((ROOT / 'docs/titan-10b-r-results.json').read_text())
    with (ROOT / 'docs/titan-10b-r-paired-scores.csv').open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 720
    keys = ('split', 'style', 'seed', 'candidate_side', 'candidate_kickoff')
    assert len({tuple(x[k] for k in keys) for x in rows}) == 720
    assert len({x['style'] for x in rows}) == 15
    assert len({x['seed'] for x in rows}) == 12
    assert set(Counter(x['style'] for x in rows).values()) == {48}
    assert set(Counter(x['seed'] for x in rows).values()) == {60}
    for _, data in [('stress', [x for x in rows if x['split'] == 'stress']),
                    ('validation', [x for x in rows if x['split'] == 'validation'])]:
        assert len(data) == 360
    for source, aggregate in [('champion', 'baseline'), ('runtime', 'challenger')]:
        clean = evidence['comparison'][aggregate]
        raw = evidence['raw_comparison'][aggregate]
        for row in rows:
            for middle in ('', 'raw_'):
                gf = int(row[source + '_' + middle + 'gf'])
                ga = int(row[source + '_' + middle + 'ga'])
                assert int(row[source + '_' + middle + 'points']) == (3 if gf > ga else int(gf == ga))
            assert int(row[source + '_passes_uncollected']) == (
                int(row[source + '_passes_attempted']) - int(row[source + '_passes_completed'])
                - int(row[source + '_passes_intercepted']))
        for key, column in [('points', 'points'), ('goals_for', 'gf'), ('goals_against', 'ga')]:
            assert sum(int(x[source + '_' + column]) for x in rows) == clean[key]
            assert sum(int(x[source + '_raw_' + column]) for x in rows) == raw[key]
        for key in ('passes_attempted', 'passes_completed', 'passes_intercepted',
                    'turnovers', 'policy_errors', 'policy_timeouts', 'decisions'):
            assert sum(int(x[source + '_' + key]) for x in rows) == clean[key]
        assert sum(int(x[source + '_passes_uncollected']) for x in rows) == clean['passes_uncollected_derived']
        assert sum(int(x[source + '_raw_timeouts']) for x in rows) == raw['policy_timeouts']
        assert sum(int(x[source + '_raw_errors']) for x in rows) == raw['policy_errors']
        total_ms = sum(float(x[source + '_decision_total_ms']) for x in rows)
        assert math.isclose(total_ms / clean['decisions'], clean['decision_mean_ms'], rel_tol=1e-10)
        assert max(float(x[source + '_decision_max_ms']) for x in rows) == clean['decision_max_ms']
        total_raw_ms = sum(float(x[source + '_raw_decision_total_ms']) for x in rows)
        assert math.isclose(total_raw_ms / raw['decisions'], raw['decision_mean_ms'], rel_tol=1e-10)
        assert max(float(x[source + '_raw_decision_max_ms']) for x in rows) == raw['decision_max_ms']
        for key, column in [('control_fraction', 'controlled_ticks'), ('possession_fraction', 'possession_ticks')]:
            ticks = sum(int(x[source + '_' + column]) for x in rows)
            assert math.isclose(ticks / (720 * 2400), clean[key], abs_tol=1e-12)
    blocks = defaultdict(list)
    for row in rows:
        blocks[int(row['seed'])].append(int(row['runtime_points']) - int(row['champion_points']))
    order = []
    for split in ('stress', 'validation'):
        order.extend(sorted({int(x['seed']) for x in rows if x['split'] == split}, key=str))
    means = [sum(blocks[k]) / len(blocks[k]) for k in order]
    rng = random.Random(719331)
    bootstrap = sorted(sum(rng.choices(means, k=12)) / 12 for _ in range(5000))
    interval = [bootstrap[125], bootstrap[4874]]
    assert interval == evidence['comparison']['paired_seed_block_bootstrap_95']
    a, b = evidence['comparison']['baseline'], evidence['comparison']['challenger']
    ra, rb = evidence['raw_comparison']['baseline'], evidence['raw_comparison']['challenger']
    limit = a['decision_mean_ms'] * 1.35 + .04
    extra = (rb['policy_timeouts'] - ra['policy_timeouts']) * 1000 / 720
    gate = {
        'more_fresh_points': b['points'] > a['points'],
        'positive_seed_bootstrap_lower_bound': interval[0] > 0,
        'zero_policy_exceptions': rb['policy_errors'] == 0,
        'no_reproducible_deadline_failures': b['policy_timeouts'] == 0 and evidence['validations']['runtime']['stats']['over deadline'] == 0,
        'acceptable_mean_runtime': b['decision_mean_ms'] <= limit,
        'acceptable_raw_timeout_rate': extra <= 2.,
    }
    assert gate == evidence['decision']['gates']
    assert all(gate.values()) == evidence['decision']['eligible_for_v10_0']
    # Preserve the original branch-only gate decision as historical evidence.
    assert not evidence['decision']['promotion_to_main_performed']
    promotion = evidence.get('promotion')
    for path, expected in evidence['registration']['baselines'].items():
        historical_path = ROOT / path
        if promotion and path == 'my-team/team.py':
            historical_path = ROOT / promotion['replaced_champion_archive']
        assert hashlib.sha256(historical_path.read_bytes()).hexdigest() == expected
    for spec in evidence['protocol']['sources'].values():
        assert hashlib.sha256((ROOT / spec['path']).read_bytes()).hexdigest() == spec['sha256']
    if promotion:
        assert promotion['promoted'] and all(gate.values())
        assert promotion['source_sha256'] == evidence['source_freeze']['source_sha256']
        assert promotion['source_sha256'] == evidence['protocol']['sources']['runtime']['sha256']
        assert hashlib.sha256((ROOT / promotion['active_source']).read_bytes()).hexdigest() == promotion['source_sha256']
        validation = promotion['official_validation']
        assert validation['ok'] and validation['stats']['decisions'] == 2000
        assert validation['stats']['exceptions'] == validation['stats']['over deadline'] == 0
    print('Verified all 720 pairs, scores, pass/retention/runtime totals, raw deadlines, bootstrap, source hashes and original gates.')


if __name__ == '__main__':
    main()
