"""Native comparisons using the default roster observed in the course replays.

The decision/failure loop uses the official SDK and native deadline enforcement.
It intentionally does not call optional initial_formation hooks. Use this
profile when reproducing the supplied default-roster course matches.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
# Respect a complete SDK supplied through PYTHONPATH or an installed wheel.
# A Git worktree may contain the Python sources without the compiled engine.
sys.path.append(str(ROOT / "student-sdk"))
from soccer import SoccerEnv, TeamController, runner
from soccer.helpers import load_controller

def native_match(candidate,opponent,seed,side,kick,reg):
    paths=[candidate,opponent]
    if side:paths.reverse()
    controllers=[load_controller(p) for p in paths]
    kickoff=side if kick else 1-side
    telemetry=dict(first_goal=None,slow=[])
    with SoccerEnv(config_path=reg['config_path'],max_ticks=2400,per_decision_timeout_ms=20.,
                   team_ids=('policy_a','policy_b')) as env:
        for c in controllers:c.reset(seed)
        observations=env.reset(seed=seed,kickoff_team=kickoff)
        initial_roster=[list(p.position) for p in list(observations['team_a'].my_players)+list(observations['team_a'].opponents)]
        previous=[TeamController.idle(observations[key]) for key in ('team_a','team_b')]
        while not env.finished:
            actions={}
            for slot,key in ((0,'team_a'),(1,'team_b')):
                obs=observations[key]
                action,elapsed,error=runner._decide(controllers[slot],obs)
                if slot==side and telemetry['first_goal'] is None and sum(obs.score):
                    telemetry['first_goal']='candidate' if obs.score[0]>obs.score[1] else 'opponent'
                if error is None:previous[slot]=action
                else:action=previous[slot]
                if elapsed>20. or error is not None:
                    telemetry['slow'].append(dict(side=slot,tick=obs.tick,elapsed_ms=elapsed,error=error))
                env.record_decision(slot,elapsed,error)
                actions[key]=action
            if env.finished:break
            observations,_=env.step(actions)
        result=env.result()
    assert result['engine_version']==reg['engine_version'] and result['config_hash']==reg['config_hash']
    assert not result.get('platform_error')
    return result,telemetry,initial_roster


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team", type=Path, required=True)
    parser.add_argument("--opponent", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--side", type=int, choices=(0, 1), default=0)
    parser.add_argument("--candidate-kickoff", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/default.toml")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Output already exists; retain earlier evidence.")
    profile = dict(config_path=str(args.config.resolve()),
                   config_hash="372990895c7eca2a", engine_version="0.1.0")
    result, telemetry, roster = native_match(
        str(args.team.resolve()), str(args.opponent.resolve()), args.seed,
        args.side, args.candidate_kickoff, profile)
    payload = dict(formation="native default; custom formation hooks not called",
                   seed=args.seed, candidate_slot=args.side,
                   candidate_takes_kickoff=args.candidate_kickoff,
                   result=result, telemetry=telemetry, initial_roster=roster)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print("Native score:", result["score"], "ticks:", result["ticks"])


if __name__ == "__main__":
    main()
