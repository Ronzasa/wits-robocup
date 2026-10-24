# Tactic investigation: protocol (written before any result was produced)

Branch: `experiment/tactic-investigation` (from `master` @ e71f9b8). Nothing here is promoted.
`master`, `my-team/`, the simulator (`engine/`, `student-sdk/`, `configs/`), the local `champion/`
and every opponent under test are read-only. Opponents under test are *copies* in `opponents/`
(hashes in `HASHES.txt`); probe controllers written for experiments live in `probes/`.

## Ideas under test

1. **Kickoff foul bait.** When we own a protected kickoff, delay our first kick briefly so that
   opponents who enter the centre circle are relocated to a touchline (the engine's only foul),
   and release before the restart expires (3 s = 60 ticks).
2. **Goal-wall wedging.** Use legal player-player collisions to displace a defender and open a
   *verified* shooting lane (clear segment, width >= ball diameter + margin) on a defended goal.
3. **Defender-assisted own goal.** Use a defender's kick cooldown (5 ticks) by rebounding the ball
   off the end wall into that defender's body so that it deflects into goal (`own_goal` event).

Only legal actions (`PlayerAction`) and public observations (`obs`) may be used. No seed, no
opponent name, no branching on side, 0 fouls by us, 20 ms deadline.

## Frozen baseline

`baseline/team.py`, sha256 `6529c92e...` (see `HASHES.txt`): the delivered v with faster code,
`LINK_MARGIN 0.03`, lock-the-lead, wall-breaker and trailing wall. It must hash identically at the
end of the investigation. Simulator: engine `_engine.abi3.so` and `configs/default.toml` hashes are
recorded in `HASHES.txt`; the repo SDK differs from the local platform copy only in line endings.

## Stage 0: mechanism proof (native, reproducible, no strength claims)

Each idea gets a script in `probes/` that drives the real engine through `soccer.play_match` with
fixed seeds and prints/writes raw counts to `results/`. An idea is **promising** only if its
mechanism is demonstrated *and* its public-observation trigger can plausibly fire in real matches:

* Bait: >= 1 opponent `foul` event while our restart is still live, in some opponent, with our kick
  still accepted before expiry. Report foul rate per opponent and delay length.
* Wedging: in a controlled probe a defender is displaced by >= 1.0 unit by legal pushes and a lane
  >= 1.15 wide (ball diameter 0.9 + 0.25 margin) opens; report the success rate and time to open.
* Own goal: in a controlled probe a cooldown-window rebound produces an `own_goal` goal event;
  report the success rate over fixed geometries and then how often the trigger geometry occurs in
  ordinary matches (activations per match).

If the mechanism is not shown, or cannot be triggered from public observations, it is closed
(documented, not developed).

## Stage 1: development (may tune)

Seeds `30000..30199`. Candidates may be modified only using these seeds.

## Stage 2: confirmation (the gate; no tuning allowed)

Fresh seeds `40000..40149` (never used before: all earlier work used seeds below 25000).
Balanced design: every seed is played in all four combinations of (our side) x (who kicks off),
for baseline and candidate on identical configurations, so each unit is a *pair*.

Opponents (copies, hashed): `champion_original`, `lock_no_breaker`, `champion_press_formation`,
`bus_wall`, plus built-ins `tactical`, `possession`, `balanced`, `man_marking` (30 seeds each, as
harm / reliability checks).

Primary metric: league points per match (win 3, draw 1, loss 0) of the candidate minus the
baseline on the same unit. Pooled over all strong-opponent units, paired t-interval 95% (a
bootstrap interval is reported as a cross-check).

## Promotion gates (all must hold; promotion still needs the owner's approval)

1. Pooled paired points difference: **95% lower bound > 0**.
2. No single opponent where the 95% *upper* bound of the points difference is < 0 (no significant harm).
3. `./start.sh check` PASSED, `validate`: 0 exceptions, 0 over-deadline, 0 missing actions,
   0 non-finite values; slowest decision < 20 ms in validate.
4. 0 policy errors in all evaluation matches; 0 fouls by us.
5. Raw deadline misses (`policy_timeouts`) per match not above 1.25 x the baseline's rate on the
   same units plus 0.002/match (the sandbox is loaded and produces sporadic misses on both).
6. No forbidden constructs (subprocess, socket, threading, pickle, eval, file writing) and no use
   of the seed, opponent identity or `obs.side`.

Also reported (not gates): goals for/against, goal difference, activations, conversions
(activation -> goal within 10 s), mean decision time.
