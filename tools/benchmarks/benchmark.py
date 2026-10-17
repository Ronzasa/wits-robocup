"""Reproducible coursework benchmarks using only the official soccer SDK.

Run from the complete student distribution after START.cmd doctor:
    python PATH_TO_TITAN/benchmark.py --repo . --out PATH_TO_TITAN/runs/starter
The output folder must not exist. Raw native records are retained unchanged.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_fixture(fixture):
    from soccer import play_match
    slot = fixture["candidate_slot"]
    teams = [fixture["team"], fixture["opponent"]]
    if slot == 1:
        teams.reverse()
    kickoff = slot if fixture["candidate_takes_kickoff"] else 1 - slot
    match_id = "{}-{}-{}-side{}-kick{}".format(
        fixture["split"], fixture["opponent"], fixture["seed"],
        slot, int(fixture["candidate_takes_kickoff"]),
    )
    result = play_match(
        teams[0], teams[1],
        seed=fixture["seed"],
        kickoff_team=kickoff,
        config_path=fixture["config_path"],
        max_ticks=2400,
        per_decision_timeout_ms=20.0,
        match_id=match_id,
    ).result
    if result["ticks"] != 2400 or result["terminal_reason"] != "time_limit":
        raise RuntimeError("Incomplete fixture: " + match_id + ": " + str(result))
    if result["engine_version"] != "0.1.0" or result["config_hash"] != fixture["config_hash"]:
        raise RuntimeError("Wrong engine/configuration: " + match_id)
    if result["kickoff_team"] != kickoff or result.get("platform_error"):
        raise RuntimeError("Invalid fixture: " + match_id)
    return {
        "fixture_id": match_id,
        "split": fixture["split"],
        "opponent": fixture["opponent"],
        "seed": fixture["seed"],
        "candidate_slot": slot,
        "candidate_takes_kickoff": fixture["candidate_takes_kickoff"],
        "result": result,
    }


def candidate_score(row):
    i = row["candidate_slot"]
    return row["result"]["score"][i], row["result"]["score"][1 - i]


def points(row):
    ours, theirs = candidate_score(row)
    return 3 if ours > theirs else 1 if ours == theirs else 0


def interval(rows):
    blocks = defaultdict(list)
    for row in rows:
        blocks[row["seed"]].append(points(row))
    means = [sum(values) / len(values) for values in blocks.values()]
    if not means:
        return [None, None]
    rng = random.Random(719331)
    samples = sorted(
        sum(rng.choices(means, k=len(means))) / len(means)
        for _ in range(3000)
    )
    return [samples[75], samples[2924]]


def aggregate(rows):
    n = len(rows)
    if not n:
        raise ValueError("Empty group cannot validate a benchmark")
    scores = [candidate_score(row) for row in rows]
    stats = [row["result"]["stats"][row["candidate_slot"]] for row in rows]
    total = lambda key: sum(s.get(key, 0) for s in stats)
    ticks = sum(row["result"]["ticks"] for row in rows)
    attempted = total("passes_attempted")
    completed = total("passes_completed")
    intercepted = total("passes_intercepted")
    decisions = sum(s["decision_time_ms"]["count"] for s in stats)
    decision_time = sum(s["decision_time_ms"]["total_ms"] for s in stats)
    validation = {
        key: sum(s.get("validation", {}).get(key, 0) for s in stats)
        for key in sorted({key for s in stats for key in s.get("validation", {})})
    }
    return {
        "matches": n,
        "independent_seed_blocks": len({r["seed"] for r in rows}),
        "wins": sum(a > b for a, b in scores),
        "draws": sum(a == b for a, b in scores),
        "losses": sum(a < b for a, b in scores),
        "points": sum(points(row) for row in rows),
        "points_per_match": sum(points(row) for row in rows) / n,
        "points_per_match_seed_bootstrap_95": interval(rows),
        "goals_for": sum(a for a, _ in scores),
        "goals_against": sum(b for _, b in scores),
        "goal_difference": sum(a - b for a, b in scores),
        "goal_difference_per_match": sum(a - b for a, b in scores) / n,
        "shots": total("shots"),
        "shots_blocked": total("shots_blocked"),
        "passes_attempted": attempted,
        "passes_completed": completed,
        "passes_intercepted": intercepted,
        "passes_uncollected_derived": attempted - completed - intercepted,
        "pass_completion": completed / attempted if attempted else None,
        "possession_fraction": total("possession_ticks") / ticks,
        "control_fraction": total("controlled_ticks") / ticks,
        "dribbles": total("dribbles"),
        "dribble_distance": total("dribble_distance"),
        "tackles_attempted": total("tackles_attempted"),
        "tackles_won": total("tackles_won"),
        "turnovers": total("turnovers"),
        "fouls": total("fouls"),
        "policy_errors": total("policy_errors"),
        "policy_timeouts": total("policy_timeouts"),
        "decisions": decisions,
        "decision_mean_ms": decision_time / decisions,
        "decision_max_ms": max(s["decision_time_ms"]["max_ms"] for s in stats),
        "validation": validation,
        "shot_quality": "not available",
        "goalkeeper_saves": "not available",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--team", type=Path, default=None)
    parser.add_argument("--protocol", type=Path, default=Path(__file__).with_name("protocol.json"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--splits", nargs="+", choices=("public", "development", "validation", "stress"), default=["public", "development"])
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    repo = args.repo.resolve()
    source = args.team.resolve() if args.team else repo / "my-team/team.py"
    out = args.out.resolve()
    if out.exists():
        parser.error("Output already exists; use a new folder to avoid stale results.")
    if args.workers < 1:
        parser.error("--workers must be positive")
    protocol = json.loads(args.protocol.read_text())
    all_seeds = [s for values in protocol["seeds"].values() for s in values]
    if len(all_seeds) != len(set(all_seeds)):
        parser.error("Seed splits overlap")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(repo / "student-sdk"))
    sys.path.insert(0, str(repo / "tools"))
    import soccer
    from soccer.validate import validate
    from evaluator import submissions
    with soccer.SoccerEnv(config_path=str(repo / "configs/default.toml")) as env:
        if env.engine_version != protocol["engine_version"] or env.config_hash != protocol["config_hash"]:
            raise RuntimeError("The registered protocol does not match this engine/configuration")
        effective_config = env.config()

    original_sha = digest(source)
    out.mkdir(parents=True)
    frozen = out / "team"
    frozen.mkdir()
    shutil.copy2(source, frozen / "team.py")
    spec = str(frozen / "team.py")
    submission = submissions.inspect(source.parent)
    if submission.errors:
        raise RuntimeError("Official folder check failed: " + str(submission.errors))
    report = validate(spec, ticks=400)
    validation_record = {
        "ok": report.ok,
        "controller": report.controller,
        "errors": report.errors,
        "warnings": report.warnings,
        "stats": report.stats,
        "folder_errors": submission.errors,
        "folder_warnings": submission.warnings,
        "static_review_flags": submission.flags,
    }
    (out / "validation.json").write_text(json.dumps(validation_record, indent=2) + "\n")
    if not report.ok or report.stats["decisions"] != 2000:
        raise RuntimeError("Official five-seed validation failed or was incomplete")

    fixtures = []
    for split in args.splits:
        for opponent in protocol["opponents"]:
            for seed in protocol["seeds"][split]:
                for slot in (0, 1):
                    for kickoff in (True, False):
                        fixtures.append({
                            "team": spec, "opponent": opponent, "seed": seed,
                            "candidate_slot": slot, "candidate_takes_kickoff": kickoff,
                            "config_path": str(repo / "configs/default.toml"),
                            "config_hash": protocol["config_hash"], "split": split,
                        })
    metadata = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "repo": str(repo), "source": str(source), "source_sha256": original_sha,
        "frozen_team": spec, "python": sys.version,
        "protocol": protocol, "protocol_sha256": digest(args.protocol),
        "workers": args.workers, "splits": args.splits,
        "expected_fixtures": len(fixtures), "effective_config": effective_config,
        "fixture_note": "All four side/kickoff combinations. Candidate stat slot stored separately; raw native result unchanged.",
    }
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("Official validation passed. Running {} fixtures on {} workers.".format(len(fixtures), args.workers), flush=True)
    rows = []
    counts = Counter()
    with (out / "matches.jsonl").open("w") as handle:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(run_fixture, fixture) for fixture in fixtures]
            for future in as_completed(futures):
                row = future.result()
                rows.append(row)
                handle.write(json.dumps(row) + "\n")
                counts[(row["split"], row["opponent"])] += 1
                target = len(protocol["seeds"][row["split"]]) * 4
                if counts[(row["split"], row["opponent"])] == target:
                    print("{} / {}: {} matches complete".format(row["split"], row["opponent"], target), flush=True)
    rows.sort(key=lambda r: r["fixture_id"])
    if len(rows) != len(fixtures) or len({row["fixture_id"] for row in rows}) != len(fixtures):
        raise RuntimeError("Incomplete/duplicate result set")
    actual = {(r["split"], r["opponent"], r["seed"], r["candidate_slot"], r["candidate_takes_kickoff"]) for r in rows}
    expected = {(f["split"], f["opponent"], f["seed"], f["candidate_slot"], f["candidate_takes_kickoff"]) for f in fixtures}
    if actual != expected:
        raise RuntimeError("Executed fixtures differ from the registered plan")
    if digest(source) != original_sha or digest(frozen / "team.py") != original_sha:
        raise RuntimeError("Source changed during benchmark")
    summary = {"all": aggregate(rows), "by_opponent": {}, "by_split": {}, "by_kickoff": {}, "by_side": {}}
    for opponent in protocol["opponents"]:
        summary["by_opponent"][opponent] = aggregate([r for r in rows if r["opponent"] == opponent])
    for split in args.splits:
        subset = [r for r in rows if r["split"] == split]
        summary["by_split"][split] = {
            "all": aggregate(subset),
            "by_opponent": {
                opponent: aggregate([r for r in subset if r["opponent"] == opponent])
                for opponent in protocol["opponents"]
            },
        }
    for owner in (True, False):
        summary["by_kickoff"][str(owner)] = aggregate([r for r in rows if r["candidate_takes_kickoff"] == owner])
    for side in (0, 1):
        summary["by_side"][str(side)] = aggregate([r for r in rows if r["candidate_slot"] == side])
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    table = [
        "| Opponent | Matches | W-D-L | Points/match | 95% seed-block interval | GF-GA | Mean ms |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for opponent, s in summary["by_opponent"].items():
        low, high = s["points_per_match_seed_bootstrap_95"]
        table.append("| {} | {} | {}-{}-{} | {:.3f} | [{:.3f}, {:.3f}] | {}-{} | {:.4f} |".format(
            opponent, s["matches"], s["wins"], s["draws"], s["losses"],
            s["points_per_match"], low, high, s["goals_for"], s["goals_against"], s["decision_mean_ms"],
        ))
    (out / "table.md").write_text("\n".join(table) + "\n")
    print("\n".join(table), flush=True)
    pooled = summary["all"]
    print("TOTAL: {} matches, {:.3f} points/match, {}-{} goals; {} policy errors, {} timeouts.".format(
        pooled["matches"], pooled["points_per_match"], pooled["goals_for"], pooled["goals_against"],
        pooled["policy_errors"], pooled["policy_timeouts"],
    ), flush=True)
    print("Mean/max decision ms:", pooled["decision_mean_ms"], pooled["decision_max_ms"], flush=True)
    print("Validation counters:", pooled["validation"], flush=True)


if __name__ == "__main__":
    main()
