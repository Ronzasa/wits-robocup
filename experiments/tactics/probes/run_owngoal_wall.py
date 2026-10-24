import importlib.util, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "harness"))
import common; from common import soccer
sp = importlib.util.spec_from_file_location("w", os.path.join(HERE, "owngoal_wall_probe.py")); w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)
rows = []
for opp in ("bus_wall", "champion_original", "tactical", "balanced"):
    for power in (1.0, 0.6):
        for ty in range(-28, 29, 4):
            w.TY, w.POWER = float(ty), power
            m = soccer.play_match(w.WallBomb(), common.spec(opp), seed=11, kickoff_team=0, max_ticks=1200)
            st = m.result["stats"]
            rows.append({"opp": opp, "power": power, "ty": ty, "score": list(m.score), "own_goals": [t["own_goals"] for t in st], "kicks": [t["kicks"] for t in st]})
tot = {o: [sum(r["score"][0] for r in rows if r["opp"] == o), sum(r["score"][1] for r in rows if r["opp"] == o), sum(sum(r["own_goals"]) for r in rows if r["opp"] == o), len([1 for r in rows if r["opp"] == o])] for o in {r["opp"] for r in rows}}
print("opp: [goals_for, goals_against, own_goals_total, matches]", tot)
json.dump({"engine_sha256": common.engine_hash(), "rows": rows, "totals": tot}, open(os.path.join(common.RESULTS, "owngoal_wall_probe.json"), "w"), indent=1)
