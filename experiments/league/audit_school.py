"""Read-only public replay measurements; never executes a match or student source."""
import argparse
import collections
import datetime
import json
import math
import statistics
from pathlib import Path


SCHOOL = Path(__file__).resolve().parent / "school"
SLUG = "401976-nkqubela-hokwana"


def xy(position):
    return [round(position["x"], 5), round(position["y"], 5)]


def guard_prediction(frame, player_id, post_max):
    # Formula from the public local MONSTER source, independently evaluated on
    # recorded states. No controller, engine or opponent source is loaded.
    bx, by = xy(frame["ball_position"])
    score = frame["score"]
    depth = 3.3 if score[0] > score[1] else 1.2
    aim = [-50 + depth, (5.4, -1.8, 1.8, -5.4)[player_id]]
    if bx < -38 and abs(by) > 4 and player_id == (0 if by > 0 else 3):
        aim = [max(-48.98, min(-50 + depth, bx - .6)),
               (1 if by > 0 else -1)*max(5.4, min(post_max, abs(by)))]
    player = frame["players"][player_id]
    px, py = player["position"]["x"], player["position"]["y"]
    vx, vy = player["velocity"]["x"], player["velocity"]["y"]
    dx, dy = aim[0] - px, aim[1] - py
    distance = math.hypot(dx, dy)
    gain = min(8, distance*6)/max(distance, 1e-9)
    ax, ay = dx*gain-vx*.9, dy*gain-vy*.9
    norm = max(1, math.hypot(ax, ay))
    return [ax/norm, ay/norm]


def replay_summary(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    header, frames, events = data["header"], data["frames"], data["events"]
    side = header["team_ids"].index(SLUG)
    if side != 0:
        raise ValueError("This diagnostic currently expects selected home replays")
    result = {"file": path.name, "header": {key: header[key] for key in
              ("engine_version", "config_hash", "seed", "kickoff_team", "team_ids", "players_per_team")},
              "created_utc": datetime.datetime.fromtimestamp(header["created_unix_seconds"], datetime.timezone.utc).isoformat(),
              "recorded": data.get("recorded"), "initial_positions": [xy(p["start"]) for p in header["initial_roster"][:5]],
              "frames": len(frames), "last_tick": frames[-1]["tick"], "final_score": frames[-1]["score"],
              "event_counts": dict(collections.Counter(event["kind"] for event in events))}
    result["player_geometry"] = []
    for player_id in range(5):
        points = [frame["players"][player_id]["position"] for frame in frames if frame["tick"] >= 120]
        result["player_geometry"].append({"id": player_id,
            "median_x": statistics.median(p["x"] for p in points),
            "x_range": [min(p["x"] for p in points), max(p["x"] for p in points)],
            "y_range": [min(p["y"] for p in points), max(p["y"] for p in points)],
            "goal_line_fraction": statistics.mean(p["x"] < -43 and abs(p["y"]) < 9 for p in points)})
    wall_by_state = collections.defaultdict(list)
    for frame in frames:
        a, b = frame["score"]
        state = "leading" if a > b else "trailing" if a < b else "level"
        wall_by_state[state].append(sum(p["position"]["x"] < -43 and abs(p["position"]["y"]) < 9
                                      for p in frame["players"][:5]) >= 4)
    result["four_guard_fraction_by_score"] = {state: {"frames": len(values), "fraction": statistics.mean(values)}
                                             for state, values in wall_by_state.items()}
    result["local_guard_formula_check"] = {}
    for post_max in (7.3, 9.5):
        residuals = []
        for previous, current in zip(frames, frames[1:]):
            if previous["tick"] < 120 or current["tick"] != previous["tick"] + 1:
                continue
            for player_id in range(4):
                action = current["players"][player_id].get("action")
                if action is None:
                    continue
                predicted = guard_prediction(previous, player_id, post_max)
                actual = action["movement"]
                residuals.append(math.hypot(predicted[0] - actual["x"], predicted[1] - actual["y"]))
        result["local_guard_formula_check"][str(post_max)] = {
            "decisions": len(residuals), "within_1e-3": sum(value < .001 for value in residuals),
            "mean_error": statistics.mean(residuals), "max_error": max(residuals)}
    result["goals"] = []
    indexed = {frame["tick"]: frame for frame in frames}
    for goal in (event for event in events if event["kind"] == "goal"):
        context = []
        for offset in (-60, -20, -5, 0):
            frame = indexed.get(goal["tick"] + offset)
            if frame is None:
                continue
            context.append({"tick": frame["tick"], "score": frame["score"],
                            "ball": xy(frame["ball_position"]), "ball_velocity": xy(frame["ball_velocity"]),
                            "ours": [xy(p["position"]) for p in frame["players"][:5]],
                            "opponents": [xy(p["position"]) for p in frame["players"][5:]]})
        kicks = [event for event in events if event["kind"] == "kick" and goal["tick"] - 60 <= event["tick"] <= goal["tick"]]
        result["goals"].append({"event": goal, "last_kicks": kicks[-5:], "context": context})
    return result


def snapshot_comparison():
    paths = [SCHOOL / "nkqubela-current.json", SCHOOL / "nkqubela-later.json"]
    if not all(path.exists() for path in paths):
        return None
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    old, new = [{row["match_id"]: row for row in report["matches"]} for report in reports]
    common = old.keys() & new.keys()
    def summary(rows):
        wins = sum(row["score"][0] > row["score"][1] for row in rows)
        draws = sum(row["score"][0] == row["score"][1] for row in rows)
        return {"matches": len(rows), "wdl": [wins, draws, len(rows)-wins-draws],
                "points": 3*wins+draws, "ppg": (3*wins+draws)/len(rows) if rows else None,
                "goals": [sum(row["score"][i] for row in rows) for i in (0, 1)]}
    return {"files": [path.name for path in paths], "runs": [report["run"] for report in reports],
            "standings": [{key: report["standing"].get(key) for key in
                            ("rank", "division", "played", "points", "wins", "draws", "losses", "goals_for", "goals_against", "policy_errors", "policy_timeouts", "forfeits", "last_updated")}
                           for report in reports],
            "matched_fixtures": len(common), "changed_scores": sum(old[key]["score"] != new[key]["score"] for key in common),
            "old_only": len(old.keys()-common), "new_only": len(new.keys()-common),
            "matched_before": summary([old[key] for key in common]),
            "matched_after": summary([new[key] for key in common]),
            "attribution_limit": "Different live ladder snapshots; no source hashes and no fixed opponent-source cohort. This is not a controlled Titan-versus-Monster trial."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replays", nargs="+")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = {"scope": "Observed replay behavior; no source hash, historical source identity or school dominance inferred.",
              "replays": [replay_summary(Path(path)) for path in args.replays],
              "snapshot_comparison": snapshot_comparison()}
    with Path(args.output).open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    for replay in result["replays"]:
        print(json.dumps({key: replay[key] for key in ("file", "recorded", "final_score", "four_guard_fraction_by_score", "local_guard_formula_check")}))


if __name__ == "__main__":
    main()
