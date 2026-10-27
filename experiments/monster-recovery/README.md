# MONSTER Recovery files

**Use [restored/team.py](../../experiments/monster-recovery/restored/team.py) for the recovery.** It restores the frozen team12 reference engine, with only the display name/version and explanatory header changed. It introduces no unproven tactical changes and claims no improvement beyond that reference.

- `restored/team.py`: restores the existing team12 reference decision engine under a recovery name; no new tactical behavior.
- `reference/team.py`: byte-for-byte frozen `sandbox-champion-hunt` reference, provisionally identified by the user as team12.
- `challenger/team.py`: independently qualified keeper-repair experiment; see the gate decision before using it.
- `rejected/late-cover/team.py`: rejected late-cover combination.

Full native results and decision: [report](../../docs/monster-recovery/README.md).
