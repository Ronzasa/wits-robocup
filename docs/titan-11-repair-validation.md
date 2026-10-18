# TITAN-11 reception and runtime repair

**Retain v10.0. The repair does not pass every registered promotion gate.**

Candidate: [`experiments/titan-11-r/team.py`](../experiments/titan-11-r/team.py), SHA-256 `75239fcc4b80f1fa4e12a7e6a6ac9b142ff309286fc662bef814e8a800777011`. Active champion: [`my-team/team.py`](../my-team/team.py), SHA-256 `5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6`. No change to `main`, the active champion, archived versions, SDK, engine or competition configuration.

## What was fixed

Two old native diagnostic games reproduced approved passes at ticks 1821 and 1865 with actual launch speeds about 10.2 units/s. The planner had physically verified a named recipient, but `act()` required more than 10.5 units/s to establish a reception plan, and cancelled live plans below 9 units/s. Approval and execution disagreed.

The isolated handoff repair removes those speed-only gates for named passes. Every new and continuing plan still needs the original executable receiver rollout, safe first touch and strict full-route opponent race. Changed last touch, expiry, missing recipient or failed verification still cancel it. The kick-selection, shooting, keeper-safeguard and cover functions retain their original source; the resulting on-policy games can differ.

The independent runtime repair defers unused heuristic ETA calculations in `_intercept()` until its original reach tests find no sample. Its answer remains the same, including heuristic fallback, sparse samples and wall paths. It never substitutes heuristic ETA for verified pass feasibility. Exact replay matched 9,600 actions and reception states, avoiding 458,193 of 1,117,152 ETA calls. The patch changes only `_intercept()` and the two named-reception conditions in `act()`; all other method ASTs are identical. See [regression tests](../tests/test_titan11_repair.py), [exact comparison](titan-11-repair/runtime-equivalence.json) and [original failure inspection](titan-11-repair/failure-inspection.json).

### Native reproductions and limits

The two known development matches were replayed with both frozen and repaired controllers. Every repaired slow-pass plan commanded the verified receiver target. Outcomes were mixed:

| Fixed replay | Ours–theirs | Slow named passes | Coordinated plans | Intended touches |
|---|---:|---:|---:|---:|
| 0-frozen | 4–3 | 1 | 0 | 1 |
| 0-repair | 4–3 | 2 | 2 | 0 |
| 1-frozen | 1–3 | 1 | 0 | 1 |
| 1-repair | 0–3 | 1 | 1 | 1 |

Both original uncoordinated slow passes eventually reached their recipients through ordinary movement. The defect is a mismatch between approval and commanded coordination; these cases do **not** prove that the original receiver missed its collection. Repaired play follows different on-policy trajectories, so the two-versus-three pass samples are not a causal completion comparison. Scores did not improve in these two clips. They are excluded from qualification, and no code was changed in response. Full native paired tournaments, rather than these selected clips, determine eligibility.

## Registered development comparison

Four new seed blocks, eight fixed styles, both sides and kickoffs: 128 configurations per version. Runtime-only, handoff-only and combined were frozen before these results. No additional variants were created after observing outcomes.

| Version | Matches | Points | W/D/L | Goals for–against | Pass completion | Turnovers | Accepted mean ms | Initial raw misses |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v10 | 128 | 205 | 59/28/41 | 201–164 | 53.24% | 715 | 0.1995 | 0 |
| titan11 | 128 | 217 | 66/19/43 | 234–170 | 57.77% | 799 | 0.2168 | 1 |
| runtime | 128 | 217 | 66/19/43 | 234–170 | 57.77% | 799 | 0.1895 | 0 |
| handoff | 128 | 220 | 65/25/38 | 226–163 | 56.87% | 782 | 0.2134 | 0 |
| combined | 128 | 220 | 65/25/38 | 226–163 | 56.87% | 782 | 0.1865 | 0 |

Selection: **combined**. Runtime-only football matched frozen TITAN-11 on every clean native fixture; combined matched handoff-only. The handoff feature was eligible because it improved development points over frozen TITAN-11. Passing a unit test alone did not make it a football improvement. Full selection and reliability checks: [selection.json](titan-11-repair/selection.json).

## New independent qualification

24 previously unused seed blocks, 12 frozen opponents, both pitch assignments and kickoff arrangements: **1152 paired configurations, 2304 complete 2,400-tick native matches**. Candidate and protocol were committed before play. This cohort is not pooled with the earlier failed qualification. All opponent styles were previously known; these are fresh seeds, not evidence of new-style generalization.

| Version | Matches | Points | W/D/L | Goals for–against | Pass completion | Turnovers | Accepted mean ms | Initial raw misses |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v10 | 1152 | 2084 | 621/221/310 | 2084–1220 | 52.36% | 6550 | 0.2107 | 6 |
| repair | 1152 | 2144 | 650/194/308 | 2226–1286 | 54.66% | 6595 | 0.1903 | 9 |

Paired points-per-match difference: **+0.052083**. Whole-seed paired bootstrap 95% interval: **[-0.07552083333333333, 0.1675347222222222]**. Additional initial raw deadline misses per 1,000 fixtures: **2.604167**, original maximum **2**. Failed gates: **positive_paired_95_lower, raw_deadlines**. Full inputs and per-opponent metrics: [final-gates.json](titan-11-repair/final-gates.json), [metrics.json](titan-11-repair/metrics.json).

Initial raw football points, including the actual consequences of failed decisions: **2084 → 2144**; raw paired 95% interval **[-0.07552083333333333, 0.1675347222222222]**. Worst initial raw decision: v10.0 **36.944 ms**, repair **49.894 ms**. First-clean maximum: **19.028 → 15.030 ms**. The accepted-mean ceiling is **0.324419 ms**.

| Opponent | v10.0 points | Repair points | Difference |
|---|---:|---:|---:|
| long_shooter | 227 | 246 | +19 |
| tight_links | 267 | 254 | -13 |
| v10-compact | 153 | 171 | +18 |
| v10-counter | 112 | 141 | +29 |
| v10-linekeeper | 150 | 128 | -22 |
| v10-long | 124 | 121 | -3 |
| v10-mark | 190 | 218 | +28 |
| v10-press | 116 | 158 | +42 |
| v10 | 133 | 107 | -26 |
| v9.0 | 188 | 185 | -3 |
| v9.1 | 152 | 138 | -14 |
| wide_switch | 272 | 277 | +5 |

Per-opponent rows are descriptive, with equal weighting in this registered local pool. They are not separate promotion tests or estimates of the opponent frequencies in the school league.

The mean runtime reduction is real in this cohort, but neither previously failed promotion gate is repaired. Native pass completion improved while conceded goals and turnovers increased. Six of twelve styles yielded fewer points, including the direct v10.0 comparison. These mixed outcomes do not establish stronger retention or broad competitive superiority. No fresh result was used to create another variant or expand the registered cohort.

Original gates remain unchanged: positive fresh points difference and paired 95% lower bound, zero policy exceptions, no repeated deadline failure, accepted mean at most baseline×1.35+0.04 ms, at most two additional raw misses per 1,000 fixtures, passing untouched official public-seed intake and valid actions. Initial raw results, exact timing repeats and first-clean football records are all retained. Repeats never erase raw misses. Local results do not establish an online league-ranking gain.

Eight separately instrumented exact repetitions of two new repair timeout fixtures and two new baseline timeout fixtures recorded **0 new source-side misses**, with a maximum wall time of **6.986 ms** and maximum measured process CPU time of **6.988 ms**. They record wall/CPU/GC overlap without disabling collection or changing scheduling. These repetitions do not erase any qualification miss or identify the original call's cause. See [latency-diagnostics.json](titan-11-repair/latency-diagnostics.json).

The old 69/127 ms spikes and the new raw spikes remain unexplained: their original per-call CPU/GC traces do not exist. Faster typical computation and a new raw-deadline result cannot prove that arbitrary environmental stalls or the school's historical reliability counter are fixed.

## Reproduction and evidence

123 regressions passed before development and again against the selected source before fresh qualification; both test logs are retained beside this report. The registered development and validation stages contain **2,944 complete native source-side matches and 7,065,600 source-side decisions**. Diagnostic repetitions, public intake and shared-state checks are separate. [audit.json](titan-11-repair/audit.json) verifies the active champion and every pre-existing repository file. [registration.json](titan-11-repair/registration.json) records disjoint cohorts and the finite selection rule.

```sh
ROBOCUP_TEAM_PATH="$PWD/experiments/titan-11-r/team.py" python -m unittest discover -s tests -q
python tools/benchmarks/run_intelligence.py --protocol docs/titan-11-repair/validation-protocol.json --out /workspace/work/titan11-repair-reproduction
python tools/titan11/evaluate.py /workspace/work/titan11-repair-reproduction
```

Use a new directory on every run. Reproducing these fixtures does not create another independent promotion cohort. [native-evidence.zip](titan-11-repair/native-evidence.zip) includes every raw/accepted fixture, timing repeat, environment record, histogram, official intake, source snapshot, test log and diagnostic repair reproduction. Its manifest verifies each entry. The original failed TITAN-11 report and evidence remain unchanged.
