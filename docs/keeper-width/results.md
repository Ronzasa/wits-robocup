# Integrated keeper back pass, width and attacking phases: actual results

**All requested features are in one file: `experiments/keeper-width/team.py`. It has not earned promotion; main and the active champion remain unchanged.**

The single-file deliverable is byte-for-byte the frozen R3 integrated controller, SHA-256 `6d9ee05c2423e03fea67bfde818249db9d5f638c7a8cd2ae9aad22e65d51d9fc`. It includes the existing keeper back pass, wider passing support and the requested clock schedule. The four prototype revisions are archived research sources, not four separate tactics to upload.

The native sandbox completed **656 full scheduled matches**: 528 in development and 128 fresh direct champion games. All used the stock engine 0.1.0, official course config `372990895c7eca2a`, five players, 2,400 ticks and a 20 ms decision deadline. One timed worker ran at a time. No game physics, SDK timer, GC, process settings or seed-dependent controller decisions were changed.

## Requested behavior

| Standard 120-second match | Attacking intent |
|---|---|
| 0–60 seconds | Normal football with the requested back pass and wider support |
| 60–90 seconds | Moderate attack; free support advances |
| 90–120 seconds | Ultra attack; more advanced support and a selective regain outlet |

The schedule reads the actual match length and simulation rate, and applies regardless of score as requested. A short intake match still keeps its first half normal. The goalkeeper, ball chaser, urgent recovery, restart protection and existing verified receiver plans retain priority. The striker keeps a central half-space and another free player supplies width. Passing support favors open lanes, separation from the carrier and other assigned targets, and a brief hold that translates with the carrier. Actual passes still use executable reception and full-route opponent races. Support targets are not guaranteed player positions: a player receiving a pass must move close to the ball.

The keeper back-pass and collection methods were checked for AST identity with the original back-pass experiment. The integrated source imports only math and the official soccer SDK, and contains one controller class in one `team.py`.

## Development: fresh paired opponent-pool screens

The opponent pool contains frozen v10, counter, press, compact defence, quick-wall and the active Elite Cutback. Each seed is tested on both field assignments and both kickoff arrangements. Each source was frozen in Git before its run.

| Integrated revision | Configurations per source | Champion points | Integrated points | Champion goals | Integrated goals | Raw misses, champion / integrated |
|---|---:|---:|---:|---|---|---|
| R1 | 48 | 89 | 77 | 114–55 | 101–83 | 0 / 0 |
| R2 | 48 | 81 | 70 | 122–67 | 87–59 | 1 / 0 |
| R3 | 48 | 98 | 98 | 123–52 | 117–58 | 0 / 1 |
| R4 | 96 | 161 | 148 | 216–124 | 162–126 | 0 / 1 |

R1 used a smoothed team-possession flag too broadly. R2 required stronger ownership evidence and added a possession triangle; it reduced concessions but lost scoring. R3 restored role-specific forward distances, kept the striker central, translated support holds with the carrier and declined searched unpressured backward links. It tied champion points, including 5W–2D–1L and 18–9 goals against the champion over eight development games; poor results against pressing opponents erased those gains in the full pool. R4 tested one shorter pressure outlet and a closer possession triangle under an explicitly registered development-only extension, using four new seed blocks; it remained worse overall. The hold-out seeds and all original promotion gates were unchanged.

**No integrated source earned more development points than the champion.** The original 12-seed, 384-configuration league validation therefore remains unused. The development confidence intervals are exploratory, with only two seed blocks in R1–R3 and four in R4; they cannot establish class-league superiority.

## Fresh direct champion test

R3 was frozen and selected before a separate direct test on 32 new seeds, both field assignments and kickoff arrangements: 128 actual integrated-versus-champion games. These are each side’s points from the same games, not champion self-play points.

| Metric | Integrated R3 | Current champion |
|---|---:|---:|
| Wins / draws / losses | 53 / 27 / 48 | 48 / 27 / 53 |
| League points | 186 | 171 |
| Goals | 192 | 173 |
| Pass completion | 51.52% | 50.92% |
| Turnovers | 771 | 803 |
| Mean decision time | 0.228 ms | 0.219 ms |
| Maximum decision time | 22.073 ms | 9.222 ms |
| Raw deadline misses | 1 | 0 |
| Policy exceptions | 0 | 0 |

The direct points difference is +0.117188 per match. The 20,000 whole-seed bootstrap paired 95% interval is **[-0.351562, +0.562500]**. It includes zero. The observed lead is not a demonstrated large or statistically credible advantage. This direct experiment does not replace the failed pool-development selection or establish league performance.

The integrated controller had 7.8125 additional raw deadline misses per 1,000 direct fixtures, exceeding the original allowance of two. Its exact repeat had no own miss, and that repeat does not remove the raw failure. Average runtime was approximately 4.3% higher than the champion. A small average time does not establish compliance with the per-decision deadline.

## Native spacing and keeper participation

R3 development passive telemetry measures actual observed outfield span and nearest supporting-player distance during controlled possession. These are descriptive physical measurements; they are not proofs that every player is always unmarked.

| Clock phase | Champion / R3 mean outfield width | Champion / R3 nearest support distance |
|---|---|
| normal | 17.84 / 19.26 units | 5.89 / 9.58 units |
| moderate | 19.07 / 19.65 units | 4.11 / 8.85 units |
| ultra | 19.19 / 19.37 units | 4.55 / 8.14 units |

In R3’s 48 pool-development matches, the keeper back pass issued 32 new plans, with 32 confirmed native kicks and 26 named-keeper collections. 3 collections had immediate controlled possession. Native contacts and immediate control are separate measures.

## Checks, evidence and reproducibility

The delivered integrated file passed **131 regressions**, including clock boundaries, arbitrary match length and rate, reset/restart behavior, protected receptions, urgent defence, spacing, central support and translating the hold with a moving carrier. R2–R4 each passed the 130-test suite available at their freeze; the extra moving-carrier test was added for delivery. Every development source passed the official public-seed intake, with 2,000 decisions per source, zero exceptions and zero deadline misses. All full scheduled fixtures completed with zero policy exceptions. Raw misses are preserved; no adverse outcome was dropped or replaced by a clean repeat.

The native diagnostic replay of the R1 worst loss reproduced the same score with zero errors/timeouts. Its ownership count includes no-touch kickoff states and must not be interpreted as 592 opponent counterattacks. It supports checking the trigger, not attributing every conceded goal to that trigger.

- `registration.json`, generation protocols, reviews, and `generation-4-development-amendment.json`: sources, decisions and fresh seeds.
- `direct-validation-protocol.json`: predeclared 32-seed direct hypothesis; not a league-promotion substitute.
- `development-decision.json`, `generation-*-vs-active.json`, `fresh-head-to-head-results.json`, `decision.json`: actual machine-readable results and no-promotion decision.
- `tests/fixtures/keeper-width-native-evidence.zip`: raw matches, diagnostic repeats, source/opponent snapshots, intake reports, passive observations and per-file SHA-256 manifest.
- `evidence.json`: archive integrity, checks and raw sample totals.

From the repository root with the shipped native engine installed in the SDK:

```sh
ROBOCUP_TEAM_PATH="$PWD/experiments/keeper-width/team.py" ROBOCUP_WIDTH_TEAM_PATH="$PWD/experiments/keeper-width/team.py" python -m unittest discover -s tests -q
python tools/benchmarks/run_keeper_width.py --protocol docs/keeper-width/development-protocol.json --out /path/to/new-r1
python tools/benchmarks/run_keeper_width.py --protocol docs/keeper-width/generation-2-protocol.json --out /path/to/new-r2
python tools/benchmarks/run_keeper_width.py --protocol docs/keeper-width/generation-3-protocol.json --out /path/to/new-r3
python tools/benchmarks/run_keeper_width.py --protocol docs/keeper-width/generation-4-protocol.json --out /path/to/new-r4
python tools/benchmarks/run_keeper_head_to_head.py --protocol docs/keeper-width/direct-validation-protocol.json --out /path/to/new-direct
```

**Decision: retain the active champion.** The requested integrated controller is available for review, but the evidence does not justify calling it substantially stronger or promoting it. Main, `my-team/team.py`, and every archived champion remain unchanged.
