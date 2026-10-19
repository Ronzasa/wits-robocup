# Goalkeeper tactics — second development round

**Decision: RETAIN_V10_REJECT_BOTH.** Both candidates remain experimental. The active v10.0 source and main were not modified.

## Frozen experiment

Four unused development seeds × six fixed opponent styles × both sides × both kickoffs = 96 full fixtures per source; 288 native matches total. Power and trap each played independently against the same frozen v10 controls. Every match used 2,400 ticks, the original engine/configuration and the native 20 ms deadline. Pinball Slingshot and Cooldown Ambush were false in every tested source. Source/opponent hashes and seed exclusions were frozen before the run in `goalkeeper-r2-development-protocol.json`.

The first attempted run was interrupted after regression failures identified two overly broad edits: recovery movement replaced the v10 keeper command, and stranded-keeper detection lacked an adjacent observation. Both were corrected before this final run. Its allocated seeds are excluded, its protocol and partial native records retained, and no partial score was used to tune the final source. Regression runs briefly overlapped early final fixtures; raw deadline records are retained without waiving any misses.

## Changes

- Power play separates entry eligibility from continued possession, retaining verified return flights and backward recycling. Loss of possession, a ball behind the keeper, missing cover, score changes, expiry and the minimum recovery window still cancel it. Existing travel, fastest counter-flight and cover-arrival calculations govern late trailing activation. Recovery delegates to the unchanged v10 keeper. Cover becoming the nominal chaser alone no longer cancels while our team retains possession.
- Keeper return passes still require the existing carrier-contact, dense trajectory, opponent race, teammate body-interference and first-touch checks. A space bonus permits safe recycling only with at least ten metres of receiver space. Keeper distribution uses the existing verified v10 kick selector.
- Trap detection observes adjacent ticks and recognizes an advanced keeper while braking or turning. Two receivers, three leads and three launch speeds are searched; every pass must still have a verified collection beyond the keeper. Goal-bound v10 finishes retain priority. The trap can challenge an existing forward pass, subject to the existing pass/carry score floor. The established shot selector supplies the open-goal finish.

## Competitive outcomes

| Source | Matches | Points | W–D–L | GF–GA | Raw deadline misses | Policy errors |
|---|---:|---:|---|---|---:|---:|
| v10 | 96 | 162 | 48–18–30 | 206–94 | 0 | 0 |
| power | 96 | 158 | 47–17–32 | 202–91 | 0 | 0 |
| trap | 96 | 165 | 49–18–29 | 206–94 | 0 | 0 |

All outcomes above are original raw native matches. Timeout repeats are stored separately; they do not erase misses or replace the raw competitive table. Accepted comparisons and the original gates are retained in the JSON report. Four seed blocks are development evidence, not a league-performance guarantee.

| Candidate | Accepted points vs v10 | Paired PPM delta [95% whole-seed interval] | Mean decision ms | Development gate |
|---|---|---|---:|---|
| power | 158 vs 162 | -0.041667 [-0.093750, +0.000000] | 0.268541 | REJECT |
| trap | 165 vs 162 | +0.031250 [+0.000000, +0.093750] | 0.269237 | REJECT |

## Actual tactical commands

Counts below are under-deadline accepted commands from original matches, grouped into episodes after gaps longer than five ticks. A run is not a collection; a selected pass is not a completed pass or a caused goal. Native goals/concessions and league points above determine competitiveness. Tick counts, examples, total native passes/completions and five-second goal/turnover associations are retained in JSON, with associations explicitly non-causal.

### power

`{"power_active": 11, "power_advance_tick": 19, "power_cancel": 18, "power_home": 19, "power_recovery_tick": 18, "power_start": 19}`

Native passes: 3780 attempted, 2159 completed; turnovers: 564. Reproduced candidate deadline failures: 0.

### trap

`{"trap_run": 5}`

Native passes: 3790 attempted, 2158 completed; turnovers: 558. Reproduced candidate deadline failures: 0.

## Interpretation and decision

Power play issued 2,639 advance/active movement commands across 19 episodes,
with 11 transitions into the active state, but **zero `power_pass` commands**.
Retaining an attack longer therefore did not establish a working goalkeeper
passing network. Its four-point loss rejects this candidate despite three
fewer concessions.

Trap issued 28 run commands across five episodes but **zero `trap_pass`
commands**. Its three extra points were entirely against `v10-counter` (23 →
26); points against `aggressive-keeper` were unchanged (22 → 22). Total goals
and concessions were unchanged. Its paired 95% interval starts at zero, so
this is insufficient evidence of a competitive improvement or of executable
open-goal exploitation. Existing v10 shots are not relabeled as trap goals.

**Both changes are rejected for competitive use. No integrated candidate or
fresh qualification was run.** The user's effectiveness goal has not been
established by these experiments. Their code and negative evidence are retained
for review; v10 remains the champion.

## Verification and reproduction

All 126 regressions passed, including six new tests for backward recycling, verified-flight retention, opponent-touch cancellation, ball-behind-keeper recovery, braking keepers and observation gaps. The original unchanged-champion hash, physics/shot/keeper/cover AST checks, legal-action checks and all-off equivalence tests remain in force.

`python tools/titan_x/build.py` rebuilds the all-off controller and the two goalkeeper standalones. The archived pinball and ambush files are untouched. Run `PYTHONPATH=student-sdk python -m unittest discover -s tests -q` after installing the bundled native extension. Reproduce the paired development with `PYTHONPATH=student-sdk python tools/benchmarks/run_titan_x.py --protocol docs/tactics/goalkeeper-r2-development-protocol.json --out /new/output/path`. Use one native worker.

The evidence archive `tests/fixtures/titan-x-goalkeeper-r2-evidence.zip` retains final and interrupted native records, source snapshots, intakes, raw timings, exact repeats, protocols, test logs and per-file hashes.

Fresh qualification requires more points, a strictly positive paired whole-seed lower bound, and all safety/runtime gates. Failed changes are rejected for competitive use; retaining their source on the experimental branch is not a promotion.
