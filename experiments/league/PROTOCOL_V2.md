# Pre-holdout revision to league selection

The original selection, original full-source plan, and all original candidate
files remain preserved. No final 830000-series holdout result has selected a
policy. Revision two has its own plan, selection labels and lock.

A code review found a material defect in `ray_cover`: clipping each guard's
projected y position independently can send two guards to exactly the same
point for a wide ball. This contradicts its intended minimum spacing. The
separate `ray_cover2` clamps the common screen centre before placing guards,
preserving spacing and the original outer bounds. The original source and its
results remain untouched. Geometry regression checks exercise actual policy
target requests and include the failing wide-ball case.

The fresh candidate set is ray_cover2, guardian, adaptive3 and the original
Monster control. The opponent set is the original thirteen plus the separate
OpenGap stress team, covering a forward-pressing, open attacking style. This
amendment fixes that set before any new primary selection fixtures.

Run `workflow_v2.py --stage selection` to write all source/infrastructure hashes
before playing custom formations on 822000..822002 and default formations on
822002..822004. Each policy faces 224 selection fixtures. The same fixed rule
chooses the strongest eligible new candidate by league points, then goal
difference, then lower mean decision time. Zero policy errors, zero forfeits
and legal actions are required. Timeouts remain included and reported.

`--stage lock` packages only the selected controller's name/version metadata
and freezes its SHA before holdout. The untouched final schedules are default
formations on 830000..830005 and custom formations on 830005..830010, under
fresh v2 labels. Each policy plays 560 final fixtures, with 280 per formation
mode, forty per opponent and ten seed clusters. Titan and Monster controls
play identical fixtures. All upper bounds are exclusive.

`--stage report` requires complete aligned fixtures and retains every fault.
It writes `FINAL_REPORT_V2.json` and the shared final README. Evidence is for a
local tactical pool; school leaderboard dominance remains unverified.

## Counter-definition correction before the release lock

The first lock attempt used every nonzero `validation` counter as an action
eligibility failure. This incorrectly treated `rejected_kicks` as an invalid
payload. The SDK's `PlayerAction` documentation explicitly counts a kick that
is unavailable because of range or cooldown; player movement and simultaneous
actions can make a previously available kick unavailable. The official
`student-sdk/soccer/validate.py` does not reject submissions for this counter.

The structural-action eligibility gate is therefore precisely
`missing_actions`, `non_finite_values`, and `invalid_player_ids`, along with the
unchanged zero-policy-error, zero-forfeit and valid-protocol requirements.
The experiment retains its complete-action requirement even though the SDK
only warns about missing actions. The SDK does not fail `clamped_values` and
only warns about `dropped_debug_payloads`; neither is a structural failure.
Every unavailable kick, clamp, debug drop and timeout remains in the raw data
and full reported metrics.

This corrects the counter definition to the documented SDK semantics before
the release lock and any final holdout. It changes no controller, source hash,
manifest, score, fixture, point-ranking criterion or tie-break rule. Existing
selection evidence is reused in full; no fixture needs to be rerun.
