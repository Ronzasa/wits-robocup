# Tactic 01 — Goalkeeper Power Play

**Status:** Concept only — not implemented or validated  
**Category:** Late-game, high-risk attacking overload  
**Target implementation:** Existing Guardiola/Klopp controller (prefer the proven v10.0 descendant of the uploaded v9.1 source)  
**Experiment flag:** `KEEPER_POWER_PLAY`  
**Production:** Do **not** change `main/my-team/team.py` or submit this tactic unless the user explicitly approves after independent qualification.

## Idea

Use the goalkeeper (player 0) as a temporary **fifth outfield player** in selected late-game attacks, primarily as a passing and possession-recycling outlet rather than a routine striker. A fifth outfield option may improve combinations and overload opponent marking, but removing the goalkeeper from goal is an extremely costly risk.

The game rules permit this: every player can move and kick, there is no penalty area and no offside line. The agent sees its own goal at negative x and attacks toward positive x regardless of physical side.

## Proposed activation (experimental values, not optimized)

- The team is **trailing**, especially by one goal.
- **At most ~35 seconds** remain; strongest initial trial is the final **15–35 seconds** if the team is already in a sustained attack.
- The team has **credible secure attacking possession**, not merely the most recent touch; the ball is preferably in the opponent's half.
- There is no immediate opposing shot, loose-ball race loss, or imminent counterattack.
- The goalkeeper can reach a useful passing position in time to matter.
- Do not activate when drawing/winning in the initial variant; test such riskier versions independently, not in the first candidate.

Since the standard match is 2,400 ticks at 20 Hz (120 seconds), 35 and 15 seconds correspond to `time_remaining` approximately 0.292 and 0.125.

## Proposed movement and team coordination

1. Keep a **normal goalkeeper** outside the brief high-risk activation.
2. During the power play, advance player 0 carefully as a fifth passing outlet, generally **behind** the outfield attack and toward the midfield rather than leaving it permanently near the opponent's goal.
3. Extend **safe pass-option and receiver eligibility** to player 0 only while the power play is active; currently ordinary passing excludes player 0. Require the same legal launch, physically verified reception, cooldown, interception race and executable recipient movement as every other receiver.
4. Preserve normal goalkeeper clearance and defensive recovery logic outside the mode. Teammates should recognize the extra outlet and maintain complementary runs and at least one rest-defense position where tactically feasible.
5. On actual enemy control, an unsafe loose-ball forecast, a goal/restart, or expiration of the window, **command immediate recovery** toward the defended goal. Recovery is not instantaneous; a goalkeeper at x=-15 needs roughly four seconds just to travel toward x=-48 at the 8-unit/s speed cap, before acceleration and collisions.
6. Add a hysteresis/cooldown so the goalkeeper cannot oscillate rapidly between attack and goal on marginal possession changes.

## Important limitations

- **This is not proven to improve league points.**
- The keeper's forward position makes long-range empty-net goals much easier for an opponent; merely issuing a retreat command cannot undo that exposure.
- This tactic cannot be implemented effectively as one keeper movement target. It also needs mode state, passing eligibility and receiver/movement coordination.
- Simulate possible losing-possession outcomes conservatively; do not claim to know future opponent behavior.

## Evaluation before adoption

Create one isolated challenger based on frozen v10.0 and leave the active controller unchanged. Include an always-off baseline plus small, isolated activation variants (e.g. last 15 / 25 / 35 seconds). Choose thresholds **only on development seeds**, freeze them before qualification, and preserve rejected results.

Measure:
- Equalizers and comeback wins while trailing in the activation window.
- Opponent empty-net goals and concessions after keeper advance.
- Net **league points**, not just added touches or possession.
- Keeper distance from own goal, recovery time and possession turnover rate.
- All raw exceptions, invalid kicks, deadline misses and latency tails.

Use mirrored paired native fixtures against strong pressing/counterattacking opponents and frozen v10.0, including unseen seeds/opponent styles. Retain the original promotion gate: more points, strictly positive whole-seed bootstrap 95% lower confidence bound, zero policy exceptions, no repeated deadline failure, and <=2 extra raw deadline misses per 1,000 fixtures. **Explicit user authorization is required before any production promotion.**

## Decision log

- **2026-10-18:** Saved as the first proposed tactic in the isolated tactics playbook.
- **Next:** Gather other tactical ideas before choosing which to implement and test.
