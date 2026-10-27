"""Build an isolated geometric four-guard screen from public ball geometry."""
from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / "gaps2/team.py").read_text(encoding="utf-8")
source = source.replace('name = "MONSTER CORNER"', 'name = "MONSTER RAY COVER"')
source = source.replace("version = 'league-corner-duel-1'", "version = 'league-ray-cover-1'")
marker = '            if self.COVER_SHIFT and i<4 and abs(by)>6 and bx<self.left+15:'
assert source.count(marker) == 1
source = source.replace(marker, '''            # Project the visible goal mouth onto the covering line. Close
            # attackers see a narrower interval there than at the goal itself;
            # retaining the full fixed width leaves avoidable body-size gaps.
            # The lower spacing bound keeps teammates from overlapping.
            if i<4 and self.left+depth+1.0 < bx < self.left+25.0:
                distance = max(3.0,bx-self.left)
                ratio = clip((bx-self.left-depth)/distance,0.60,1.0)
                centre = by*clip(depth/distance,0.0,0.4)
                aim = (self.left+depth,clip(centre+slots[i]*ratio,-self.goal-1.5,self.goal+1.5))
''' + marker)
target = root / "ray_cover/team.py"
target.parent.mkdir(parents=True, exist_ok=True)
if target.exists() and target.read_text(encoding="utf-8") != source:
    raise RuntimeError("Existing candidate differs")
target.write_text(source, encoding="utf-8")
print(target)
