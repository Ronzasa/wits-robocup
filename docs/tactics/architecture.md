# TITAN-X experiment architecture

The source of truth is frozen v10.0 plus the build-time fragment in
`tools/titan_x/tactics.pyfrag`. `build.py` produces independent, self-contained
`team.py` files, each containing exactly one controller and importing only math
and the official soccer SDK. There are no runtime imports of the fragment.

The manager defaults all four flags to false in `experiments/titan-x/team.py`.
Each of `titan-x-power`, `titan-x-trap`, `titan-x-pinball`, and `titan-x-ambush`
enables exactly one flag. Those files are experiments, not submission upgrades.

## Command ownership and cancellation

The unchanged v10 decision process runs first. A small kick-selection hook can
propose a different verified pass. Existing goal-bound finishes and productive
forward direct/endwall passes keep priority; a safe carry establishes an extra
score hurdle. Goalkeeper power-play recovery precedes all new movement. An
already verified reception excludes other movement assignments for that player.
Only a newly selected TITAN-X pass owns a new reception movement. Goalkeeper
trap and pinball proposals are evaluated in that deterministic order, and only
one can be installed. The ambush is a separate movement-only proposal and cannot
replace an active pass or a carrier's kick, goalkeeper or defensive cover.

Only a power play changes goalkeeper movement. Its recovery delegates the
movement command back to v10's existing goalkeeper logic. Its cover assignment
is temporary and loses priority to the ball chaser and an existing receiver;
the keeper aborts if its covering player becomes the ball chaser. The power
state machine and realistic travel checks are described in
[the retained concept](goalkeeper-power-play.md).

The trap observes public keeper displacement on adjacent ticks and requires a
meaningful advance away from goal, velocity toward the ball and nearby attacking
play. It sends a free attacker beyond the keeper's rushing line and can choose
a square/reverse pass into a central finishing angle. A correctly positioned
keeper produces no trap. It never gives the ball away to provoke a rush.

The pinball extends v10's side-wall search into advanced wide attacking play.
It searches two receivers, two forward leads and two legal launch speeds: at
most eight launches. It explicitly targets post-side-wall collection in the
central finishing corridor. An actual bounce is compulsory. A 2.4-second dense
trajectory covers interception opportunities on both legs. Friction, wall
restitution and first-tick carrier contact are inherited unchanged from v10.

The ambush reads the last-touch opponent's public cooldown, considers two nearby
outfielders and simulates no more than five ticks. An actual executable first
touch must precede the opponent's legal next kick and every opponent's earliest
verified contact, including body contact by the cooling-down player. It has no
sticky pressing assignment: the next observation must independently revalidate
it, or ordinary movement resumes. No additional screening player is assigned
without evidence of a safe benefit; normal cover and support remain in charge.

## Additional passing checks

All new passes use `_carrier_contact`, a dense `_pass_path` and `_pass_race`.
The receiver follows `_move` with the same first command the manager will issue;
the route needs a legal kick or physical body touch. Local first-touch checking
also evaluates cooldown, momentum, rebound velocity and nearby opponents. Other
teammates' possible body interference is conservatively rejected along the
route. A missing interception returns infeasible, without an ETA substitute.

The local first-touch flag is restored with `finally`; v10's movement estimates,
shots, keeper physics, defensive cover and counterpress functions have identical
ASTs. A new tactical reception keeps its own verified movement on launch, then
updates only while the existing v10 plan and an actual-command race remain live.
The all-off controller is checked for identical movement, kicks, debug and pass
plans against v10 across a sequence of observations.

## Evaluation and limits

`registration.json` fixes cohorts, opponent archive hashes, selection rules and
the original promotion gates before native play. `evaluate.py` runs targeted,
independent development, conditional interaction and fresh qualification stages.
One serial worker uses the unmodified native 20 ms deadline and 2,400-tick
matches throughout. Raw timeout rows and exact repeats are retained separately.
Whole-seed paired bootstrap intervals resample 16 complete seed blocks in the
768-pair qualification, preserving both sides, both kickoffs and all 12 styles.

Controller telemetry is bounded to eight labels per decision. The external
runner counts executed command ticks only for valid decisions under 20 ms, and
groups adjacent run/challenge ticks into episodes. Those are commands, not proof
of ball collection or caused goals. Match pass statistics, turnovers, goals and
points are native engine results. Five-second event associations are explicitly
non-causal. Native timing histograms and slow-call CPU/GC observations are also
external to the timed controller; cgroup counters accompany every raw match.

The frozen local opponents cannot establish improvement against the actual
school league leaders. Promotion evidence is limited to these registered native
fixtures. A weak, inactive or timing-unsafe tactic is retained as a documented
failed experiment, without enabling it in the current team.
