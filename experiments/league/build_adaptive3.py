"""Assemble the wall-only portfolio; existing prototypes remain immutable."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
source = (ROOT / "adaptive2/team.py").read_text(encoding="utf-8")
corner = (ROOT / "gaps2/team.py").read_text(encoding="utf-8")
corner = corner.replace("class Monster(TeamController):", "class _CounterPolicy:")
counter_start = source.index('"""MONSTER: independent predictive pressure and close-control soccer.')
wrapper_start = source.index("\nclass LeagueAdaptive(TeamController):", counter_start)
wrapper = source[wrapper_start:]
wrapper = wrapper.replace('version = "observation-portfolio-v2"', 'version = "observation-portfolio-v3"')
wrapper = wrapper.replace("    Policy changes happen at restarts or after a persistent opponent wall.",
                          "    A policy change requires a persistent observed opponent goal-mouth wall.")
wrapper = wrapper.replace("        self._last_score = None\n", "")
wrapper = wrapper.replace("        score = tuple(obs.score)\n", "")
wrapper = wrapper.replace("        score_changed = self._last_score is not None and score != self._last_score\n", "")
wrapper = wrapper.replace("            # At an adverse restart the whole team can rebuild cover together.\n", "")
wrapper = wrapper.replace("            if self._wall_ticks >= self.WALL_CONFIRM_TICKS or (score_changed and score[0] < score[1]):",
                          "            if self._wall_ticks >= self.WALL_CONFIRM_TICKS:")
wrapper = wrapper.replace("        self._last_score = score\n", "")
result = source[:counter_start]+corner+wrapper
if len(result.encode("utf-8")) >= 256*1024:
    raise RuntimeError("Portfolio exceeds the course source size limit")
target = ROOT / "adaptive3/team.py"
target.parent.mkdir(parents=True, exist_ok=True)
if target.exists() and target.read_text(encoding="utf-8") != result:
    raise RuntimeError("Existing adaptive3 candidate differs; choose a new version")
target.write_text(result, encoding="utf-8")
print(str(target)+" ("+str(len(result.encode("utf-8")))+" bytes)")
