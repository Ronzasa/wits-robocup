# MONSTER Recovery: leaderboard diagnosis and native qualification

The repair fails one or more registered gates and is not an accepted upgrade. Do not promote it.

**Use [restored/team.py](../../experiments/monster-recovery/restored/team.py) for the recovery.** It restores the frozen team12 reference engine, with only the display name/version and explanatory header changed. It introduces no unproven tactical changes and claims no improvement beyond that reference.

The user reports that MONSTER performs worse than team12. They tentatively identified `sandbox-champion-hunt` as team12 ("i think so"). This study therefore uses that branch's frozen controller as the **provisional** team12 reference. The archive does not contain a team12 source file or a submission source hash, so the identity cannot be established from the archive alone.

`main`, `sandbox-champion-hunt`, `my-team/team.py`, archived champions, and the original uploaded MONSTER remain unchanged. All work belongs to experimental branch `monster-recovery`.

## Evidence supplied by the user

`download.zip` contains a HAR named `download.devtools`, with a team statistics response and no match replays. Only a selected own-team summary is published. HAR requests, headers, cookies, credentials, HTML and the full team response remain excluded.

The snapshot reports rank 168/270, division 9, 951 points from 1,012 games (248W–207D–557L), 1,005–1,420 goals, zero exceptions and 15 timeouts. Completed passes rank 247, shots 218, territory 261 and blocks 3. Entrant version 1 is not a controller hash. These cumulative statistics do not establish attribution of every event to MONSTER13.

MONSTER sets `SHELL=True` and `SHELL_RELEASE=False`. Its `act()` therefore bypasses normal multi-player attacking and reception logic in favor of four home coverers and one outlet. Being good at blocks is not sufficient to win. The earlier review also found the uploaded MONSTER weaker over a broad opponent panel: see [the original review](../monster-13/README.md).

## Independent structural tests

Two new development seeds, four opponents, both sides and both kickoff arrangements: 160 full native fixtures, 32 per controller. No tactical variants were combined.

| Controller | Matches | Points | W–D–L | Goals for–against | Exceptions | Raw deadline misses | Mean / max ms |
|---|---:|---:|---|---|---:|---:|---|
| baseline | 32 | 46 | 14–4–14 | 43–48 | 0 | 0 | 0.040 / 4.081 |
| open-play | 32 | 24 | 8–0–24 | 50–87 | 0 | 0 | 0.258 / 4.355 |
| three-cover | 32 | 26 | 8–2–22 | 53–103 | 0 | 0 | 0.085 / 9.043 |
| two-cover | 32 | 12 | 3–3–26 | 61–167 | 0 | 0 | 0.111 / 7.148 |
| adaptive | 32 | 78 | 25–3–4 | 37–19 | 0 | 0 | 0.079 / 8.944 |

`open-play` only disables MONSTER's shell. `three-cover` and `two-cover` independently release extra runners, retain MONSTER's original touch, shot, duel and movement physics, and allow only one attacking carrier to kick. All three lost points and were rejected. Removing the cover does not make the isolated attack engine as strong as team12.

## Broader development and frozen selection

Two further exposed development seeds, eight opponents, all four side/kickoff arrangements: 256 full fixtures, 64 per source.

| Controller | Matches | Points | W–D–L | Goals for–against | Exceptions | Raw deadline misses | Mean / max ms |
|---|---:|---:|---|---|---:|---:|---|
| baseline | 64 | 80 | 20–20–24 | 86–75 | 0 | 0 | 0.038 / 4.034 |
| adaptive | 64 | 99 | 29–12–23 | 60–69 | 0 | 0 | 0.107 / 9.120 |
| late-cover | 64 | 98 | 28–14–22 | 84–67 | 0 | 0 | 0.115 / 8.072 |
| nearpost | 64 | 118 | 35–13–16 | 136–58 | 0 | 1 | 0.171 / 27.591 |

`late-cover` embeds frozen team12 normal play and original MONSTER cover. It switches only while leading inside the final 20 seconds, defers active receptions, existing kicks and friendly control, and returns to attack if the lead disappears. It scored 98 versus 99 for team12 and was rejected. It retains one SDK subclass and stays below the 256 KiB limit. Two initial adapter prototypes failed public intake because of missing helper/state names; both failures and corrected sources are retained. They were fixed before any tournament. The corrected adapter passed intake but was still rejected on competitive results.

`nearpost` reuses an independently screened keeper package from the previous division 6 replay investigation. Its components were separately tested there before combination; they are not newly isolated causal tests in this study. It preserves team12 attacking code while removing the automatic five-player wall after falling two goals behind, guarding contested keeper clearances with contact-aware checks/braking, and positioning the keeper earlier at the near post. Historical component evidence remains in [the previous evidence archive](../monster-13/evidence.zip).

The selected development source scored 118 points versus 99 for team12 and 80 for MONSTER. Its name/version metadata was updated for the frozen candidate; every method AST is identical to the tested development parent. Source and selection are recorded in `finalist-manifest.json` and `qualification-plan.json`. This is a team12-based repair, not a claim that freeing MONSTER's runners solved its attack.

One development decision exceeded 20 ms: 27.590792 ms at tick 1777, seed 3260277102, against the Milla stress surrogate, side 0 with opposing kickoff. Two diagnostic native repeats did not reproduce the stall: 1.513178 ms unprofiled (thread CPU 1.515293 ms), 4.563952 ms with profiling. The original event remains counted. Its cause is unresolved; clean repeats do not prove an environmental cause. Diagnostic profiles never contribute qualification timing evidence.

## Untouched qualification

The candidate and both references were frozen before the first fixture. Sixteen untouched seeds 4127068101–4127068116; nine opponents; both sides and kickoff arrangements; **1,728 full fixtures, 576 per source**. The panel includes original MONSTER, provisional team12, v10, v9.1, v10-counter, v10-press, v10-compact, strong-replay, and the explicitly approximate Milla-stress surrogate. It does not contain the actual Milla controller. No qualification results were used to retune or select another challenger, and there was no optional extension or early stop.

| Controller | Matches | Points | W–D–L | Goals for–against | Exceptions | Raw deadline misses | Mean / max ms |
|---|---:|---:|---|---|---:|---:|---|
| baseline | 576 | 698 | 191–125–260 | 739–776 | 0 | 0 | 0.039 / 19.214 |
| adaptive | 576 | 1075 | 323–106–147 | 729–640 | 0 | 1 | 0.111 / 21.981 |
| challenger | 576 | 1075 | 315–130–131 | 1239–697 | 0 | 0 | 0.173 / 18.902 |

The repair scored 1,239 goals versus the reference's 729, but conceded 697 versus 640 and won 315 matches versus 323. The extra goals did not increase league points. Its qualification timing was clean, while the reference recorded one raw 21.980773 ms miss. The recovery file's own public intake had zero exceptions and zero deadline misses; the reference's benchmark miss remains part of its evidence.

The columns above are separate controllers against identical common fixtures. They are not complementary head-to-head totals. Confidence intervals below resample complete seed blocks (20,000 draws, fixed RNG). Fixtures with the same seed are not counted as independent samples.

| Paired comparison | Points difference per fixture | Seed-block 95% interval | Additional raw misses/1,000 fixtures |
|---|---:|---|---:|
| challenger − baseline | +0.6545 | [+0.4740, +0.8490] | +0.000 |
| challenger − adaptive | +0.0000 | [-0.1059, +0.1059] | -1.736 |

The frozen team12 reference versus MONSTER itself has a paired difference of **+0.6545 points/fixture**, 95% interval **[+0.5017, +0.8160]**. Retaining or returning to this reference is a choice of existing control, not selection of another experimental challenger using qualification data.

| Opponent | Challenger − MONSTER points/fixture | Challenger − team12 points/fixture |
|---|---:|---:|
| champion-current | +0.4688 | +1.0938 |
| milla-stress | +1.0469 | +0.3750 |
| monster-original | -0.6719 | -0.3750 |
| strong-replay | +0.2344 | -0.1719 |
| v10 | +0.6250 | -0.2656 |
| v10-compact | +1.5781 | -0.2344 |
| v10-counter | +0.9688 | -0.1719 |
| v10-press | +0.9688 | -0.1875 |
| v9.1 | +0.6719 | -0.0625 |

The registered gates require a positive paired 95% lower bound against **both** references, zero exceptions, no more than two additional raw misses/1,000 fixtures in both qualification and cumulative all current-study runs using the same decision code, no opponent-style decline greater than 0.25 points/fixture against either reference, successful official intake and the 256 KiB code limit.

- positive_points_lower_vs_both: **FAIL**
- zero_exceptions: **PASS**
- qualification_raw_miss_rate: **PASS**
- cumulative_raw_miss_rate: **PASS**
- style_gate: **FAIL**
- official_intake: **PASS**
- code_limit: **PASS**

Cumulative raw accounting includes development and qualification, including the original 27.59 ms event. See `results/final-audit.json` for every slow event on either side and the exact denominators. Failed adapter prototypes and instrumented diagnostic repeats are explicitly separate from frozen-policy tournament reliability.

## Reproduction and constraints

The restored submission was prepared as a behavior-identical copy of the existing control, not selected as another tactical challenger. Its method and tactical-constant ASTs match the reference exactly, and decision code does not read the changed name/version. In 16 additional native behavior-regression fixtures, it issued **38,400 identical team decisions / 192,000 identical player commands** on the same public observations, across both sides/kickoffs, two fresh seeds and two opponents. This is an equivalence check, not another strength or timing qualification; the reference's tournament numbers are not counted twice. Its own final file also passes official intake.

Every research fixture uses the official native engine 0.1.0, config 372990895c7eca2a, 2,400 ticks and unchanged 20 ms enforcement. Exactly one timed worker runs at a time. There are no simulator edits, hidden-state inputs, deadline changes, GC/affinity tricks or opponent changes. Default rosters match the previously supplied course replays. Optional custom formation hooks are exercised separately by official intake; default-roster tournament findings do not establish identical outcomes under all formation profiles.

The candidate is [experiments/monster-recovery/challenger/team.py](../../experiments/monster-recovery/challenger/team.py). It is experimental and has not replaced the active submission. The frozen provisional team12 source is [reference/team.py](../../experiments/monster-recovery/reference/team.py).

The evidence archive includes registrations, frozen sources, raw native rows, summaries, action/AST regressions, intake reports, timing diagnostics and the independent audit. Extract it and use a complete course repository/SDK:

```sh
PYTHONPATH=/path/to/student-sdk python research/reproduce.py \
  --repo /path/to/wits-robocup --evidence . \
  --cohort qualification --out /tmp/monster-recovery-reproduction
```

This reconstructs the registered panel by SHA256. Only local paths are relocated. All seeds, policies, official timing and fixtures stay fixed. Hardware scheduling can change wall times; raw misses from this study remain in the archive.
