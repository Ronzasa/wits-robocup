# TITAN-X special-tactic experiments

The active controller remains frozen TITAN v10.0 in `my-team/team.py`.
TITAN-X is developed only on `titan-x-special-tactics`.

- [Actual validation results](titan-x-validation.md)
- [Tactical Opportunity Manager and safety checks](architecture.md)
- [Retained Goalkeeper Power Play concept](goalkeeper-power-play.md)
- [Original request](titan-x-request.md)
- [Preregistered selection and promotion rules](registration.json)
- [Frozen selection](selection.json)
- [Qualification protocol](qualification-protocol.json)
- [Qualification results](qualification-results.json)
- [Final decision](decision.json)

The all-off starting controller is
[`experiments/titan-x/team.py`](../../experiments/titan-x/team.py).
The four standalone experimental files are:

| Tactic | Only enabled flag | File |
|---|---|---|
| Goalkeeper Power Play | `KEEPER_POWER_PLAY` | [team.py](../../experiments/titan-x-power/team.py) |
| Goalkeeper Trap | `GOALKEEPER_TRAP` | [team.py](../../experiments/titan-x-trap/team.py) |
| Pinball Slingshot | `PINBALL_SLINGSHOT` | [team.py](../../experiments/titan-x-pinball/team.py) |
| Cooldown Ambush | `COOLDOWN_AMBUSH` | [team.py](../../experiments/titan-x-ambush/team.py) |

Each folder contains a self-contained `team.py`. Assembly helpers are offline
development tools; competition controllers do not read them or any other file.
An integrated variant is produced only if independent results justify it.
Full native records, validation reports, exact repeats and frozen sources are
archived with a per-file hash manifest; see [evidence metadata](evidence.json).
