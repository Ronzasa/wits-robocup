"""Build independent MONSTER parameter variants without touching TITAN."""
import argparse
import ast
import re
from pathlib import Path

LAB = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument("name")
    p.add_argument("--base", default="monster/team.py")
    p.add_argument("--set", action="append", default=[])
    a = p.parse_args()
    if not re.fullmatch("[a-z0-9_-]+", a.name):
        raise ValueError("Use a simple experiment name")
    source = (LAB / a.base).read_text()
    allowed = {"PRESSERS", "CARRY_SPEED", "SHOT_MARGIN", "LOCK_LEAD", "LOCK_DEPTH", "FORMATION", "WIDTH", "PASS_WEIGHT", "SWEEP", "DEFENSE", "KEEPER_DEPTH", "DUELS", "TWIN_KEEPERS", "SHELL", "SHELL_DEPTH", "SHELL_RELEASE", "SHELL_BANK", "SHELL_LOCK_FIVE", "KEEPER_MODEL", "FIXED_OUTLET", "OUTLET_X", "ADAPTIVE_POSTS"}
    allowed.update({"POST_MAX", "PREDICT_POST", "SUPPORT", "SHOT_FIRST", "AIM_DUEL", "SMART_CLEAR",
                    "COVER_SHIFT", "BREAKAWAY_TOUCH", "WALL_SHOT_MARGIN", "OUTLET_Y", "MARK_WINDOW"})
    for setting in a.set:
        key, raw = setting.split("=", 1)
        if key not in allowed:
            raise ValueError(key)
        value = ast.literal_eval(raw)
        source, count = re.subn(r"(?m)^    "+key+r" = .*?$", "    "+key+" = "+repr(value), source)
        if count!=1:
            raise RuntimeError("Setting not found exactly once: "+key)
    source = re.sub(r'(?m)^    version = .*?$', '    version = '+repr(a.name), source)
    target = LAB / "pool" / a.name / "team.py"
    if target.exists():
        raise RuntimeError("Keep variants immutable; use a new name")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
