# MONSTER laboratory scorecard

All competitive rows: official engine/config, 2,400 ticks, 20 ms, four fixtures per seed.
Training/validation are selection data. Only the locked holdout is a final estimate.

| Run | Split | N | W/D/L | Goals | Mean GD | Win % | Decisive win % | Mean/max ms | Errors/timeouts |
|---|---|---:|---|---|---:|---:|---:|---|---|
| [blue-control-balanced](results/blue-control-balanced.json) | generalization | 20 | 19/1/0 | 22–3 | +0.950 | 95.0 | 100.0 | 0.036/7.479 | 0/0 |
| [blue-control-possession](results/blue-control-possession.json) | generalization | 20 | 20/0/0 | 20–0 | +1.000 | 100.0 | 100.0 | 0.026/5.549 | 0/0 |
| [blue-control-tactical](results/blue-control-tactical.json) | generalization | 20 | 20/0/0 | 20–0 | +1.000 | 100.0 | 100.0 | 0.041/6.551 | 0/0 |
| [blue-generalization-balanced](results/blue-generalization-balanced.json) | generalization | 20 | 19/1/0 | 22–3 | +0.950 | 95.0 | 100.0 | 0.037/7.408 | 0/0 |
| [blue-generalization-possession](results/blue-generalization-possession.json) | generalization | 20 | 20/0/0 | 20–0 | +1.000 | 100.0 | 100.0 | 0.026/5.495 | 0/0 |
| [blue-generalization-tactical](results/blue-generalization-tactical.json) | generalization | 20 | 20/0/0 | 20–0 | +1.000 | 100.0 | 100.0 | 0.041/6.652 | 0/0 |
| [blue-generalization-titan](results/blue-generalization-titan.json) | generalization | 20 | 3/11/6 | 32–34 | -0.100 | 15.0 | 33.3 | 0.298/12.978 | 0/0 |
| [blue-screen-blue-a-kickoff](results/blue-screen-blue-a-kickoff.json) | train | 16 | 10/6/0 | 28–8 | +1.250 | 62.5 | 100.0 | 0.168/7.510 | 0/0 |
| [blue-screen-blue-b-reserve](results/blue-screen-blue-b-reserve.json) | train | 16 | 7/6/3 | 18–10 | +0.500 | 43.8 | 70.0 | 0.150/7.719 | 0/0 |
| [blue-screen-blue-c-combined](results/blue-screen-blue-c-combined.json) | train | 16 | 3/10/3 | 12–11 | +0.062 | 18.8 | 50.0 | 0.132/7.219 | 0/0 |
| [blue-screen-titan](results/blue-screen-titan.json) | train | 16 | 11/4/1 | 23–7 | +1.000 | 68.8 | 91.7 | 0.154/5.455 | 0/0 |
| [blue-validation-blue-c-combined](results/blue-validation-blue-c-combined.json) | generalization | 20 | 10/7/3 | 27–10 | +0.850 | 50.0 | 76.9 | 0.128/5.678 | 0/0 |
| [blue-validation-titan](results/blue-validation-titan.json) | generalization | 20 | 14/5/1 | 31–6 | +1.250 | 70.0 | 93.3 | 0.132/6.828 | 0/0 |
| [final-selection-v25](results/final-selection-v25.json) | validation | 40 | 29/8/3 | 72–23 | +1.225 | 72.5 | 90.6 | 0.162/18.493 | 0/0 |
| [grid01-v02-press](results/grid01-v02-press.json) | train | 16 | 0/1/15 | 26–41 | -0.938 | 0.0 | 0.0 | 0.623/11.938 | 0/0 |
| [grid01-v03-shield](results/grid01-v03-shield.json) | train | 16 | 0/8/8 | 20–28 | -0.500 | 0.0 | 0.0 | 0.618/10.950 | 0/0 |
| [grid01-v04-lock](results/grid01-v04-lock.json) | train | 16 | 0/8/8 | 25–33 | -0.500 | 0.0 | 0.0 | 0.611/16.276 | 0/0 |
| [grid01-v05-fortress](results/grid01-v05-fortress.json) | train | 16 | 0/12/4 | 16–20 | -0.250 | 0.0 | 0.0 | 0.612/17.130 | 0/0 |
| [grid02-v06-duel](results/grid02-v06-duel.json) | train | 16 | 2/6/8 | 30–36 | -0.375 | 12.5 | 20.0 | 0.533/10.888 | 0/0 |
| [grid02-v07-duel-shield](results/grid02-v07-duel-shield.json) | train | 16 | 2/8/6 | 28–32 | -0.250 | 12.5 | 25.0 | 0.532/11.099 | 0/0 |
| [grid03-v08-duel-fortress](results/grid03-v08-duel-fortress.json) | train | 16 | 0/10/6 | 20–26 | -0.375 | 0.0 | 0.0 | 0.643/11.294 | 0/0 |
| [grid03-v09-twins](results/grid03-v09-twins.json) | train | 16 | 0/10/6 | 35–41 | -0.375 | 0.0 | 0.0 | 0.635/12.843 | 0/0 |
| [grid03-v10-twin-press](results/grid03-v10-twin-press.json) | train | 16 | 1/7/8 | 20–27 | -0.438 | 6.2 | 11.1 | 0.631/10.760 | 0/0 |
| [grid04-v11-shell](results/grid04-v11-shell.json) | train | 16 | 6/2/8 | 23–28 | -0.312 | 37.5 | 42.9 | 0.188/8.491 | 0/0 |
| [grid04-v12-shell-close](results/grid04-v12-shell-close.json) | train | 16 | 4/5/7 | 15–21 | -0.375 | 25.0 | 36.4 | 0.246/9.754 | 0/0 |
| [grid05-hybrid](results/grid05-hybrid.json) | train | 16 | 6/2/8 | 23–28 | -0.312 | 37.5 | 42.9 | 0.194/8.799 | 0/0 |
| [grid06-v14-score-release](results/grid06-v14-score-release.json) | train | 16 | 6/2/8 | 19–30 | -0.688 | 37.5 | 42.9 | 0.317/6.736 | 0/0 |
| [grid06-v15-bank-five](results/grid06-v15-bank-five.json) | train | 16 | 1/9/6 | 17–22 | -0.312 | 6.2 | 14.3 | 0.207/8.704 | 0/0 |
| [grid06-v16-hybrid-bank](results/grid06-v16-hybrid-bank.json) | train | 16 | 1/6/9 | 13–30 | -1.062 | 6.2 | 10.0 | 0.303/8.173 | 0/0 |
| [grid07-v17-keeper-shell](results/grid07-v17-keeper-shell.json) | train | 16 | 7/0/9 | 20–21 | -0.062 | 43.8 | 43.8 | 0.298/27.110 | 0/6 |
| [grid07-v18-keeper-press](results/grid07-v18-keeper-press.json) | train | 16 | 3/2/11 | 28–36 | -0.500 | 18.8 | 21.4 | 0.555/21.800 | 0/3 |
| [grid08-v19-fast-keeper](results/grid08-v19-fast-keeper.json) | train | 16 | 5/3/8 | 18–22 | -0.250 | 31.2 | 38.5 | 0.193/16.796 | 0/0 |
| [grid08-v20-safe-five](results/grid08-v20-safe-five.json) | train | 16 | 1/6/9 | 21–33 | -0.750 | 6.2 | 10.0 | 0.166/7.209 | 0/0 |
| [grid09-v21-close-outlet](results/grid09-v21-close-outlet.json) | train | 16 | 8/1/7 | 28–24 | +0.250 | 50.0 | 53.3 | 0.197/6.830 | 0/0 |
| [grid09-v22-close-model](results/grid09-v22-close-model.json) | train | 16 | 7/1/8 | 23–19 | +0.250 | 43.8 | 46.7 | 0.205/8.302 | 0/0 |
| [grid10-v23-post-pressure](results/grid10-v23-post-pressure.json) | train | 16 | 9/7/0 | 29–13 | +1.000 | 56.2 | 100.0 | 0.165/8.296 | 0/0 |
| [grid10-v24-post-model](results/grid10-v24-post-model.json) | train | 16 | 7/8/1 | 19–9 | +0.625 | 43.8 | 87.5 | 0.200/15.082 | 0/0 |
| [monster-generalization-balanced](results/monster-generalization-balanced.json) | generalization | 20 | 20/0/0 | 107–1 | +5.300 | 100.0 | 100.0 | 0.077/6.507 | 0/0 |
| [monster-generalization-possession](results/monster-generalization-possession.json) | generalization | 20 | 20/0/0 | 133–0 | +6.650 | 100.0 | 100.0 | 0.072/4.676 | 0/0 |
| [monster-generalization-tactical](results/monster-generalization-tactical.json) | generalization | 20 | 17/3/0 | 41–4 | +1.850 | 85.0 | 100.0 | 0.067/3.309 | 0/0 |
| [monster-generalization-titan-buggy](results/monster-generalization-titan-buggy.json) | generalization | 20 | 14/2/4 | 33–11 | +1.100 | 70.0 | 77.8 | 0.104/6.722 | 0/0 |
| [monster-generalization-titan-original](results/monster-generalization-titan-original.json) | generalization | 20 | 14/2/4 | 33–11 | +1.100 | 70.0 | 77.8 | 0.101/5.448 | 0/0 |
| [monster-generalization-v06-duel](results/monster-generalization-v06-duel.json) | generalization | 20 | 15/2/3 | 79–33 | +2.300 | 75.0 | 83.3 | 0.142/6.017 | 0/0 |
| [monster-generalization-v21-close-outlet](results/monster-generalization-v21-close-outlet.json) | generalization | 20 | 4/10/6 | 26–29 | -0.150 | 20.0 | 40.0 | 0.130/7.442 | 0/0 |
| [monster-v25-holdout](results/monster-v25-holdout.json) | holdout | 100 | 79/14/7 | 185–57 | +1.280 | 79.0 | 91.9 | 0.145/9.626 | 0/0 |
| [selection-v21-close-outlet](results/selection-v21-close-outlet.json) | validation | 40 | 17/14/9 | 61–51 | +0.250 | 42.5 | 65.4 | 0.204/7.451 | 0/0 |
| [selection-v23-post-pressure](results/selection-v23-post-pressure.json) | validation | 40 | 29/8/3 | 73–22 | +1.275 | 72.5 | 90.6 | 0.193/71.721 | 0/2 |
| [selection-v24-post-model](results/selection-v24-post-model.json) | validation | 40 | 28/9/3 | 67–25 | +1.050 | 70.0 | 90.3 | 0.225/62.249 | 0/1 |
| [v01-titan](results/v01-titan.json) | train | 16 | 0/3/13 | 19–32 | -0.812 | 0.0 | 0.0 | 0.626/12.578 | 0/0 |

Protected original TITAN SHA-256: `5c73068b5e574093e9e1afce972ff8b3546b484c103505c9e79d80772ac6299d`.
Full JSON reports retain source hashes, immutable snapshots, per-fixture results, passing/possession/shot/interception statistics and uncertainty intervals.
