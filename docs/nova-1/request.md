# PROJECT NOVA-1 — Build a New Championship Soccer AI

Repository: https://github.com/Ronzasa/wits-robocup

Create branch: `nova-1-next-generation`

**Mission:** Build a fundamentally new, independently designed, high-performance RoboCup agent capable of outperforming TITAN v10.0 and challenging the strongest school teams.

This is not another TITAN patch. Do not copy the v10 tactical policy and attach new heuristics. Its verified low-level physics and validation utilities may be reused after equivalence testing, but the decision-making architecture must be newly implemented.

## Core system

**1. Unified team decision engine**

Design one controller that jointly coordinates all five players.

Generate a small, bounded collection of physically feasible team plans: direct attacks, through balls, quick combinations, shots, possession retention and defensive recovery.

Each plan must include compatible player movement assignments, not just a kick decision. Prevent support players from abandoning defensive cover or intended receptions.

**2. Model-based action evaluation**

Use the official ground-ball physics, movement acceleration, damping, collisions, kick cooldown and interception rules.

Evaluate promising plans over a short prediction horizon against several plausible opponent responses.

Use exact physical verification where available and conservative approximations elsewhere. Never treat a heuristic interception estimate as a guaranteed reception.

Keep the online decision budget strictly bounded and comfortably under 20 ms.

**3. Offline competitive policy learning**

Build an offline optimization system that learns a compact policy/value function from actual native match outcomes.

Use population-based search, structured policy optimization or another justified approach.

Optimize league points and matchup robustness, not passing volume or arbitrary tactical scores.

Train against a league containing v10.0, v9.1, independent offensive and defensive agents, aggressive pressing, counterattacking, long passing and generated adversarial variations.

Evaluate candidates over multiple seeds and opponent styles. Include a robustness objective so gains against a few favorable opponents do not conceal significant failures elsewhere.

Do not repeat TITAN-11's tiny parameter search and call it comprehensive learning. Use a meaningful, staged optimization budget and document what was actually explored.

**4. Learned coordinated football**

The policy should be capable of discovering and executing:

- Progressive passing and timely through balls
- Off-ball runs timed to expected receptions
- High-probability finishing opportunities
- Effective defensive recovery and counterattack prevention
- Goalkeeper positioning based on legal ball trajectories
- Match-state-aware risk management when winning or losing

These are desired behaviors, not mandatory hand-coded tactical packages. Keep features only when they improve real match outcomes.

**5. Lightweight final controller**

Distill the learned strategy into one self-contained, legal Python `team.py`.

The submitted controller must not need online training, model files, additional packages, network access or expensive full-tree search.

Embed compact trained parameters directly in the controller. Use only permitted SDK functionality.

## Development strategy

Start by producing a functioning independent baseline controller and proving it is legal and reliable.

Then implement the joint planner and learning system. Run iterative native competitions and improve the policy based on actual results.

Compare against v10.0 throughout development, but keep final test seeds and some opponent styles completely unseen during training, policy selection and tuning.

Do not use held-out validation results to select new parameters.

## Promotion criteria

Freeze v10.0 unchanged.

Before proposing NOVA-1 for competition submission, require:

- More league points than v10.0 on fresh, paired, independent fixtures.
- A strictly positive whole-seed bootstrap 95% lower confidence bound for the points-per-match improvement.
- Robust performance against previously unseen opponent styles, not only the training league.
- Zero controller exceptions and no reproducible deadline failures.
- The existing raw deadline gate: no more than two additional deadline misses per 1,000 fixtures.
- Passed SDK acceptance, single-file validation and all applicable regression checks.
- No substantial unexplained collapse in direct head-to-head results against v10.0 or other strong opponents.

Use at least 768 fresh paired fixtures in the principal qualification, with both sides and kickoff arrangements, and reserve an additional completely untouched confirmation cohort if the first qualification succeeds.

Never substitute mean decision speed for deadline reliability.

## Required outputs

Implement the full controller, offline trainer, adversarial opponent league, reproducible tournament pipeline, regression tests and benchmark report.

Publish the strongest candidate's results against v10.0, including points, wins, goals for/against, direct head-to-head performance, individual opponent breakdowns, confidence intervals, deadline misses and runtime distributions.

If it is weaker, continue development only using development data and preserve all failures honestly. Do not rename a failed candidate as a champion.

**The objective is not to create the most complicated soccer AI. The objective is to discover and validate a new controller that wins significantly more matches than v10.0.**

Do not modify `main` or the current submitted `my-team/team.py` without explicit approval.