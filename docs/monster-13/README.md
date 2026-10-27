# MONSTER13: frozen baseline and first engineering results

**Keep the uploaded MONSTER `v25-fast-post` unchanged.** The best small development candidate failed fresh qualification, so no experimental modification is recommended. The user's new champion is preserved byte-for-byte at [my-team/team.py](../../my-team/team.py) on branch `monster-13-review`, and at [uploaded/team.py](../../experiments/monster-13/uploaded/team.py). `main`, `sandbox-champion-hunt`, and archived champions are unchanged.

This review adopts the user's uploaded `team (13).py` as the new behavior baseline. It does not claim that the upload is universally stronger than the previous controller or that an actual match against Milla Singh has been won. The earlier division-leader study is retained as context and its old-baseline qualification was suspended when the user supplied this new file.

## Reliability foundation

The original upload completed **1,075,200 decision calls in 448 full native research fixtures**, with **zero policy exceptions and zero raw deadline misses**. These include repeated development controls; they are not 448 independent seed samples. The slowest original-source decision across these cohorts was **6.900575 ms** against the official 20 ms limit.

Official intake independently passed all five public seeds / 2,000 decisions: zero errors or warnings, exceptions, deadline misses, missing actions or nonfinite values. Mean **0.059 ms**, slowest **2.116 ms**. The controller defines one SDK subclass and all runtime code fits in its single 27,381-byte file. It uses the existing 7 ms search budget through `perf_counter`; the official deadline and engine enforcement were never changed.

The frozen SHA-256 is `1bf09f5fcab940eae8f387ef36030d302dfe9e52aa6ae0fe82f48742ea6e85b7`. Original CRLF line endings are retained. The branch submission and archived upload have the same bytes.

## Strength comparison with the previous adaptive controller

The first panel used **128 full fixtures per source**, four fresh seeds `3260271101–3260271104`, eight common opponents, both pitch assignments and both kickoff arrangements.

- Previous adaptive: **216 points**, 61W–33D–34L, 160–157 goals.
- Uploaded MONSTER13: **149 points**, 42W–23D–63L, 164–165 goals.
- Paired MONSTER-minus-adaptive difference: **−0.5234375 points per fixture**, seed-block 95% interval **[−0.9375, −0.265625]**.

| Common opponent | Previous adaptive points | MONSTER13 points |
| --- | ---: | ---: |
| Previous adaptive | 19 | 25 |
| Milla stress surrogate | 36 | 33 |
| Strong replay controller | 17 | 8 |
| v10 compact | 38 | 13 |
| v10 counter | 29 | 27 |
| v10 press | 24 | 11 |
| Frozen v10 | 19 | 9 |
| Frozen v9.1 | 34 | 23 |

These columns are separate sources facing identical common opponents; their scores are not complementary head-to-head scores. The previous-adaptive reference row is self-play for that source. In the upload's actual direct matches against the previous adaptive, MONSTER scored **22–17 goals**, with **8 wins, one draw and seven losses** (25–22 points). That narrow direct advantage did not transfer to the wider panel.

The eight-style panel is a local research population, not the live league schedule. Intake exercises the normal custom-formation hook; comparative fixtures use the native default rosters that faithfully reproduced the supplied course replays. A different formation profile or opponent population could change strength results. The upload's custom four-cover starting formation is therefore not silently substituted into the course-replay benchmark.

## What the code actually executes

`SHELL=True` selects four covering players and one outlet on practically every ordinary decision. It bypasses most of the normal pressing, passing and reception logic below that branch. Improving the inactive `passing()` routine alone would not improve this submitted configuration.

The outlet waits around x=−20 on a side selected by the first incoming wide attack, then chases projected ball positions. Four covering players issue full-power diagonal clearances. Their home depth changes from 1.2 to 3.3 units after taking a lead. The two outside coverers adjust toward nearby wide threats. These facts guided isolated experiments; they were not treated as evidence that any particular change must win.

## Independent development and rejection

Four first-round hypotheses were tested individually across four styles, two exposed seeds `3260272101–3260272102`, both sides/kickoffs: **32 matches per source**, 160 full matches total. The separate cooldown experiment repeated the same panel with a contemporaneous baseline, 64 additional matches. That repeated baseline is not independent validation.

| Source | Points | Goals |
| --- | ---: | ---: |
| baseline | 37 | 45–45 |
| release | 40 | 49–57 |
| hold-depth | 40 | 51–47 |
| outlet12 | 40 | 46–46 |
| central-clear | 21 | 46–80 |
| stagger | 32 | 41–55 |

- **release:** enable the existing release from the four-cover shape when behind or facing a visible goal wall. It gained three points but conceded 57 goals versus 45.
- **hold-depth:** retain the 1.2-unit cover depth after taking a lead. It gained three points but showed mixed seed results.
- **outlet12:** move the waiting outlet from x=−20 to x=−12. It gained three points with the lowest concessions among the tied candidates, so it was selected for qualification.
- **central-clear:** maximize forward impulse in dangerous home clearances. It lost 16 points. A forward requested kick direction alone is not evidence of a safe native outcome.
- **stagger:** let a farther eligible covering player clear while reserving the nearest player's cooldown for a rebound. It lost five points. Preserving one cooldown was not a demonstrated advantage against simultaneous opposing pressure.

All tested source roles had zero policy exceptions and raw misses. The failed sources remain in the evidence archive. No source changes or combinations followed their results.

## Fresh qualification: outlet adjustment rejected

The selected source differs behaviorally only in `OUTLET_X = -12.0`. Its final version label changed to `v25-outlet12-candidate`; all function ASTs match its development parent. The original upload remains unchanged.

The [plan](results/qualification-plan.json) and source hashes were frozen before **512 new paired native fixtures**, 256 per source. Eight untouched seeds `3260274101–3260274108` cover all eight styles and all four pitch/kickoff arrangements. One worker, engine `0.1.0`, config `372990895c7eca2a`, 2,400 ticks, official 20 ms deadline. No source tuning, reselection or discarded fixtures followed qualification.

| Source | W–D–L | Points | Goals |
| --- | --- | ---: | ---: |
| Original upload | 94–55–107 | **337** | 377–347 |
| Outlet adjustment | 84–79–93 | **331** | 374–331 |

Paired difference: **−0.0234375 points per fixture**, 95% seed-block interval **[−0.140625, +0.09765625]**. The adjustment conceded fewer goals and lost fewer matches, but also won fewer matches. It did not demonstrate a league-point improvement. The interval includes zero, so this is not a claim of statistically significant harm.

| Common opponent | Original points | Adjustment points |
| --- | ---: | ---: |
| Previous adaptive | 60 | 67 |
| Milla stress surrogate | 62 | 62 |
| v10 counter | 35 | 39 |
| v10 press | 48 | 43 |
| v10 compact | 10 | 16 |
| Frozen v9.1 | 49 | 42 |
| Frozen v10 | 50 | 43 |
| Strong replay controller | 23 | 19 |

| Registered gate | Result |
| --- | --- |
| Positive paired points 95% lower bound | **FAIL: −0.140625** |
| Zero policy exceptions | Pass: zero |
| At most +2 extra raw misses / 1,000 fixtures | Pass: zero additional |
| No style decline greater than 0.25 points / fixture | Pass |
| Official public-seed intake | Pass |
| Promote experimental change | **No** |

Both source roles had zero raw misses and exceptions. Qualification contained **three opposing-side raw misses**, retained in full; the initial comparison contained two and development one. Thus the 992 research fixtures contain six opposing-side misses, not an all-sides zero-miss result. Their causes were not determined or filtered. Rejected kick requests are recorded separately in SDK validation fields; they are not policy exceptions.

## Reproducible clearance failure

The diagnostic at `own-goal-repro/` records a full native game: MONSTER13 versus frozen v10, seed `3260271104`, candidate side 0 with its own kickoff. It reproduced the initial panel's **0–2 loss**, with **both goals recorded as own-goals by covering player 1** at event ticks 1441 and 1993. This is one selected exposed diagnostic, not independent competitive validation.

Before the second goal, players 1 and 2 both kick at tick 1991. Opposing and friendly body contacts return the ball toward the goal while those players are on cooldown. The first goal also follows interleaved friendly/opposing kicks. The recorded actions show why a single-player launch model or a requested forward vector cannot establish safety. Correct future modelling needs joint movement, impulse ordering and contacts, validated against native outcomes. Neither the straight-clearance nor cooldown-stagger experiments proved that they solve this problem.

The supplied Milla replays used earlier behavior strongly consistent with the previous adaptive fallback, not MONSTER13's permanent four-cover shape. Those four losses totaled 1–10, including four user own-goals. Their native reconstructions and short controlled keeper interventions are retained in the contextual archive. Short interventions with recorded opponent actions are not wins against a reactive opponent.

The Milla stress source is a partially fitted public-observation model, not recovered opponent code: held-out kick-direction median error about 35.4 degrees and power error .366. Wins against that model must not be presented as wins against Milla Singh. No actual leader win is claimed here.

## Next engineering targets

1. **Joint contact and clearance safety.** Reproduce the defender own-goal chains and test corrections against actual simultaneous impulses and body contacts. Counting avoided own-goal credits alone is insufficient; the opponent may still score.
2. **More attacking support against compact teams.** Test a controlled release of a second outlet with an executable recovery plan. The baseline's one-attacker shape has a clear local weakness against compact and pressing styles. A useful mode must improve points while retaining the current reliability.
3. **Actual reception and finishing execution.** Keep future decisions aligned with movement commands, cooldowns and first-touch physics. The existing `race()` fallback includes heuristic arrival estimates; it must not be advertised as verified pass feasibility if passing is enabled later.

These are further experiments, not implemented or accepted upgrades. The tested original file is retained as requested.

## Evidence and reproduction

The [archive](evidence.zip) contains executed harnesses, frozen sources, raw match records, registrations, tests, intake results, diagnostic replay, and selected earlier leader-study context. The original HAR, request metadata, cookies, headers, the full table capture and redundant fitted feature rows are excluded. `MANIFEST.json` records payload hashes; [evidence-manifest.json](evidence-manifest.json) records the archive hash and integrity check.

Seven focused action/AST regressions pass. The initial six-test script and log are retained alongside the extended seven-test script. The latter verifies keeper/outlet boundaries, protected actions, release behavior and cooldown selection; none substitutes for native match results.

To reproduce a fixture, provide the complete official native SDK through `PYTHONPATH`:

```bash
PYTHONPATH=/path/to/complete/student-sdk \
python tools/benchmarks/champion_hunt_match.py \
  --candidate experiments/monster-13/uploaded/team.py \
  --opponent champions/v10.0/team.py \
  --seed 3260271104 --side 0 --own-kickoff \
  --output reproduced-monster-case.json
```

All original executed batch scripts and absolute paths are retained in the archive, with frozen opponents for remapping. Older leader-study builders expecting the old adaptive SHA should be pointed at that archived baseline, not run against the newly adopted branch submission. Do not overwrite historical evidence.

`audit_results.py` independently recomputes the paired interval and gates from raw records. It verifies all **992** full research attempts are complete and balanced within their cohorts. The diagnostic replay and two five-match official intakes are separate. Dataset matching and confidence calculations preserve complete seed blocks instead of treating repeated sides/kickoffs as independent samples.
