# Experiment ledger

All named pool files are new MONSTER implementations, not TITAN subclasses or
copies. The immutable hashed sources used in every match are under
`candidates/`; full per-fixture metrics are in `results/` and tabulated by
`lab.py --scorecard`. Screens used four training seeds × four fixture types
(16 matches), unless a report explicitly says otherwise.

| Versions | Hypothesis / architecture | Observed selection result and disposition |
|---|---|---|
| v01 | Predictive field pressing, short control, conservative shot/pass races | 0W/3D/13L, 19–32 goals; rejected. High possession mostly reflected TITAN protecting a lead. |
| v02 | More pressure, faster central start, aggressive finishing | 0/1/15, 26–41; rejected. More attacks did not compensate for conceding first. |
| v03 | Deeper cover and advanced keeper | 0/8/8, 20–28; fewer losses but no wins. |
| v04 | Protect an early lead | 0/8/8, 25–33; ineffective when MONSTER rarely scored first. |
| v05 | Compact low defense | 0/12/4, 16–20; draw-heavy and not strong enough. |
| v06–v07 | Robust simultaneous-kick planning, faster touches | First actual TITAN defeats: each won 2 of 16. Kept the contested-kick idea, not these complete policies. |
| v08 | Contested kicks plus fortress | 0/10/6; rejected. |
| v09–v10 | Two players sharing goal coverage | 0/10/6 and 1/7/8; rejected. Roles/attack balance remained weak. |
| v11 | Four-cover counterattack with one outlet | 6/2/8, 23–28; first credible alternative architecture. |
| v12 | Hold the closer line after taking a lead | 4/5/7; worse than v11. |
| v13 | Release on seeing an opposing wall | Same 6/2/8 as v11; condition rarely activated because TITAN kept attacking MONSTER's visible wall. |
| v14 | Release players when trailing | 6/2/8 but 19–30 goals; weakened defense, rejected. |
| v15–v16 | Bank clearances, five-player lead protection, optional release | 1/9/6 and 1/6/9; rejected. Unreliable outlet collection and defensive rearrangement. |
| v17–v18 | Explicit public-observation keeper movement model, longer shots | v17 reached 7/0/9 but had six timeouts; v18 3/2/11 with three timeouts. Rejected as implementations under the 20 ms rule. |
| v19 | Bounded cheaper keeper model | 5/3/8, 18–22; legal in screen, no improvement over the simpler shell. |
| v20 | Isolated five-player lead wall | 1/6/9, 21–33; rejected. |
| v21 | Closer fixed outlet instead of following every side change | 8/1/7, 28–24. Validation: 17/14/9, 61–51; passed >50% of decisive games on fresh selection seeds. |
| v22 | Fixed outlet plus keeper model | 7/1/8; less reliable than v21. |
| v23 | Fixed outlet plus active near-post pressure | 9/7/0, 29–13. Validation: 29/8/3, 73–22; major defensive improvement over v21. Rare validation timing overruns remained. |
| v24 | Near-post pressure plus keeper model | 7/8/1 in screen; 28/9/3, 67–25 in validation with one timing overrun. Extra complexity did not beat v23. |
| v25 | Same near-post policy with unnecessary waiting-outlet trajectory allocation removed | Validation: 29/8/3, 72–23; zero errors/timeouts, mean 0.162 ms, max 18.493 ms. Selected and frozen before holdout. |

These are complete strategy comparisons, not claims that every changed
parameter was causally isolated. The closest tactical ablation is v21 versus
v23 on the identical 40 validation fixtures: adding near-post pressure changed
17/14/9 to 29/8/3, raised goals from 61 to 73 and reduced concessions from 51
to 22. v25 preserves that architecture while reducing allocations; timing
budgets mean it is not claimed to be bitwise action-identical under all loads.

## Evidence of TITAN weaknesses

The first v23 replay, seed 700000, candidate absolute side 0 with kickoff,
finished 1–1. The official event log records TITAN kickoff fouls at ticks **19**
and **1762**; the latter follows TITAN's goal at tick 1750 and MONSTER's restart.
MONSTER had no fouls. See the corresponding `.diagnostics.json` for exact events.

Source review locates the missing protection in the active wall specialist:
`_siege_act` can move its carrier toward a ball on the opponent's kickoff
without applying normal-play restart protection. This is a demonstrated
opponent-policy weakness, not engine tampering.

TITAN's siege predictor moves every opponent toward an assumed five-slot
fixed wall, even when observations show four cover players and a distant
outlet. MONSTER's moving near-post defender violates that assumption. The
paired v21/v23 result supports a tactical weakness in those fixed-slot corner
attacks. It does not prove that this is the only cause of every goal difference.

The original general keeper-threshold hypothesis was **not established** as
a reliable winning method. Keeper-model candidates were slower and did not
beat the simpler post-pressure strategy; the final model is disabled.

No source, replay or private algorithm for Gabriel Behane or Kevin Ebrahim was
used. Strength against frozen TITAN does not establish leaderboard strength;
the independent holdout and other-opponent results are reported separately.

## Blue Team follow-up, after MONSTER's locked holdout

The separate `blue-pool/` preserves three small TITAN derivatives and their
builder. On 16 new training fixtures MONSTER went 11/4/1 against original
TITAN, 10/6/0 against kickoff protection alone, 7/6/3 against a goal-side
outlet reserve, and 3/10/3 against both changes. Kickoff protection alone
removed the foul but worsened goal difference; it is not an isolated playing
strength improvement.

The combined candidate's fresh 20-fixture comparison reduced MONSTER's record
from 14/5/1 (31–6) to 10/7/3 (27–10), with zero restart fouls. However, it lost
3/11/6 (32–34) directly to original TITAN. Its official-baseline record and
scores exactly matched frozen controls: 59/1/0, 62–3 across 60 fixtures.
All Blue tests were free of policy errors/timeouts, and official check and
validation passed. It remains an experimental countermeasure and is **not
promoted as a generally stronger TITAN**. The validated submission is intact.

See `REPORT.md` for holdout conclusions and `results/blue-*.json` for the
training, fresh paired tests and original-TITAN baseline controls.
