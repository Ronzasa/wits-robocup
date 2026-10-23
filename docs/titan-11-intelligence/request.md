# PROJECT TITAN-11 — Next-Generation Autonomous Soccer Intelligence

## Mission

Build **TITAN-11**, a substantially more intelligent RoboCup 5v5 soccer agent that evolves the existing v10.0 TITAN-10B-R champion from a predominantly heuristic controller into a coordinated, predictive, learning-informed tactical system.

**Implement all six improvements described below.** This is an implementation project, not a proposal or theoretical design exercise.

Repository: https://github.com/Ronzasa/wits-robocup

- Base branch: `main`, NOT `master`.
- New development branch: `titan-11-tactical-intelligence`.
- Frozen competition baseline: `my-team/team.py`, currently v10.0 TITAN-10B-R.
- Expected v10.0 baseline SHA-256: `5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6`.
- New candidate: `experiments/titan-11/team.py`.

Verify the repository's current state before starting. Preserve the original v10.0 controller byte-for-byte. Never modify the champion, historical experiments, engine, competition rules or official SDK.

## Existing performance

On 720 matched fresh local fixtures, v10.0 achieved:

- 1,922 points.
- 618 wins, 68 draws, 34 losses.
- 2,351 goals scored; 349 conceded.
- 49.02% pass completion.
- 3,777 turnovers.
- 3 raw deadline misses, matching the previous baseline.
- All 95 regression tests passing.

These results establish v10.0 as a strong baseline but reveal opportunities in decision quality, ball retention, finishing and performance against equally strong agents.

Optimize for **expected match points against strong, diverse opponents**, not simply pass completion, possession, or goals against weak bots.

---

# IMPROVEMENT 1 — Predictive Tactical Planning

Replace rigid, independently evaluated shot/pass/dribble decisions with a bounded, forward-looking tactical planner.

### Implementation

1. Implement a lightweight model-predictive action evaluator using the public observation, documented physics and existing verified movement/ball models.
2. Generate candidate actions:
   - Direct shots.
   - Controlled dribbles.
   - Short passes.
   - Progressive passes.
   - Through balls into space.
   - Diagonal releases.
   - Side-wall and end-wall passes.
   - Safe recycling.
   - Emergency defensive clearances.
3. Simulate the most promising actions over approximately 0.5–2.0 seconds where computation permits.
4. Model player acceleration, damping, kick cooldown, ball friction, wall reflections, receiver execution and opponent interception.
5. Predict plausible opponent responses rather than treating them as stationary obstacles.
6. Evaluate resulting field positions, scoring opportunities, possession retention, counterattack exposure and recovery support.

Use an expected-value function such as:

`V(action) = scoring_value + future_attack_value + possession_value - turnover_cost - counterattack_risk - execution_uncertainty`

Calibrate weights empirically, not through arbitrary changes to the live champion.

### Runtime constraints

- Use cheap feasibility filters before detailed evaluation.
- Reuse the existing trajectory and interception calculations.
- Apply beam search or progressive widening only to top-ranked candidates.
- Cache repeated predictions within a decision.
- Use fixed work budgets and deterministic tie-breaking.
- Provide a legal fallback for every observation.
- Never violate the official 20 ms decision deadline.

The goal is better decisions, not necessarily deeper search.

---

# IMPROVEMENT 2 — Coordinated Five-Player Attacking Intelligence

Replace mostly static support lanes with coordinated attacking patterns.

### Implementation

Develop a joint planner for all five players:

- Goalkeeper: safe distribution and defensive insurance.
- Defender/libero: circulation, progression and counterattack cover.
- Midfielder/pivot: passing triangles and support.
- Creator: line-breaking passes and playmaking.
- Striker: penetrating runs, finishing and space exploitation.

Implement:

**A. Dynamic positional play**

Adjust formation width, depth and spacing according to ball position, defender locations, pressure and possession certainty.

**B. Third-man combinations**

Predict sequences such as:

`Defender → Midfielder → Striker`

The third player should begin moving before the second pass becomes available.

**C. Through-ball intelligence**

Search for destinations in reachable empty space, not just a teammate's current or projected position.

**D. Overloads and isolation**

Create local numerical advantages while exploiting switches to unmarked players.

**E. Counterattack coordination**

On a verified regain, coordinate immediate progression, supporting runs and defensive cover.

**F. Rest defence**

Retain sufficient defensive coverage whenever attackers commit forward.

Evaluate coordinated movement and the ball-carrier's action jointly, with executable receiver trajectories.

Avoid commanding a receiver toward a theoretical destination that its actual movement command cannot reach.

---

# IMPROVEMENT 3 — Goalkeeper-Aware Elite Finishing

Improve shooting decisions using opponent goalkeeper prediction.

### Implementation

1. Predict the opposing goalkeeper's likely movement toward each shooting trajectory.
2. Account for current momentum, acceleration, positioning, cooldown and remaining ball flight time.
3. Sample achievable shooting directions, powers and legal wall rebounds.
4. Identify near-post, far-post and central openings.
5. Evaluate defender contact or kick opportunities along the ball's complete path.
6. Compare immediate shots against dribbles, cutbacks and passes that may produce a higher-quality chance.
7. Support rebound follow-up positioning when a shot is likely to be blocked or deflected.
8. Validate actual first-tick carrier contact before accepting a shot.

Build a computationally efficient estimate of:

`P(goal | shot, goalkeeper state, defenders, ball state)`

The probability estimate must be calibrated against native-match evidence; do not present arbitrary heuristic scores as statistically calibrated probabilities.

Prioritize higher expected scoring efficiency rather than shot count.

---

# IMPROVEMENT 4 — Threat-Based Defensive Intelligence

Replace purely proximity-driven defensive decisions with opponent threat assessment and coordinated coverage.

### Implementation

**A. Offensive threat assessment**

Rank opponents based on their ability to:

- Shoot into the goal.
- Receive a dangerous pass.
- Exploit an uncovered central corridor.
- Win a loose ball.
- Create a numerical advantage.
- Progress into a high-value shooting area.

**B. Coordinated marking**

Use a small, deterministic assignment optimizer to distribute defenders between direct pressure, passing-lane screening, goal-side marking and cover.

**C. Intelligent pressing**

Press only when the expected benefit outweighs the risk of abandoning defensive coverage.

**D. Anticipatory interception**

Move into the opponent's likely passing destination rather than always pursuing the current ball position.

**E. Counterattack prevention**

Protect dangerous central areas and exit lanes immediately following possession loss.

**F. Adaptive goalkeeper**

Preserve proven goalkeeper behavior, testing predictive improvements separately.

Do not introduce a rigid five-player defensive wall or permanent retreat strategy. Previous v8 experiments showed that broad defensive changes can significantly reduce competitive performance.

Measure goals conceded, counterattack concessions, opponent high-quality chances and points — not defensive shape alone.

---

# IMPROVEMENT 5 — Engine-Specific Kickoff and Wall Playbooks

Exploit the legitimate tactical opportunities created by the official RoboCup engine.

### Implementation

Develop specialized, physics-valid playbooks for:

1. Own kickoffs with guaranteed initial possession.
2. Opponent kickoffs with protected centre-circle positioning.
3. Planned opening passing combinations.
4. Quick attacks immediately after restarts.
5. Side-wall rebound passes.
6. End-wall passes and second-ball recovery.
7. Long diagonal switches using wall geometry.
8. Goalkeeper distribution under pressure.
9. Controlled ball recovery near boundaries.

Search and optimize initial formations and restart sequences offline.

Ensure every move is legal and no player enters the prohibited centre circle during an opponent kickoff.

Do not exploit hidden engine state, seed-specific opponent behavior or modify physics/configuration.

Select playbooks dynamically from the current publicly observable match state, and immediately abandon a sequence if its execution or safety conditions fail.

---

# IMPROVEMENT 6 — Self-Play Learning and Automated Tactical Optimization

Develop an offline system that continuously discovers stronger tactical policies through tournament evaluation.

### Implementation

**A. Opponent league**

Construct a training pool containing:

- TITAN-10B-R v10.0.
- Frozen v9.1 and earlier champions.
- Existing development opponent styles.
- Aggressive pressing agents.
- Defensive and counterattacking agents.
- Possession-focused agents.
- Long-range shooting agents.
- Wall specialists.
- Diverse newly generated legal challengers.

**B. Self-play**

Run candidate policies against each other and their archived ancestors.

**C. Automated parameter optimization**

Search tactical parameters including:

- Shoot versus pass thresholds.
- Risk tolerance.
- Defensive pressure intensity.
- Support positioning.
- Space valuation.
- Through-ball timing.
- Shot selection.
- Transition aggression.
- Rest-defence spacing.

Start with computationally efficient derivative-free optimization, evolutionary search or population-based training.

**D. Offline value learning**

Investigate whether a compact fitted value function can outperform hand-authored decision scores.

Train using native-match outcomes and observation/action traces, without accessing hidden information unavailable to the competition controller.

Do not require a large neural network at inference time.

**E. Generalization**

Evaluate against unseen seeds and held-out opponent styles. Prevent overfitting to the fixed local opponent pool.

**F. Deployment**

The learning process may use development scripts and offline dependencies, but the submitted `team.py` must remain fully standalone under the official controller rules.

Embed any learned numerical parameters or compact model directly into `team.py`. No runtime file reads, model downloads, networking or unsupported imports.

---

# Implementation Architecture

Build all six improvements as independent, testable components before attempting full integration.

Recommended development phases:

**Phase 1 — Diagnostics**

Profile v10.0 match performance. Identify and categorize failed attacks, lost receptions, turnovers, missed high-quality shooting opportunities, exposed defenders and conceded goals.

**Phase 2 — Individual challengers**

Implement and test each improvement separately against unchanged v10.0.

Use separate experimental variants or configurable experimental flags. Do not make every new behavior active immediately.

**Phase 3 — Joint planner**

Integrate the best predictive attacking, coordinated movement and finishing components.

Maintain the original reliable movement, collision and reception mechanics unless a change has direct evidence of improvement.

**Phase 4 — Defensive and set-play integration**

Add promising defensive and restart improvements through measured ablations.

**Phase 5 — Self-play optimization**

Optimize the combined policy through offline opponent-league training.

**Phase 6 — Independent competition validation**

Freeze the strongest development candidate before evaluating on a preregistered, untouched validation cohort.

A component failing its own ablation should remain implemented but disabled in the final challenger. Completion means all six strategies have working code and evidence, not that every one must be enabled regardless of results.

---

# Statistical Evaluation

The competition baseline is **v10.0 TITAN-10B-R**, not v9.1.

Compare against the exact frozen champion using matched seeds, both pitch assignments and both kickoff arrangements.

Use development fixtures for experimentation and reserved, independent fixtures for final validation.

Track:

- League points and points per match.
- Paired bootstrap 95% confidence interval, resampled by independent seed block.
- Wins, draws and losses.
- Goals scored and conceded.
- Performance against each opponent.
- Shot quality and conversion.
- Pass attempts, completion and interception.
- Uncollected passes.
- Turnovers.
- Possession and control.
- Defensive failures and counterattack goals.
- Kickoff and wall-play outcomes.
- Mean, p99, p99.9 and worst-case runtime.
- Raw deadline misses and policy exceptions.

Include per-feature ablations, plus an ablation of the fully integrated challenger.

A useful diagnostic is head-to-head play against v10.0 itself, in addition to the opponent league.

Do not infer a real league-ranking improvement from local matches.

---

# Promotion Gates

Preserve the established promotion methodology while replacing the old competition baseline with v10.0.

The final TITAN-11 release must meet all of the following:

1. Higher fresh league points than v10.0.
2. Positive paired 95% confidence interval lower bound for points per match.
3. Zero policy exceptions.
4. No reproducible deadline failure.
5. Accepted mean decision time no greater than `v10.0 mean × 1.35 + 0.04 ms`.
6. At most two additional **raw** deadline misses per 1,000 fixtures relative to v10.0.
7. Official SDK validation successful under the unchanged 20 ms limit.
8. All existing regression tests pass, plus focused tests for every new subsystem.
9. No illegal actions, hidden state access or unsupported runtime dependencies.
10. Source frozen before independent fresh evaluation.

Use 720 or more paired fresh fixtures if practical, with enough independent seed blocks to support the paired inference. Explain any limitation in statistical power.

Never conceal timeouts through reruns or relax a failed gate.

---

# Final Deliverables

Create:

- `experiments/titan-11/team.py` — complete standalone challenger.
- Tactical planning and self-play development tools.
- Automated training/evaluation scripts.
- Regression tests and tactical scenario tests.
- Diagnostic replays of successful and failed strategies.
- Development ablation results.
- Frozen independent tournament results.
- `docs/titan-11-validation.md` — comprehensive analysis.
- Machine-readable per-fixture results and configuration.
- Reproducible execution commands.

Document why each improvement was enabled or disabled.

Commit all work to `titan-11-tactical-intelligence` and prepare a reviewable pull request.

Do not modify or promote `my-team/team.py` without explicit approval.

## Final instruction

**Write and test actual working code.**

Do not stop after describing algorithms, recommending tactics, or creating an architectural document.

Implement the six improvements, validate each independently, combine those with proven value, and use offline self-play to find stronger parameters.

Preserve TITAN-10B-R's physics accuracy, match reliability and hard 20 ms decision deadline.

The goal is a measurable improvement against increasingly difficult opponents while retaining or improving performance against the existing pool.

If TITAN-11 fails any promotion gate, preserve v10.0 and report exactly what failed, supported by full evidence.