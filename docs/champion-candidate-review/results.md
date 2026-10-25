# Uploaded champion candidate review

## Decision

**Keep the uploaded file frozen. Neither tested change demonstrates an upgrade.**
There are concrete action conflicts to address, but protecting those actions
did not produce more points in this study. No champion is promoted or replaced.

The upload is the earlier `replay-finishing-handoffs-v1` implementation with
lead protection re-enabled, a new two-goal trailing wall, and a wall-breaking
postprocessor. Its name does not establish qualification or championship
performance. The frozen upload's SHA256 is
`7708f5d3b10202092f1fce73abfc61a5d7a61d91326d95d69cec872d4c7ba758`.

## Findings

1. **Two goals behind disables normal attacking play.** `act()` immediately
   returns `_lock_wall()` whenever the deficit reaches two, regardless of time
   remaining. Every player goes to the home goal mouth and clears forward;
   normal receivers, support and attacking decisions stop. This can limit
   further concessions, but leaves no planned comeback attack. In a separate
   native diagnostic against v9.1, this branch occupies 871 of 2,400 ticks.
   That diagnostic does not prove that continuing normal play would win.
2. **Wall breaking overwrites already coordinated actions.** It runs after
   `_act_normal()`, selects pushers using proximity to the ball, and replaces
   their complete actions. It does not exempt the named receiver, designated
   cover player, or players with existing kick commands. A native diagnostic
   against team (8), seed 3104278101, candidate side 0 without kickoff, records
   82 ticks changing an active receiver's action, 1,714 changing the cover
   player's action, and 8 cancelled kick commands. These counts can overlap;
   they are action changes, not a count of lost goals or possessions.
3. **Its extra shot bypasses the usual physics checks.** A static gap and
   clear line permit a full-power kick without checking current ball momentum,
   drag, subsequent contacts or goalkeeper arrival. A focused public-input
   regression uses a ball travelling at -30 units/s: a +22 impulse still leaves
   it travelling backwards. The geometric-gap check nevertheless requests the
   shot. The guarded experiment reuses `_shot_option()` and its existing
   momentum/contact, goal-plane and defender checks. Those forecasts remain
   models, not guarantees about future contacts.
4. **Lead protection applies throughout the match.** The SDK documents
   `time_remaining` as a fraction in [0,1]. `LOCK_TIME=1.0` means the entire
   match, so a one-goal lead triggers the wall immediately. This was preserved
   in all three files; previous evidence did not support blindly removing it.

Six focused regression tests reproduce the original conflicts and verify the
isolated changes, including preservation of lead protection. Their observations
are synthetic public-input fixtures using native field dimensions. They are
separate from the native match evidence and do not establish points improvement.

The two diagnostic fixtures were selected to explain observed behavior changes.
They are untimed functional reruns, not qualification fixtures, and never replace
scheduled results. Their instrumented controller inspects its own before/after
actions; the native engine and opponent code remain unchanged.

## Fixed native comparison

Three frozen sources, tested independently:

- Uploaded file, unchanged.
- Only disable the trailing wall (`TRAIL_WALL=0`).
- Only guard wall-break action arbitration and reuse the existing shot check.

Each plays 80 full matches: five common opponent styles × four newly chosen
seeds (3104278101–3104278104) × both pitch assignments × both kickoff
arrangements. Opponents are unchanged team (8), v10-counter, v10-press,
v10-compact and v9.1. The order is randomized, with one worker. All 240 scheduled
matches are retained. There is no outcome-based stopping, repeated result
replacement, feature combination or qualification selection.

The driver uses the replay-matched public native defaults, 2,400 ticks, engine
0.1.0, configuration `372990895c7eca2a`, and the unmodified 20 ms deadline and
failure handling. The official five-public-seed intake is a separate check
using its normal SDK formation hook; all three pass with zero exceptions or
misses. No simulator configuration, physics, opponent source or SDK file changed.

| Metric | Upload | No trailing wall | Guarded wall break |
|---|---:|---:|---:|
| Full matches | 80 | 80 | 80 |
| Wins–draws–losses | 50–6–24 | 50–6–24 | 49–6–25 |
| Points | 156 | 156 | 153 |
| Goals for–against | 70–52 | 73–54 | 68–52 |
| Pass completion | 50.18% | 51.17% | 62.24% |
| Shots | 329 | 338 | 545 |
| Turnovers | 240 | 240 | 239 |
| Mean decision, ms | 0.1016 | 0.1101 | 0.1166 |
| Maximum decision, ms | 9.815 | 14.755 | 19.906 |
| Policy exceptions | 0 | 0 | 0 |
| Raw deadline misses | 0 | 0 | 0 |

No-trailing-wall changes zero individual fixture points outcomes. Its paired
points difference is 0, with a sample seed-block bootstrap interval [0,0].
This is not proof of equivalence: there are only four independent seed blocks
and the changed behavior is conditional on falling two goals behind.

Guarded wall breaking changes one win to a loss. Its paired points difference
is -0.0375 per fixture, bootstrap 95% interval [-0.1125,0]. It does not establish
a points upgrade. The interval also does not establish a general deterioration.
It makes many more completed passes and shots while scoring fewer goals and
points. Those supporting statistics are insufficient grounds for adoption.

Both changes have zero additional raw misses in this cohort. The guarded
version's 19.906 ms maximum leaves little observed headroom under 20 ms;
its cause was not diagnosed and must not be excused as environmental noise.
These limited development results do not prove universal deadline compliance.

The opponent controllers recorded four raw deadline misses: one against the
upload, two against no-trailing-wall, and one against guarded-wall-break. They
remain counted in the original fixtures; no timing correction or clean rerun
replaces them. The sole paired points change occurs in a different fixture,
with no timeout on either side. Opponents also recorded six rejected-kick
validation counts; the three reviewed sources recorded none. All sides have
zero policy exceptions. The cause of the timing spikes is unresolved.

| Common opponent | Upload points | No trailing wall | Guarded wall break |
|---|---:|---:|---:|
| Uploaded team (8) | 18 | 18 | 15 |
| v10-counter | 36 | 36 | 36 |
| v10-press | 30 | 30 | 30 |
| v10-compact | 38 | 38 | 38 |
| v9.1 | 34 | 34 | 34 |

The upload itself wins 6 and loses 10 against team (8) in its 16 direct games,
18–30 points. That sample does not establish that this upload beats team (8).
The common opponent field is a local proxy; it is not the private source of
the top-ranked school teams. No ranking or division improvement is established.

## Implication for further work

The useful engineering target is a coherent wall-breaking plan: opening a lane
and actually exploiting it must be evaluated together. Appending uncoordinated
pushes after pass selection is a reproducible conflict. However, protecting
every normal role can also remove the pressure that creates an opening. The
current experiment does not resolve that tradeoff or justify shipping its fix.

Removing the trailing wall creates more attacking attempts but earned no extra
points here. Treat it as a comeback policy hypothesis, not a demonstrated upgrade.
Keep the existing lead lock as a separately tested choice. Neither change has
earned an independent qualification run or promotion from this development study.

## Evidence

- [Frozen sources](../../experiments/champion-candidate-review/README.md).
- [Preregistered comparison](registration.json), [full summary](summary.json),
  [all 240 scores](scores.csv), [paired points outcome changes](paired-score-changes.json).
- [Native diagnostic observations](native-diagnostic.json),
  [regression check record](regression-tests.json).
- [Evidence ZIP](evidence.zip) and [payload hashes](evidence-manifest.json):
  frozen sources and opponents, raw native records, intake reports, executed
  harnesses, original preparation script and functional diagnostics. The
  archived scripts retain their executed absolute paths; remap paths into a
  separate output directory to repeat the batch without overwriting evidence.

With a complete compiled SDK installed or supplied on `PYTHONPATH`:

```sh
python -m unittest discover -s tests -p test_candidate_wall_arbitration.py -v
python tools/benchmarks/default_roster.py --team experiments/champion-candidate-review/uploaded/team.py --opponent /path/to/opponent.py --seed 3104278101 --side 0 --no-candidate-kickoff --out fresh-match.json
```

`main`, active `my-team/team.py`, archived champions, the previous experimental
controller and the attachment remain unchanged. All review changes are isolated
on the existing feature branch; none is an approved submission replacement.
