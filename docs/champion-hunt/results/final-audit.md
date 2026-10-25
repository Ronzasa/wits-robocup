# Final evidence audit

Read-only recomputation from native JSONL records, registered source hashes and official intake output. No simulation or candidate modification was performed in this audit.

- Adaptive direct: **79 W / 46 D / 3 L**, **283–55 points**, **203–121 goals** across 128 complete balanced fixtures / 32 fresh seeds. Zero candidate and opposing exceptions or deadline misses; zero candidate fouls. Mean **0.115240 ms**, max **8.682870 ms**. There are **13 rejected kick requests**. Specialist activated in **65/128**.
- Paired field: adaptive **91 W / 30 D / 39 L**, **303 points**, **177–148 goals**; frozen uploaded baseline **84 W / 23 D / 53 L**, **275 points**, **147–139 goals**; 160 matches each / 8 fresh seed blocks. Paired gain **+0.175 points/fixture**, independently reproduced seed-block 95% interval **[0.09375, 0.25]**, 97.5% interval **[0.08125, 0.25625]**.
- Adaptive field mean **0.101954 ms**, max **16.552420 ms**; frozen source mean **0.100690 ms**, max **10.121886 ms**. Both source roles have **zero exceptions, raw misses and fouls**, and **1 rejected kick request each**. **One opposing-side raw miss exists**; do not report all sides as zero.
- The entire field points gain is against the uploaded wall controller (**75 vs 47**, where baseline is self-play). Other styles are unchanged: counter **60/60**, press **59/59**, compact **55/55**, v9.1 **54/54**. Specialist activated in **18/32** upload matches, **0/128** ordinary-style matches.
- Final source / opponent hashes match all four relevant frozen registrations. Final fixtures are complete, unique and balance both pitch assignments and both kickoff arrangements; engine **0.1.0**, config **372990895c7eca2a**, 2400 ticks.
- **Original strong-score gates FAIL:** adaptive wins **61.71875%**, below 75%, and mean goal difference **0.640625**, below 1.5. Positive direct and field confidence bounds and zero final candidate exceptions/misses support an experimental improvement, not the stronger domination claim or automatic promotion.
- Provenance: adaptive-plan.json still references V2; the public-score initialization fix was developed as V3 before fresh final qualification. adaptive-selection.json and both qualification registrations freeze the correct final source SHA. Preserve the original plan, explain this revision rather than altering it.
- Inventory: **1577 JSONL native results + 1 separately recovered aborted native result + 4 timed diagnostic repeats = 1582 timed native attempts**. Five separate untimed parity matches and per-source five-match official intakes are not included in that count.
- Parent timing stalls were not reproduced; their raw failures remain retained. Cache parity establishes behavior preservation and later timing observations, not proof of the original stall's cause.

See final-audit.json for recomputed totals and frozen hashes. No active champion or main branch was changed by this audit.
