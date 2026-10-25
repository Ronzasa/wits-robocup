# Replay evaluation audit — no challenger promoted

## Decision

**The experiments do not establish a reliable league-points upgrade over uploaded team (8).py. Keep the benchmark frozen; do not promote these challengers.** The final corrected-roster validation yields 287 points for the selected variant and 286 for team (8), while the selected variant wins fewer games. The 95% confidence interval includes zero. No controller source, active champion or archived champion was changed during this audit.

## Evaluation error found and corrected

The supplied replay bodies use the engine's default initial roster. All five ten-player initial rosters are reproduced by a normal public `SoccerEnv.reset`, with maximum coordinate errors no greater than 1.8e-6 pitch units. The earlier local `soccer.play_match` driver calls each controller's optional `initial_formation()` hook. For the uploaded team (8), that produces a starting-player displacement of up to **31.182688 units** relative to the captured school replay. This difference affects kickoff and goal-reset states.

The earlier native games were valid SDK games, but they did not establish performance in the captured course setup. I should have checked this parity before interpreting their results. Engine version and configuration hash alone did not catch the formation difference.

The corrected driver uses only public SDK operations, default native rosters, 2,400 ticks, and the unmodified 20 ms native deadline and failure policy. It never calls `set_formation` or changes game physics, hidden state, controller interfaces or opponent source. Four external replay-roster regression cases now pin this setup; all pass. A portable driver reproduces the score and physical statistics of a previously scheduled corrected fixture.

An action-replay check reproduces one complete captured game to within 1e-5 state error. Other recorded action streams drift after 494–2,353 ticks; two final scores differ. Their complete replay equivalence is not established. The initial-roster result is direct and holds for all five captures.

## Fixed studies and all outcomes

1. **Original SDK/custom-formation study:** six frozen versions ×32 exposed development fixtures =192 full matches. The no-work-caps variant wins selection with 67 points versus full-v2's 57. Its untouched five-style validation is 312–293 points, but the paired 95% interval is [−0.1625,+0.3875]; it fails.
2. **Default-roster confirmation of that same fixed selection:** 160 fixtures per controller =320 full matches, new seeds, five styles. It scores **293–311** points; interval [−0.26875,+0.05000]. It fails. No alternative source is selected using this validation.
3. **Corrected-roster development:** eight preregistered sources ×32 exposed development fixtures =256 full matches. Selection uses development results only; a single winner then receives untouched validation.

Total in this investigation: **1,408 scheduled full native matches**, plus public intake checks, separate functional diagnostics and driver regression checks. All scheduled raw results remain in the evidence. None are replaced by repeats.

### Corrected development, head-to-head against unchanged team (8)

| Frozen source | Points | Opponent points | W–D–L | Raw own misses |
|---|---:|---:|---|---:|
| earlier-passing | 40 | 52 | 12–4–16 | 0 |
| full-v2 | 52 | 43 | 17–1–14 | 0 |
| no-recovery | 35 | 56 | 10–5–17 | 0 |
| no-keeper-safety | 52 | 43 | 17–1–14 | 0 |
| no-retention | 63 | 33 | 21–0–11 | 0 |
| no-work-caps | 54 | 39 | 17–3–12 | 0 |
| edge-contact | 54 | 39 | 17–3–12 | 0 |
| team8-unlocked | 36 | 57 | 11–3–18 | 0 |

The selected variant, `no-retention`, disables only the added `_retain_touch` self-recapture layer. Existing controlled touches, named pass receivers and short teammate handoffs remain present. The recovery, keeper-clearance and bounded-verification additions remain present. Removing the lead lock is separately controlled: `team8-unlocked` is the unchanged uploaded file with only `LOCK_LEAD=0`.

That control scores **36–57 points** against the original locked version. Disabling the all-player goal wall has a competitive cost in this sample. The requested `LOCK_LEAD=0` setting was not silently reversed.

### Final untouched corrected-roster validation

All five styles use all four pitch/kickoff combinations for each of eight unseen seeds, 2938064701–2938064708. The source is fixed before validation. There is no tuning or second selection using these outcomes.

| Metric | Selected no-self-recapture variant | Uploaded team (8) |
|---|---:|---:|
| Full matches | 160 | 160 |
| Wins–draws–losses | 81–44–35 | 86–28–46 |
| Points | 287 | 286 |
| Goals for–against | 243–135 | 158–130 |
| Mean decision, ms | 0.1749 | 0.1168 |
| Maximum decision, ms | 9.918 | 11.111 |
| Policy exceptions | 0 | 0 |
| Raw deadline misses | 0 | 0 |

The paired difference is **+0.00625 points per fixture**, with a seed-block bootstrap 95% interval of **[−0.24375,+0.22500]**. The positive confidence-lower-bound gate fails. The candidate has 5 fewer wins and 16 more draws. More goals and fewer losses do not provide a useful points advantage here.

| Common opponent | Selected variant points | Team (8) points |
|---|---:|---:|
| team8 | 40 | 46 |
| v10-counter | 63 | 64 |
| v10-press | 54 | 62 |
| v10-compact | 69 | 55 |
| v9.1 | 61 | 59 |

These are paired performances against common opponents, not complementary scores between the two benchmarked controllers. The `team8` row includes baseline self-play. The field consists of frozen v10 counter/press/compact styles, v9.1 and team (8); these are not the private source policies of the top two real league teams.

### Raw timing history stays counted

Zero misses in the final corrected cohort is not a claim that this source has never exceeded the deadline. The same no-self-recapture variant previously records one **27.135 ms** miss in the original custom-formation development cohort. Original full-v2 also retains its earlier **24.948 ms** miss from the preceding 64-game test. A roster mismatch does not establish the cause of either timing spike, and neither miss is erased or excused.

## Functional diagnoses

- A same-state diagnostic at tick 1,612 finds full-v2 rejecting a modeled receiving pass when its selected-pass witness budget is insufficient. The uncapped policy returns a named pass. This explains a concrete decision difference; it does not prove the uncapped variant is stronger. Its independent validations fail.
- A second diagnostic uses two independent policy states observing identical native inputs until their first command difference. At ticks 572–576 the movement/kick commands agree; full-v2 establishes a self-recapture plan at tick 576. At tick 577 both still choose player 3 as chaser, but its movement changes from approximately (0.984,−0.178) to (0.998,−0.068) under the added plan. This demonstrates the extra pursuit behavior without claiming that a particular frame caused the eventual loss.
- The edge-contact experiment changes six internal kick buffers from 0.18 to 0.03 while preserving the true 2.2 engine range. It does not win development selection and is not promoted.

## What changes in the workflow

Use the replay-matched native driver for this course setup. Select future challengers against a representative opponent field during development, not only direct matches against team (8). Keep that development separate from untouched validation. Judge improvements by paired points and reliability; goals, pass completion and feature activation are supporting metrics. A failed validation remains a failure.

The captured running league table is also not ordered monotonically by its displayed current raw points: rank 1 has 2,679 points while rank 2 has 2,806 in one snapshot. The HAR does not establish whether that is provisional or a separate ranking rule. These local proxy-field points must not be presented as a guaranteed division change.

## Reproduce and inspect

With a complete compiled course SDK installed or supplied on `PYTHONPATH`, run:

```sh
python tools/benchmarks/default_roster.py --team /path/to/team.py --opponent /path/to/opponent.py --seed 1000 --side 0 --candidate-kickoff --out fresh-match.json
python -m unittest discover -s tests -p test_default_roster_benchmark.py -v
```

The roster regression test deliberately supplies controllers with a different valid custom formation, then verifies that all ten starting positions still match the four external school replay fixtures.

- [Corrected development](corrected-development.json), [corrected validation](corrected-validation.json), [all corrected scores](corrected-scores.csv).
- [Formation comparison](formation-parity.json), [five-roster check](all-roster-parity.json), [action replay parity and drift](replay-parity.json).
- [Driver regression result](driver-tests.json), [portable driver reproduction](portable-driver-verification.json).
- [Evidence ZIP](evidence.zip): frozen source files, opponents, preregistrations, raw scheduled records, executed harnesses and all diagnostics. No raw HAR, cookies or authorization headers are included.

No new champion or release is recommended by these results. `main`, active `my-team/team.py`, archived champions and the original uploaded team (8) remain unchanged.
