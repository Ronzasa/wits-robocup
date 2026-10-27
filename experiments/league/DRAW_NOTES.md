# V1 draw-conversion diagnosis

`DRAW_AUDIT.json` reads only the frozen V1 release's 560 exposed holdout
fixtures. It confirms **457W/101D/2L**: **86 draws were 0–0**, and 15 were 1–1.
Default starts produced 54 draws; custom starts 47. Own kickoff produced 54;
the other kickoff 47. Neither starting mode explains most remaining draws.
The release had zero errors, timeouts and fouls across these 101 games.

| Opponent | All 40 games, W/D/L | Draw scores | Own shots/game in draws | Own control | Own attacking territory |
|---|---|---|---:|---:|---:|
| Old MONSTER v51 | 18/22/0 | 20×0–0, 2×1–1 | 8.23 | 3.51% | 43.96% |
| Synthetic Counter | 19/21/0 | 21×0–0 | 5.14 | 6.40% | 53.16% |
| Blue C | 21/19/0 | 15×0–0, 4×1–1 | 14.95 | 16.41% | 30.44% |
| MONSTER v21 | 27/12/1 | 7×0–0, 5×1–1 | 9.42 | 3.92% | 40.16% |
| TITAN | 31/9/0 | 8×0–0, 1×1–1 | 3.89 | 22.77% | 30.07% |
| Synthetic Gap Press 2 | 33/6/1 | 5×0–0, 1×1–1 | 13.17 | 7.53% | 56.06% |
| Tactical baseline | 34/6/0 | 6×0–0 | 2.00 | 3.03% | 27.75% |
| Synthetic Pressure | 35/5/0 | 4×0–0, 1×1–1 | 2.00 | 5.73% | 39.33% |
| Synthetic Open Gap | 39/1/0 | 1×1–1 | 3.00 | 6.29% | 20.75% |

The other five official baselines have no draws. The first five rows account
for 83/101 draws (82.2%). MONSTER v51, MONSTER v21 and Counter, which use dense
goal cover, account for 55/101 (54.5%). This is primarily a goal-screen and
counterattack problem, with a distinct group pinned in its own half against
active attackers.

The aggregate draw has 115.3 kicks, 8.17 shots and 1.97 completed passes per
game, 8.65% control and 40.94% attacking territory. Only 3.93% of registered
pass attempts complete; defensive clearances also enter that metric, so this
does not mean the controller intentionally selected that many passes.

There are two useful hypotheses, requiring new experiments:

1. **Sustained siege without progress.** Against Counter, the drawn games
   have *more* kicks and territory than wins (137 vs 83 kicks; 53.2% vs 44.1%
   territory), but fewer shots (5.14 vs 7.42). Possession alone is not enough.
   Against the MONSTER variants, drawn games have fewer shots and less control
   than wins. A close finisher and a supporting receiver could help a single
   attacker stalled near a static screen.
2. **Defensive recycling without a viable outlet.** Against TITAN, draws have
   261 own kicks/game, 143 registered pass attempts and only one completion;
   territory is 30%. Blue C draws similarly have 168 kicks, 117 registered
   pass attempts and 1.26 completions. A finisher used only near the opposing
   goal cannot fix games that never establish an attack. Clearance collection
   and a temporarily closer receiving option need separate attention.

These are diagnostic inferences. Aggregate metrics do not record where each
attempt occurred or whether a shot was available. Runtime tactical modes and
trajectories were not recorded. V1's source normally remains in its four-cover
counter mode; default/custom in this audit refers to kickoff formation.
Scoring first also changes both teams' tactics, so win-versus-draw metric
differences are not causal estimates.

Candidate triggers should use public play observations:

- For a second attacker, require a level score, persistent opposing goal-mouth
  cover, the ball established in the attacking half, repeated failed progress,
  and a safe ball race. Give the supporting player a distinct receiving lane;
  recall it immediately on a dangerous turnover or losing race. Preserve three
  projected guards and avoid oscillating roles through a short hysteresis.
- For a contact finisher, require a reachable close goal-mouth ball, a ready
  kick and a path forecast that includes carrier and blocker body contacts.
  Trigger on the observed opportunity rather than opponent name or seed.
- For escape support, detect repeated own-half clearance/re-interception
  cycles and a stranded outlet. Bring a receiver toward an actually collectable
  lane instead of sending a second player forward into empty space. Keep the
  shooting screen intact while the opponent controls a dangerous ball.

The main risk is exposing the goal during a turnover. V1 loses only twice in
560 games, so indiscriminate attacking releases can undo the measured gain.
Use paired **league points**, not just fewer draws: converting a draw to a win
earns two points, while converting an existing win to a loss costs three.
Retain all outcomes and faults, including new losses against the formerly
easy pool.

The V1 holdout is now exposed and can diagnose failures only. New candidates
must use the reserved 840000–840003 training seeds, 850000–850003 selection
seeds and, after a source lock, untouched 860000–860009 final seeds. Do not
alter frozen V1 or select a new release from the old holdout's favorable rows.
