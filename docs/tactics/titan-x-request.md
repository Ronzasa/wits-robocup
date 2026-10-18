# PROJECT TITAN-X — Four Unconventional Tactical Weapons

**Repository:** https://github.com/Ronzasa/wits-robocup

**Development branch:** `titan-x-special-tactics`

**Base controller:** Frozen TITAN v10.0, `my-team/team.py`, preserving the Guardiola/Klopp architecture inherited from v9.1.

## Mission

Implement four experimental, physics-aware tactical systems that could create scoring opportunities our existing controller does not recognize.

Do not build a new soccer AI. Preserve our current goalkeeper safeguards, defending, player roles, verified passing, shooting, counterpressing, wall physics and support movement.

These four tactics must be independently switchable, mechanically verified, and tested against frozen v10.0 before integration.

The goal is to **win more matches**, not to demonstrate impressive-looking tactics.

---

## TACTIC 01 — GOALKEEPER POWER PLAY

**Concept:** Temporarily convert our goalkeeper into a fifth outfield attacker when chasing a goal late in the match.

### Activation

Consider activating only when:

- Our team is losing.
- Approximately 15–35 seconds remain.
- We have confirmed attacking possession or a strongly favorable interception.
- The ball is safely advanced into the opponent's half.
- No immediate counterattack or goal-bound threat exists.
- The goalkeeper can reach a useful supporting position before the attacking opportunity disappears.

All thresholds are initial hypotheses requiring development testing.

### Behavior

1. Advance goalkeeper 0 toward a useful position behind the attack, generally around midfield.
2. Include the goalkeeper as an eligible passing receiver during the active power play.
3. Establish five-player passing triangles, with verified pass feasibility and protected receiver movement.
4. Use the goalkeeper for possession recycling, passing and distribution, rather than routinely positioning it as the furthest striker.
5. Maintain an appropriate defensive covering player wherever possible.
6. Immediately command recovery when opponent possession or dangerous ball movement is detected.

Important: a goalkeeper far from goal cannot return instantly. Model its realistic recovery time and possible empty-net concessions before activating.

Use a persistent state machine with activation, active play, recovery and cooldown states. Avoid repeated activation/deactivation every tick.

### Objective

Increase late-game equalizers and comeback wins without causing more goals conceded than the tactical benefit justifies.

---

## TACTIC 02 — THE GOALKEEPER TRAP

**Concept:** Exploit opposing goalkeepers that aggressively leave their goal.

Instead of simply shooting at a guarded goal, deliberately create situations where the opponent goalkeeper commits toward a ball and leaves space behind.

### Behavior

1. Track the opposing goalkeeper's position and recent movement through public observations.
2. Detect when its behavior indicates an aggressive rush away from the goal.
3. Generate physically executable attacking options that could exploit that movement.
4. Coordinate a primary attacker to threaten possession near the goalkeeper.
5. Send a second attacker into an open finishing or receiving position.
6. Evaluate a direct finish, square pass, delayed finish, or another legal attacking action after the goalkeeper has committed.
7. Abort if the goalkeeper stays correctly positioned or the pass/shot is not physically safe.

Do not assume every goalkeeper will chase bait. Do not sacrifice possession simply to induce a speculative response.

### Objective

Increase high-quality chances and goals against aggressive or poorly positioned goalkeepers.

---

## TACTIC 03 — THE PINBALL SLINGSHOT

**Concept:** Turn the side walls into extra passing surfaces to bypass compact defensive lines.

The existing controller already supports some wall passing. This tactic must meaningfully extend that ability rather than duplicate `_bank_release()`.

### Behavior

1. Identify moments when direct passes are blocked but a side-wall rebound could reach open attacking space.
2. Search a tightly bounded set of physically legal wall-contact points and launch velocities.
3. Model ball friction, wall restitution, player collisions, first-tick carrier contact and opponent interception opportunities.
4. Assign a receiving attacker to run toward the predicted rebound point before the ball reaches the wall.
5. Coordinate supporting players to maintain a passing option and defensive cover.
6. Require physically verified receiver arrival, safe first touch and opponent interception margins.
7. Give an already safe and productive direct pass or shot priority unless the rebound option has a demonstrable advantage.

Explore fast rebound passes into central shooting positions and diagonal runs behind compact defenders.

### Objective

Create attacking opportunities through defensive structures that normally block direct progression.

---

## TACTIC 04 — THE COOLDOWN AMBUSH

**Concept:** Exploit the mandatory five-tick, approximately 0.25-second kick cooldown after an opposing player kicks.

### Behavior

1. Detect an opposing player's actual kick or reliable public kick-cooldown state.
2. Identify the affected player and the remaining cooldown.
3. Predict the immediate ball path using the official simulator physics.
4. Calculate whether one of our players can reach or intercept the ball before the opponent can legally kick again.
5. Temporarily assign the nearest suitable defender to challenge the ball.
6. Where beneficial, position one supporting player to screen the most dangerous passing outlet.
7. Preserve the goalkeeper and essential defensive cover.
8. Cancel the ambush immediately when the interception is no longer favorable or the ball escapes the local pressing area.

A player's kick cooldown does not prevent body collisions, nor does it prevent another opponent from kicking. Account for both.

Do not initiate the ambush if it exposes our goal to a more dangerous counterattack.

### Objective

Convert opponent kicks and loose-ball moments into immediate recoveries and counterattacking chances.

---

## IMPLEMENTATION ARCHITECTURE

Build a **Tactical Opportunity Manager** that runs alongside the existing v10 decision process.

Each tactic should implement:

- An eligibility detector.
- A bounded tactical opportunity evaluator.
- A coordinated movement and action proposal.
- An execution/safety validator.
- An immediate cancellation or recovery condition.

Use the flags:

- `KEEPER_POWER_PLAY`
- `GOALKEEPER_TRAP`
- `PINBALL_SLINGSHOT`
- `COOLDOWN_AMBUSH`

Default all flags to `False` in the initial development controller.

Preserve the ordinary v10 decision whenever no tactic is eligible or no new action provides a credible advantage.

**Critical:** Do not allow overlapping tactics to issue contradictory player commands. Define deterministic priority and respect existing verified reception plans.

All tactical decisions must use official observations and permitted physics. Do not use hidden opponent state, online file reads, external dependencies, clocks, or any modification to the engine or competition configuration.

## EXPERIMENTAL PROCESS

### Phase 1 — Independent implementation

Create four isolated challenger variants, each enabling exactly one tactic.

Add focused unit tests for eligibility, cancellation, movement legality, interception verification and previously protected v10 behavior.

### Phase 2 — Targeted native testing

Test each tactic in situations where it is theoretically useful:

- Goalkeeper Power Play: late-game trailing situations.
- Goalkeeper Trap: aggressive goalkeeper opponents.
- Pinball Slingshot: compact and centrally blocking defenses.
- Cooldown Ambush: quick passing, pressing and counterattacking opponents.

Measure tactic activation frequency, actual execution, goals created, goals conceded, turnovers and league points.

A tactic that rarely activates or fails to produce meaningful additional opportunities should not be carried forward merely because it passes unit tests.

### Phase 3 — Independent competitive evaluation

Compare each enabled tactic against frozen v10.0 in paired full native matches using both field assignments, kickoff arrangements, and diverse opponents.

Keep all results, including failures.

Evaluate impact on:

- League points, wins and draws.
- Goals scored and conceded.
- Pass completion and turnovers.
- Matchup performance against strong opponents.
- Raw deadline misses, exceptions and runtime tails.

### Phase 4 — Integration

Only consider combining tactics that demonstrate promising independent competitive results.

Run interaction tests because two individually useful tactics may interfere with one another.

Do not enable all four by default.

### Phase 5 — Fresh qualification

Freeze the final controller and experiment protocol before playing on unused seeds.

Require the original promotion standards:

- Higher paired league points than v10.0.
- Strictly positive whole-seed bootstrap 95% confidence lower bound.
- Zero policy exceptions.
- No reproducible deadline failure.
- No more than two additional raw deadline misses per 1,000 fixtures.
- Accepted mean runtime within the existing ceiling.
- Legal actions and passing official SDK validation.

Use a fresh 768-or-more-fixture paired qualification. Do not tune or select tactics using qualification outcomes.

## DELIVERABLES

Produce:

1. Four standalone experimental tactic implementations.
2. A modular Tactical Opportunity Manager.
3. Individual regression tests and native match evaluations.
4. A report showing which tactics actually help and which fail.
5. A combined experimental controller only if integration is justified.
6. A final comparison against TITAN v10.0.
7. Documentation in `docs/tactics/`, retaining the existing Goalkeeper Power Play concept.

**Never modify `main`, `my-team/team.py`, or the frozen champion without explicit user authorization.**

## CENTRAL DESIGN PRINCIPLE

Our existing Guardiola/Klopp controller remains the normal football brain.

These four systems are special weapons. They should activate only when they create a real, measurable opportunity that the ordinary controller would otherwise miss.

**Build unconventional football intelligence that wins games—not merely unusual behavior.**