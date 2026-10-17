# TITAN-11 — final decision: retain v10.0

**No challenger passed every registered promotion gate.** `my-team/team.py`
and the `main` champion remain v10.0, byte-for-byte unchanged. No rejected
features were combined, no v11 champion was declared, and the combination seed
group was not used to try to rescue a failed qualification.

The development branch is `titan-11-championship`, based on main commit
`0a7a3aeba3950eb1b2ed0deeb7a06f2f9b3563e5`. Frozen v10.0 is
[`champions/v10.0/team.py`](../../champions/v10.0/team.py), SHA256
`5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6`.
Archived v9.1 and original TITAN-10B are also unchanged.

The standalone [research reference](../../experiments/titan-11/team.py) is an
exact copy of the tested cover-refinement source. It is **unpromoted**, not a
recommended replacement for the active league submission. Every experimental
controller is self-contained in its own `team.py`; none imports benchmark tools
or a second custom Python file.

## Fresh qualification results

Each row is **576 paired fixtures**, 12 frozen opponents × 12 unused seed blocks
× both field assignments × both kickoff arrangements. The confidence interval
resamples whole seed blocks, preserving opponent/side/kickoff dependence.
Different rows use different unused cohorts; compare each to its own matched
v10.0 baseline, not to another row's raw point total.

| Challenger | Points v10 → challenger | Paired 95% Δ points/match | Raw own misses v10 → challenger | Raw mean ms v10 → challenger | Decision |
|---|---:|---:|---:|---:|---|
| Progressive passing | 1004 → 1144 | [+0.1354, +0.3438] | 2 → 4 | 0.20367 → 0.18108 | REJECT: raw deadline delta at most 2 per 1000 |
| Passing-R | 1088 → 1095 | [-0.0833, +0.1198] | 4 → 3 | 0.20775 → 0.17569 | REJECT: positive paired 95 lower |
| Attacking space search | 1043 → 974 | [-0.3073, +0.0729] | 2 → 4 | 0.20358 → 0.20888 | REJECT: more points; positive paired 95 lower; raw deadline delta at most 2 per 1000 |
| Selective lookahead | 1041 → 1053 | [-0.1024, +0.1250] | 0 → 3 | 0.20947 → 0.17668 | REJECT: positive paired 95 lower; raw deadline delta at most 2 per 1000 |
| Coordinated cover refinement | 1004 → 1001 | [-0.1562, +0.1510] | 4 → 1 | 0.20840 → 0.16682 | REJECT: more points; positive paired 95 lower |

All qualification sources had **zero policy exceptions**, passed the official
five-public-seed acceptance check, and stayed inside the mean-runtime ceiling.
No candidate deadline failure repeated on its exact rerun. Every initial raw
miss still counts. Original passing's 4 versus 2 misses is **3.4722 additional
misses/1,000 fixtures**, above the allowed 2; it was rejected despite a strong
football result. Passing-R preserved its tactics, passed reliability, but its
points gain did not replicate convincingly on the next unused cohort. We did
not pool or select favorable cohorts to override a failed gate.

The cover refinement conceded **534 versus 611** goals but scored **827 versus
949**. Its final **1,001 versus 1,004 points** and interval crossing zero do not
justify promotion. The same rule rejects lookahead's small average gain and
movement's reduction in points. Lower goals conceded, longer passing or a lower
mean decision time alone is not enough.

## Development and isolation

The [initial registration](registration.json), [seed registry](seed-registry.json)
and source hashes were recorded before their respective tests. Development
used 48 fixtures/source (six strong styles, two seeds, four arrangements), then
192/source for positive-point candidates (eight styles, six development seeds).
No tactical coefficients were tuned on held-out outcomes.

| Experiment | 48-fixture points, v10=54 | 192-fixture points, v10=239 | Outcome |
|---|---:|---:|---|
| Equivalent chase runtime | 54 | — | Behavior-preserving engineering result; no standalone points promotion |
| Progressive passing | 83 | 305 | Football gain; rejected by fresh raw-timing gate |
| Attacking movement | 55 | 243 | Rejected by fresh points and timing gates |
| Initial deep cover | 49 | — | Development rejection; scored 34 versus 63 goals |
| Extra shot targets/powers | 54 | — | Development rejection; no points gain |
| Selective lookahead | 57 | 268 | Rejected by fresh confidence and timing gates |
| Refined coordinated cover | 75 | 292 | Rejected by fresh points/confidence gates |

Passing added four bounded forward-lead/switch options, a longer verified
flight for distant links and a third transition lead. Every new option retained
the executable-receiver race, actual-launch verification and full opponent
interception checks. Movement searched five spaces for free attackers, while
retaining chaser/receiver/cover priorities. Finishing added four legal
keeper-informed target/power options. Lookahead reused the controlled-touch
endpoint and two bounded goal rays. Each was a separate complete controller.

One [bounded cover refinement](cover-r-registration.json) followed the initial
cover's development failure and source review. It protected a live receiver's
target from the later cover hook, preserved secure/unpressured shape, and moved
only the actual guard when possession was threatened. It avoided duplicating
an existing marker. Its 12 additional validation seeds were reserved before its
first development fixture. No goalkeeper/shooting policy, player speed, game
configuration, broad five-player shield or rejected passing feature was added.

## Runtime investigation and verified engineering results

The school reported **2,481 combined exceptions/missed deadlines** and 1.045 ms
mean decision time. The user confirmed v10.0 active, but per-match failures,
upload time, artifact hash and counter aggregation window were unavailable.
The site could not be read using the available web tool. The online cause
remains unresolved; the local evidence does not attribute those events to old
submissions or host noise.

A 64-match instrumented diagnostic captured 153,600 v10.0 decisions with zero
exceptions/misses. The slowest call took 13.801 ms and overlapped a measured
10.573 ms generation-2 GC pause. Other calls reached approximately 8 ms without
GC. Profiles identified heuristic chasing as the average-cost hotspot and
bank-pass movement witnesses as the slow-case hotspot.

Independent chase ablations reused the identical ETA distance/arithmetic and
converted shared forecast ticks once. On 9,600 shared observations they reduced
mean CPU from .19995 to .15996 ms, with identical action fingerprints. The cache
retains one actual immutable path object, resets with field/match setup, and
never uses a bare numeric object identity.

Witness ablations bound immutable constants locally and reject impossible
fallbacks with a conservative projection bound: existing acceleration/damping
sums for a 12-step prefix, maximum speed thereafter, reapplied after four actual
steps with clipping allowance and roundoff tolerance. A bound never approves a
reception; successful contact still requires the existing movement witness.

A rotating same-host comparison of 40 captured hard states, 12 repetitions:

| Runtime source | Mean CPU ms | p99 CPU ms | Max CPU ms |
|---|---:|---:|---:|
| Frozen v10.0 | 7.17251 | 10.53964 | 11.93201 |
| Initial witness optimization | 4.38784 | 7.11612 | 8.12508 |
| Periodic remaining-movement bound | 3.92348 | 6.30927 | 7.59935 |

The last row reduced hard-case mean CPU **45.3%** and p99 **40.1%** in that
controlled diagnostic. Four native equivalence runs compared **307,200 shared
decisions**, including all movements, kicks, debug output and non-cache state.
The passing-R comparison used original passing as its behavior baseline;
the pure runtime comparisons used v10.0. Random reachability checks and the
saved moving/wall-reception cases also matched. These improvements remain
experimental under the strict points-promotion rule. They do not establish
zero deadline misses on every host. See [full reliability details](reliability.md).

## Failure analysis and native reproductions

* The large first passing gain was insufficient: it failed the raw timing gate.
  Its equivalent faster source's gain was inconclusive on different unused seeds.
* The movement heuristic improved mean completed-pass distance in development
  (8.49 versus 8.12 pitch units) while fresh scoring and points declined. Open
  space and pass length were weak proxies for winning.
* Both cover variants illustrate the attack/defence tradeoff. The refinement's
  development gains did not transfer to its complete fresh qualification.
* Lookahead reduced conceded goals but failed confidence and timing requirements.
  The extra finishing options provided no development points gain.
* The saved native v9.1 missed reception and receiver-only recovery still
  reproduced, with collection at tick 1507 and zero errors/timeouts.
* Eight development native replays recorded 15 changed pass choices: 13 intended
  receiver first touches and two other teammate first touches. No opponent
  first touch was observed. Post-touch tracking found no opponent contact in
  the next five ticks across all 15; 14 had sufficient coverage for the longer
  10/20-tick windows, also without opponent contact. These cases do not explain
  the fresh points nonreplication and are not presented as causal proof or a
  representative league completion estimate.

## Evidence, acceptance and interruption handling

**7,344 complete formal native fixtures**, **17,625,600 source-side
controller decisions**, **32 raw source-side deadline misses**, **zero
source-side policy exceptions**. Full results include both teams' statistics.
The five fresh qualification cohorts account for 2,880 paired comparisons.
Instrumented diagnostics, short public validation and timing repeats are
additional records, not extra independent strength samples.

All fixtures use the official engine **0.1.0**, registered course configuration,
**2,400 ticks** and **20 ms** deadline. A single serial worker rotates source
order; no profiling runs beside timed tournaments. No submitted controller
imports timers, changes GC, scheduling, process affinity or deadline settings.

A workspace restart interrupted movement after 48 complete challenger and 47
complete baseline fixtures. Every completed raw/accepted prefix was preserved
byte-for-byte; the first missing source/fixture resumed the identical schedule.
No result existed for the in-flight partial fixture, so its internal counters
are unknown. Its infrastructure interruption is documented separately and does
not erase any returned policy failure. Full means/maxima/native buckets survived;
fine histogram quantiles explicitly report the resumed portion's coverage.

The file/folder inspector, single-controller loader and actual five public seeds
(1001–1005, 400 ticks each) were applied before every formal run. The final
research-reference intake check again passed all 2,000 decisions: **0 exceptions,
0 over 20 ms, 0 missing actions, 0 non-finite values**, maximum **5.483 ms**.
All **116 regression tests** also passed with that research controller selected.
The gated assembler refused every rejected feature; no active source was written.

* [Complete metrics CSV](metrics.csv), [all 7,344 paired/raw outcome rows](paired-scores.csv),
  [full metrics JSON](metrics.json), [source hashes](source-hashes.json).
* `native-evidence.zip`: unaltered raw/first-clean/repeat records, public checks,
  metadata, environment logs, source/protocol hashes, diagnostics and per-file
  SHA256 manifest. Baseline raw records are included, not filtered out.
* `tests/fixtures/titan-11-opponents.zip` freezes 12 legal opponents: v10.0,
  v9.1, v9.0, six v10-derived compact/keeper/press/counter/long/mark variants,
  and three specialist references. Most opponents are v9.1/v10 strength;
  individual strengths and regressions are reported rather than assumed.
* Source/protocol hashes were verified before and after the runs. The untouched
  reserved runtime seeds were renamed to `passing-r` in a recorded
  [addendum](passing-r-registration.json); no seed values changed. The cover
  addendum reserved 12 more disjoint seeds, bringing the registry to 102.
* The passing-R equivalence source's later docstring-only cleanup has an
  [executable-AST/hash mapping](passing-r-metadata-amendment.json). The exact
  comparison source is preserved in a compressed fixture. Its final source
  hash was frozen before qualification.

## Reproduction

From the full repository, choose new output paths; tools refuse to overwrite
previous evidence. Do not run timing benchmarks concurrently with profiling.

```bash
python3 -m unittest discover -s tests
python3 tools/benchmarks/run_titan11.py --protocol docs/titan-11/validation-cover-r-protocol.json --out work/review-cover
python3 tools/benchmarks/evaluate_titan11.py work/review-cover
python3 tools/benchmarks/report_titan11.py --runs work/review-cover --out work/review-export
python3 tools/profile_titan11.py champions/v10.0/team.py --out work/old-replay.json
python3 tools/profile_titan11.py experiments/titan-11-reach-step-bound/team.py --out work/runtime-replay.json
python3 tools/compare_titan11_runtime.py --sources champions/v10.0/team.py experiments/titan-11-reach-runtime/team.py experiments/titan-11-reach-step-bound/team.py --out work/hard-runtime.json
python3 -m zipfile -e tests/fixtures/titan-11-opponents.zip work/titan11-opponents
python3 tools/verify_passing_runtime.py --baseline champions/v10.0/team.py --challenger experiments/titan-11-reach-step-bound/team.py --against work/titan11-opponents/v10/team.py work/titan11-opponents/v10-press/team.py work/titan11-opponents/v10-counter/team.py work/titan11-opponents/v9.1/team.py --seeds 1239849544 1403182426 --out work/native-equivalence.json
python3 tools/titan11_cases.py --team experiments/titan-11-passing/team.py --seeds 1994254003 998003032 --follow-ticks 20 --out work/post-touch.json
python3 tools/reproduce_execution_reception.py --challenger experiments/titan-11-passing-r/team.py --out work/native-reception
```

All nine formal protocols are stored beside this report. The resume tool accepts
only an unfinished run and reuses its frozen source/opponent hashes. Bootstrap
intervals describe seed variability over this fixed local pool, not a probability
of winning the school league. Online standings and the reported 2,481 events
remain unverified by local tests. **Keep the existing v10.0 competition upload.**
