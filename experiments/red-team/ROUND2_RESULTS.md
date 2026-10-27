# Second-generation MONSTER: locked holdout

100 full fixtures per opponent and policy; 25 seeds crossed with both sides and kickoff owners.
Official engine 0.1.0, unchanged course config, 2,400 ticks, enforced 20 ms for both teams.

| Opponent | Old v25 W/D/L | New v51 W/D/L | Old goals | New goals | Paired points/game change (95% seed CI) |
|---|---:|---:|---:|---:|---:|
| titan | 73/24/3 | 86/14/0 | 173–61 | 178–26 | +0.290 [+0.120, +0.460] |
| blue-c-combined | 38/33/29 | 46/50/4 | 103–77 | 91–26 | +0.410 [+0.150, +0.670] |
| v21-close-outlet | 19/56/25 | 37/59/4 | 126–134 | 82–39 | +0.570 [+0.220, +0.910] |
| v25-fast-post | 37/27/36 | 57/30/13 | 125–125 | 114–51 | +0.630 [+0.390, +0.850] |

Overall: old **167/140/93, 527–397**; new **226/153/21, 465–142**.
Pooled points/game change **+0.475**, seed-bootstrap 95% CI **[0.3725, 0.5825]**.

New policy errors/timeouts: **0/3**.
New decision mean/max: **0.123/59.192 ms**.

Each arm has 400 fixtures but 25 seed clusters. Paired bootstrap resamples seeds, not individual games. Timeout-filtered results are descriptive sensitivity only; all fixtures remain primary.

Full metrics, per-opponent latency and fault-free sensitivity are in `ROUND2_AUDIT.json`.
See `ROUND2.md` for rejected experiments and `ROUND2_REPORT.md` for interpretation.
