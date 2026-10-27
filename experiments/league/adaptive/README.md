# Observation-driven portfolio experiment

`team.py` combines the archived legal TITAN and MONSTER policies in one
standalone submission. Its default is TITAN's open build-up, passing, keeper,
pressing and lead protection. It switches to MONSTER's four-cover counter
policy after twelve consecutive observations of four opponents covering their
goal mouth, or at a restart after falling behind. That choice uses positions
and scores only. The switch remains active for the rest of that match.

Only the selected policy computes actions on each tick. The ordinary helper
policy classes do not inherit `TeamController`; `LeagueAdaptive` is the sole
submission entry point. `build.py` is offline assembly tooling and is not
required at runtime. Existing TITAN and MONSTER sources remain unchanged.

One diagnostic match using the official engine, seed 810000, candidate side 0
and candidate kickoff, versus archived MONSTER completed 2,400 ticks at 0-0
with no invalid actions, errors or timeouts. This single match does not establish
improvement. The common league benchmark determines whether this candidate
should be selected.
