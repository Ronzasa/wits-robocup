# Physics tactics: development review and single revision

The 64 configurations per source were completed before this review. Frozen v10
earned 100 points and the active Cutback reference earned 107. Ambush earned 95,
Wall-Brake 100 and Rebound Shot 100. No tactic qualified from these small results.
All three final isolated builds still receive the fixed unused qualification
cohort. No feature combinations or additional competitive development cohorts
are used.

## Rebound Ambush — priority

There were 19 accepted plans, 19 confirmed native wall bounces and 19 assigned
player contacts. Only three contacts were reported as immediate controlled
receptions; a kick touch need not leave a controlled ball. Those counts do not
prove that Ambush improved the outcome over ordinary chasing.

The first clean successful fixture was replayed without a deadline miss or
exception and reproduced its score. At tick 506 the plan predicted a bounce at
507, but a strict `old_bounce < current_tick` check cancelled it exactly at 507.
Ordinary chasing subsequently completed the collection. The revision includes
the exact bounce tick, maintains a feasible fixed aim after the bounce, and
checks the existing commanded chase before starting a new ambush. A safe
existing chase within 0.10 seconds is preserved. The exact native bounce state
is now a regression case.

## Wall-Brake Pass

Two native kicks and wall bounces occurred. Both ended when the passer kicked
again before the intended receiver collected. A nominally safe receiver route
did not account for the passer chasing its own rebound.

The revision exposes the post-movement player state already computed inside
v10's carrier-contact helper, through an optional output argument. Default
contact results and arithmetic remain identical. It uses the existing player
rollout to reject self-collection before the receiver and coordinates a short
passer departure while the verified reception remains feasible. The designated
cover player cannot launch this tactic. Existing direct passes retain priority;
this search adds only slow lateral/backward routes near a side wall, which the
existing advancing-bank search does not cover.

## Precision Rebound Shot

There were no executions. The initial wrapper preserved every geometric goal
forecast, including a blocked trajectory. The revision preserves only a
physically verified safe shot when considering this tactic. It activates v10's
existing restitution-aware bank-shot helper at three bounded goal targets,
checks opponents along the full dense route, and checks the final pre-goal
movement/kick step. It keeps existing named passes. Unrelated shooting logic,
keeper behavior and defensive cover remain unchanged.

## Native physics and independent qualification

Four legal native flight fixtures cover upper/lower side walls, an oblique
side-wall rebound and an end-wall rebound. Stock engine/configuration are used;
only legal starting formations and ordinary player commands set up the flights.
All 81 sampled position/velocity pairs per flight match frozen v10's forecast
within 0.00002 units. No state, restitution, friction, engine or configuration
is modified.

The original development sources and records remain frozen. The final source
hashes are recorded in `revision.json` and the qualification protocol before
the 768-configurations-per-source cohort is opened. No qualification outcome
will change a source, threshold, opponent, seed or cohort size. Raw native
points are the primary outcome. Exact clean repeats are diagnostic only.

The active champion and `main` remain unchanged regardless of this experiment's
outcome; a later deployment requires the owner's explicit approval.
