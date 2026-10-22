# Ten-game scouting review: Gabriel Behane vs Zamokuhle Maziya

These recordings show the two opponents playing one another. Nkqubela Hokwana's
controller is not playing in them. The observations below describe visible
behavior; the experiments test whether selected ideas help our own controller.
They do not reconstruct either opponent's source code.

Gabriel won six, drew three and lost one, scoring 13 and conceding six in the
ten recorded results. This describes this supplied set, not their league-wide
win rates or which player currently occupies first place.

## Results and coverage

The viewer is playing at about four times simulation speed. A second of video
usually contains four seconds of game time. Video timestamps below are the
primary references. Match times are approximate, reconstructed from the visible
tick counter and checked against its 80-ticks-per-recording-second progression.
One clock OCR outlier in game 10 was removed before the fit.

| File | Blue team | Final blue–red | Gabriel's result | Coverage starts around |
|---|---|---:|---|---:|
| game1.mp4 | Gabriel | 1–2 | Loss | 0:18 |
| game2.mp4 | Zamokuhle | 1–3 | Win | 0:18 |
| game3.mp4 | Gabriel | 2–0 | Win | 0:17 |
| game4.mp4 | Zamokuhle | 0–1 | Win | 0:16 |
| game5.mp4 | Gabriel | 1–0 | Win | 0:18 |
| game6.mp4 | Zamokuhle | 1–1 | Draw | 0:18 |
| game7.mp4 | Gabriel | 1–1 | Draw | 0:21 |
| game8.mp4 | Zamokuhle | 0–1 | Win | 0:12 |
| game9.mp4 | Gabriel | 1–0 | Win | 0:00 |
| game10.mp4 | Zamokuhle | 1–1 | Draw | 0:06 |

All final scoreboards reach tick 2400. Most recordings omit the opening seconds.
Gabriel's goals in games 5 and 6 already appear on the first captured scoreboard;
their buildups cannot be assessed. The other 17 goals have annotated sequences.
Game 4 cuts off part of the lower pitch. Game 10 includes a long paused ending;
paused frames were excluded from position summaries. The footage is 30 fps and
compresses multiple native ticks into each frame, so individual kicks, collisions
and five-tick cooldowns cannot always be distinguished.

## What is worth copying

### 1. Goalkeeper depth changes the area defended

Gabriel's deepest player, visually checked as the keeper in representative
frames, often stands roughly 10–14 pitch units from his goal line. Zamokuhle's
keeper usually stands around two units from it. The contrast appears with either
team color and across all ten recordings. The estimated per-game median depths
are:

| Game | Gabriel | Zamokuhle |
|---|---:|---:|
| 1 | 13.4 | 2.0 |
| 2 | 11.3 | 2.0 |
| 3 | 13.4 | 1.6 |
| 4 | 12.3 | 2.0 |
| 5 | 10.7 | 1.6 |
| 6 | 11.6 | 2.0 |
| 7 | 11.0 | 1.6 |
| 8 | 11.6 | 2.0 |
| 9 | 9.5 | 1.6 |
| 10 | 10.6 | 2.0 |

This is a positioning hypothesis, not evidence that advancing the keeper caused
Gabriel's better result. It can reduce the width of the immediate shooting angle
and put the keeper closer to a loose ball. It also exposes space behind it.
Zamokuhle's first goal in game 7 shows the danger: Gabriel's keeper joins the
upper-left contest, and the next attack arrives through a lower receiving lane.

**Experiment:** caps of 6, 10 and 14 units, with depth decreasing as the ball
approaches our goal. For a fast goal-bound ball, compare executable saving paths
with the ordinary home line, using current velocity and cooldown. Retain an
available ordinary save if the advanced target cannot save. The existing sweep,
kick selection and keeper-priority code remain in charge.

### 2. A useful outlet is available before the recovery

Game 7, video **20.3–21.8**, is especially useful. Gabriel releases the ball out
of a defensive-side contest into the open lower channel. Blue 2 is already well
ahead of that contest, runs onto the ball and finishes. The ball crosses much of
midfield before the recipient's final touch. This is a concrete counterexample
to expecting every attack to consist of several short passes.

Games 3 and 9 also show diagonal progression toward a wide player who can face
goal. The width stretches the marking assignments and changes the next shooting
angle. Current v10/TITAN-X support normally follows the ball or marks opponents
when defending; it can leave no advanced outlet when possession changes.

**Experiment:** allow one spare outfielder to stay ahead in a wide channel during
selected midfield/defensive transitions. Preserve goalkeeper, ball chaser, cover
and the other marking/supporting outfielder. Cancel it on a fast goalward ball,
deep pressure or multiple immediate central runners. A verified reception is
never reassigned. Passes still have to pass the existing execution-aware race.

The videos show the movements defenders actually made. Our pass verifier asks
whether a defender could intercept under a legal movement. A long ball that
succeeded in a recording can therefore still be rejected by our verifier; the
scouting footage does not justify replacing physical checks with optimistic ETAs.

### 3. Wall pressure needs a player inside the field

In game 2, video **5.9–7.5**, the upper-left corner contest is followed by a ball
back into the field and a central/lower receiver finishing. In game 4,
**15.9–17.5**, Gabriel works the same general corner-to-inside pattern. Game 8,
**2.6–4.2**, provides another example of pressure near the upper-left wall followed
by an inside player collecting and finishing.

The footage supports wall-assisted buildups and second-ball collection. It does
not reveal whether every rebound was a deliberately selected bank pass, a shot
against the wall, a clearance or a body deflection. Calling every rebound a
planned wall combination would overstate the evidence.

Current support pushes most free players forward of the ball and keeps cover
near its lateral coordinate. Near an attacking corner, that can flatten support
along the goal line. The existing `_endwall_link` already searches wall cutbacks;
adding another elaborate wall search would duplicate part of that capability.

**Experiment:** position one spare supporter centrally and a few units behind a
secure wide attack. It creates a cutback angle and a location from which to
collect rebounds. Preserve the chaser, designated cover, existing receiver and
the second free attacker. All passes, wall physics and first-touch verification
remain unchanged.

### 4. The final angle often matters more than possession volume

Game 3's first goal progresses through midfield into the lower/right channel
before the final finish. Game 6's equalizer changes receiving sides near the box.
Game 9 progresses along the lower channel before releasing to the upper/right
attacker. These are useful examples of moving the ball into a fresh finishing
angle. They are not evidence that maximal short-pass volume is the objective.

The present experiments change the positions that create those options. Shooting
and pass safety remain unchanged, so their results can reveal whether the
spacing itself helps. No player-speed, kick-power or competition-rule changes
are involved.

## Every visible goal

Sequences show the last approximately 6.4 game seconds before the scoreboard
changes. Some attacks begin earlier. Each link contains twelve frames, ordered
left to right and top to bottom. The notes describe observable sequences without
claiming exact commands or intent.

| Game / scorer | Video goal time | Visible sequence | Evidence |
|---|---:|---|---|
| 1 / Gabriel | 0:07.77 | Lower-right attack, boundary/rebound activity, inside collection and finish | [frames](frames/g1-goal1.jpg) |
| 1 / Zamokuhle | 0:15.10 | Upper-left progression, then a lower/inside receiving lane for the finish | [frames](frames/g1-goal2.jpg) |
| 1 / Zamokuhle | 0:23.30 | Left-channel runner carries the attack beyond the nearest marker | [frames](frames/g1-goal3.jpg) |
| 2 / Gabriel | 0:07.53 | Upper-left boundary contest, ball returns inside, central/lower finish | [frames](frames/g2-goal1.jpg) |
| 2 / Zamokuhle | 0:10.37 | Midfield release to lower wing, return inside and new finishing angle | [frames](frames/g2-goal2.jpg) |
| 2 / Gabriel | 0:16.77 | Lower-left wall/corner phase, inside collection and close finish | [frames](frames/g2-goal3.jpg) |
| 2 / Gabriel | 0:20.93 | Upper-left contest, inside continuation and central shot | [frames](frames/g2-goal4.jpg) |
| 3 / Gabriel | 0:08.73 | Central progression, release to lower-right runner, finish | [frames](frames/g3-goal1.jpg) |
| 3 / Gabriel | 0:18.07 | Long forward diagonal into right channel, receiver reaches shooting position | [frames](frames/g3-goal2.jpg) |
| 4 / Gabriel | 0:17.47 | Upper-left boundary pressure, ball moves inside to a lower receiver | [frames](frames/g4-goal1.jpg) |
| 6 / Zamokuhle | 0:08.70 | Upper/right and lower/right receivers exchange the attacking angle | [frames](frames/g6-goal1.jpg) |
| 7 / Zamokuhle | 0:03.53 | Upper-left keeper/attacker contest, subsequent attack through lower lane | [frames](frames/g7-goal1.jpg) |
| 7 / Gabriel | 0:21.80 | Long defensive release; lower-channel outlet runs onto it and finishes | [frames](frames/g7-goal2.jpg) |
| 8 / Gabriel | 0:04.20 | Upper-left boundary pressure, inside recovery and finish | [frames](frames/g8-goal1.jpg) |
| 9 / Gabriel | 0:10.30 | Lower-channel progression, diagonal release to upper/right attacker | [frames](frames/g9-goal1.jpg) |
| 10 / Zamokuhle | 0:08.33 | Right-side boundary phase, ball recycled toward central receiving options | [frames](frames/g10-goal1.jpg) |
| 10 / Gabriel | 0:15.83 | Central-to-left progression, change into lower receiving lane, finish | [frames](frames/g10-goal2.jpg) |

The game 5 goal and Gabriel's earlier goal in game 6 have no visible buildup.
There is no attribution for them beyond the captured scoreboards.

## Measurement and validation

All 8,939 video frames were processed for candidate player/ball detections.
Goalkeeper-depth summaries sample every third frame, discard terminal pauses,
and use only samples with five detected team players. Depth is estimated from
the deepest detected player, with representative frames visually checked.
It is a goalkeeper proxy, not reliable per-player identity tracking. Cropping,
overlaps, compression and detection omissions limit its accuracy. No pass
completion, possession percentage or kick-power statistic is inferred from
these screen recordings.

Input hashes, clock fits, per-game depth samples and the complete goal timeline
are stored beside this report. The analysis archive retains scripts, score-only
glyph templates and all detection candidates. Original videos and unrelated
browser/sidebar imagery are not published. The original files are required to
reproduce image extraction; install OpenCV, NumPy, SciPy, Pillow and Tesseract
in an offline development environment. None are dependencies of `team.py`.

The performance experiments are preregistered in [registration.json](registration.json).
Their native results and final recommendation belong in the validation report.
An observed tactic is accepted only after it helps the controller in matched
native fixtures. A proxy opponent tests an observed idea; it is not the actual
Gabriel or Zamokuhle controller.
