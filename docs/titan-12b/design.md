# TITAN-12B design and isolation

The frozen baseline is v10.0 on main commit
`0a7a3aeba3950eb1b2ed0deeb7a06f2f9b3563e5`; its active and archived source hash is
`5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6`.
The branch is `titan-12b-counter-defence` and no TITAN-11 tactic is inherited.

The official game has five players. The user explicitly authorized retaining
**one outlet briefly in a high-risk emergency**, rather than requesting six
simultaneous distinct roles. Normal cover leaves the other two free runners'
commands intact. Emergency support reserves the verified receiver, if present,
or the most advanced existing free-runner target as the outlet; it never rewrites
that player's attacking command. It does not manufacture an additional player.

## Initial independent components (development precursors)

* **Detector:** reuse v10's directly observed own-contact/loss evidence and the
  already-computed ball races. A genuine recent loss, likely impending loss, or
  an opponent advancing into a dangerous central area can activate risk scoring.
  Stale phase/controlling-team labels alone cannot invent a possession loss.
  A secure holder, favorable existing pass, or ready own kicker suppresses it.
* **Single cover:** rank at most four opponents by projected goal distance,
  centrality, forward velocity and availability of an unblocked passing lane.
  Ignore forwards already guarded goal-side. Move only the designated defender.
  Use a nearby goal-side point if it can contribute soon; otherwise screen the
  pass lane locally, or make no change. This is not a permanent deep formation.
* **Emergency support:** independently tested with original v10 cover. Require
  a clear opponent race advantage, urgent danger and two substantial threats.
  Use at most one extra outfielder who can reach a useful screen within .65 s.
  Reserve goalkeeper, chaser, live receiver and one outlet. A burst lasts at most
  .6 seconds, never extends while the same threat persists, and cannot rearm
  merely because its high-risk score briefly flickers below threshold.
* **Recovery:** targets are rebuilt from v10 every decision. No defensive target
  is retained across ticks. Secured possession or an absent threat releases the
  new assignment immediately, and clears the emergency latch. Protected restarts,
  score changes and tick rollback clear episode state.

The risk/positioning estimates are heuristics, not certified interceptions.
All execution-aware pass verification remains byte-for-byte unchanged. Every
original method except `reset()` and the single defensive call in `act()` is
preserved; shooting, carry/pass choices, keeper safeguards, movement physics,
marking and counterpress are not rewritten. The new hook runs after existing
verified receiver planning and never edits the goalkeeper, primary chaser or
named receiver target. A current ready kicker keeps all original decisions.

## Initial cost and legal interface

There is no new ball rollout, pass-race search or simulation tree. There are at
most four threat candidates and five friends; lane checks and the one support
selection are bounded. The controller imports only `math` and the official
`soccer` interface, has exactly one controller class and is self-contained in
`team.py`. Development builders, diagnostics and tournament tools are outside
submission folders and are never imported by a controller. No controller reads
clocks or changes GC, engine settings, affinity, scheduling or the 20 ms limit.

## Regression and native checks

The independent sources passed 122 regressions each, including 46 saved native
counter situations, goal-side/mirrored marking, unguardable/wide threats,
verified receivers, ready kickers, protected restarts, immediate recovery,
role-capacity limits and the non-extending emergency timer.

A separate instrumented native diagnostic ran 16 complete matches/source
against `v10-counter`, `v10-press`, v9.1 and `v10-compact`, both sides/kickoffs.
Across 115,200 decisions all pre-existing policy state, kicks, keeper/chaser
commands and live receiver commands matched a v10 shadow on identical public
observations. Detection alone changed zero actions. Single cover changed 779
ticks; emergency support changed 54, so both action components were exercised.
All source-side native diagnostic policy exceptions and raw misses were zero.
Instrumentation changes allocation/timing and is not substituted for strength
or reliability evidence from the uninstrumented tournament controller.

The first saved-snapshot test used manually written decimal field constants;
17 cases differed by sub-micro-unit coordinates from native float32 metadata.
The regression fixture now preserves the exact public field values, including
`ball_friction=0.9850000143051147` and `kick_range=2.200000047683716`.
The snapshots then reproduced exactly, without relaxing comparisons or changing
controller code. The earlier failed test logs remain in the evidence archive.

## Registered extension: observed-flight precursor

Both speculative cover variants and the one flight-filter refinement lost
points in the completed 48-fixture development screens. Before any held-out
results existed, one architecture extension was registered in
`route-registration.json`. This explicitly extends the initial research budget;
it does not change the champion, promotion gates, raw timing policy or failed
results. No further tactical tuning is planned after this freeze.

The new detector forecasts only the ball currently observed in flight. It uses
the unchanged `_verified_intercept()` with explicit local dense step metadata
for at most four opponents and the existing chaser. An unavailable physical
contact is infeasible; no heuristic ETA substitutes for it. Opponents' earliest
verified contacts determine the candidate receiving points and the primary
chaser's verified earlier contact suppresses an unnecessary cover override.
Possible alternate receivers are limited to the first .25 seconds after the
earliest contact; their ranking follows contact time, not speculative depth.

An already goal-bound near-term shot retains the existing v10 response. A
reception within 14 pitch units of our goal also retains it, avoiding new
cover assignments in the goalkeeper's immediate area. The designated defender
must be able to contribute before collection/lane arrival rather than after
it. Recovery, role locks, the .6-second emergency limit and outlet remain the
same independently tested components.

The extra computation is one 1.25-second dense public-physics forecast and at
most five bounded contact queries. It is gated off whenever any own player is
ready to kick, so it cannot overlap the expensive own shooting/pass search.
It does not modify the existing pass cache, receiver aim, pursuit heuristic,
shooting or keeper code. New regressions cover actual direct and wall-rebound
counterpasses, nonexistent contacts, earlier own chasers, goal-bound shots,
terminal-area safety and cache isolation.

The new detector, single cover and emergency support undergo independent native
checks before combination. Their complete development ablation will precede
selection and one 768-pair held-out qualification. Even a weak development
winner will receive that final qualification; no favorable cohort will be
selected, pooled or rerun to override a failed gate.

## Final integration: anticipate a legal release before it occurs

The observed-flight precursor found 229 threat ticks in 38,400 shared native
observations per variant, but no useful positioning changes: the defender was
too late. A second version also considers up to two legal imminent releases
while an opposing carrier controls the ball just after our loss. This is a
bounded prediction of possible enemy actions, not a claim to know enemy intent.

The carrier must be ready to kick. Its forecast uses the unchanged legal
kick-impulse, requested-velocity and actual carrier-contact helpers, with movement
toward our goal. At most two forward/central receivers within 35 pitch units
are considered. The resulting wall-aware routes use the same dense public
physics and strict contact witnesses. Current observations at t=0 are not
mistaken for new collections: future contacts start at the next movement step.
All feasible opposing receivers compete along each route, and a physically
earlier primary chaser suppresses a needless cover intervention. An unavailable
contact remains infeasible; no ETA is substituted.

Controlled central shooting danger, already goal-bound near-term shots and
terminal collections inside 14 units of our goal retain the baseline response.
This protects the keeper's existing decisions and avoids new goal-mouth cover
assignments. Opponent cooldowns, launch power, player acceleration and speed
caps remain official. Hypothetical contacts assume the public free-motion
forecast; future collisions and the opponent's chosen action remain unknown.

Requiring a goal-side marker to arrive *before* the opposing collection made
the strict predictive positioning variants inactive too. Before any physical-
threat strength tournament or held-out result, the final integration restored
the **original independently tested cover target selector**, rather than adding
another set of fitted timing coefficients. Its positioning ETA is a heuristic,
distinct from the opponent's physically verified collection. The final detector
is identical to the predictive precursor, and the target selector/assignment
methods are identical to the initial independently tested components. Regression
tests enforce this method-level isolation.

`verified-cover` and `verified-double` passed independent native checks before
`verified-combined` was created. All three then entered the same complete paired
development screen. The registered selection chose the combined controller:
71 versus v10's 70 points, 51 versus 48 goals scored, 45 conceded each. Single
cover tied it; emergency support alone matched v10. This is preliminary evidence,
not a promotion result. The selected source was copied **byte-for-byte** to
`experiments/titan-12b/team.py`, and both its expansion and final qualification
protocols were frozen before the expansion began.

The selected source hash is
`8e33c9f624ec9bf61282eaa076cc2b539ec511c72d320787d8c91fc7be1d4074`,
already committed in checkpoint `f843834`. Both assignments are enabled. Their
methods are identical to the isolated variants; only the two action flags differ.
The combined source passed **135 regressions** and 38,400 native shared-state
checks before its first tournament. Across all independent precursors and the
combination, 499,200 shared native decisions checked preservation of original
state, kicks and protected role commands. These are diagnostic comparisons,
not extra independent strength samples or a guarantee of zero timing spikes.

The final work adds at most two 1.25-second forecasts and ten bounded contact
queries. Local dense step metadata is shared by queries on the same path without
changing our passing cache or receiver aim. It is disabled whenever any own
player is ready to kick, so it cannot overlap the expensive own kick search.
There is no full-tree search, learning dependency or submitted timer/GC control.
The registered promotion gates and untouched final seed cohort are unchanged.

A final post-qualification development-seed replay added an exact snapshot of
the selected controller, including public cooldowns and pre-hook emergency
state. It reproduces without tolerance relaxation. Final verification passed
136 tests. These additional 9,600 native shared-state checks bring the diagnostic
total to 508,800; the controller and every formal result remain unchanged.
