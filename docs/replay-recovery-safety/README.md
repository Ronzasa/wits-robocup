# Replay recovery and safety, v2

Submission file: [team.py](../../experiments/replay-finishing-handoffs/team.py).
Version: `replay-recovery-safety-v2`. Base: feature-branch commit
`8cc79367bcfe7a05009eaf66fdd37d9d1275a395`.

**Evaluation correction:** the 64-match run below used the SDK's custom
formation hooks, whereas the captured course replays start with native default
rosters. A subsequent 1,408-match investigation corrected this setup and tested
isolated variants. No challenger qualified; the final held-out variant scored
287 points versus team (8)'s 286, with an inconclusive confidence interval.
See the [audit and corrected results](../replay-evaluation-audit/results.md).
Those results belong to the documented variants, not unchanged full-v2.

Initially implemented at the owner's request without executing the controller.
The owner subsequently authorised matches. The frozen version has now played
**64 full native head-to-head matches against uploaded team (8).py**:
31 wins, 7 draws, 26 losses; 100–85 points and 95–55 goals. Both passed official
intake, but the candidate recorded one raw deadline miss versus none for team
(8), and the seed-block 95% interval for its points advantage includes zero.
**It remains unqualified.** See the [complete results](head-to-head/results.md).

## Evidence guiding the changes

The uploaded HAR ZIP contains four complete, faithful own-team games against
Zamokuhle, seeds 1000–1003, with all four pitch/kickoff combinations represented.
The owner identified the submitted controller as uploaded `team (8).py`.
These were existing games, not tests of this implementation.

- Scores, our team first: 0–5, 1–2, 0–6, 0–5.
- Seventeen opposing finishes plus one keeper own goal.
- Fourteen opposing finishes have no outfielder goal-side of the shooter at
  the final kicking observation; fifteen finish within 0.5 units of a post.
- At 30.65 s in seed 1003, the keeper is explicitly recorded as scoring an own
  goal after a requested clearance still leaves positive velocity toward its
  right-hand goal. Requested direction did not establish the actual outcome.
- Controlled-ball ticks: 865/9,600 for us, 2,539/9,600 for the opponent.
- Mean outfielder width: 20.34 vs 20.47. Full-power kick share: about 17.5% for
  both teams. These observations do not establish width or maximum power as
  the main missing feature.
- The final captured league snapshot reports 1,083 policy timeouts over 1,012
  fixtures for our team, with a 0.4882 ms mean. The replay bodies have no
  per-decision timing and cannot attribute the timeouts to code or environment.

Only derived observations are documented here. Raw HAR, request headers,
credentials and session data are not part of this commit.

## Changes

### Temporary defensive recovery

One available outfielder recovers toward the goal-side shooting corridor when
the opponent has dangerous possession or a fast ball threatens our half.
Targets account for the ball's forward motion and advanced opposing receivers.
Selection favors the previous guard in a close race. Entry/exit thresholds
provide hysteresis; secure own possession or a vanished threat restores normal
assignments immediately.

The keeper, primary chaser, verified receiver and active short-touch carrier
are excluded. A player able to kick is also excluded. This does not introduce
a permanent deep defender or a second emergency defender. Final verified pass
reception retains priority if a new pass selects the recovering player.

### Keeper clearance outcome checks

Existing clearances that are safe in the model retain priority. A near-goal
clearance is evaluated using the existing capped impulse and carrier-contact
model followed by a twelve-tick ball continuation with drag and wall returns.
A dangerous original permits at most fifteen alternatives: altered movement,
five directions at two powers, and no-kick body-blocking choices. If all
modeled kicks remain dangerous, a no-kick movement is used.

Future player interactions remain uncertain. This is not a proof that own
goals are impossible. Keeper positioning, shot anticipation and sweep/save
methods are otherwise retained.

### Bounded verification and reuse

Each decision uses separate finite work allowances:

| Work | General candidate search | Selected/live reception | Short handoffs |
|---|---:|---:|---:|
| Pass races | 24 | 6 | 4 |
| Interception samples | 3,200 | 2,400 | 400 |
| Receiver movement steps | 1,200 | 900 | 160 |
| Fallback movement-witness steps | 800 | 600 | 120 |

These are deterministic work limits, not measured milliseconds. They reserve
verification for the actual selected launch and live receiver commands, and
prevent long candidate searches from consuming the short-handoff allowance.

An exhausted verification is **unknown**. It cannot be used as evidence that
an opponent has no interception. Partial interception/rollout results are not
cached. A selected pass that fails its final check falls back to an ordinary
carry or checked keeper clearance instead of launching without a receiver plan.

Per-decision caches retain up to twelve pass forecasts, twenty-four touch
evaluations, and the active pass's bounded interception/receiver queries.
First-touch velocity data is restored with a cached forecast. All caches reset
each decision; no earlier observation or changed cooldown can authorize a pass.

### Short-touch execution

Under moderate pressure, a slow carry can use a strict version of the existing
touch forecast. It checks body contacts, cooldown, both pre-movement readiness
and post-movement kick range, and a conservative opponent reach envelope. It
does not substitute a heuristic recapture ETA for a failed short rollout.

An existing qualifying touch is retained; otherwise at most six small
alternatives are considered, subject to the shared twenty-four-touch limit.
The selected carrier follows the same receding chase target used in that
forecast while cooling down. The plan ends on a score change, different touch,
verified pass plan, collection opportunity, excessive separation or expiry.
Unmodeled teammate/player collisions can still invalidate a forecast.

## Preserved behavior and delivery

- `LOCK_LEAD=0` remains set; the all-player goal wall is disabled.
- Single Python submission file, one controller subclass, imports only `math`
  and the official soccer SDK. The recorded site file-size limit is 256 KB.
- General movement and heuristic `_intercept()` are retained.
- Near-post targeting, shooting physics and goalkeeper save/sweep routines are
  retained. The goal-plane fix and named short handoffs from v1 remain present.
- `main`, active `my-team/team.py` and archived champions are not modified.
- This feature-branch version is **unqualified**. The four changes have been
  tested together in the original head-to-head run and subsequently isolated
  in the linked audit. No variant established a qualification points advantage.
  No promotion is justified.

The work caps can reject useful passes, conservative short-touch envelopes can
reject executable carries, and the recovery target can reduce attacking support
while active. The measured head-to-head advantage is uncertain and the raw
deadline miss requires further investigation before claiming this version is
stronger or reliable enough for competition.
