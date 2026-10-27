# Why the head-to-head win did not establish league superiority

Update: public school evidence is now archived in [school/REPORT.md](school/REPORT.md).
That report supersedes the earlier lack-of-school-data limitation below and
documents mutable live results, current v51-style defense and actual close-shot
failures. The original audit is retained for provenance.

The recorded v51 MONSTER convincingly beat frozen TITAN: 86 wins, 14 draws,
no defeats over 100 balanced fixtures in the second-round holdout. This is a
measured matchup advantage, not evidence of being better in every aspect.

The local student guide says the class plays a round robin on hidden seeds.
Wins earn three points, draws one, followed by goal difference. Points assign
divisions of twenty; mean decision time orders teams within each division.
Consequently speed can explain a rank difference within a division, but cannot
explain a large difference in actual league points. The school standings,
uploaded-file hashes, opponent fixtures and server logs are not in this repo;
the exact cause of the reported points gap is still unknown.

The three existing `Downloads/replay*.json` files were rechecked on 27 October.
They are the same earlier games among Ethan Ikopit, Zamokuhle Maziya and
Muhammed Abed, using engine 0.1.0 and config `372990895c7eca2a`, seeds
1000/1001/1002, 2,400 ticks and a 20 ms limit. They contain no current MONSTER
submission or league table. They confirm the profile in those archived games,
but cannot explain the reported current points gap.

The previous release estimate used four closely related opponents. It was
226W/153D/21L, so 38.25% of those games were draws. It explicitly did not
verify superiority over the school field. Six easy baselines had a ceiling
effect: both old and new MONSTER earned 117W/3D/0L in 120 fixtures. v51 scored
fewer goals in that baseline suite and drew two additional games in twenty
against each of two older TITAN versions.

The source explains the narrow playing style. `SHELL=True` and
`SHELL_RELEASE=False` return the four-defender shell every decision, including
when losing. `SUPPORT=False` leaves one attacker; the more general pressing,
marking and passing code below the early return is unused. Defenders clear
full power into a predetermined wide lane. This is effective counterattack
and goal protection against tested opponents, but it does not establish broad
attacking strength. For example, one archived older-TITAN suite records 54.7
pass attempts and 1.75 completed passes per match (3.2%), 12.2% control and
33.5% territory. Those metrics describe the tactic; they are not scoring rules.
Earlier naive extra-attacker and clearance-search experiments were rejected,
so more tactics need comparative match evidence, not an assumption of benefit.

Evidence: `../red-team/ROUND2_REPORT.md`, `../red-team/ROUND2_RESULTS.md`,
`../red-team/monster/team.py`,
`../red-team/results/r2-generalization-v51-stream-post-titan-original.json`,
`../../docs/student-guide.md` section 10.

The new league benchmark reserves separate screening (810000 onwards),
selection (820000 onwards), and final holdout (830000 onwards) seeds. Use
identical opponent sets and four starts per seed for every paired comparison.
Keep frozen TITAN, MONSTER and older versions as controls, add all six official
baselines, and include structurally different legal stress opponents. Select
for total league points, weak matchups, reliability and computation cost;
report goal difference and draws as well as wins. Neither synthetic opponents
nor a finite local holdout prove school-league dominance.

`bench.py` stores immutable snapshots for candidates and source opponents,
records every fixture before moving on, uses the untouched course config,
and enforces 2,400 ticks, five players and the 20 ms limit. Runs are sequential
and labels cannot overwrite previous evidence. Platform failures have no
fabricated draw score; they invalidate the protocol. Forfeits remain outcomes.

Example:

```powershell
python experiments/league/bench.py --teams experiments/red-team/monster/team.py --opponents balanced tactical possession structured_attack man_marking ball_chaser my-team/team.py --start 810000 --end 810001 --label monster-screen
```

`--compare BEFORE.json AFTER.json` compares single-candidate reports on exact
matching fixtures and computes a paired points-per-game change with a 95%
bootstrap interval over seed clusters. A single-seed screen has no interval.

`analyse.py REPORT.json` or `analyse.py REPORT.jsonl` prints compact opponent
and overall tables from finished or in-progress runs. Add `--before SPEC
--after SPEC --output NEW.json` for a paired comparison inside a report with
multiple candidates. Partial reports disclose unmatched fixtures; they are
selection diagnostics, not final evaluation.
