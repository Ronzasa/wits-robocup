# Operation MONSTER — measured findings

## Verdict on the frozen TITAN

**MONSTER convincingly defeated the validated TITAN in the reserved holdout:**
**79 wins, 14 draws, 7 losses**, goals **185–57**, mean goal difference **+1.28**
over **100 full-length official-simulator fixtures**. This meets the requested
70% measured-match milestone. It does not establish universal leaderboard or
championship superiority.

The exact MONSTER is `monster/team.py`, `Monster`, version `v25-fast-post`,
27,381 bytes, SHA-256
`1bf09f5fcab940eae8f387ef36030d302dfe9e52aa6ae0fe82f48742ea6e85b7`.
The validated `my-team/team.py` is unchanged, SHA-256
`5c73068b5e574093e9e1afce972ff8b3546b484c103505c9e79d80772ac6299d`.

## Primary scorecard and uncertainty

Source: `results/monster-v25-holdout.json`. Seeds 730000–730024 were reserved
before tuning. The candidate was selected on separate training/validation
seeds, then hash-locked **before** these 100 matches. It was not changed after
the holdout began.

| Metric | MONSTER | Frozen TITAN |
|---|---:|---:|
| Wins / draws / losses | 79 / 14 / 7 | 7 / 14 / 79 |
| Goals | 185 | 57 |
| Goals per match | 1.85 | 0.57 |
| Mean decision time | 0.145 ms | 0.492 ms |
| Maximum decision time | 9.626 ms | 22.760 ms |
| Policy errors | 0 | 0 |
| Timeouts | 0 | 3 |
| Fouls per match | 0 | 1.11 |
| Possession | 24.56% | 75.45% |
| Native shots per match | 3.71 | 17.28 |
| Pass completion | 5.37% | 40.92% |

Win rate is **79% of all matches** and **91.86% of decisive matches**. The
descriptive match-level Wilson 95% interval is **70.02–85.83%**. Four fixtures
share each seed, so they are not 100 independent random draws: the
**25-seed-cluster bootstrap interval is 69–88%**, and the seed-cluster normal
95% interval for mean goal difference is **+1.041 to +1.519**. Thus the sample
passes the target; an underlying win probability above 70% is not guaranteed.

The final protocol audit confirms exactly 100 unique fixtures, all four
side/kickoff combinations per seed, 2,400 ticks and the expected config hash.
Three fixtures contained a TITAN timeout. Excluding those fixtures as a
**post-hoc sensitivity check** leaves **76W/14D/7L in 97 matches**, goals
**178–56**, mean GD **+1.258**. The advantage therefore persists without those
timeouts. All 100 matches remain the primary result; nothing was rerun or
replaced. See `holdout-audit.json` and `lab.py --audit-holdout`.

All four fixture types were actually executed:

| MONSTER absolute side | Kickoff owner | W/D/L | Goals |
|---|---|---:|---:|
| 0 | TITAN | 19/6/0 | 39–13 |
| 0 | MONSTER | 21/2/2 | 46–14 |
| 1 | TITAN | 18/3/4 | 44–15 |
| 1 | MONSTER | 21/3/1 | 56–15 |

This was the unchanged Wits engine **0.1.0**, course configuration
**372990895c7eca2a**, five players, **2,400 ticks**, **20 ms for both teams**.
The harness explicitly crosses field side and kickoff owner, rather than
assuming the SDK tournament's side-swap shortcut balances kickoff. See
`README.md` for the exact protocol, source protection and command lines.

## Generalization

The same frozen source played 20 fixtures per opponent, using five separate
generalization seeds × four fixture types:

| Opponent | MONSTER W/D/L | Goals | Mean GD |
|---|---:|---:|---:|
| balanced | 20/0/0 | 107–1 | +5.30 |
| tactical | 17/3/0 | 41–4 | +1.85 |
| possession | 20/0/0 | 133–0 | +6.65 |
| older TITAN, fixed two-goal branch | 14/2/4 | 33–11 | +1.10 |
| older TITAN, buggy trailing wall | 14/2/4 | 33–11 | +1.10 |
| previous MONSTER v21, fixed-outlet shell | 4/10/6 | 26–29 | −0.15 |
| previous MONSTER v06, field pressing | 15/2/3 | 79–33 | +2.30 |

The official baselines combined are **57W/3D/0L, 281–5 goals**. Every
generalization run had zero MONSTER errors/timeouts. The two older TITAN files
are closely related and produced identical outcomes; they are not independent
strategy families. Twenty matches per opponent give limited precision.

The v21 comparison is a real limitation: MONSTER is not uniformly strongest
against its own pool. Its −3 total goals over 20 matches are not strong proof
of a true negative matchup, but they prevent a claim of universal dominance.
No tuning was done from these or the final holdout results.

## How the independent agent wins

MONSTER was written as a new controller, without importing, subclassing or
copying TITAN's policies. Its selected architecture is a four-player goal
screen plus one stable wide outlet, rather than TITAN's normal build-up and
irreversible wall-specialist architecture.

The near-side covering player presses a ball near its own post instead of
remaining in its wall slot. The outlet waits closer to the clearance path and
holds its chosen side, then uses momentum-aware interception, short controlled
touches and impulse-aware finishing. Contested touches explicitly consider
either ordering of simultaneous legal kicks. All decisions use current public
observations and self-maintained match state; there is no runtime source/file
access, hidden engine state, hardcoded result, opponent identity or seed branch.

Normal field pressing alone failed: the initial independent implementation
went 0W/3D/13L. More pressing, twin keepers, bank clearances, extra attackers and
five-player lead walls were tested and rejected. A keeper-trajectory shot
model was slower and did not beat the simpler selected strategy; it is
disabled in the frozen agent. See `EXPERIMENTS.md` and the full `SCORECARD.md`.

## Demonstrated TITAN weaknesses

1. **Its active siege path bypasses kickoff protection.** In an actual v23
   replay, seed 700000, side 0, TITAN committed fouls at ticks **19** and
   **1762**; the latter follows its goal at tick 1750 and MONSTER's restart.
   MONSTER committed no fouls. The official holdout averaged 1.11 TITAN fouls
   per match. Source review locates missing protection in the specialist's
   siege path. The raw events are in the replay diagnostics, not inferred
   private opponent data.
2. **Corner siege forecasting assumes fixed five-slot defenders.** TITAN
   predicts opponents returning to those slots even when observations show
   four cover players, a moving post defender and a distant outlet. On the
   same 40 validation fixtures, adding post pressure changed MONSTER from
   **17W/14D/9L, 61–51** to **29W/8D/3L, 73–22**. This supports a weakness in
   those fixed-slot corner attacks; it does not assign every goal difference
   to one line of code.
3. **Siege support leaves the counterattacking outlet goal-side of all three
   support runners.** The original specialist places them around ball x−12,
   often x≈32 in TITAN's attacking frame, while MONSTER's outlet waits around
   x≈20. Clearances can put it behind that line. This is the concrete transition
   hypothesis tested by the separate Blue reserve-marker candidate.

The more general hypothesis that goalkeeper prediction thresholds alone would
produce a stronger agent was not established: those candidate implementations
were rejected. High possession, shot counts and passing percentage were poor
proxies for victory in this matchup. Native shot/pass metrics are bookkeeping
proxies, **not an xG model**; soft touches can be counted as shot/pass attempts.

## Official validity and lifecycle

The exact frozen MONSTER passed:

```powershell
python launch.py check experiments/red-team/monster
python launch.py validate experiments/red-team/monster --against tactical --ticks 2400 --json
```

Full tactical validation: five public seeds, **12,000 decisions**, mean
**0.063 ms**, maximum **2.930 ms**, zero warnings, exceptions, timeouts, missing
actions or non-finite values. Five-player formation accepted unchanged.
`reset` clears match state, including receiver and outlet-side state. One
`TeamController` subclass and standard-library/SDK dependencies only.

A final repeat of both official commands also passed: validation mean
**0.057 ms**, maximum **1.592 ms**, 12,000 decisions and zero warnings/errors.
The exact command output is saved in `checks/monster-check.json` and
`checks/monster-validation.json`. These are repeated validity checks, not
additional independent competitive evidence.

The policy leaves time after its 7 ms optional-search budget for constructing
all five actions. Timing is measured on this Windows machine; OS scheduling
and search budgets can affect exact reproduction. Exploratory timeouts were
retained and their implementations were not selected as the final controller.

## Scope of the conclusion

The locked experiment supports a strong advantage over **this frozen TITAN**
and good results against the three official baselines. It does not establish
strength against Gabriel Behane, Kevin Ebrahim or a hidden championship field;
no private source or verified replay evidence for those competitors was used.

## Separate TITAN countermeasures: useful, not promoted

Only after the final MONSTER holdout, three small derivatives were created
from frozen TITAN. `blue_build.py` reproduces their source transformations:

- A: guard the specialist on the opponent's stationary centre restart.
- B: reserve one siege support player goal-side of a visible distant outlet.
- C: combine both changes.

All three are standalone files in `blue-pool/`. No validated submission was
edited. Training screens used four new seeds, 700004–700007, 16 fixtures each:

| Opponent faced by MONSTER | MONSTER W/D/L | Goals |
|---|---:|---:|
| frozen TITAN control | 11/4/1 | 23–7 |
| Blue A, kickoff guard | 10/6/0 | 28–8 |
| Blue B, reserve defender | 7/6/3 | 18–10 |
| Blue C, combined | 3/10/3 | 12–11 |

The kickoff-only patch eliminated restart fouls but did not improve goal
difference. The reserve helped, and the combination was selected for a fresh
paired check. No MONSTER code changed during this Blue stage.

On fresh seeds **740005–740009**, 20 fixtures per opponent, MONSTER went
**14W/5D/1L, 31–6** against frozen TITAN and **10W/7D/3L, 27–10** against Blue C.
MONSTER's mean GD fell from **+1.25 to +0.85**, but remained positive. TITAN's
restart fouls fell from **0.85 per match to zero**. These are preliminary
five-seed comparisons, not a separate 100-match Blue holdout or proof that the
countermeasure closes the matchup.

Blue C also faced frozen TITAN directly: **3W/11D/6L, 32–34**. Against official
baselines it scored **19W/1D/0L, 22–3** versus balanced, **20W/0D/0L, 20–0**
versus tactical, and **20W/0D/0L, 20–0** versus possession. Frozen TITAN controls
on the identical baseline fixtures produced exactly the same scores. All
Blue-stage fixtures had zero policy errors/timeouts for both teams.

Thus Blue C is retained as a **matchup countermeasure experiment**, not a
proven stronger replacement. Its direct loss to frozen TITAN prevents that
recommendation. The exact experimental file is
`blue-pool/blue-c-combined/team.py`, SHA-256
`66b768ce051e423bb5de851416651395fe7581f0677edad777dd5dd02023adc8`.
It passed official `check` and five-match `validate`: 12,000 decisions,
mean **0.034 ms**, max **5.402 ms**, zero errors/warnings. Exact outputs are
saved under `checks/blue-*.json`.

The original `my-team/team.py` remains the user's validated TITAN, unchanged
from the initial snapshot. The research stage did not commit, push or submit
anything. The user subsequently authorized committing and pushing the complete
archive on `titan-final-upgrade`, including both agents and experimental Blue
candidates. No competition submission or replacement of validated TITAN was
authorized. The initial unrelated dirty work was preserved and included in
that requested archive. `.gitattributes` preserves the exact tested agent bytes.
