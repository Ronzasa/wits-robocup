# Frozen TITAN: hypotheses before MONSTER tuning

Protected SHA-256: `5c73068b5e574093e9e1afce972ff8b3546b484c103505c9e79d80772ac6299d`.
The entire frozen source was read. It has a shared physics/control core,
normal play, a wall specialist, and an adaptive controller. MONSTER is a new
implementation and imports none of these policies.

| Area | Source observation | Testable hypothesis, not initially a demonstrated flaw |
|---|---|---|
| Keeper | Home depth 2.2; trajectory tracking starts at vx < -8, speed >=12, linear arrival <1.25 s; central sweeps compare with own chaser rather than always with opponent | Slow goal-bound shots or delayed far-post shots after a rush could beat it |
| Defense | One chaser, one close cover, two marks; lateral cover adjustment only at abs(ball y)>=12 and enemy within 5 | A pincer press or switch of play could open a central runner |
| Interception | Acceleration/coasting reach bounds, sparse forecast; pass reception verified through rollouts | Changing direction within the five-tick cooldown might upset expected recapture |
| Shooting | Seven normal goal targets; lane heuristic plus contact checks and full ground trajectory | Early pressure might force blocked shots or low-value clearances |
| Retention | Multiple nested dribble/pass/bank/handoff searches, explicit receiver plans | A second presser could intercept the release while the first forces it |
| Transition | Quick release activated after observed turnover, room/race gates; counterpress lasts one second with escape gates | An immediate diagonal outlet may outrun its local counterpress |
| Score | Normal policy parks five players as soon as lead>=1; trailing-wall branch removed | Conceding first is expensive, but endpoint trajectories may defeat the wall |
| Wall | Slot x=goal+1.2, y=(-5.6,-2.8,0,2.8,5.6), fixed full-power +x clearance | Ball outside the outer defender's kick radius near the post may finish through an endpoint |
| Adaptation | Four opponents near x=goal+1.2 for six ticks permanently activates specialist | A differently positioned defensive screen may avoid the specialist; must also generalize |
| Wall-breaking | Static gap shot plus three pushers; specialist approaches the corner and models clearance order | A moving/offset screen might resist it; deliberately weak ordinary opponents are not enough evidence |
| CPU | Optional searches share 7 ms budget, but normal movement/receiving still runs afterward | More simultaneous pressure may increase work; runtime exploitation is not the aim and no artificial CPU load is applied |

All tests use official rules, 2,400 ticks and 20 ms decisions. Both actual field
sides and both kickoff owners are explicit fixtures. Training seeds are
700000–700019, validation 710000–710009. Final holdout 730000–730024 is reserved
before selection (100 fixtures). The harness locks its source hash at first
holdout use and refuses to expose those seeds to a different candidate.

## First observed result

MONSTER v01: **0W/3D/13L**, goals **19–32**, in 16 training fixtures across four
seeds and all four fixture types. No policy errors, timeouts or fouls. This
rejects the claim that the initial controller is already competitive with
TITAN. Its 68% possession is misleading because TITAN often retreats after
scoring. In the first recorded match TITAN scored first at tick 185; MONSTER
equalized twice, and TITAN retook the lead after each restart. These events
justify investigating kickoff/first-goal defense and restart transitions.
