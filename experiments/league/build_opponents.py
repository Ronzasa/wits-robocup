"""Reproduce the independent stress opponent variants before league testing."""
from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / "opponents/pressure/team.py").read_text(encoding="utf-8")
target = root / "opponents/counter/team.py"
text = source.replace("Pressure", "Counter").replace("BACKS = 1", "BACKS = 3").replace("PRESS = 2", "PRESS = 1")
target.parent.mkdir(parents=True, exist_ok=True)
if target.exists() and target.read_text(encoding="utf-8") != text:
    raise RuntimeError("Refusing to overwrite a different opponent")
target.write_text(text, encoding="utf-8")
print(target)
