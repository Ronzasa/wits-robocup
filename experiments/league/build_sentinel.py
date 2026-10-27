"""Isolate predictive goal coverage with the observed-gap shot search."""
from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / "gaps/team.py").read_text(encoding="utf-8")
source = source.replace('name = "MONSTER GAPS"', 'name = "MONSTER SENTINEL"')
source = source.replace("version = 'league-observed-gaps-1'", "version = 'league-predictive-cover-1'")
source = source.replace('PREDICT_POST = False', 'PREDICT_POST = True')
target = root / "sentinel/team.py"
target.parent.mkdir(parents=True, exist_ok=True)
if target.exists() and target.read_text(encoding="utf-8") != source:
    raise RuntimeError("Existing candidate differs")
target.write_text(source, encoding="utf-8")
print(target)
