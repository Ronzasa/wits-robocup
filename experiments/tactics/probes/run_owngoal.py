"""Sweep end-wall rebound kicks vs a pinned defensive wall; count own goals. -> results/owngoal_probe.json"""
import importlib.util, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "harness"))
import common
from common import soccer
sp = importlib.util.spec_from_file_location("og", os.path.join(HERE, "owngoal_probe.py"))
og = importlib.util.module_from_spec(sp); sp.loader.exec_module(og)
rows = []
for opp in ("bus_wall", "champion_original"):
    for power in (1.0, 0.7):
        for ang in range(-40, 41, 2):
            og.ANGLE, og.POWER = float(ang), power
            m = soccer.play_match(og.OwnGoalProbe(), common.spec(opp), seed=7, kickoff_team=0, max_ticks=400)
            st = m.result["stats"]
            rows.append({"opp": opp, "power": power, "angle": ang, "score": list(m.score), "stats_own_goals": [t.get("own_goals", 0) for t in st], "stats_defender_kicks": [t.get("kicks", 0) for t in st], "goal_events": [str(e) for _, e in og.GOALS]})
n_own = sum(1 for r in rows if any(r["stats_own_goals"]))
print("configs", len(rows), "with own goal", n_own, "any goals", sum(1 for r in rows if sum(r["score"])))
os.makedirs(common.RESULTS, exist_ok=True)
json.dump({"engine_sha256": common.engine_hash(), "rows": rows}, open(os.path.join(common.RESULTS, "owngoal_probe.json"), "w"), indent=1)
for r in rows:
    if sum(r["score"]): print(r)
