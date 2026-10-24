"""Run the wedging mechanism probe vs the sealed wall. Writes results/wedge_probe.json."""
import importlib.util, json, os, statistics, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "harness"))
import common
from common import soccer
sp = importlib.util.spec_from_file_location("wedge_probe", os.path.join(os.path.dirname(os.path.abspath(__file__)), "wedge_probe.py"))
wp = importlib.util.module_from_spec(sp); sp.loader.exec_module(wp)

LANE = 1.15
CONFIGS = [(0, "mid"), (2, "mid"), (3, "mid"), (4, "mid"), (3, "flank"), (4, "flank")]
SEEDS = list(range(100, 130))
TICKS = 900
out = {"engine_sha256": common.engine_hash(), "lane_min_width": LANE, "ticks": TICKS, "seeds": [SEEDS[0], SEEDS[-1]], "rows": []}
for n, target in CONFIGS:
    wp.N, wp.TARGET = n, target
    first, final_gaps, best_gaps, disp, frac = [], [], [], [], []
    opened = 0
    for seed in SEEDS:
        soccer.play_match(wp.WedgeProbe(), common.spec("bus_wall"), seed=seed, kickoff_team=1, max_ticks=TICKS)
        log = wp.LOG
        SETTLE = 100
        late = [(t, g) for t, g, *_ in log if t >= SETTLE]
        t_open = next((t for t, g in late if g >= LANE), None)
        frac.append(sum(1 for _, g in late if g >= LANE) / len(late))
        if t_open is not None:
            opened += 1; first.append((t_open - SETTLE) / 20.0)
        best_gaps.append(max(g for t, g, *_ in log if t >= SETTLE))
        final_gaps.append(log[-1][1])
        disp.append(log[0][4] - min(x for *_, x in log[-100:]) if False else log[-1][4] - log[5][4])
    row = {"pushers": n, "target": target, "seeds": len(SEEDS), "lane_opened_after_settle": opened,
           "p_open": opened / len(SEEDS), "median_seconds_to_open": statistics.median(first) if first else None,
           "mean_fraction_ticks_open": statistics.mean(frac), "mean_best_gap": statistics.mean(best_gaps), "mean_final_gap": statistics.mean(final_gaps),
           "mean_wall_x_shift": statistics.mean(disp)}
    out["rows"].append(row)
    print(row, flush=True)
os.makedirs(common.RESULTS, exist_ok=True)
json.dump(out, open(os.path.join(common.RESULTS, "wedge_probe.json"), "w"), indent=1)
