# TITAN Physics Tactics: actual results

**Experimental branch only. Main and the active Elite Replay Cutback champion are unchanged.**

**Recommendation: keep the active Cutback champion. All three physics tactics are rejected for deployment.** Ambush did not show a significant points gain and exceeded the deadline limit; Wall-Brake lost points; Rebound Shot did not change points and failed reliability. The active reference earned 1,553 points in this fresh comparison.

All three tactics were implemented independently from frozen v10. No combinations were tested or deployed. The decision is governed by raw native match points, statistical significance, actual executions and reliability. A theoretical forecast, successful first touch or higher mean score alone cannot qualify a tactic.

## Qualification decision

| Tactic | Qualified against frozen v10 | Failed gates |
|---|---|---|
| ambush | NO | positive_paired95_lower, positive_familywise_lower, raw_deadlines |
| wall-brake | NO | more_raw_points, positive_paired95_lower, positive_familywise_lower |
| rebound-shot | NO | more_raw_points, positive_paired95_lower, positive_familywise_lower, no_reproduced_deadline, raw_deadlines |

Passing these gates would qualify an experiment against v10, not authorize replacing the current champion. The active Cutback reference is reported separately below.

The campaign completed **4,160 scheduled full native matches**, plus **57 identical timeout-fixture repeats**. Legal native physics fixtures and diagnostic execution replays are separate; they are not pooled into league points.

## Development and single revision

64 matched configurations per source, with two fresh seeds, eight frozen styles, both pitch assignments and both kickoff arrangements. These are the original R0 development sources. The final R1 sources are evaluated on untouched qualification seeds.

| Tactic | v10 points | Active points | R0 points | GF–GA | Raw misses |
|---|---:|---:|---:|---:|---:|
| ambush | 100 | 107 | 95 | 132–93 | 0 |
| wall-brake | 100 | 107 | 100 | 138–94 | 1 |
| rebound-shot | 100 | 107 | 100 | 137–93 | 0 |

The [development review](development-review.md) records the native failures, bounded revision and their regressions. The [revision manifest](revision.json) preserves original and final source hashes. No qualification result selected another implementation, changed a threshold, added seeds or extended the cohort.

## Frozen fresh qualification

768 matched configurations per source: 12 styles × 16 unused seed blocks × both sides × both kickoff arrangements. All sources and the protocol were committed before this cohort was opened. Each fixture uses the stock native engine, 2,400 ticks and the official 20 ms deadline, with one timed worker and rotating source order.

**All points, goals, pass metrics and deadline counts below are raw native results.** Exact clean repeats diagnose interrupted fixtures and do not replace raw outcomes in any gate.

| Metric | v10 | active | ambush | wall-brake | rebound-shot |
|---|---:|---:|---:|---:|---:|
| Points | 1435 | 1553 | 1437 | 1429 | 1435 |
| Wins | 428 | 473 | 429 | 427 | 428 |
| Draws | 151 | 134 | 150 | 148 | 151 |
| Losses | 189 | 161 | 189 | 193 | 189 |
| Goals scored | 1582 | 1739 | 1579 | 1578 | 1582 |
| Goals conceded | 805 | 705 | 802 | 811 | 805 |
| Passes attempted | 31800 | 31859 | 31719 | 31808 | 31795 |
| Passes completed | 16651 | 16632 | 16613 | 16667 | 16649 |
| Pass completion fraction | 0.523616 | 0.522050 | 0.523755 | 0.523988 | 0.523636 |
| Uncollected passes, derived | 6313 | 6374 | 6337 | 6306 | 6311 |
| Turnovers | 4073 | 4001 | 4047 | 4077 | 4073 |
| Policy exceptions | 0 | 0 | 0 | 0 | 0 |
| Raw deadline misses | 4 | 11 | 7 | 4 | 9 |
| Mean decision ms | 0.222354 | 0.234032 | 0.233817 | 0.228015 | 0.228385 |
| Maximum decision ms | 49.582125 | 86.590273 | 44.709887 | 50.797976 | 48.481440 |
| Raw p95 bin upper ms | 0.550 | 0.550 | 0.575 | 0.550 | 0.550 |
| Raw p99 bin upper ms | 2.075 | 2.075 | 2.075 | 2.125 | 2.100 |
| Raw p999 bin upper ms | 4.400 | 4.475 | 4.425 | 4.450 | 4.450 |

### Actual tactic executions

Counts below come from raw native observations. Plans and movement commands are reported separately from native wall contacts and receptions. A post-wall contact is a real first touch; immediate controlled possession is a separate measurement. A kick reception can immediately send the ball onward. Wall-Brake collection requires the named receiver; a passer re-kick does not count. A rebound-shot goal requires a confirmed native kick, verified native wall reflection and an uninterrupted goal by that shooter.

| Tactic | Plans | Ambush movement steps | Native launch kicks | Native bounces | Post-wall contacts | Immediate control | Rebound-shot goals | Open at whistle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ambush | 50 | 1261 | — | 48 | 48 | 11 | — | 0 |
| wall-brake | 9 | — | 9 | 9 | 9 | 6 | — | 0 |
| rebound-shot | 2 | — | 2 | 2 | — | — | 1 | 1 |

Complete execution counters, including interrupted or uncollected episodes, remain in the qualification result JSON and raw archive. Native goal/concession totals measure the whole independently modified controller; they are not all attributed to a single tactical episode.

### Paired significance and reliability

Ordinary paired 95% intervals use the unchanged comparison tool. The registered familywise test uses 20,000 whole-seed bootstrap resamples and a 98.333333% two-sided Bonferroni interval for the three comparisons against v10. Its lower bound must be strictly positive. This describes variation across local seeds against fixed opponents, not a probability of winning the school league.

#### ambush

Versus v10: points per match delta **+0.002604**, ordinary 95% interval **[-0.015625, 0.022135416666666668]**, familywise interval **[-0.018229166666666664, 0.02734375]**. Additional raw misses/1,000: **+3.906250**. Own deadline failures on exact repeats: **0**.

Versus active Cutback, context only: points per match delta **-0.151042**, ordinary 95% interval **[-0.2786458333333333, -0.013020833333333336]**.

| Registered gate vs v10 | Result |
|---|---|
| more_raw_points | PASS |
| positive_paired95_lower | FAIL |
| positive_familywise_lower | FAIL |
| zero_exceptions | PASS |
| no_reproduced_deadline | PASS |
| raw_deadlines | FAIL |
| mean_runtime | PASS |
| sdk_intake | PASS |
| legal_actions | PASS |
| fixture_count | PASS |
| actual_native_success | PASS |

#### wall-brake

Versus v10: points per match delta **-0.007812**, ordinary 95% interval **[-0.0234375, 0.0]**, familywise interval **[-0.03125, 0.0]**. Additional raw misses/1,000: **+0.000000**. Own deadline failures on exact repeats: **0**.

Versus active Cutback, context only: points per match delta **-0.161458**, ordinary 95% interval **[-0.2864583333333333, -0.03125]**.

| Registered gate vs v10 | Result |
|---|---|
| more_raw_points | FAIL |
| positive_paired95_lower | FAIL |
| positive_familywise_lower | FAIL |
| zero_exceptions | PASS |
| no_reproduced_deadline | PASS |
| raw_deadlines | PASS |
| mean_runtime | PASS |
| sdk_intake | PASS |
| legal_actions | PASS |
| fixture_count | PASS |
| actual_native_success | PASS |

#### rebound-shot

Versus v10: points per match delta **+0.000000**, ordinary 95% interval **[0.0, 0.0]**, familywise interval **[0.0, 0.0]**. Additional raw misses/1,000: **+6.510417**. Own deadline failures on exact repeats: **1**.

Versus active Cutback, context only: points per match delta **-0.153646**, ordinary 95% interval **[-0.2760416666666667, -0.02734375]**.

| Registered gate vs v10 | Result |
|---|---|
| more_raw_points | FAIL |
| positive_paired95_lower | FAIL |
| positive_familywise_lower | FAIL |
| zero_exceptions | PASS |
| no_reproduced_deadline | FAIL |
| raw_deadlines | FAIL |
| mean_runtime | PASS |
| sdk_intake | PASS |
| legal_actions | PASS |
| fixture_count | PASS |
| actual_native_success | PASS |

### Opponent breakdown

| Opponent | v10 points | Active points | Ambush | Wall-Brake | Rebound Shot |
|---|---:|---:|---:|---:|---:|
| aggressive-keeper | 90 | 102 | 89 | 89 | 90 |
| depth14-proxy | 86 | 116 | 85 | 86 | 86 |
| elite-cutback | 74 | 87 | 74 | 73 | 74 |
| long_shooter | 157 | 158 | 161 | 157 | 157 |
| quick_wall | 189 | 192 | 189 | 189 | 189 |
| tight_links | 175 | 176 | 176 | 175 | 175 |
| v10-compact | 110 | 131 | 107 | 110 | 110 |
| v10-counter | 114 | 103 | 116 | 114 | 114 |
| v10-press | 80 | 93 | 78 | 80 | 80 |
| v10 | 88 | 104 | 88 | 87 | 88 |
| v9.1 | 101 | 105 | 103 | 98 | 101 |
| wide_switch | 171 | 186 | 171 | 171 | 171 |

There were 35 source-side raw deadline calls in the slow-call log; 1 overlapped a recorded GC event and 0 had a wall-minus-thread-CPU gap above 5 ms. These observations do not remove any deadline miss from a gate.

## Physics and execution evidence

The native flight fixture uses legal formations and normal player commands with the stock configuration. Upper/lower side walls, an oblique rebound and an end-wall rebound each provide 81 native position/velocity samples. The maximum forecast error is below 0.00002 units. No native state, friction, restitution, engine or configuration is injected or edited.

The development execution records include the first clean Ambush collection and the first failed Wall-Brake attempt. They reproduce their original scores with zero exceptions and deadline misses. The failed Wall-Brake case is evidence of passer interference, not a successful reception. Diagnostic R1 replays, when present, remain separate from qualification points.

The [fresh R1 execution records](../../tests/fixtures/physics-qualification-executions.json) replay the first clean native success for each tactic. All three reproduced their original scores with zero exceptions and deadline misses. The unfinished rebound-shot episode began with 21 ticks left in the match and is reported as open at the whistle, not a goal.

Original v10 movement, interception, receiver rollout, shot/bank geometry, goalkeeper and cover functions are reused. Two optional captures expose existing path velocities and the already-computed post-kick player state; default physics outputs are unchanged. The all-off build preserves v10 commands on real native observations. Regression fixtures cover strict opponent races, protected roles, wall exits, slow reception, a real exact-bounce state, redundant chase suppression, safe-shot feasibility and identical contact arithmetic. All 112 final regressions passed before source freeze. Their exact logs are retained in the native archive.

## Reproduction

`python -m unittest discover -s tests -q` runs the regressions. `python tools/physics_tactics/build.py` rebuilds the isolated source files from frozen v10. Run a frozen protocol into a new directory with `python tools/benchmarks/run_physics_tactics.py --protocol PATH --out NEW_DIRECTORY`. Use one timed worker and the bundled stock engine. Never overwrite old runs.

Native archive: `tests/fixtures/physics-tactics-native-evidence.zip`, 3,228,176 bytes, SHA-256 `c93664b3513b5ca295b65e6b57119fd453442f7d087fdb09090d7ce8dfc8d8fd`. Its CRC, exact file list and every manifest SHA-256 were verified against the preserved original files. Fixture hashes are in [evidence.json](evidence.json).

The depth14 proxy is a known local controller testing an observed keeper-position idea. No source or result is represented as either actual league leader. The active champion, existing champion archives, SDK and competition configuration remain unchanged.
