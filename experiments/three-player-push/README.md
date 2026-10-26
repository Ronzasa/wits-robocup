# Three-player wall pressure — implemented, not promoted

This experiment implements the requested **three full-strength pushers, one ball carrier/shooter and one goalkeeper**. The branch submission at `my-team/team.py` remains the current TITAN Adaptive Counter; `main` is unchanged. The requested experimental implementation is [team.py](team.py).

**Recommendation: do not replace the current submission with this version.** Pushing physically displaces defenders, but the development results do not show that committing three players improves winning. No independent qualification or champion promotion was performed.

## Behavior

- Recognize four opponents clustered within three units of their goal and within nine units of its centre for six consecutive ticks. The detector uses public positions, without requiring the old specific player-ID/slot arrangement.
- Preserve the current safe handoff: defer for live receiving contracts and selected kicks; bootstrap the specialist with the public score.
- During the recognized-wall siege, assign the three spare outfield players to three distinct defenders on the carrier's side. Approach diagonally, then apply unit-length movement toward a point beyond the defender, with a sideways component. This is maximum **legal movement**, not extra strength or a change to collision physics.
- The fourth outfield player retains the existing ball-chasing and controlled-touch logic. Check five goal targets using the inherited shot/contact forecasts; reject a direct shot when the inherited early-body forecast predicts a teammate obstruction. Preserve the existing corner/rebound shot and controlled-touch fallbacks.
- Keep the inherited goalkeeper movement and clearance action. Pushers do not kick. Stop the pushing role when the wall condition disappears; the inherited specialist's ordinary and conditional bait behavior then applies. As in the existing adaptive controller, the specialist selection itself remains latched until reset.

These are local changes to the experimental wall mode. The original fallback helper, general shooting functions, movement function and opening policy are AST-identical to the frozen current team. All runtime code is in the single 239,703-byte `team.py`; it imports only `math` and the official `soccer` interface and defines one SDK controller subclass.

## Native development results

Each row has 16 full 2,400-tick fixtures: four seeds, both field assignments and both kickoff arrangements. The same packed-wall fixtures were used for each common-opponent policy. All are **exposed development**, not independent qualification or a live league evaluation.

| Test | W–D–L | Points | Goals |
| --- | --- | ---: | ---: |
| Three pushers vs current adaptive team | 2–7–7 | 13 vs opponent's 28 | 30–36 |
| Three pushers vs dedicated packed wall | 15–1–0 | 46 | 54–0 |
| Current adaptive team vs same packed wall | 2–14–0 | 20 | 2–0 |
| Same new detection/shots, **no pushers**, vs packed wall | 16–0–0 | 48 | 83–0 |

The direct paired points-difference interval is **[−2.25, +0.375] points per fixture**, using complete seed-block bootstrap resampling. Its lower bound fails the positive-points gate; the observed point score also regresses. Four independent seeds provide limited precision, and the interval does not establish a statistically significant negative effect. The development gate nevertheless fails, so untouched qualification seeds were not consumed.

The no-pusher ablation changes exactly one slice from `[:3]` to `[:0]`, retaining the broader detector, new gap-shot evaluation and default deeper targets for spare players. It scored **29 more goals and two more points** against the same wall. Therefore the full bundle's advantage over the old controller cannot be credited to pushing. The ablation was not tested directly against the current champion or a broad opponent panel; its 83–0 result does not justify promoting it either.

The packed-wall opponent is an independent development agent with a centred goalkeeper, four other goalmouth defenders and legal forward clearances. It is not Olwethu Phiri's controller, a recovered opponent policy or a reproduction of the complete match in the screenshot. A final screenshot cannot establish that opponent's full decision policy.

## Physical mechanism and reliability

Four separate untimed native movement probes compare restoring defenders with and without sustained attackers in open space and at the goal wall. No state injection, physics changes or private engine access is used. Maximum defender displacement **relative to the paired control run** was approximately **1.52 units in open space** and **4.85 units at the wall**. These are maximum observed coordinate differences, not persistent open shooting lanes, guaranteed push force or scoring probabilities. Raw trajectories are in [contact-probe.json](contact-probe.json).

Across the 64 timed development matches, all source and opposing roles had zero policy exceptions and raw deadline misses. The three-pusher source itself played 32 of those matches, with **zero exceptions, raw deadline misses, fouls or rejected kick requests**. Its slowest decision was **18.482399 ms**, below the official 20 ms deadline but with limited observed peak headroom. Raw counts remain in each match record; no failures or slow fixtures were removed.

Official intake separately passed all five public seeds / 2,000 decisions: mean **0.102 ms**, slowest **3.225 ms**, zero exceptions, deadline misses, missing actions or nonfinite values. Intake uses the normal formation hook. Comparative matches use native default rosters, consistent with the earlier replay-matched benchmark.

Five focused regression tests pass: three full movement roles and a separate unchanged goalkeeper, only the carrier kicking, six-tick broad recognition/reset, discontinuous-tick confirmation reset, and frozen fallback/general-method preservation. An initial test incorrectly assumed the goalkeeper must always move backwards; the inherited target can require a small forward correction. The test was corrected to compare the goalkeeper action directly against the frozen controller. No controller change was made to satisfy that assertion.

## Reproduce

Base commit: `149a5470756b6deb9d0e4ba7507c963903a77eed` on `sandbox-champion-hunt`. Experimental branch: `titan-three-player-push`.

Provide the complete official native SDK through `PYTHONPATH` or an installed wheel. From the repository root:

```bash
PYTHONPATH=/path/to/complete/student-sdk python tests/three-player-push/test_roles.py
PYTHONPATH=/path/to/complete/student-sdk python tests/three-player-push/probe_contact.py --out new-contact-probe.json
```

`tests/three-player-push/build.py` reproduces the requested source from the frozen current submission. For native batches, copy one development registration to a **new directory** and run:

```bash
PYTHONPATH=/path/to/complete/student-sdk python tests/three-player-push/run_native.py --registration NEW_DIRECTORY/registration.json
```

The runner refuses to overwrite raw match output, verifies source hashes, uses the unchanged official decision/failure loop and records every native result. `run_native_v1.py` is the exact harness used for the first direct comparison; the later version additionally reads controller mode fields **after** the match through its own bound-loader wrapper. It does not wrap policy decisions or change the SDK loader. Engine `0.1.0`, config hash `372990895c7eca2a`, 20 ms, 2,400 ticks, one worker. Timings can differ on another machine.

Raw results, registrations, summaries, intake and regression output are retained here. [evidence.json](evidence.json) records file hashes and the rejection decision. Direct seeds: `3249101101–3249101104`; common-opponent seeds: `3249102101–3249102104`. No candidate was tuned after these results, and no qualification data was used to select a winner.

- Requested source SHA-256: `70cbd7622fbe18955cfd002b40430ebb1c3327313cac82663c463d2ef677aa7e`.
- Frozen current submission SHA-256: `27b3ef88ddede6267fd0583278b821c2abcd27de38772dfe9051307778e880ce`.

The useful follow-up is to investigate broader wall recognition and shot opportunities independently. These measurements give no reason to force all three spare players into contact as a general upgrade.
