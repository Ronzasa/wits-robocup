# Replay-led controller validation

**Decision: RETAIN_BASELINES. Main, active v10.0 and frozen TITAN-X Trap are unchanged.**

The selected source improved total points, but the paired confidence intervals included zero. It failed the registered positive-lower-bound gate, so retain the existing controllers. The experiment remains available for inspection; it is not a promoted champion.

The footage review is in [replay-analysis.md](replay-analysis.md), with a result table for all ten games and annotated evidence for all 17 visible goals. The two opponents played one another, so the supplied videos do not measure our controller against them. Local native tests below evaluate observed tactical ideas against frozen, known local opponents. No result is presented as a match against the actual leaders.

The campaign completed **3,408 scheduled full native matches**, plus **45 identical timeout-fixture repeats**. All matches use 2,400 ticks and the official 20 ms deadline; intake validation uses the SDK public seeds. Points, goals and pass metrics use the first clean exact run, independent of score; raw points are also shown for qualification. Raw rows and all repeats are retained separately. Every original deadline miss remains in the reliability gate.

## Independent screen

Five variants played 48 matched configurations each, alongside frozen Trap and v10: six styles, two seeds, both sides and both kickoffs. The keeper cap is the only difference among the three keeper variants. Outlet and cutback variants change only their selected support target.

| Variant | Trap points | v10 points | Variant points | GF–GA | Raw misses | Mean ms |
|---|---:|---:|---:|---:|---:|---:|
| keeper6 | 74 | 74 | 68 | 90–65 | 0 | 0.2313 |
| keeper10 | 74 | 74 | 78 | 85–61 | 2 | 0.2345 |
| keeper14 | 74 | 74 | 79 | 82–59 | 0 | 0.2339 |
| outlet | 74 | 74 | 91 | 118–69 | 0 | 0.2373 |
| cutback | 74 | 74 | 77 | 90–62 | 0 | 0.2375 |

The cap-10 keeper is excluded by its raw deadline regression. Independent results justified testing the cap-14 keeper, outlet and cutback, plus their combination, on new configurations. The outlet screen improved points while conceding more goals: winning matches, rather than pass volume or a single defensive statistic, controls selection.

## Fresh development confirmation

128 unused matched configurations per source: eight styles × four seeds × both pitch assignments × both kickoffs. No source or parameter was changed from this stage’s outcomes.

| Variant | Trap points | v10 points | Variant points | GF–GA | Raw misses | Mean ms |
|---|---:|---:|---:|---:|---:|---:|
| keeper14 | 200 | 203 | 189 | 229–165 | 2 | 0.2405 |
| outlet | 200 | 203 | 201 | 271–178 | 1 | 0.2421 |
| cutback | 200 | 203 | 234 | 286–140 | 1 | 0.2426 |
| combined | 200 | 203 | 208 | 299–220 | 0 | 0.2460 |

Selected source: `experiments/elite-scout-cutback/team.py`; SHA-256 `553bcd85a537d57a43c16e4498fab402fbbabb940e15cb8c5aa110d4c6fa9a5e`. Eligible for registered qualification: `True`.

### Selected-source development matchups

These development results explain the selection; they are not the untouched qualification result.

| Opponent | Trap points | v10 points | Selected points |
|---|---:|---:|---:|
| depth14-proxy | 26 | 26 | 29 |
| quick_wall | 48 | 48 | 48 |
| tight_links | 42 | 42 | 41 |
| v10-compact | 18 | 18 | 33 |
| v10-counter | 8 | 8 | 22 |
| v10-press | 18 | 18 | 15 |
| v10 | 21 | 21 | 18 |
| v9.1 | 19 | 22 | 28 |

## Frozen fresh qualification

768 paired configurations per source: 12 styles × 16 unused seed blocks × both sides × both kickoffs. The source and protocol were committed before these seeds were opened. Paired confidence intervals use 5,000 whole-seed bootstrap resamples with seed 719331. Qualification results did not select a different source, change thresholds or extend the cohort.

| Metric | Frozen Trap | v10.0 | Challenger |
|---|---:|---:|---:|
| Points | 1374 | 1381 | 1444 |
| Wins | 401 | 404 | 430 |
| Draws | 171 | 169 | 154 |
| Losses | 196 | 195 | 184 |
| Goals for | 1527 | 1527 | 1688 |
| Goals against | 810 | 805 | 845 |
| Passes attempted | 31181 | 31118 | 31446 |
| Passes completed | 16672 | 16648 | 16710 |
| Pass completion | 0.534685 | 0.534996 | 0.531387 |
| Uncollected passes (derived) | 6201 | 6202 | 6217 |
| Turnovers | 4123 | 4124 | 4075 |
| Mean decision ms | 0.241119 | 0.227623 | 0.238835 |
| Raw points | 1374 | 1381 | 1444 |
| Raw deadline misses | 5 | 8 | 6 |
| Raw exceptions | 0 | 0 | 0 |
| Raw max ms | 37.6844 | 66.2217 | 45.2790 |
| Raw p95 bin upper ms | 0.575 | 0.550 | 0.575 |
| Raw p99 bin upper ms | 2.150 | 2.125 | 2.125 |
| Raw p999 bin upper ms | 4.550 | 4.575 | 4.600 |

Versus **trap**: points-per-match delta **+0.091146**, paired 95% interval **[-0.0546875, 0.2526041666666667]**. Additional raw misses/1,000: **1.302083**. Reproduced candidate deadline failures: **0**.

| Gate | Result |
|---|---|
| more_points | PASS |
| positive_ci | FAIL |
| zero_errors | PASS |
| no_repeated_timeout | PASS |
| raw_deadlines | PASS |
| mean_runtime | PASS |
| sdk | PASS |
| legal_actions | PASS |
| fixture_count | PASS |

Versus **v10**: points-per-match delta **+0.082031**, paired 95% interval **[-0.06901041666666667, 0.24739583333333331]**. Additional raw misses/1,000: **-2.604167**. Reproduced candidate deadline failures: **0**.

| Gate | Result |
|---|---|
| more_points | PASS |
| positive_ci | FAIL |
| zero_errors | PASS |
| no_repeated_timeout | PASS |
| raw_deadlines | PASS |
| mean_runtime | PASS |
| sdk | PASS |
| legal_actions | PASS |
| fixture_count | PASS |

### Qualification matchups

| Opponent | Trap points | v10 points | Challenger points |
|---|---:|---:|---:|
| aggressive-keeper | 68 | 68 | 86 |
| depth14-proxy | 96 | 91 | 100 |
| long_shooter | 153 | 155 | 158 |
| quick_wall | 187 | 187 | 190 |
| tight_links | 168 | 168 | 178 |
| titan-x-trap | 85 | 91 | 83 |
| v10-compact | 79 | 79 | 97 |
| v10-counter | 93 | 93 | 98 |
| v10-press | 89 | 89 | 103 |
| v10 | 79 | 85 | 83 |
| v9.1 | 99 | 97 | 93 |
| wide_switch | 178 | 178 | 175 |

Slow-call diagnostics retain 19 source-side raw deadline calls across the three sources. GC overlaps: 1; wall-minus-thread-CPU gaps above 5 ms: 0. These observations do not remove raw misses from any gate.

## Engineering and reproducibility

Each controller is a standalone `team.py`, with one controller class, math and official soccer imports only. Existing shooting, movement physics, strict reception races, first-touch model, defensive-cover and trap helpers retain identical ASTs. The [function integrity record](function-integrity.json) checks every existing controller method. The changed targets sit inside the original role/keeper decision process. Tests include all-off command equivalence, protected receivers, keeper-depth bounds, actual cooldown-aware saving paths, a real momentum-limited case where the home save must win, support-role preservation and legal actions. Regression logs in the native archive give the exact test counts.

The native harness freezes source and opponent hashes, checks SDK intake, rotates source order within each configuration, runs one serial worker and preserves all raw timing records. Repeats are identical and accepted only as the first clean result, independent of score. Official engine, config, current submission and frozen sources were not edited. No clock, GC, affinity or deadline control exists inside the controller.

Reproduce regressions with `python -m unittest discover -s tests -q`. Build the five initial ablations with `python tools/elite_scout/build.py`. Replay any frozen native protocol with `python tools/benchmarks/run_elite_scout.py --protocol PATH --out NEW_DIRECTORY` using the official engine and one timed worker.

Native evidence: `tests/fixtures/elite-scout-native-evidence.zip`, SHA-256 `7e7c8d4c1be00e06d5cdf7c532e3f6762b50d773b2543c341e68933555012569`, 202 files. Its CRC and every entry in the SHA-256 manifest were checked. The video-analysis archive holds detection candidates and analysis scripts; cropped goal evidence is linked from the scouting report. The original recordings remain outside the repository.

The `depth14-proxy` opponent tests a known local controller with the observed keeper-depth idea. It is not either league leader. Improvement in this local opponent set is evidence for a candidate; live league standings are a separate observation.
