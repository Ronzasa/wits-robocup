"""Reproduce one champion-hunt fixture through the frozen native match driver.

Provide the complete official SDK through PYTHONPATH or an installed wheel.
This uses native default rosters, 2,400 ticks and the official 20 ms deadline.
It does not call optional initial_formation hooks.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate", type=Path,
        default=ROOT / "experiments/champion-hunt-adaptive/team.py")
    parser.add_argument(
        "--opponent", type=Path,
        default=ROOT / "experiments/champion-candidate-review/uploaded/team.py")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--side", type=int, choices=(0, 1), default=0)
    parser.add_argument(
        "--own-kickoff", action=argparse.BooleanOptionalAction, default=True,
        help="Whether the candidate takes kickoff (default: yes).")
    parser.add_argument("--config", type=Path, default=ROOT / "configs/default.toml")
    parser.add_argument(
        "--output", type=Path,
        help="Write JSON to this new file; otherwise print JSON to stdout.")
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error("Output already exists; retain earlier evidence.")
    for label, path in (("candidate", args.candidate),
                        ("opponent", args.opponent), ("config", args.config)):
        if not path.is_file():
            parser.error(f"Missing {label} file: {path}")

    # Lazy import keeps --help usable before installing the native SDK.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from default_roster import native_match

    registration = dict(
        config_path=str(args.config.resolve()),
        config_hash="372990895c7eca2a", engine_version="0.1.0")
    source_hashes = {
        label: hashlib.sha256(path.read_bytes()).hexdigest()
        for label, path in (("candidate", args.candidate),
                            ("opponent", args.opponent))
    }
    result, telemetry, roster = native_match(
        str(args.candidate.resolve()), str(args.opponent.resolve()),
        args.seed, args.side, args.own_kickoff, registration)
    payload = dict(
        formation="native default; custom formation hooks not called",
        seed=args.seed, candidate_slot=args.side,
        candidate_takes_kickoff=args.own_kickoff,
        source_sha256=source_hashes, registration=registration,
        result=result, telemetry=telemetry, initial_roster=roster)
    encoded = json.dumps(payload, indent=2) + "\n"
    if args.output is None:
        print(encoded, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation also protects evidence created while the match ran.
        with args.output.open("x") as output:
            output.write(encoded)


if __name__ == "__main__":
    main()
