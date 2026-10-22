# Keeper possession experiment: development results

**No challenger advances. The active Elite Replay Cutback champion is unchanged.**

Sources were frozen in commit `d7c3bc1` before the screen. These are development results from two previously unused seeds against six fixed opponents, both field assignments and kickoff arrangements: **48 matched configurations per controller, 192 full native matches**. One serial timed worker used stock engine 0.1.0, course config `372990895c7eca2a`, 2,400 ticks and the official 20 ms deadline. No policy, physics, SDK, timer, GC or process settings were modified during evaluation.

| Controller | Points | W–D–L | Goals scored / conceded | Pass completion | Turnovers | Mean ms | Max ms | Raw deadline misses | Exceptions |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| active | 98 | 29–11–8 | 117 / 46 | 54.26% | 240 | 0.220 | 25.428 | 1 | 0 |
| backpass | 93 | 28–9–11 | 115 / 53 | 57.61% | 247 | 0.228 | 7.750 | 0 | 0 |
| wall-counter | 98 | 29–11–8 | 117 / 46 | 54.26% | 240 | 0.220 | 10.382 | 0 | 0 |
| combined | 93 | 28–9–11 | 115 / 53 | 57.61% | 247 | 0.226 | 12.901 | 0 | 0 |

Back passes and the combined version produced **45 actual native kicks and 38 named-keeper collections**, including 16 observations of immediate controlled possession. Four attempts met another teammate first; three were superseded by another back-pass plan. Those categories are not seven confirmed opponent turnovers. Immediate control is distinct from a useful contact or immediate onward kick. Overall possession rose from 47.17% to 49.47%, but match points fell by five and goals conceded rose by seven. More passes and possession did not establish a winning improvement.

The wall-counter-only version executed **zero new native launches** and had identical scores, passes and turnover totals to the champion in this screen. The geometry/physics regression demonstrates a reachable post-wall collection, but there is no evidence here of a useful competitive execution. Its runtime measurements cannot establish the cost of actually taking the new wall route. The combined version likewise executed no new wall counters. Do not describe this as an effective keeper wall-counter tactic.

Per-opponent back-pass point changes (eight configurations per opponent): counter +3, press −6, Elite Cutback −2, and no change against v10, compact defence or quick wall. These small development groups do not establish a general matchup advantage.

## Selection and reliability

The preregistered development rule required both more raw points than active and at least one actual new receiver contact. No challenger qualified. **The twelve fresh validation seeds were not used**, the 384-configuration validation tournament was not run, and no challenger passed the promotion gates. The two-seed bootstrap intervals in the machine-readable comparisons are exploratory development outputs; they are not sufficient evidence for statistical superiority or league-wide performance.

All four sources passed the official five-public-seed, 2,000-decision intake with zero exceptions, deadline misses, missing actions or non-finite values. All challengers had zero raw decision deadline misses in the full development screen. The champion had one raw 25.428 ms miss; the passive wrapper measured 25.432 ms thread CPU with no observed GC overlap. One identical fixture repeat completed without a miss. Its raw timeout remains counted. This isolated sample does not identify the cause, prove an environmental issue, or certify future reliability. Average back-pass cost was approximately 3.6% above the champion in this screen.

The successful reception fixture was replayed unchanged: same final score, zero exceptions or deadline misses, with the native kick and keeper contact trace archived. A separate diagnostic compared the fully disabled challenger with the champion on all 2,400 native observations of a full match: actions and debug data were exactly equal. The shadow comparison ran outside the official decision timer and is excluded from tournament runtime metrics. A replay capture serialization error was corrected before the successful replay; no policy source or tournament result changed.

## Code and evidence

- `experiments/keeper-backpass/team.py`: back pass only.
- `experiments/keeper-wall-counter/team.py`: keeper wall counter only.
- `experiments/keeper-support/team.py`: combined.
- `registration.json`, `development-protocol.json`: frozen sources, seeds, selection and gates.
- `development-decision.json`, `*-vs-active.json`: raw comparisons and the no-advancement decision.
- `tests/fixtures/keeper-support-native-evidence.zip`: raw/diagnostic records and per-file SHA-256 manifest.
- `tests/fixtures/keeper-support-native-reproduction.json`: public observation and action trace.
- `evidence.json`: archive SHA-256, verification and check totals.

The 109 regressions passed against each independently enabled source. The active `my-team/team.py` remains SHA-256 `553bcd85a537d57a43c16e4498fab402fbbabb940e15cb8c5aa110d4c6fa9a5e`; no champion archive was changed.

## Reproduce

Install the shipped Linux native engine in the student SDK, then run:

```sh
python -m unittest discover -s tests -q
python tools/benchmarks/run_keeper_support.py --protocol docs/keeper-support/development-protocol.json --out /path/to/new-run
python tools/benchmarks/analyze_keeper_support.py --run /path/to/new-run --out /path/to/new-analysis
python tools/benchmarks/reproduce_keeper_support.py --run /path/to/new-run --out /path/to/new-reproduction.json
```

A useful next hypothesis would require an open forward outlet after the keeper receives, and receiver positioning that creates a usable wall route. Neither has been demonstrated by this experiment; forcing more backward passes or blind wall clearances is unsupported.
