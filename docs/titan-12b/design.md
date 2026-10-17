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

## Independent components

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

## Cost and legal interface

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

## Registered extension: physically observed counterpass routes

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
