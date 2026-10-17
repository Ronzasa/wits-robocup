# TITAN-11 reliability investigation

v10.0 was confirmed active by the user. The school reports 2,481 combined
exceptions/deadline events and 1.045 ms mean decision time. Per-match failures,
submission time and the counter's aggregation window were unavailable. The
school website could not be read through the available web tool. There is no
evidence here that attributes those events to previous versions, host noise,
or a particular controller defect. Zero local exceptions does not disprove the
school's report.

The submitted artefact must be one `team.py`, import with exactly one
`TeamController` subclass implementing `act()`, then pass the SDK's five public
seeds (1001–1005, 400 ticks each), with zero exceptions and zero decisions above
20 ms. A low mean cannot compensate for a failed public seed. Every screened
source undergoes that actual check, plus folder/static review; benchmark tools
are development utilities and are never imports of the submission.

## Initial native diagnosis

64 diagnostic matches, 153,600 v10.0 decisions, both sides and kickoffs:

| Measurement | Mean ms | p99 ms | p99.9 ms | Maximum ms |
|---|---:|---:|---:|---:|
| Wall | 0.212913 | 1.919048 | 4.130848 | 13.801369 |
| CPU | 0.213669 | 1.918567 | 4.123148 | 13.805795 |

No policy exceptions, deadline misses or cgroup throttling occurred in this
instrumented diagnostic. The slowest call overlapped a measured generation-2
GC pause of 10.573 ms; another GC pause lasted 7.981 ms. Some calls took roughly
8 ms without a GC event. These observations establish local sources of latency,
not the cause of the school's events. Snapshotting, GC observation and holding
match records change the diagnostic's allocation profile, so its latency is
not substituted for competition evidence.

The host runs Python 3.12.14 and has a two-CPU cgroup quota. Earlier archived
parallel runs had measured quota throttling; all TITAN-11 strength tests use
one serial worker and retain per-fixture CPU/wall/cgroup records. No controller
changes timers, GC policy, process scheduling, deadlines or SDK settings.

## Behavior-preserving changes

On 9,600 shared observations the frozen v10.0 used 0.199950 ms mean CPU.
Inlining the identical heuristic ETA arithmetic, while reusing the already
computed distance, used 0.177753 ms. Independently, converting the shared chase
forecast's tick indices once used 0.178532 ms. Combining those two equivalent
changes used 0.159960 ms, a 20.0% reduction. All four action fingerprints were
identical. These replay measurements are diagnostics, not tournament results.

The forecast cache retains one actual immutable path object, never just its
numeric identity; it resets with both field setup and match reset. Exact native
shadow comparison then matched movements, kicks, debug output and all non-cache
controller state on 76,800 decisions, alternating which source drove the match.

The 48-fixture development screen also reproduced all v10.0 scores and native
match statistics for this runtime-only source, at lower mean decision time.
It cannot satisfy a *positive* points-improvement gate on its own: preserving
behavior is its purpose.

## Tail limitation

Replaying the 40 slowest captured decisions showed bank-pass fallback movement
witnesses, not heuristic chasing, dominated their cost. Mean CPU on these hard
cases was 6.666 ms before and 6.813 ms after the initial chase optimization;
its average speedup did **not** solve the worst cases. The slight difference is
uncontrolled replay variation, not evidence of an improvement in tail latency.
Any further witness optimization must independently preserve feasibility and
native decisions, then be tested again with the selected tactical candidate.

Raw competition deadline counts, exact-repeat outcomes, public acceptance and
full gate decisions are recorded separately in the final experiment report.
An exact clean repeat does not erase a raw miss or establish an environmental
cause. The 20 ms deadline is unchanged in every promotion run.

## Raw development spikes

The first screen retained a 33.178 ms raw lookahead decision. Expanded
development retained a 33.797 ms v10.0 decision. Both exact fixtures repeated
cleanly (maxima about 5 ms), neither fixture had cgroup throttling, and their
whole-match CPU and wall time were close. There was no per-call GC tracing in
these strength runs, so GC remains a hypothesis for those particular spikes,
not an established cause. Both failures count as raw misses. The final gate
uses the corresponding source's raw counts and rejects any repeated candidate
failure; a favorable repeat never removes timing evidence.

## Receiver-witness optimization, independently checked

The slow-case profile traced most CPU to `_bank_release()` → `_pass_race()` →
`_pass_reachable()` fallback rollouts. Two additional isolated runtime variants
were tested before fresh tactical validation:

* Bind immutable field constants and `hypot` locally in the existing rollout;
  preserve the exact arithmetic, speed cap, wall rejection and final contact test.
* Before an expensive fallback, reject an impossible displacement using a
  conservative speed-capped projection bound. Start with the nonnegative initial
  velocity projection, bound the first 12 steps with the existing damping and
  acceleration sums, and bound remaining steps by maximum speed. Clipping speed
  cannot exceed this nonnegative projection bound. A `1e-7` tolerance protects
  boundary roundoff. This check never substitutes a bound for a successful
  movement witness: it only avoids simulating a provably impossible fallback.

All three variants (local-only, bound-only, combined) matched 100,000 randomly
sampled physical-reachability queries. Their 9,600-observation action fingerprints
also matched v10.0 exactly. On the 40 captured hard decisions, mean CPU was:

| Source | Mean CPU per hard case, ms |
|---|---:|
| v10.0 | 6.6659 |
| Chase optimizations only | 6.8134 |
| Local witness bindings | 5.4275 |
| Projection bound | 4.7525 |
| Local bindings + projection bound | 4.4158 |

The combined witness changes cut this hard-case mean by 33.8% relative to v10.0.
On shared observations, p99.9 CPU fell from 4.2568 to 3.2400 ms. Recorded maxima
still varied with GC; the optimized hard-case replay had an 18.63 ms maximum.
This is a headroom improvement, not a promise that every host pause is controlled.

A second native shadow comparison of the combined runtime source matched all
76,800 decisions and non-cache state against untouched v10.0, with no driven or
shadow deadline overruns. All 112 regressions passed, including moving/wall
receptions, infeasible receiver races, speed-capped reachability and single-file
legality. No shooting, goalkeeper, tactical cover or pass-feasibility decision
was changed by these runtime variants in the recorded comparisons.

These diagnostics ran between development and fresh validation. The orchestration
parent was paused while its existing development worker finished normally;
no timed fixture was paused, discarded or run alongside profiling. The parent
resumed only after diagnostics and regressions completed. Tactical sources
remained frozen; any final combination with this equivalent runtime source must
still pass fresh paired competition and official acceptance checks.

## Runtime-qualified passing source

The first passing challenger won its fresh football comparison but was rejected
for four raw misses versus two. Its timing failures remain recorded; a clean
repeat was never treated as removal of a failure. The reserved unused runtime
seeds were used to qualify a different source, `titan-11-passing-r`, with identical passing
tactics and the independently checked witness optimizations.

An additional equivalent optimization reapplies the conservative distance bound
after each four actual pursuit steps. It can only stop a rollout that no remaining
legal input can rescue. The contact allowance includes any displacement caused by
clipping the target; successful contact still requires the original movement
witness. In 100,000 physical queries and 76,800 native decisions it matched v10.0.

A rotating same-host diagnostic compared all three sources on the same 40 hard
states, 12 times each. Every action and non-cache state matched:

| Source | Mean CPU ms | p99 CPU ms | Max CPU ms |
|---|---:|---:|---:|
| v10.0 | 7.17251 | 10.53964 | 11.93201 |
| Initial witness optimization | 4.38784 | 7.11612 | 8.12508 |
| Periodic remaining-movement bound | 3.92348 | 6.30927 | 7.59935 |

This reduces hard-case mean CPU by **45.3%** and p99 by **40.1%** on these captured
states. It is a diagnostic, not a claim of a universal latency maximum. Default
GC and the official timing rules remain unchanged.

The runtime-qualified passing source also matched the original passing source on
another 76,800 native decisions, with zero driven/shadow overruns. Before its new
qualification, a module docstring label was cleaned up; its executable AST was
identical. The exact earlier comparison source is preserved in
`tests/fixtures/titan-11-passing-r-equivalence.py.gz`, and the hash/AST mapping is
in `passing-r-metadata-amendment.json` inside the evidence archive. The subsequent
qualification freezes the final source hash and never changes it during testing.

## Final qualification outcome

Passing-R passed the reliability gates (three raw misses versus v10.0's four,
no repeated candidate failure, zero exceptions), but its 1,095 versus 1,088 points
had a paired 95% interval of [−0.08333, +0.11979] points/match. It was rejected.
The cover refinement also passed reliability but lost three points. No tested
tactical source passed every registered gate, so v10.0 remains unchanged. The
full results and all raw failures are retained in the final report and archive.
