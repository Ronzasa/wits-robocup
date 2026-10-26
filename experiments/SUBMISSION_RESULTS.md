# Submission results — final file

**Upload `../my-team/team.py` alone.** Controller: `AdaptiveChampion`, version
`champion-hunt-adaptive-1.3`; size **163,576 bytes**, below the 256 KiB limit.

SHA-256: `5c73068b5e574093e9e1afce972ff8b3546b484c103505c9e79d80772ac6299d`.

## Matched official-simulator comparison

The exact final file and the frozen original TITAN each played these **420
fixtures**, at 2,400 ticks, five players and a 20 ms decision deadline, with
engine 0.1.0 and config hash `372990895c7eca2a`:

- Balanced, tactical and possession: seeds **2000–2049**, both field sides,
  using the official SDK evaluation protocol: 300 matches total.
- The same opponents: seeds **4000–4009**, **both field sides and both kickoff
  owners**, through official SDK `play_match`: 120 matches total.

| Metric | Existing TITAN | Final submission |
|---|---:|---:|
| Wins / draws / losses | 419 / 1 / 0 | 419 / 1 / 0 |
| Goals scored / conceded | 442 / 14 | 442 / 14 |
| Goal difference | +428 | +428 |
| Mean decision time | 0.06736 ms | 0.06022 ms |
| Maximum decision time | 23.8639 ms | 13.0860 ms |
| Decisions measured | 1,008,000 | 1,008,000 |
| Timeouts | 4 | 0 |
| Policy errors | 0 | 0 |

| Opponent, 140 matches each | Before W/D/L | After W/D/L | Before goals | After goals |
|---|---:|---:|---:|---:|
| balanced | 139/1/0 | 139/1/0 | 151–9 | 151–9 |
| tactical | 140/0/0 | 140/0/0 | 147–5 | 147–5 |
| possession | 140/0/0 | 140/0/0 | 144–0 | 144–0 |

The supported improvement is **deadline reliability**, with the competitive
score record preserved. No higher win rate or championship superiority is
claimed. Timing is measured on this machine and does not guarantee server
timing. The 7 ms optional-search budget may change choices with machine load.

Raw final reports are `results/submission-holdout-*.json` and
`results/submission-fair-*.json`; all record the final source hash above. Paired
before reports are `original-holdout-*` and `original-fair-*`. All platform-error
counts are zero. SDK side swaps always give the evaluated team kickoff; the
separate fair suite explicitly covers the other kickoff owner as well.

## Retained changes and rejected experiments

- **Removed score-dependent retreat while trailing.** The older local TITAN
  file used `TRAIL_WALL = 2` and parked at 0–2 or 1–3. The newest downloaded
  file already disabled the constant; the final removes the branch entirely.
  Positive-lead walls remain intact.
- **Bounded optional searches to 7 ms**, returning the best candidate found
  so far. Existing dribbling, transitions, passing, goalkeeping, shot physics,
  interception checks and defensive marking are preserved.
- **Reduced shooting-search cost** with early rejection of unsafe candidates
  and reuse of existing acceleration reach tables.
- **Reverted** the new keeper guard/sweep behavior: independent 40-match
  self-play gave 13W/14D/13L and 80–81 goals, versus the original's 11W/18D/11L
  and 79–79. The uncertainty was wide and did not support keeping it.
- **Reverted** the new shot reach model after one possession win became a
  draw in the larger holdout. **Reverted** deeper central cover after losses
  increased from 8 to 13 in the exploratory 40-match comparison.

Intermediate sources and raw reports remain under `experiments/`. Reports
labelled `selected-*` and `final-*` are intermediate experiments, **not this
submission**. Their hashes differ. `RESULTS.md` explicitly marks its earlier
keeper version as superseded.

## Final acceptance checks actually executed

```powershell
python tools/test_titan.py
python launch.py check my-team
python launch.py validate my-team --against tactical --ticks 2400 --json
git diff --check
```

- **7 regression tests passed**, including reproducing the old 0–2/1–3 wall,
  preserving positive-lead defense, specialist behavior while trailing, legal
  formation, finite complete actions and safe exhaustion of search budget.
  Score scenarios are policy tests, not fabricated simulator score results.
- Official **check PASSED**.
- Official full-length tactical **validation PASSED**: five public seeds,
  **12,000 decisions**, mean **0.034 ms**, maximum **5.405 ms**, no warnings,
  exceptions, timeouts, missing actions or non-finite values; custom formation
  accepted without correction.
- `git diff --check` passed. Imports are only standard-library `math`/`time`
  and the official `soccer` SDK. No extra submission modules are required.

The repository initially held the starter. The original used for improvement
was the newest TITAN found at
`C:\Users\tech\Downloads\TITAN_fixed_two_goal_defence.py`, preserved verbatim in
`titan-original/team.py`. Existing replay headers identify Ethan Ikopit,
Muhammed Abed and Zamokuhle Maziya; no verified Gabriel Behane or Kevin Ebrahim
data/source was available, and no result against them is claimed. See
`README.md` for fuller provenance and experiment commands.

Work remains uncommitted on **`titan-final-upgrade`**. Master was not changed;
nothing was pushed or submitted to Moodle.
