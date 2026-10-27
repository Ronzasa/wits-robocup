"""Sequential league benchmark using only the unchanged public simulator.

Each seed crosses absolute side and kickoff owner. Sources are content-addressed
before play; JSONL retains each fixture immediately, including failures. A run
label is exclusive and cannot overwrite earlier evidence.
"""
import argparse
import hashlib
import json
import random
import re
import statistics
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONFIG_HASH = "372990895c7eca2a"
CONFIG = ROOT / "configs/default.toml"
sys.path.insert(0, str(ROOT))
import bootstrap
bootstrap.ensure_engine(ROOT)
from soccer import _engine
from soccer import TeamController
from soccer.helpers import load_controller
from soccer.runner import baseline_names, play_match, summarise_results


class DefaultFormation(TeamController):
    """Diagnostic server-style starts; policy observations/actions unchanged."""
    def __init__(self, spec):
        self.inner = load_controller(spec)
        self.name, self.version = self.inner.name, self.inner.version

    def initial_formation(self, field):
        return None

    def reset(self, seed):
        self.inner.reset(seed)

    def act(self, obs):
        return self.inner.act(obs)

    def on_match_end(self, result):
        self.inner.on_match_end(result)


def runtime_team(spec, formation):
    if formation == "default" and spec not in baseline_names():
        return DefaultFormation(spec)
    return spec


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def infrastructure():
    paths = [CONFIG]
    paths += sorted((ROOT / "student-sdk/soccer").glob("*.py"))
    paths += sorted((ROOT / "engine" / bootstrap.platform_slot()).glob("*"))
    return {str(p.relative_to(ROOT)): digest(p) for p in paths if p.is_file()}


def freeze(spec, allow_baseline):
    if allow_baseline and spec in baseline_names():
        return {"spec": spec, "runtime_spec": spec, "sha256": None,
                "key": "baseline:" + spec}
    source = Path(spec)
    if not source.is_absolute():
        source = ROOT / source
    if source.is_dir():
        source /= "team.py"
    source = source.resolve(strict=True)
    contents = source.read_bytes()
    sha = hashlib.sha256(contents).hexdigest()
    target = HERE / "sources" / sha / "team.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.read_bytes() != contents:
            raise RuntimeError("Immutable source snapshot changed: " + str(target))
    else:
        with target.open("xb") as stream:
            stream.write(contents)
    # Load before scheduling, so a misspelled specification fails early.
    controller = load_controller(str(target))
    return {"spec": spec, "runtime_spec": str(target), "sha256": sha,
            "name": controller.name, "version": controller.version,
            "key": "source:" + sha}


def score(row):
    reason = row.get("terminal_reason")
    if isinstance(reason, dict) and "forfeit" in reason:
        return [0, 3] if reason["forfeit"]["team"] == row["candidate_side"] else [3, 0]
    return row["score"]


def points(row):
    a, b = score(row)
    return 3 if a > b else int(a == b)


def summarise(rows):
    # Failed platform calls have no fabricated score and cannot earn a draw.
    # Preserve raw evidence, including legacy reports that retained a leading
    # on-field score after the candidate forfeited. All summary metrics must
    # use the same adjudication as league points.
    scored = [dict(r, score=score(r), goal_difference=score(r)[0]-score(r)[1])
              for r in rows if r.get("score") is not None]
    result = summarise_results(scored)
    result.pop("goal_difference_ci95", None)  # Fixtures share seed clusters.
    result["scheduled_matches"] = len(rows)
    result["platform_errors"] = sum(bool(r.get("platform_error")) for r in rows)
    result["protocol_failures"] = sum(bool(r["protocol_issues"]) for r in rows)
    result["complete_matches"] = sum(r.get("ticks") == 2400 for r in rows)
    result["forfeits"] = sum("forfeit" in r.get("terminal_reason", "") for r in rows)
    result["league_points"] = sum(points(r) for r in scored)
    result["points_per_match"] = (result["league_points"] / len(rows)) if rows else None
    result["seed_clusters"] = len({r["seed"] for r in rows})
    result["validation"] = []
    for side in (0, 1):
        totals = {}
        for row in scored:
            for key, value in row["stats"][side].get("validation", {}).items():
                totals[key] = totals.get(key, 0) + value
        result["validation"].append(totals)
    result["by_start"] = {}
    for side in (0, 1):
        for kickoff in (0, 1):
            subset = [r for r in scored if r["candidate_side"] == side
                      and r["kickoff_team"] == kickoff]
            result["by_start"][f"side{side}-kickoff{kickoff}"] = {
                "matches": len(subset), "points": sum(points(r) for r in subset),
                "wdl": [sum(r["score"][0] > r["score"][1] for r in subset),
                        sum(r["score"][0] == r["score"][1] for r in subset),
                        sum(r["score"][0] < r["score"][1] for r in subset)],
                "goals": [sum(r["score"][i] for r in subset) for i in (0, 1)]}
    return result


def check_row(row):
    issues = []
    if row.get("platform_error"):
        return ["platform_error"]
    if row.get("engine_version") != _engine.ENGINE_VERSION:
        issues.append("engine_version")
    if row.get("config_hash") != CONFIG_HASH:
        issues.append("config_hash")
    if row.get("ticks") != 2400 and "forfeit" not in row.get("terminal_reason", ""):
        issues.append("incomplete_match")
    if (row.get("ticks") == 2400 and row.get("terminal_reason") != "time_limit"
            and "forfeit" not in row.get("terminal_reason", "")):
        issues.append("unexpected_terminal_reason")
    if len(row.get("stats", [])) != 2:
        issues.append("missing_stats")
    return issues


def run(args):
    if not args.teams or not args.opponents or args.start is None or args.end is None:
        raise ValueError("Provide --teams, --opponents, --start and --end")
    if args.end <= args.start:
        raise ValueError("--end must exceed --start; the upper bound is exclusive")
    if not args.label or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.label):
        raise ValueError("--label must contain only letters, digits, dot, dash or underscore")
    results_dir = HERE / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    target = results_dir / (args.label + ".json")
    raw = target.with_suffix(".jsonl")
    if target.exists() or raw.exists():
        raise FileExistsError("Existing result label; use a fresh --label")
    before = infrastructure()
    archived_manifest = ROOT / "experiments/red-team/protected.json"
    if archived_manifest.exists():
        protected = json.loads(archived_manifest.read_text(encoding="utf-8"))["files"]
        for relative, actual in before.items():
            expected = protected.get(relative)
            if expected is not None and actual != expected:
                raise RuntimeError("Official infrastructure differs from archived hash: " + relative)
    teams = [freeze(spec, False) for spec in args.teams]
    opponents = [freeze(spec, True) for spec in args.opponents]
    if len({team["key"] for team in teams}) != len(teams):
        raise ValueError("Duplicate candidate source hashes")
    if len({team["key"] for team in opponents}) != len(opponents):
        raise ValueError("Duplicate opponent source hashes or baselines")
    report = {"label": args.label, "engine_version": _engine.ENGINE_VERSION,
              "config_hash": CONFIG_HASH, "seeds_exclusive": [args.start, args.end],
              "protocol": {"ticks": 2400, "players": 5, "timeout_ms": 20,
                           "fixtures_per_seed_opponent": 4, "workers": 1,
                           "formation": args.formation},
              "teams": teams, "opponents": opponents, "infrastructure_sha256": before,
              "results": [], "summaries": [], "complete": False}
    started = time.perf_counter()
    with raw.open("x", encoding="utf-8") as stream:
        # Fixture order is explicit and stable; no background competition runs.
        for candidate in teams:
            candidate_rows = []
            per_opponent = []
            for opponent in opponents:
                pair_rows = []
                for seed in range(args.start, args.end):
                    seed_rows = []
                    for side in (0, 1):
                        for kickoff in (0, 1):
                            fixture = f"{args.label}-c{teams.index(candidate)}-o{opponents.index(opponent)}-{seed}-s{side}-k{kickoff}"
                            sides = (runtime_team(candidate["runtime_spec"], args.formation),
                                     runtime_team(opponent["runtime_spec"], args.formation))
                            if side:
                                sides = sides[::-1]
                            replay = None
                            if len(pair_rows) < args.record:
                                replay_dir = HERE / "replays"
                                replay_dir.mkdir(parents=True, exist_ok=True)
                                replay = str(replay_dir / (fixture + ".rep"))
                            try:
                                row = play_match(*sides, seed=seed, kickoff_team=kickoff,
                                                 config_path=str(CONFIG), max_ticks=2400,
                                                 players_per_team=5, per_decision_timeout_ms=20,
                                                 match_id=fixture, record_replay=replay,
                                                 record_debug=bool(replay)).result
                                row["absolute_score"] = list(row["score"])
                                row["absolute_team_ids"] = list(row["team_ids"])
                                row["absolute_outcome"] = row.get("outcome")
                                if side:
                                    for key in ("score", "stats", "team_ids", "team_versions"):
                                        if key in row:
                                            row[key] = list(reversed(row[key]))
                                a, b = row["score"]
                                reason = row.get("terminal_reason")
                                if isinstance(reason, dict) and "forfeit" in reason:
                                    # The engine returns the on-field score at
                                    # stoppage. Course grading adjudicates a
                                    # forfeit 0-3, even if the offender led.
                                    row["on_field_score"] = [a, b]
                                    a, b = (0, 3) if reason["forfeit"]["team"] == side else (3, 0)
                                    row["score"] = [a, b]
                                    row["score_adjudication"] = "course_forfeit_0_3"
                                row["goal_difference"] = a - b
                                row["outcome"] = "candidate_win" if a > b else "opponent_win" if a < b else "draw"
                            except Exception as exc:
                                row = {"match_id": fixture, "score": None, "ticks": 0,
                                       "stats": [{}, {}], "platform_error": f"{type(exc).__name__}: {exc}"}
                            row.update(seed=seed, candidate_side=side, kickoff_team=kickoff,
                                       candidate_kickoff=(side == kickoff), sides_swapped=bool(side),
                                       candidate_key=candidate["key"], opponent_key=opponent["key"],
                                       candidate_spec=candidate["spec"], opponent_spec=opponent["spec"],
                                       formation=args.formation)
                            row["protocol_issues"] = check_row(row)
                            stream.write(json.dumps(row) + "\n")
                            stream.flush()
                            report["results"].append(row)
                            pair_rows.append(row)
                            candidate_rows.append(row)
                            seed_rows.append(row)
                    print(json.dumps({"candidate": candidate["spec"], "opponent": opponent["spec"],
                                      "seed": seed, "scores": [r["score"] for r in seed_rows]}), flush=True)
                per_opponent.append({"opponent_key": opponent["key"], "opponent": opponent["spec"],
                                     "summary": summarise(pair_rows)})
            summary = summarise(candidate_rows)
            report["summaries"].append({"candidate_key": candidate["key"], "candidate": candidate["spec"],
                                        "overall": summary, "by_opponent": per_opponent})
            print(json.dumps({"candidate": candidate["spec"], "points": summary["league_points"],
                              "wdl": [summary["team_a_wins"], summary["draws"], summary["team_b_wins"]],
                              "goals": summary["goals"], "timing": summary["team_stats"][0]}), flush=True)
    after = infrastructure()
    report["infrastructure_unchanged"] = before == after
    report["source_snapshots_unchanged"] = all(
        item["sha256"] is None or digest(item["runtime_spec"]) == item["sha256"]
        for item in teams + opponents)
    report["wall_seconds"] = time.perf_counter() - started
    report["complete"] = True
    report["valid_protocol"] = (before == after and report["source_snapshots_unchanged"]
                                and not any(r["protocol_issues"] for r in report["results"]))
    with target.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps({"file": str(target), "valid_protocol": report["valid_protocol"]}), flush=True)
    if not report["valid_protocol"]:
        raise RuntimeError("Protocol failed; all evidence retained in " + str(target))


def compare(paths):
    reports = [json.loads(Path(path).read_text(encoding="utf-8")) for path in paths]
    if any(len(report["teams"]) != 1 for report in reports):
        raise ValueError("--compare requires reports with one candidate each")
    if any(not report.get("complete") or not report.get("valid_protocol") for report in reports):
        raise ValueError("Cannot compare reports with a failed or incomplete protocol")
    key = lambda row: (row["opponent_key"], row["seed"], row["candidate_side"], row["kickoff_team"],
                       row.get("formation", "custom"))
    old, new = [{key(row): row for row in report["results"]} for report in reports]
    if any(len(index) != len(report["results"]) for index, report in zip((old, new), reports)):
        raise ValueError("Duplicate comparison fixture")
    if old.keys() != new.keys():
        raise ValueError("Comparison requires identical opponents, seeds, sides, kickoffs and formations")
    if not old:
        raise ValueError("Comparison requires at least one matched fixture")
    clusters = {}
    for fixture in old:
        clusters.setdefault(fixture[1], []).append(points(new[fixture]) - points(old[fixture]))
    means = [statistics.mean(values) for values in clusters.values()]
    rng = random.Random(917482)
    boots = sorted(statistics.mean(rng.choices(means, k=len(means))) for _ in range(5000))
    result = {"before": paths[0], "after": paths[1], "matches": len(old), "seed_clusters": len(means),
              "points_per_match_change": statistics.mean(means),
              "seed_bootstrap95": [boots[125], boots[4874]] if len(means) > 1 else None,
              "note": "All fixtures retained; seed clusters preserve paired side/kickoff/opponent dependence."}
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teams", nargs="+")
    parser.add_argument("--opponents", nargs="+")
    parser.add_argument("--start", type=int)
    parser.add_argument("--end", type=int)
    parser.add_argument("--label")
    parser.add_argument("--record", type=int, default=0, help="First N fixtures per candidate/opponent")
    parser.add_argument("--formation", choices=("custom", "default"), default="custom",
                        help="Honor initial_formation, or use default starts for both source controllers")
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"))
    args = parser.parse_args()
    if args.record < 0:
        parser.error("--record cannot be negative")
    if args.compare:
        compare(args.compare)
    else:
        run(args)


if __name__ == "__main__":
    main()
