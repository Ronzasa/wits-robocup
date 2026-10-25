# Champion hunt: an adaptive counter, not a universal replacement

The recommended experimental file is [TITAN Adaptive Counter](../../experiments/champion-hunt-adaptive/team.py). It beat the uploaded `champion_candidate.py` **79 wins, 46 draws and 3 losses** in 128 fresh native matches, scoring **283–55 league points** and **203–121 goals**. In a separate paired five-style panel, it earned **303 points versus the uploaded controller's 275**, with a positive paired 95% confidence interval.

**Keep the active champion unchanged.** The adaptive file passes this study's engineering gates, but misses the original strong score targets of 75% wins and +1.5 goals per direct match. These results support an experimental improvement against the tested field; they do not establish a live league ranking or dominance over the top two teams.

All experiments are on `sandbox-champion-hunt`, based on `5249bf925b579f9dde9b9739694670bfa2207493`. Neither `main`, `my-team/team.py`, the uploaded opponent nor archived champions was modified. No promotion is performed.

## What changed and why

The uploaded opponent can withdraw all five players into a narrow goal wall. Its wall-breaking response also sends players forward when facing a wall. Replacing its whole policy with a permanent counter produced excellent direct scores but a severe regression against ordinary opponents. The final adaptive controller therefore embeds two unchanged helper policies in one submission file:

1. **Original fallback:** use the uploaded controller until the public observations establish its distinctive wall. Ordinary attacking, passing, goalkeeping and cover decisions remain in this helper.
2. **Recognized-wall specialist:** require four matching enemy slots, including the goalkeeper, for six consecutive observations. Then defer switching until no live reception contract or selected kick would be interrupted. Reset the specialist, initialize its score from the current observation, and latch it for the rest of that match. Reset clears the latch for the next match.

The specialist uses wide pressure and **7.5-unit/s controlled touches**, below the player's 8-unit/s speed limit, rather than the earlier 10.5-unit/s touches that outran the carrier. It forecasts slot-restoring defenders, cooldowns, clearance impulses and body contacts. An enemy touch is not automatically treated as the end of an attack: a poorly directed clearance can add momentum toward its own goal or leave a collectible rebound. It also conditionally uses four home defenders and a separate outlet when leading by one, or tied after scoring, to draw the target's wall-breakers forward. This is opponent-specific behavior, not a recommendation for permanent deep cover.

The recognizer uses only public IDs, positions, tick numbers and goal coordinates. It does not identify users, read opponent source at runtime, inspect hidden state, change physics or modify SDK interfaces. Only one helper policy runs in steady state. The transition frame executes fallback first and specialist only after safe handoff checks.

## Final adaptive results

| Evaluation | Adaptive | Comparator | Interpretation |
| --- | --- | --- | --- |
| Fresh direct, 128 fixtures | 79W–46D–3L; 283 points; 203–121 goals | Uploaded opponent: 55 points | Clear target-specific advantage |
| Fresh five-style field, 160 fixtures per policy | 91W–30D–39L; 303 points; 177–148 goals | Uploaded baseline: 84W–23D–53L; 275 points; 147–139 goals | +28 paired field points |
| Direct paired points difference per fixture | +1.78125, 95% CI [1.5234375, 2.0625] | Same direct fixtures | Resample complete seed blocks |
| Direct goal difference per fixture | +0.640625, 95% CI [0.53125, 0.7578125] | Same direct fixtures | Positive, below the +1.5 target |
| Field paired points difference per fixture | +0.175, 95% CI [0.09375, 0.25] | Identical common opponents/seeds | 8 independent seed blocks |

The additional 97.5% field interval is [0.08125, 0.25625]. Bootstrap intervals describe this finite opponent panel; they do not measure uncertainty over all league styles or future simulator changes. The field bootstrap uses 20,000 replicates and preserves all opponents, sides and kickoffs within each seed block.

| Common opponent | Adaptive points | Uploaded baseline points | Specialist activations |
| --- | ---: | ---: | ---: |
| Frozen upload | 75 | 47 | 18/32 |
| v10-counter | 60 | 60 | 0/32 |
| v10-press | 59 | 59 | 0/32 |
| v10-compact | 55 | 55 | 0/32 |
| v9.1 | 54 | 54 | 0/32 |

These field columns are separate policies playing the **same common opponents**, not complementary head-to-head scores. The baseline's frozen-upload row is self-play. The adaptive latch never activated in the 128 ordinary-style fixtures, and their points and outcomes were preserved. This limited panel does not establish a universal false-positive rate.

The specialist activated in 65/128 direct matches. One illustrative direct result was **5–1** at seed `3249067131`, candidate side 1, without its own kickoff. This is a selected example from the reported cohort, not separate validation.

## Reliability, runtime and other measured tradeoffs

| Final adaptive source | Direct qualification | Field qualification |
| --- | ---: | ---: |
| Decisions | 307,200 | 384,000 |
| Policy exceptions | 0 | 0 |
| Raw decisions over 20 ms | 0 | 0 |
| Fouls | 0 | 0 |
| Mean decision time | 0.115240 ms | 0.101954 ms |
| Slowest decision | 8.682870 ms | 16.552420 ms |
| Rejected kick requests | 13 | 1 |

The field baseline source also had zero exceptions, raw deadline misses and fouls; its mean was 0.100690 ms and maximum 10.121886 ms. Additional candidate misses were **0 per 1,000 fixtures**, within the +2 limit. **One opposing-side raw miss** occurred in the field panel and remains in the raw records; the zero-miss statement applies to the adaptive and baseline source roles. No fixture was discarded. Candidate clamped values, invalid IDs, missing actions, nonfinite values and dropped debug payloads were all zero. Rejected kick requests are separately reported, not relabeled as policy exceptions or silently removed.

Official intake separately passed five public-seed short matches / 2,000 decisions, zero errors or warnings, zero exceptions or deadline misses, mean **0.114 ms**, maximum **7.002 ms**. Intake exercises the normal custom formation hook. Comparative tournaments use the replay-matched native default rosters and deliberately do not call that hook.

Winning took priority over passing statistics: field pass completion fell from **51.53% to 45.94%**, derived uncollected passes rose **661 to 732**, and turnovers rose **483 to 551**. The increase in goals and points comes from the target-specific counter. The SDK does not expose shot quality or goalkeeper saves in this harness; neither metric is invented.

## Gates and decisions

| Registered check | Final adaptive result | Decision |
| --- | --- | --- |
| At least 75% direct wins | 61.71875% | **FAIL** |
| At least +1.5 mean direct goal difference | +0.640625 | **FAIL** |
| Positive direct paired points 95% lower bound | +1.5234375 | Pass |
| Positive direct goal-difference 95% lower bound | +0.53125 | Pass |
| Positive field paired points 95% lower bound | +0.09375 | Pass |
| Zero policy exceptions | 0 | Pass |
| At most +2 extra raw misses per 1,000 fixtures | 0 | Pass |
| Official intake | Passed | Pass |
| Promote active champion | Not authorized; strong targets missed | **No promotion** |

The [original specialist](../../experiments/champion-hunt/team.py) is retained as evidence, **not the league recommendation**. Its untouched direct qualification achieved **89W–36D–3L**, **303–45 points**, **356–124 goals**, with several 8–0 wins, zero candidate exceptions/misses/fouls and maximum 13.571494 ms. Its 69.53125% win rate still missed the 75% target. One opponent raw miss was retained in that cohort.

The decisive rejection was transfer: across four generic styles / 64 fixtures per policy, the specialist earned **53 points versus 136** for the uploaded file. Its paired difference was −1.296875 points per fixture, 95% CI [−1.828125, −0.90625]. This triggered a new development generation with a public-observation gate. The aggressive 8–0 examples belong to this rejected universal specialist, not the adaptive file.

## Source freeze, development failures and validation provenance

The complete search contains more than 1,500 native attempts, including losing ideas, forfeits and runtime diagnostics. The final independent audit inventories **1,577 JSONL attempts + one recovered forfeited attempt + four timed diagnostic repeats = 1,582 timed native attempts**. Five untimed parity matches, native mechanics probes and official short intake runs are separate. Development results were not mixed into final qualification.

- Generation 1 direct qualification used 32 fresh seeds `3249063101–3249063132`. Its later four-style transfer audit used `3249066101–3249066104`. Both failed variants and results remain frozen.
- Generation 2 used only exposed development seeds `3249061101–3249061108` while fixing handoff logic. The initial V2 wrapper produced **19 fouls in 32 development matches**: a cold start into wall mode skipped score initialization, so the first equalizer failed to initialize opponent-kickoff protection. V3 seeds the current public score immediately after reset. Its 18 synthetic checks, real-helper kickoff-history regression and 32 development matches passed; native development fouls dropped to zero.
- `adaptive-plan.json` intentionally retains its original V2 source pointer. `adaptive-selection.json` records the V3 behavior parent and the final source freeze **before** qualification. The qualification registrations independently pin the final file hash. Display name/version are the only differences between V3 development source and the final file; all function ASTs match. The preregistered schedules and gates were not rewritten after outcomes.
- Generation 2 direct qualification used untouched seeds `3249067101–3249067132`, all four side/kickoff combinations, 128 fixtures. The separate paired field qualification used untouched seeds `3249068101–3249068108`, five styles, all four arrangements, 320 fixtures total. Sources were hashed before and after execution. No qualification tuning or reselection followed.
- An earlier corner-transplant development source lacked `_goal_half`, raised 20 policy exceptions and forfeited at tick 873. The original aborted harness asserted before persisting that result. Its log and recovered native result are retained, and later batches persist early failures. Fixed sources have separate identities.
- Earlier promising parents had **41.615816 ms** and **22.381192 ms** raw misses. Native repetitions and passive thread-CPU/GC diagnostics did not reproduce those stalls. Both occurred in ordinary opening play, not the siege search. Their cause remains unresolved; they are counted and are not dismissed as environmental noise.

Runtime optimization shares immutable candidate-independent coasting forecasts within one siege evaluation and reuses an existing reach table with the same arithmetic. It preserves candidate order and gives each path its own mutable state. Independent review, 111 synthetic full decisions per child, 132 exact reach-table checks, 90 touch cases, 2,160 candidate paths and 22,416 intermediate states passed. Across five untimed native matches, each of three optimized children matched 12,000 original commands exactly (36,000 comparisons total). These parity runs are correctness evidence, not timing qualification. Subsequent timed cohorts observed no candidate misses; they do not prove the earlier unexplained stalls were eliminated.

## What was verified about the engine

Public native experiments used the unmodified compiled engine, ordinary reset/step calls and legal actions. Two opposed-kick cases established team 0 before team 1 kick processing and the per-impulse speed cap. Two opposed-body-contact cases established team 0 before team 1 contact response with drag applied before those contacts; model error was below 1.2e−7 in those cases. Ten boundary examples support body contacts before wall reflection. These are specific tested interactions, not complete reverse-engineering of the private engine.

The specialist's motion and clearance forecasts are simplified models. They are not guarantees of exact future player collisions or goalkeeper behavior. Native goals near the aperture also disproved an overly conservative fixed goal inset. The exact aperture boundary predicate remains unresolved; competing models fit the observed examples. Competitive benefit is established by native match outcomes, not by counting modeled scoring proposals. Native own-goal events support the pressure mechanism, but no claim is made that a single forecast caused every own goal.

## Reproduce and inspect

The [evidence archive](evidence.zip) contains original executed harnesses, builders, frozen trial sources, raw JSONL, logs, registrations, diagnostic profiles, native probes and rejection results. `MANIFEST.json` inside it records every payload SHA-256. Paths and original registrations are retained verbatim; many historical batch scripts refer to the original workspace layout. The portable CLI below avoids that dependency for a current matchup.

Install or point `PYTHONPATH` to the **complete official student SDK**, including its native engine. The repository's Python-only SDK tree is insufficient by itself. From the repository root:

```bash
PYTHONPATH=/path/to/complete/student-sdk \
python tools/benchmarks/champion_hunt_match.py \
  --seed 3249067131 --side 1 --no-own-kickoff \
  --output reproduced-7131.json
```

Defaults are the final adaptive file against the frozen uploaded file. Override `--candidate` or `--opponent` for the specialist or another source. This calls the unchanged [native default-roster driver](../../tools/benchmarks/default_roster.py), preserves the official decision/failure loop, and records raw timings, source hashes and initial roster. It refuses to overwrite earlier output. Engine `0.1.0`, config hash `372990895c7eca2a`, 2,400 ticks, 20 ms deadline, one worker. Wall-clock timings can vary across machines; keep every new raw miss.

Readable key records are in [results/](results/). The final independent [audit](results/final-audit.md) recomputes the aggregates and field interval from the raw records. Archive integrity and protected source hashes are recorded in `evidence-manifest.json`.

| Frozen file | SHA-256 |
| --- | --- |
| Recommended adaptive | `27b3ef88ddede6267fd0583278b821c2abcd27de38772dfe9051307778e880ce` |
| Specialist | `05d9ce27b4e6f54db44a3e5c8b6a929e0dbce0dcf00b5a0b69f9e6ebf6681196` |
| Uploaded baseline | `7708f5d3b10202092f1fce73abfc61a5d7a61d91326d95d69cec872d4c7ba758` |

Study execution dates in original records are UTC, 25 October 2026. Packaging and publication occur afterward; no new validation cohort is implied.
