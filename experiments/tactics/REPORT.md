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

---
# High press with instant fallback (user suggestion)
* The baseline already has a counterpress (`COUNTERPRESS_SECONDS = 1.0`). Raising it to 2.0 or 3.0 changed nothing
  (identical goals in all 150 paired units): that knob is inert.
* New candidate `candidates/hpress_v1.py`: when an opponent holds the ball in their half (ball x >= HPRESS_X) free
  outfielders (one stays as cover) stand goal-side of the carrier's nearest passing options; re-evaluated every tick,
  so fallback is instant. Dev seeds 30000..30014 x both sides, 5 opponents (150 paired units), points/match vs baseline:
  press line x>=5: -0.060 [-0.235,+0.115] (GF 1.05->0.99); x>=20: -0.067 [-0.257,+0.124]; 3 pressers: identical to v1 (cap).
  No gain, slight negative, 0 errors, 0 fouls. Not promoted; confirmation seeds unused.

---
# Tighter ball-carrier marking without gaps (user suggestion)
`candidates/contain_v1.py`: when an opponent holds the ball in our half (x <= 25) the second-nearest defender stands on the
carrier->goal line 3.5 behind the carrier and (v1) a third drops goal-side of the opponent closest to our goal; the keeper and
the deepest outfielder are never used so no gap opens. Dev seeds 30000..30014 x both sides, 5 opponents, 150 paired units:
* v1 (layer + marker): dPts -0.133 [-0.304,+0.037], GF 1.05->0.96, GA 0.50->0.55
* contain_nomark (layer only): dPts -0.027 [-0.197,+0.143], GF 1.05->1.07, GA 0.50->0.58
Conceded goals rose in both. Overriding the baseline's tuned marking does not help locally. Not promoted.

---
# Lab and tuner (user request: one framework that brings each experiment to its best)
* `lab/team.py`: baseline + switches for the press (`HPRESS_*`) and the carrier containment (`CONTAIN_*`), all OFF by
  default. Verified identical to the baseline on 18 matches (scores and kick/shot/pass/control stats).
* `harness/tune.py`: coordinate descent over 9 settings, 55 s per trial on 100 paired units (5 opponents x 10 seeds x 2 sides,
  seeds 30020..30029), baseline results cached, objective dPts + 0.25 dGD, rejects any trial with errors or fouls.
* Result of tuning round 1 (`results/tune1`): the press and containment switches were never accepted (all negative, as in
  the manual tests). It accepted TRANSITION_SECONDS 2.5 and SHOOT_RANGE 28 (+0.14 points on the tuning units).
* Validation on fresh development seeds 30100..30119 (200 paired units): dPts +0.005 [-0.113, +0.123], GF 0.99->0.97,
  GA 0.42->0.43. The tuning gain was selection noise; nothing is promoted.
* Lesson: with ~100 units a tuner finds spurious +0.14 gains among ~15 trials; any accepted setting must pass a separate
  validation set, which is now part of the procedure. Reliable detection of ~0.1 point effects needs ~600+ paired units.

---
# Website replay (format v4) as an opponent source
Replay supplied by the user: `128211-raquel-defranca` vs `373722-zamokuhle-maziya`, seed 1000, final 0-5 (website
match r00-...-0000001000-home). It holds per-tick positions, velocities, cooldowns and every player's *action* for both teams,
so behaviour can be extracted (public data, no code). Raw file (21 MB) is not committed; `harness/extract_replay.py` makes the
compact team-relative dataset `replays/zamokuhle_maziya_vs_raquel_seed1000.json.gz` (team 1 rotated 180 deg to the obs frame).

How Zamokuhle played (one match, 5-0): possession 55%; keeper fixed at x=-48.2; two midfielders around x -5..-2 and two forwards
at x 30-45 with |y| ~ 9-14 when attacking (outfield spread +15.7 / +9.7), dropping to x -17/-9 when defending; kicks alternate
tap (power 0.1-0.6) then full-power drive (mean power 0.44, 19% full); ALL five goals ended at the ball |y| ~ 6.6-6.8, i.e. shots into
the corners next to the posts (goal half-width 7), taken after wide-forward cut-backs while Raquel's defenders were stretched.

`opponents/clone_zamokuhle.py` (k-NN behaviour clone from this single match): FAILS as a stand-in. It scores 0 goals against
balanced, tactical, press_formation and the baseline (and concedes 5-10 per match), so one match of data is not enough for an
interactive clone; it is not used as evidence. More replays (especially top teams vs our team) are needed.

---
# Forward clearance ("stop passing sideways in defence", from an outside analysis of a Nkqubela replay)
Lab switch `CLEAR_ON` (`lab/team.py`): when the ball is in our half (x <= CLEAR_X) and an opponent is within CLEAR_R of it,
whoever can kick drives it at full power toward the far end, aimed at the flank away from the nearest opponent.
Dev seeds 30040..30054 x both sides x 5 opponents = 150 paired units, points/match vs baseline:
* clear_a (x<=-15, r<=8): -0.020 [-0.231,+0.191], GF 1.00->0.94, GA 0.53->0.55
* clear_b (x<=-30, r<=5): +0.060 [-0.130,+0.250], GF 1.00->0.94, GA 0.53->0.45
Neither is distinguishable from zero; clear_b's lower conceded goals are an observation to validate on separate seeds (n>=600), not a result.
Cooldown awareness (suggestion 3) is already provided by `obs.can_kick`; the controller never sends a kick on cooldown.

---
# Replay 2: Morare Bokgoshi 3 - 1 Zamokuhle Maziya (seed 1003; `harness/replay_report.py`)
* Zamokuhle LOST this match, so "Zamokuhle = long-ball powerhouse" is not supported: his kick power median is 0.24 (13% full power, 71% below 0.5),
  38% of kicks aimed at a teammate, 1 rejection (out of range). In the first replay: median 0.34, 19% full, 34% aimed at a teammate. Same signature in both matches.
* Morare ("spammer" claim): 46 rejected kicks, 44 `on_cooldown` of 176 kicks (26% wasted), median power 0.21, 14% full, 44% aimed at a teammate.
  The spam claim is true; being rejected has no cost beyond the kick not happening. Morare defended deep (outfield mean x -16, -19, -5, -11) and won 3-1.
* Morare's goals: ticks 210, 1144, 2017 with the ball at |y| 6.9, 6.9, 5.5; Zamokuhle's goal at |y| 5.6. All 4 goals in this match went in near the posts, as did all
  5 in replay 1: 9 of 9 goals at 5.5 <= |y| <= 6.9 (goal half-width 7).
Datasets: replays/morare_bokgoshi_vs_zamokuhle_seed1003.json.gz, replays/zamokuhle_maziya_vs_morare_seed1003.json.gz.

---
# Replay 3: Nkqubela Hokwana (us) 0 - 5 Zamokuhle Maziya (seed 1000, our team = engine team 0)
`harness/replay_report.py`: we made 87 kicks (median power 0.56, 0 rejected), Zamokuhle 201 (median 0.45); possession 38% vs 62%.
All five goals: Zamokuhle's striker (players 7, 8, 9) FULL-POWER shot (power 1.00) taken 5 ticks after his own previous touch, from x = -27.8,
-35.0, -38.9, -28.2, -45.7 (28-40 units from our goal for four of them), ball crossing the line at |y| = 6.1-6.8 (corner next to the post, goal half-width 7).
Our defenders were far upfield or off to a flank at the shot (e.g. goal@218: players at x -16.7, -23.2, -16.2, -6.8; goal@1064: players around y -14..-19).
Keeper feasibility (needed lateral = |y_line - y_keeper| - 2.2 kick range, vs max reachable from rest in the ticks between kick and goal):
| goal | kick->goal ticks | needed | max | keeper moved | savable by keeper alone |
| 218 | 15 | 3.8 | 4.6 | 2.6 | yes if it starts at the kick |
| 692 | 10 | 3.3 | 2.6 | 1.5 | no |
| 1064 | 8 | 1.9 | 1.8 | 1.4 | no (borderline) |
| 2040 | 15 | 3.9 | 4.6 | 2.6 | yes if it starts at the kick |
| 2375 | 2 | 4.8 | 0.2 | 0.3 | no |
Reading: 3 of 5 cannot be saved by the keeper once the shot is taken; the shots have to be prevented (pressure on the striker, a defender in the
shooting lane, or the keeper already shaded toward the ball side). Stand-in `opponents/corner_shooter.py` (dribble with taps, full-power far-corner shot
from x>=18) concedes only 0.083 goals per match against the baseline because our outfield contests it normally, so it does NOT reproduce the real pressure;
more replays or a harder stand-in are required before testing a fix.

---
# Website HAR (lamp.ms.wits.ac.za): standings, match list and 5 replays (snapshot 2026-10-25, ladder running, 254 teams)
Data: `replays/standings_snapshot_2026-10-25.csv` (compact), raw replays kept out of git. Tools: `harness/replay_report.py`, `harness/goal_geometry.py`, `harness/shot_conversion.py`.
Correction to an earlier note: shooter distances in replay 3 were measured from the centre; the shots were taken 4-22 units from the goal line (typically 18-22), not 28-40.
* Our row: rank 95, 1.69 pts/match, GF 0.91, GA 1.33, win 53%, division 5, decision mean 0.49 ms, **policy_timeouts 1083 in 1012 matches (~1.07 per match)**, 0 errors.
  So the 963-ish "exceptions and missed deadlines" are raw deadline misses on the tournament machine, not exceptions. Top teams have 1-8 (but Ethan_Ikopit 716 and Tlou_Kgatla 190 are also top-10, so timeouts alone do not decide results).
* Bunker-style teams (GF < 1.3, GA < 0.5, > 100 matches): 13 teams, 11 of them in the top 61, e.g. Muhammed_Abed (rank 4: GF 0.98, GA 0.18, territory 26%), Ethan_Ikopit (rank 8: 0.97 / 0.15 / 26%),
  Tebogo_Mabhele, Saurav_Lall, Olwethu_Phiri... They score about one goal per match and concede ~0.15-0.4: ~2.4-2.8 points per match.
  Ethan_Ikopit beat Zamokuhle_Maziya (GF 4.22 per match) 1-0 in 3 of 4 matches; Abed won 1-0 once, lost 0-1 once, so a deep block holds against the best attacker in the league.
* We score as many goals per match as those teams (0.91 vs ~0.95) but concede 1.33 vs 0.15-0.4: the gap is conceded goals (our blowout losses and no early lock), not scoring.
* Zamokuhle in the two new replays: seed 1001 we lost 1-2 (our goal at his keeper's expense; his goals 1, 4... he kicks median 0.26, 63% possession), seed 1003 we lost 0-5 with the same 4-5 deep 'corner' goals.

---
# Bunker-team replays (Ethan_Ikopit 1-0 and Muhammed_Abed 1-0 over Zamokuhle_Maziya)
Matches: m-f25d50c2f1ce7db8 (Ikopit, seed 1000, kickoff Ikopit), m-c8aed6a617083e9a (Ikopit, seed 1001), m-9862c4f0fb79e872 (Abed, seed 1002).
* Phase 1 (until their first goal): normal play. Phase 2: lock. Ikopit seed 1000: possession 19%, 46 kicks; Abed: possession 18%, 24 kicks (!); outfield at x -47.8 .. -48.4
  (Ikopit y -5.5, -1.9, 1.7, 5.4 with keeper at x -46; Abed y -5.9, -2.9, 2.9, 5.9 with keeper at y 0, spacing 2.9 = body gap equal to the ball diameter), std of y ~1.
  Zamokuhle had 81-82% possession, 178-247 kicks and scored 0. This is the same structure as our `_lock_wall`; their keepers sit at the goal line (-46 / -48.5).
* How they scored the single goal: all three goals (ticks 384, 564, 1536) were a striker moving up the pitch with micro-taps (power 0.03-0.18) and then ONE full-power
  kick into the corner next to the post from 16-20 units out: ball |y| 6.2 / 6.9 / 5.9. Zamokuhle's defenders were off-line (his outfield at x +11..+28 attack-relative) and his keeper did not stop it.
* So across 4 replays all 16 goals (11 Zamokuhle vs us, 5 others) are corner shots at 5.5 <= |y| <= 6.9 from <=22 units, and every top team uses taps-then-drive.
  The wall (players at |y| ~ 3 and ~ 6 plus keeper) is exactly what covers those corners; the keeper alone cannot (see keeper feasibility above).

---
# Post guard (two defenders to the post corners when an opponent holds the ball in our shooting zone)
Lab switch `GUARD_N/GUARD_X/GUARD_Y` (`lab/team.py`), stand-ins `opponents/tap_drive.py` (3 attackers, taps then a full-power corner drive) and
`opponents/corner_shooter.py` (single striker; MODE 'near' = post on the ball's side). Probe: `probes/guard_probe.py`.
* Full-team test vs tap_drive (10 seeds x 2 sides): baseline and both guards 1.2-0.1, 3.0 pts: the stand-in cannot create chances against an intact team, so it cannot rank fixes.
* Mechanism test (our outfield frozen except the guard; striker corner shots from 24 units, 120 matches, seeds 31000..31059): goals conceded
  N=0: 50 (0.080 per shot), N=2 with ball x<=-25: 32 (0.043), N=2 with ball x<=-15: 45 (0.062). The x<=-25 guard removes ~36% of goals in this handicapped scenario (Poisson z ~ 2.0, one of three configurations tried).
  The keeper alone saves ~92% of these shots (the real matches convert far more, so the stand-in shot is weaker than the real one).
* Full-game paired tests (150 units: 5 opponents, seeds 30070..30084, both sides): guard2 (x<=-25) dPts -0.187 [-0.358,-0.015], GF 0.99->0.90, GA 0.33->0.39;
  guard2_x15 dPts -0.240 [-0.413,-0.067], GF 0.99->0.85. Both significantly worse than baseline: pulling defenders back takes away the chaser support and the outlet.
Decision: rejected. The mechanism works in the handicapped probe but the cost in normal play outweighs it; nothing promoted.

---
# Our own shot placement (4 replays vs Zamokuhle) and a corner-shot preference
Our attempts toward goal from <=30 units across the four matches: 20 attempts, 1 goal; aimed y at the goal line: 11 within |y|<=3.5 (central), 6 near the
post corners 5-7, 3 wide (|y| 8.7-9.0 or -7.8: misses). Winners' goals: all at 5.5-6.9. The baseline (`_before_endwall`) rates five targets (-5.7,-3,0,3,5.7) by opponent-ETA margin and flight time.
Lab switch `CORNER_BONUS` adds a score bonus to the |y|=5.7 targets. Dev seeds 30090..30104, 150 paired units: bonus 0.6 and bonus 2.0 gave identical results,
dPts -0.033 [-0.080,+0.014], GF 1.03->1.01: shot selection is not the bottleneck in these matches. Not promoted.

---
# User's current file (team (11).py, sha256 c1973559...; "replay finishing and cooldown handoffs")
Differs from the baseline lineage: adds near-post aim lanes and relay handoffs, but sets `LOCK_LEAD = 0`, has no trailing wall and no wall breaker. check/validate: PASSED (slowest 8.1 ms, 0 exceptions).
Dev seeds 30110..30124, 150 paired units vs the frozen baseline: dPts -0.293 [-0.472,-0.115] (GF 0.96 -> 3.97 because it keeps attacking after leading, GA 0.45 -> 0.74;
lock_no_breaker -0.90). The same file with `LOCK_LEAD = 1` (candidates/user11_lock.py): +0.080 [-0.034,+0.194] on those seeds, and on fresh seeds 30130..30159
(300 units) +0.013 [-0.077,+0.104] (GF 0.98 -> 0.96, GA 0.45 -> 0.42), i.e. equal to the baseline within noise. Conclusion: the lock is what protects points; the new attacking features are neutral.

---
# From-scratch agent "Bunker-Striker" (`agents/bunker_striker.py`, ~110 lines)
Goal-line wall (keeper + 4 at y 0, +-2.9, +-5.9), one striker that tap-dribbles and drives a full-power corner shot, everyone in the wall when leading or 2+ behind.
check PASSED, decision time 0.02 ms. Paired vs the frozen baseline (dev seeds 30170..30179, 6 opponents, 120 units): v1 dPts -1.500 [-1.741,-1.259] (GF 1.09 -> 0.13);
v2 (better ball chasing, waits outside the centre circle) dPts -1.550 [-1.779,-1.321] (GF 0.17, 2 fouls from centre-circle encroachment).
A single striker cannot win or keep the ball against these opponents; the baseline's interception forecasting and passing machinery is what scores. Not promoted, not recommended for submission.

---
# Bunker-Striker v2/v3 (absolute scores, dev seeds 30170..30177 x both sides, 6 opponents; baseline gets ~2.0 vs champion/press, ~3.0 vs the built-ins)
* v2 (2 attackers with ball-leading interception, dynamic wall with fast fallback, cover outside the circle): 0.86 pts/match, GF 0.28, GA 0.85, 14 fouls (attackers chased their kickoffs).
* v3 (= v2 + hold shape outside the centre circle while the other side kicks off): 0.85 pts/match, GF 0.27, GA 0.83, 0 fouls, 1 timeout.
  Per opponent: champion 0.31, press_formation 0.31, lock_no_breaker 0.38, possession 1.88, balanced 1.06, tactical 1.19 points per match.
* Reading: removing fouls fixed one self-inflicted problem but the agent still cannot win or keep the ball against strong teams, so the striker rarely reaches a shooting position (GF 0.0-0.06 vs the three strongest).
  Files: `agents/bunker_striker.py` (v1), `_v2.py`, `_v3.py`, scorer `harness/quick_abs.py`.

---
# Sandbox campaign: "champion candidate" (`candidates/champion_candidate.py`) vs the user's file as run and vs the frozen baseline
Built in `/home/claude/sandbox` from the user's team (11): `LOCK_LEAD = 1`, trailing wall at 2 goals behind, and the baseline's wall breaker ported into `act()`; nothing else changed.
check PASSED; validate 0 exceptions, 0 over deadline. Paired, 5 opponents (champion_original, press_formation, lock_no_breaker, possession, balanced), both sides:
* vs the user's file as run (seeds 30200..30214, 150 units): dPts +0.247 [+0.089,+0.404] (GF 4.15 -> 0.95, GA 0.73 -> 0.37). Points gain is significant; the file as run scores 8 goals a match against the built-ins because it never locks, which the candidate gives up (goal difference).
* vs the frozen baseline: seeds 30200..30214 (150 units) +0.113 [-0.016,+0.243], GA 0.48 -> 0.37; fresh seeds 30220..30249 (300 units) +0.063 [-0.045,+0.172], GA 0.54 -> 0.46. Positive trend, not significant (promotion gate 1 is NOT met against the baseline).

## Head-to-head vs champion_candidate.py (treated as a top team)

Setup: seeds 30500..30559, both sides (120 matches per row), paired against the candidate playing itself.
Scripts and results are in `sandbox_h2h/`.

| Challenger | pts/match | GD/match | paired diff vs reference | 95% CI |
|---|---|---|---|---|
| candidate vs itself (reference) | 1.183 | -0.158 | - | - |
| late all-in, last 30% when not leading | 0.883 | -0.408 | -0.300 | [-0.468, -0.132] (worse) |
| late all-in, last 15% | 1.067 | -0.275 | -0.117 | [-0.248, +0.015] |
| lock only after >=2 opponent shots at us | 1.167 | -0.033 | -0.017 | [-0.189, +0.155] |
| lock only after >=5 opponent shots at us | 1.158 | +0.017 | -0.025 | [-0.199, +0.149] |

Also: coordinate descent over 11 numeric constants head-to-head (`results/h2h1`) accepted nothing
(all trials inside noise 1.30-1.42 vs reference 1.35; TRAIL_WALL=1 and SHOOT_RANGE=46 clearly worse).

Conclusion: no challenger beat the candidate with a positive 95% lower bound. The threat-gated lock moves
goal difference up slightly (-0.158 -> -0.03/+0.02) at no measurable cost in points, but the gain is inside noise,
so it is NOT promoted. Nothing here modifies main or the champion.

## Challenger that beats the champion candidate: stiff goal-line wall

Finding (from 60 recorded candidate-vs-candidate matches, `sandbox_h2h/goals_scan.py`):
- the first scorer wins about two thirds of matches; the lock fails to hold in about 22% of them
- 12 of 105 goals are own goals, but all are opponent shots deflected by a defender's last touch, so they are not a bug
- equalisers against the lock happen when the wall is pushed apart (players ended 3-4.5 apart, so the ball fits through).
  The lock moved each player at speed `distance/1.5`, so a displaced player came back slowly and attackers could walk the wall apart.

Change (one line, `candidates/challenger_stiff_wall.py`, sha256 prefix cd42787b2c53): `LOCK_RAMP = 0.2` replaces the 1.5 in
`s = 1.0 if d > LOCK_RAMP else d / LOCK_RAMP`. A displaced wall player drives back at full speed until it is within 0.2 of its slot.
Nothing else differs from `champion_candidate.py`.

Head-to-head against `champion_candidate.py` (challenger vs candidate, both sides and kickoffs, paired against candidate-vs-itself):

| Set | Seeds | n | pts/match (ref -> challenger) | GD (ref -> challenger) | paired diff, 95% CI |
|---|---|---|---|---|---|
| dev (setting picked here; ramp 0.5 gave +0.18, 0.2 gave +0.25) | 30500-30559 | 120 | 1.183 -> 1.433 | -0.158 -> 0.000 | +0.25 [+0.07, +0.43] |
| validation | 31000-31079 | 160 | 1.400 -> 1.650 | -0.006 -> +0.138 | +0.25 [+0.09, +0.41] |
| confirmation 1 | 33000-33099 | 200 | 1.420 -> 1.495 | -0.005 -> +0.040 | +0.075 [-0.06, +0.21] |
| confirmation 2 | 34000-34099 | 200 | 1.335 -> 1.610 | -0.055 -> +0.110 | +0.275 [+0.14, +0.41] |

Pooled over the three sets not used to choose the setting (n=560, inverse-variance): +0.19 points per match, 95% CI [+0.11, +0.27].
Ramp 0.05 matched ramp 0.2 on the validation set (+0.25), so the setting is not on a knife edge.

Reliability: 0 fouls and 0 policy errors in every run. Raw timeouts 18 vs 12 over the 560 confirmation matches, with two jobs sharing two cores (both files show occasional timeouts; the change adds no computation).
`start.sh check` on a folder holding the challenger as team.py: PASSED.

Pool (champion_original, lock_no_breaker, press_formation, bus_wall, dribbler, structured_attack, ball_chaser, balanced; seeds 32000-32019, challenger vs candidate on the same units):
strong opponents +0.05 [+0.001, +0.099], weak opponents -0.013 [-0.037, +0.012] (one goal against ball_chaser); no errors, 0 fouls.

Caveats: the local pool cannot reproduce the real top teams, so this is evidence against a copy of the candidate, not against the live ladder.
The effect on the third set alone was small; the pooled estimate (about +0.2) is the honest size, not the first +0.25.
Not promoted: nothing here modifies main or the champion.
