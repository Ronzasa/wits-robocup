"""Compare two benchmark outputs on identical side/kickoff/seed fixtures."""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path
import random

from benchmark import aggregate, candidate_score, points


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline", type=Path)
    p.add_argument("challenger", type=Path)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        p.error("Comparison output exists; preserve it and use another filename")
    def read(root):
        rows = [json.loads(line) for line in (root / "matches.jsonl").read_text().splitlines()]
        if len(rows) != len({r["fixture_id"] for r in rows}):
            raise ValueError("Duplicate fixture IDs")
        return {r["fixture_id"]: r for r in rows}
    base = read(args.baseline)
    candidate = read(args.challenger)
    if not candidate or not set(candidate).issubset(base):
        raise ValueError("Challenger does not have a corresponding baseline for each fixture")
    keys = sorted(candidate)
    paired = [(base[k], candidate[k]) for k in keys]
    for before, after in paired:
        for field in ("split", "opponent", "seed", "candidate_slot", "candidate_takes_kickoff"):
            if before[field] != after[field]:
                raise ValueError("Mismatched fixture metadata")
        for field in ("engine_version", "config_hash", "ticks", "kickoff_team"):
            if before["result"][field] != after["result"][field]:
                raise ValueError("Mismatched engine/rules")
    blocks = defaultdict(list)
    for before, after in paired:
        blocks[before["seed"]].append(points(after) - points(before))
    means = [sum(v) / len(v) for v in blocks.values()]
    rng = random.Random(719331)
    boot = sorted(sum(rng.choices(means, k=len(means))) / len(means) for _ in range(5000))
    baseline = aggregate([b for b, _ in paired])
    challenger = aggregate([a for _, a in paired])
    report = {
        "baseline_path": str(args.baseline),
        "challenger_path": str(args.challenger),
        "paired_fixtures": len(paired),
        "independent_seed_blocks": len(blocks),
        "splits": sorted({a["split"] for _, a in paired}),
        "points_per_match_difference": challenger["points_per_match"] - baseline["points_per_match"],
        "paired_seed_block_bootstrap_95": [boot[125], boot[4874]],
        "goal_difference_per_match_change": challenger["goal_difference_per_match"] - baseline["goal_difference_per_match"],
        "goals_scored_change": challenger["goals_for"] - baseline["goals_for"],
        "goals_conceded_change": challenger["goals_against"] - baseline["goals_against"],
        "fixtures_with_more_points": sum(points(a) > points(b) for b, a in paired),
        "fixtures_with_same_points": sum(points(a) == points(b) for b, a in paired),
        "fixtures_with_fewer_points": sum(points(a) < points(b) for b, a in paired),
        "baseline": baseline, "challenger": challenger,
        "by_opponent": {},
        "scope": "Local seed variability over these fixed opponents; not a probability of winning the class competition.",
    }
    for opponent in sorted({a["opponent"] for _, a in paired}):
        sub = [(b, a) for b, a in paired if a["opponent"] == opponent]
        s0 = aggregate([b for b, _ in sub]); s1 = aggregate([a for _, a in sub])
        report["by_opponent"][opponent] = {
            "baseline": s0, "challenger": s1,
            "points_per_match_difference": s1["points_per_match"] - s0["points_per_match"],
        }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print("Matched fixtures:", report["paired_fixtures"])
    print("Points/match: {:.3f} -> {:.3f}; delta {:+.3f}; paired 95% interval {}".format(
        baseline["points_per_match"], challenger["points_per_match"],
        report["points_per_match_difference"], report["paired_seed_block_bootstrap_95"],
    ))
    print("Goals:", str(baseline["goals_for"]) + "-" + str(baseline["goals_against"]),
          "->", str(challenger["goals_for"]) + "-" + str(challenger["goals_against"]))
    print("Errors/timeouts:", challenger["policy_errors"], challenger["policy_timeouts"])
    print("Per-opponent point differences:", {k: v["points_per_match_difference"] for k, v in report["by_opponent"].items()})


if __name__ == "__main__":
    main()
