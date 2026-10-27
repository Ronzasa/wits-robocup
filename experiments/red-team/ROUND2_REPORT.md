# MONSTER second release: findings

The selected controller is **v51-stream-post**, standalone source
`pool/v51-stream-post/team.py`, SHA-256
`0d9be04ce17bbb21f73d31ac6ca8a2b9afde81cee9ae865eff99f6564b9151b6`.
It was selected and recorded in `round2-selection.json` before the first
second-round holdout fixture. No policy change followed exposure of that
holdout. The first-release source remains in `pool/v25-fast-post/team.py`,
SHA-256 `1bf09f5fcab940eae8f387ef36030d302dfe9e52aa6ae0fe82f48742ea6e85b7`.
Validated TITAN remains byte-for-byte unchanged.
The exact selected bytes have now been promoted to **`monster/team.py`**.

## What changed and why

The main tactical fix limits the near-post defender's outward target from
**9.5 to 7.3** field units from the centre of the goal. Actual replay evidence
showed the old guard following a wide ball too far out, leaving the inside of
the post open. The closer limit still reaches the corner attacker but leaves
less distance to recover when a shot turns inward. The ordinary four-cover,
wide-outlet counterattack remains intact.

Interception now consumes a streaming trajectory and stops forecasting as
soon as it finds a reachable frame. Passes needing repeated path comparisons
still use materialized paths. Redundant wall counting is skipped when its
release feature is disabled. These changes reduce unnecessary allocation;
they do not claim to eliminate operating-system scheduling delays.

The geometric refactor passed **1,000 deterministic cases**, with exactly
equal path samples and interception targets. Whole-match results can still
differ because both controllers use elapsed-time search budgets. The
equivalence check is in `checks/stream-equivalence.json`.
All 26 candidate builders also reproduced their archived source bytes
exactly; evidence is in `checks/build-reproducibility.json`. No candidate
source was rewritten during those checks.

## Actual research and selection

Twenty-six new versions, v26–v51, were built and executed. Extra attackers,
shot-first duels, defender-contact finishing, clearance searches, different
outlet lanes, fast-open dribbling and mark-triggered pace were tested. None
justified replacing the simpler coverage policy across the broader pool.
See `ROUND2.md`, `round2_build.py`, the immutable `pool/` files and the complete
`SCORECARD.md`; rejected experiments and timing overruns are retained.

The round executed **2,432 full competitive fixtures**, including paired
controls and reused selection seeds, plus the separate instrumented timing
diagnostic and official validity checks. That is an execution count, not
2,432 independent samples; primary uncertainty uses 25 seed clusters.

On 160 validation fixtures per policy, covering TITAN, patched Blue C, v21
and v25, old v25 scored **69W/56D/35L, 231–169 goals, 263 league points**.
Selected v51 scored **101W/52D/7L, 202–52 goals, 355 points**. Thus the gain
primarily came from conceding less; scoring did not increase. The simpler
v36 tactical prototype scored 359 points. v51's streaming implementation had
comparable selection performance and avoided generating unused path frames.

## Locked new holdout

Seeds **770000–770024** were reserved before this round's first match. Every
seed crosses both field sides and both kickoff owners, with the unchanged
official engine/config, 2,400 ticks and an enforced 20 ms deadline for both
teams. Every opponent has **100 complete fixtures**; none was rerun or removed.

| Opponent | v51 W/D/L | Goals | Mean GD |
|---|---:|---:|---:|
| Frozen TITAN | **86/14/0** | **178–26** | **+1.52** |
| Patched Blue C | 46/50/4 | 91–26 | +0.65 |
| MONSTER v21 | 37/59/4 | 82–39 | +0.43 |
| Old release v25 | **57/30/13** | **114–51** | **+0.63** |
| Total | **226/153/21** | **465–142** | **+0.8075** |

The old release was evaluated on exactly those fixtures as a fixed paired
control. It scored **167W/140D/93L, 527–397 goals, 641 league points**, versus
v51's **226W/153D/21L, 465–142 goals, 831 points**. Paired mean improvement is
**+0.475 league points/game**, seed-cluster bootstrap 95% CI **+0.373 to +0.583**;
mean GD improves **+0.4825**, CI **+0.373 to +0.590**. All 800 fixtures passed
the protocol audit. `ROUND2_RESULTS.md` and `ROUND2_AUDIT.json` preserve the
per-opponent before/after comparison, timing and uncertainty.
The four opponents are related policies; they are not four independent
championship strategy families.

Against TITAN on these matched seeds, old v25 scored **73W/24D/3L, 173–61**;
new v51 scored **86W/14D/0L, 178–26**. The paired points/game gain is **+0.29**,
CI **+0.12 to +0.46**. In each of the four opponent comparisons the advantage
remains positive when any fixture with a policy failure in either arm/team
is excluded. Those subsets are descriptive sensitivity checks; all fixtures
remain primary. On the 79 fault-free TITAN pairs, new v51 scored 67W/12D/0L.

## Separate generalization and tradeoffs

Both releases played the same 20 fixtures per opponent, five fresh seeds
780000–780004 crossed with both sides/kickoffs. No policy was tuned afterward.

| Opponent | Old v25 W/D/L | New v51 W/D/L | Old goals | New goals |
|---|---:|---:|---:|---:|
| balanced | 20/0/0 | 20/0/0 | 114–0 | 105–1 |
| tactical | 18/2/0 | 18/2/0 | 44–7 | 36–2 |
| possession | 20/0/0 | 20/0/0 | 122–0 | 125–0 |
| structured_attack | 20/0/0 | 20/0/0 | 76–1 | 67–3 |
| man_marking | 20/0/0 | 20/0/0 | 142–0 | 141–0 |
| ball_chaser | 19/1/0 | 19/1/0 | 87–6 | 80–2 |
| Older TITAN, original | 16/4/0 | 14/6/0 | 33–11 | 27–6 |
| Older TITAN, buggy wall | 16/4/0 | 14/6/0 | 33–11 | 27–6 |

The six official baselines' points are unchanged: **117W/3D/0L** each.
New goals were **554–8**, versus old **585–14**. Several weaker-opponent
blowouts became smaller. Both older TITAN files produced **two additional
draws per 20 fixtures** in place of wins, an actual selection-policy tradeoff;
they are closely related versions, not independent families. No new policy
was built to erase this unfavorable result. The release is retained for its
large, independently measured gain over the primary four-opponent pool.

## Deadline and validity evidence

Official `check` passed. Official five-match `validate` against tactical
passed with 12,000 decisions, mean **0.068 ms**, maximum **3.631 ms**, no
warnings, exceptions, deadline overruns, missing actions or non-finite values.
Exact outputs are in `checks/r2-v51-check.json` and
`checks/r2-v51-validation.json`.

The promoted `monster/team.py` was checked again at its actual release path.
Both commands passed: five validation matches, 12,000 decisions, mean
**0.061 ms**, max **2.073 ms**, zero warnings/errors/overruns. Exact outputs
are `checks/r2-release-check.json` and `checks/r2-release-validation.json`.

The 400-match new-policy holdout had **zero policy exceptions**, but **three
elapsed-time deadline overruns in 960,000 decisions**. They remain in the
primary results: one versus v21 (max **59.192 ms**) and two versus v25
(max **32.692 ms**). Against TITAN the maximum was **8.771 ms**, with zero
timeouts; against Blue C it was **12.299 ms**, also zero timeouts. The official
20 ms failure policy applied in every fixture. This is not a claim that
every observed call stayed below 20 ms.

The matched v25 control had **14 timeouts** over its 400 primary fixtures,
versus v51's three. Mean decisions were **0.147 ms to 0.123 ms** across that
pool. These are full-policy observations, not an isolated proof of a specific
optimization's effect. Generalization added two v51 timeouts: man_marking
(max 67.418 ms) and the older buggy TITAN (max 108.829 ms). Five timeouts
therefore remain across the 560 final evaluation games (1,344,000 decisions).

Fresh validation also recorded one isolated v51 overrun of 102.227 ms. An
instrumented 16-match timing diagnostic had no overruns (max 9.717 ms), but did
not reproduce the long stalls. Windows thread CPU measurements were coarse
(15.625 ms steps), so those logs do not establish the cause. Scheduling is a
hypothesis, not a proven explanation. The agent keeps a 7 ms optional-search
budget; CPU time limits were never relaxed and no engine/SDK file was edited.

## Limits of the result

The independently held-out TITAN matchup is strong, including **no defeats
in 100 games**. v51 also directly beat its previous release. It does not
uniformly dominate the tougher pool: Blue C and v21 produced many draws.
The architecture is still a defensive counterattacker, not a possession or
pressing team. No source or verified matchup evidence for Gabriel Behane or
Kevin Ebrahim was available, so leaderboard superiority is unverified.

The holdout was not used to tune another policy. The complete frozen sources,
raw JSON/JSONL outcomes, replay samples, checks and reproduction scripts are
preserved. The original `my-team/team.py` remains the validated TITAN.
