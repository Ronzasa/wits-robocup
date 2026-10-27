"""Official-engine adversarial laboratory. No submission imports this module."""
import argparse
import hashlib
import json
import math
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
ROOT = LAB.parents[1]
sys.path.insert(0, str(ROOT))
import bootstrap
bootstrap.ensure_engine(ROOT)
from soccer.runner import play_match, summarise_results
from soccer import _engine
from soccer import SoccerEnv, TeamAction, PlayerAction, TeamController
from soccer.helpers import load_controller

TITAN_SHA = "5c73068b5e574093e9e1afce972ff8b3546b484c103505c9e79d80772ac6299d"
SPLITS = {"train": (700000, 700020), "validation": (710000, 710010),
          "holdout": (730000, 730025), "generalization": (740000, 740010),
          "round2-train": (750000, 750012), "round2-validation": (760000, 760010),
          "round2-holdout": (770000, 770025),
          "round2-holdout-control": (770000, 770025),
          "round2-generalization": (780000, 780010)}
MONSTER_V1_SHA = "1bf09f5fcab940eae8f387ef36030d302dfe9e52aa6ae0fe82f48742ea6e85b7"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def protect():
    path = LAB / "protected.json"
    if path.exists():
        manifest = json.loads(path.read_text())
        for relative, expected in manifest["files"].items():
            if sha(ROOT / relative) != expected:
                raise RuntimeError("PROTECTED FILE CHANGED: " + relative)
        return manifest
    if sha(ROOT / "my-team/team.py") != TITAN_SHA:
        raise RuntimeError("Validated TITAN hash mismatch")
    files = [ROOT / "my-team/team.py", LAB / "frozen-titan/team.py", ROOT / "configs/default.toml"]
    files += sorted((ROOT / "student-sdk/soccer").glob("*.py"))
    files += sorted((ROOT / "engine/windows-x86_64").glob("*"))
    manifest = {"files": {str(p.relative_to(ROOT)): sha(p) for p in files if p.is_file()},
                "splits_exclusive": SPLITS,
                "protocol": "4 fixtures per seed: candidate side 0/1 x kickoff owner 0/1; 2400 ticks; 20 ms"}
    path.write_text(json.dumps(manifest, indent=2))
    return manifest


def resolve(value):
    if value == "titan":
        return str(LAB / "frozen-titan/team.py")
    if value.endswith(".py"):
        p = Path(value)
        return str(p.resolve() if p.is_absolute() or p.exists() else (LAB / p).resolve())
    return value


def wilson(wins, n):
    if not n:
        return [0.0, 1.0]
    z = 1.96
    p = wins / n
    d = 1 + z*z/n
    mid = (p + z*z/(2*n))/d
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return [mid-half, mid+half]


def report(rows):
    summary = summarise_results(rows)
    n = len(rows)
    wins, losses = summary["team_a_wins"], summary["team_b_wins"]
    summary["win_rate"] = wins / n if n else 0
    summary["decisive_win_rate"] = wins / (wins+losses) if wins+losses else None
    summary["win_rate_wilson95"] = wilson(wins, n)
    groups = {}
    for r in rows:
        groups.setdefault(r["seed"], []).append(r)
    means = [statistics.mean(r["score"][0]-r["score"][1] for r in group) for group in groups.values()]
    summary["independent_seeds"] = len(means)
    summary["mean_gd_seed_cluster_ci95_halfwidth"] = 1.96*statistics.stdev(means)/math.sqrt(len(means)) if len(means)>1 else None
    if len(groups) > 1:
        per_seed = [sum(r["score"][0]>r["score"][1] for r in group)/len(group) for group in groups.values()]
        rng = random.Random(41629)
        boot = sorted(statistics.mean(rng.choices(per_seed, k=len(per_seed))) for _ in range(3000))
        summary["win_rate_seed_bootstrap95"] = [boot[75], boot[2924]]
    summary["by_fixture"] = {}
    for side in (0, 1):
        for own_kickoff in (False, True):
            subset = [r for r in rows if r["candidate_side"] == side and r["candidate_kickoff"] == own_kickoff]
            summary["by_fixture"][f"side{side}-ownkickoff{int(own_kickoff)}"] = {
                "matches": len(subset), "wins": sum(r["score"][0]>r["score"][1] for r in subset),
                "draws": sum(r["score"][0]==r["score"][1] for r in subset),
                "goals": [sum(r["score"][i] for r in subset) for i in (0, 1)]}
    return summary


class TimingDiagnostic(TeamController):
    """Offline timing observer; forwards actions and lifecycle unchanged."""
    def __init__(self,spec):
        self.inner = load_controller(spec)
        self.name,self.version = self.inner.name,self.inner.version

    def initial_formation(self,field):
        return self.inner.initial_formation(field)

    def reset(self,seed):
        self.timing = {"decisions":0,"max_cpu_ms":0,"max_wall_ms":0,"slow_calls":[]}
        self.inner.reset(seed)

    def act(self,obs):
        wall,cpu = time.perf_counter(),time.thread_time()
        try:
            return self.inner.act(obs)
        finally:
            elapsed_cpu = (time.thread_time()-cpu)*1000
            elapsed_wall = (time.perf_counter()-wall)*1000
            t = self.timing
            t["decisions"] += 1
            t["max_cpu_ms"] = max(t["max_cpu_ms"],elapsed_cpu)
            t["max_wall_ms"] = max(t["max_wall_ms"],elapsed_wall)
            if elapsed_wall>5:
                t["slow_calls"].append({"tick":obs.tick,"wall_ms":elapsed_wall,"cpu_ms":elapsed_cpu})

    def on_match_end(self,result):
        self.inner.on_match_end(result)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--team", default="monster/team.py")
    p.add_argument("--against", default="titan")
    p.add_argument("--split", choices=SPLITS, default="train")
    p.add_argument("--seeds", default=None, help="exclusive START..END within split")
    p.add_argument("--label", default=None)
    p.add_argument("--record", type=int, default=0, help="record first N fixtures")
    p.add_argument("--inspect-replay")
    p.add_argument("--verify", action="store_true")
    p.add_argument("--sweep", nargs="+", help="benchmark these frozen pool files sequentially")
    p.add_argument("--probe-goal", action="store_true", help="controlled legal kick geometry diagnostic, not a competitive benchmark")
    p.add_argument("--scorecard", action="store_true")
    p.add_argument("--opponents", nargs="+", help="run the same candidate sequentially against this opponent set")
    p.add_argument("--diagnose-result", help="extract actual goal/foul/wall observations from recorded fixtures")
    p.add_argument("--audit-holdout", action="store_true", help="verify the locked final protocol and report timeout sensitivity")
    p.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"), help="paired comparison of two result files on identical fixtures")
    p.add_argument("--cpu-profile", action="store_true", help="instrumented timing diagnostic, excluded from competitive scorecard")
    a = p.parse_args()
    protect()
    if a.cpu_profile and (a.sweep or a.opponents):
        raise ValueError("Run timing diagnostics as a single team/opponent pair")
    if a.compare:
        before,after = [json.loads(Path(path).read_text(encoding="utf-8")) for path in a.compare]
        assert before["opponent_sha256"] == after["opponent_sha256"] and before["opponent"] == after["opponent"]
        key = lambda r:(r["seed"],r["candidate_side"],r["kickoff_team"])
        old,new = [{key(r):r for r in data["results"]} for data in (before,after)]
        assert old.keys() == new.keys()
        points = lambda r:3 if r["score"][0]>r["score"][1] else int(r["score"][0]==r["score"][1])
        clusters = {}
        for fixture in old:
            o,n = old[fixture],new[fixture]
            clusters.setdefault(fixture[0],[]).append((points(n)-points(o),n["goal_difference"]-o["goal_difference"]))
        means = [tuple(statistics.mean(pair[i] for pair in rows) for i in (0,1)) for rows in clusters.values()]
        rng = random.Random(91831)
        boot = [sorted(statistics.mean(pair[i] for pair in rng.choices(means,k=len(means))) for _ in range(3000)) for i in (0,1)]
        result = {"before":a.compare[0],"after":a.compare[1],"matches":len(old),"seed_clusters":len(clusters),
                  "points_per_match_change":statistics.mean(pair[0] for pair in means),
                  "mean_gd_change":statistics.mean(pair[1] for pair in means),
                  "points_change_seed_bootstrap95":[boot[0][75],boot[0][2924]],
                  "gd_change_seed_bootstrap95":[boot[1][75],boot[1][2924]],
                  "before_summary":before["summary"],"after_summary":after["summary"]}
        out = LAB/(Path(a.compare[1]).stem+".comparison.json")
        out.write_text(json.dumps(result,indent=2),encoding="utf-8")
        print(json.dumps({k:v for k,v in result.items() if not k.endswith("summary")}))
        return
    if a.audit_holdout:
        data = json.loads((LAB/"results/monster-v25-holdout.json").read_text())
        lock = json.loads((LAB/"holdout-lock.json").read_text())
        # Audit the historical release against its immutable source, even
        # after the main MONSTER file has advanced to a newer generation.
        assert data["source_sha256"] == lock["sha256"] == sha(LAB/"pool/v25-fast-post/team.py")
        assert data["opponent_sha256"] == TITAN_SHA
        rows = data["results"]
        expected = {(seed, side, kickoff) for seed in range(*SPLITS["holdout"])
                    for side in (0, 1) for kickoff in (0, 1)}
        actual = [(r["seed"], r["candidate_side"], r["kickoff_team"]) for r in rows]
        assert len(actual) == len(set(actual)) == 100 and set(actual) == expected
        assert all(r["ticks"] == 2400 and r["terminal_reason"] == "time_limit"
                   and r["config_hash"] == "372990895c7eca2a" for r in rows)
        for r in rows:
            assert r["score"] == (r["absolute_score"][::-1] if r["candidate_side"] else r["absolute_score"])
            assert r["candidate_kickoff"] == (r["kickoff_team"] == r["candidate_side"])
            assert all(r["stats"][0]["validation"][key] == 0
                       for key in ("missing_actions", "non_finite_values", "invalid_player_ids"))
        clean = [r for r in rows if all(s["policy_errors"] == 0 and s["policy_timeouts"] == 0 for s in r["stats"])]
        audit = {"protocol_checks_passed": True, "fixtures": len(rows), "independent_seeds": 25,
                 "source_sha256": data["source_sha256"], "protected_titan_sha256": TITAN_SHA,
                 "excluded_for_either_policy_error_or_timeout": [r["match_id"] for r in rows if r not in clean],
                 "sensitivity_fault_free_only": report(clean),
                 "note": "Post-hoc descriptive sensitivity only. All 100 fixtures remain the primary result; no reruns or replacements."}
        (LAB/"holdout-audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
        print(json.dumps(audit))
        return
    if a.sweep and a.opponents:
        for team in a.sweep:
            cmd = [sys.executable, str(Path(__file__).resolve()), "--team", team,
                   "--opponents", *a.opponents, "--split", a.split,
                   "--label", (a.label or "league")+"-"+Path(team).parent.name,
                   "--record", str(a.record)]
            if a.seeds:
                cmd += ["--seeds", a.seeds]
            subprocess.run(cmd,check=True)
        return
    if a.opponents:
        for opponent in a.opponents:
            suffix = Path(opponent).parent.name if opponent.endswith(".py") else opponent
            cmd = [sys.executable, str(Path(__file__).resolve()), "--team", a.team,
                   "--against", opponent, "--split", a.split,
                   "--label", (a.label or "opponents")+"-"+suffix,
                   "--record", str(a.record)]
            if a.seeds:
                cmd += ["--seeds", a.seeds]
            subprocess.run(cmd,check=True)
        return
    if a.diagnose_result:
        result = json.loads(Path(a.diagnose_result).read_text())
        diagnostics = []
        for row in result["results"]:
            replay = row.get("replay_path")
            if not replay:
                continue
            data = _engine.read_replay(replay,True)
            frames = data["frames"]
            side = row["candidate_side"]
            other = 1-side
            enemy_goal_x = -50 if other==0 else 50
            own_goal_x = -enemy_goal_x
            events = data["events"]
            goals = [e for e in events if e["kind"]=="goal"]
            foul_events = [e for e in events if e["kind"]=="foul"]
            tied_enemy_wall = 0
            own_wall = 0
            for f in frames:
                enemy = f["players"][5*other:5*other+5]
                own = f["players"][5*side:5*side+5]
                count = sum(abs(q["position"]["x"]-enemy_goal_x)<3.5 and abs(q["position"]["y"])<9 for q in enemy)
                own_count = sum(abs(q["position"]["x"]-own_goal_x)<3.5 and abs(q["position"]["y"])<9 for q in own)
                own_wall += own_count>=4
                tied_enemy_wall += f["score"][0]==f["score"][1] and f["score"][0]>0 and count>=4
            diagnostics.append({"fixture":row["match_id"],"score_candidate_first":row["score"],
                                "candidate_side":side,"candidate_kickoff":row["candidate_kickoff"],
                                "goal_events":goals,"foul_events":foul_events,
                                "tied_enemy_wall_ticks":tied_enemy_wall,"candidate_wall_ticks":own_wall,
                                "frames":len(frames)})
        out = Path(a.diagnose_result).with_suffix(".diagnostics.json")
        out.write_text(json.dumps(diagnostics,indent=2))
        print(json.dumps(diagnostics))
        return
    if a.scorecard:
        lines = ["# MONSTER laboratory scorecard", "",
                 "All competitive rows: official engine/config, 2,400 ticks, 20 ms, four fixtures per seed.",
                 "Training/validation are selection data. Only the locked holdout is a final estimate.", "",
                 "| Run | Split | N | W/D/L | Goals | Mean GD | Win % | Decisive win % | Mean/max ms | Errors/timeouts |",
                 "|---|---|---:|---|---|---:|---:|---:|---|---|"]
        for f in sorted((LAB/"results").glob("*.json")):
            data = json.loads(f.read_text())
            if not isinstance(data,dict) or "summary" not in data:
                continue
            if data.get("instrumented_cpu_profile"):
                continue
            s = data["summary"]
            t = s["team_stats"][0]
            decisive = "n/a" if s["decisive_win_rate"] is None else f"{100*s['decisive_win_rate']:.1f}"
            lines.append(f"| [{f.stem}](results/{f.name}) | {data['split']} | {s['matches']} | {s['team_a_wins']}/{s['draws']}/{s['team_b_wins']} | {s['goals'][0]}–{s['goals'][1]} | {s['mean_goal_difference']:+.3f} | {100*s['win_rate']:.1f} | {decisive} | {t['decision_mean_ms']:.3f}/{t['decision_max_ms']:.3f} | {t['policy_errors']}/{t['policy_timeouts']} |")
        lines += ["", "Protected original TITAN SHA-256: `"+TITAN_SHA+"`.",
                  "Full JSON reports retain source hashes, immutable snapshots, per-fixture results, passing/possession/shot/interception statistics and uncertainty intervals."]
        (LAB/"SCORECARD.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
        print(str(LAB/"SCORECARD.md"))
        return
    if a.probe_goal:
        probes = []
        for target_y in (6.8, 7.0, 7.2, 7.4, 7.6):
            env = SoccerEnv(config_path=str(ROOT / "configs/default.toml"), max_ticks=2400)
            env.set_formation(0, [(-40,-24),(-40,24),(-25,-24),(-25,24),(-9,0)])
            env.set_formation(1, [(-35,-25),(-32,-23),(-28,-25),(-24,-23),(-20,-25)])
            observations = env.reset(seed=111, kickoff_team=0)
            kicked = False
            greatest_x = (-100, 0)
            goals = []
            for tick in range(240):
                obs = observations["team_a"]
                action = TeamAction({i: PlayerAction() for i in range(5)})
                if not kicked:
                    p4 = obs.my_players[4]
                    bx, by = obs.ball.position
                    if obs.can_kick(4):
                        dx, dy = obs.opponent_goal[0]-bx, target_y-by
                        norm = math.hypot(dx,dy)
                        action.kick(4, (dx/norm,dy/norm), 1.0)
                        kicked = True
                    else:
                        dx,dy = bx-p4.position[0],by-p4.position[1]
                        norm = max(1e-9,math.hypot(dx,dy))
                        action.move(4,(dx/norm,dy/norm))
                observations, _ = env.step({"team_a": action, "team_b": TeamAction({i:PlayerAction() for i in range(5)})})
                pos = observations["team_a"].ball.position
                if pos[0]>greatest_x[0]:
                    greatest_x = tuple(pos)
                goals += [e for e in observations["team_a"].events if e["kind"]=="goal"]
                if goals:
                    break
            probes.append({"aim_y_at_x50": target_y, "goals": goals, "furthest_observed_position": greatest_x,
                           "config_hash": env.result()["config_hash"]})
            env.close()
        (LAB/"results/goal-mouth-probe.json").write_text(json.dumps(probes,indent=2))
        print(json.dumps(probes))
        protect()
        return
    if a.sweep:
        for team in a.sweep:
            label = (a.label or "sweep")+"-"+Path(team).parent.name
            cmd = [sys.executable, str(Path(__file__).resolve()), "--team", team,
                   "--against", a.against, "--split", a.split, "--label", label,
                   "--record", str(a.record)]
            if a.seeds:
                cmd += ["--seeds", a.seeds]
            subprocess.run(cmd, check=True)
        return
    if a.verify:
        print("Protected TITAN, SDK, engine and config hashes verified.")
        return
    if a.inspect_replay:
        data = _engine.read_replay(str(Path(a.inspect_replay).resolve()), True)
        goals = [e for e in data["events"] if e["kind"] == "goal"]
        frames = data.get("frames", [])
        context = []
        for g in goals:
            nearby = [f for f in frames if f["tick"] in (g["tick"]-12, g["tick"]-4, g["tick"]-1)]
            simplified = [{"tick": f["tick"], "ball": f.get("ball_position"),
                           "velocity": f.get("ball_velocity"),
                           "players": [(i, q["position"], q["velocity"]) for i, q in enumerate(f.get("players", []))]}
                          for f in nearby]
            kicks = [e for e in data["events"] if e["kind"]=="kick" and g["tick"]-40<=e["tick"]<g["tick"]]
            context.append({"goal": g, "frames": simplified, "last_kicks": kicks[-3:]})
        print(json.dumps({"teams": data["header"]["team_ids"], "seed": data["header"]["seed"],
                          "goal_context": context}, default=str))
        return
    team, opponent = resolve(a.team), resolve(a.against)
    digest = sha(team)
    if a.split == "round2-holdout-control":
        assert digest == MONSTER_V1_SHA, "Paired holdout control must be the predeclared first MONSTER"
        assert (LAB/"round2-holdout-lock.json").exists(), "Freeze the new finalist before exposing its paired control seeds"
    snapshot = LAB / "candidates" / digest[:12] / "team.py"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if not snapshot.exists():
        snapshot.write_bytes(Path(team).read_bytes())
    # Always benchmark the immutable snapshot, not an editor's in-progress file.
    team = str(snapshot)
    lo, hi = SPLITS[a.split]
    start, end = tuple(map(int, a.seeds.split(".."))) if a.seeds else (lo, hi)
    if not lo <= start < end <= hi:
        raise ValueError("Seeds must stay within the declared split")
    label = a.label or f"{digest[:12]}-{a.split}-{Path(a.against).stem}-{start}-{end}"
    target = LAB / "results" / (label + ".json")
    if target.exists():
        raise RuntimeError("Result label already exists; use a new label")
    if a.split in ("holdout", "round2-holdout"):
        lock = LAB / ("holdout-lock.json" if a.split == "holdout" else "round2-holdout-lock.json")
        if lock.exists() and json.loads(lock.read_text())["sha256"] != digest:
            raise RuntimeError("Holdout was already exposed to a different candidate; reserve a new split")
        lock.write_text(json.dumps({"sha256": digest, "seeds": [lo, hi], "source": str(snapshot)}, indent=2))
    rows = []
    started = time.perf_counter()
    with target.with_suffix(".jsonl").open("x", encoding="utf-8") as stream:
        for seed in range(start, end):
            for side in (0, 1):
                for kickoff in (0, 1):
                    name = f"{label}-{seed}-s{side}-k{kickoff}"
                    replay = str(LAB / "replays" / (name + ".rep")) if len(rows)<a.record else None
                    sides = (team, opponent) if side == 0 else (opponent, team)
                    if a.cpu_profile:
                        sides = tuple(TimingDiagnostic(spec) if Path(spec).is_file() else spec for spec in sides)
                    row = play_match(*sides, seed=seed, kickoff_team=kickoff,
                                     config_path=str(ROOT / "configs/default.toml"), max_ticks=2400,
                                     per_decision_timeout_ms=20, match_id=name,
                                     record_replay=replay, record_debug=bool(replay)).result
                    row["absolute_score"] = list(row["score"])
                    if side == 1:
                        row["score"] = list(reversed(row["score"]))
                        row["stats"] = list(reversed(row["stats"]))
                    row["goal_difference"] = row["score"][0]-row["score"][1]
                    row["candidate_side"] = side
                    if a.cpu_profile:
                        ordered = sides if side==0 else sides[::-1]
                        row["cpu_timing"] = [spec.timing if isinstance(spec,TimingDiagnostic) else None for spec in ordered]
                    row["candidate_kickoff"] = kickoff == side
                    row["sides_swapped"] = bool(side)
                    rows.append(row)
                    stream.write(json.dumps(row)+"\n")
                    stream.flush()
            print(f"{label} seed {seed}: " + ", ".join(f"{r['score'][0]}-{r['score'][1]}" for r in rows[-4:]), flush=True)
    protect()
    s = report(rows)
    result = {"source_sha256": digest, "source_snapshot": str(snapshot.relative_to(LAB)),
              "instrumented_cpu_profile": a.cpu_profile,
              "opponent": a.against, "opponent_sha256": sha(opponent) if Path(opponent).is_file() else None,
              "split": a.split, "seeds_exclusive": [start, end], "summary": s,
              "wall_seconds": time.perf_counter()-started, "results": rows}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"file": str(target), "sha256": digest, "matches":s["matches"],
                      "WDL":[s["team_a_wins"],s["draws"],s["team_b_wins"]],
                      "goals":s["goals"], "mean_gd":s["mean_goal_difference"],
                      "win_rate":s["win_rate"], "decisive_win_rate":s["decisive_win_rate"],
                      "wilson95":s["win_rate_wilson95"],
                      "mean_max_ms":[s["team_stats"][0]["decision_mean_ms"],s["team_stats"][0]["decision_max_ms"]],
                      "errors_timeouts":[s["team_stats"][0]["policy_errors"],s["team_stats"][0]["policy_timeouts"]]}), flush=True)


if __name__ == "__main__":
    main()
