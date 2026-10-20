# Deadline and reporting audit

Adaptive and Original Architect policy sources are unchanged. This audit does
not reverse Adaptive's rejection or waive any native deadline miss.

## Reporting bug

The Adaptive report's per-opponent loop assigned `b` to the final style's v10
subtotal. Its later interpretation paragraph reused `b` as if it still contained
all v10 matches. The tables, machine-readable summaries, paired statistics and
gates used the correct data. The paragraph incorrectly said +152 points,
+2,758 passes and negative reductions in concessions and turnovers.

The fix names style-local variables explicitly. Full regeneration against the
immutable native archive now reports **+6 points, +110 completed passes, 13
fewer concessions and 24 fewer turnovers versus v10**. A regression regenerates
the entire report from archived matches and checks both the prose and unchanged
native summaries, comparisons, gates and decision. The original archive and its
hash remain unchanged; its embedded historical report is superseded only by
this documented correction.

## Historical deadline evidence

| Opponent | Seed | Candidate slot | Kickoff | Original tick | SDK wall ms | Thread CPU ms | GC overlap |
|---|---:|---:|---|---:|---:|---:|---|
| v10-counter | 1010963236 | 0 | opponent | 391 | 22.302004 | 22.306189 | none |
| v10-press | 1866751028 | 1 | opponent | 290 | 31.414155 | 31.416737 | none |

Each original match recorded one Adaptive-side timeout and no opposing timeout.
The first exact repeat of each fixture also had one Adaptive timeout, with
maximum SDK times 145.500305 ms and 54.380663 ms respectively. The previous
runner did not trace individual decisions during repeats. Thus the evidence
establishes **fixture-level miss recurrence**, not a confirmed recurrence at
the same tick, state or code path. The old conservative gate remains failed.
Wall time closely matching thread CPU in the original two misses does not
support simply declaring them scheduler preemption or GC pauses.

## Fresh forensic checks

Three serial full-native repeats of each case ran for each unchanged source:
v10, Original Architect and Adaptive (18 timed full matches). No candidate-side
miss occurred. Two additional full capture matches reached the original target
ticks with no timeout on either side; capture runs are diagnostic, not timing
gate evidence. Every match retained the 2,400-tick duration and native 20 ms
deadline. Per-decision wall/thread CPU, GC overlap and both teams' slow calls
are recorded.

At the original target ticks, the capture calls took 0.171026 ms and 0.125636
ms. Twenty cloned pre-decision-state diagnostic calls per case had median wall
times 0.158728 ms and 0.126189 ms; maxima were 0.258593 ms and 3.272263 ms.
Offline profiles contained 1,151 and 850 calls, dominated by the existing
interception/ETA work rather than a reproduced expensive Adaptive search.
Cloned-state profiling is not a replacement for native match timing. The old
input snapshots were not retained, so exact state identity cannot be established
from archival hashes alone, even though the no-timeout deterministic prefixes
reach the same public ticks.

**Conclusion:** no stable algorithmic hotspot was reproduced in these checks.
The root cause of the old CPU-charged outliers remains unproven. All old misses
remain counted. The new evaluation instruments raw matches and every exact
repeat identically, so future recurrence can be compared by tick and input
fingerprint instead of inferring a repeated code failure from fixture totals.
