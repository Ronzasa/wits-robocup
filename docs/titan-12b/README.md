# TITAN-12B — retain v10.0

**Do not replace the existing v10.0 competition upload.** The complete challenger
is implemented at [`experiments/titan-12b/team.py`](../../experiments/titan-12b/team.py),
but it is **unpromoted**: fresh qualification produced **1,445 versus 1,449 points**,
an inconclusive paired confidence interval, and an unacceptable raw deadline gap.
`my-team/team.py` and `main` remain unchanged. No v12 champion was declared.

The branch is `titan-12b-counter-defence`, based on main commit
`0a7a3aeba3950eb1b2ed0deeb7a06f2f9b3563e5`. The final source was already frozen
in checkpoint **`f843834` before its first tournament**. It was selected under the
registered development rule, copied byte-for-byte to the required path, then
qualified without further code or coefficient changes.

## Fresh qualification

**768 paired comparisons**: 12 frozen opponents × 16 unused seed blocks × both
pitch assignments × both kickoff arrangements. Each comparison contains one
full v10 fixture and one full challenger fixture. All matches use engine 0.1.0,
course configuration `372990895c7eca2a`, 2,400 ticks and the native **20 ms** limit.

| Result | Frozen v10.0 | TITAN-12B |
|---|---:|---:|
| League points | 1449 | 1445 |
| Wins | 433 | 431 |
| Draws | 150 | 152 |
| Losses | 185 | 185 |
| Goals scored | 1360 | 1347 |
| Goals conceded | 742 | 733 |
| Turnovers | 4379 | 4388 |

Raw initial results and first-clean strength totals **coincide** for every row
in this table. Exact repeats were triggered only by a missed deadline by either
team, accepted at the first clean result regardless of score, and preserved.
No exception was repaired. The full records include both teams' statistics.

The points difference is **−4**; the paired whole-seed 95% bootstrap interval is
**[−0.052083, +0.041667] points per match**, using 5,000 fixed-RNG resamples.
The interval includes zero. There is no credible points improvement to promote.
Nine fewer goals conceded did not compensate for 13 fewer goals scored and two
fewer wins. These are sample outcomes, not proof of a general decline in every
opponent matchup or a prediction of school standings.

| Gate | Result |
|---|---|
| More fresh league points | FAIL |
| Positive paired 95% lower bound | FAIL |
| Zero policy exceptions | PASS |
| No repeated candidate deadline failure | PASS |
| Original mean-runtime ceiling | PASS |
| At most two additional raw misses per 1,000 fixtures | FAIL |
| Official five-public-seed acceptance | PASS |

No thresholds were relaxed and no favorable validation cohorts were pooled or
selected after results. The other reserved held-out groups were left unused.

## Runtime and reliability

| Raw measurement | v10.0 | TITAN-12B |
|---|---:|---:|
| Policy exceptions | 0 | 0 |
| Deadline misses | 2 | 6 |
| Mean decision ms | 0.202431 | 0.211363 |
| p99 ms, measured bin | 1.925–1.950 | 1.925–1.950 |
| p99.9 ms, measured bin | 3.925–3.950 | 3.950–3.975 |
| Maximum decision ms | 31.854 | 93.840 |

Low mean decision latency is not substituted for the raw deadline gate.
The recorded mean decision time increased about **4.4%**
and passed the original ceiling of baseline × 1.35 + .04 ms. However, **four
additional raw misses / 768 fixtures = 5.2083 / 1,000**, exceeding the allowed 2.
All exact repeats of these source failures were clean; that does not erase them.
There were no repeated selected-source deadline failures across its development
and fresh runs. The raw histograms cover every source-side decision.

Every timed tournament used one serial worker with rotating source order.
No profiling or regression suite ran beside it. Per-fixture CPU/wall/cgroup
records are retained; the final run recorded **zero quota throttling**. There was
no per-call GC/CPU trace in the strength run, so the cause of the large spikes
remains **unknown**. They are not reclassified as environmental noise. The early
detector-only screen's 110.395 ms miss is also retained, along with its clean
6.738 ms exact repeat. No submitted code changes clocks, GC, scheduling,
affinity, game parameters or the deadline.

## Implemented controller and safeguards

The final controller combines a physically checked threat detector, designated
cover, emergency support and immediate recovery:

* Forecast the ball already in flight, or at most **two legal imminent enemy
  releases** just after our possession loss. Use the existing kick/contact
  physics, opponent cooldowns and dense wall-aware trajectories. Hypothetical
  passes are possible enemy actions; enemy intent and future collisions remain
  unknown.
* Rank physically possible opposing outfield contacts. `_verified_intercept()`
  returning `None` is infeasible, never replaced by a heuristic ETA. Check the
  existing primary chaser's earlier physical contact before intervening. Local
  dense step metadata leaves our passing cache and receiver aim unchanged.
* Reposition only the designated cover toward a useful goal-side receiving
  point or local lane screen. Its movement-target ETA remains a positioning
  heuristic; it is not an interception certificate. Already goal-bound shots,
  central controlled shooting danger and terminal receptions inside 14 units
  of our goal retain v10's response.
* Add one second defender only for urgent multiple threats. Preserve the
  goalkeeper, primary chaser, named verified receiver and the most advanced
  existing free runner's command as the outlet. The user explicitly permitted
  **one outlet briefly** because five players cannot fill six distinct roles.
  The emergency lasts at most **.6 seconds**, never extends on a persistent
  threat, and cannot rearm just because the urgency score flickers.
* Build targets from v10 afresh each decision. Secured possession or disappearing
  danger removes the new assignments immediately. No permanent deep shape or
  v8 five-player shield is introduced.

The new computation is bounded to two 1.25-second forecasts and at most ten
contact queries. It is gated off whenever any own player is ready to kick, so
it cannot overlap the expensive own kick search. All original controller
methods except reset/state initialization and the single post-planning call in
`act()` are unchanged. Shooting, goalkeeper safeguards, ball chasing,
verified own passes and the original counterpress are preserved. Same-state
command preservation does not guarantee identical later attacking outcomes;
the full paired games measured those effects.

Both flags are enabled in the selected, complete combined controller. Its hash is
`8e33c9f624ec9bf61282eaa076cc2b539ec511c72d320787d8c91fc7be1d4074`.
Frozen v10 is [`champions/v10.0/team.py`](../../champions/v10.0/team.py), hash
`5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6`.
Archived v9.1 and original TITAN-10B are also unchanged.

## Independent development and failure analysis

| Completed development experiment | v10 points → challenger | Goals scored | Goals conceded | Decision |
|---|---:|---:|---:|---|
| Observation-only initial detector, 48 | 70 → 70 | 48 → 48 | 45 → 45 | Behavior check; no points improvement |
| Initial single cover, 48 | 70 → 61 | 48 → 47 | 45 → 58 | Reject |
| Initial emergency support, 48 | 70 → 66 | 48 → 51 | 45 → 45 | Reject |
| Flight-filter single-cover refinement, 48 | 70 → 64 | 48 → 50 | 45 → 59 | Reject |
| Final verified single cover, 48 | 70 → 71 | 48 → 51 | 45 → 45 | Preliminary only |
| Final verified emergency support, 48 | 70 → 70 | 48 → 48 | 45 → 45 | Neutral in this screen |
| Final combined controller, 48 | 70 → 71 | 48 → 51 | 45 → 45 | Selected by registered tie rule |
| Selected expansion, 192 | 283 → 285 | 241 → 241 | 217 → 209 | Inconclusive; 95% interval crosses zero |

The early cover replay exposed a concrete risk-model error: at ticks 1035–1037
in development self-play seed 405490241, cover moved toward an off-ball forward
while a fast shot was already committed toward our goal. A goal followed at
1048. That identifies an unsuitable decision context, not proof that the single
move alone caused the goal. Full native replay records and the rejected sources
remain available.

The observed-flight-only and strict early-arrival predictive variants preserved
all old actions in their native samples: they found no useful positioning window.
Reacting after release was too late. The final development integration added
bounded imminent legal releases and restored the original independently tested
cover target timing. All architecture amendments preceded **every** held-out
result. No new coefficients were fitted after the final freeze. See
[the design and stage-specific details](design.md) and the registrations beside
this report.

The final detector and independent assignments passed regressions and native
checks **before combination**. The combined methods are identical to those
independent variants; only the two action flags differ. Their subsequent common
screen measures the interaction rather than declaring failed precursors to be
proven improvements. The small development gain failed to transfer to the fresh
cohort, so no successful championship upgrade is claimed.

## Per-opponent fresh results

Each row contains 64 matched comparisons. These descriptive subgroup results
are not separate significance tests or a substitute for the primary interval.
The pool includes v10 self-play, v9.1, compact defence, strong keeper, pressing,
counterattacking, marking and long-passing variants plus specialist references.

| Frozen style | Points v10 → candidate | Δ points | Goals scored | Goals conceded |
|---|---:|---:|---:|---:|
| long_shooter | 165 → 166 | +1 | 164 → 165 | 35 → 34 |
| tight_links | 174 → 178 | +4 | 184 → 188 | 35 → 34 |
| v10 | 92 → 90 | -2 | 76 → 73 | 76 → 76 |
| v10-compact | 105 → 102 | -3 | 71 → 69 | 52 → 53 |
| v10-counter | 113 → 111 | -2 | 119 → 116 | 90 → 86 |
| v10-linekeeper | 105 → 100 | -5 | 89 → 84 | 67 → 68 |
| v10-long | 67 → 66 | -1 | 67 → 61 | 98 → 99 |
| v10-mark | 139 → 138 | -1 | 113 → 113 | 52 → 48 |
| v10-press | 87 → 88 | +1 | 78 → 78 | 75 → 75 |
| v9.0 | 117 → 120 | +3 | 112 → 114 | 78 → 74 |
| v9.1 | 101 → 102 | +1 | 84 → 83 | 64 → 63 |
| wide_switch | 184 → 184 | +0 | 203 → 203 | 20 → 23 |

## Tests, intake and complete evidence

**136 regression tests passed** with the selected standalone file. They include
frozen champions, unchanged original methods, role locks, physically possible
and unavailable contacts, earlier chasers, direct/wall counterpasses, legal
controlled releases, cooldowns, goal-bound/terminal safety, immediate recovery,
non-extending emergency timing, cache isolation, 46 exact precursor snapshots
and one exact final-controller native snapshot, including cooldowns and
emergency episode state.

Across 212 additional instrumented native diagnostic fixtures, **508,800 shared
decisions** checked that old policy state, kicks, goalkeeper/chaser commands and
verified receiver commands matched v10 on identical observations. The selected
combined source alone had 38,400 such checks before its first tournament; another
9,600 post-qualification checks archived its exact final-controller snapshot. These
are not additional independent strength samples. One strict precursor's driven
native diagnostic had a raw deadline miss; it is retained, not included as
competition proof. No policy exception occurred.

The final SDK intake repeated all five public seeds (1001–1005, 400 ticks each):
**2,000 decisions, zero exceptions, zero deadline misses, zero missing or
non-finite actions**, maximum **5.386 ms**.
The folder inspector/static review found no errors or flags. Every experimental
controller is self-contained in exactly one `team.py`, defines one controller
implementation with `act()`, and imports only `math` and the official SDK.
Passing intake does not establish better competition performance.

The complete formal campaign contains **2,400 scheduled full-match fixtures**,
**5,760,000 source-side decisions**, **13 raw source-side deadline misses** across
all baselines/experiments, and **zero source-side policy exceptions**. Replays,
native diagnostics, public seeds and exact timing repeats are additional records,
not extra independent strength observations. All 14 source summaries and every
scheduled outcome are exported without deleting failures.

Earlier test logs include 17 snapshot-coordinate assertions caused by manually
written decimal field constants and one misplaced local variable in a test.
The fixture now preserves exact native float32 field values, and the test scope
was corrected. These were test-harness issues; controller source was not changed
to make those assertions pass. Final tests compare snapshots exactly, and all
failed logs remain archived.

* [Full metrics](metrics.json), [metrics CSV](metrics.csv), [2,400 raw/paired rows](paired-scores.csv).
* [Gate decision](decision.json), [complete schedule/hash audit](final-audit.json),
  [SDK intake](final-intake.json), [source hashes](source-hashes.json).
* [Native evidence archive](native-evidence.zip) preserves unaltered raw, first-clean and repeat records,
  timing/environment logs, native replays, diagnostics, test logs, metadata,
  frozen protocol/source/opponent hashes and a per-file SHA256 manifest.
  Baseline raw records are included.
* [Initial registration](registration.json), [seed registry](seed-registry.json),
  [development selection](selection.json), [final protocol](validation-route-protocol.json).
  Six development seed blocks and 16 fresh final blocks were used. All 86 newly
  reserved values are disjoint from 596 earlier recorded seed/protocol values;
  64 reserved validation values remain unused. No failed cohort was pooled or
  rerun to rescue the challenger.

## Reproduction

Use the full repository and new output paths; tools refuse to overwrite prior
evidence. Do not run profiling/regressions beside a timed tournament.

```bash
ROBOCUP_TEAM_PATH=experiments/titan-12b/team.py python3 -m unittest discover -s tests
python3 tools/verify_counter_defence.py --sources experiments/titan-12b/team.py --seeds 2096210638 --out work/review-native
python3 tools/benchmarks/run_titan12b.py --protocol docs/titan-12b/validation-route-protocol.json --out work/review-validation
python3 tools/benchmarks/evaluate_titan12b.py work/review-validation
python3 tools/benchmarks/report_titan12b.py --runs work/review-validation --out work/review-export
python3 tools/replay_counter_defence.py --team experiments/titan-12b-cover/team.py --style v10 --seed 405490241 --side 0 --no-kickoff --out work/review-failed-cover
```

Intervals describe seed variability over this fixed local opponent pool; they
are not a probability of improving the school's live standings. The school's
earlier reliability counter cannot be explained without per-match/platform
evidence. **The recommended competition submission remains v10.0.**
