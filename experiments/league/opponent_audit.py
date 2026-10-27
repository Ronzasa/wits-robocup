"""Read-only reliability audit of opponents in existing league benchmark results."""
import argparse
import hashlib
import json
from pathlib import Path


def terminal_forfeit(row):
    reason = row.get("terminal_reason")
    if isinstance(reason, dict) and "forfeit" in reason:
        return reason["forfeit"].get("team")
    return row.get("forfeit_by")


def read(path):
    contents = path.read_bytes()
    if path.suffix == ".jsonl":
        lines = contents.decode("utf-8").splitlines()
        rows, incomplete = [], False
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                if index != len(lines)-1:
                    raise
                incomplete = True
        return rows, {"complete": False, "trailing_incomplete_line": incomplete}, contents
    report = json.loads(contents)
    return report["results"], {key: report.get(key) for key in
                               ("complete", "valid_protocol", "infrastructure_unchanged", "source_snapshots_unchanged")}, contents


def audit(path):
    rows, metadata, contents = read(path)
    groups, fault_rows = {}, []
    seen = set()
    duplicate_count = 0
    for row in rows:
        fixture = (row["candidate_key"], row["opponent_key"], row["seed"],
                   row["candidate_side"], row["kickoff_team"], row.get("formation", "custom"))
        duplicate_count += fixture in seen
        seen.add(fixture)
        key = row["opponent_key"]
        group = groups.setdefault(key, {"opponent": row["opponent_spec"], "opponent_key": key,
            "matches": 0, "candidates": {}, "decisions": 0, "decision_total_ms": 0,
            "decision_max_ms": 0, "policy_errors": 0, "policy_timeouts": 0,
            "opponent_forfeits": 0, "candidate_forfeits": 0,
            "platform_errors": 0, "protocol_failures": 0, "validation": {}})
        group["matches"] += 1
        candidate = row["candidate_spec"]
        group["candidates"][candidate] = group["candidates"].get(candidate, 0)+1
        stats = row.get("stats", [{}, {}])[1]
        timing = stats.get("decision_time_ms", {})
        group["decisions"] += timing.get("count", 0)
        group["decision_total_ms"] += timing.get("total_ms", 0)
        group["decision_max_ms"] = max(group["decision_max_ms"], timing.get("max_ms", 0))
        errors, timeouts = stats.get("policy_errors", 0), stats.get("policy_timeouts", 0)
        group["policy_errors"] += errors
        group["policy_timeouts"] += timeouts
        validation = stats.get("validation", {})
        for metric, value in validation.items():
            group["validation"][metric] = group["validation"].get(metric, 0)+value
        forfeit = terminal_forfeit(row)
        opponent_forfeit = forfeit is not None and forfeit != row["candidate_side"]
        candidate_forfeit = forfeit is not None and forfeit == row["candidate_side"]
        group["opponent_forfeits"] += opponent_forfeit
        group["candidate_forfeits"] += candidate_forfeit
        group["platform_errors"] += bool(row.get("platform_error"))
        group["protocol_failures"] += bool(row.get("protocol_issues"))
        illegal = {metric: validation.get(metric, 0) for metric in
                   ("non_finite_values", "missing_actions", "invalid_player_ids") if validation.get(metric, 0)}
        if errors or timeouts or opponent_forfeit or illegal or row.get("platform_error") or row.get("protocol_issues"):
            fault_rows.append({"match_id": row["match_id"], "candidate": candidate,
                "opponent": row["opponent_spec"], "candidate_side": row["candidate_side"],
                "score": row.get("score"), "opponent_errors": errors, "opponent_timeouts": timeouts,
                "opponent_forfeit": opponent_forfeit, "validation": illegal,
                "platform_error": row.get("platform_error"), "protocol_issues": row.get("protocol_issues", [])})
    for group in groups.values():
        group["decision_mean_ms"] = group["decision_total_ms"]/group["decisions"] if group["decisions"] else None
    totals = {metric: sum(group[metric] for group in groups.values()) for metric in
              ("matches", "decisions", "policy_errors", "policy_timeouts", "opponent_forfeits", "candidate_forfeits", "platform_errors", "protocol_failures")}
    illegal_totals = {metric: sum(group["validation"].get(metric, 0) for group in groups.values())
                      for metric in ("non_finite_values", "missing_actions", "invalid_player_ids")}
    critical = bool(totals["policy_errors"] or totals["opponent_forfeits"] or totals["platform_errors"]
                    or totals["protocol_failures"] or any(illegal_totals.values()) or duplicate_count)
    return {"file": str(path), "sha256": hashlib.sha256(contents).hexdigest(), **metadata,
            "duplicate_fixtures": duplicate_count, "opponent_totals": totals,
            "illegal_action_totals": illegal_totals, "critical_reliability_issue": critical,
            "by_opponent": list(groups.values()), "fault_fixtures": fault_rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError("Existing audit evidence; use a fresh output")
    result = {"scope": "Opponent stats[1], normalized by the benchmark; no matches executed or outcomes removed.",
              "reports": [audit(Path(path)) for path in args.reports]}
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    for report in result["reports"]:
        print(json.dumps({key: report[key] for key in ("file", "complete", "opponent_totals", "illegal_action_totals", "critical_reliability_issue")}))
        for opponent in report["by_opponent"]:
            if opponent["policy_errors"] or opponent["policy_timeouts"] or opponent["opponent_forfeits"]:
                print(json.dumps({"opponent": opponent["opponent"], "matches": opponent["matches"],
                                  "errors": opponent["policy_errors"], "timeouts": opponent["policy_timeouts"],
                                  "forfeits": opponent["opponent_forfeits"]}))


if __name__ == "__main__":
    main()
