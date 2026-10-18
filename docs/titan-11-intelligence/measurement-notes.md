# Measurement definitions

The competition result is the native official result, scored 3/1/0. Accepted
records retain the first interruption-free exact repetition; initial raw records
and all failed repetitions are preserved separately. Deadline qualification uses
initial raw candidate misses per fixture, never accepted-only counts. Both raw
and accepted football results are reported.

Confidence intervals resample complete independent seed blocks. Each block
contains every opponent, both field assignments and both kickoff arrangements.
Local inference is conditional on this fixed opponent pool and does not establish
an improvement in the online class standings.

The official result supplies goals, shots, passes attempted/completed/intercepted,
turnovers, possession/control and action-validation counters. Uncollected passes
are the derived difference `attempted - completed - intercepted`; this is the
engine's aggregate accounting, not a video-labelled reception count.

Raw controller runtime is measured by the unchanged SDK's `_decide`. A wrapper
records its returned elapsed time after that measurement finishes. Histogram bins
are 0.025 ms wide; reported p99 and p99.9 are intervals within those bins. Mean
and maximum use exact SDK totals. Experiments run serially, without concurrent
profiling, learning, regression suites or native diagnostic matches. Per-fixture
CPU/wall totals and cgroup CPU-throttling changes are retained. These can reveal
coincident scheduling pressure but do not prove the cause of a specific spike.

Additional diagnostic metrics use public observations. A counterattack concession
is provisionally labelled when an opposing goal follows an observed control loss
within 80 ticks. This misses losses without control and may include other goal
sequences; it is a proxy, not official attribution. Danger-contact ticks require
an opponent within kick range while the ball is in the final defensive quarter.
A goalbound-shot forecast describes flight time, goal-line aperture and end speed.
The learned shot target is a goal within the following 40 observations, rather
than a claim to calibrated xG or causal attribution of every goal to that kick.
Goal conversion in the native aggregate is goals divided by native shot count.

Learning traces and replays contain diagnostic instrumentation and are excluded
from official decision-time and reliability comparisons. Training labels use
native outcomes and public state/action traces only. The exported training
sample artifact preserves every feature and label actually used by fitting; the
full trace SHA and all native training results are retained for provenance.
