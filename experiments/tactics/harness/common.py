"""Shared helpers: locate the simulator SDK, opponent specs, paired runner.

The simulator is never modified. The SDK is imported from the first of:
  $SOCCER_SDK, <repo>/student-sdk (if its engine binary is present),
  /home/claude/platform/soccer-student-0.1.0/student-sdk (identical engine; see HASHES.txt).
"""
import hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TACTICS = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(TACTICS))
RESULTS = os.path.join(TACTICS, "results")

def _sdk_path():
    cands = [os.environ.get("SOCCER_SDK"),
             os.path.join(REPO, "student-sdk"),
             "/home/claude/platform/soccer-student-0.1.0/student-sdk"]
    for c in cands:
        if c and os.path.exists(os.path.join(c, "soccer", "_engine.abi3.so")):
            return c
    raise RuntimeError("no SDK with an engine binary found")

SDK = _sdk_path()
if SDK not in sys.path:
    sys.path.insert(0, SDK)
import soccer  # noqa: E402

def engine_hash():
    with open(os.path.join(SDK, "soccer", "_engine.abi3.so"), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

OPP = os.path.join(TACTICS, "opponents")
OPPONENTS = {
    "champion_original": os.path.join(OPP, "champion_original.py"),
    "lock_no_breaker": os.path.join(OPP, "lock_no_breaker.py"),
    "press_formation": os.path.join(OPP, "champion_press_formation.py"),
    "bus_wall": os.path.join(OPP, "bus_wall.py"),
    "dribbler": os.path.join(OPP, "dribbler.py"),
}
BUILTINS = ["do_nothing", "random_legal", "ball_chaser", "structured_attack",
            "man_marking", "balanced", "possession", "tactical"]

def spec(name):
    return OPPONENTS.get(name, name)

def points(goals_for, goals_against):
    return 3 if goals_for > goals_against else 1 if goals_for == goals_against else 0
