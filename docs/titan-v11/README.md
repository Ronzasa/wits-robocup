# TITAN v11 tactical development

Independent experiments on frozen Guardiola/Klopp TITAN v10.0. No main or
active-champion changes are authorized by this work.

- [Performance report](results.md)
- [Machine-readable results and gates](results.json)
- [Frozen preregistration](registration.json)
- [Native development protocol](development-protocol.json)
- [Evidence archive index](evidence.json)

| Candidate | Flag | Source |
|---|---|---|
| All off | neither | [team.py](../../experiments/titan-v11-off/team.py) |
| Tactic 05: Passing Lane Architect | `PASSING_LANE_ARCHITECT` | [team.py](../../experiments/titan-v11-architect/team.py) |
| Tactic 06: Counterattack Firewall | `COUNTERATTACK_FIREWALL` | [team.py](../../experiments/titan-v11-firewall/team.py) |

The source of truth is frozen v10 plus
[`tools/titan_v11/tactics.pyfrag`](../../tools/titan_v11/tactics.pyfrag).
[`build.py`](../../tools/titan_v11/build.py) verifies the champion hash before
assembling self-contained controller files. It inserts one target-planning hook
after existing reception and defensive safeguards and one final-command
telemetry hook. All other original methods remain AST-identical.

Architect supplies movement only to unprotected supporters after existing
physics verifies a reachable prospective pass. It leaves actual pass and shot
selection to v10. Firewall screens a projected outlet-to-goal corridor with the
existing cover defender while a friendly controlling player confirms possession.
Every loss of possession releases immediately to v10 defense. Neither tactic
has a sticky movement plan that can override reception, carrier or goalkeeper
actions. The pre-existing four TITAN-X tactics are absent from these candidates.

`register.py` seals sources and unused seed cohorts once. `run_titan_v11.py`
uses the original native full-match timing harness with final-command telemetry.
`analyze.py` applies the frozen significance, intention and reliability gates;
`package_evidence.py` preserves raw records with a verified SHA-256 manifest.
No combined candidate, qualification or promotion is justified merely by an
activation, a unit-test pass or a positive aggregate points estimate.

An initial trial was interrupted on a possession-eligibility review finding
before outcome analysis. The final source additionally requires a friendly
controlling player, preserving the old cover safeguard when team-control
metadata is stale. Both initial protocols, frozen initial sources and partial
native records are retained; every initially allocated seed was excluded from
the final registration. The interruption is documented in the report.
