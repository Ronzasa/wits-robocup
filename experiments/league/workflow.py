"""Predeclared selection, immutable release lock and fresh league holdout.

Only selection and holdout stages play matches. Every result label is exclusive;
an interrupted or mismatched run is retained and requires manual investigation.
"""
import argparse
import ast
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import analyse
import bench


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PLAN = HERE / "workflow-plan.json"
LOCK = HERE / "selection-lock.json"
RELEASE = ROOT / "league-team/team.py"
REPORT = HERE / "FINAL_REPORT.json"
README = HERE / "README.md"
PLAN_REVISION = 1
NEW_TEAMS = [f"experiments/league/{name}/team.py" for name in
             ("gaps2", "guardian", "pressure_cover", "ray_cover", "adaptive3")]
MONSTER = "experiments/red-team/monster/team.py"
TITAN = "my-team/team.py"
BASELINES = ["balanced", "tactical", "possession", "structured_attack", "man_marking", "ball_chaser"]
OPPONENTS = BASELINES + [TITAN, MONSTER,
    "experiments/red-team/blue-pool/blue-c-combined/team.py",
    "experiments/red-team/pool/v21-close-outlet/team.py",
    "experiments/league/opponents/pressure/team.py",
    "experiments/league/opponents/counter/team.py",
    "experiments/league/opponents/gap_press2/team.py"]
SELECTION = [("league-selection-custom", "custom", 820000, 820002),
             ("league-selection-default", "default", 820002, 820004)]
HOLDOUT = [("league-holdout-default", "default", 830000, 830005),
           ("league-holdout-custom", "custom", 830005, 830010)]


def fixture_count(schedules, formation=None):
    return len(OPPONENTS)*4*sum(end-start for _, mode, start, end in schedules
                               if formation is None or mode == formation)


def seed_count(schedules):
    return len({seed for _, _, start, end in schedules for seed in range(start, end)})


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_exclusive(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def source_manifest(spec):
    if spec in BASELINES:
        if spec not in bench.baseline_names():
            raise RuntimeError("Required official baseline unavailable: "+spec)
        return {"spec": spec, "sha256": None, "key": "baseline:"+spec}
    path = ROOT / spec
    sha = bench.digest(path)
    return {"spec": spec, "sha256": sha, "key": "source:"+sha}


def plan_model():
    return {"protocol_version": PLAN_REVISION, "candidates": [source_manifest(spec) for spec in NEW_TEAMS+[MONSTER]],
            "opponents": [source_manifest(spec) for spec in OPPONENTS],
            "infrastructure_sha256": bench.infrastructure(),
            "engine_version": bench._engine.ENGINE_VERSION, "config_hash": bench.CONFIG_HASH,
            "selection_schedule": SELECTION, "holdout_schedule": HOLDOUT,
            "selection_rule": "Highest points among new legal, zero-error, zero-forfeit candidates; then goal difference, then lower mean decision time. Monster remains the fixed control.",
            "protocol": {"ticks": 2400, "players": 5, "timeout_ms": 20,
                         "fixtures_per_seed_opponent": 4, "workers": 1},
            "holdout_matches_per_policy": fixture_count(HOLDOUT), "holdout_seed_clusters": seed_count(HOLDOUT)}


def ensure_plan(create=False):
    current = json.loads(json.dumps(plan_model()))
    if not PLAN.exists():
        if not create:
            raise RuntimeError("Selection plan has not been written")
        if any((HERE/"results"/(label+suffix)).exists()
               for label, _, _, _ in SELECTION+HOLDOUT for suffix in (".json", ".jsonl")):
            raise RuntimeError("Cannot create a predeclared plan after scheduled results exist")
        write_exclusive(PLAN, {"created_utc": utc_now(), "model": current})
        print("Wrote full-source selection plan before the first fixture: "+str(PLAN), flush=True)
    plan = read_json(PLAN)
    if plan["model"] != current:
        raise RuntimeError("A planned source, opponent, infrastructure file or protocol changed")
    return plan


def fixture_key(row):
    return (row["candidate_key"], row["opponent_key"], row["seed"],
            row["candidate_side"], row["kickoff_team"], row.get("formation", "custom"))


def verify_report(path, schedule, candidates, model):
    report = read_json(path)
    label, formation, start, end = schedule
    if not all(report.get(key) is True for key in
               ("complete", "valid_protocol", "infrastructure_unchanged", "source_snapshots_unchanged")):
        raise RuntimeError("Existing report is incomplete or failed protocol: "+str(path))
    if report.get("label") != label or report.get("seeds_exclusive") != [start, end]:
        raise RuntimeError("Existing report label or seeds differ: "+str(path))
    expected_protocol = dict(model["protocol"], formation=formation)
    if report.get("protocol") != expected_protocol:
        raise RuntimeError("Existing report protocol differs: "+str(path))
    if (report.get("engine_version") != model["engine_version"]
            or report.get("config_hash") != model["config_hash"]
            or report.get("infrastructure_sha256") != model["infrastructure_sha256"]):
        raise RuntimeError("Existing report uses different official infrastructure")
    for field, expected in (("teams", candidates), ("opponents", model["opponents"])):
        actual = [{key: item[key] for key in ("spec", "sha256", "key")} for item in report[field]]
        if actual != expected:
            raise RuntimeError("Existing report source manifests differ: "+field)
        for item in report[field]:
            if item["sha256"] is not None and bench.digest(item["runtime_spec"]) != item["sha256"]:
                raise RuntimeError("Archived runtime source changed: "+item["runtime_spec"])
    expected_keys = {(candidate["key"], opponent["key"], seed, side, kickoff, formation)
                     for candidate in candidates for opponent in model["opponents"]
                     for seed in range(start, end) for side in (0, 1) for kickoff in (0, 1)}
    keys = [fixture_key(row) for row in report["results"]]
    if len(keys) != len(set(keys)) or set(keys) != expected_keys:
        raise RuntimeError("Report fixtures are duplicated, missing or mismatched: "+str(path))
    expected_specs = {item["key"]: item["spec"] for item in candidates}
    opponent_specs = {item["key"]: item["spec"] for item in model["opponents"]}
    for row in report["results"]:
        if (row.get("protocol_issues") or bench.check_row(row) or row.get("score") is None
                or row.get("candidate_spec") != expected_specs[row["candidate_key"]]
                or row.get("opponent_spec") != opponent_specs[row["opponent_key"]]
                or row["score"] != bench.score(row)):
            raise RuntimeError("Invalid fixture or unadjudicated forfeit in "+str(path))
    raw = Path(path).with_suffix(".jsonl")
    if not raw.exists() or [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()
                            if line.strip()] != report["results"]:
        raise RuntimeError("Raw evidence differs from completed report: "+str(path))
    return report


def run_schedule(schedule, candidates, model):
    # Recheck every planned original before each formation arm.
    ensure_plan()
    for item in candidates:
        if source_manifest(item["spec"]) != item:
            raise RuntimeError("Candidate changed before scheduled run: "+item["spec"])
    label, formation, start, end = schedule
    target = HERE/"results"/(label+".json")
    raw = target.with_suffix(".jsonl")
    if target.exists():
        report = verify_report(target, schedule, candidates, model)
        print("Reusing verified completed report: "+str(target), flush=True)
        return report
    if raw.exists():
        raise RuntimeError("Interrupted raw evidence exists; refusing to rerun or overwrite: "+str(raw))
    command = [sys.executable, str(HERE/"bench.py"), "--teams", *[item["spec"] for item in candidates],
               "--opponents", *OPPONENTS, "--start", str(start), "--end", str(end),
               "--formation", formation, "--label", label]
    subprocess.run(command, cwd=str(ROOT), check=True)
    ensure_plan()
    return verify_report(target, schedule, candidates, model)


def selection():
    model = ensure_plan(create=True)["model"]
    for schedule in SELECTION:
        run_schedule(schedule, model["candidates"], model)
    print("Both selection formation arms completed and verified.", flush=True)


def scheduled_reports(schedules, candidates, model):
    return [verify_report(HERE/"results"/(schedule[0]+".json"), schedule, candidates, model)
            for schedule in schedules]


def metadata_release(source_bytes, name, version):
    """Replace only two literal values in the direct submission class."""
    source = source_bytes.decode("utf-8")
    tree = ast.parse(source)
    controllers = [node for node in tree.body if isinstance(node, ast.ClassDef)
                   and any(isinstance(base, ast.Name) and base.id == "TeamController" for base in node.bases)]
    if len(controllers) != 1:
        raise RuntimeError("Expected exactly one direct TeamController entry class")
    offsets, total = [], 0
    for line in source_bytes.splitlines(keepends=True):
        offsets.append(total)
        total += len(line)
    edits = []
    for field, replacement in (("name", name), ("version", version)):
        assignments = [node for node in controllers[0].body if isinstance(node, ast.Assign)
                       and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                       and node.targets[0].id == field]
        if len(assignments) != 1 or not isinstance(assignments[0].value, ast.Constant):
            raise RuntimeError("Expected one literal controller "+field+" assignment")
        value = assignments[0].value
        start = offsets[value.lineno-1]+value.col_offset
        end = offsets[value.end_lineno-1]+value.end_col_offset
        edits.append((start, end, json.dumps(replacement).encode("utf-8")))
    result = source_bytes
    for start, end, replacement in sorted(edits, reverse=True):
        result = result[:start]+replacement+result[end:]
    # Compare executable ASTs with only the two metadata literals neutralized.
    def neutralized(contents):
        parsed = ast.parse(contents.decode("utf-8"))
        controller = next(node for node in parsed.body if isinstance(node, ast.ClassDef)
                          and node.name == controllers[0].name)
        for node in controller.body:
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
                    and target.id in ("name", "version") for target in node.targets):
                node.value = ast.Constant(value=None)
        return ast.dump(parsed, include_attributes=False)
    if neutralized(result) != neutralized(source_bytes) or len(result) >= 256*1024:
        raise RuntimeError("Release changed executable logic or exceeds the source size limit")
    return result


def load_lock():
    ensure_plan()
    if not LOCK.exists():
        raise RuntimeError("The selected release must be SHA-locked before holdout")
    locked = read_json(LOCK)
    if locked["plan_sha256"] != bench.digest(PLAN):
        raise RuntimeError("The predeclared selection plan changed after locking")
    if bench.digest(ROOT/locked["selected"]["spec"]) != locked["selected"]["sha256"]:
        raise RuntimeError("Selected original source changed after locking")
    if not RELEASE.exists() or bench.digest(RELEASE) != locked["release"]["sha256"]:
        raise RuntimeError("The locked release changed or is missing")
    for relative, expected in locked["selection_reports_sha256"].items():
        if bench.digest(ROOT/relative) != expected:
            raise RuntimeError("Locked selection evidence changed: "+relative)
    return locked


STRUCTURAL_ACTION_COUNTERS = ("missing_actions", "non_finite_values", "invalid_player_ids")


def eligible_metrics(metrics):
    # The SDK counts unavailable kicks as physics outcomes, not invalid
    # payloads. Clamps are normalization; dropped debug payloads are warnings.
    # This experiment retains its stronger requirement to supply every action.
    return not (metrics["policy_errors"] or metrics["forfeits"]
                or metrics["platform_errors"] or metrics["protocol_failures"]
                or any(metrics["validation"].get(key, 0) for key in STRUCTURAL_ACTION_COUNTERS))


def lock_release():
    model = ensure_plan()["model"]
    if LOCK.exists():
        load_lock()
        print("Existing release lock verified; no reselection: "+str(LOCK), flush=True)
        return
    if any((HERE/"results"/(label+suffix)).exists()
           for label, _, _, _ in HOLDOUT for suffix in (".json", ".jsonl")):
        raise RuntimeError("Cannot select or lock after holdout evidence exists")
    reports = scheduled_reports(SELECTION, model["candidates"], model)
    rows = [row for report in reports for row in report["results"]]
    candidates = analyse.candidate_map(rows)
    rankings = []
    for item in model["candidates"]:
        metrics = analyse.metrics(candidates[item["key"]]["rows"])
        metrics["goal_difference"] = metrics["goals"][0]-metrics["goals"][1]
        eligible = eligible_metrics(metrics)
        rankings.append({**item, "metrics": metrics, "eligible": eligible,
                         "new_candidate": item["spec"] in NEW_TEAMS})
    eligible_new = [item for item in rankings if item["eligible"] and item["new_candidate"]]
    if not eligible_new:
        raise RuntimeError("No new candidate meets zero-error, zero-forfeit and legal-action requirements")
    eligible_new.sort(key=lambda item: (-item["metrics"]["points"], -item["metrics"]["goal_difference"],
                       item["metrics"]["mean_ms"] if item["metrics"]["mean_ms"] is not None else float("inf"), item["spec"]))
    selected = eligible_new[0]
    control = next(item for item in rankings if item["spec"] == MONSTER)
    comparison = analyse.paired(candidates, MONSTER, selected["spec"])
    release_name = "MONSTER LEAGUE"
    release_version = "league-v1-"+selected["sha256"][:12]
    release_bytes = metadata_release((ROOT/selected["spec"]).read_bytes(), release_name, release_version)
    release_sha = hashlib.sha256(release_bytes).hexdigest()
    RELEASE.parent.mkdir(parents=True, exist_ok=True)
    if RELEASE.exists():
        if RELEASE.read_bytes() != release_bytes:
            raise RuntimeError("Existing league-team/team.py differs; refusing to overwrite")
    else:
        with RELEASE.open("xb") as stream:
            stream.write(release_bytes)
    # The official loader checks entry-class discovery after packaging.
    controller = bench.load_controller(str(RELEASE))
    if controller.name != release_name or controller.version != release_version:
        raise RuntimeError("Release metadata or entry-class discovery failed")
    locked = {"locked_utc": utc_now(), "plan_sha256": bench.digest(PLAN),
              "selection_reports_sha256": {str((HERE/"results"/(stage[0]+".json")).relative_to(ROOT)):
                  bench.digest(HERE/"results"/(stage[0]+".json")) for stage in SELECTION},
              "selected": {key: selected[key] for key in ("spec", "sha256", "key")},
              "release": {"spec": "league-team/team.py", "sha256": release_sha,
                          "key": "source:"+release_sha, "name": release_name, "version": release_version,
                          "metadata_only_change": True},
              "selection_ranking": rankings, "selected_metrics": selected["metrics"],
              "structural_action_counter_gate": list(STRUCTURAL_ACTION_COUNTERS),
              "unavailable_kicks": "rejected_kicks retained as a physics outcome, not a structural-action disqualification; see SDK actions.py and validate.py",
              "control_metrics": control["metrics"], "selected_vs_control": comparison,
              "selected_beat_control_on_points": selected["metrics"]["points"] > control["metrics"]["points"],
              "note": "Highest eligible NEW candidate selected by the fixed rule; this does not imply it beat Monster. Fresh holdout decides the practical comparison. Timeouts remain included."}
    write_exclusive(LOCK, locked)
    print(json.dumps({"locked": str(LOCK), "selected": selected["spec"], "release_sha256": release_sha,
                      "selected_points": selected["metrics"]["points"], "control_points": control["metrics"]["points"],
                      "selected_beat_control_on_points": locked["selected_beat_control_on_points"]}), flush=True)


def holdout_candidates(model, locked):
    by_spec = {item["spec"]: item for item in model["opponents"]}
    return [{key: locked["release"][key] for key in ("spec", "sha256", "key")}, by_spec[TITAN], by_spec[MONSTER]]


def holdout():
    model = ensure_plan()["model"]
    locked = load_lock()
    candidates = holdout_candidates(model, locked)
    for schedule in HOLDOUT:
        load_lock()
        run_schedule(schedule, candidates, model)
        load_lock()
    print(f"Fresh holdout complete: {fixture_count(HOLDOUT)} fixtures per policy across {seed_count(HOLDOUT)} seed clusters.", flush=True)


def format_metric(value, places=4):
    return "n/a" if value is None else f"{value:.{places}f}"


def final_report():
    model = ensure_plan()["model"]
    locked = load_lock()
    policies = holdout_candidates(model, locked)
    reports = scheduled_reports(HOLDOUT, policies, model)
    rows = [row for report in reports for row in report["results"]]
    candidates = analyse.candidate_map(rows)
    summaries, modes, opponents = [], [], []
    holdout_count, holdout_seeds = fixture_count(HOLDOUT), seed_count(HOLDOUT)
    per_opponent_count = 4*sum(end-start for _, _, start, end in HOLDOUT)
    mode_counts = {mode: fixture_count(HOLDOUT, mode) for mode in ("custom", "default")}
    selection_count = fixture_count(SELECTION)
    expected_identity = None
    for policy in policies:
        policy_rows = candidates[policy["key"]]["rows"]
        identity = {(row["opponent_key"], row["seed"], row["candidate_side"], row["kickoff_team"], row["formation"])
                    for row in policy_rows}
        if (len(policy_rows) != holdout_count or len(identity) != holdout_count
                or len({row["seed"] for row in policy_rows}) != holdout_seeds):
            raise RuntimeError(f"Final policy requires {holdout_count} unique fixtures and {holdout_seeds} seed clusters")
        if expected_identity is not None and identity != expected_identity:
            raise RuntimeError("Final policy fixtures are not completely aligned")
        expected_identity = identity
        summaries.append({**policy, **analyse.metrics(policy_rows)})
        for mode in ("custom", "default"):
            subset = [row for row in policy_rows if row["formation"] == mode]
            if len(subset) != mode_counts[mode]:
                raise RuntimeError(f"Formation {mode} requires {mode_counts[mode]} fixtures per policy")
            modes.append({"candidate_key": policy["key"], "spec": policy["spec"], "formation": mode,
                          **analyse.metrics(subset)})
        for opponent in model["opponents"]:
            subset = [row for row in policy_rows if row["opponent_key"] == opponent["key"]]
            if len(subset) != per_opponent_count:
                raise RuntimeError(f"Each opponent requires {per_opponent_count} fixtures per policy")
            opponents.append({"candidate_key": policy["key"], "spec": policy["spec"],
                              "opponent": opponent["spec"], "opponent_key": opponent["key"],
                              **analyse.metrics(subset)})
    comparisons = [analyse.paired(candidates, control, "league-team/team.py") for control in (TITAN, MONSTER)]
    if any(not item["complete_fixture_match"] or item["matched_fixtures"] != holdout_count
           or item["seed_clusters"] != holdout_seeds for item in comparisons):
        raise RuntimeError("Final paired comparison is incomplete")
    # Secondary descriptive view: remove the native reference opponents while
    # preserving all fixtures against every source-defined tactical opponent.
    source_keys = {item["key"] for item in model["opponents"] if item["key"].startswith("source:")}
    source_count = len(source_keys)*per_opponent_count
    source_candidates = analyse.candidate_map([row for row in rows if row["opponent_key"] in source_keys])
    source_summaries = []
    for policy in policies:
        subset = source_candidates[policy["key"]]["rows"]
        if len(subset) != source_count or len({row["seed"] for row in subset}) != holdout_seeds:
            raise RuntimeError("Secondary source-defined pool has incomplete fixtures or seed clusters")
        metrics = analyse.metrics(subset)
        source_summaries.append({**policy, **metrics,
                                 "win_rate": metrics["wdl"][0]/metrics["scored_matches"]})
    source_comparisons = [analyse.paired(source_candidates, control, "league-team/team.py")
                          for control in (TITAN, MONSTER)]
    if any(not item["complete_fixture_match"] or item["matched_fixtures"] != source_count
           or item["seed_clusters"] != holdout_seeds for item in source_comparisons):
        raise RuntimeError("Secondary source-defined pool comparison is incomplete")
    source_pool = {"scope": "Secondary local source-defined tactical pool; excludes native baselines and is not the actual school field.",
                   "opponent_count": len(source_keys), "matches_per_policy": source_count,
                   "seed_clusters": holdout_seeds,
                   "opponents": [item for item in model["opponents"] if item["key"] in source_keys],
                   "summaries": source_summaries, "paired_comparisons": source_comparisons,
                   "note": "Descriptive secondary analysis only; the original full-pool primary result and selection criterion remain unchanged. All faults and matched source-opponent fixtures are retained."}
    evidence = {str((HERE/"results"/(stage[0]+".json")).relative_to(ROOT)):
                bench.digest(HERE/"results"/(stage[0]+".json")) for stage in HOLDOUT}
    result = {"scope": f"Local {len(OPPONENTS)}-opponent pool; school leaderboard dominance is unverified.",
              "selection_lock_sha256": bench.digest(LOCK), "holdout_reports_sha256": evidence,
              "release": locked["release"], "selected_source": locked["selected"],
              "selection_selected_metrics": locked["selected_metrics"],
              "selection_control_metrics": locked["control_metrics"],
              "selection_selected_beat_control": locked["selected_beat_control_on_points"],
              "protocol": {**model["protocol"], "matches_per_policy": holdout_count, "seed_clusters": holdout_seeds,
                           "opponents": len(OPPONENTS), "matches_per_mode": mode_counts},
              "summaries": summaries, "by_formation": modes, "by_opponent": opponents,
              "paired_comparisons": comparisons,
              "secondary_source_defined_pool": source_pool,
              "note": f"All fixtures retained, including policy faults. Forfeits adjudicated 0-3. Confidence intervals resample {holdout_seeds} paired seed clusters; they do not establish performance against the unknown student cohort."}
    labels = {"league-team/team.py": "Release", TITAN: "Titan", MONSTER: "Monster v51"}
    lines = ["# League validation", "",
        "The selected standalone submission is [league-team/team.py](../../league-team/team.py). "
        +"Its playing logic matches `"+locked["selected"]["spec"]+"`; packaging changed only controller name/version metadata.", "",
        "Selection: the new candidate earned "+str(locked["selected_metrics"]["points"])
        +" points versus Monster's "+str(locked["control_metrics"]["points"])+f" across {selection_count} fixtures per policy. "
        +("It beat the control on selection points." if locked["selected_beat_control_on_points"] else
          "The fixed rule selected the strongest eligible new candidate; it did not beat the control on selection points."), "",
        f"Fresh holdout used {len(OPPONENTS)} fixed opponents, {holdout_count} fixtures per policy and {holdout_seeds} previously untouched seed clusters. "
        "Half used custom kickoff formations and half used the engine's default formations. Both sides and kickoff owners were crossed; "
        "the original engine/config, 2,400 ticks and 20 ms deadlines were retained.", "",
        "| Policy | W/D/L | Points | GF/GA | Mean/max decision ms | Errors/timeouts | Forfeits |",
        "|---|---|---:|---|---|---|---:|"]
    for item in summaries:
        lines.append(f"| {labels[item['spec']]} | {'/'.join(map(str,item['wdl']))} | {item['points']} | "
                     f"{'/'.join(map(str,item['goals']))} | {format_metric(item['mean_ms'])}/{format_metric(item['max_ms'],3)} | "
                     f"{item['policy_errors']}/{item['policy_timeouts']} | {item['forfeits']} |")
    lines += ["", "Paired changes in points per match for the release, with 95% seed-cluster bootstrap intervals:", ""]
    for comparison in comparisons:
        low, high = comparison["seed_bootstrap95"]
        lines.append(f"- Versus {labels[comparison['before']]}: {comparison['points_per_match_change']:+.3f} "
                     f"[{low:+.3f}, {high:+.3f}] across all {holdout_count} matched fixtures.")
    lines += ["", f"The secondary comparison excludes the {len(model['opponents'])-len(source_keys)} native baselines. "
              f"Its {len(source_keys)} source-defined tactical opponents give {source_count} fixtures per policy over "
              f"the same {holdout_seeds} seed clusters. This local stress pool is not the actual school field.", "",
              "| Policy | Source-pool W/D/L | Points | Win rate | GF/GA |",
              "|---|---|---:|---:|---|"]
    for item in source_summaries:
        lines.append(f"| {labels[item['spec']]} | {'/'.join(map(str,item['wdl']))} | {item['points']} | "
                     f"{item['win_rate']:.1%} | {'/'.join(map(str,item['goals']))} |")
    lines += ["", "Secondary paired changes in release points per match, with 95% seed-cluster intervals:", ""]
    for comparison in source_comparisons:
        low, high = comparison["seed_bootstrap95"]
        lines.append(f"- Versus {labels[comparison['before']]}: {comparison['points_per_match_change']:+.3f} "
                     f"[{low:+.3f}, {high:+.3f}] across {source_count} matched source-opponent fixtures.")
    lines += ["", "| Formation | Release points | Titan points | Monster points |",
              "|---|---:|---:|---:|"]
    for mode in ("custom", "default"):
        values = [next(item["points"] for item in modes if item["spec"] == policy["spec"] and item["formation"] == mode)
                  for policy in policies]
        lines.append("| "+mode+" | "+" | ".join(map(str,values))+" |")
    lines += ["", f"Each opponent row contains {per_opponent_count} fixtures per policy:", "",
              "| Opponent | Release points | Titan points | Monster points |", "|---|---:|---:|---:|"]
    for opponent in model["opponents"]:
        values = [next(item["points"] for item in opponents if item["spec"] == policy["spec"]
                       and item["opponent_key"] == opponent["key"]) for policy in policies]
        label = opponent["spec"] if opponent["sha256"] is None else Path(opponent["spec"]).parent.name
        lines.append("| "+label+" | "+" | ".join(map(str,values))+" |")
    lines += ["", "All fixtures and decision faults remain included; forfeits are scored 0-3. "
              "Unavailable kick attempts remain in the full validation counters and do not invalidate a legal action payload. "
              "Full source hashes, action validity, per-mode/per-opponent metrics and comparisons are in "
              f"[{REPORT.name}]({REPORT.name}), with the pre-holdout decision in [{LOCK.name}]({LOCK.name}).", "",
              "This is evidence against a local tactical pool. School leaderboard dominance remains unverified; "
              "the student cohort, server scheduling and future submissions can differ. Original Titan, Monster and archived experiments remain preserved.", ""]
    markdown = "\n".join(lines)
    result["readme_sha256"] = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    if REPORT.exists() and read_json(REPORT) != result:
        raise RuntimeError("Existing final report differs; refusing to overwrite")
    if README.exists() and README.read_text(encoding="utf-8") != markdown:
        raise RuntimeError("Existing README differs; refusing to overwrite")
    if not REPORT.exists():
        write_exclusive(REPORT, result)
    if not README.exists():
        with README.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(markdown)
    print(json.dumps({"report": str(REPORT), "readme": str(README),
                      "summaries": [{"policy": item["spec"], "points": item["points"], "wdl": item["wdl"]}
                                    for item in summaries], "comparisons": comparisons}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("selection", "lock", "holdout", "report"), required=True)
    args = parser.parse_args()
    stages = {"selection": selection, "lock": lock_release, "holdout": holdout, "report": final_report}
    stages[args.stage]()


if __name__ == "__main__":
    main()
