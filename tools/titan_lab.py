"""Reproducible TITAN experiments using the unmodified official SDK/engine."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import bootstrap

bootstrap.ensure_engine(ROOT)
from soccer.runner import evaluate, play_match, summarise_results
from soccer.helpers import load_controller
from soccer import TeamController


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--team", default="my-team/team.py")
    parser.add_argument("--opponents", nargs="+", default=["balanced", "tactical", "possession"])
    parser.add_argument("--start", type=int, default=1000)
    parser.add_argument("--end", type=int, default=1020)
    parser.add_argument("--label", default="candidate")
    parser.add_argument("--replays", action="store_true")
    parser.add_argument("--diagnose", action="store_true")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--score-offset", type=int, default=0,
                        help="diagnostic: add this many goals to the opponent score seen by TITAN")
    parser.add_argument("--both-kickoffs", action="store_true",
                        help="test both kickoff owners on both field sides (SDK evaluate always gives team_a kickoff)")
    args = parser.parse_args()
    if args.replays:
        folder = Path(r"C:\Users\tech\Downloads")
        for path in sorted(folder.glob("replay*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            header = data["header"]
            goals = [e for e in data["events"] if e["kind"] == "goal"]
            print(json.dumps({"file": str(path), "teams": header["team_ids"],
                              "config": header["config_hash"], "seed": header["seed"],
                              "goals": goals, "keys": list(data),
                              "frame_example": data.get("frames", [None])[0]}, default=str))
        return
    if args.diagnose or args.profile:
        controller = load_controller(str((ROOT / args.team).resolve()))
        slow = []
        class Probe(TeamController):
            name = controller.name
            def reset(self, seed):
                controller.reset(seed)
            def initial_formation(self, field):
                return controller.initial_formation(field)
            def act(self, obs):
                start = time.perf_counter()
                action = controller.act(obs)
                elapsed = (time.perf_counter() - start) * 1000
                if elapsed > 5:
                    slow.append({"ms": round(elapsed, 3), "tick": obs.tick,
                                 "score": obs.score, "ball": obs.ball.position,
                                 "velocity": obs.ball.velocity})
                return action
        if args.profile:
            import cProfile
            import pstats
            profile = cProfile.Profile()
            profile.enable()
        for seed in range(args.start, args.end):
            play_match(Probe(), args.opponents[0], seed=seed,
                       per_decision_timeout_ms=1000 if args.profile else 20)
        if args.profile:
            profile.disable()
            pstats.Stats(profile).sort_stats("tottime").print_stats(28)
        print(json.dumps(sorted(slow, key=lambda x: -x["ms"])[:25]))
        return
    output = ROOT / "experiments" / "results"
    output.mkdir(parents=True, exist_ok=True)
    team = str((ROOT / args.team).resolve())
    source_hash = hashlib.sha256(Path(team).read_bytes()).hexdigest()
    for opponent in args.opponents:
        opponent_spec = str((ROOT / opponent).resolve()) if ".py" in opponent else opponent
        if args.score_offset or args.both_kickoffs:
            class ScoreView:
                def __init__(self, obs):
                    self._obs = obs
                    self.score = (obs.score[0], obs.score[1] + args.score_offset)
                def __getattr__(self, key):
                    return getattr(self._obs, key)
            class Handicap(TeamController):
                def __init__(self):
                    self.controller = load_controller(team)
                    self.name = self.controller.name
                def reset(self, seed):
                    self.controller.reset(seed)
                def initial_formation(self, field):
                    return self.controller.initial_formation(field)
                def act(self, obs):
                    return self.controller.act(ScoreView(obs) if args.score_offset else obs)
            rows = []
            for seed in range(args.start, args.end):
                for swapped in (False, True):
                    for kickoff in ((0, 1) if args.both_kickoffs else (int(swapped),)):
                        sides = (opponent_spec, Handicap()) if swapped else (Handicap(), opponent_spec)
                        row = play_match(*sides, seed=seed, kickoff_team=kickoff,
                                         config_path=str(ROOT / "configs/default.toml")).result
                        if swapped:
                            row["score"].reverse()
                            row["stats"].reverse()
                        row["sides_swapped"] = swapped
                        row["titan_kickoff"] = kickoff == int(swapped)
                        rows.append(row)
            report = {"team_a": team, "team_b": opponent_spec,
                      "score_offset_diagnostic": args.score_offset,
                      "both_kickoffs": args.both_kickoffs,
                      "summary": summarise_results(rows), "results": rows}
        else:
            report = evaluate(team, opponent_spec, seeds=range(args.start, args.end),
                              swap_sides=True, workers=1, config_path=str(ROOT / "configs/default.toml"))
        report["source_sha256"] = source_hash
        report["seed_range_exclusive"] = [args.start, args.end]
        destination = output / (args.label + "-" + Path(opponent).stem + ".json")
        destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
        s = report["summary"]
        print(json.dumps({"label": args.label, "opponent": opponent, "sha256": source_hash,
                          "matches": s["matches"], "wins": s["team_a_wins"],
                          "draws": s["draws"], "losses": s["team_b_wins"],
                          "goals": s["goals"], "mean_gd": s["mean_goal_difference"],
                          "ci95": s["goal_difference_ci95"], "stats": s["team_stats"][0],
                          "platform_errors": sum(bool(r.get("platform_error")) for r in report["results"])}), flush=True)


if __name__ == "__main__":
    main()
