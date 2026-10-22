# Elite Replay Cutback activation

The project owner selected Elite Replay Cutback as the new champion and requested
that it replace the active `my-team/team.py` on `main`.

The active file and [champion archive](../champions/elite-cutback/team.py) are exact
copies of `experiments/elite-scout-cutback/team.py` from
[`elite-replay-tactics` commit b4c2495](https://github.com/Ronzasa/wits-robocup/blob/b4c24958757b1c2e93b8857b7166367f94051223/experiments/elite-scout-cutback/team.py).
There are no tactical or metadata edits to the tested file.

SHA-256: `553bcd85a537d57a43c16e4498fab402fbbabb940e15cb8c5aa110d4c6fa9a5e`.

The previous [v10.0 champion](../champions/v10.0/team.py) is preserved byte for byte:
SHA-256 `5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6`.
Existing v9.0/v9.1 champions, experimental sources, SDK, engine and competition
configuration remain unchanged.

## Selection evidence

The frozen fresh comparison covered 768 matched configurations per controller,
12 opponents, 16 unused seeds, both field assignments and both kickoff arrangements.

| Controller | Points | Wins | Goals scored–conceded | Raw deadline misses |
|---|---:|---:|---:|---:|
| TITAN-X Trap | 1,374 | 401 | 1,527–810 | 5 |
| v10.0 | 1,381 | 404 | 1,527–805 | 8 |
| Elite Replay Cutback | 1,444 | 430 | 1,688–845 | 6 |

The cutback controller passed the registered reliability gates, with zero
exceptions and a mean decision time of 0.239 ms. The paired 95% confidence intervals
included zero: `[-0.054688, 0.252604]` points per match against Trap and
`[-0.069010, 0.247396]` against v10.0. The original automatic promotion decision
therefore retained the baselines. This activation records the owner's subsequent
explicit choice; it does not change that statistical result or the frozen evidence.

[Complete experiment and evidence](https://github.com/Ronzasa/wits-robocup/blob/b4c24958757b1c2e93b8857b7166367f94051223/docs/elite-scout/validation.md).

## Activation checks

All 95 regressions on `main` passed with the new active file. The official SDK
validator passed all five public seeds at 400 ticks each: 2,000 decisions, zero
exceptions, zero deadline misses, no missing player actions and no non-finite
values. Mean decision time was 0.200 ms and the slowest was 5.166 ms, under the
unchanged 20 ms deadline. Folder inspection also passed.

[Machine-readable intake results](elite-cutback-intake.json).

## Submission

Upload [my-team/team.py](../my-team/team.py) through the course submission system.
It contains the complete controller in a single file. GitHub pushes do not update
the league submission.
