# Adaptive Passing Lane Architect

Selective development of Tactic 05 from commit `906f7b9`. Frozen TITAN v10.0
and the original Architect are immutable controls. Main and the active champion
remain unchanged; no result authorizes promotion without explicit approval.

- [Detailed performance report](results.md)
- [Results, comparisons and gates](results.json)
- [Preregistered rules and excluded-seed audit](registration.json)
- [Frozen three-way native protocol](development-protocol.json)
- [Evidence archive index](evidence.json)
- [Experimental controller](../../experiments/titan-adaptive-architect/team.py)
- [Source fragment](../../tools/adaptive_architect/tactics.pyfrag)

The policy detects two closing defenders near the carrier, an imminent
interception race and restricted baseline passing space. A stationary compact
block or low pressure keeps the v10 shape. Under meaningful pressure, unchanged
physics must verify an alternative route and its executable receiver command;
its score must exceed the baseline route by more than 0.35, or make a route
feasible where the baseline has none. This bounded heuristic is not proof of a
completed pass or future score improvement.

The carrier, goalkeeper, both cover assignments, chaser and current recipient
are protected. Original transitions, counterpress, passing, shooting and
reception ownership retain priority. Counterattack Firewall and all four older
special tactics are disabled. All original v10 methods except the two hook call
sites in `act` are AST-identical. No engine, SDK, physics, configuration or
deadline changes are made.

Telemetry distinguishes pressure/rejection diagnostics from matching final
movement commands. The external native harness reads cumulative engine pass
completion counters after each step, verifies every increment against the final
record and retains completion traces. Completions after a recent supported
receiver's accepted pass plan are associations, not causal attribution.
Controller code does not read native counters, files, clocks or external tools.

`build.py` reproduces the source and checks both frozen control hashes.
`register.py` allocates fresh development and reserved qualification seeds.
`run_adaptive_architect.py` runs one native worker with the unchanged 20 ms
deadline; `analyze.py` applies the sealed two-baseline gates.
`package_evidence.py` verifies and archives raw records, repeats, sources,
opponents, diagnostic probes, completion traces and test logs.

Sixteen development seed blocks include three strong frozen v10 variants and
both sides and kickoffs. Qualification requires statistically supported gains
over both baselines, no compact regression, preservation of v10 metrics and all
original runtime/safety gates. A failed development experiment receives no fresh
qualification, integration or promotion.

## Reporting correction

The live performance report now fixes a narrative subtotal-shadowing error.
The original native tables, statistics, gates and immutable evidence archive
are unchanged. Its embedded historical report is superseded by the live
correction; see [the audit](../original-architect/deadline-and-reporting-audit.md).
