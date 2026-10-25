# Native head-to-head: v2 vs uploaded team (8).py

The new controller wins more games and points in this sample, but the points advantage is not statistically established and it records one additional raw deadline miss. **Do not treat it as a qualified replacement.**

## Fixed protocol

- Candidate: `replay-recovery-safety-v2`, source commit `3bf534fcc72c58fa698ac5140ef1cdb1e373d886`.
- Candidate SHA256: `7cb159d7547b4bb93303e4e01d593988ad633303c06b15bcc1fe07607bffc88a`.
- Uploaded team (8).py SHA256: `5b4a2c6638d6a92fe09c580f55b148cf91d592276a166254a7ab51a4fc90b957`.
- 16 newly chosen seeds, 2938064101–2938064116; all four candidate pitch/kickoff combinations per seed.
- 64 full native matches, one worker, 2,400 ticks each, engine 0.1.0, config `372990895c7eca2a`, unmodified 20 ms deadline and official failure policy.
- Both files were frozen before execution. No tuning, outcome-based stopping, timeout removal or result replacement. Both controllers passed official five-public-seed intake: 2,000 decisions each, zero exceptions and deadline misses.
- Native elapsed times and outcomes remain authoritative. Passive timing collection occurs outside the timed controller call. No controller source was edited during this comparison.

## Raw scheduled results

| Metric | New v2 | Uploaded team (8).py |
|---|---:|---:|
| Full matches | 64 | 64 |
| Wins–draws–losses | 31–7–26 | 26–7–31 |
| League points | 100 | 85 |
| Goals scored–conceded | 95–55 | 55–95 |
| Native pass completion | 74.07% (2577/3479) | 57.52% (1136/1975) |
| Derived uncollected passes | 385 | 302 |
| Turnovers | 279 | 325 |
| Controlled-ball ticks | 14.14% | 7.44% |
| Policy exceptions | 0 | 0 |
| Raw deadline misses | 1 | 0 |
| Mean decision, ms | 0.2090 | 0.1194 |
| Maximum decision, ms | 24.948 | 8.642 |

All 64 scheduled matches reached the full time limit. Each controller made 153,600 decisions. Both had zero invalid IDs, missing actions, non-finite values, clamped values, dropped debug payloads and rejected-kick validation events. Native pass metrics are included; derived uncollected passes equal attempted minus completed minus intercepted. More completed passes alone does not establish stronger match performance.

## Points uncertainty and reliability

The observed paired points difference is **+0.234375 per fixture**. The preregistered percentile bootstrap, resampling sixteen four-fixture seed blocks 10,000 times, gives a 95% interval of **[-0.421875, +0.937500]**. This includes zero. Neither the positive win-evidence criterion nor a reliable overall upgrade is established.

One additional raw miss in 64 fixtures scales to **15.625 additional misses per 1,000 fixtures**, above a +2/1,000 allowance when using team (8) as comparator. This head-to-head run is not the original multi-opponent qualification against frozen v10. The candidate has not been promoted.

## Timing diagnostic — not a replacement result

The sole raw miss is the candidate at tick 1,255 in seed 2938064102, candidate side 1 with kickoff: **24.948239 ms**. There is no associated policy exception. A separately recorded exact native fixture repeat has zero misses on both sides; that candidate decision measures **1.418024 ms wall** and **1.418679 ms thread CPU**. The original scheduled miss and result stay counted.

Cgroup counters show no CPU throttling increase during the scheduled cohort. The original slow call has no thread-CPU measurement, so a clean repeat and these counters do not establish whether the original spike came from the controller, garbage collection, scheduling or another cause. Its cause remains unresolved.

## Assignment breakdown

| Candidate assignment | Wins | Draws | Losses | Goals for–against |
|---|---:|---:|---:|---|
| Pitch side 0 | 18 | 0 | 14 | 48–24 |
| Pitch side 1 | 13 | 7 | 12 | 47–31 |
| Takes kickoff | 13 | 4 | 15 | 45–30 |
| Opponent kickoff | 18 | 3 | 11 | 50–25 |

The temporary recovery guard is active on 29,187 observed candidate decision ticks; the short carry plan is active on 4,751. Activation counts do not establish causal credit for goals or wins. This compares complete controllers; it does not isolate recovery, keeper safety, work limits, handoffs or finishing changes.

## Evidence and limits

- [Registration](registration.json), [full summary](summary.json), [64 scores](scores.csv).
- [Candidate intake](new-intake.json), [team (8) intake](team8-intake.json), [timing repeat](timing-repeat.json).
- [Evidence ZIP](evidence.zip) contains raw native results, frozen files, the executed harnesses, metadata and intake records.
- These are local head-to-head results against one opponent. They do not establish league ranking improvement or performance against Zamokuhle, Morare or the other league teams.
- `main`, active `my-team/team.py` and archived champions remain unchanged. Candidate `LOCK_LEAD=0`; uploaded team (8) retains its original settings.
