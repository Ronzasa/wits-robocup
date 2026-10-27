"""Fix projected guard spacing in a separate, immutable ray-cover candidate."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
source = (ROOT / "ray_cover/team.py").read_text(encoding="utf-8")
old = '''                centre = by*clip(depth/distance,0.0,0.4)
                aim = (self.left+depth,clip(centre+slots[i]*ratio,-self.goal-1.5,self.goal+1.5))'''
new = '''                centre = by*clip(depth/distance,0.0,0.4)
                limit = self.goal+1.5
                # Shift the whole screen inside the bounds. Clipping each
                # guard separately collapses their spacing for a wide ball.
                centre = clip(centre,-limit+5.4*ratio,limit-5.4*ratio)
                aim = (self.left+depth,centre+slots[i]*ratio)'''
if source.count(old) != 1:
    raise RuntimeError("Expected one original projected screen")
source = source.replace(old, new)
source = source.replace('name = "MONSTER RAY COVER"', 'name = "MONSTER RAY COVER2"')
source = source.replace("version = 'league-ray-cover-1'", "version = 'league-ray-cover-2'")
target = ROOT / "ray_cover2/team.py"
target.parent.mkdir(parents=True, exist_ok=True)
contents = source.encode("utf-8")
if target.exists():
    if target.read_bytes() != contents:
        raise RuntimeError("Existing ray_cover2 differs; choose a new revision")
else:
    with target.open("xb") as stream:
        stream.write(contents)
print(target)
