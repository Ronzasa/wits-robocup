# Goalkeeper Power Play concept

This experiment retains the idea of making goalkeeper 0 a temporary fifth
attacker while trailing late. It is a possession-recycling option behind the
attack, rather than a permanent extra striker. v10.0 remains the default team.

TITAN-X tests an idle → advance → active → recover → cooldown state machine.
Eligibility requires 15–35 seconds remaining, advanced possession or a favorable
verified loose-ball race, a useful supporting destination reachable under actual
movement, a covering outfielder, and no current dangerous counter. The evaluator
compares simulated travel and recovery with a fastest empty-net ball flight.
When recovery is slower, an outfielder must have time to reach central cover
before the keeper arrives at its advanced position. This reduces exposure;
it cannot guarantee a save after a future turnover.

Only the active state can pass to goalkeeper 0, through the same execution-aware
race and additional first-touch check as the other TITAN-X passes. A possession
loss, backwards ball threat, score change, missing cover or expiry cancels the
attack. Recovery returns control to v10's goalkeeper decisions. Reaching home
starts a six-second cooldown. Existing receivers keep priority over cover moves.

The activation thresholds are development hypotheses. Results and any rejection
of this concept are recorded in the TITAN-X validation report; this document is
not a claim that an empty-net tactic improves competition results.
