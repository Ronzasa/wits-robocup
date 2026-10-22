# Soccer agent platform — student edition

Active champion: **[team.py — Elite Replay Cutback](my-team/team.py)** on the
`main` branch, selected by the project owner after the replay-led evaluation.
[Read the activation record](docs/elite-cutback-promotion.md) and
[the full paired results](https://github.com/Ronzasa/wits-robocup/blob/b4c24958757b1c2e93b8857b7166367f94051223/docs/elite-scout/validation.md).
The exact previous [v10.0 champion](champions/v10.0/team.py) is preserved.
Upload only `team.py` through the course submission system; a GitHub push does
not update the league entry.

[TITAN-10B](experiments/titan-10b/team.py) checks executable receiver movements
and the actual command after role selection. On 720 paired fresh local fixtures
it earned **1917 versus v9.1's 1847 points**. Raw deadline misses rose from 22
to 33, failing the registered timing gate; v9.1 was retained at that stage.
[Read all metrics and limitations](docs/titan-10b-validation.md).
The unchanged [v9.1 champion](champions/v9.1/team.py) is preserved.

[TITAN-10B-R](experiments/titan-10b-r/team.py) was the **v10.0** champion.
It preserves TITAN-10B decisions while reducing runtime
and earned **1922 versus v9.1's 1864 points** across 720 fresh paired fixtures.
It passed every original promotion gate. Its exact tested build is now archived at
[`champions/v10.0/team.py`](champions/v10.0/team.py); the unchanged
[v9.1 champion](champions/v9.1/team.py) is preserved.
[Read the full runtime and promotion evidence](docs/titan-10b-r-validation.md).

The [strict interception build](experiments/strict-interceptions/team.py) requires
physically verified pass receptions and rebound collection. On 560 paired fresh
local fixtures it earned **1507 versus v9.0's 1440 points** and passed the
promotion gate. [Read the results](docs/v9.1-interceptions-validation.md).
The unchanged [v9.0 champion](champions/v9.0/team.py) is preserved.

Version 9.0 corrected early defender-contact prediction and compared threatened shots
with verified alternatives. On 672 paired fresh fixtures, it earned
**1699 versus v7's 1535 points**, with **542 versus 477 wins**.
[Read the full comparison](docs/v9.0-validation.md).

The complete requested **[v8.0 tactical experiment](experiments/v8-full/team.py)**
adds striker marking, five-player goal defence at a two-goal lead, rebound
counters, third-man short passing, Pelé finishing, long shots and wall collection.
It earned **1,464 versus v7's 1,555 points** on 672 paired fresh fixtures and
conceded **566 versus 476 goals**. It remains experimental;
[read the results and limitations](docs/v8.0-validation.md) before uploading it.

Write a soccer team in Python, play it against reference opponents on your own
machine, and watch the match in your browser.

Nothing to install and nothing to build. You need **Python 3.8 or newer** and
nothing else — the simulation engine is already compiled and included for
Windows, macOS and Linux.

---

## Start here

**Windows** — double-click `START.cmd`.

**macOS and Linux** — open a terminal in this folder and run:

```bash
bash start.sh
```

After the first run `./start.sh` works too. (Some unzip tools drop the
executable bit; the first run puts it back.)

Your browser opens the dashboard. Pick two teams, press a button, watch the
match. That is the whole loop.

If something looks wrong, run `START.cmd doctor` (or `./start.sh doctor`) and
it will tell you what it found.

---

## Writing your team

Your team is [`my-team/team.py`](my-team/team.py). One file, and that file *is*
your submission — what you debug here is exactly what you hand in.

```text
my-team/
  team.py      all of your code, in this one file
```

Open it and edit it. It is already a working team, so you can change one thing
and immediately see whether it helped.

**All of your code goes in `team.py`.** A second `.py` file next to it will not
be importable when the server loads your team, so it is rejected rather than
quietly ignored. Check at any time with:

```bash
START.cmd check        # Windows
./start.sh check       # macOS and Linux
```

which runs the marker's own checks: the folder's structure, and then your team
actually playing a match.

When you are done, **upload `my-team/team.py` to Moodle**. That is the whole
hand-in: no zip, no folder, nothing to fill in — Moodle already knows who you
are, and that is where your name on the leaderboard comes from.

You implement one method:

```python
from soccer import TeamAction, TeamController, closest_to_ball

class MyTeam(TeamController):
    def act(self, obs):      # called every tick, ball or no ball
        if closest_to_ball(obs):
            ...              # it is there to be won
        ...
```

`act` runs on every tick of the match, whether the ball is yours or theirs.
Working out which of those it is — and what your team should be doing about it
— is the assignment. What you never decide is which end you are playing: both
sides are given the same view of the pitch, with your goal on the left and
theirs on the right.

There is one optional third method, `initial_formation`, which chooses where
your team lines up at every kickoff.

The full API — every field on `obs`, every helper, every action — is in
[`docs/student-guide.md`](docs/student-guide.md).

Two more examples to read are in [`examples/`](examples/): `simple_team.py` is
the same team as `my_team.py`, and `annotated_team.py` explains itself line by
line.

---

## Running matches from the command line

The dashboard is easier, but the command line gives you numbers and repeats.

Every command below is written `./start.sh …`, which is the macOS and Linux
form. **On Windows write `START.cmd …` instead** — the arguments after it are
identical on all three platforms, and so are the results. Name your team by its
**folder**:

```bash
./start.sh play my-team --against balanced          # one match, with statistics
./start.sh check                                    # is my submission complete?
./start.sh validate my-team                         # does it play legally?
./start.sh tournament my-team --against balanced --seeds 1000..1020
./start.sh baselines                                # the opponents you can play
```

`check` is the one to run before you hand anything in. It applies the same
checks the marking pipeline does — that your team is one file called `team.py`,
and whether it loads and plays inside the deadline — so a submission that passes
here is one the marker will accept.

One match is close to a coin toss between evenly matched teams. `tournament`
plays a whole set of seeds and reports the spread, which is the number worth
paying attention to.

### Playing against a team of your own

You are not limited to the reference opponents. Make a second team and play
the two against each other:

```bash
./start.sh new their-team                           # a fresh, valid submission
./start.sh play my-team --against their-team
```

Both folders appear in the dashboard too, so you can watch the match.

---

## Watching your team play

Matches are deterministic: the same team, opponent and seed always produce
exactly the same match. That is what makes debugging possible.

Your teams are listed first in both dropdowns, under **Your teams** — pick one,
pick an opponent, and choose **Record and watch**. It plays the match, saves it
to `replays/`, and opens it in the browser viewer, where you can pause, step a
tick at a time, scrub backwards and click a player to see what it was doing.

Live view runs baseline against baseline only. To watch your own team, record
it and open the recording — same match, same result, and you can step through
it, which live view cannot do.

---

## What is not in this download

This is the local practice environment. It deliberately leaves out the league
infrastructure, the results website and the marking pipeline, which run on the
course server.

Your team file is the whole submission, so nothing here is missing from what
you hand in.

---

## Troubleshooting

**"Python 3.8 or newer was not found"** — install it from
<https://www.python.org/downloads/>. On Windows, tick *Add python.exe to PATH*
in the installer.

**"No engine bundled for this machine"** — the download does not contain a
build for your platform. Say which platform you are on when you ask.

**"Permission denied" running ./start.sh** — the unzip tool dropped the
executable bit. Run `bash start.sh` instead; it puts the bit back, and
`./start.sh` works from then on.

**macOS says the engine "cannot be opened"** — macOS quarantines anything
downloaded through a browser, and the engine is not notarised by Apple.
`start.sh` clears that tag for this folder every time it runs, so start with
`bash start.sh` rather than calling `python3 launch.py` yourself. To clear it
by hand, from a terminal inside this folder:

```bash
xattr -dr com.apple.quarantine .
```

**A change to your team made no difference** — check you saved the file, and
that you are running `my-team` and not an example.

**"missing team.py"** — a team is a folder with a `team.py` in it, and that is
the name the marker loads. Run `./start.sh new <name>` to get a valid one.

**Anything else** — run `./start.sh doctor` and include its output when you ask.
