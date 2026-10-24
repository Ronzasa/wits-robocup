# Tactic investigation: Stage 0 report (mechanism proofs). Nothing promoted.

Branch `experiment/tactic-investigation`. Baseline sha256 6529c92e... unchanged. Engine sha256 in HASHES.txt.
Raw data: `results/*.json`. Scripts: `probes/`.

## 1. Kickoff foul bait: mechanism shown, NOT promising
* Delaying our kick past tick ~34 makes built-in opponents (ball_chaser, structured_attack, man_marking,
  balanced, possession, tactical) enter the circle: fouls in 33/40 (no delay), 40/40 (delay 45, 55) matches;
  our kick is still accepted before the 60-tick expiry (first move at tick <= 56).
* champion_original, lock_no_breaker, press_formation, bus_wall, do_nothing, random_legal: 0 fouls in every
  configuration. dribbler fouls regardless of our kick time.
* Conclusion: it only fires on opponents the baseline already beats ~60-0 and never on strong ones.
  Closed (no development). Conversion to goals was not measured because activations are zero where it matters.

## 2. Goal-wall wedging: mechanism shown, PROMISING (not yet developed)
* Against the sealed five-player wall (`bus_wall`), seeds 100..129, wall settled (tick >= 100):
  0 pushers: lane >= 1.15 wide opens in 0/30 matches. 2, 3, 4 pushers: 30/30, median 2.6-3.2 s,
  open ~90% of ticks afterwards (details in `results/wedge_probe.json`).
* Caveats: only the wall bodies were counted, not our own pushers, so the lane is not yet shown to be
  *shootable*; the stand-in wall returns to fixed spots; per-defender displacement >= 1.0 was not measured
  (wall mean shift 0.1-0.3). These must be closed in Stage 1 by measuring actual goals.
* Headroom exists: baseline on dev seeds 30000..30019 (both sides) scores 0.475 goals/match and 1.95
  points/match vs bus_wall (0 conceded), see `results/baseline_headroom_stage1seeds.json`.

## 3. Defender-assisted own goal: NOT demonstrated, closed
* 164 single-kick end-wall rebound geometries: 0 own goals.
* Sustained end-wall bombardment (240 matches, 4 opponents, 1200 ticks): 1 opponent own goal total
  (tactical, 1 match) with no evidence of the cooldown mechanism; our own side recorded 20 own goals
  (it is harmful to us). Stat attribution of `own_goals` per team index is not yet verified.
* Conclusion: not reproducible, activations ~0.004/match. Closed.

## Next (needs your go-ahead)
Stage 1 for wedging only: candidate in `candidates/`, tuned on seeds 30000..30199, then one untouched
confirmation on 40000..40149 with the paired harness and the gates in PROTOCOL.md.

---
# Stage 1 (development, seeds 30000..30019 x both sides = 40 paired units vs bus_wall)

Finding 0: the frozen baseline already contains idea 2 (`_wall_break`: legal pushes on defenders plus a
shot through the widest gap). So "wedging" here means improving that code, not adding a new mechanism.

Diagnosis (`probes/diag_wallbreak.py`, `probes/trace_shots.py`): vs the sealed wall the baseline is in wall-break
state ~1700+ ticks per match; a >=1.15 gap exists ~65% of those ticks, but a kicker is in range in only ~100 ticks and
~35 shots per match yield ~0.47 goals/match. Trace of a shot: the ball is deflected back within 3 ticks. The wall
defenders kick it away when it enters their 2.2 kick range, so a lane free of bodies is not a *verified* lane:
it also needs every nearby defender to be on kick cooldown while the ball is in their range.

Candidates (single-file copies of the baseline, `candidates/`), paired vs baseline, points per match:

| Candidate | Change | dPts vs baseline (95% CI) | goals for | timeouts/match |
|---|---|---|---|---|
| wedge_v1 | lane check also treats our own bodies as obstacles; tries every gap | -0.050 [-0.482, +0.382] | 0.47 -> 0.45 | 0.000 -> 0.025 (sporadic, sandbox load) |
| wedge_v2 | v1 + shoot only if every defender whose kick range the ball crosses is on cooldown (public `kick_cooldown_ticks`) | -0.100 [-0.543, +0.343] | 0.47 -> 0.42 | 0.000 -> 0.000 |

Both are statistically indistinguishable from zero and point slightly negative. Bus defenders kick whenever
they can, so the cooldown gate almost never opens. No candidate meets gate 1 (95% lower bound > 0).

Decision: do not spend the untouched confirmation seeds (40000..40149) on a candidate that shows no
development-seed benefit; the confirmation set stays unused. Nothing is promoted; baseline sha256 unchanged.

# Overall outcome
All three ideas fail the promotion gates: (1) bait fires only on opponents already beaten, (2) wedging is already
in the baseline and the two refinements show no gain, (3) own goal not reproducible. Raw data in `results/`.
Possible follow-up if you want it: a larger dev run (n>=400 units) to detect a ~0.2 point effect, or a different
approach to making a wall give up the ball (not one of the three assigned ideas).

---
# Defending investigation (after the user confirmed the running file)
Running file = frozen baseline minus `TRAIL_WALL` (7-line diff; sha256 41e938a4...).
* Pure 5-man goal wall (`bus_wall`) vs strong stand-in attackers (10 seeds x both sides): concedes 0.10-0.20 goals/match,
  0.80-0.90 league points/match, i.e. mostly 0-0 draws, despite 37-40 shots against (`results` in this section: probes/profile.py output).
* Trailing-wall thresholds, paired vs baseline on dev seeds (5 opponents x 20 units): TRAIL_WALL=2 dPts 0.000 (never triggers
  vs stand-ins); TRAIL_WALL=1 dPts -0.27 [-0.43,-0.12] (harmful: it removes comebacks). Stand-ins never lead by 3, so TRAIL_WALL=3
  (the delivered file) cannot be tested locally; it only matters against teams like the real top two.
* Replay tracking (`probes/video_goals.py`, 24 goals in 4 videos): ~3.7 attackers beyond +10 six frames before a goal, ~1.5 of ours
  defending the final third; ball was detected in only ~20% of frames so ball-path conclusions are not reliable.
* Conclusion: no new controller change proven. Recommendation is to submit the delivered file (TRAIL_WALL=3), which is
  expected to cap blowouts (about 3 goals saved per top-team loss in the 4 replays IF the wall holds at the stand-in rate); this affects goal
  difference, not points, and is unverified against the real top teams.
