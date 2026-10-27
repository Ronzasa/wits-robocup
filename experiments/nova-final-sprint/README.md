# NOVA final sprint — submission selection

**Selected file: `baseline`.** Did not strictly improve original NOVA in broader development; retain untouched NOVA.

`team.py` contains the exact selected source, SHA256 `b10d96375fa0723db8d8966d099f96f340440f569b95f6751cfb9c66406be484`.
`original/team.py` remains the untouched NOVA fallback, SHA256
`b10d96375fa0723db8d8966d099f96f340440f569b95f6751cfb9c66406be484`.
Prepared: 2026-10-27T23:26:07+02:00 (Africa/Johannesburg). `main`, active `my-team/team.py` and
archived champions remain unchanged. This experimental submission selection does
not automatically promote the repository champion or update the school upload.

## Change under test

NOVA normally forces a shot against a packed wall after the ball reaches x>30,
even when its own shot model gives it a poor chance. `patient-wall` changes only
`PB_X` from30 to99, allowing the ordinary shot/pass/dribble value comparison to
decide those touches. High-confidence shots remain eligible. Goalkeeper,
defensive cover, receiver planning, movement, contact and ball forecasts retain
their original algorithms. New variants surface exceptions through SDK accounting;
opportunity counters are diagnostic additions. Source metadata identifies each
variant; tactical methods do not read the version.

Four independent single-constant variants were frozen before development:
patient-wall (`PB_X=99`), responsive-wall (`WALL_D=1`), rebound-depth
(`PB_FX=43`) and wall-pressure (`PB_FX=48`). No features were combined. The first
screen selected only the highest-point eligible variant; the others were rejected.

## Initial exposed development: two fresh seeds, four styles, 64 fixtures per source

| Controller | Points | W–D–L | Goals | SDK errors | Raw misses | Mean / max ms |
|---|---:|---:|---:|---:|---:|---:|
| Original NOVA | 128 | 36–20–8 | 159–8 | 0 | 0 | 0.071 / 6.212 |
| MONSTER16 | 92 | 16–44–4 | 21–8 | 0 | 0 | 0.041 / 4.696 |
| patient-wall | 132 | 36–24–4 | 159–4 | 0 | 0 | 0.112 / 11.895 |
| responsive-wall | 125 | 36–17–11 | 159–11 | 0 | 0 | 0.072 / 5.945 |
| rebound-depth | 129 | 36–21–7 | 159–7 | 0 | 0 | 0.070 / 5.301 |
| wall-pressure | 127 | 37–16–11 | 160–11 | 0 | 0 | 0.076 / 17.832 |

## Broader exposed development: two further fresh seeds, eight styles, 128 fixtures per source

| Controller | Points | W–D–L | Goals | SDK errors | Raw misses | Mean / max ms |
|---|---:|---:|---:|---:|---:|---:|
| Original NOVA | 328 | 105–13–10 | 466–15 | 0 | 1 | 0.070 / 20.402 |
| MONSTER16 | 226 | 54–64–10 | 74–17 | 0 | 0 | 0.038 / 6.490 |
| patient-wall | 328 | 104–16–8 | 440–13 | 0 | 0 | 0.102 / 8.021 |

Qualification was **not started** because the chosen variant did not clear broader development. Its preregistered qualification seeds remain unused. Against MONSTER in broader development, patient play drew all16fixtures; original NOVA had1win,13draws and2losses. Both earned16points. Avoiding losses also removed the only win, so this did not solve the draw-conversion problem.

### Bounded timing diagnosis

baseline: 3 exact-fixture repeats, 0 raw misses, 0 SDK errors, maximum 2.267ms. The original miss stays counted; these repeats do not establish an environmental cause.

## Reliability and interpretation

- Official engine0.1.0, config372990895c7eca2a, full2,400ticks and unchanged20ms
  SDK enforcement. One timed native worker at a time; a fresh process per fixture.
- Original NOVA's authored `gc.freeze()` is preserved identically in variants;
  it is contained between fixtures. No new GC, clock, affinity or SDK changes.
- Both field assignments and kickoffs, plus default/controller formation profiles.
  Profiles can coincide physically; they are not independent seed samples.
- Frozen original NOVA contains an internal fallback exception handler. Its SDK
  error count does not prove zero swallowed exceptions. New variants call the
  policy directly so their exceptions are counted by the official SDK.
- Raw misses from either side are retained. Clean diagnostic reruns, if any,
  never erase a miss or prove its cause was environmental.
- Two-seed development intervals cannot establish a reliable upgrade. Only one
  frozen candidate may qualify, without tuning, early stopping or optional
  extensions. Incomplete evaluation or any failed gate selects original NOVA.
- Wall counters count opportunities, not goals or causal conversions. The first
  screen's points gain came from fewer losses; scoring was unchanged.
- This local panel does not contain the actual controllers of every school
  league leader and does not establish a Division1 ranking. Recent league stats
  identify a draw-heavy weakness but cannot prove an individual tactical cause.

## Evidence and reproduction

`evidence.zip` contains all frozen variants and controls, opponent snapshots,
registrations, raw native rows, summaries, integrity audits, regression tests,
official intakes and reproduction tools. Original registrations preserve their
workspace paths as provenance. The reproducer remaps only file locations.

Extract the archive and use the official course SDK:

```sh
python audit.py phase1 phase2
python reproduce.py phase2 --out new-development-reproduction
```

Run only completed panels, use a new output folder, and run one timed worker at
a time. The original evidence is never overwritten. Only the selected `team.py`
is uploaded to the school; auxiliary Python files are research tools.
