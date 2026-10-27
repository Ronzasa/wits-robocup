"""Bounded draw-conversion screen, fresh selection and separate release lock.

All original league-team sources, locks and holdout evidence remain unchanged.
Only explicitly requested screen/selection/holdout stages play missing fixtures.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import analyse
import bench
import workflow as w

HERE, ROOT = w.HERE, w.ROOT
BASE = "league-team/team.py"
STRIKER = "league-striker/team.py"
NEW = ["experiments/league/contact_finish/team.py", "experiments/league/siege/team.py",
       "experiments/league/outlet_pivot/team.py"]
SCREEN_OPPONENTS = [w.TITAN, w.MONSTER,
    "experiments/red-team/blue-pool/blue-c-combined/team.py",
    "experiments/red-team/pool/v21-close-outlet/team.py",
    "experiments/league/opponents/counter/team.py", "experiments/league/opponents/open_gap/team.py"]
SCREEN_RUNS = [(("draw-screen-custom", "custom", 840000, 840003), [BASE, NEW[1]]),
               (("draw-contact-custom", "custom", 840000, 840003), [NEW[0]]),
               (("draw-screen-default", "default", 840003, 840005), [BASE, NEW[0], NEW[1]]),
               (("draw-pivot-custom", "custom", 840000, 840003), [NEW[2]]),
               (("draw-pivot-default", "default", 840003, 840005), [NEW[2]])]
SELECTION = [("draw-selection-custom", "custom", 850000, 850001),
             ("draw-selection-default", "default", 850001, 850002)]
HOLDOUT = [("draw-holdout-default", "default", 860000, 860005),
           ("draw-holdout-custom", "custom", 860005, 860010)]
SCREEN_PLAN = HERE/"draw-screen-plan.json"
SCREEN_RESULT = HERE/"DRAW_SCREEN.json"
SELECTION_PLAN = HERE/"draw-selection-plan.json"
SELECTION_RESULT = HERE/"DRAW_SELECTION.json"
LOCK = HERE/"draw-lock.json"
FINAL = HERE/"DRAW_FINAL_REPORT.json"
REJECTION = HERE/"DRAW_REJECTION.json"


def same_or_write(path, value):
    if path.exists():
        if w.read_json(path) != value:
            raise RuntimeError("Existing artifact differs; refusing overwrite: "+str(path))
    else:
        w.write_exclusive(path, value)
    return value


def full_opponents():
    frozen = w.read_json(HERE/"workflow-v2-plan.json")["model"]["opponents"]
    if len(frozen) != 14 or [w.source_manifest(item["spec"]) for item in frozen] != frozen:
        raise RuntimeError("The original fourteen-opponent pool changed")
    return frozen


def preserved():
    paths = [ROOT/BASE, HERE/"workflow-v2-plan.json", HERE/"selection-v2-lock.json", HERE/"FINAL_REPORT_V2.json"]
    for label in ("league-holdout-v2-default", "league-holdout-v2-custom"):
        paths += [HERE/"results"/(label+suffix) for suffix in (".json", ".jsonl")]
    return {str(path.relative_to(ROOT)): bench.digest(path) for path in paths}


def model(opponents):
    return {"opponents": opponents, "infrastructure_sha256": bench.infrastructure(),
            "engine_version": bench._engine.ENGINE_VERSION, "config_hash": bench.CONFIG_HASH,
            "protocol": {"ticks": 2400, "players": 5, "timeout_ms": 20,
                         "fixtures_per_seed_opponent": 4, "workers": 1}}


def screen_plan(create=False):
    expected = {"candidates": [w.source_manifest(spec) for spec in [BASE]+NEW],
                "model": model([w.source_manifest(spec) for spec in SCREEN_OPPONENTS]),
                "full_opponents": full_opponents(), "preserved_v1_sha256": preserved(),
                "protocol_sha256": bench.digest(HERE/"DRAW_PROTOCOL.md")}
    if not SCREEN_PLAN.exists():
        if not create:
            raise RuntimeError("Run --stage screen first")
        w.write_exclusive(SCREEN_PLAN, {"created_utc": w.utc_now(), "definition": expected,
            "note": "Research screen was predeclared in DRAW_PROTOCOL; this manifest records completed early research sources and freezes remaining pivot runs. Independent selection receives its own plan before any 850000-series fixture."})
    plan = w.read_json(SCREEN_PLAN)
    if plan["definition"] != expected:
        raise RuntimeError("A draw-screen source, opponent, infrastructure file or preserved V1 artifact changed")
    return plan["definition"]


def manifests(specs, plan):
    index = {item["spec"]: item for item in plan["candidates"]}
    return [index[spec] for spec in specs]


def report_path(schedule):
    return HERE/"results"/(schedule[0]+".json")


def verify(schedule, teams, game_model):
    return w.verify_report(report_path(schedule), schedule, teams, game_model)


def run(schedule, teams, game_model):
    screen_plan()
    if bench.infrastructure() != game_model["infrastructure_sha256"]:
        raise RuntimeError("Official infrastructure changed")
    if any(w.source_manifest(item["spec"]) != item for item in teams+game_model["opponents"]):
        raise RuntimeError("Planned playing source changed")
    target = report_path(schedule)
    if not target.exists():
        if target.with_suffix(".jsonl").exists():
            raise RuntimeError("Interrupted evidence exists; refusing a rerun: "+str(target))
        label, formation, start, end = schedule
        command = [sys.executable, str(HERE/"bench.py"), "--teams", *[item["spec"] for item in teams],
                   "--opponents", *[item["spec"] for item in game_model["opponents"]], "--start", str(start),
                   "--end", str(end), "--formation", formation, "--label", label]
        subprocess.run(command, cwd=str(ROOT), check=True)
    checked = verify(schedule, teams, game_model)
    screen_plan()
    return checked


def evidence(reports):
    return {str((HERE/"results"/(report["label"]+".json")).relative_to(ROOT)):
            bench.digest(HERE/"results"/(report["label"]+".json")) for report in reports}


def comparison(rows, candidate, expected_count, expected_seeds):
    indexed = analyse.candidate_map(rows)
    paired = analyse.paired(indexed, BASE, candidate)
    if (not paired["complete_fixture_match"] or paired["matched_fixtures"] != expected_count
            or paired["seed_clusters"] != expected_seeds):
        raise RuntimeError("Draw comparison requires complete aligned fixtures")
    summary = {}
    for spec in (BASE, candidate):
        key = analyse.find_candidate(indexed, spec)
        metrics = analyse.metrics(indexed[key]["rows"])
        metrics["goal_difference"] = metrics["goals"][0]-metrics["goals"][1]
        metrics["win_rate"] = metrics["wdl"][0]/metrics["scored_matches"]
        summary[spec] = metrics
    old, new = summary[BASE], summary[candidate]
    return {"policies": summary, "paired": paired,
            "win_change": new["wdl"][0]-old["wdl"][0], "draw_change": new["wdl"][1]-old["wdl"][1],
            "loss_change": new["wdl"][2]-old["wdl"][2],
            "qualifies": w.eligible_metrics(new) and new["wdl"][0] > old["wdl"][0]
                         and new["points"] >= old["points"]}


def reject(stage, detail):
    result = same_or_write(REJECTION, {"stage": stage, "status": "rejected_keep_validated_v1",
        "retained": w.source_manifest(BASE), "detail": detail,
        "note": "No draw-conversion candidate met the predeclared improvement and reliability criteria. Original release and evidence remain unchanged."})
    compared = detail.get("comparisons")
    if compared is None:
        single = detail.get("comparison", detail.get("primary"))
        compared = {} if single is None else {next(spec for spec in single["policies"] if spec != BASE): single}
    lines = ["# Draw-conversion screen outcome", "", "Retain the validated `league-team/team.py`. "
             "The bounded extension ended at the "+stage+" stage because no new candidate met its improvement gate.", "",
             "| Candidate | W/D/L | Points | Change in wins | Change in points |", "|---|---|---:|---:|---:|"]
    if compared:
        base = next(iter(compared.values()))["policies"][BASE]
        lines.append(f"| Validated V1 | {'/'.join(map(str,base['wdl']))} | {base['points']} | 0 | 0 |")
    for spec, comparison_result in compared.items():
        candidate = comparison_result["policies"][spec]
        baseline = comparison_result["policies"][BASE]
        lines.append(f"| {Path(spec).parent.name} | {'/'.join(map(str,candidate['wdl']))} | {candidate['points']} | "
                     f"{comparison_result['win_change']:+d} | {candidate['points']-baseline['points']:+d} |")
    lines += ["", "Rejection is a completed experiment result. No worse candidate replaces the validated release, "
              "and no exposed old holdout is reused as fresh evidence. All fixtures, faults and paired comparisons "
              "remain in [DRAW_REJECTION.json](DRAW_REJECTION.json). The actual school win rate requires uploading "
              "the selected release and receiving new school fixtures.", ""]
    markdown = "\n".join(lines)
    note = HERE/"DRAW_REJECTION.md"
    if note.exists() and note.read_text(encoding="utf-8") != markdown:
        raise RuntimeError("Existing rejection note differs; refusing overwrite")
    if not note.exists():
        with note.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(markdown)
    return result


def screen():
    plan = screen_plan(create=True)
    reports = []
    for index, (schedule, specs) in enumerate(SCREEN_RUNS):
        teams = manifests(specs, plan)
        # Earlier research arms are completed by the root; this stage only
        # schedules the last isolated pivot arms, never recreates missing data.
        reports.append(verify(schedule, teams, plan["model"]) if index < 3 else run(schedule, teams, plan["model"]))
    rows = [row for report in reports for row in report["results"]]
    seed_modes = {(mode, seed) for (label, mode, start, end), _ in SCREEN_RUNS for seed in range(start, end)}
    count, clusters = len(seed_modes)*len(SCREEN_OPPONENTS)*4, len({seed for _, seed in seed_modes})
    comparisons = {spec: comparison([row for row in rows if row["candidate_spec"] in (BASE, spec)], spec, count, clusters)
                   for spec in NEW}
    qualified = [spec for spec in NEW if comparisons[spec]["qualifies"]]
    qualified.sort(key=lambda spec: (-comparisons[spec]["policies"][spec]["wdl"][0],
        -comparisons[spec]["policies"][spec]["points"], -comparisons[spec]["policies"][spec]["goal_difference"], spec))
    result = {"screen_plan_sha256": bench.digest(SCREEN_PLAN), "reports_sha256": evidence(reports),
              "comparisons": comparisons, "selected_for_fresh_selection": qualified[0] if qualified else None,
              "status": "qualified_for_fresh_selection" if qualified else "rejected"}
    same_or_write(SCREEN_RESULT, result)
    if not qualified:
        reject("screen", result)
    print(json.dumps(result), flush=True)


def check_evidence(sha_map):
    for relative, expected in sha_map.items():
        if bench.digest(ROOT/relative) != expected:
            raise RuntimeError("Draw evidence changed: "+relative)


def selection_plan(create=False):
    research = screen_plan()
    result = w.read_json(SCREEN_RESULT)
    if result["screen_plan_sha256"] != bench.digest(SCREEN_PLAN):
        raise RuntimeError("Research screen manifest changed")
    check_evidence(result["reports_sha256"])
    candidate = result["selected_for_fresh_selection"]
    if candidate is None:
        return None
    expected = {"screen_result_sha256": bench.digest(SCREEN_RESULT),
                "candidates": manifests([candidate, BASE], research), "model": model(research["full_opponents"]),
                "preserved_v1_sha256": research["preserved_v1_sha256"],
                "selection": SELECTION, "holdout": HOLDOUT,
                "criterion": "More wins and at least as many league points as V1, no policy exceptions/forfeits or fatal structural counters. New policy ranking: wins, points, goal difference. All timeouts/unavailable kicks retained."}
    expected = json.loads(json.dumps(expected))
    if not SELECTION_PLAN.exists():
        if not create:
            raise RuntimeError("Run --stage selection before lock or holdout")
        if any(report_path(schedule).with_suffix(suffix).exists()
               for schedule in SELECTION+HOLDOUT for suffix in (".json", ".jsonl")):
            raise RuntimeError("Cannot predeclare selection after its fixtures or final evidence exist")
        w.write_exclusive(SELECTION_PLAN, {"created_utc": w.utc_now(), "definition": expected})
        print("Wrote fresh-selection full-source plan before the first fixture.", flush=True)
    declared = w.read_json(SELECTION_PLAN)["definition"]
    if declared != expected:
        raise RuntimeError("Fresh selection source hashes, evidence or protocol changed")
    return declared


def schedule_size(schedules, game_model):
    return len(game_model["opponents"])*4*sum(end-start for _, _, start, end in schedules)


def schedule_seeds(schedules):
    return len({seed for _, _, start, end in schedules for seed in range(start, end)})


def selection():
    plan = selection_plan(create=True)
    if plan is None:
        print("Screen rejected all new candidates; retain validated V1.", flush=True)
        return
    reports = [run(schedule, plan["candidates"], plan["model"]) for schedule in SELECTION]
    rows = [row for report in reports for row in report["results"]]
    candidate = plan["candidates"][0]["spec"]
    compared = comparison(rows, candidate, schedule_size(SELECTION, plan["model"]), schedule_seeds(SELECTION))
    result = {"selection_plan_sha256": bench.digest(SELECTION_PLAN), "reports_sha256": evidence(reports),
              "candidate": candidate, "comparison": compared,
              "status": "qualified_for_separate_lock" if compared["qualifies"] else "rejected"}
    same_or_write(SELECTION_RESULT, result)
    if not compared["qualifies"]:
        reject("selection", result)
    print(json.dumps(result), flush=True)


def verified_selection():
    plan = selection_plan()
    if plan is None:
        return None, None
    result = w.read_json(SELECTION_RESULT)
    if result["selection_plan_sha256"] != bench.digest(SELECTION_PLAN):
        raise RuntimeError("Draw selection plan changed after its result")
    check_evidence(result["reports_sha256"])
    reports = [verify(schedule, plan["candidates"], plan["model"]) for schedule in SELECTION]
    actual = comparison([row for report in reports for row in report["results"]], result["candidate"],
                        schedule_size(SELECTION, plan["model"]), schedule_seeds(SELECTION))
    if actual != result["comparison"]:
        raise RuntimeError("Selection accounting no longer matches its preserved evidence")
    return plan, result


def lock():
    plan, result = verified_selection()
    if result is None or not result["comparison"]["qualifies"]:
        print("No qualifying extension; no new release lock is created.", flush=True)
        return
    if LOCK.exists():
        load_lock()
        print("Existing draw lock verified; no reselection.", flush=True)
        return
    if any(report_path(schedule).with_suffix(suffix).exists()
           for schedule in HOLDOUT for suffix in (".json", ".jsonl")):
        raise RuntimeError("Cannot package or select after new final holdout exposure")
    original = plan["candidates"][0]
    version = "draw-v1-"+original["sha256"][:12]
    contents = w.metadata_release((ROOT/original["spec"]).read_bytes(), "MONSTER STRIKER", version)
    destination = ROOT/STRIKER
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() != contents:
            raise RuntimeError("Existing league-striker differs; refusing overwrite")
    else:
        with destination.open("xb") as stream:
            stream.write(contents)
    controller = bench.load_controller(str(destination))
    if controller.name != "MONSTER STRIKER" or controller.version != version:
        raise RuntimeError("Packaged controller discovery or metadata failed")
    same_or_write(LOCK, {"locked_utc": w.utc_now(), "selection_plan_sha256": bench.digest(SELECTION_PLAN),
        "selection_result_sha256": bench.digest(SELECTION_RESULT), "original": original,
        "release": w.source_manifest(STRIKER), "baseline": plan["candidates"][1],
        "metadata_only_change": True, "note": "Separate extension locked before new 860000-series holdout. Original V1 remains unchanged."})
    print(json.dumps(w.read_json(LOCK)), flush=True)


def load_lock():
    plan = selection_plan()
    if plan is None or not LOCK.exists():
        raise RuntimeError("A qualifying draw extension must be separately locked before holdout")
    locked = w.read_json(LOCK)
    if (locked["selection_plan_sha256"] != bench.digest(SELECTION_PLAN)
            or locked["selection_result_sha256"] != bench.digest(SELECTION_RESULT)
            or locked["original"] != plan["candidates"][0]
            or locked["baseline"] != plan["candidates"][1]
            or locked["release"] != w.source_manifest(STRIKER)):
        raise RuntimeError("A locked draw source, baseline or selection artifact changed")
    return plan, locked


def holdout():
    plan, locked = load_lock()
    teams = [locked["release"], locked["baseline"]]
    for schedule in HOLDOUT:
        load_lock()
        run(schedule, teams, plan["model"])
        load_lock()
    print("New independent holdout completed; run --stage report for the promotion decision.", flush=True)


def report():
    plan, locked = load_lock()
    teams = [locked["release"], locked["baseline"]]
    reports = [verify(schedule, teams, plan["model"]) for schedule in HOLDOUT]
    rows = [row for part in reports for row in part["results"]]
    total, seeds = schedule_size(HOLDOUT, plan["model"]), schedule_seeds(HOLDOUT)
    primary = comparison(rows, STRIKER, total, seeds)
    source_keys = {item["key"] for item in plan["model"]["opponents"] if item["key"].startswith("source:")}
    source_rows = [row for row in rows if row["opponent_key"] in source_keys]
    per_opponent = 4*sum(end-start for _, _, start, end in HOLDOUT)
    secondary = comparison(source_rows, STRIKER, len(source_keys)*per_opponent, seeds)
    by_mode, by_opponent = {}, {}
    for mode in ("custom", "default"):
        subset = [row for row in rows if row["formation"] == mode]
        count = len(plan["model"]["opponents"])*4*sum(end-start for _, arm, start, end in HOLDOUT if arm == mode)
        clusters = len({seed for _, arm, start, end in HOLDOUT if arm == mode for seed in range(start, end)})
        by_mode[mode] = comparison(subset, STRIKER, count, clusters)
    for opponent in plan["model"]["opponents"]:
        by_opponent[opponent["spec"]] = comparison([row for row in rows if row["opponent_key"] == opponent["key"]],
                                                  STRIKER, per_opponent, seeds)
    promote = primary["qualifies"]
    result = {"status": "promote_separate_draw_extension" if promote else "reject_extension_keep_validated_v1",
              "chosen": locked["release"] if promote else locked["baseline"],
              "draw_lock_sha256": bench.digest(LOCK), "reports_sha256": evidence(reports),
              "primary": primary, "secondary_source_defined_pool": secondary,
              "by_formation": by_mode, "by_opponent": by_opponent,
              "protocol": {**plan["model"]["protocol"], "matches_per_policy": total, "seed_clusters": seeds,
                           "source_matches_per_policy": len(source_keys)*per_opponent},
              "note": "Local tactical pool only, not the actual school field. All fixtures, unavailable kicks and timeouts retained. Promotion requires more wins, no league-point regression and no fatal policy/action faults. Original release remains available and unchanged."}
    same_or_write(FINAL, result)
    if not promote:
        reject("final_holdout", result)
    same_or_write(HERE/"DRAW_PROMOTION.json", {"status": result["status"], "chosen": result["chosen"],
                  "final_report_sha256": bench.digest(FINAL)})
    lines = ["# Draw-conversion validation", "", "Decision: **"+result["status"]+"**. "
             "The selected file is `"+result["chosen"]["spec"]+"`; the original V1 file and evidence remain unchanged.", "",
             f"Independent final comparison: {total} matched fixtures per policy over {seeds} fresh seed clusters.", "",
             "| Pool | Policy | W/D/L | Points | Win rate | GF/GA | Errors/timeouts |",
             "|---|---|---|---:|---:|---|---|"]
    for pool_name, compared in (("All 14 opponents", primary), ("Source-defined opponents", secondary)):
        for spec in (BASE, STRIKER):
            metrics = compared["policies"][spec]
            lines.append(f"| {pool_name} | {'V1' if spec == BASE else 'Extension'} | "
                f"{'/'.join(map(str,metrics['wdl']))} | {metrics['points']} | {metrics['win_rate']:.1%} | "
                f"{'/'.join(map(str,metrics['goals']))} | {metrics['policy_errors']}/{metrics['policy_timeouts']} |")
    lines += ["", "Changes are extension minus V1. Confidence intervals use paired seed-cluster bootstrap:", ""]
    for pool_name, compared in (("Primary", primary), ("Secondary source-only", secondary)):
        low, high = compared["paired"]["seed_bootstrap95"]
        lines.append(f"- {pool_name}: {compared['win_change']:+d} wins, {compared['draw_change']:+d} draws, "
            f"{compared['loss_change']:+d} losses; points/game {compared['paired']['points_per_match_change']:+.3f} "
            f"[{low:+.3f}, {high:+.3f}].")
    lines += ["", "Every fixture and fault remains included. The secondary source-only pool excludes native baselines; "
              "neither pool is the actual school cohort. Full mode/opponent metrics, hashes and comparisons are in "
              "[DRAW_FINAL_REPORT.json](DRAW_FINAL_REPORT.json).", ""]
    markdown = "\n".join(lines)
    destination = HERE/"DRAW_REPORT.md"
    if destination.exists() and destination.read_text(encoding="utf-8") != markdown:
        raise RuntimeError("Existing draw report differs; refusing overwrite")
    if not destination.exists():
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(markdown)
    screen_plan()
    print(json.dumps({"decision": result["status"], "chosen": result["chosen"],
                      "primary": primary, "secondary": secondary}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("screen", "selection", "lock", "holdout", "report"), required=True)
    args = parser.parse_args()
    stages = {"screen": screen, "selection": selection, "lock": lock, "holdout": holdout, "report": report}
    stages[args.stage]()


if __name__ == "__main__":
    main()
