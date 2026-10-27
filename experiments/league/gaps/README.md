# Observed gap and corner research candidates

`team.py` changes only MONSTER's proposed wall-shot aim points. It projects
observed defender bodies onto the opponent goal plane, merges their covered
intervals, and tries at most five additional gap centres before the nine fixed
aims. The existing launch, interception, contact and shot safety checks still
validate every aim. The 7 ms optional-search budget is unchanged.

`../gaps2/team.py` adds a separate corner-duel change on top. Within six units
of the opponent goal and near or outside a post, it considers inward goal
directions as well as forward directions. Eighteen-tick rollouts under three
opponent kick assumptions and both kick orderings score actual goals,
goal-mouth approach and visible body blocks. Its expected-value objective has
a worst-case term; it deliberately tolerates a clearance risk in the opponent
corner, so competitive validation is necessary.

Run `python experiments/league/gaps/build.py` to reproduce both standalone
files from the unchanged archived MONSTER source. Assembly is offline. Neither
controller reads files or opponent identity at runtime. Neither candidate is
a validated release until common league measurements support selection.
