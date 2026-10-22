# Integrated keeper back pass, width and attacking phases

Experimental branch `keeper-width-attacking-phases`. The single requested candidate is `experiments/keeper-width-attack/team.py`; it includes the existing keeper back pass. Main and the active Elite Replay Cutback champion stay unchanged.

The standard match uses normal play for 0–60 seconds, moderate attack for 60–90 seconds, and ultra attack for 90–120 seconds. Scheduling uses actual match ticks and simulation rate, with no score exception. First-half normal means normal attacking intent with the requested wider support and back passes. The final phase advances free receivers and preserves a late counter outlet; the keeper, ball chaser and defensive cover retain their jobs.

Off-ball targets favor open passing lanes, more lateral width, at least 7.5 units from the ball and 6 units from other assigned targets. A short 0.4-second hold limits unnecessary switching, and urgent pressure can invalidate it. Existing pass plans, keeper saves, cover, restart restrictions, counterpress duties and the successful central cutback retain priority. Width is applied to available support players; nobody can be guaranteed to be unmarked on every tick. Actual passes still require the inherited executable receiver and opponent races.

`registration.json` freezes sources, fresh seeds and reliability gates before native development. The sandbox compares the integrated source with active and the older back-pass-only controller; those are baselines, not alternative deliverables. No large winning margin is claimed without measured results.
