"""Fix optional debug annotation without overwriting the archived prototype."""
from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / "adaptive/team.py").read_text(encoding="utf-8")
source = source.replace('version = "observation-portfolio-v1"', 'version = "observation-portfolio-v2"')
source = source.replace('actions.debug["text"] = "League: covered counter and wall attack"',
                        'actions.annotate(text="League: covered counter and wall attack")')
source = source.replace('actions.debug["text"] = "League: open build-up, passing and pressure"',
                        'actions.annotate(text="League: open build-up, passing and pressure")')
target = root / "adaptive2/team.py"
target.parent.mkdir(parents=True, exist_ok=True)
if target.exists() and target.read_text(encoding="utf-8") != source:
    raise RuntimeError("Existing candidate differs")
target.write_text(source, encoding="utf-8")
print(target)
