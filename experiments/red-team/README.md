# Operation MONSTER

The current independent agent is **`monster/team.py`**, class `Monster`,
version **`v51-stream-post`**, SHA-256
`0d9be04ce17bbb21f73d31ac6ca8a2b9afde81cee9ae865eff99f6564b9151b6`.
It is an exact copy of the tested immutable `pool/v51-stream-post/team.py`.
The previous release is preserved in `pool/v25-fast-post/team.py`.

Validated TITAN remains **`../../my-team/team.py`**, byte-for-byte unchanged,
SHA-256 `5c73068b5e574093e9e1afce972ff8b3546b484c103505c9e79d80772ac6299d`.
The separate Blue candidates remain experimental. No competition submission
or replacement of validated TITAN is performed. The user authorized archiving
both agents and all evidence on the experimental Git branch.

## Measured improvement

These are matched **100-game holdouts per opponent and policy**, using 25
previously untouched seeds, both sides and both kickoff owners:

| Opponent | Old v25 W/D/L | New v51 W/D/L |
|---|---:|---:|
| Frozen TITAN | 73/24/3 | **86/14/0** |
| Patched Blue C | 38/33/29 | **46/50/4** |
| MONSTER v21 | 19/56/25 | **37/59/4** |
| MONSTER v25 | 37/27/36 | **57/30/13** |
| Total | 167/140/93 | **226/153/21** |

Old v25's last row is its self-play control under the same jittered fixtures.
The new policy earned **831 league points versus 641**. Paired improvement:
**+0.475 points/game**, seed-cluster bootstrap 95% interval **+0.373 to +0.583**.
TITAN goals changed from **173–61 to 178–26**. Full pooled goals changed from
**527–397 to 465–142**: much lower conceding is the main source of the gain.

The six official baselines also produced **117W/3D/0L in 120 games** for each
release. There are tradeoffs: more draws against two older TITAN versions,
and fewer blowout goals in several baseline matchups. v51 is still draw-heavy
against strong wall agents. Leaderboard superiority is unverified.

See [the report](ROUND2_REPORT.md), [paired scorecard](ROUND2_RESULTS.md),
[full audit](ROUND2_AUDIT.json), [research/rejections](ROUND2.md), and
[every recorded experiment](SCORECARD.md). First-round records remain in
[RELEASE1.md](RELEASE1.md), [REPORT.md](REPORT.md), and [EXPERIMENTS.md](EXPERIMENTS.md).

## Strategy and validity

Four defenders cover the goal with a stable wide counterattacking outlet.
The near-post guard stays closer to the mouth instead of chasing a wide ball
too far out. Predictive interception streams trajectory samples until a
reachable frame is found; repeated-use pass paths remain materialized.
More elaborate attack/keeper/contact models were tested and rejected.

The single-file controller imports only `math`, `time.perf_counter` and the
official `soccer` SDK. It uses public match observations and its own resettable
state. It has one `TeamController` subclass and returns five player actions.
No runtime file/source access, opponent identity checks, hidden state, seed
branches, engine modifications or additional dependencies are used.

Official `check` and five-match `validate` passed. Both teams' **20 ms**
deadlines are enforced in all competitive matches; optional searches have a
7 ms budget. The 400-match new holdout recorded zero exceptions and **three
elapsed-time timeouts in 960,000 decisions**. Two more occurred in its 160
generalization games; these remain in the raw results. Rare long stalls have
not been conclusively diagnosed. The reports do not claim that every
observed decision stayed under 20 ms.

## Protocol and reproduction

All competitive results use the unchanged official Wits engine **0.1.0**,
course config hash **372990895c7eca2a**, five players and **2,400 ticks**.
Every seed explicitly crosses absolute side 0/1 and kickoff owner 0/1.
SDK side-swapping alone does not balance kickoff ownership.

Scores/stats are candidate-first. `absolute_score`, `candidate_side` and
`candidate_kickoff` preserve the mapping; native team names/outcome strings
remain absolute. Wins and losses are calculated from normalized scores.

Round-two seeds (upper endpoints exclusive): training 750000..750012,
selection 760000..760010, final holdout 770000..770025, generalization
780000..780010. The fixed v25 control intentionally shares final holdout
seeds for paired comparison. It accepts only the predeclared old source hash
and cannot run before the new finalist is locked. `round2-selection.json`
records the decision before holdout exposure; the lock refuses other hashes.

From the repository root:

```powershell
python experiments/red-team/lab.py --verify
python launch.py check experiments/red-team/monster
python launch.py validate experiments/red-team/monster --against tactical --ticks 2400 --json
python experiments/red-team/round2_build.py --verify-stream
python experiments/red-team/round2_build.py --audit
python experiments/red-team/lab.py --scorecard
```

Audit validates the archived 800 paired primary fixtures, source hashes,
balanced starts, complete matches and action validity. Re-run benchmarks with
**fresh labels**; existing results are never overwritten:

```powershell
python experiments/red-team/lab.py --team pool/v51-stream-post/team.py --split round2-holdout --opponents titan blue-pool/blue-c-combined/team.py pool/v21-close-outlet/team.py pool/v25-fast-post/team.py --label reproduce-r2-holdout
python experiments/red-team/lab.py --team pool/v25-fast-post/team.py --split round2-holdout-control --opponents titan blue-pool/blue-c-combined/team.py pool/v21-close-outlet/team.py pool/v25-fast-post/team.py --label reproduce-r2-control
python experiments/red-team/lab.py --sweep pool/v25-fast-post/team.py pool/v51-stream-post/team.py --split round2-generalization --seeds 780000..780005 --opponents balanced tactical possession structured_attack man_marking ball_chaser experiments/titan-original/team.py experiments/titan-buggy/team.py --label reproduce-r2-generalization
```

The same fixture repeated is reproduction, not new independent evidence.
Elapsed-time searches and OS load can change exact outcomes. Reported
uncertainty resamples the **25 seed clusters**, preserving their correlated
side/kickoff/opponent fixtures. Fault-free subsets are post-hoc sensitivity
checks; all fixtures remain in the primary scorecard.

## Isolation and future experiments

`protected.json` verifies validated TITAN, its recovery copy, SDK, engine and
configuration before/after matches. Source snapshots under `candidates/` are
immutable; benchmarks execute those copies. `.gitattributes` preserves agent
bytes despite Windows line-ending conversion. `pool/` retains all candidates.

`build.py` creates a new standalone parameter variant, and refuses to overwrite:

```powershell
python experiments/red-team/build.py next-trial --base pool/v51-stream-post/team.py --set POST_MAX=7.1
python experiments/red-team/lab.py --team pool/next-trial/team.py --split round2-train --seeds 750008..750012 --label next-trial-training
```

Reserve a new independent holdout before selecting another release. The old
and second-round holdouts are exposed and must not select a new policy.
`round2_build.py` preserves the source transformations for all 26 new variants;
its generation flags intentionally refuse existing snapshot names.
Use `--verify-existing` with each generation flag to check archived builds
without writing files, for example `--stream --verify-existing`. All 26 were
verified byte-for-byte; see `checks/build-reproducibility.json`.
`lab.py --compare BEFORE AFTER` compares identical fixtures. Optional
`--cpu-profile` is an instrumented timing diagnostic, excluded from the
competitive scorecard. Replay diagnostics and the earlier goal-mouth probe
are also distinct from full competitive matches.
