# Keeper possession and wall counters

**Development complete: no challenger advances; main and the active champion remain unchanged.** [Actual results](results.md): active 98 points, back passes 93, wall counters 98 (zero new executions), combined 93. Back passes completed 38 named-keeper collections from 45 native kicks. The fresh validation seeds remain unused.

Experimental branch `keeper-possession-counters`, based on active Elite Replay Cutback commit `40b2787`. Main and `my-team/team.py` remain unchanged.

- `experiments/keeper-backpass/team.py`: pressure-triggered back passes to a ready keeper close to home.
- `experiments/keeper-wall-counter/team.py`: keeper distribution to a named outfield receiver after a verified side-wall rebound.
- `experiments/keeper-support/team.py`: both features, tested as a separate source.

The existing productive forward passes, finishing, defensive cover and ordinary keeper saves keep priority. New receivers use the existing dense native ball forecast, executable movement rollout, first-touch check, cooldowns, full-route opponent race and teammate obstruction check. The keeper does not advance as a general extra attacker. The existing reception manager owns the receiving command, and a change of touch or infeasible race cancels it. The current controller already supports direct keeper distribution.

The back-pass search tries two speeds; the keeper wall search tries at most four launches. New trajectories are only considered in the defensive area. No physics, SDK timing, game configuration or player attributes are changed.

The sources are frozen before development; `registration.json` records development selection and untouched validation seeds and gates. Development is 48 matched configurations per source, including both pitch assignments and kickoff arrangements. A challenger proceeds to 384 fresh matched validation configurations only if it wins more development points and executes at least one new native reception. Raw deadline misses count even when diagnostic repeats succeed. No automatic promotion is authorized.

Run the regressions with `python -m unittest discover -s tests -q`. Run the native screen with `python tools/benchmarks/run_keeper_support.py --protocol docs/keeper-support/development-protocol.json --out /path/to/new-output`. The official Linux engine must be installed in the student SDK; the distribution ships the same binary in `engine/linux-x86_64`.
