# Selected league controller

The standalone submission is `../../league-team/team.py`, packaged from
`ray_cover2/team.py`. Its SHA and pre-holdout decision are in
`selection-v2-lock.json`. Packaging changes only controller name and version;
the tested playing logic is preserved.

The selected policy uses these active mechanisms:

1. **A goal screen that follows shooting geometry.** Four guards project the
   goal mouth onto their covering line using the ball's position. Close shots
   see a narrower opening at that line, allowing the guards to close the fixed
   corridors seen in the school replay. One common centre is bounded before
   placing players, maintaining at least 2.16 units between their targets.
   Wide near-post cover remains available outside the projected-screen region.
2. **Predictive counterattack recovery.** The outlet follows a friction- and
   rebound-aware ball trajectory and searches for a reachable interception,
   accounting for its movement and kick cooldown. A stable wide outlet offers
   a counter route after defensive clearances.
3. **Controlled touches.** Kick direction and power compensate for current
   ball velocity. Short forecasts include the carrier's movement and body
   contact, balancing progress, opponent reach and the ability to collect the
   next touch rather than always using full power.
4. **Observed shooting gaps.** Against a dense goal-mouth wall, shot aims also
   come from the spaces between visible blocker bodies. The existing shot
   forecast checks the proposed routes and cooldowns; there are at most five
   extra aims in addition to the original nine.
5. **Contested-kick decisions.** Ordinary duels consider both orders of
   simultaneous kicks. Near the attacking corner, the controller also tries
   inward goal-directed kicks so that repeatedly kicking into the end wall is
   less attractive than an actual scoring opportunity.
6. **Restart and lead management.** Score changes reset pass/restart state;
   the outlet respects the opponent's protected centre circle. Guard depth
   changes when leading while the outlet continues counterattacking.
7. **Bounded optional computation.** Search shares a seven-millisecond budget
   inside the twenty-millisecond decision deadline. The complete five-player
   action is still returned when optional search ends. Measured overruns, if
   any, remain in the final results.

The current winner retains four guards and one outlet. Releasing a second
attacker, switching policies after the first conceded goal, and more elaborate
clearances were all tested; their extra complexity did not earn as many points
in selection. The source also preserves disabled research options, which are
not credited as active tactics.

All runtime decisions use public observations and resettable in-match state.
The submission imports only `math`, `time.perf_counter` and official `soccer`
classes. It has one TeamController subclass and no runtime files, external
dependencies, opponent identity tests, hidden state or seed-based decisions.

Final results concern a fixed local tactical pool. The real school field must
still play the submitted release before its actual league win rate is known.
