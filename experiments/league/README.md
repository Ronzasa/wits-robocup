# League validation

The selected standalone submission is [league-team/team.py](../../league-team/team.py). Its playing logic matches `experiments/league/ray_cover2/team.py`; packaging changed only controller name/version metadata.

Selection: the new candidate earned 598 points versus Monster's 561 across 224 fixtures per policy. It beat the control on selection points.

Fresh holdout used 14 fixed opponents, 560 fixtures per policy and 10 previously untouched seed clusters. Half used custom kickoff formations and half used the engine's default formations. Both sides and kickoff owners were crossed; the original engine/config, 2,400 ticks and 20 ms deadlines were retained.

| Policy | W/D/L | Points | GF/GA | Mean/max decision ms | Errors/timeouts | Forfeits |
|---|---|---:|---|---|---|---:|
| Release | 457/101/2 | 1472 | 1478/40 | 0.1410/26.076 | 0/1 | 0 |
| Titan | 401/89/70 | 1292 | 760/387 | 0.1859/70.653 | 0/1 | 0 |
| Monster v51 | 407/128/25 | 1349 | 1555/165 | 0.1454/13.771 | 0/0 | 0 |

Paired changes in points per match for the release, with 95% seed-cluster bootstrap intervals:

- Versus Titan: +0.321 [+0.266, +0.375] across all 560 matched fixtures.
- Versus Monster v51: +0.220 [+0.107, +0.346] across all 560 matched fixtures.

The secondary comparison excludes the 6 native baselines. Its 8 source-defined tactical opponents give 320 fixtures per policy over the same 10 seed clusters. This local stress pool is not the actual school field.

| Policy | Source-pool W/D/L | Points | Win rate | GF/GA |
|---|---|---:|---:|---|
| Release | 223/95/2 | 764 | 69.7% | 448/35 |
| Titan | 163/87/70 | 576 | 50.9% | 484/377 |
| Monster v51 | 175/120/25 | 645 | 54.7% | 486/148 |

Secondary paired changes in release points per match, with 95% seed-cluster intervals:

- Versus Titan: +0.588 [+0.509, +0.659] across 320 matched source-opponent fixtures.
- Versus Monster v51: +0.372 [+0.209, +0.544] across 320 matched source-opponent fixtures.

| Formation | Release points | Titan points | Monster points |
|---|---:|---:|---:|
| custom | 746 | 646 | 670 |
| default | 726 | 646 | 679 |

Each opponent row contains 40 fixtures per policy:

| Opponent | Release points | Titan points | Monster points |
|---|---:|---:|---:|
| balanced | 120 | 120 | 118 |
| tactical | 108 | 120 | 112 |
| possession | 120 | 120 | 120 |
| structured_attack | 120 | 120 | 116 |
| man_marking | 120 | 120 | 120 |
| ball_chaser | 120 | 116 | 118 |
| my-team | 102 | 55 | 95 |
| monster | 76 | 14 | 46 |
| blue-c-combined | 82 | 48 | 68 |
| v21-close-outlet | 93 | 57 | 65 |
| pressure | 110 | 112 | 114 |
| counter | 78 | 107 | 69 |
| gap_press2 | 105 | 116 | 98 |
| open_gap | 118 | 67 | 90 |

All fixtures and decision faults remain included; forfeits are scored 0-3. Unavailable kick attempts remain in the full validation counters and do not invalidate a legal action payload. Full source hashes, action validity, per-mode/per-opponent metrics and comparisons are in [FINAL_REPORT_V2.json](FINAL_REPORT_V2.json), with the pre-holdout decision in [selection-v2-lock.json](selection-v2-lock.json).

This is evidence against a local tactical pool. School leaderboard dominance remains unverified; the student cohort, server scheduling and future submissions can differ. Original Titan, Monster and archived experiments remain preserved.
