# League research protocol

The goal is league points across different observed styles, followed by goal
difference and reliable, inexpensive decisions. A win over TITAN alone does
not qualify a release. School standings use a class round robin; the public
course guide describes three points per win, one per draw, then divisions of
twenty with mean decision time ordering within each division. The live school
rules and cohort still need to be checked against the supplied leaderboard.

All competitive fixtures use the original course config and engine, 2,400
ticks and both teams' 20 ms deadlines. Every seed crosses absolute side 0/1
with kickoff owner 0/1. Sources are frozen by full SHA-256 before play.
Results include every fixture and every error or timeout; no rerun replaces
an inconvenient result. Sequential execution reduces competing CPU load.

Research seeds are 810000..810010 (exclusive end). Initial broad screen uses
810000..810003. Selection uses 820000..820004. Final holdout uses
830000..830010. The final candidate's full source hash must be locked before
any final results are examined. Selection may reject all candidates. If the
final result disappoints, it is reported and those seeds become exposed.

The fixed primary opponent set has twelve equally weighted members:

- Six offered native baselines: balanced, tactical, possession,
  structured_attack, man_marking and ball_chaser.
- Archived TITAN, archived MONSTER v51, Blue C, and MONSTER v21.
- Independently written Pressure and Counter stress teams under opponents/.

Every policy faces the same frozen opponents. TITAN and MONSTER controls are
included. MONSTER's own-play row remains in the comparison. This pool is a
local sample of tactics, not a substitute for the unknown student field.
Additional public school evidence may motivate separate diagnostic opponents;
such a scope change must be recorded before final selection.

The primary comparison is paired points per game, clustered by seed to retain
correlation between sides, kickoff owners, and opponents. Pooled win rate,
goals, per-opponent points, action validity, errors, timeouts and decision
mean/max are also reported. Fewer goals conceded, more passes, or beating
TITAN head to head cannot substitute for more league points.

Validated files under my-team/ and experiments/red-team/ remain controls.
New candidates and evidence live here; the selected single-file submission
will be published locally in league-team/team.py after validation. Nothing
is uploaded to the school by these tools.

## School evidence amendment, before selection or final holdout

Public school evidence on October 27 identifies a v51-style four-cover policy
in the current entrant's replays. The replay pipeline uses the default
kickoff formation, while earlier local benchmarks honor initial_formation.
Current ladder rows and regenerated replays also changed during inspection;
there is no stable historical Titan-versus-Monster comparison available.

Therefore robustness to both starting formations becomes a release criterion.
The harness's --formation default only overrides initial_formation for both
source controllers; it forwards original observations, actions and lifecycle.
It changes no engine, config or team source. Default-start training uses
810003..810005. Selection uses 820000..820002 in custom mode and
820002..820004 in default mode. Final holdout uses 830000..830005 in
default mode and 830005..830010 in custom mode. All bounds are exclusive.
Thus each policy still plays 480 primary fixtures over ten fresh seed clusters,
half in each formation mode. Final opponent list will be fixed in selection
lock if a separately documented, school-inspired stress opponent is added.

One archived portfolio prototype raised when writing to optional debug=None.
It was rejected and preserved. The engine stops a forfeiting team with its
on-field score still present; relying on score alone can wrongly award a win.
New benchmarks preserve that on-field score and separately adjudicate 0-3
under the course rule. The analyser applies this correction to historical
prototype records as well. No forfeiting policy qualifies for release.

## Corrected geometry and expanded open-play coverage, before final holdout

The first selection set completed without exposing any 830000-series seed.
Ray cover led with 554 points (173W/35D/0L), versus MONSTER's 527 points
(162W/41D/5L), in 208 fixtures each. Static review nevertheless demonstrated
that independently clipping wide-ball guard targets could put two guards at
the same point. This is corrected in the separately named ray_cover2 source
by clamping the screen's common centre, preserving guard spacing. The original
candidate and first selection evidence remain unchanged.

A second predeclared selection therefore compares corrected Ray Cover2,
Guardian and the wall-only portfolio against MONSTER. It adds Open Gap, a
source-contained adversary based on our own TITAN open-play controller with
gap-targeted shots and supporting attackers. It contains no student source
or identity checks. The first weak pressure diagnostic remains auxiliary.

The new primary pool has fourteen equally weighted opponents. Selection uses
822000..822002 custom and 822002..822004 default (224 fixtures per policy).
The separate v2 plan and source manifest precede all of those fixtures. The
winning new source is then SHA-locked before any final play. Untouched final
seeds stay 830000..830005 default and 830005..830010 custom: 560 fixtures per
policy, ten seed clusters, compared against both original controls. There is
no reselection after observing final results.
