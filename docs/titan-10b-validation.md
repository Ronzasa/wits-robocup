# TITAN-10B: execution-aware passing

**Not promoted.** `my-team/team.py` and the workspace mirror remain byte-identical v9.1. The unchanged champion is [preserved here](../champions/v9.1/team.py).
The [frozen challenger](../experiments/titan-10b/team.py) remains separate and reviewable.
Fresh points improved, but raw deadline misses rose **22 → 33**, exceeding the
registered allowance of two additional misses per 1,000 fixtures. The original
20 ms deadline and promotion rule were retained. These are local native-engine
results, not a measured change in league rank.

## Reproduced execution failure

Against frozen v7, seed 1239849544, side 0, own kickoff, v9.1 tick **1497**
approved receiver 2 at **0.40 s**. The receiver never got closer than **2.3510**
units through that predicted window; kick range is 2.2. The pass remained
uncollected through the recorded window. A second clean native replay matched
all 81 public frames and commands exactly, at the normal 20 ms deadline.

The physical forecast allowed a kick after moving into range. `act()` instead
selects a carrier using the observation's **before-movement** `can_kick`, then
requires its moved position to be within `kick_range - 0.18`. The forecast's
constant-acceleration witness also need not match `_move()`'s braking/turning.
Live role, cover or friend-avoidance targets can further change the issued run.

In a native counterfactual with the same fixture and unchanged policy until
1497, changing **only receiver 2's run** to the executable aim produced collection
at **tick 1507**. Both teams had zero exceptions and deadline misses. This is
a diagnostic mechanism check, not a strength or rank result.
[Public snapshots, actual commands and the native counterfactual](../tests/fixtures/execution-reception-cases.json).
Reproduce both native cases from this checkout (normal 20 ms deadline):

```sh
python tools/reproduce_execution_reception.py --out work/reception-replay
```

The runner restores the exact frozen v7 opponent from git history and preserves
raw observations/results. It fails on an interruption or any frame mismatch.
Earlier full-history diagnostic retries caused observer allocation/GC stalls;
they were retained separately and excluded. A bounded observer reproduced the
clean primary case without changing the policy or deadline. Supplementary
snapshots are trajectory regressions, not fresh evidence.

## Minimal integration

- Keep `_pass_reachable()` and `_verified_intercept()` unchanged for opponents'
  physical capability checks. The general `_intercept()` remains unchanged.
- Roll a named receiver forward using the actual `_move()` law, current momentum,
  damping, acceleration, speed cap, cooldown and `act()`'s kick gates. A physically
  possible native kick is insufficient if the controller would not request it.
- Reuse the dense pass flight, including carrier contact and both rebound legs.
  Try at most four clipped aims: the previous verified point and short advances
  along the real flight. Check every native tick, not just sparse movement samples.
- New passes command the selected execution aim. Live plans update their aim as
  the ball travels, then validate again using the **actual first movement** that
  survived role, cover and avoidance selection. Cancel an unsupported plan while
  preserving that movement command. A non-carrier cannot claim a first-tick kick.
- Shared `_pass_race()` propagates the check to direct links, transition releases,
  side/end-wall collection, legacy pass safety, and new/live reception plans.
  Opponents retain their conservative physical opportunities along the full route.

Shooting, goalkeeper, defensive cover, ordinary movement and existing carrier/
touch collision helpers are unchanged. Tests compare unchanged helper ASTs and
show actual-command cancellation leaves every player's current command unchanged.
All player attributes and competition constraints are fixed; only `math` and the
official `soccer` SDK are imported by the controller. No identity/seed-based
tactics, hidden engine state, engine changes or runtime file access are used.

Command-priority following, held targets and the optional first-touch-quality
filter remain **disabled**. Their separate experiments did not justify including
them. The optional filter tested post-contact restitution, approach speed,
cooldown and immediate defender recovery; it was not promoted for higher pass
completion alone. The disabled framework was action/plan-equivalent to v9.1
on 600 shared native public observations.

The rollout is bounded and collision-free for future player travel. It cannot
guarantee collection after unknown player collisions, future opponent actions or
later tactical changes. Its purpose is to reject an execution the current
commands cannot support, not to claim globally optimal reachability.

## Independent experiments and source freeze

Screen: eight fixed styles × two new development seeds × four side/kickoff
arrangements = **64 paired fixtures per source**. `quality` adds only first-touch
screening to `execution`; `aligned` combines execution with command priority;
`aligned_hold`/`aligned_quality` add the respective independently tested feature.
`role_aware` preserves role commands and validates their actual first step.

| Variant | Points | W/D/L | GF–GA | Pass completion |
|---|---:|---:|---:|---:|
| champion | 156 | 49/9/6 | 195–37 | 46.94% |
| execution | 164 | 52/8/4 | 198–32 | 52.59% |
| follow | 161 | 51/8/5 | 200–33 | 47.63% |
| hold | 160 | 51/7/6 | 204–34 | 45.03% |
| quality | 164 | 52/8/4 | 198–32 | 52.72% |
| aligned | 164 | 52/8/4 | 201–31 | 53.13% |
| aligned_hold | 159 | 50/9/5 | 207–41 | 51.37% |
| aligned_quality | 164 | 52/8/4 | 201–31 | 53.13% |
| role_aware | 158 | 50/8/6 | 191–36 | 52.63% |

Expanded development: ten styles × six development seeds × four arrangements
= **240 paired fixtures per source**.

| Variant | Points | W/D/L | GF–GA | Pass completion |
|---|---:|---:|---:|---:|
| champion | 594 | 189/27/24 | 804–124 | 52.01% |
| execution | 621 | 197/30/13 | 788–129 | 52.64% |
| aligned | 618 | 196/30/14 | 808–130 | 52.52% |
| quality | 621 | 197/30/13 | 788–129 | 52.67% |
| role_aware | 615 | 196/27/17 | 775–132 | 52.39% |
| role_lifecycle | 621 | 197/30/13 | 788–129 | 52.64% |

The execution-only ablation earned 621 points but did not resolve the known live
role-command mismatch. Command priority changed the named receiver's role command
and scored fewer points. The selected complete integration was `role_aware`
with its lifecycle correction, which preserves existing cover/avoidance commands. The first-touch filter added no
development points, wins or goal benefit; held targets lost points in the combined
screen. Retention metrics were mixed, so pass completion never selected a winner.

A lifecycle regression found before reading the first fresh aggregate scores
showed that a replacement pass could be cancelled by a check against the old
trajectory. A failing regression test reproduced it; a one-line guard prevents
the stale check. Both first-cohort 720-fixture runs were preserved and excluded
without inspecting their aggregate results. The corrected integration repeated
development, and twelve new unused seeds were registered under the same gate.

Frozen at **2026-10-17 18:09:16 SAST**, before any corrected fresh fixture. Release cleanup changed only
documentation and version; normalized decision ASTs were identical. Fresh scores
were never used to tune or replace this candidate.

## Frozen fresh comparison

**720 paired fixtures per source**: 15 known frozen opponents, 12 unused seeds,
both pitch assignments and kickoff arrangements. Engine 0.1.0, course config
`372990895c7eca2a`, 2,400 ticks, normal **20 ms** decision deadline, one worker per
source concurrently. This is fresh-seed validation over a known pool, not a claim
to have tested the current league leader or wholly unseen opponents.

[Complete source-bound evidence](titan-10b-results.json) ·
[Every paired score and pass/retention/runtime metric](titan-10b-paired-scores.csv).

| Metric | v9.1 | TITAN-10B |
|---|---:|---:|
| Points | 1847 | 1917 |
| Wins | 591 | 618 |
| Draws | 74 | 63 |
| Losses | 55 | 39 |
| Goals for | 2357 | 2477 |
| Goals conceded | 464 | 401 |
| Passes attempted | 33843 | 34934 |
| Passes completed | 15808 | 16641 |
| Passes intercepted | 11221 | 11222 |
| Uncollected passes | 6814 | 7071 |
| Turnovers | 3531 | 3699 |
| Pass completion | 46.71% | 47.64% |
| Ball control share | 9.76% | 9.92% |

Pass completion increased, but uncollected passes and turnovers also increased.
The uncollected share was 20.13% → 20.24% of attempts. These results do not
establish improved retention across every metric.

Points/match difference **+0.0972**;
paired whole-seed bootstrap 95% interval **[+0.0153, +0.1875]**, 5,000
resamples. The interval measures seed variability over this fixed pool only.

| Style (48 fixtures each) | v9.1 points | Challenger points | Change |
|---|---:|---:|---:|
| direct_hunter | 124 | 136 | +12 |
| direct_legacy | 142 | 142 | +0 |
| fast_counter | 144 | 141 | -3 |
| high_press | 142 | 144 | +2 |
| long_shooter | 109 | 118 | +9 |
| quick_wall | 144 | 142 | -2 |
| relay_legacy | 136 | 142 | +6 |
| tight_links | 123 | 128 | +5 |
| v3.7 | 121 | 128 | +7 |
| v4 | 116 | 115 | -1 |
| v6.1 | 119 | 115 | -4 |
| v7 | 90 | 103 | +13 |
| v9.1 | 67 | 87 | +20 |
| wall_runner | 139 | 141 | +2 |
| wide_switch | 131 | 135 | +4 |

## Promotion, reliability and runtime

Every registered gate must pass: more fresh points and a positive paired 95%
lower bound; zero policy exceptions; no reproducible deadline failures; mean
decision time ≤ champion ×1.35 +0.04 ms; at most two additional raw candidate
timeouts per 1,000 fixtures. Otherwise keep v9.1.

| Gate | Result |
|---|---|
| more fresh points | Pass |
| positive seed bootstrap lower bound | Pass |
| zero policy exceptions | Pass |
| no reproducible deadline failures | Pass |
| acceptable mean runtime | Pass |
| acceptable raw timeout rate | Fail |

Mean accepted decision time: **0.2162 → 0.2481 ms**;
registered ceiling **0.3319 ms**. Raw exceptions:
**0 → 0**;
raw candidate deadline misses **22 → 33**.
Raw points: **1847 → 1917**. The extra raw misses were
**15.28 per 1,000 fixtures**, above the limit of 2.

| Runtime measure (ms) | v9.1 | Challenger |
|---|---:|---:|
| Raw mean | 0.2174 | 0.2501 |
| Raw maximum | 91.8029 | 478.0459 |
| First clean repeat maximum | 19.9874 | 19.9875 |

Exact interrupted-fixture repeats and standalone validation were clean. That
alone does not prove the raw timing difference was harmless, so the gate was
not relaxed. The challenger needs further runtime work before promotion.

Any fixture with either team's timeout was repeated identically, at most three
times, accepting the first clean result regardless of score. Exceptions were
never repaired by repeating. Raw rows and all attempts remain in the workspace.
Repeated fixtures including opponent interruptions:
**15 → 18**.
Accepted tables retain the same input fixtures and do not erase raw interruptions.

Additional standalone official validation: 2,000 decisions per source.
Champion: 0 exceptions,
0 overruns, mean
0.219 ms, maximum
4.822 ms.
Challenger: 0 exceptions,
0 overruns, mean
0.211 ms, maximum
6.491 ms.
Challenger warnings: []; folder errors/warnings/static flags:
[] / [] / [].

## Tests and exact sources

All **81 regressions** pass, including the retained 60 and 21 execution/first-touch/
planning cases. New coverage includes the repeated native miss and collection,
before/after-movement gates, moving receivers, actual-command cancellation,
opponent interception, both mirrored wall routes, cooldowns, glancing first
touches, bounded aim changes and unchanged non-receiver commands.

```sh
python3 -m unittest discover -s tests -v
ROBOCUP_TEAM_PATH=champions/v9.1/team.py python3 -m unittest discover -s tests -v
TITAN10B_TEAM_PATH=experiments/titan-10b/team.py ROBOCUP_TEAM_PATH=experiments/titan-10b/team.py python3 -m unittest discover -s tests -v
```

Champion SHA-256: `c7fce081f12f283b9c9f9ee200f0dcc33769339a60bf535fc3446613612fabf6`.
Frozen challenger SHA-256: `269a24fe3f826500b3d6c1aad76f8770f0084f5a3ad81258cd7c2f50fba36108`.
