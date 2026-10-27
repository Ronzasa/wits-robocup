"""Compact league tables and paired seed-cluster comparisons, including JSONL."""
import argparse
import json
import random
import statistics
from pathlib import Path


def load(path):
    source = Path(path)
    if source.suffix == ".jsonl":
        lines = source.read_text(encoding="utf-8").splitlines()
        rows = []
        trailing_incomplete = False
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                if index != len(lines) - 1:
                    raise
                trailing_incomplete = True
        return rows, {"complete": False, "trailing_incomplete_line": trailing_incomplete}
    report = json.loads(source.read_text(encoding="utf-8"))
    return report["results"], {key: report.get(key) for key in
                               ("complete", "valid_protocol", "infrastructure_unchanged")}


def score(row):
    reason = row.get("terminal_reason")
    if isinstance(reason, dict) and "forfeit" in reason:
        return [0, 3] if reason["forfeit"]["team"] == row["candidate_side"] else [3, 0]
    return row["score"]


def points(row):
    a, b = score(row)
    return 3 if a > b else int(a == b)


def metrics(rows):
    scored = [r for r in rows if r.get("score") is not None]
    wins = sum(score(r)[0] > score(r)[1] for r in scored)
    draws = sum(score(r)[0] == score(r)[1] for r in scored)
    losses = len(scored) - wins - draws
    stats = [r["stats"][0] for r in scored]
    decisions = sum(s.get("decision_time_ms", {}).get("count", 0) for s in stats)
    decision_ms = sum(s.get("decision_time_ms", {}).get("total_ms", 0) for s in stats)
    validation = {}
    for stat in stats:
        for key, value in stat.get("validation", {}).items():
            validation[key] = validation.get(key, 0) + value
    return {"scheduled_matches": len(rows), "scored_matches": len(scored),
            "wdl": [wins, draws, losses], "points": 3*wins + draws,
            "points_per_match": (3*wins + draws)/len(rows) if rows else None,
            "goals": [sum(score(r)[i] for r in scored) for i in (0, 1)],
            "mean_ms": decision_ms/decisions if decisions else None,
            "max_ms": max((s.get("decision_time_ms", {}).get("max_ms", 0) for s in stats), default=0),
            "policy_errors": sum(s.get("policy_errors", 0) for s in stats),
            "policy_timeouts": sum(s.get("policy_timeouts", 0) for s in stats),
            "validation": validation,
            "platform_errors": sum(bool(r.get("platform_error")) for r in rows),
            "protocol_failures": sum(bool(r.get("protocol_issues")) for r in rows),
            "forfeits": sum("forfeit" in r.get("terminal_reason", "") for r in rows)}


def candidate_map(rows):
    candidates = {}
    seen = set()
    for row in rows:
        fixture = (row["candidate_key"], row["opponent_key"], row["seed"],
                   row["candidate_side"], row["kickoff_team"], row.get("formation", "custom"))
        if fixture in seen:
            raise ValueError("Duplicate fixture across input reports: " + str(fixture))
        seen.add(fixture)
        candidates.setdefault(row["candidate_key"], {"spec": row["candidate_spec"], "rows": []})["rows"].append(row)
    return candidates


def find_candidate(candidates, selector):
    exact = [key for key, value in candidates.items() if selector in (key, value["spec"], key.split(":", 1)[-1])]
    if len(exact) == 1:
        return exact[0]
    matches = [key for key, value in candidates.items()
               if key.split(":", 1)[-1].startswith(selector)
               or Path(value["spec"]).parent.name == selector]
    if len(matches) != 1:
        raise ValueError("Candidate selector must identify one source: " + selector)
    return matches[0]


def compact_table(candidates):
    print("| Candidate | Opponent | N | W/D/L | Points | GF/GA | Mean/max ms | Errors/timeouts | Platform/protocol |")
    print("|---|---|---:|---|---:|---|---|---|---|")
    summaries = []
    for key, candidate in candidates.items():
        groups = {}
        for row in candidate["rows"]:
            groups.setdefault((row["opponent_key"], row["opponent_spec"]), []).append(row)
        for (opponent_key, opponent), rows in [*groups.items(), (("overall", "ALL"), candidate["rows"])]:
            stats = metrics(rows)
            label = Path(candidate["spec"]).parent.name
            against = opponent if opponent == "ALL" or "/" not in opponent and "\\" not in opponent else Path(opponent).parent.name
            mean = "n/a" if stats["mean_ms"] is None else f"{stats['mean_ms']:.4f}"
            print(f"| {label} | {against} | {stats['scheduled_matches']} | {'/'.join(map(str, stats['wdl']))} | {stats['points']} | {'/'.join(map(str, stats['goals']))} | {mean}/{stats['max_ms']:.3f} | {stats['policy_errors']}/{stats['policy_timeouts']} | {stats['platform_errors']}/{stats['protocol_failures']} |")
            summaries.append({"candidate_key": key, "candidate": candidate["spec"],
                              "opponent_key": opponent_key, "opponent": opponent, **stats})
    return summaries


def paired(candidates, before, after):
    before_key, after_key = [find_candidate(candidates, selector) for selector in (before, after)]
    def index_rows(rows):
        indexed = {}
        for row in rows:
            key = (row["opponent_key"], row["seed"], row["candidate_side"], row["kickoff_team"],
                   row.get("formation", "custom"))
            if key in indexed:
                raise ValueError("Duplicate comparison fixture: " + str(key))
            indexed[key] = row
        return indexed
    old, new = [index_rows(candidates[key]["rows"]) for key in (before_key, after_key)]
    common = old.keys() & new.keys()
    if not common:
        raise ValueError("Candidates have no matched fixtures")
    broken = [key for key in common if old[key].get("score") is None or new[key].get("score") is None
              or old[key].get("protocol_issues") or new[key].get("protocol_issues")]
    if broken:
        raise ValueError("Matched comparison has platform/protocol failures; refusing to drop or score them")
    seed_values = {}
    opponent_values = {}
    for key in sorted(common):
        difference = points(new[key]) - points(old[key])
        seed_values.setdefault(key[1], []).append(difference)
        opponent_values.setdefault(key[0], []).append(difference)
    clusters = list(seed_values.values())
    total = sum(map(sum, clusters))
    count = sum(map(len, clusters))
    rng = random.Random(917482)
    bootstrap = []
    if len(clusters) > 1:
        for _ in range(5000):
            sampled = rng.choices(clusters, k=len(clusters))
            bootstrap.append(sum(map(sum, sampled))/sum(map(len, sampled)))
        bootstrap.sort()
    return {"before": candidates[before_key]["spec"], "before_key": before_key,
            "after": candidates[after_key]["spec"], "after_key": after_key,
            "matched_fixtures": count, "seed_clusters": len(clusters),
            "before_unmatched": len(old.keys() - common), "after_unmatched": len(new.keys() - common),
            "complete_fixture_match": old.keys() == new.keys(),
            "points_per_match_change": total/count,
            "seed_bootstrap95": [bootstrap[125], bootstrap[4874]] if bootstrap else None,
            "by_opponent": {key: {"matched_fixtures": len(values), "points_per_match_change": statistics.mean(values)}
                            for key, values in opponent_values.items()},
            "note": "Paired seed bootstrap preserves opponent/side/kickoff dependence. Partial reports are descriptive; unmatched fixtures are disclosed."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", help="One or more unified .json or in-progress .jsonl reports")
    parser.add_argument("--before", help="Candidate specification, parent-folder name or source hash prefix")
    parser.add_argument("--after")
    parser.add_argument("--output", help="Write table metrics/comparison JSON; refuses overwrite")
    args = parser.parse_args()
    if bool(args.before) != bool(args.after):
        parser.error("Provide --before and --after together")
    rows, metadata = [], []
    for path in args.reports:
        data, meta = load(path)
        rows.extend(data)
        metadata.append({"path": path, **meta})
    candidates = candidate_map(rows)
    summaries = compact_table(candidates)
    result = {"reports": metadata, "summaries": summaries}
    if args.before:
        if any(meta.get("complete") and meta.get("valid_protocol") is not True for meta in metadata):
            raise ValueError("Completed report failed protocol; refusing competitive comparison")
        result["comparison"] = paired(candidates, args.before, args.after)
        print(json.dumps(result["comparison"], indent=2))
    if args.output:
        with Path(args.output).open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2)


if __name__ == "__main__":
    main()
