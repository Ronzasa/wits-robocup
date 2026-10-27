"""Describe a frozen release's draws from saved results; no matches execute."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def read_report(path):
    data = path.read_bytes()
    if path.suffix == ".jsonl":
        rows = [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
        return rows, {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "kind": "jsonl"}
    report = json.loads(data)
    return report["results"], {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
                               "complete": report.get("complete"), "valid_protocol": report.get("valid_protocol")}


def outcome(row):
    a, b = row["score"]
    return "win" if a > b else "loss" if a < b else "draw"


def team_metrics(rows, side):
    ticks = sum(row["ticks"] for row in rows)
    matches = len(rows)
    stats = [row["stats"][side] for row in rows]
    total = lambda metric: sum(stat.get(metric, 0) for stat in stats)
    ratios = {"possession_fraction": total("possession_ticks")/ticks if ticks else None,
              "control_fraction": total("controlled_ticks")/ticks if ticks else None,
              "territory_fraction": total("territory_ticks")/ticks if ticks else None}
    metrics = ("kicks", "shots", "shots_blocked", "passes_attempted", "passes_completed", "passes_intercepted",
               "dribbles", "dribble_distance", "turnovers", "tackles_attempted", "tackles_won", "fouls")
    totals = {metric: total(metric) for metric in metrics}
    return {"totals": totals, "per_match": {key: value/matches if matches else None for key, value in totals.items()},
            **ratios, "pass_completion": total("passes_completed")/total("passes_attempted") if total("passes_attempted") else None,
            "policy_errors": total("policy_errors"), "policy_timeouts": total("policy_timeouts"),
            "rejected_kicks": sum(stat.get("validation", {}).get("rejected_kicks", 0) for stat in stats)}


def summary(rows):
    counts = collections.Counter(outcome(row) for row in rows)
    return {"matches": len(rows), "wdl": [counts["win"], counts["draw"], counts["loss"]],
            "goals": [sum(row["score"][side] for row in rows) for side in (0, 1)],
            "scores": dict(sorted(collections.Counter(f"{row['score'][0]}-{row['score'][1]}" for row in rows).items())),
            "candidate": team_metrics(rows, 0), "opponent": team_metrics(rows, 1)}


def group_by(rows, field):
    groups = collections.defaultdict(list)
    for row in rows:
        groups[row[field]].append(row)
    return {str(key): summary(subset) for key, subset in groups.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    lock = json.loads((HERE / "selection-v2-lock.json").read_text(encoding="utf-8"))
    key = lock["release"]["key"]
    rows, sources = [], []
    for report in args.reports:
        data, metadata = read_report(Path(report))
        rows.extend(row for row in data if row["candidate_key"] == key)
        sources.append(metadata)
    keys = [(row["opponent_key"], row["seed"], row["candidate_side"], row["kickoff_team"], row["formation"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate release fixtures")
    if any(row.get("platform_error") or row.get("protocol_issues") or row.get("score") is None for row in rows):
        raise ValueError("Release fixtures contain platform/protocol issues")
    draws = [row for row in rows if outcome(row) == "draw"]
    per_opponent = []
    opponents = collections.defaultdict(list)
    for row in rows:
        opponents[row["opponent_spec"]].append(row)
    for spec, subset in opponents.items():
        draw_rows = [row for row in subset if outcome(row) == "draw"]
        per_opponent.append({"opponent": spec, "all": summary(subset), "draws": summary(draw_rows),
                             "wins": summary([row for row in subset if outcome(row) == "win"]),
                             "draws_by_formation": group_by(draw_rows, "formation")})
    per_opponent.sort(key=lambda row: (-row["draws"]["matches"], row["opponent"]))
    result = {"release": lock["release"], "sources": sources,
              "scope": "Read-only exposed V1 holdout diagnosis, not a new policy's final evaluation. Runtime tactical modes and trajectories were not recorded; formation and aggregate metrics are observable here.",
              "overall": summary(rows), "draws": summary(draws),
              "draws_by_formation": group_by(draws, "formation"),
              "draws_by_own_kickoff": group_by(draws, "candidate_kickoff"),
              "draws_by_side": group_by(draws, "candidate_side"),
              "draws_by_score": group_by([dict(row, score_label=f"{row['score'][0]}-{row['score'][1]}") for row in draws], "score_label"),
              "by_opponent": per_opponent,
              "draw_fixtures": [{key: row.get(key) for key in ("match_id", "opponent_spec", "seed", "candidate_side", "candidate_kickoff", "kickoff_team", "score", "formation", "replay_path")}
                                for row in draws]}
    with Path(args.output).open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({"all": result["overall"]["wdl"], "draw_scores": result["draws"]["scores"],
                      "draws_by_formation": {key: value["matches"] for key, value in result["draws_by_formation"].items()}}))
    for row in per_opponent:
        if row["draws"]["matches"]:
            print(json.dumps({"opponent": row["opponent"], "wdl": row["all"]["wdl"], "draw_scores": row["draws"]["scores"],
                              "our_draw_metrics": row["draws"]["candidate"], "their_draw_metrics": row["draws"]["opponent"]}))


if __name__ == "__main__":
    main()
