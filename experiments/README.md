# TITAN submission experiments, 26 October 2026

The submission is **`../my-team/team.py`**, controller `AdaptiveChampion`, version
`champion-hunt-adaptive-1.3`. Upload that file alone. This directory contains
benchmark evidence and frozen candidates; none is imported by the submission.

The repository initially contained the SDK starter, on clean branch
`titan-final-upgrade` at `106956a`. The existing TITAN implementation was found
at `C:\Users\tech\Downloads\TITAN_fixed_two_goal_defence.py` and copied verbatim
to `titan-original/team.py` before any changes. Its SHA-256 is
`fbefad666f340467110e77c204aa0cb0a787be6b1885b40115e8cb3035d1e4ae`.
The Downloads files were never modified. No commits, pushes, master changes,
or Moodle submissions were made.

The bundled official simulator works with Windows Python 3.11.9. The alternate
installation requested by the user was checked and contains the same SDK and
starter. All competitive runs use engine **0.1.0**, config hash
**372990895c7eca2a**, the unmodified `configs/default.toml`, **2,400 ticks**,
five players, and a **20 ms** decision deadline. Only profiling runs explicitly
relaxed the timeout; profiling results are not counted as competitive evidence.
The reported lab comparisons run sequentially with one worker. Two early CLI
baseline tournaments ran concurrently; their timing is not used in the final
before/after tables.

## Changes and selection

- Removed the trailing-wall branch and its `TRAIL_WALL` setting. The older
  `team12_clean_broadwall_stiff.py` has `TRAIL_WALL = 2`, activating the wall at
  0–2 and 1–3. The latest downloaded file already sets it to zero; removing the
  branch prevents that setting from reintroducing the bug. Positive-lead wall
  behavior and the specialist's lead/tie bait remain as before.
- Tested a keeper guard and safer sweeps. **Reverted them** after independent
  self-play did not confirm a benefit: 80–81 goals in 40 matches versus 79–79
  for the original. The existing predictive keeper and save rollouts remain.
- Tested acceleration, current velocity, speed-cap and kick-cooldown bounds
  in a new shot evaluator. **Rejected it after the larger holdout**: it turned
  one possession win into a draw and scored one fewer goal overall in that
  300-match suite. The final submission retains TITAN's existing ball impulse,
  drag, carrier contact, goalkeeper/defender lane and early-body shot checks.
  It rejects already unsafe candidates earlier to reduce search cost. Reports
  labelled `shot-*`, `final-*`, and `self-final-fair-holdout-*` describe this
  discarded intermediate. The exact intermediate is in `with-shot-final/`.
  Reports labelled `selected-*` describe the later keeper intermediate in
  `keeper-selected/`. Only **`submission-*`** reports describe the final file.
- Gave optional shot/pass/bank/handoff/siege searches a shared 7 ms budget.
  Searches return the best candidate found so far, leaving time for movement,
  receiving and SDK validation. Reused existing reach tables and rejected
  unsafe shot options before doing further work. The clock budget can change
  candidate selection under different machine loads; it is not a hard real-time
  guarantee against OS scheduling delays.
- Preserved existing controlled dribbles, forward passes, quick transitions,
  marking and the wall specialist. A deeper central-cover experiment was
  **rejected**: in the 40-match TITAN comparison it increased losses from 8 to
  13 and reduced goal difference from +6 to +2. Its code is absent from the
  submission; its frozen source and results remain for review.

## Reproduction

Use the repository root as the working directory. `python launch.py` is the
same launcher called by `START.cmd`; neither the engine nor SDK was changed.

```powershell
python launch.py doctor
python tools/test_titan.py
python launch.py check my-team
python launch.py validate my-team --against tactical --ticks 2400 --json
python tools/titan_lab.py --team experiments/titan-original/team.py --label original-holdout --start 2000 --end 2050
python tools/titan_lab.py --label submission-holdout --start 2000 --end 2050
python tools/titan_lab.py --team experiments/titan-original/team.py --label original-fair --both-kickoffs --start 4000 --end 4010
python tools/titan_lab.py --label submission-fair --both-kickoffs --start 4000 --end 4010
```

`--end` is exclusive. Default opponents are balanced, tactical and possession.
`--opponents experiments/titan-original/team.py` runs a comparison with the
frozen original. Full result records, source hashes, seeds, validation counters,
latency and platform errors are stored under `results/`.

The SDK tournament's `swap_sides=True` gives the evaluated team kickoff in
both fixtures: it swaps team order **and** kickoff owner. We retained those
official tournament results and separately added `--both-kickoffs`, which
runs four fixtures per seed through the official `play_match`: two field sides
times two kickoff owners. The SDK itself is unchanged.

The initial starter-only diagnostic was 2W/6D/12L, goals 6–19, against balanced
over seeds 1000–1009 and two sides. It is not used as the TITAN improvement
baseline. TITAN's 120-match initial suite was 120W/0D/0L, goals 125–1; an
additional 300-match suite at seeds 2000–2049 was 299W/1D/0L, goals 313–9.

## Opponent evidence and limits

No replay JSON was present in the repository or the specified simulator
installation initially. Three existing JSON replays were found in Downloads
and inspected with `python tools/titan_lab.py --replays`. Their headers name
Ethan Ikopit, Muhammed Abed and Zamokuhle Maziya, with the same engine/config.
They do not verify any Gabriel Behane or Kevin Ebrahim strategy. No private
source code for those competitors was accessed, no opponent was reconstructed
from invented data, and no match against either named competitor is claimed.

The highest-win reference suites have a ceiling effect because TITAN protects
its first lead. Small self-play improvements have wide uncertainty; they do
not establish championship superiority or predict hidden opponents/seeds.
Only standard-library `math`/`time` and the official `soccer` SDK are imported
by the submission. It is below the official 256 KiB source limit.

Final measured tables and official validation results are in
**`SUBMISSION_RESULTS.md`**. `RESULTS.md` is a superseded keeper-intermediate
report and records a different source hash.
