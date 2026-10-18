# NOVA-1 independent controller

**Failed qualification. Keep v10.0 for competition:** NOVA scored 1,055 points
versus v10.0's 1,659 and had 17 initial deadline misses versus 10. The active
`my-team/team.py` was not changed.

The final learned development candidate is **[team.py](../../experiments/nova-1/team.py)**. Its exact
source hash, learned parameters and selection evidence are in
[selected-policy.json](selected-policy.json).

This is a research candidate, not an automatic replacement for the active
submission. Check the [native validation report](../nova-1-validation.md)
and [promotion decision](decision.json) before using it.
`my-team/team.py` and the archived champions remain unchanged.

The experimental controller is standalone: it needs only `math` and the official
`soccer` SDK. The training tools, JSON registries and other Python files are
not runtime dependencies.

The independent architecture and frozen development generations live in
`tools/nova/`. Native-outcome training is `tools/nova/train.py`; exact source
reconstruction is `tools/nova/rebuild_population.py`; frozen fixture replay is
`tools/nova/replay_registered.py`. All training, development selection and
qualification records are retained in the evidence archive linked by the
validation report.
