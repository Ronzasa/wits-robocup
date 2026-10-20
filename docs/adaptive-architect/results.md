# Adaptive Passing Lane Architect — native development results

**Decision: RETAIN_V10_REJECT_ADAPTIVE.** Frozen v10, the original Architect, main and the active champion are unchanged.

## Method and frozen scope

Continued from commit 906f7b9 on a new experimental branch. Sixteen unused development seed blocks × pressing, compact and counterattacking v10 variants × both pitch assignments × both kickoffs = 192 matched configurations per source and 576 full native matches. The three independent sources are frozen v10, original Architect and Adaptive Architect. Counterattack Firewall and the four earlier experimental tactics are disabled in every tested source.

Every match used 2,400 ticks, engine 0.1.0, configuration 372990895c7eca2a and the native 20 ms deadline. One timed worker ran after all 152 regressions passed. Sources, opponent archive, seeds, shuffle order and gates were registered before this cohort. Eight full public-seed diagnostic-probe matches verified completion counters before registration; they are retained but excluded from development outcomes. No development outcome tuning or cohort extension occurred. Sixteen other unused seeds remain reserved for qualification.

## Selective policy changes

- **Pressure detection:** requires at least two nearby defenders, at least two approaching the ball faster than 1.2 units/s, an existing ball-interception race no slower than 0.8 seconds and at least one blocked baseline support lane. Player positions, velocities and drag-aware flight-space checks drive the decision; no opponent names or style identifiers enter the controller. A stationary compact goal-side block suppresses support changes. Low pressure and open shape lanes retain v10 targets.
- **Verified advantage:** evaluates the baseline shape target and two local angle changes at two legal pass speeds. A new route needs the unchanged carrier-contact, drag/path, executable receiver race, opponent/body-interception and teammate-interference checks. Its exact first receiver movement includes teammate avoidance. The route must beat a physically verified baseline route by more than 0.35 score units, or create a verified route where the baseline has none. The score combines progress, actual arrival/margin and predicted defender space. This is a selection heuristic, not proof that a later pass will complete.
- **Authority:** excludes the carrier, goalkeeper, chaser, both cover assignments and existing receiver. Restarts, original counterpress and Klopp transition bursts retain priority. Opposing touches or unheld/stale control cannot create support assignments. There are no persistent support movement commands; every decision revalidates eligibility. Speculative receive-aim state is restored. Actual pass and shot selection, goalkeeper, cover and every original physics method remain unchanged.
- **Diagnostics:** bounded labels identify pressure, compact/low-pressure rejection, missing support, unsafe routes and insufficient gain. Only proposals matching final accepted movement commands count as activations. Pass plans carry receiver diagnostics. The external harness reads native completed-pass counters after engine steps, outside controller timing, and verifies their increments against final engine statistics for every original match. Recent-support/plan links are associations, not causal pass creation.

## Original raw native outcomes

| Source | Matches | Wins | Draws | Losses | Points | GF–GA | Passes completed/attempted | Completion | Turnovers | Deadline misses | Exceptions |
|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---:|
| v10 | 192 | 62 | 40 | 90 | 226 | 238–277 | 3959/7228 | 54.7731% | 1150 | 7 | 0 |
| architect | 192 | 78 | 37 | 77 | 271 | 260–272 | 4080/7353 | 55.4876% | 1173 | 6 | 0 |
| adaptive | 192 | 63 | 43 | 86 | 232 | 243–264 | 4069/7252 | 56.1087% | 1126 | 7 | 0 |

Native raw misses and competitive outcomes are never erased by repeats. Exact timeout repeats are retained separately; accepted and raw comparisons must both pass. No miss is waived as environmental noise.

## Paired significance and compact preservation

The preregistration requires more raw and accepted points than BOTH baselines, positive whole-seed 97.5% bootstrap lower bounds and exact one-sided whole-seed sign-flip p ≤ 0.025 against each comparator (a two-comparison correction). Bootstrap uses 10,000 resamples and fixed seed 719331; the exact test enumerates every sign assignment across the sixteen seed blocks. Every style, side and kickoff stays together within its seed.

| Comparator | Raw PPM change | 97.5% whole-seed interval | Exact p | Accepted PPM change |
|---|---:|---|---:|---:|
| v10 | +0.031250 | [-0.104167, +0.166667] | 0.339310 | +0.031250 |
| architect | -0.203125 | [-0.406250, +0.000000] | 0.978943 | -0.203125 |

Compact points must not fall below either comparator; compact concessions must not exceed v10. The original per-style preservation, total concessions, turnovers, completion-rate, SDK, legality, exception, timing and reproducibility checks also apply. Qualification retains the original 768-pair minimum and all original promotion gates; development does not waive them.

| Opponent | v10 points | Original points | Adaptive points | v10 GF–GA | Original GF–GA | Adaptive GF–GA |
|---|---:|---:|---:|---|---|---|
| v10-press | 80 | 104 | 85 | 80–97 | 93–82 | 78–89 |
| v10-compact | 66 | 84 | 61 | 46–75 | 62–68 | 45–68 |
| v10-counter | 80 | 83 | 86 | 112–105 | 105–122 | 120–107 |

## Actual executions, rejected opportunities and completions

### v10

Accepted diagnostic/command counts: `{}`.

Team-level episodes: `{}`.

Native completed-pass increments observed: 3959. Supported-receiver plan completion links: not instrumented in this frozen control (association only).

### architect

Accepted diagnostic/command counts: `{"architect_support": 901}`.

Team-level episodes: `{"architect_support": 678}`.

Native completed-pass increments observed: 4080. Supported-receiver plan completion links: not instrumented in this frozen control (association only).

### adaptive

Accepted diagnostic/command counts: `{"adaptive_pressure": 4306, "adaptive_reject_compact": 231, "adaptive_reject_low_pressure": 5134, "adaptive_reject_no_free_support": 35, "adaptive_reject_no_gain": 46, "adaptive_reject_no_movement_gain": 20, "adaptive_reject_no_verified_lane": 7431, "adaptive_support": 295, "adaptive_verified_gain": 541}`.

Team-level episodes: `{"adaptive_pressure": 2450, "adaptive_reject_compact": 220, "adaptive_reject_low_pressure": 2710, "adaptive_reject_no_free_support": 29, "adaptive_reject_no_gain": 42, "adaptive_reject_no_movement_gain": 20, "adaptive_reject_no_verified_lane": 2417, "adaptive_support": 235, "adaptive_verified_gain": 423}`.

Native completed-pass increments observed: 4069. Supported-receiver plan completion links: 51 (association only).

### Adaptive movement by opponent style

| Opponent | Executed support commands | Pressure diagnostics | Compact rejections | Native completions linked to a supported receiver plan |
|---|---:|---:|---:|---:|
| v10-press | 87 | 1341 | 62 | 13 |
| v10-compact | 117 | 1508 | 94 | 18 |
| v10-counter | 91 | 1457 | 75 | 20 |

## Interpretation

Adaptive gained 152 points over v10, completed 2758 more passes, conceded -159 fewer goals and recorded -756 fewer turnovers. These aggregate improvements do not establish a supported points advantage: the paired interval includes zero and the exact p-value versus v10 is 0.339310. It also trails original Architect by 39 points.

Compact opposition remained a failure: 61 points versus 66 for v10 and 84 for original Architect. The detector blocked stationary compact situations but still issued 117 support commands against the compact style, compared with 87 against pressing. Dynamic compact-opponent situations therefore still passed the pressure gate. This classifier did not deliver the required compact preservation.

Native telemetry recorded 295 executed support commands in 235 team-level episodes, and 51 native completions matching recently supported receiver plans. Those associations do not rescue the competitive failure or establish causal pass creation.

Adaptive had 7 original raw deadline misses and a first exact repeat incurred a candidate miss in 2 fixtures. Accepted clean repeats never remove the raw misses or the reproducibility failure. No timing event is waived; this independently blocks qualification.

Support labels identify final executed commands. All pressure/rejection/gain labels are diagnostics, not activations; a verified proposal can lose ownership to a later v10 reception command. Team-level episodes split after gaps longer than five ticks; two supporters can act in one tick. Completion traces, rejection/pressure examples, source snapshots and five-second goal/turnover associations are retained in the evidence. Associations are not causal claims.

## Reliability and gate decision

Accepted mean-runtime ceiling: 0.383166 ms. Adaptive mean: 0.275435 ms. Raw max: 110.937836 ms. Extra raw misses/1,000 fixtures: 0.000000. Candidate deadline failures reproduced on first exact repeat: 2.

| Gate | Result |
|---|---|
| raw_more_points_than_v10 | PASS |
| raw_positive_97_5_seed_lower_vs_v10 | FAIL |
| raw_exact_sign_flip_p_vs_v10 | FAIL |
| accepted_more_points_than_v10 | PASS |
| accepted_positive_97_5_seed_lower_vs_v10 | FAIL |
| accepted_exact_sign_flip_p_vs_v10 | FAIL |
| raw_more_points_than_architect | FAIL |
| raw_positive_97_5_seed_lower_vs_architect | FAIL |
| raw_exact_sign_flip_p_vs_architect | FAIL |
| accepted_more_points_than_architect | FAIL |
| accepted_positive_97_5_seed_lower_vs_architect | FAIL |
| accepted_exact_sign_flip_p_vs_architect | FAIL |
| compact_points_at_least_both | FAIL |
| compact_no_extra_concessions | PASS |
| no_style_points_regression_vs_v10 | FAIL |
| no_extra_overall_concessions | PASS |
| no_extra_turnovers | PASS |
| pass_completion_at_least_v10 | PASS |
| five_actual_adaptive_episodes | PASS |
| zero_policy_exceptions | PASS |
| no_reproduced_candidate_deadline_failure | FAIL |
| raw_deadline_allowance | PASS |
| mean_runtime | PASS |
| official_sdk | PASS |
| legal_actions | PASS |
| complete_registered_cohort | PASS |
| native_completion_trace_integrity | PASS |

Exact deadline-repeat fixtures: 33 additional full native matches, retained without erasing original outcomes or misses. The development cohort plus repeats and eight public diagnostic probes totals 617 recorded full matches. Official SDK intakes are separate.

## Verification and reproduction

152 regressions passed before development, including the inherited physics/safety suite and tests for closing versus receding defenders, compact/open-lane/slow-race rejection, protected player roles, low-pressure v10 command equivalence, no-gain rejection, physically feasible new lanes and speculative-state restoration. Native SDK intakes and legal actions are retained. Both old source hashes and every original v10 method except the two movement/telemetry hook call sites remain unchanged.

`python tools/adaptive_architect/build.py` reproduces the adaptive source while verifying frozen v10 and original Architect. After installing the bundled official extension, run `PYTHONPATH=student-sdk python -m unittest discover -s tests -q`; reproduce the cohort with `PYTHONPATH=student-sdk python tools/benchmarks/run_adaptive_architect.py --protocol docs/adaptive-architect/development-protocol.json --out /new/output/path`; analyze with `python tools/adaptive_architect/analyze.py --run /new/output/path --out /new/results.json`. Keep one timed native worker.

The evidence archive contains raw/accepted matches, exact repeats, full native completion traces, official intakes, frozen sources/opponents, histograms, slow-call/GC/CPU diagnostics, protocols and test logs, with a verified per-file SHA-256 manifest. Sixteen local seed blocks and three fixed public variants cannot establish performance against private league teams.

**Rejected for competitive use. No fresh qualification or promotion was run.** Failed gates: raw_positive_97_5_seed_lower_vs_v10, raw_exact_sign_flip_p_vs_v10, accepted_positive_97_5_seed_lower_vs_v10, accepted_exact_sign_flip_p_vs_v10, raw_more_points_than_architect, raw_positive_97_5_seed_lower_vs_architect, raw_exact_sign_flip_p_vs_architect, accepted_more_points_than_architect, accepted_positive_97_5_seed_lower_vs_architect, accepted_exact_sign_flip_p_vs_architect, compact_points_at_least_both, no_style_points_regression_vs_v10, no_reproduced_candidate_deadline_failure. The selective implementation is retained only as an experiment; activation counts are not an improvement claim.
