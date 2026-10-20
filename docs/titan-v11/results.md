# TITAN v11 — Passing Lane Architect and Counterattack Firewall

**Development decision: RETAIN_V10_REJECT_BOTH.** No active champion or main changes.

## Scope and method

Two independent, movement-only additions to frozen Guardiola/Klopp TITAN v10.0. The all-off source preserves v10 actions, debug and receive plans. Goalkeeper Power Play, Goalkeeper Trap, Pinball Slingshot and Cooldown Ambush are absent from these sources. No combined source was tested unless both independent candidates passed.

Eight unused development seeds × pressing, compact and counterattacking v10 opponents × both sides × both kickoffs = 96 paired configurations, 288 native full matches. Sources, opponent archive, seeds, shuffle order and selection rules were frozen before play. Every fixture used 2,400 ticks, engine 0.1.0, configuration 372990895c7eca2a and the unchanged native 20 ms deadline. One timed worker, no concurrent tests.

An initial trial (73 completed full matches, excluded from selection) was interrupted on a code-review finding before outcome analysis: team-control metadata without a friendly holder could have bypassed the existing cover safeguard. The final source requires a friendly controlling player as well as team control and no opposing last touch. Every seed allocated to the interrupted protocol, including its reserves, was excluded before registering the final cohort. Partial raw native records, frozen old sources and protocols are retained. No interrupted score was used for tuning.

The three styles are frozen local strong v10 variants, not private league teams. Source hashes are retained in registration, protocol and native metadata; unused integration and qualification cohorts are reserved separately.

## Implementation

- **Tactic 05, Passing Lane Architect:** examines at most two free supporters, three local targets and two pass speeds. Existing carrier-contact, dense drag/trajectory simulation, defender races and executable receiver rollouts validate each prospective lane, including the exact first movement with teammate avoidance. Predicted defender separation helps rank lanes. Teammate interference is rejected. The established pass selector still chooses actual passes, and new receive plans own their movement. The carrier, keeper, both cover assignments, chaser and live receiver are excluded. Existing transition bursts, counterpress and restart restrictions take priority. Speculative receiver-aim state is restored.
- **Tactic 06, Counterattack Firewall:** projects opposing outlets 0.6 seconds from public velocity, ranks plausible pass-plus-run routes toward our goal, and screens the quickest threatening corridor using the existing cover defender. Its target never advances beyond the baseline cover line, stays within 12 metres of its depth and an 18-metre displacement budget, and requires a reachable guard position. It cannot move a carrier, chaser, goalkeeper or live receiver. At possession loss or opposing touch it releases immediately to unchanged v10 defensive interception, counterpress and cover safeguards; there is no persistent attack target.
- Every original v10 method except the two call sites in `act` is AST-identical. There is no new pass/shot policy, goalkeeper logic, physics routine, game configuration or deadline.

## Original raw native outcomes

| Source | Matches | Wins | Draws | Losses | Points | GF–GA | Completed passes | Turnovers | Deadline misses | Exceptions |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| v10 | 96 | 36 | 25 | 35 | 133 | 121–115 | 2047 | 587 | 1 | 0 |
| architect | 96 | 43 | 17 | 36 | 146 | 121–114 | 2054 | 572 | 0 | 0 |
| firewall | 96 | 38 | 23 | 35 | 137 | 117–120 | 2077 | 601 | 1 | 0 |

Timeout repeats never erase raw misses or original competitive outcomes. Raw and accepted/repeat comparisons are both retained; a candidate must pass both point/significance requirements.

## Statistical selection and reliability

The preregistration requires strictly positive 97.5% whole-seed bootstrap lower bounds and one-sided exact sign-flip p ≤ 0.025 for each candidate (a correction for two independent tactic hypotheses), more raw and accepted points, no points regression in any registered style, at least five executed tactic episodes, and the tactic-specific intent metric. Architect needs more completed passes without more turnovers; Firewall needs fewer concessions. All existing SDK, legality, exception, deadline/reproducibility and runtime gates also apply. The original 768-pair minimum is a qualification gate; it is not waived for promotion or treated as a development fixture requirement.

| Candidate | Raw PPM delta | 97.5% seed interval | Exact p | Accepted mean ms | Raw max ms | Episodes | Development supported |
|---|---:|---|---:|---:|---:|---:|---|
| architect | +0.135417 | [-0.19791666666666666, 0.39583333333333337] | 0.222656 | 0.266562 | 18.154390 | 297 | False |
| firewall | +0.041667 | [-0.13541666666666669, 0.20833333333333331] | 0.343750 | 0.242428 | 34.268050 | 296 | False |

### architect actual commands and failures

Telemetry counts (support/screen are executed movements; loss release is a state event): `{"architect_support": 375}`.

Team-level episodes: `{"architect_support": 297}`.

Failed development gates: positive_raw_97_5_seed_lower, positive_accepted_97_5_seed_lower, raw_exact_sign_flip_p_at_most_0_025, accepted_exact_sign_flip_p_at_most_0_025, no_style_points_regression.

| Opponent | v10 points | Candidate points | v10 GF–GA | Candidate GF–GA |
|---|---:|---:|---|---|
| v10-press | 45 | 58 | 44–40 | 43–30 |
| v10-compact | 57 | 50 | 37–20 | 38–26 |
| v10-counter | 31 | 38 | 40–55 | 40–58 |

### firewall actual commands and failures

Telemetry counts (support/screen are executed movements; loss release is a state event): `{"firewall_loss_release": 2771, "firewall_screen": 1771}`.

Team-level episodes: `{"firewall_loss_release": 2365, "firewall_screen": 296}`.

Failed development gates: positive_raw_97_5_seed_lower, positive_accepted_97_5_seed_lower, raw_exact_sign_flip_p_at_most_0_025, accepted_exact_sign_flip_p_at_most_0_025, no_style_points_regression, intent_metric.

| Opponent | v10 points | Candidate points | v10 GF–GA | Candidate GF–GA |
|---|---:|---:|---|---|
| v10-press | 45 | 43 | 44–40 | 39–42 |
| v10-compact | 57 | 59 | 37–20 | 37–24 |
| v10-counter | 31 | 35 | 40–55 | 41–54 |

## Attribution and limitations

Support and screen labels are counted only if the final issued player movement matches the proposed tactic movement, changes the baseline movement meaningfully, and the SDK accepts the decision under 20 ms without error. The loss-release label records relinquishing tactical ownership; it is a state event, not a new movement or a prevented counterattack. Supporter commands can occur twice in a tick; episodes are team-level groups separated by more than five ticks without the same label. A movement command is not proof of a completed pass or a prevented goal. Native total passes, turnovers, goals, wins and points above are actual engine results; five-second post-command associations in JSON are explicitly non-causal. No goals are credited to a tactic simply because it activated.

Eight seed blocks limit precision and fixed local opponents limit generalization. All sources and thresholds were frozen before outcomes; these results were not used to tune the same cohort.

## Verification and reproduction

133 controller regressions passed before native testing, including original safety/physics checks and 13 new tests for method equivalence, all-off equivalence, role authority, executable lanes, defender motion, immediate loss release and telemetry command ownership. Four additional statistical-analysis regressions passed after matches, checking exact sign-flip probabilities, zero-effect intervals and paired-fixture integrity (137 tests total). Native SDK intakes and static inspection are retained for each tested source.

`python tools/titan_v11/build.py` reproduces isolated source hashes. With the bundled official native extension installed, run `PYTHONPATH=student-sdk python -m unittest discover -s tests -q`, then `PYTHONPATH=student-sdk python tools/benchmarks/run_titan_v11.py --protocol docs/titan-v11/development-protocol.json --out /new/output/path`. Analyze with `python tools/titan_v11/analyze.py --run /new/output/path --out /new/results.json`. Keep one timed worker.

The native evidence archive retains raw/accepted full-match rows, official validation, frozen sources/opponents, slow decisions, timing histograms, cgroup diagnostics and exact timeout repeats with a verified per-file SHA-256 manifest.

## Interpretation

Architect gained 13 points, completed 7 more passes and recorded 15 fewer turnovers. Its gains were uneven; the per-opponent table shows the compact-opponent regression alongside the gains against pressing and counterattacking opponents. The broad seed interval and exact p-value do not establish a reliable overall advantage; the compact regression also fails the preservation gate.

Firewall gained 4 points but conceded 5 more goals and recorded 14 more turnovers. The screening commands did not achieve the tactic's concession-reduction objective. Its points estimate is also statistically inconclusive.

The baseline and Firewall each had one raw native deadline miss; Architect had none. First exact repeats were clean and no candidate deadline failure reproduced. The raw misses remain counted; none was waived as environmental noise. All intakes, action-legality, exception and runtime gates passed.

**Both candidates are rejected for competitive use. No combination, fresh qualification or promotion was run.** Retaining their code as experiments does not establish an improvement; v10 remains the champion.
