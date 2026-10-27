# MONSTER–NOVA hybrid research

**Experimental branch only. No champion replacement.**

Decision: **no qualified hybrid upgrade**.
Rejected for promotion: at least one original qualification gate failed.

The uploaded MONSTER16 (`e4987079…`) and NOVA/div1.py (`b10d9637…`) are frozen.
The selected experimental `team.py` is NOVA's movement, receiving and kick
evaluation with up to three MONSTER gap-aim candidates against a visible packed
goal-line wall. NOVA still evaluates and chooses the kick. This is a small shot
search change, not a transplant of MONSTER's permanent four-player home defence.
It is **not evidence of a Division 1 ranking**.

## Broader development

Eight frozen opponent styles, two fresh development seeds, both sides, both
kickoffs and two formation profiles: 128 full matches per controller.

| Controller | Points | W–D–L | Goals for–against | SDK errors | Raw misses | Mean / max ms |
|---|---:|---:|---:|---:|---:|---:|
| Original NOVA | 318 | 98–24–6 | 443–9 | 0 | 0 | 0.071 / 14.293 |
| Original MONSTER16 | 243 | 62–57–9 | 95–22 | 0 | 0 | 0.038 / 5.306 |
| Gap-aiming hybrid | 319 | 98–25–5 | 442–8 | 0 | 0 | 0.067 / 12.352 |

The one-point development lead was sufficient only for the preregistered advance
to qualification. It was not accepted as proof of a stronger controller.

## Untouched qualification

One candidate was frozen before any qualification fixture. Eight untouched seeds,
eight styles, balanced sides/kickoffs and both formation profiles: 512 matches
per controller. All 1,536 fixtures were completed, with no qualification tuning,
early stopping or optional seed extensions.

| Controller | Points | W–D–L | Goals for–against | SDK errors | Raw misses | Mean / max ms |
|---|---:|---:|---:|---:|---:|---:|
| Original NOVA | 1287 | 400–87–25 | 1914–57 | 0 | 1 | 0.066 / 34.915 |
| Original MONSTER16 | 897 | 219–240–53 | 335–95 | 0 | 0 | 0.037 / 18.308 |
| Gap-aiming hybrid | 1283 | 397–92–23 | 1932–55 | 0 | 1 | 0.067 / 24.286 |

| Paired comparison | Points / fixture difference | Seed-block bootstrap 95% CI | Additional raw misses / 1,000 fixtures |
|---|---:|---:|---:|
| gaps − baseline | -0.0078 | [-0.0352, +0.0176] | +0.000 |
| gaps − monster16 | +0.7539 | [+0.6914, +0.8203] | +1.953 |

Qualification points by opponent, 64 fixtures per controller per style:

| Opponent | NOVA points | MONSTER16 points | Hybrid points | Hybrid goals |
|---|---:|---:|---:|---:|
| monster-wall | 61 | 66 | 57 | 5–15 |
| nova-self | 74 | 90 | 74 | 30–30 |
| v10-compact | 192 | 75 | 192 | 291–0 |
| v10-press | 192 | 109 | 192 | 362–5 |
| team12 | 192 | 184 | 192 | 213–1 |
| v10-counter | 192 | 142 | 192 | 370–2 |
| v9.1 | 192 | 125 | 192 | 354–1 |
| strong-replay | 192 | 106 | 192 | 307–1 |

Registered gates:

- baseline: positive_paired_95_lower: **FAIL**.
- baseline: additional_raw_deadline_misses_per1000: **PASS**.
- baseline: worst_style_decline: **PASS**.
- baseline: worst_formation_profile_decline: **PASS**.
- monster16: positive_paired_95_lower: **PASS**.
- monster16: additional_raw_deadline_misses_per1000: **PASS**.
- monster16: worst_style_decline: **PASS**.
- monster16: worst_formation_profile_decline: **PASS**.
- zero_policy_exceptions: **PASS**.
- official_intake: **PASS**.
- single_sdk_class: **PASS**.
- code_bytes_max: **PASS**.

Bounded timing diagnostics (original qualification misses remain counted):

- baseline: 3 exact-fixture reruns; 0 deadline misses, 0 SDK errors; max 3.413 ms.
- gaps: 3 exact-fixture reruns; 0 deadline misses, 0 SDK errors; max 1.727 ms.

Failure to reproduce a spike does not establish an environmental cause. No timing event was excluded.

## Independent experiments and rejected components

| Isolated change | Development outcome | Decision |
|---|---|---|
| Projected defensive block/cover targets in NOVA | 113 vs NOVA 129 points; 22 vs 12 conceded | Reject; partial geometry does not retain MONSTER's full defensive unit |
| MONSTER gap aims in NOVA | 130 vs NOVA 129 points | Sole component advanced to broader development and qualification |
| Near-post duel on the carrier's own dribble | 161 eligible checks, zero overrides; tied NOVA | Inactive; do not combine |
| Whole defensive-engine switch only at goal resets, leading in final minute | 42 switches, 65,843 MONSTER decisions; tied NOVA on points | No points gain; do not combine |
| MONSTER movement with NOVA kicks/receiving | Original prototype 86 vs MONSTER 90; then discovered cache alias mutation | Excluded from selection; raw evidence retained |
| Corrected ball-control transplant | 84 vs MONSTER 90; 24–14 vs 24–10 goals | Reject; improved pass completion did not improve winning |

The cache correction copies NOVA's outer action dictionary before movement
overlays. NOVA can return the dictionary stored in its short-lived action cache.
The original prototype fails the added cache regression; the corrected version
passes it. Its results were recorded separately, never overwritten.

## Method and reliability limits

- All fixtures use the unchanged native engine 0.1.0, official config
  `372990895c7eca2a`, 2,400 ticks and the actual 20 ms SDK decision accounting.
- One timed worker at a time; fresh interpreter for each fixture. Original NOVA
  calls `gc.freeze()` at import. New hybrid sources omit that global side effect;
  the original upload is byte-identical and isolated between fixtures.
- The `default` profile uses native default rosters. The `controller` profile
  applies each controller's official initial formation before reset. For policies
  without a custom formation these setups can coincide; they are not independent
  seed samples.
- Confidence intervals resample whole seeds over all matched opponents, sides,
  kickoffs and profiles. Repeated development cohorts are not pooled as fresh
  independent evidence. Eight qualification seeds remain a limited sample.
- Raw deadline events from **both** teams remain in every record, including
  opposing-controller events. No event was deleted or attributed to the host
  without evidence. Gate calculations use each tested controller's own events.
- A temporary execution-tool connection loss occurred during qualification. The
  same native batch process continued and its files remained intact; no fixture
  restart, replacement run or seed change was needed. The incident is recorded.
- The frozen NOVA `act()` has an internal exception fallback. Its zero SDK errors
  do not prove zero swallowed exceptions. Hybrids call its internal policy directly
  so new errors surface through official SDK accounting.
- `extra_aims` counts proposed shot targets, not accepted kicks, successful
  executions or goals attributable to the feature. Other counters likewise
  describe checks/overrides/mode decisions rather than causal conversions.
- Derived uncollected passes are attempts minus completions minus interceptions;
  the native engine does not provide a separate first-touch quality statistic.
- Fixtures use frozen local opponents. They do not reproduce the live league's
  current opponent population or establish a league division.

## Files and reproduction

- `team.py`: frozen gap-aiming challenger, self-contained, experimental only.
- `evidence.zip`: originals, all variants, opponent snapshots, registrations,
  raw JSONL results, summaries, audits, intake reports, regression logs and tools.
- `decision.json`: machine-readable original qualification gates and decision.

Extract `evidence.zip` and use the official course SDK in `PYTHONPATH`:

```sh
python audit.py phase1 phase1-score phase1-ball phase1-ball-v2 phase2 qualification
python reproduce.py phase2 --out fresh-phase2
```

Use a new output directory, one timed run at a time. The reproducer verifies
source hashes, remaps archived absolute paths, and retains the exact seeds and
fixture arrangements. Native reruns may differ with machine timing and runtime
search budgets. Never overwrite the recorded evidence.

The archived `build.py` is the original experimental builder, with its original
workspace input locations preserved as provenance. The generated single-file
sources are included; rebuilding is not necessary to reproduce matches. Source
paths in old registrations likewise preserve their original locations and are
remapped by `reproduce.py` and `audit.py`.

`main`, active `my-team/team.py`, uploaded originals and archived champions were
not changed. Promotion requires explicit user approval even if every gate passes.

Total recorded full tournament fixtures: **2,816**, including repeated development controls. Timing diagnostic reruns are separate and never pooled into qualification.
