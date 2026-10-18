# NOVA-1 native validation

**Decision: RETAIN_V10_0. No promotion or change to main/my-team/team.py.**

The competitive objective was not achieved; v10.0 is the stronger measured submission. The selected controller is an independently implemented five-player planner, not a TITAN tactical patch. The result below is a local native benchmark; it does not establish a school ranking or performance against private league leaders.

Frozen candidate: `experiments/nova-1/team.py`, policy `g04-p00`, SHA-256 `8f66bdd17b8c70ccb879c96a6ce4db530922df5f9e9bccc888b20cedfd551463`. Frozen v10.0 SHA-256: `5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6`. Base main: `0a7a3aeba3950eb1b2ed0deeb7a06f2f9b3563e5`.

## Principal qualification

768 paired fixture configurations, 16 whole-seed blocks, 12 fixed opponent styles, both field assignments and both kickoff arrangements; 2,400 ticks per match with the official 20 ms wall deadline. Sources, protocols and the combined opponent archive were frozen before exposing heldout outcomes.

Accepted paired points/match delta: **-0.7865**, whole-seed paired bootstrap 95% interval **[-0.8490, -0.7188]** (5,000 resamples, fixed bootstrap seed). The independent unit is the match seed, not each mirrored fixture.

Raw initial fixtures, including all original deadline misses:

| Metric | Frozen v10.0 | NOVA-1 |
|---|---:|---:|
| Fixtures | 768 | 768 |
| League points | 1,659 | 1,055 |
| Wins | 519 | 319 |
| Draws | 102 | 98 |
| Losses | 147 | 351 |
| Goals scored | 2,326 | 1,357 |
| Goals conceded | 569 | 968 |
| Shots | 3,948 | 5,096 |
| Passes attempted | 32,565 | 29,747 |
| Passes completed | 17,358 | 12,887 |
| Passes intercepted | 9,140 | 10,911 |
| Uncollected passes (derived) | 6,067 | 5,949 |
| Turnovers | 3,776 | 4,771 |
| Policy exceptions | 0 | 0 |
| Raw deadline misses | 10 | 17 |
| Pass completion | 53.3% | 43.3% |
| Mean decision time | 0.2230 ms | 0.3461 ms |
| Maximum decision time | 48.935 ms | 61.598 ms |

First-clean exact repeats are used only for the paired football comparison; initial attempts and every failed repeat remain in the archive. Accepted points: 1659 v10.0 / 1055 NOVA-1. Raw extra deadline misses: **+9.1146 per 1,000 fixtures**. Repeats that also missed a deadline: 1. No mean-time substitution or environmental exemption is applied to the raw deadline gate.

Uncollected passes are the SDK-derived attempted − completed − intercepted count; they are not a separately annotated replay statistic. The SDK does not expose calibrated shot quality or goalkeeper saves.

### Matchup results

| Opponent | v10 pts | NOVA pts | NOVA W/D/L | NOVA goals | Δ points/match |
|---|---:|---:|---|---|---:|
| long_shooter | 154 | 78 | 19/21/24 | 50–66 | -1.1875 |
| tight_links | 162 | 131 | 39/14/11 | 88–37 | -0.4844 |
| unseen-asymmetric | 192 | 192 | 64/0/0 | 343–2 | +0.0000 |
| unseen-counter | 190 | 163 | 50/13/1 | 91–2 | -0.4219 |
| unseen-long | 192 | 192 | 64/0/0 | 347–0 | +0.0000 |
| unseen-swarm | 192 | 192 | 64/0/0 | 266–0 | +0.0000 |
| v10 | 88 | 17 | 3/8/53 | 26–142 | -1.1094 |
| v10-compact | 101 | 29 | 6/11/47 | 25–109 | -1.1250 |
| v10-counter | 97 | 15 | 2/9/53 | 43–169 | -1.2812 |
| v10-long | 93 | 17 | 4/5/55 | 26–154 | -1.1875 |
| v10-press | 82 | 11 | 1/8/55 | 18–137 | -1.1094 |
| v9.1 | 116 | 18 | 3/9/52 | 34–150 | -1.5312 |

Sealed generated opponent styles: 256 paired fixtures; v10.0 766 points, NOVA 739; paired delta -0.1055, 95% interval [-0.15625, -0.0625]. These are unseen parameterized local styles, not access to private school submissions. No heldout result was used for learning, candidate selection or a further tactical edit.

### Registered gates

| Gate | Pass |
|---|---|
| more_points | NO |
| positive_paired_95_lower | NO |
| unseen_more_points | NO |
| unseen_no_material_regression | NO |
| worst_style_no_collapse | NO |
| head_to_head_no_collapse | NO |
| zero_policy_exceptions | yes |
| no_repeated_deadline_failure | NO |
| raw_deadlines | NO |
| official_intake | yes |
| valid_actions | yes |
| source_frozen | yes |
| principal_fixture_count | yes |

The confirmation cohort remains untouched.

## Independent architecture and bounded execution

NOVA defines its own roles, formations, possession classification, goalkeeper targeting, plan proposals, compatible five-player movement assignments and scoring. A prospective pass locks the intended receiver and moves support toward the predicted collection point while assigning separate defensive cover. Every pass requires an executable receiver rollout, first-touch feasibility and earlier arrival than every physically verified opponent interception. Heuristic chase estimates only choose movement targets.

The low-level helper whitelist and exact hashes are in `nova-1/physics-provenance.json`. Source equivalence and 2,000 randomized movement/reach/contact comparisons, dense wall trajectories and executable receiver comparisons test the reuse. No TITAN act(), tactical selection, defensive shape or goalkeeper policy is inherited.

Promising complete team plans are evaluated against pressing and blocking/rushing opponent responses. The online bound is three plans × two responses × ten simulation steps (60 steps), with five pass launch trials, bounded receipt aims and shared dense flight/step forecasts. The short model uses acceleration, damping, speed caps, kick cooldown, body/wall restitution and player separation; future opponent input and future one-touch choices are hypotheses, not exact guarantees. Exact frozen helpers verify the pass and first kick. The policy embeds 8 geometry/risk parameters and 12 linear weights (19 active search dimensions); it imports only math and the permitted soccer SDK.

## Development and actual learning budget

144 native policy evaluations, 141 distinct source hashes, 134 distinct 19-dimensional parameter vectors. Retained elites are not counted as new parameter discoveries. Cross-entropy populations contain 24 policies, six elites and two retained parameter elites. Each policy plays 24 full native fixtures on a rotating six-style development league. The objective is paired points/match + 0.25 worst-style delta + 0.15 mean of the two worst-style deltas. Pass counts never determine fitness. Repeated baseline fixtures across population batches are not additional independent seeds.

### Per-generation best on that generation’s development fixtures

| Generation | Framework | Policies | Best policy | NOVA/v10 points | Paired Δ | Robust objective |
|---|---|---:|---|---|---:|---:|
| 0 | R4 | 24 | g00-p22 | 10/33 | -0.9583 | -1.6583 |
| 1 | R5 | 24 | g01-p01 | 39/55 | -0.6667 | -1.1667 |
| 2 | R6 | 24 | g02-p23 | 31/53 | -0.9167 | -1.6604 |
| 3 | R7-PASS | 24 | g03-p15 | 30/40 | -0.4167 | -0.9792 |
| 4 | R7-PASS | 24 | g04-p19 | 50/57 | -0.2917 | -0.5729 |
| 5 | R7-PASS | 24 | g05-p15 | 14/33 | -0.7917 | -1.5354 |

Generations use different development seeds/styles; these raw point totals are not causal comparisons of architecture revisions. All parameter vectors, source hashes, framework snapshots and outcomes are retained. Every registered framework/population reconstruction must reproduce its exact hash.

The initial population uses frozen R4. Development then exposed keeper carry/recovery and future receipt ownership inconsistencies; R5 corrects those command contracts, preserves support runs and models advancing carry pursuit. R6 prevents three similar cheap-ranked plans starving a distinct feasible action family from the same three-plan response budget. Each change has a focused regression, was frozen before its generation and used development data only. No measured population source was edited.

Failed training intake evaluations: 1. Their source hashes are ineligible for shortlist selection; the native measurements and original validation reports remain in the evidence. A fast mean never cancels a failed intake.

| Failed source | Original SDK error |
|---|---|
| g02-p23 | 1 of 2000 decisions exceeded the 20 ms deadline (slowest 25.1 ms). On the server these become repeated actions and count against reliability. |

Public-intake timing failures do not have the native fixture slow-call CPU/GC instrumentation, so the evidence cannot establish their cause. They remain failures regardless of the later native timing.

### Isolated first-command contact experiment

Four native development replays of frozen g02-p00 exposed a carrier-body reversal: at tick 495, a forward carry request produced vx=−11.6259 after contact, while a legal braking first command preserved vx=+6.1468. The case is a physical regression, not proof that braking wins games. Across those instrumented diagnostic games 33 named receivers touched their passes, 6 plans were superseded, 4 had another player touch first and 1 was unfinished; 16/179 isolated predicted launches differed from the next native position by more than half a unit, excluding goal resets. Other-player collisions and opponent actions are not covered by an isolated carrier witness. The diagnostic harness observes extra state, so none of its timing is used for qualification.

Pass-only and carry-only first-command changes were then tested independently with identical learned weights on 32 paired configurations per source, four strong styles and two unused development seeds. Each chooses between the ordinary movement and a legal brake by post-contact velocity error, before the existing physical pass verifier. It compares two cheap contact trials per option and keeps one launch, without an additional expensive pass race. A combined test runs only if both isolated features help. The registered development selection rules and all failures remain in the branch.

| Variant | Points | Δ points/match vs R6 | Worst-style Δ vs R6 | Eligible |
|---|---:|---:|---:|---|
| r6 | 6 | +0.0000 | +0.0000 | no |
| r7-pass | 8 | +0.0625 | +0.0000 | yes |
| r7-carry | 6 | +0.0000 | -0.2500 | no |

Framework for uncreated generations 3–5: **r7-pass**. Combined native test run: False. The scheduler was paused between complete native batches for diagnostics; no decision was paused and no measured population source changed. This development study used no qualification or heldout result.

### Controlled-body retention experiment

The first shortlist exposed a large competitive deficit (best 83 vs v10.0 238 points). A slow-shot goalkeeper hypothesis had no matching missed-goal case in the available development traces, so the goalkeeper was left unchanged. A separate action-space limitation was concrete: every selected carrier plan requested a kick. An isolated experiment adds movement-only retention when the first step produces a controllable body touch and no verified opponent interception in the first 0.10 seconds. Otherwise the existing kicked carries remain. The chosen drive movement continues in its short response model; act() can issue movement without a kick. Passing verification, shooting, goalkeeper behavior and defensive roles remain unchanged. The same three-plan × two-response × ten-step bound is retained.

The reference is the frozen first-shortlist winner with identical weights. Both sources and v10.0 play 64 configurations over eight known styles, two separate unused development seeds and both sides/kickoffs.

| Source | Points | Δ points/match vs reference |
|---|---:|---:|
| Existing reference | 43 | 0 |
| Body retention | 34 | -0.1406 |

Adopted for uncreated generation 5: **False**. The existing generation-4 population stays byte-frozen. The original promotion gates and sealed cohorts remain unchanged. Focused regressions require an actual movement-only action for a controllable contact and reject retention of a fast ball or an imminent tackle.

### Initially available opponent kicks

A separate model regression exposes an optimistic first step: the previous response model never let a ready defender kick until step 1. With a ready defender beside the ball, two opposing legal impulses cancel a close shot that the delayed model counted as a goal. R9 changes only the pressing response to allow an opponent kick on step 0. Own uncommanded follow-up shots remain forbidden on step 0; the blocking response retains its one-step lag. The budget stays at three plans × two responses × ten steps.

This follow-up was registered before population selection ended and before any sealed outcome. It reuses the population winner’s learned 19 parameters without retuning. A 64-configuration screen uses two unused development seeds; a separate 128-configuration check on four more development seeds runs only if the screen helps. Both cohorts must improve paired points without the registered style/head regressions, pass SDK intake and raise no exceptions. Population snapshots and the original selection remain preserved.

| Development stage | Reference pts | Immediate-response pts | Δ points/match | Eligible |
|---|---:|---:|---:|---|
| screen | 29 | 36 | +0.1094 | yes |
| check | 77 | 65 | -0.0938 | no |

Adopted: **False**. Learned parent: `g04-p00`. The original promotion gates, principal qualification seeds and conditional competition confirmation remain unchanged.

### Development selection

| Stage | Selected policy | NOVA/v10 points | Paired Δ | Worst-style Δ |
|---|---|---|---:|---:|
| selection-0-results | g03-p20 | 83/238 | -1.2109 | -1.9375 |
| selection-1-results | g04-p00 | 74/228 | -1.2031 | -1.8750 |

Each shortlist uses 128 fixture configurations per candidate on four development seeds, with up to eight distinct intake-passing sources. The registered extra two generations run only if the first shortlist remains weaker or fragile. Failed intake hashes are ineligible for selection. Training, shortlists, qualification and conditional confirmation use disjoint seed cohorts.

### Independent development diagnostics

Preregistered after the architecture fixes but before source selection: 64 paired configurations per source on two separate development seeds. These diagnostics neither select parameters nor replace the frozen candidate. They isolate response evaluation with identical learned weights and compare learned vs default parameters within the same framework.

| Model | NOVA/v10 points | Paired Δ | Worst-style Δ |
|---|---|---:|---:|
| learned-joint | 31/115 | -1.3125 | -1.8750 |
| learned-open | 27/115 | -1.3750 | -1.8750 |
| untrained-joint | 32/115 | -1.2969 | -1.6250 |

Negative ablations are retained; architectural complexity alone is not evidence of competitive value.

### Preserved failures

The first independent baseline passed the public short SDK check but raised two IndexErrors in a full native game. At tick 1352 the conservative forecast had already stopped near the opponent goal aperture while the native engine still supplied a live ball (x=49.9508247375, y=5.5898900032). R2 handles an empty forecast using the observed live position. The original source, partial native rows, failure frame and logs remain available.

The 32-configuration R2 screen scored v10.0 63 points, open-loop NOVA 32 and joint NOVA 29. These failures were retained and motivated development-only corrections; neither was called a champion. An observer assertion initially used the wrong argument in one test; its failed log is retained alongside the corrected test run.

## Timing evidence

Raw decision distributions use the unmodified SDK wall timer in 0.025 ms bins. Intervals below are bin bounds, not more precise measurements.

| Source | Median ms | p95 ms | p99 ms | p99.9 ms |
|---|---|---|---|---|
| v10 | [0.125, 0.150) | [0.525, 0.550) | [2.100, 2.125) | [4.325, 4.350) |
| nova | [0.225, 0.250) | [0.450, 0.475) | [3.650, 3.675) | [5.875, 5.900) |

The external harness records thread CPU and GC overlap on the original slow calls for both controllers, and per-fixture cgroup/wall/CPU changes. GC policy, clocks, affinity, SDK and engine remain unchanged. Correlation with GC or a wall/CPU gap is diagnostic evidence, not proof of a sole cause and never grounds to discard a raw miss. The external observation window includes dispatch/return overhead, so CPU/GC observations are not an exact decomposition of SDK act() time.

```json
{
  "v10": {
    "calls_ge_5ms": 1009,
    "raw_calls_gt_20ms": 10,
    "slow_calls_with_gc_overlap": 2,
    "deadline_calls_with_gc_overlap": 0,
    "deadline_wall_cpu_gap_gt_5ms": 0
  },
  "nova": {
    "calls_ge_5ms": 5620,
    "raw_calls_gt_20ms": 17,
    "slow_calls_with_gc_overlap": 39,
    "deadline_calls_with_gc_overlap": 0,
    "deadline_wall_cpu_gap_gt_5ms": 0
  }
}
```

No GC overlap or wall-minus-thread-CPU gap over 5 ms was recorded on these original deadline calls. The measurements are consistent with CPU-accounted work, and do not justify dismissing the misses as long descheduling pauses. They do not establish a sole root cause and never waive the registered gate.

### Offline decision replay and hotspots

1920 recorded native frames reconstructed with pre-decision state and native kick/control gates; action mismatches: 0. Maximum evaluated plans/steps: 3/60. This checks command replay, not the accuracy of hypothetical opponent responses. The separate cProfile replay adds overhead and uses Python observation records; its timings never enter a deadline gate.

| Function | Calls | Own ms | Cumulative ms |
|---|---:|---:|---:|
| act | 1,920 | 37.19 | 1561.89 |
| _estimate_chase | 40,883 | 564.65 | 933.83 |
| _shape | 2,195 | 25.69 | 571.81 |
| _select | 46 | 2.10 | 389.46 |
| <genexpr> | 13,170 | 4.26 | 248.20 |
| <genexpr> | 11,520 | 4.95 | 232.97 |
| _response | 258 | 81.16 | 224.47 |
| <lambda> | 7,680 | 3.97 | 193.44 |
| _proposals | 46 | 5.41 | 161.96 |
| _pass_path | 3,475 | 93.08 | 142.52 |
| _collect | 377 | 3.56 | 81.55 |
| _move | 35,492 | 37.81 | 67.54 |

## Reproduction and evidence

Final regression run: 118 tests; official candidate intake: 2,000 decisions, passed=True. The complete regression log and SDK intake JSON are retained. All registered population sources are rebuilt and hash-checked by a regression; the selected-source test also verifies the measured frozen policy and actual finite five-player commands. Legacy v10 API tests protect the unchanged champion; NOVA-specific tests exercise the independent controller, shared physics and selected-source integrity.

Run from this branch with the official student SDK/native engine installed:

```bash
python -m unittest discover -s tests -q
python tools/nova/rebuild_population.py --out work/nova-rebuilt
python tools/nova/replay_registered.py --protocol docs/nova-1/qualification-protocol.json --out work/nova-qualification-replay
python tools/nova/replay_registered.py --protocol docs/nova-1/g00-batch00-protocol.json --population work/nova-rebuilt --out work/nova-g00-replay
```

The training program deliberately refuses to overwrite existing source registrations or evidence. The full search command is `python tools/nova/train.py --work <fresh-evidence-directory>` in a clean development checkout with generated generation/selection files absent. `qualify.py` then freezes the source and principal protocol and conditionally confirms. From this populated final branch, the replay tool above verifies original source hashes and relocates only their paths in a new protocol; it preserves the original seeds, styles, ordering and limits. Reconstruction uses explicit generation-specific framework snapshots; it does not substitute the latest template for old policies.

New searches can differ because intake eligibility and the last timing tie-break depend on new measurements. Exact registered source reconstruction and frozen-protocol replay remain available; no claim of identical timing or identical new search results across machines is made.

Evidence archive: `tests/fixtures/nova-1-native-evidence.zip`, SHA-256 `bebc21462abb5a8d49ca8820928c20e77fde4e2a361bb7bf21c08eec743e958d`; 1,735 manifest-verified files, 21,991,300 compressed bytes. It retains native raw/accepted records, all repeat attempts, source/opponent snapshots, intake reports, environments, slow-call evidence, histograms, partial failed runs and test logs. Private scratch notes are excluded. Registered parameters, sources, protocols, fixed opponent archives and tests are committed separately.

No generated controller needs this evidence, trainer, parameter files or any other Python file at runtime. The candidate remains a development experiment unless all registered promotion gates and confirmation pass and the user explicitly approves promotion.
