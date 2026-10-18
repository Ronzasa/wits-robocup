# TITAN-11 tactical intelligence — independent validation

**Retain v10.0: TITAN-11 did not pass every promotion gate.** The active `my-team/team.py` remains byte-for-byte v10.0. `main` was never modified. No local result is presented as an online league-ranking gain.

The standalone challenger is [`experiments/titan-11/team.py`](../experiments/titan-11/team.py), SHA-256 `485e8dea6a7ea13fc3d881bf735662d4aabecc177681d98971193056419bac35`. The exact champion is [`champions/v10.0/team.py`](../champions/v10.0/team.py), SHA-256 `5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6`.

## Fresh competition result

768 paired fixtures, 16 previously untouched independent seed blocks, 12 frozen opponents, both pitch assignments and both kickoff arrangements. Every match ran 2,400 ticks with the unchanged native 20 ms deadline. The candidate and validation protocol were committed before independent play began. Primary football scores use first-clean exact repetitions; every initial raw result and failed repeat is retained and separately reported.

| Controller | Points | W/D/L | Goals for–against | Pass completion | Turnovers | Accepted mean ms | Initial raw misses |
|---|---:|---:|---:|---:|---:|---:|---:|
| v10.0 | 1387 | 409/160/199 | 1334–764 | 52.37% | 4360 | 0.2048 | 5 |
| TITAN-11 | 1454 | 436/146/186 | 1519–781 | 54.74% | 4330 | 0.2128 | 8 |

Paired points-per-match difference: **+0.087240**, whole-seed paired bootstrap 95% interval **[-0.037760416666666664, 0.21223958333333331]**. Raw points: 1387 versus 1454; raw paired interval [-0.037760416666666664, 0.21223958333333331]. Additional initial raw deadline misses per 1,000 fixtures: **3.906250**, allowed maximum 2. Zero-policy-exception gate: True.

Raw p99 timing bins: v10 [1.9, 1.925] ms; challenger [2.0, 2.025] ms. Raw p99.9 bins: v10 [4.05, 4.075] ms; challenger [3.45, 3.475] ms. Worst initial raw decision: v10 69.382779 ms; challenger 127.912921 ms. Accepted-mean ceiling: 0.316538 ms.

Failed gates: **positive_paired_95_lower, raw_deadlines**. Final full gate inputs and per-opponent native statistics: [`final-gates.json`](titan-11-intelligence/final-gates.json). No failed cohort was pooled with another cohort to obtain significance, no fresh result was used to tune source, and no timeout was removed from the raw deadline calculation.

## Implemented systems and selection

All six systems have working standalone source variants and native ablations. The final enabled subset is **predictive, playbooks, learning**. Other components remain implemented and disabled; this is intentional rather than deploying every experiment regardless of evidence.

1. **Predictive planning:** original shot/link/wall/carry proposals plus two executable empty-space pass candidates; one baseline leaf plus at most two challenger leaves. Public acceleration, damping, cooldown, friction, actual first-tick carrier contact, receiver commands and opponent interception are reused. Scoring combines progression, retention, recovery support and counter exposure. The beam and action-family proposal retention have deterministic fixed caps.
2. **Five-player coordination:** dynamic two-outlet triangles, role-sensitive depth/width, verified-regain runs, joint pass/support evaluation, third-man runs during a verified pass in flight, rebound follow-up and retained cover. Existing goalkeeper, chaser and verified receiver commands remain protected in target planning. The original flight-inactive version is archived and its separate native result retained.
3. **Finishing:** two executed goalkeeper responses, momentum/cooldown, full-route physical defender checks, additional legal wall direction and two reduced-power trials. The fitted shot signal uses native two-second conversion labels; small calibration groups are poor, so it is not advertised as calibrated xG. Original direction-only and complete power variants are evaluated separately.
4. **Threat defence:** predicted opponent progression and central receiving danger, small deterministic guard assignment, selective extra pressure only after recent dangerous loss, protected primary roles and immediate restoration after regain. This is not a permanent deep formation. The football ablation, rather than geometry alone, decides whether it is enabled.
5. **Playbooks:** independently evaluated legal initial formation, own opening circulation, guarded second pass, abort-on-failed-execution conditions, goalkeeper distribution, restitution-aware wall switch and inherited verified end-wall recovery. Opponent protected-restart targets are not overridden. There is no hidden state, seed-specific tactic or physics change.
6. **Offline learning/self-play:** native-labelled compact linear value fit and logistic conversion signal, an archived champion/style league plus generated legal specialists and parent self-play, and four preregistered derivative-free parameter designs. Trained coefficients are embedded directly. Inference imports only `math` and the official SDK; no file/model reads, network, clocks or external dependency.

The conservative runtime reach bound preserves successful physical witnesses. It never substitutes heuristic ETA for pass feasibility. The ordinary heuristic `_intercept` and original movement/collision/reception mechanics are retained. Official `act` supplies the current public observation to each tactical decision.

Enabled/disabled details:

- `predictive`: enabled after development ablation/integration selection.
- `coordinated`: disabled — removed by integration/search selection.
- `finishing`: disabled — higher_fresh_points, positive_paired_95_lower, no_repeated_deadline_failure.
- `defence`: disabled — higher_fresh_points, positive_paired_95_lower.
- `playbooks`: enabled after development ablation/integration selection.
- `learning`: enabled after development ablation/integration selection.

## Development and feature ablations

The complete initial screen, explicit power/flight refinement screen, all-feature and leave-one-feature-out integrations and finite self-play search are preserved. Development confidence intervals based on only two seed blocks are weak and were not treated as independent promotion evidence. The final cohort has 16 independent blocks. The registrations prohibit carrying an individually rejected component into the release and prohibit tuning on final results.

| Stage/source | Matches | Points | Goals for–against | Raw misses | Accepted mean ms |
|---|---:|---:|---:|---:|---:|
| ablations/v10 | 64 | 96 | 106–87 | 0 | 0.2033 |
| ablations/runtime | 64 | 96 | 106–87 | 2 | 0.2001 |
| ablations/predictive | 64 | 108 | 130–80 | 0 | 0.2091 |
| ablations/coordinated | 64 | 115 | 137–104 | 1 | 0.2298 |
| ablations/finishing | 64 | 96 | 106–87 | 0 | 0.2034 |
| ablations/defence | 64 | 85 | 99–93 | 0 | 0.2073 |
| ablations/playbooks | 64 | 107 | 88–60 | 0 | 0.1965 |
| ablations/learning | 64 | 101 | 111–84 | 0 | 0.2011 |
| finishing-power/v10 | 64 | 96 | 106–87 | 1 | 0.2026 |
| finishing-power/finishing | 64 | 61 | 63–108 | 0 | 0.2024 |
| finishing-power/coordinated | 64 | 105 | 143–96 | 0 | 0.2362 |
| integration-0/v10 | 64 | 96 | 106–87 | 0 | 0.2007 |
| integration-0/all | 64 | 87 | 131–121 | 0 | 0.2491 |
| integration-0/all-minus-predictive | 64 | 84 | 121–111 | 1 | 0.2379 |
| integration-0/all-minus-coordinated | 64 | 110 | 94–58 | 1 | 0.2115 |
| integration-0/all-minus-finishing | 64 | 88 | 133–116 | 1 | 0.2506 |
| integration-0/all-minus-defence | 64 | 108 | 150–104 | 0 | 0.2400 |
| integration-0/all-minus-playbooks | 64 | 108 | 138–93 | 0 | 0.2371 |
| integration-0/all-minus-learning | 64 | 80 | 128–126 | 0 | 0.2426 |
| integration-0/selected | 64 | 116 | 160–111 | 0 | 0.2403 |
| integration-0/selected-minus-predictive | 64 | 117 | 143–100 | 0 | 0.2335 |
| integration-0/selected-minus-coordinated | 64 | 123 | 109–60 | 0 | 0.2036 |
| integration-0/selected-minus-playbooks | 64 | 118 | 156–82 | 2 | 0.2422 |
| integration-1/v10 | 64 | 96 | 106–87 | 2 | 0.2010 |
| integration-1/selected-minus-learning | 64 | 117 | 161–110 | 1 | 0.2395 |
| optimization/v10 | 64 | 99 | 85–81 | 0 | 0.1963 |
| optimization/parent | 64 | 90 | 86–91 | 1 | 0.2027 |
| optimization/search-0 | 64 | 79 | 72–89 | 0 | 0.2054 |
| optimization/search-1 | 64 | 115 | 122–85 | 0 | 0.2069 |
| optimization/search-2 | 64 | 106 | 111–88 | 0 | 0.2076 |
| optimization/search-3 | 64 | 71 | 67–94 | 2 | 0.2064 |

## Diagnostics, measurement limits and reproducibility

The diagnostic capture, exact model training samples/native results, original source hashes, all raw/first-clean match records, failed repeats, runtime histograms and CPU/wall/cgroup observations are archived with a digest manifest. Instrumented diagnostics and replays are excluded from strength and official latency inference. Original rare wall-time spikes have no per-call CPU/GC trace; repeat evidence alone cannot assign their cause to the environment or controller.

Per-fixture data: [`per-fixture.csv`](titan-11-intelligence/per-fixture.csv). Full aggregate/per-opponent native counters, pass accounting, conversion, possession and control: [`metrics.json`](titan-11-intelligence/metrics.json). Deadline cases: [`deadline-cases.json`](titan-11-intelligence/deadline-cases.json). Exact definitions and proxy limitations: [`measurement-notes.md`](titan-11-intelligence/measurement-notes.md). Model calibration: [`fit-report.json`](titan-11-intelligence/fit-report.json). Native diagnostic replay results are separately archived.

All original regressions and focused subsystem tests are run with the selected candidate. Official intake validates exactly one controller in a single `team.py` and five public seeds at 400 ticks each. Audit output records the exact test count, source hashes and validation result.

From the repository root (Python with the official SDK available):

```sh
python -m unittest discover -s tests -q
ROBOCUP_TEAM_PATH="$PWD/experiments/titan-11/team.py" python -m unittest discover -s tests -q
python tools/benchmarks/run_intelligence.py --protocol docs/titan-11-intelligence/validation-protocol.json --out /workspace/work/titan11-validation-reproduction
python tools/titan11/evaluate.py /workspace/work/titan11-validation-reproduction
python tools/titan11/train.py --traces tests/fixtures/titan-11-native-training-samples.json.gz --out /workspace/work/titan11-fit-reproduction
```

Use a new output directory every time. These reproduction fixtures have already been used and cannot serve as a new independent promotion cohort. `tools/titan11/build.py` can assemble another isolated challenger from explicit feature flags and JSON parameters; `campaign.py` is the archived finite tournament-selection pipeline. Offline fitting alone requires NumPy (`tools/titan11/requirements.txt`). Diagnostic replay generation uses `tools/titan11/replays.py`; decompress `.native.json.gz` losslessly for the SDK replay viewer.

## Additional final audit and diagnostic evidence

All **117 pre-validation regression tests passed against the selected candidate**. The final suite has **118 passing tests**, including an additional post-validation wall-reception regression that checks collection after a rebound and rejection of a cooldown body block on the first leg. The controller did not change. Official candidate intake passed all five public seeds: 2,000 decisions, zero exceptions, zero missed deadlines and zero missing/non-finite actions. All submitted imports and the single-controller folder passed static inspection. The saved parameter/flag configuration rebuilds the exact registered candidate bytes. See [`final-audit.json`](titan-11-intelligence/final-audit.json).

The corrected exact public-observation replay reproduced **9,600 of 9,600 recorded v10.0 actions** and the same 9,600 runtime-control actions. All complete feature variants plus the selected candidate were checked on those observations. The tactical target hook never changed the protected goalkeeper, chaser or verified recipient target. This is a shared-state regression check; native on-policy tournaments supply the strength evidence.

The 67-point fresh gain was concentrated against v10 compact defence (+34) and v9.1 (+26). Against v10.0 itself the gain was only 2 points. Across the four held-out styles, points were **557 → 560**, a gain of **3 over 256 fixtures**. The eight development styles on fresh seeds supplied the other 64 points. These results do not establish broad superiority against strong unseen opponents. See [`style-splits.json`](titan-11-intelligence/style-splits.json).

Passing attempts rose from 30,035 to 31,973, and completed passes from 15,729 to 17,501. Completion improved from 52.37% to 54.74%. Derived uncollected passes rose from 5,963 to 6,207; their share fell from 19.85% to 19.41% because attempts increased. Native possession and control both fell slightly. Native goal-per-shot ratio fell from 45.08% to 43.88%, while shots increased from 2,959 to 3,462. More goals and passes did not satisfy the match-points confidence or raw-reliability gates.

Eight instrumented exact fixture repetitions, covering two original candidate timeout fixtures and two baseline timeout fixtures, did not reproduce a deadline miss. The largest new diagnostic wall time was 4.692 ms. Original per-call CPU/GC traces are unavailable, so the cause of the original 69.383/127.913 ms peaks remains unknown. Original raw misses **5 → 8**, all first-clean repeats and environment records remain intact. The additional 3.90625 raw misses per 1,000 fixtures exceed the allowed 2. Repetition results do not erase that failure. The school's historical reliability counter cannot be explained by these local diagnostics.

An extra post-qualification public intake check found **one 26.787 ms decision in 2,000 calls** for the generated possession *training opponent*. Its format, actions and imports were valid and it raised no exceptions. One exact diagnostic repeat had zero misses (maximum 4.478 ms). The initial failure remains recorded; that opponent is not certified reliable by this project. It appeared in optimization, and was absent from the 12-opponent final validation cohort. The selected submitted candidate's own public intake passed. See the original [`generated-opponent-intakes.json`](titan-11-intelligence/generated-opponent-intakes.json) and separately labelled repeat. The interrupted post-check script log is retained in the evidence archive.

Four fixed, paired development diagnostic matches showed 4–8 goals for v10.0 and 9–3 for the selected source. Their counter-concession proxy was 2 versus 0; danger-contact ticks were 281 versus 195. Intended receiver touches were 58 of 68 planned releases versus 62 of 82 (one candidate plan was still in flight at trace end); other teammate touches accounted for 9 versus 17. Native completion counts any teammate, so these measures have different definitions. Own wall-route proxies were 23 versus 20, with 9 versus 6 subsequent own recoveries. These small diagnostic samples are descriptive. The complete tournament conceded 17 more goals; the four-game diagnostic cannot establish better defence. Exact restart windows, wall proxies and reception outcomes are in [`paired-diagnostic-metrics.json`](titan-11-intelligence/paired-diagnostic-metrics.json).

Native SDK replays and public-frame traces preserve both successful and failed development cases. Scores below are canonical **ours–theirs**; the raw replay uses its recorded physical field assignment. All eight diagnostic replay scores reproduced their archived formal-development scores exactly.

| Source/case | Opponent | Seed | Physical source slot | Ours–theirs |
|---|---|---:|---:|---:|
| Selected controller, 0-baseline | wall-specialist | 483341721 | 1 | 0–3 |
| Selected controller, 0-challenger | wall-specialist | 483341721 | 1 | 4–3 |
| Selected controller, 1-baseline | v10-counter | 1267476391 | 1 | 3–2 |
| Selected controller, 1-challenger | v10-counter | 1267476391 | 1 | 1–3 |
| Rejected finishing, 0-baseline | v10-press | 442797613 | 0 | 2–3 |
| Rejected finishing, 0-challenger | v10-press | 442797613 | 0 | 2–1 |
| Rejected finishing, 1-baseline | v9.1 | 442797613 | 0 | 3–2 |
| Rejected finishing, 1-challenger | v9.1 | 442797613 | 0 | 0–2 |

The compact model was independently refitted from the exported native feature/label dataset and produced exactly equal embedded coefficients. The retained dataset contains every feature/label used in fitting and all 64 native training results, plus the full original trace digest. It avoids committing the unused 77 MB of redundant per-tick training snapshots; regenerate those with `diagnose.py --training` if needed.

The campaign contains **3,520 scheduled full native matches**, **8,448,000 source-side decisions**, **28 initial source-side raw deadline misses across all baselines and experiments**, and **zero policy exceptions**. Failed unit-fixture prototypes and all diagnostics are separately labelled and archived; they are not promotion evidence. Neither `main`, the active controller, earlier experiments, the engine, SDK nor rules/configuration were changed.

Download [`native-evidence.zip`](titan-11-intelligence/native-evidence.zip) for the complete preserved raw/accepted fixture records, repeats, timing histograms, environment records, source snapshots, diagnostic replays and audit logs. [`archive-audit.json`](titan-11-intelligence/archive-audit.json) records the digest and verifies every archive-manifest entry. The official browser viewer can inspect a decompressed `.native.json` replay tick by tick.

Two early shared-state diagnostics reconstructed controlling team from the holder. They are superseded by `exact-native-verification.json`, which reconstructs the actual public team flag and requires every replayed baseline action to equal the recorded native action. Earlier diagnostic and unit-fixture logs are retained for provenance; synthetic fixture failures are separate from the zero policy-exception count in formal native matches.

No CPU-quota throttling was recorded in any of the 11 final-validation fixtures containing source-side deadline events (13 calls total). Fixture-level observations cannot identify the CPU/GC behaviour of the original slow call. See [`deadline-environment-summary.json`](titan-11-intelligence/deadline-environment-summary.json).
