# Public school ladder audit, 27 October 2026

The reported weakness is real in the first saved table, but the school exposes
a **mutable live ladder**, not separate public TITAN and MONSTER tournaments.
The same team entry and replay token changed scores during this investigation.
Historical comparisons need saved snapshots, submission hashes and matching
opponents; a current replay cannot be treated as the earlier recorded game.

## What the public data establishes

The user's entry is `401976-nkqubela-hokwana`, displayed as
`Nkqubela_Hokwana`. Both snapshots below come from the public
[team endpoint](https://lamp.ms.wits.ac.za/soccer/api/team?run=ladder&slug=401976-nkqubela-hokwana).
Raw responses and retrieval metadata are preserved alongside this report.

| Saved snapshot, UTC | Rank/division | Games | W/D/L | Points | Points/game | GF/GA | Errors/timeouts/forfeits |
|---|---|---:|---|---:|---:|---|---|
| 06:49:24 | 169 / 9 | 996 | 247/206/543 | 947 | 0.951 | 991/1398 | 0/15/0 |
| 10:27:16 | 123 / 7 | 900 | 287/341/272 | 1202 | 1.336 | 916/488 | 0/0/0 |

The later snapshot is provisional: it has fewer completed games and no
`last_updated` value. These are not controlled comparisons of known source
versions. Of 708 exact match IDs shared between the snapshots, 488 scores
changed. That common subset changed from 743 points and 810–949 goals to
1006 points and 829–375 goals. Another 288 old and 192 later match IDs do not
overlap. These IDs do not guarantee frozen opponent code or identical starts.

For example, the saved early Vareshan seed-1000 row was 0–6; the later row and
the replay retrieved at 10:25:59 were 0–0 under the **same replay token**.
The tactical seed-1000 row changed from 3–0 to 2–0. Both retrieved replays say
`faithful: true` against their later stored scores. This proves result
replacement between the snapshots; it does not identify which upload caused
the replacement.

The later team statistics show 2.097 shots/game (rank 253/270), 4.084 completed
passes/game (249/270), 4.49% control (206/270) and 23.78% attacking territory
(266/270). The shell blocks many shots, ranking third on that metric. Its
defensive strength coexists with a weak attack and many draws.

The [site metadata](https://lamp.ms.wits.ac.za/soccer/api/site) lists the live
`ladder` and an August demonstration run; it does not expose a historical
TITAN/MONSTER source comparison. Engine 0.1.0 and config
`372990895c7eca2a` match the local course environment. The saved
[table endpoint](https://lamp.ms.wits.ac.za/soccer/api/table?run=ladder) says four
fixtures per pairing, seeds 1000–1003 and alternating sides. This differs from
our deliberately broader four-starts-per-seed local protocol. Both enforce
20 ms decisions. Public UI help confirms three points per win, one per draw;
points assign divisions of twenty, and mean decision time orders teams within
a division. Fifteen isolated timeouts and no forfeits cannot explain the
earlier 543 defeats by automatic forfeit.

## What three public replays show

Downloaded only these three public replays, without student source files:

| Replay | Final score | Retrieval UTC |
|---|---|---|
| [Vareshan, seed 1000](https://lamp.ms.wits.ac.za/soccer/api/replay?name=ladder%2Fm-423861e57212793c) | 0–0 | 10:25:59 |
| [Tactical, seed 1000](https://lamp.ms.wits.ac.za/soccer/api/replay?name=ladder%2Fm-bb1100afdf402783) | 2–0 | 10:25:58 |
| [Akshat, seed 1000](https://lamp.ms.wits.ac.za/soccer/api/replay?name=ladder%2Fm-615cecd41e9cf441) | 0–4 | 10:28:23 |

All 27,360 measured defender movements after tick 120 match the local v51
MONSTER guard formula with post limit 7.3 within 0.001. The largest vector
error is below 0.00004. A 9.5 post-limit formula disagrees on 1,591 decisions.
This identifies the observed **defensive behavior**, not an exact source hash
or the full uploaded controller. Public entrant metadata carries version `1`
and no source hash.

All three replays start from the SDK's default 1-2-2 formation, rather than
MONSTER's custom four-guard kickoff. Their guards then recover to
x=-48.8 and y=5.4,-1.8,1.8,-5.4; when leading they move to x=-46.7.
This is a material replay-path difference from local custom-formation tests.
It is not sufficient evidence that every historical scored fixture used that
start. Testing both default and custom formations is warranted.

The Akshat defeat exposes failures after the wall has already settled:

- Goals occur on ticks 657, 979, 1797 and 2242. The outlet is parked around
  (-20,-21) at every goal, leaving nearby attackers unpressed. Four guards
  remain near the goal for 77.9% of the 1,743 trailing frames.
- Two finishes pass the lower interval around y=-3.4 to -3.6 between fixed
  guards at -1.8 and -5.4. Their 3.6-unit spacing exceeds the 2.9-unit diameter
  covered by player-plus-ball contact radius, leaving a geometric corridor.
- Repeated full-power diagonal clearances do not ensure an outward ball.
  At tick 978 a defender kicks toward (+0.871,-0.491), but measured ball vx
  remains -13.37 after the tick; the goal follows at 979. At 1796 another
  clearance leaves vx=-17.16 before the goal at 1797. At 2239 a positive-x
  clearance changes measured vx from -1.47 to -14.25 after contacts, before
  another attacker finishes. A velocity-only impulse calculation is not
  sufficient: player-body collisions and contested kicks also matter.

These observations support three concrete experiment priorities: pressure on
close attackers, emergency clearance evaluation including body contacts, and
shot-aware guard positioning rather than permanent lanes. Default-start
formation recovery is another robustness target, but it did not directly
cause these four late goals. More draws will not produce league dominance.

`../opponents/gap_press/team.py` is an original synthetic stress opponent
motivated by these geometries: two advanced attackers, observed guard-gap
midpoints, close diagonal finishing and cooldown-aware lane ranking. It
contains no student identity checks or imported student code. It is a test
opponent, not a claim to reproduce Akshat's private implementation.

## Reproduction and evidence

Every downloaded artifact has a `.meta.json` sidecar with public URL, retrieval
time, response hash and size. `school-audit.json` contains replay measurements,
goal contexts and snapshot comparisons. `replay-audit.json` is the earlier
replay-only measurement. The pure-JSON diagnostic executes no controller or
match:

```powershell
python experiments/league/audit_school.py experiments/league/school/replay-vareshan-1000.json experiments/league/school/replay-tactical-1000.json experiments/league/school/replay-akshat-1000.json --output NEW-OUTPUT.json
```

`fetch_school.py` performs ordinary unauthenticated HTTPS GETs to the public
school host and refuses evidence overwrites. No access controls were bypassed,
no private student sources were fetched, and no engine or SDK file was edited.
