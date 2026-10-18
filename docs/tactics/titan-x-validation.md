# TITAN-X validation — four special-tactic experiments

**Decision: RETAIN_V10_0. The active v10.0 champion and main are unchanged.**

The four tactics were implemented as independently switchable additions to the frozen Guardiola/Klopp controller. All four flags are false in the initial manager. Four standalone one-flag sources, bounded physics checks, 120 regressions, targeted native tests, an independent common development set, and a frozen 768-pair qualification were completed.

## Independent targeted native tests

Each tactic played 16 complete fixtures, paired with v10, against its two registered relevant styles. Both pitch assignments and both kickoff arrangements were included. No match was shortened or initialized with a fabricated late-game score.

| Tactic | v10 points | Tactic points | v10 GF–GA | Tactic GF–GA | Actual command episodes |
|---|---:|---:|---:|---:|---|
| power | 28 | 28 | 20–13 | 20–14 | {'power_start': 2, 'power_advance_tick': 2, 'power_cancel': 2, 'power_recovery_tick': 2, 'power_home': 2} |
| trap | 31 | 31 | 52–12 | 52–12 | {} |
| pinball | 35 | 35 | 24–5 | 24–5 | {} |
| ambush | 37 | 35 | 47–9 | 45–12 | {'ambush_challenge': 4} |

## Independent common development set

Each one-flag candidate played the identical 96 configurations: six fixed styles × four development seeds × both sides × both kickoffs. One shared v10 result per configuration was paired with each candidate. Source order rotated in one serial worker. No threshold or flag was tuned from these outcomes.

| Tactic | v10 points | Tactic points | Paired PPM change [95% seed interval] | GF–GA | Raw misses v10 / tactic | Episodes |
|---|---:|---:|---|---:|---:|---|
| power | 142 | 139 | -0.0312 [-0.0625, +0.0000] | 165–104 | 0 / 1 | {'power_start': 21, 'power_advance_tick': 21, 'power_cancel': 18, 'power_recovery_tick': 20, 'power_home': 21, 'power_active': 1, 'power_cancel_cover': 2} |
| trap | 142 | 142 | +0.0000 [+0.0000, +0.0000] | 170–103 | 0 / 4 | {'trap_run': 10} |
| pinball | 142 | 142 | +0.0000 [+0.0000, +0.0000] | 169–103 | 0 / 0 | {} |
| ambush | 142 | 141 | -0.0104 [-0.1562, +0.1667] | 170–104 | 0 / 1 | {'ambush_challenge': 38} |

Selection: **trap**. Independently promising tactics: `[]`. Integration justified: `False`. Best-failure qualification only: `True`.

Inactive tactics are not carried forward merely for passing unit tests. The selection file states the preregistered rule and exact source hash. If development produced no supported tactic, the strongest failed standalone still underwent the requested fresh qualification; it was not silently declared a new champion.

The power play reached its active state only once in development and launched no keeper-recycling pass; most advances were cancelled. That is insufficient additional attacking involvement, and its points fell. The trap made ten run episodes, but no special trap pass. Its score changes were against quick_wall in matches v10 already won: some winning margins increased and some decreased, with no additional league points. The pinball produced no additional accepted pass, so it adds overhead without a measured opportunity. The ambush made 38 challenge episodes but did not improve points or goals conceded. These observations reject enabling the four initial hypotheses; they do not establish that every possible implementation of the concepts would fail.

The power-play prototype has a specific limitation: its advanced-ball and backward-velocity guards remain active after activation. They can cancel an attempted recycling phase as the ball returns toward the keeper. The keeper also has to travel while cover retreats. This implementation therefore does not demonstrate a stable five-player passing network. The trap/pinball selectors retain a conservative goal-bound-flight priority and productive-pass priority; their eligibility is much narrower than the raw number of attacks. Those limits are reported as failed development hypotheses, rather than relaxing guards after seeing qualification data.

## Frozen fresh qualification

768 matched configurations per source: 12 fixed styles × 16 fresh seed blocks × both sides × both kickoffs, 2,400 ticks each under the original native 20 ms deadline. Whole-seed bootstrap uses 5,000 resamples, fixed bootstrap seed 719331. Qualification outcomes were not used to change the source, choose flags, or extend the cohort.

| Metric | v10.0 | Selected TITAN-X |
|---|---:|---:|
| Points | 1492 | 1499 |
| Wins | 453 | 456 |
| Draws | 133 | 131 |
| Losses | 182 | 181 |
| Goals scored | 1603 | 1605 |
| Goals conceded | 724 | 728 |
| Passes attempted | 31248 | 31253 |
| Passes completed | 16164 | 16179 |
| Pass completion | 0.517281 | 0.517678 |
| Uncollected passes (derived) | 6243 | 6241 |
| Turnovers | 4181 | 4181 |
| Accepted mean ms | 0.213903 | 0.223110 |
| Raw deadline misses | 2 | 2 |
| Raw policy exceptions | 0 | 0 |
| Raw maximum ms | 26.914015994407237 | 26.620691998687107 |
| Raw p95 ms (bin upper) | 0.525 | 0.525 |
| Raw p99 ms (bin upper) | 2.025 | 2.075 |
| Raw p99.9 ms (bin upper) | 4.200 | 4.275 |

Paired points-per-match change **+0.009115**, 95% interval **[0.0, 0.0234375]**.
Extra raw misses per 1,000 fixtures: **0.000000** (maximum 2). Accepted mean ceiling: **0.328769 ms** (v10 × 1.35 + 0.04 ms).

| Gate | Result |
|---|---|
| more_points | PASS |
| positive_whole_seed_95_lower | FAIL |
| zero_policy_exceptions | PASS |
| no_reproducible_deadline_failure | PASS |
| raw_deadline_allowance | PASS |
| mean_runtime | PASS |
| official_sdk | PASS |
| legal_actions | PASS |
| fresh_fixture_count | PASS |

## Qualification matchups

| Opponent | v10 points | TITAN-X points | PPM change |
|---|---:|---:|---:|
| aggressive-keeper | 89 | 89 | +0.0000 |
| long_shooter | 160 | 158 | -0.0312 |
| quick_wall | 192 | 192 | +0.0000 |
| relay_legacy | 184 | 184 | +0.0000 |
| tight_links | 171 | 178 | +0.1094 |
| v10-compact | 112 | 112 | +0.0000 |
| v10-counter | 78 | 78 | +0.0000 |
| v10-long | 84 | 84 | +0.0000 |
| v10-press | 95 | 95 | +0.0000 |
| v10 | 89 | 89 | +0.0000 |
| v9.1 | 63 | 63 | +0.0000 |
| wide_switch | 175 | 177 | +0.0312 |

## Mechanical verification and timing

Focused regressions cover power eligibility, recovery and cooldown; observed keeper commitment; successful trap passing; post-side-wall collection; full-route cooldown body blocks and teammate interference; unreachable and moving receivers; cooldown challenge success/cancellation; bounded legal commands; unchanged champion hash; unchanged physics/shooting/keeper/cover ASTs; and all-off action/plan equivalence. The original 95 regressions also pass. All official five-public-seed intake records are retained.

Raw deadline diagnostics: 4 candidate-side misses across both sources; 0 overlap a GC callback; 0 show a wall-minus-thread-CPU gap above 5 ms. External observers do not replace SDK timings. No raw miss is waived as environmental noise. The archive includes exact-repeat rows, slow calls, raw timing histograms and cgroup deltas. Reproducible candidate deadline failures: 0.

Telemetry counts accepted commands under 20 ms, grouped into episodes. A run/challenge is not proof of collection. Goals and turnovers within five seconds of commands are associations, not causal goals-created estimates. Game-level engine outcomes and matched v10 comparisons are the performance evidence. Inactive tactics have no claimed incremental opportunities.

## Reproduction and retained evidence

`python -m unittest discover -s tests -q` runs regressions. `python tools/titan_x/build.py` reproduces the five initial standalone sources from frozen v10 and the fragment. Each protocol freezes exact source/opponent hashes before play. `python tools/benchmarks/run_titan_x.py --protocol docs/tactics/qualification-protocol.json --out /new/output/path` replays qualification in a fresh directory with the official engine installed. Run only one timed native worker.

Full native evidence: `tests/fixtures/titan-x-native-evidence.zip`, 2,308,407 bytes, 177 files; SHA-256 `6c1c4df69e6bb2d8d90c06217a175b915d4a35a6b7859c475e019343518a0606`. Every archived file has a SHA-256 entry in `evidence-manifest.json`; archive CRC and each entry were verified. All original raw results, first-clean exact repeats, validations, source snapshots, opponents, metadata and stage logs are preserved.

These are local fixed-opponent tests, not access to private league sources or proof of standings improvement. No main, active submission, champion, SDK, engine or competition configuration file was changed.
