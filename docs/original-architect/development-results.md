# Unchanged Original Architect — development

**Decision: RETAIN_V10. v10 remains champion.**

Frozen sources from 906f7b9; 384 paired configurations across 12 fresh seed blocks and 8 styles, both sides and both kickoffs. There are 768 original full native matches. Every game uses 2400 ticks, engine 0.1.0, configuration 372990895c7eca2a and the native 20 ms deadline. One worker; no policy, SDK, physics or configuration changes.

## Original raw outcomes

| Source | Matches | W–D–L | Points | GF–GA | Completed/attempted passes | Completion | Turnovers | Raw misses | Exceptions |
|---|---:|---|---:|---|---|---:|---:|---:|---:|
| v10 | 384 | 188–99–97 | 663 | 664–399 | 7888/14894 | 52.9609% | 2190 | 1 | 0 |
| architect | 384 | 182–102–100 | 648 | 653–417 | 7975/14817 | 53.8233% | 2209 | 11 | 0 |

Repeat-selection status: 2 selected rows still contain a timeout after the three-repeat cap. The `accepted/` directory is the retained repeat-selected tier: first clean if available, otherwise the last unresolved attempt. Unresolved rows are diagnostic only and always disqualifying; they are not described as deadline-clean evidence.

Every original row and miss is retained. Exact timeout repeats take the first clean run regardless of score; they never erase raw outcomes or reliability failures. Both raw and accepted comparisons must pass.

## Whole-seed statistics

| Records | PPM change | Selection interval | Exact one-sided p |
|---|---:|---|---:|
| raw | -0.039062 | [-0.221354, +0.182292] | 0.656250 |
| accepted | -0.039062 | [-0.221354, +0.182292] | 0.656250 |

Balanced integer whole-seed point sums preserve all styles/sides/kickoffs and avoid floating-point zero drift. Development retains the previous 97.5% positive-lower-bound/exact-p ≤ 0.025 criteria, with 10,000 bootstrap resamples, RNG 719331. Qualification requires the original 95% positive lower bound, 5,000 resamples and exact-p ≤ 0.05. Qualification is a separate 16-seed, 12-style, 768-pair cohort; development is never reused as qualification.

| Opponent | v10 points | Architect points | v10 GF–GA | Architect GF–GA |
|---|---:|---:|---|---|
| v10 | 62 | 64 | 67–67 | 66–73 |
| v10-press | 58 | 67 | 55–62 | 65–61 |
| v10-compact | 61 | 79 | 37–36 | 36–24 |
| v10-counter | 88 | 78 | 87–58 | 77–58 |
| v10-long | 73 | 60 | 72–64 | 62–74 |
| v9.1 | 62 | 57 | 61–66 | 67–77 |
| tight_links | 126 | 112 | 132–32 | 118–37 |
| wide_switch | 133 | 131 | 153–14 | 162–13 |

## Executions and runtime

Executed Architect support commands: 1674; team-level episodes: 1271. Only matching final commands accepted under 20 ms count. A movement is not proof of a completed pass or a caused goal; the native match metrics establish outcomes.

Accepted mean ms: v10 0.243302, Architect 0.267218; ceiling 0.368458. Architect raw max 198.965624ms. Extra raw misses/1000: 26.041667. Additional full exact repeats: 22.

First exact repeats with candidate misses: 2; same public-input miss recurrence: 0. All raw and repeat calls have the same wall/thread CPU/GC tracing and slow-call public-input hashes. Whole-fixture recurrence does not prove a deterministic code hotspot. Any first-repeat candidate miss still fails the conservative gate; unresolved repeats also disqualify. No miss is waived.

## Registered gates

| Gate | Result |
|---|---|
| raw_more_points | FAIL |
| raw_positive_seed_lower | FAIL |
| raw_exact_significance | FAIL |
| accepted_more_points | FAIL |
| accepted_positive_seed_lower | FAIL |
| accepted_exact_significance | FAIL |
| zero_policy_exceptions | PASS |
| no_candidate_timeout_on_first_exact_repeat | FAIL |
| all_exact_repeats_resolved | FAIL |
| raw_deadline_allowance | FAIL |
| accepted_mean_runtime | PASS |
| official_sdk | PASS |
| legal_actions | PASS |
| complete_registered_cohort | PASS |
| no_style_points_regression | FAIL |
| more_completed_passes | PASS |
| no_extra_turnovers | FAIL |
| five_executed_support_episodes | PASS |

## Interpretation

Whole-cohort changes: points -15; goals scored -11; conceded +18; completed passes +87; turnovers +19. Opponent subtotals never replace these totals. Failed gates: raw_more_points, raw_positive_seed_lower, raw_exact_significance, accepted_more_points, accepted_positive_seed_lower, accepted_exact_significance, no_candidate_timeout_on_first_exact_repeat, all_exact_repeats_resolved, raw_deadline_allowance, no_style_points_regression, no_extra_turnovers.

Only a complete development pass authorizes the registered qualification. Even a full qualification pass permits a recommendation, not promotion. Main and the active champion require explicit user approval. Fixed public local opponents cannot prove private league standings.

## Reproduction

`PYTHONPATH=student-sdk python tools/original_architect/run.py --protocol docs/original-architect/development-protocol.json --out /new/run/path`; then `python tools/original_architect/analyze.py --run /new/run/path --out /new/results.json`. Use one timed worker. Frozen sources/opponents, original and repeat matches, SDK intakes, wall/CPU/GC/input traces, per-match histograms and cgroup diagnostics are retained.
