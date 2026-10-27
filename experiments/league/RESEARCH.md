# League research, October 27

The school evidence is in [school/REPORT.md](school/REPORT.md). It demonstrates
both a mutable live ladder and genuine tactical failures against close attacks.
The old claim that beating TITAN made MONSTER universally better was unsupported.

## Initial matched screens

The custom-formation screen uses three seeds, both sides and both kickoff
owners: 144 full matches per policy across twelve equally weighted opponents.
It is research data used for selection, not independent release evidence.

| Policy | Points | W/D/L | Goals | Finding |
|---|---:|---|---|---|
| Archived TITAN | 323 | 103/14/27 | 211-101 | Strong easy-opponent results; weaker against the related defensive pool. |
| Archived MONSTER | 364 | 112/28/4 | 412-18 | Strong defense, but many draws against protected goals. |
| Two-attacker transition | 298 | 92/22/30 | 416-133 | Rejected: more goals did not compensate for lost cover. |
| Corrected observation portfolio v2 | 348 | 105/33/6 | 176-53 | Switching after an adverse goal abandoned useful open play. |
| Observed shooting gaps | 374 | 118/20/6 | 427-23 | More points against goal-mouth blocks. |
| Gaps plus inward corner duels | 379 | 119/22/3 | 437-22 | Best initial screen; preserves four guards. |
| Outlet pressure cover | 367 | 113/28/3 | 425-24 | Helps some pressing matches; costs points in others. |
| Pressure plus body-aware clearances | 368 | 113/29/2 | 402-11 | Fewer conceded goals, but extra draws limit points. |

The initial portfolio v1 raised when assigning viewer text to optional
debug=None. Its 1,900 errors/95 forfeits disqualify it. Raw on-field scores at
forfeit misleadingly appeared to be wins; the accounting regression tests now
explicitly adjudicate forfeits as 0-3 without changing preserved evidence.
The corrected v2 had zero exceptions in its full screen and still lost on points.

A separate default-formation screen crossed two fresh training seeds and the
same twelve opponents (96 matches each). TITAN earned 237 points, MONSTER 246,
the corner candidate 240, and predictive-post Sentinel 228. These results are
why the release must be evaluated from both starting formations. Adding a
predictive mechanism is not itself evidence of improvement.

## School-inspired diagnostics

The first independently written close-pressure opponent was too weak to
reproduce the school defeats: MONSTER won all twelve default-start games,
64-3 goals. It remains auxiliary evidence and is not labeled a hard opponent.
A second opponent keeps three goal guards and two coordinated attackers.
Its twelve-game default-start screen produced:

| Candidate | Points | W/D/L | Goals |
|---|---:|---|---|
| MONSTER | 32 | 10/2/0 | 24-3 |
| Corner candidate | 36 | 12/0/0 | 25-2 |
| Guardian | 25 | 7/4/1 | 14-4 |
| Ray cover | 34 | 11/1/0 | 24-0 |
| Wall-only portfolio v3 | 31 | 10/1/1 | 19-10 |

Ray cover projects the observed goal mouth onto the defensive line, reducing
avoidable gaps without removing defenders. Portfolio v3 preserves TITAN open
play and switches only after sustained observed four-player walls; it removes
the adverse-score trigger and uses the corner policy for the counterattack.
Neither has yet qualified as a superior release through these diagnostics.

## Final selection

Five new candidates enter a fresh selection set alongside frozen MONSTER.
The thirteenth primary opponent is the second pressure opponent. Selection
uses 820000..820002 with custom formations and 820002..820004 with default
formations. Rank new candidates by points, then goal difference, then mean
decision time; exceptions, forfeits and invalid actions disqualify a candidate.
The selected source and standalone release hash are locked before final play.

Final evaluation then compares only that locked release, TITAN and MONSTER
over ten untouched seed clusters, half with each starting formation. Results
retain all timeouts and failures. The local sample cannot establish dominance
over the unknown class controllers; school points need subsequent real results.

Raw fixtures, content-addressed sources and the research protocol are retained
under results/, sources/ and [PROTOCOL.md](PROTOCOL.md). The SDK, native engine,
course config, archived MONSTER and validated TITAN remain unchanged.
