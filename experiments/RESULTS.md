# Superseded keeper-intermediate results

**This is not the submitted version.** Its keeper changes were subsequently
reverted after inconclusive self-play. Source is frozen in `keeper-selected/`.
See `SUBMISSION_RESULTS.md` for the actual final file and measured results.

Submission: `../my-team/team.py`, `AdaptiveChampion`, version
`champion-hunt-adaptive-1.3`.

SHA-256:
`d105483de14ee29f403b872c054bd807ba8041078f8fb34bf941efc608632a69`.

## Paired reference comparison

Both versions played **the same 540 fixtures**, through the official simulator
and SDK, at 2,400 ticks and a 20 ms decision deadline. The baseline is the
existing TITAN file saved before editing, not the repository's weak starter.

| Metric | Existing TITAN | Selected submission |
|---|---:|---:|
| Matches | 540 | 540 |
| Wins / draws / losses | 539 / 1 / 0 | 539 / 1 / 0 |
| Goals scored / conceded | 567 / 15 | 567 / 15 |
| Total goal difference | +552 | +552 |
| Mean goal difference | +1.0222 | +1.0222 |
| Mean decision time | 0.06519 ms | 0.06476 ms |
| Slowest decision | 23.8639 ms | 11.8704 ms |
| Decisions measured | 1,296,000 | 1,296,000 |
| Decisions over 20 ms | 4 | 0 |
| Policy errors | 0 | 0 |

The demonstrated gain is deadline reliability while preserving the score
record. These results do **not** establish a higher competitive win rate.
Latency is measured on this Windows machine, not guaranteed on the server.

| Opponent, 180 fixtures each | Before W/D/L | After W/D/L | Before goals | After goals |
|---|---:|---:|---:|---:|
| balanced | 179/1/0 | 179/1/0 | 193–9 | 193–9 |
| tactical | 180/0/0 | 180/0/0 | 190–6 | 190–6 |
| possession | 180/0/0 | 180/0/0 | 184–0 | 184–0 |

Per opponent, 40 fixtures use seeds 1000–1019 and SDK side swaps; 100 use
2000–2049 and SDK side swaps; 40 use 4000–4009, **both field sides and both
kickoff owners**. Raw before reports are `original-*`, `original-holdout-*`,
and `original-fair-*`. Raw final reports are `selected-training-*`,
`selected-holdout-*`, and `selected-fair-*` under `results/`. Every raw final
report records the submission hash above. All benchmark platform-error counts
are zero.

## Official acceptance and targeted tests

Executed successfully on the selected file:

```powershell
python tools/test_titan.py
python launch.py check my-team
python launch.py validate my-team --against tactical --ticks 2400 --json
git diff --check
```

- **11 focused tests passed.** They reproduce the older trailing-wall bug at
  0–2, 1–3 and 2–5, verify the selected policy continues normal play even if
  someone sets a legacy `TRAIL_WALL` attribute, preserve positive-lead walls,
  verify the specialist does not activate its bait wall when trailing, check
  legal formation and finite actions, exercise slow goal-bound balls and
  nonthreatening trajectories, and verify complete actions with zero optional
  search budget. These score scenarios are logical policy tests, not claims
  that the official simulator was initialized at those scores.
- Official `check my-team`: **PASSED**, loads and plays legally inside deadline.
- Official full-length tactical validation: **PASSED**, 5 public seeds,
  **12,000 decisions**, mean **0.034 ms**, maximum **5.391 ms**, no warnings,
  exceptions, deadline overruns, missing actions or non-finite values. Custom
  five-player formation accepted without correction.
- `git diff --check`: passed. Only the experimental branch was modified.

## Selection evidence

The initial 40-match TITAN comparison used seeds 3000–3019 with the SDK's
side-swap protocol. These are exploratory samples, not independent estimates
of general superiority:

| Frozen variant | W/D/L | Goals |
|---|---:|---:|
| Original against original | 14/14/12 | 74–74 |
| Keeper guard | 14/16/10 | 78–75 |
| Keeper plus experimental shot model | 16/15/9 | 80–74 |
| Shot model, budget and safer keeper sweep | 15/17/8 | 81–75 |
| Added deeper central screen | 16/11/13 | 78–76 |

The central screen was reverted because losses increased from 8 to 13. The
experimental shot model was also reverted after its 300-match reference
holdout: it turned one possession win into a draw and scored 312 goals against
the baseline's 313. Removing it restored the original 313–9 holdout score and
299/1/0 record. Its intermediate results labelled `final-*` must not be mistaken
for the selected submission; they refer to `with-shot-final/team.py`.

See `README.md` for provenance, exact commands, kickoff-protocol details and
the limits of the available opponent replay evidence. The existing attacking
and marking systems remain intact; no benchmark against Gabriel Behane or
Kevin Ebrahim is claimed.
