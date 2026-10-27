# Contact-aware corner finishing experiment

The standalone `team.py` preserves ray_cover2's four guards. Its additional
attacker search is gated to a level score, an observed four-player opponent
goal screen, and eighteen ticks inside a two-unit attacking-corner cluster.
Ordinary open play and play while leading or trailing use the existing policy.

Four goal aims each consider the existing carrier approach, movement behind
the shot direction, and movement outside the inward ball corridor. The short
rollout applies both modeled kick orders, then reuses `Monster.launch` to
include the carrier's movement and first body collision before forecasting
the shot. It keeps the old corner decision unless the completed model finds
a scoring improvement without fewer successful scenarios. The existing 7 ms
deadline applies; an unfinished search returns the previous best decision.

This tests whether carrier contact makes the old corner shot evaluation
misleading. It is not established improvement: later body contacts, multiple
simultaneous opponent kicks, and future opponent decisions remain approximate.
Fresh screening is required. No match was run during the locked release's
primary holdout, and no validated release or earlier evidence was modified.

Reproduce with `python experiments/league/build_contact_finish.py`. The builder
refuses to replace a differing existing candidate and is not used at runtime.
