"""Render NOVA's actual frozen native evidence; never manufacture missing runs."""
import argparse, hashlib, json, math, re, zipfile
from pathlib import Path
from build import framework_for
from profile_replays import profile

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'docs/nova-1'


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distribution(path, name):
    data = read(path)
    hist = sorted((int(k), n) for k, n in data['histograms'][name].items())
    total = sum(n for k, n in hist)
    result = {'count': total, 'bin_width_ms': data['bin_width_ms']}
    for fraction in (.5, .95, .99, .999):
        count = 0
        for k, n in hist:
            count += n
            if count >= math.ceil(total * fraction):
                result[str(fraction)] = [k * data['bin_width_ms'], (k + 1) * data['bin_width_ms']]
                break
    return result


def make_archive(work, dest):
    """Whitelist native evidence, logs and source snapshots, not private scratch."""
    assert not dest.exists(), dest
    paths = [p for p in sorted(work.rglob('*')) if p.is_file()
             and p.suffix in ('.json', '.jsonl', '.log', '.py', '.rep')]
    # This file is an explicitly private working note, even if renamed later.
    assert all(p.name != 'STATUS.md' for p in paths)
    manifest = [{'path': str(p.relative_to(work)), 'bytes': p.stat().st_size,
                 'sha256': digest(p)} for p in paths]
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for p, row in zip(paths, manifest):
            archive.write(p, 'runs/' + row['path'])
        archive.writestr('manifest.json', json.dumps(manifest, indent=2) + '\n')
    with zipfile.ZipFile(dest) as archive:
        assert archive.testzip() is None
        for row in manifest:
            assert hashlib.sha256(archive.read('runs/' + row['path'])).hexdigest() == row['sha256']
    return {'path': str(dest.relative_to(ROOT)), 'sha256': digest(dest),
            'bytes': dest.stat().st_size, 'evidence_files': len(manifest),
            'uncompressed_bytes': sum(q['bytes'] for q in manifest),
            'excluded': 'Private STATUS.md and any non-whitelisted scratch assets.'}


def metric_table(before, after):
    fields = [('Fixtures', 'matches'), ('League points', 'points'), ('Wins', 'wins'),
              ('Draws', 'draws'), ('Losses', 'losses'), ('Goals scored', 'goals_for'),
              ('Goals conceded', 'goals_against'), ('Shots', 'shots'),
              ('Passes attempted', 'passes_attempted'), ('Passes completed', 'passes_completed'),
              ('Passes intercepted', 'passes_intercepted'),
              ('Uncollected passes (derived)', 'passes_uncollected_derived'),
              ('Turnovers', 'turnovers'), ('Policy exceptions', 'policy_errors'),
              ('Raw deadline misses', 'policy_timeouts')]
    lines = ['| Metric | Frozen v10.0 | NOVA-1 |', '|---|---:|---:|']
    for label, key in fields:
        lines.append(f'| {label} | {before[key]:,} | {after[key]:,} |')
    lines.append(f"| Pass completion | {before['pass_completion']:.1%} | {after['pass_completion']:.1%} |")
    lines.append(f"| Mean decision time | {before['decision_mean_ms']:.4f} ms | {after['decision_mean_ms']:.4f} ms |")
    lines.append(f"| Maximum decision time | {before['decision_max_ms']:.3f} ms | {after['decision_max_ms']:.3f} ms |")
    return '\n'.join(lines)


def generate(work, archive):
    selection = read(DOC / 'selected-policy.json')
    decision = read(DOC / 'decision.json')
    gates = read(DOC / 'qualification-gates.json')
    data = gates['accepted']
    raw = gates['raw']
    reg = read(DOC / 'registration.json')
    selected = selection['selected']
    population=[q for p in DOC.glob('generation-*-registration.json') for q in read(p)['population']]
    unique_vectors=len({tuple(q['vector']) for q in population})
    tests = (work / 'selected-regressions.log').read_text()
    count = re.search(r'Ran (\d+) tests?', tests)
    intake = read(work / 'qualification/nova-validation.json')
    assert digest(ROOT / selection['candidate_path']) == selection['candidate_sha256']
    assert digest(ROOT / 'my-team/team.py') == reg['champion_sha256']
    lines = [
        '# NOVA-1 native validation', '',
        '**Decision: ' + decision['status'] + '. No promotion or change to main/my-team/team.py.**', '',
        'The selected controller is an independently implemented five-player planner, not a TITAN tactical patch. '
        'The result below is a local native benchmark; it does not establish a school ranking or performance against private league leaders.', '',
        f"Frozen candidate: `{selection['candidate_path']}`, policy `{selected['name']}`, SHA-256 `{selection['candidate_sha256']}`. "
        f"Frozen v10.0 SHA-256: `{reg['champion_sha256']}`. Base main: `{reg['base_commit']}`.", '',
        '## Principal qualification', '',
        f"{data['paired_fixtures']:,} paired fixture configurations, {data['independent_seed_blocks']} whole-seed blocks, "
        '12 fixed opponent styles, both field assignments and both kickoff arrangements; 2,400 ticks per match with the official 20 ms wall deadline. '
        'Sources, protocols and the combined opponent archive were frozen before exposing heldout outcomes.', '',
        f"Accepted paired points/match delta: **{data['points_per_match_difference']:+.4f}**, whole-seed paired bootstrap 95% interval "
        f"**[{data['paired_seed_block_bootstrap_95'][0]:+.4f}, {data['paired_seed_block_bootstrap_95'][1]:+.4f}]** "
        '(5,000 resamples, fixed bootstrap seed). The independent unit is the match seed, not each mirrored fixture.', '',
        'Raw initial fixtures, including all original deadline misses:', '',
        metric_table(raw['baseline'], raw['challenger']), '',
        'First-clean exact repeats are used only for the paired football comparison; initial attempts and every failed repeat remain in the archive. '
        f"Accepted points: {data['baseline']['points']} v10.0 / {data['challenger']['points']} NOVA-1. "
        f"Raw extra deadline misses: **{gates['extra_raw_misses_per_1000']:+.4f} per 1,000 fixtures**. "
        f"Repeats that also missed a deadline: {gates['repeated_deadline_failures']}. "
        'No mean-time substitution or environmental exemption is applied to the raw deadline gate.', '',
        'Uncollected passes are the SDK-derived attempted − completed − intercepted count; they are not a separately annotated replay statistic. '
        'The SDK does not expose calibrated shot quality or goalkeeper saves.', '',
        '### Matchup results', '',
        '| Opponent | v10 pts | NOVA pts | NOVA W/D/L | NOVA goals | Δ points/match |',
        '|---|---:|---:|---|---|---:|',
    ]
    for path, row in sorted(data['by_opponent'].items(), key=lambda q: Path(q[0]).parent.name):
        name = Path(path).parent.name
        b, c = row['baseline'], row['challenger']
        lines.append(f"| {name} | {b['points']} | {c['points']} | {c['wins']}/{c['draws']}/{c['losses']} | "
                     f"{c['goals_for']}–{c['goals_against']} | {row['points_per_match_difference']:+.4f} |")
    unseen = gates['unseen']
    lines += ['',
        f"Sealed generated opponent styles: {unseen['paired_fixtures']} paired fixtures; "
        f"v10.0 {unseen['baseline']['points']} points, NOVA {unseen['challenger']['points']}; "
        f"paired delta {unseen['points_per_match_difference']:+.4f}, 95% interval {unseen['paired_seed_block_bootstrap_95']}. "
        'These are unseen parameterized local styles, not access to private school submissions. '
        'No heldout result was used for learning, candidate selection or a further tactical edit.', '',
        '### Registered gates', '', '| Gate | Pass |', '|---|---|']
    lines += [f"| {name} | {'yes' if okay else 'NO'} |" for name, okay in gates['flags'].items()]
    lines += ['',
        'The confirmation cohort remains untouched.' if decision['confirmation_cohort_remains_untouched'] else
        'The separately registered confirmation cohort was run after the principal qualification passed; see confirmation-gates.json.', '',
        '## Independent architecture and bounded execution', '',
        'NOVA defines its own roles, formations, possession classification, goalkeeper targeting, plan proposals, '
        'compatible five-player movement assignments and scoring. A prospective pass locks the intended receiver and moves support toward the '
        'predicted collection point while assigning separate defensive cover. Every pass requires an executable receiver rollout, '
        'first-touch feasibility and earlier arrival than every physically verified opponent interception. Heuristic chase estimates only choose movement targets.', '',
        'The low-level helper whitelist and exact hashes are in `nova-1/physics-provenance.json`. Source equivalence and '
        '2,000 randomized movement/reach/contact comparisons, dense wall trajectories and executable receiver comparisons test the reuse. '
        'No TITAN act(), tactical selection, defensive shape or goalkeeper policy is inherited.', '',
        'Promising complete team plans are evaluated against pressing and blocking/rushing opponent responses. '
        'The online bound is three plans × two responses × ten simulation steps (60 steps), with five pass launch trials, '
        'bounded receipt aims and shared dense flight/step forecasts. The short model uses acceleration, damping, speed caps, '
        'kick cooldown, body/wall restitution and player separation; future opponent input and future one-touch choices are hypotheses, '
        'not exact guarantees. Exact frozen helpers verify the pass and first kick. The policy embeds 8 geometry/risk parameters and 12 '
        'linear weights (19 active search dimensions); it imports only math and the permitted soccer SDK.', '',
        '## Development and actual learning budget', '',
        f"{selection['total_evaluated_variants']} native policy evaluations, {selection['unique_parameter_sources']} distinct source hashes, "
        f"{unique_vectors} distinct 19-dimensional parameter vectors. Retained elites are not counted as new parameter discoveries. "
        'Cross-entropy populations contain 24 policies, six elites and two retained parameter elites. Each policy plays 24 full native '
        'fixtures on a rotating six-style development league. The objective is paired points/match + 0.25 worst-style delta + '
        '0.15 mean of the two worst-style deltas. Pass counts never determine fitness. Repeated baseline fixtures across population batches '
        'are not additional independent seeds.', '',
        '### Per-generation best on that generation’s development fixtures', '',
        '| Generation | Framework | Policies | Best policy | NOVA/v10 points | Paired Δ | Robust objective |',
        '|---|---|---:|---|---|---:|---:|']
    for path in sorted(DOC.glob('generation-*-results.json')):
        rows = read(path)
        g = int(path.name.split('-')[1]); b = rows[0]
        framework = framework_for(b['name']).upper()
        lines.append(f"| {g} | {framework} | {len(rows)} | {b['name']} | {b['points']}/{b['baseline_points']} | "
                     f"{b['paired_ppm']:+.4f} | {b['objective']:+.4f} |")
    lines += ['',
        'Generations use different development seeds/styles; these raw point totals are not causal comparisons of architecture revisions. '
        'All parameter vectors, source hashes, framework snapshots and outcomes are retained. R4/R5/R6 source reconstruction must reproduce their exact hashes.', '',
        'The initial population uses frozen R4. Development then exposed keeper carry/recovery and future receipt ownership inconsistencies; '
        'R5 corrects those command contracts, preserves support runs and models advancing carry pursuit. R6 prevents three similar cheap-ranked '
        'plans starving a distinct feasible action family from the same three-plan response budget. Each change has a focused regression, was frozen '
        'before its generation and used development data only. No measured population source was edited.', '',
    ]
    failed_intakes = [q for path in DOC.glob('generation-*-results.json') for q in read(path) if not q['intake_ok']]
    lines += [f"Failed training intake evaluations: {len(failed_intakes)}. Their source hashes are ineligible for shortlist selection; "
        'the native measurements and original validation reports remain in the evidence. A fast mean never cancels a failed intake.', '']
    if failed_intakes:
        lines += ['| Failed source | Original SDK error |', '|---|---|']
        for row in failed_intakes:
            validation = read(work / Path(row['run']).name / (row['name'] + '-validation.json'))
            lines.append(f"| {row['name']} | {'; '.join(validation['errors'])} |")
        lines += ['', 'Public-intake timing failures do not have the native fixture slow-call CPU/GC instrumentation, '
            'so the evidence cannot establish their cause. They remain failures regardless of the later native timing.', '']
    release_path = DOC / 'release-experiment-decision.json'
    if release_path.exists():
        release = read(release_path)
        lines += ['### Isolated first-command contact experiment', '',
            'Four native development replays of frozen g02-p00 exposed a carrier-body reversal: at tick 495, '
            'a forward carry request produced vx=−11.6259 after contact, while a legal braking first command preserved vx=+6.1468. '
            'The case is a physical regression, not proof that braking wins games. Across those instrumented diagnostic games '
            '33 named receivers touched their passes, 6 plans were superseded, 4 had another player touch first and 1 was unfinished; '
            '16/179 isolated predicted launches differed from the next native position by more than half a unit, excluding goal resets. '
            'Other-player collisions and opponent actions are not covered by an isolated carrier witness. '
            'The diagnostic harness observes extra state, so none of its timing is used for qualification.', '',
            'Pass-only and carry-only first-command changes were then tested independently with identical learned weights on '
            '32 paired configurations per source, four strong styles and two unused development seeds. '
            'Each chooses between the ordinary movement and a legal brake by post-contact velocity error, '
            'before the existing physical pass verifier. It compares two cheap contact trials per option and keeps one launch, without an additional expensive pass race. '
            'A combined test runs only if both isolated features help. The registered development selection rules and all failures remain in the branch.', '',
            '| Variant | Points | Δ points/match vs R6 | Worst-style Δ vs R6 | Eligible |',
            '|---|---:|---:|---:|---|']
        for name, b in release['independent_results'].items():
            relative = b['relative_to_r6']
            lines.append(f"| {name} | {b['points']} | {relative['ppm_delta']:+.4f} | {relative['worst_style_delta']:+.4f} | {'yes' if b['eligible'] else 'no'} |")
        lines += ['', f"Framework for uncreated generations 3–5: **{release['framework']}**. "
            f"Combined native test run: {release['combined_test_run']}. "
            'The scheduler was paused between complete native batches for diagnostics; no decision was paused and no measured population source changed. '
            'This development study used no qualification or heldout result.', '']
        if release['combined_test_run']:
            lines += ['Fresh combination cohort:', '', '| Variant | Points | Δ points/match vs R6 |', '|---|---:|---:|']
            for name, b in release['selection_results'].items():
                lines.append(f"| {name} | {b['points']} | {b['relative_to_r6']['ppm_delta']:+.4f} |")
            lines.append('')
    retention_path=DOC/'retention-results.json'
    if retention_path.exists():
        retention=read(retention_path)
        lines += ['### Controlled-body retention experiment', '',
            'The first shortlist exposed a large competitive deficit (best 83 vs v10.0 238 points). '
            'A slow-shot goalkeeper hypothesis had no matching missed-goal case in the available development traces, so the goalkeeper was left unchanged. '
            'A separate action-space limitation was concrete: every selected carrier plan requested a kick. '
            'An isolated experiment adds movement-only retention when the first step produces a controllable body touch and no verified opponent '
            'interception in the first 0.10 seconds. Otherwise the existing kicked carries remain. '
            'The chosen drive movement continues in its short response model; act() can issue movement without a kick. '
            'Passing verification, shooting, goalkeeper behavior and defensive roles remain unchanged. '
            'The same three-plan × two-response × ten-step bound is retained.', '',
            'The reference is the frozen first-shortlist winner with identical weights. Both sources and v10.0 play '
            '64 configurations over eight known styles, two separate unused development seeds and both sides/kickoffs.', '',
            '| Source | Points | Δ points/match vs reference |', '|---|---:|---:|',
            f"| Existing reference | {retention['reference']['points']} | 0 |",
            f"| Body retention | {retention['body_retention']['points']} | {retention['relative_ppm']:+.4f} |", '',
            f"Adopted for uncreated generation 5: **{retention['adopted']}**. "
            'The existing generation-4 population stays byte-frozen. The original promotion gates and sealed cohorts remain unchanged. '
            'Focused regressions require an actual movement-only action for a controllable contact and reject retention of a fast ball or an imminent tackle.', '']
    response_path=DOC/'response-results.json'
    if response_path.exists():
        response=read(response_path)
        lines += ['### Initially available opponent kicks', '',
            'A separate model regression exposes an optimistic first step: the previous response model never let a ready defender kick until step 1. '
            'With a ready defender beside the ball, two opposing legal impulses cancel a close shot that the delayed model counted as a goal. '
            'R9 changes only the pressing response to allow an opponent kick on step 0. '
            'Own uncommanded follow-up shots remain forbidden on step 0; the blocking response retains its one-step lag. '
            'The budget stays at three plans × two responses × ten steps.', '']
        if response.get('skipped'):
            lines += [response['skipped'], '']
        else:
            lines += ['This follow-up was registered before population selection ended and before any sealed outcome. '
                'It reuses the population winner’s learned 19 parameters without retuning. '
                'A 64-configuration screen uses two unused development seeds; a separate 128-configuration check on four more development seeds '
                'runs only if the screen helps. Both cohorts must improve paired points without the registered style/head regressions, '
                'pass SDK intake and raise no exceptions. Population snapshots and the original selection remain preserved.', '',
                '| Development stage | Reference pts | Immediate-response pts | Δ points/match | Eligible |',
                '|---|---:|---:|---:|---|']
            for name in ('screen','check'):
                row=response.get(name)
                if row is not None:
                    lines.append(f"| {name} | {row['reference']['points']} | {row['press_response']['points']} | {row['delta_ppm']:+.4f} | {'yes' if row['eligible'] else 'no'} |")
            lines += ['',f"Adopted: **{response['adopted']}**. Learned parent: `{response['population_policy']}`. "
                'The original promotion gates, principal qualification seeds and conditional competition confirmation remain unchanged.', '']
    lines += ['### Development selection', '', '| Stage | Selected policy | NOVA/v10 points | Paired Δ | Worst-style Δ |', '|---|---|---|---:|---:|']
    for path in sorted(DOC.glob('selection-*-results.json')):
        b = read(path)[0]
        lines.append(f"| {path.stem} | {b['name']} | {b['points']}/{b['baseline_points']} | {b['paired_ppm']:+.4f} | {b['worst_style_ppm']:+.4f} |")
    lines += ['',
        'Each shortlist uses 128 fixture configurations per candidate on four development seeds, with up to eight distinct intake-passing sources. '
        'The registered extra two generations run only if the first shortlist remains weaker or fragile. '
        'Failed intake hashes are ineligible for selection. Training, shortlists, qualification and conditional confirmation use disjoint seed cohorts.', '']
    if (DOC / 'ablation-results.json').exists():
        ablation = read(DOC / 'ablation-results.json')
        lines += ['### Independent development diagnostics', '',
            'Preregistered after the architecture fixes but before source selection: 64 paired configurations per source on two separate development seeds. '
            'These diagnostics neither select parameters nor replace the frozen candidate. They isolate response evaluation with identical learned '
            'weights and compare learned vs default parameters within the same framework.', '',
            '| Model | NOVA/v10 points | Paired Δ | Worst-style Δ |', '|---|---|---:|---:|']
        for name, b in ablation['models'].items():
            lines.append(f"| {name} | {b['points']}/{b['baseline_points']} | {b['paired_ppm']:+.4f} | {b['worst_style_ppm']:+.4f} |")
        lines += ['', 'Negative ablations are retained; architectural complexity alone is not evidence of competitive value.', '']
    lines += ['### Preserved failures', '',
        'The first independent baseline passed the public short SDK check but raised two IndexErrors in a full native game. '
        'At tick 1352 the conservative forecast had already stopped near the opponent goal aperture while the native engine still supplied a live ball '
        '(x=49.9508247375, y=5.5898900032). R2 handles an empty forecast using the observed live position. '
        'The original source, partial native rows, failure frame and logs remain available.', '',
        'The 32-configuration R2 screen scored v10.0 63 points, open-loop NOVA 32 and joint NOVA 29. '
        'These failures were retained and motivated development-only corrections; neither was called a champion. '
        'An observer assertion initially used the wrong argument in one test; its failed log is retained alongside the corrected test run.', '',
        '## Timing evidence', '',
        'Raw decision distributions use the unmodified SDK wall timer in 0.025 ms bins. Intervals below are bin bounds, not more precise measurements.', '',
        '| Source | Median ms | p95 ms | p99 ms | p99.9 ms |', '|---|---|---|---|---|']
    runtime = {}
    for name in ('v10', 'nova'):
        runtime[name] = distribution(work / 'qualification/decision-histograms.json', name)
        q = runtime[name]
        fmt = lambda key: f"[{q[key][0]:.3f}, {q[key][1]:.3f})"
        lines.append('| ' + name + ' | ' + ' | '.join(fmt(str(f)) for f in (.5, .95, .99, .999)) + ' |')
    slow = [json.loads(s) for s in (work / 'qualification/slow-decisions.jsonl').read_text().splitlines()]
    observations = {}
    for name in ('v10', 'nova'):
        rows = [q for q in slow if q['source'] == name]
        deadlines = [q for q in rows if q['sdk_wall_ms'] > 20.]
        observations[name] = {'calls_ge_5ms': len(rows), 'raw_calls_gt_20ms': len(deadlines),
            'slow_calls_with_gc_overlap': sum(bool(q['gc_overlap']) for q in rows),
            'deadline_calls_with_gc_overlap': sum(bool(q['gc_overlap']) for q in deadlines),
            'deadline_wall_cpu_gap_gt_5ms': sum(q['sdk_wall_ms'] - q['thread_cpu_ms'] > 5. for q in deadlines)}
    lines += ['',
        'The external harness records thread CPU and GC overlap on the original slow calls for both controllers, and per-fixture cgroup/wall/CPU changes. '
        'GC policy, clocks, affinity, SDK and engine remain unchanged. Correlation with GC or a wall/CPU gap is diagnostic evidence, '
        'not proof of a sole cause and never grounds to discard a raw miss.', '',
        '```json', json.dumps(observations, indent=2), '```', '']
    replay_profile=read(work/'offline-profile/summary.json')
    lines += ['### Offline decision replay and hotspots', '',
        f"{replay_profile['native_frames_replayed']} recorded native frames reconstructed with pre-decision state and native kick/control gates; "
        f"action mismatches: {replay_profile['action_mismatches']}. Maximum evaluated plans/steps: "
        f"{replay_profile['max_response_plans']}/{replay_profile['max_model_steps']}. "
        'This checks command replay, not the accuracy of hypothetical opponent responses. '
        'The separate cProfile replay adds overhead and uses Python observation records; its timings never enter a deadline gate.', '',
        '| Function | Calls | Own ms | Cumulative ms |', '|---|---:|---:|---:|']
    for row in replay_profile['function_profile'][:12]:
        lines.append(f"| {row['function']} | {row['calls']:,} | {row['self_ms']:.2f} | {row['cumulative_ms']:.2f} |")
    lines += ['',
        '## Reproduction and evidence', '',
        f"Final regression run: {count.group(1) if count else 'see archived log'} tests; "
        f"official candidate intake: {intake['stats']['decisions']:,} decisions, passed={intake['ok']}. "
        'The complete regression log and SDK intake JSON are retained. All registered population sources are rebuilt and hash-checked by a regression; '
        'the selected-source test also verifies the measured frozen policy and actual finite five-player commands.', '',
        'Run from this branch with the official student SDK/native engine installed:', '',
        '```bash',
        'python -m unittest discover -s tests -q',
        'python tools/nova/rebuild_population.py --out work/nova-rebuilt',
        'python tools/nova/replay_registered.py --protocol docs/nova-1/qualification-protocol.json --out work/nova-qualification-replay',
        'python tools/nova/replay_registered.py --protocol docs/nova-1/g00-batch00-protocol.json --population work/nova-rebuilt --out work/nova-g00-replay',
        '```', '',
        'The training program deliberately refuses to overwrite existing source registrations or evidence. '
        'The full search command is `python tools/nova/train.py --work <fresh-evidence-directory>` in a clean development checkout '
        'with generated generation/selection files absent. `qualify.py` then freezes the source and principal protocol and conditionally confirms. '
        'From this populated final branch, the replay tool above verifies original source hashes and relocates only their paths in a new protocol; '
        'it preserves the original seeds, styles, ordering and limits. '
        'Reconstruction uses explicit generation-specific framework snapshots; it does not substitute the latest template for old policies.', '',
        'New searches can differ because intake eligibility and the last timing tie-break depend on new measurements. '
        'Exact registered source reconstruction and frozen-protocol replay remain available; no claim of identical timing or identical new search results across machines is made.', '',
        f"Evidence archive: `{archive['path']}`, SHA-256 `{archive['sha256']}`; "
        f"{archive['evidence_files']:,} manifest-verified files, {archive['bytes']:,} compressed bytes. "
        'It retains native raw/accepted records, all repeat attempts, source/opponent snapshots, intake reports, environments, slow-call evidence, '
        'histograms, partial failed runs and test logs. Private scratch notes are excluded. '
        'Registered parameters, sources, protocols, fixed opponent archives and tests are committed separately.', '',
        'No generated controller needs this evidence, trainer, parameter files or any other Python file at runtime. '
        'The candidate remains a development experiment unless all registered promotion gates and confirmation pass and the user explicitly approves promotion.', '']
    (DOC / 'runtime-analysis.json').write_text(json.dumps({'histogram_intervals': runtime, 'original_slow_calls': observations}, indent=2) + '\n')
    (DOC / 'evidence-archive.json').write_text(json.dumps(archive, indent=2) + '\n')
    target = ROOT / 'docs/nova-1-validation.md'
    target.write_text('\n'.join(lines))
    print(target)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--archive', type=Path, default=ROOT / 'tests/fixtures/nova-1-native-evidence.zip')
    args = p.parse_args()
    profile(args.work/'execution-replays',args.work/'offline-profile')
    archive = make_archive(args.work, args.archive)
    generate(args.work, archive)


if __name__ == '__main__':
    main()
