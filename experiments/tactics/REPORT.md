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
