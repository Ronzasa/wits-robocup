# MONSTER second research round

The user requested a stronger MONSTER after the first release. Existing
results, source snapshots and the first holdout remain historical evidence.
The first-release v25 is the fixed control; TITAN stays protected and unchanged.

New seed partitions are declared before this round's first match, with
exclusive upper bounds:

- Training: 750000..750012.
- Validation/selection: 760000..760010.
- Final locked holdout: 770000..770025 (100 fixtures per opponent).
- Generalization: 780000..780010, separate from selection and holdout.

Every seed still crosses both field sides and both kickoff owners, using the
unmodified official engine, 2,400 ticks and the enforced 20 ms deadline.
No second-round candidate will be selected from the old exposed holdout.

The opponent pool includes frozen TITAN, the combined Blue countermeasure,
previous MONSTER v25/v21, and all three official baselines. The old result
against TITAN alone is insufficient to establish general playing strength.
Particular targets are stronger wall-breaking, fewer lost counterattacks,
and a positive record against earlier MONSTERs without sacrificing TITAN wins.

Initial source hypotheses, to be tested rather than asserted as facts:

1. The selected shell has only one attacking player and does not support it
   even when the opponent is visibly passive in its own half.
2. The close-duel routine preempts all shot evaluation, using only a few
   forward kick directions. It can miss a scoring sideways/corner action.
3. Four defenders clear to a fixed far-wide point without checking whether
   the outlet or an opponent can collect it.
4. Wall shot forecasts assume fixed defender positions; attempted corner
   approaches can be stalled by an adaptive near-post opponent.

All candidates and actual scorecards will remain in the laboratory. The old
release is replaced only if fresh comparative measurements support it.

Finalist selection uses fresh validation matches against all four pool
opponents: frozen TITAN, patched Blue, MONSTER v21 and MONSTER v25. League
points (3 per win, 1 per draw), worst matchup and goal difference matter;
original-TITAN wins alone cannot select the finalist. Policy errors and actual
deadline overruns remain in every report; they are never silently removed.

The final estimate will compare the hash-locked finalist with the **fixed v25
control** on identical 770000..770025 fixtures. `round2-holdout-control`
intentionally shares those seeds for paired measurement, accepts only the
already-declared v25 hash, and cannot run until the new finalist is locked.
It is not another candidate-selection partition. No new policy is selected
after either holdout arm is exposed. `lab.py --compare BEFORE AFTER` computes
paired, seed-cluster bootstrap intervals for the change in points and GD.

## Training findings

Twenty-two variants, v26–v47, each faced all three initial opponents over the
same eight full fixtures. These tiny screens are selection evidence only.
The control also played sixteen fixtures per opponent.

Replay `r2-control-v21-close-outlet-750000-s0-k0.rep` shows the near-post guard
following a wide ball to about y=-9.5 while leading. At ticks 1638 and 2172
the opponent scored inside that exposed post. This motivates limiting the
guard's displacement; it does not establish that all losses had one cause.

- Predicting a shot by moving one guard aggressively helped the v21 matchup
  but hurt TITAN results; rejected as a complete policy.
- A tighter post limit, especially 6.6 or 7.3, reduced concessions broadly.
- A second striker, moving the lead wall forward/back, and shifting the wide
  outlet did not give consistent improvements across the three opponents.
- Forecasting defender kicks/body contacts was implemented and executed, but
  did not outperform the simpler candidates. It is not assumed accurate or
  included merely because it is more complicated.
- Momentum-aware clearance searches improved goals against original TITAN in
  some screens but lost their advantage against other opponents; rejected.
- Fast free-space touches helped against modified TITAN but weakened the
  static-wall matchup when used throughout the approach.
- v46 combines a 7.3 post limit with fast touches **only when the observation
  does not show an opposing wall**. It scored 18W/6D/0L across the 24 screening
  fixtures: 8/0/0 versus TITAN, 6/2/0 versus Blue C, and 4/4/0 versus v21.
  It had zero policy errors/timeouts in that screen. Fresh validation, not
  those two training seeds, will decide whether to select it.

Exploratory timeouts, including some very large isolated wall-clock values,
remain recorded. The v25 control also timed out during fresh validation.
Their cause is not established by these logs; CPU scheduling is a hypothesis,
not an excuse to discard a fixture or relax the 20 ms rule.

## First fresh validation comparison

Each entry has 40 matches: ten validation seeds, both sides and both kickoff
owners. These are selection results, not the final holdout.

| Opponent | Released v25 W/D/L (goals) | v36 post limit W/D/L (goals) | v46 fast-open W/D/L (goals) |
|---|---|---|---|
| Frozen TITAN | 34/5/1 (79–19) | 37/3/0 (74–8) | 30/9/1 (59–13) |
| Blue C | 14/14/12 (37–32) | 18/21/1 (36–10) | 20/17/3 (37–9) |
| MONSTER v21 | 8/23/9 (57–59) | 20/18/2 (46–19) | 20/18/2 (48–21) |
| MONSTER v25 | 13/14/13 (58–59) | 28/8/4 (49–15) | 25/8/7 (47–17) |
| **Total** | **69/56/35 (231–169)** | **103/50/7 (205–52)** | **95/52/13 (191–60)** |

v36 earned 359 league points versus v25's 263 and v46's 337. Its 153 total
goal difference beat 62 and 131 respectively. v46's small extra Blue win rate
did not compensate for its regressions against TITAN and v25; rejected as the
preferred overall policy. v36's improvement primarily comes from conceding
less, not from scoring more. Its actual exploratory timing overruns remain
in the reports (five across these 160 fixtures).

The v51 implementation streams the same ball forecast into interception,
stopping generation once a reachable frame is found. Repeated-use pass/shot
paths remain materialized. A deterministic equivalence check and new matches
are required before selecting that implementation; it is not assumed equal
merely because this is intended as a performance refactor.

The subsequent v48–v50 marking-trigger screens used additional training seeds
750002–750003. None beat v36 consistently: the control scored 7/1/0 versus
TITAN and 5/3/0 versus Blue C; the marked variants scored 6/2/0 versus TITAN
and 4/4/0 versus Blue C. They were rejected without exposing holdout seeds.

The streaming implementation passed the 1,000-case geometry/interception
check and its own 160-game validation: **101W/52D/7L, 202–52**, 355 league
points, zero exceptions and one elapsed-time timeout. Official checks passed.
It was then frozen as v51 with SHA-256
`0d9be04ce17bbb21f73d31ac6ca8a2b9afde81cee9ae865eff99f6564b9151b6`.
This selection and its timing limitation were recorded before any new holdout
match in `round2-selection.json`. No later candidate was tuned on that holdout.
