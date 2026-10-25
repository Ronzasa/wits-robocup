# Review of uploaded champion_candidate.py

**No replacement is recommended. These are review experiments, not promoted
champions.** See the [results and native diagnostics](../../docs/champion-candidate-review/results.md).

- `uploaded/team.py` is the byte-identical uploaded file, SHA256
  `7708f5d3b10202092f1fce73abfc61a5d7a61d91326d95d69cec872d4c7ba758`.
- `no-trailing-wall/team.py` changes only `TRAIL_WALL = 2` to `0`.
- `guarded-wall-break/team.py` changes only `_wall_break()`. It protects
  existing kicks, receiving plans and cover/chaser assignments, and reuses the
  existing shot forecast instead of firing solely at a geometric gap.

The two changes were tested independently, never combined. All three preserve
the upload's `LOCK_LEAD=1` and `LOCK_TIME=1.0`. The docstrings and controller
version strings are retained from the frozen upload; use source hashes to
identify the tested files. The historical header about untested code does not
describe the completed evaluation in the linked report.

`main`, active `my-team/team.py`, archived champions and the earlier controller
at `experiments/replay-finishing-handoffs/team.py` remain unchanged.
