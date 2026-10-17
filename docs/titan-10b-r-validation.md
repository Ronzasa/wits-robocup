# TITAN-10B-R: execution-preserving runtime optimization

**All original promotion gates passed.** TITAN-10B-R is approved as the v10.0 candidate on `titan-10b-r-runtime`.
As requested, `main`, `my-team/team.py`, [archived v9.1](../champions/v9.1/team.py)
and [frozen TITAN-10B](../experiments/titan-10b/team.py) are unchanged. The new
implementation is [experiments/titan-10b-r/team.py](../experiments/titan-10b-r/team.py).
Passing the gate records eligibility on this feature branch; it does not merge
the branch or change the active submission.

## Runtime change and behavior baseline

The behavior baseline is original TITAN-10B, not v9.1. The competition baseline
is frozen v9.1. This build adds no new tactics or search-budget reductions.

- Share dense native tick metadata with receiver and opponent queries.
- Retain one immutable internal path by object identity, never only `id()`;
  invalidate its metadata and query cache on a different path, reset or setup.
- Cache exact physical queries by full player state, cooldown, lower/upper
  horizon. Cache `None` as unavailable, not an ETA. Store at most 32 queries;
  explicit foreign tick metadata bypasses the cache.
- Run the ordinary receiver aim before constructing alternatives. Failed aims
  retain the same target order, horizons and tie-breaking.
- Keep receiver position/velocity as scalars during rollout. Repeat the
  empty-friends `_move()` arithmetic exactly, including its second unit
  normalization; construct a player tuple only on contact.

`act()`, `_move()`, `_intercept()`, `_pass_reachable()`, `_verified_intercept()`,
shooting, keeper, cover, collision physics, player attributes, margins and budgets
remain AST-identical to original TITAN-10B. Only `reset`, `_setup`, `_pass_steps`,
`_pass_race`, `_receiver_rollout` and `_receiver_route` changed; one query wrapper
was added. No timer, GC, process-affinity, hidden-state or deadline controls are
present in the submitted controller. Imports remain `math` and the official SDK.

## Profiling and environmental investigation

The initial CPU profile found **10,132** `_pass_steps` calls for **5,066** pass
races on 9,600 shared native public observations. Tick metadata was rebuilt
twice. General chasing/positioning was a larger cost and was deliberately kept
unchanged. cProfile increases measured cost, so its times never count toward
competition reliability or the promotion gate.

The container has a two-CPU quota with a 100 ms period. The SDK uses elapsed
wall time. On the same unmodified original controller, a serial replay recorded
no cgroup throttling; concurrent diagnostic replays recorded throttling and
wall-minus-CPU delays up to **15.77 ms**. This supports a scheduling contribution
but does not prove every old spike was environmental. The old 22→33 deadline
misses were not erased or reclassified, and the original gate was not relaxed.
Fresh diagnostic records also include isolated spikes without cgroup throttling.
In inspected interrupted matches, whole-match CPU and wall time were nearly equal
and exact repeats were much faster. Their precise cause remains unresolved;
they were retained as raw deadline misses, not excused as scheduling noise.

Fresh competition uses one serial native match worker, randomized fixture order
and alternating source order per pair. The SDK and native **20 ms** deadline
are unchanged. Per-match wall/CPU and cgroup records are outside controller
timing. Fresh-run cgroup counters: `{"burst_usec": 0, "nice_usec": 0, "nr_bursts": 0, "nr_periods": 10965, "nr_throttled": 0, "system_usec": 846168, "throttled_usec": 0, "usage_usec": 1098202383, "user_usec": 1097356215}`.

Initial independent component profiles, rotating call order on each observation:

| Variant | Mean CPU ms | CPU p99.9 ms | CPU maximum ms |
|---|---:|---:|---:|
| original | 0.2193 | 4.8073 | 7.4440 |
| shared-steps | 0.2120 | 4.5239 | 6.7761 |
| scalar-rollout | 0.2166 | 4.9340 | 7.3045 |
| memo-query | 0.2074 | 4.5773 | 7.7841 |
| lazy-aims | 0.2143 | 4.6943 | 7.2208 |
| metadata-only | 0.2123 | 4.7889 | 6.9958 |
| lean-combined | 0.2104 | 4.3704 | 6.6400 |
| full-combined | 0.2044 | 4.5021 | 6.5184 |

Every component separately passed all **81** pre-existing regressions before the
final freeze. Initial profiles used native tuple players; regression coverage
also caught list-based fixture players, whose cache keys were normalized before
the corrected comparison and freeze. The complete source passed **95** tests.
All compared actions and all non-cache controller state matched exactly.

Final paired CPU comparison uses the exact frozen release, 9,600 shared public
observations and rotated call order, with zero cgroup throttling:

| Metric | Original TITAN-10B | TITAN-10B-R |
|---|---:|---:|
| Mean CPU ms | 0.2088 | 0.1961 |
| CPU p99 ms | 1.8354 | 1.7189 |
| CPU p99.9 ms | 4.3827 | 4.1213 |
| CPU maximum ms | 6.9053 | 6.6670 |

Mean CPU work fell **6.05%** on that sample. These are sampled tails,
not a universal worst-case bound. At most four receiver aims, 80 flight ticks
and 32 cached queries keep the additional computation/storage bounded.

## Native behavior and reception reproductions

**76,800 exact decision/state matches** across **32 native games**: four styles,
two development seeds, both pitch assignments and kickoff arrangements. The
driving source alternated; shadow evaluation was outside its SDK act timer.
Every movement, kick, debug field and non-cache state matched original TITAN-10B.
Both driving/opponent records and shadow queries had zero exceptions/overruns.
These instrumented games establish sampled behavior equivalence, not strength.

The bounded native replay again reproduced v9.1's missed reception at tick 1497.
Using the optimized execution model for only receiver 2's run collected at
**tick 1507**, matching original TITAN-10B, with zero errors or deadline misses.

```sh
python tools/reproduce_execution_reception.py --challenger experiments/titan-10b-r/team.py --out work/reception-runtime
python tools/verify_passing_runtime.py --out work/runtime-equivalence.json
TITAN10B_TEAM_PATH=experiments/titan-10b-r/team.py ROBOCUP_TEAM_PATH=experiments/titan-10b-r/team.py python -m unittest discover -s tests -v
```

## Frozen fresh competition

Frozen **2026-10-17T17:05:04.699598+00:00**, before all fresh fixtures. No source change
or selection used fresh outcomes. Fifteen known fixed opponent styles × twelve
unused seeds × four side/kickoff arrangements = **720 paired fixtures** per
source, **1,728,000 decisions per source**, 2,400 ticks, engine 0.1.0 and config
`372990895c7eca2a`. This measures fresh-seed performance on a known local pool,
not live league rank or unseen styles.

| Metric | v9.1 | TITAN-10B-R |
|---|---:|---:|
| Points | 1864 | 1922 |
| Wins | 596 | 618 |
| Draws | 76 | 68 |
| Losses | 48 | 34 |
| Goals for | 2293 | 2351 |
| Goals conceded | 404 | 349 |
| Passes attempted | 34379 | 35329 |
| Passes completed | 16323 | 17319 |
| Passes intercepted | 11355 | 11266 |
| Uncollected passes | 6701 | 6744 |
| Turnovers | 3512 | 3777 |
| Pass completion | 47.48% | 49.02% |
| Ball-control share | 9.86% | 10.02% |

Pass completion and ball control improved, while turnover counts rose.
Uncollected passes were 19.49% → 19.09% of attempts.
These results do not establish better retention on every metric; promotion
uses points and the original reliability gate. The positive interval's lower
bound is close to zero, so the measured points advantage is modest.

Points/match difference **+0.0806**;
paired whole-seed bootstrap 95% interval **[+0.0028, +0.1722]**, 5,000 resamples.
Twelve seed blocks over this fixed pool determine that interval.

| Opponent (48 fixtures each) | v9.1 points | Runtime points | Change |
|---|---:|---:|---:|
| direct_hunter | 130 | 125 | -5 |
| direct_legacy | 138 | 140 | +2 |
| fast_counter | 138 | 144 | +6 |
| high_press | 142 | 144 | +2 |
| long_shooter | 117 | 120 | +3 |
| quick_wall | 142 | 144 | +2 |
| relay_legacy | 134 | 134 | +0 |
| tight_links | 119 | 139 | +20 |
| v3.7 | 130 | 138 | +8 |
| v4 | 128 | 132 | +4 |
| v6.1 | 115 | 120 | +5 |
| v7 | 98 | 105 | +7 |
| v9.1 | 65 | 67 | +2 |
| wall_runner | 140 | 144 | +4 |
| wide_switch | 128 | 126 | -2 |

## Original promotion gate, reliability and runtime

All gates must pass: more fresh points and positive paired 95% lower bound;
zero policy exceptions, no reproducible deadline failures; mean time ≤ champion
×1.35 +0.04 ms; no more than **two additional raw candidate deadline misses per
1,000 fixtures**. Otherwise retain v9.1. The allowance concerns raw misses,
not only accepted repeats.

| Gate | Result |
|---|---|
| more fresh points | Pass |
| positive seed bootstrap lower bound | Pass |
| zero policy exceptions | Pass |
| no reproducible deadline failures | Pass |
| acceptable mean runtime | Pass |
| acceptable raw timeout rate | Pass |

| Runtime/reliability | v9.1 | TITAN-10B-R |
|---|---:|---:|
| Raw policy exceptions | 0 | 0 |
| Raw deadline misses | 3 | 3 |
| Raw mean ms | 0.2049 | 0.2186 |
| Raw maximum ms | 30.8066 | 37.7069 |
| Accepted mean ms | 0.2049 | 0.2185 |
| Accepted maximum ms | 19.7533 | 15.6086 |
| Raw points | 1864 | 1922 |

Runtime ceiling **0.3166 ms**; additional raw misses **0.000 per 1,000**.
Repeated fixtures including opponent interruptions:
**4 → 2**.
Each timeout-containing fixture was repeated identically at most three times,
accepting the first clean result regardless of score. All raw records and every
attempt remain in the workspace. Exceptions were never repaired by repeating.

Initial official validation: 2,000 decisions/source, zero exceptions and overruns,
zero folder warnings/errors/static flags. Maximum **3.851 →
5.463 ms**.

## Auditable evidence and rerunning

[Source-bound results](titan-10b-r-results.json) · [720 paired rows](titan-10b-r-paired-scores.csv) ·
[Registered protocol](titan-10b-r-protocol.json) · [Frozen opponent sources](../tests/fixtures/titan-10b-opponents.zip).
The archive includes a per-controller SHA-256 manifest. The runner verifies it,
freezes both candidate sources, checks all fixture keys and preserves raw data.
Run from a complete checkout; the output folder must be new:

```sh
python tools/benchmarks/run_paired.py --protocol docs/titan-10b-r-protocol.json --out work/titan10br-fresh
python tools/benchmarks/compare.py work/titan10br-fresh/accepted/champion work/titan10br-fresh/accepted/runtime --out work/titan10br-comparison.json
python tools/benchmarks/audit_runtime_results.py
```

Frozen TITAN-10B-R SHA-256: `5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6`.
Frozen behavior baseline SHA-256: `269a24fe3f826500b3d6c1aad76f8770f0084f5a3ad81258cd7c2f50fba36108`.
Frozen competition baseline SHA-256: `c7fce081f12f283b9c9f9ee200f0dcc33769339a60bf535fc3446613612fabf6`.
