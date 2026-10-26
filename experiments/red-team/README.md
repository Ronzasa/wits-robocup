# Operation MONSTER

The independent Red Team submission is **`monster/team.py`**, class `Monster`,
version `v25-fast-post`. The validated Blue Team is still **`../../my-team/team.py`**,
byte-for-byte unchanged. No engine/SDK changes, master changes or competition
submissions are part of this laboratory. After research completed, the user
authorized committing and pushing the complete archive on the experimental
branch. `.gitattributes` preserves tested agent bytes and recorded hashes.

## Isolation and recovery

This directory is the isolated environment on the existing experimental branch.
`frozen-titan/team.py` is an exact recovery copy of the validated TITAN.

- TITAN SHA-256: `5c73068b5e574093e9e1afce972ff8b3546b484c103505c9e79d80772ac6299d`.
- Frozen MONSTER SHA-256: `1bf09f5fcab940eae8f387ef36030d302dfe9e52aa6ae0fe82f48742ea6e85b7`.
- `protected.json` records hashes for TITAN, its frozen copy, the official
  Windows engine binaries, SDK Python files and course configuration.
- Every benchmark verifies those hashes before and after play. The benchmark
  runs an immutable copy under `candidates/<source-hash>/team.py`.
- `pool/` preserves named standalone strategy versions; `build.py` refuses to
  overwrite them. Failed experiments remain available for review.

The agent itself imports only `math`, `time.perf_counter` and the official
`soccer` SDK. It reads public observations and emits five legal player actions.
It performs no file, process, network, opponent-source or engine-state access.
The experiment harness may read replays and source files offline; the agent
never imports that harness or TITAN.

## Protocol

All competitive games use the bundled official engine, engine version 0.1.0,
the unchanged course config hash `372990895c7eca2a`, five players, **2,400 ticks**
and **20 ms per decision for both teams**. There are four fixtures per seed:
candidate absolute side 0 or 1, crossed with absolute kickoff owner 0 or 1.

This is explicit because SDK `evaluate(swap_sides=True)` swaps kickoff along
with side and therefore always gives its evaluated team kickoff. The new
harness calls official `play_match` for each of the four combinations.

Scores and per-team statistics in result rows are normalized to candidate
first; `candidate_side`, `candidate_kickoff` and `absolute_score` retain the
mapping to the actual engine fixture. Engine `team_ids`/`outcome` remain in
absolute order and must be interpreted through that mapping. Summary wins,
draws and losses are computed from normalized scores, not engine outcome text.

Predeclared, disjoint seed partitions (upper endpoints exclusive):

| Split | Seeds | Purpose |
|---|---|---|
| train | 700000..700020 | Candidate generation; initial screens used first four seeds |
| validation | 710000..710010 | Finalist selection: 40 fixtures per candidate |
| holdout | 730000..730025 | Locked final candidate: **100 fixtures**, 25 seed clusters |
| generalization | 740000..740010 | Other opponents and separate Blue Team checks |

`holdout-lock.json` is written before the first holdout match; a different
candidate hash is refused thereafter. No candidate is tuned from holdout
outcomes. Repeating a fixture is a reproduction, not additional independent
evidence. Raw `.jsonl` results are flushed after every fixture, and complete
`.json` reports contain all metrics and source hashes.

The report gives Wilson intervals for descriptive match win rates and also
seed-cluster bootstrap intervals/goal-difference intervals, because the four
fixtures sharing a seed are correlated. Small training samples are selection
evidence, not proof of dominance. A measured 70% win rate is not a guarantee
that the underlying win probability exceeds 70%.

## Reproduction from the repository root

Use a fresh `--label` to avoid overwriting existing evidence. End seeds are
exclusive. All commands below use the official SDK/engine through bootstrap.

```powershell
python experiments/red-team/lab.py --verify
python experiments/red-team/lab.py --audit-holdout
python launch.py check experiments/red-team/monster
python launch.py validate experiments/red-team/monster --against tactical --ticks 2400 --json
python experiments/red-team/lab.py --team pool/v25-fast-post/team.py --split validation --label reproduce-validation
python experiments/red-team/lab.py --split holdout --label reproduce-holdout
python experiments/red-team/lab.py --split generalization --seeds 740000..740005 --opponents balanced tactical possession experiments/titan-original/team.py experiments/titan-buggy/team.py pool/v21-close-outlet/team.py pool/v06-duel/team.py --label reproduce-generalization
python experiments/red-team/lab.py --scorecard
```

Build and screen a new independent variant, preserving its source:

```powershell
python experiments/red-team/build.py new-variant --base pool/v25-fast-post/team.py --set CARRY_SPEED=8.0
python experiments/red-team/lab.py --team pool/new-variant/team.py --seeds 700004..700008 --label new-variant-training
```

Do not use the exposed final holdout to select a new variant. Reserve new
seeds for any later research cycle. The lab deliberately refuses a different
source on its existing holdout partition.

Inspect actual recorded evidence:

```powershell
python experiments/red-team/lab.py --diagnose-result experiments/red-team/results/grid10-v23-post-pressure.json
python experiments/red-team/lab.py --inspect-replay experiments/red-team/replays/grid10-v23-post-pressure-700000-s0-k0.rep
```

The controlled `--probe-goal` experiment uses legal actions in the official
engine to test shot geometry with idle opponents. It is a partial-match physics
diagnostic, **not a competitive result**. It confirmed that aiming at y=6.8
scored in that setup, whereas aims at y=7.0 and above did not.

## Selected strategy

The winning configuration is an adaptive four-player goal screen with a stable
wide counterattacking outlet. Near a threatened post, its nearest covering
player closes down the ball instead of staying in a fixed wall slot. The
outlet uses predictive interception, short-touch rollouts, impulse-aware shots
and full-power planning when both teams can kick simultaneously. The near-post
rule and fixed outlet were selected by actual match comparisons.

The file retains switches for other architectures explored in the pool, but
the frozen winning configuration has the costly speculative keeper shot model,
two-keeper formation, bank clearances and five-player lead wall **disabled**.
Its optional searches have a 7 ms budget. A fixed receiver target avoids
unnecessary trajectory allocation while it waits for a clearance.

Timing includes Python and OS scheduling on this Windows machine. Search
budgets can cause different choices under different CPU load; exact bitwise
match reproduction across machines is not promised. Exploratory overruns are
retained in the scorecard rather than hidden. Official checks and the final
holdout are reported separately.

See **`REPORT.md`** for final conclusions, **`SCORECARD.md`** for every recorded
competitive run, **`EXPERIMENTS.md`** for rejected approaches, and
**`THREAT_MODEL.md`** for source observations versus tested hypotheses.

## Separate Blue Team countermeasures

`blue_build.py` creates three small TITAN derivatives from the frozen source:
`blue-a-kickoff` guards the specialist's opponent restart, `blue-b-reserve`
keeps one siege support player goal-side of an observed outlet, and
`blue-c-combined` combines both. They live under `blue-pool/`; the validated
submission is never a build target. The script refuses to overwrite snapshots.

The combined candidate was selected on separate training fixtures. Fresh
paired checks against MONSTER and broader checks can be reproduced with:

```powershell
python experiments/red-team/lab.py --seeds 740005..740010 --split generalization --opponents titan blue-pool/blue-c-combined/team.py --label reproduce-blue-paired
python experiments/red-team/lab.py --team blue-pool/blue-c-combined/team.py --seeds 740005..740010 --split generalization --opponents titan balanced tactical possession --label reproduce-blue-generalization
python launch.py check experiments/red-team/blue-pool/blue-c-combined
python launch.py validate experiments/red-team/blue-pool/blue-c-combined --against tactical --ticks 2400 --json
```

These Blue checks are a separate research stage, not additional MONSTER
holdout matches. Twenty fresh paired matches offer preliminary evidence,
not a guarantee of improvement across all opponents. See the final report.
