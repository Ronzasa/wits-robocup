"""Offline assembly of the observation-driven league portfolio."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "team.py"
titan = (ROOT / "my-team/team.py").read_text(encoding="utf-8")
monster = (ROOT / "experiments/red-team/monster/team.py").read_text(encoding="utf-8")
titan = titan.replace("class AdaptiveChampion(TeamController):", "class _TitanPolicy:")
monster = monster.replace("class Monster(TeamController):", "class _CounterPolicy:")

wrapper = '''

class LeagueAdaptive(TeamController):
    """Choose open build-up or four-cover counters from observed play.

    Policy changes happen at restarts or after a persistent opponent wall.
    Only one policy computes actions, so searches do not share a tick budget.
    """
    name = "LEAGUE Adaptive"
    version = "observation-portfolio-v1"
    WALL_CONFIRM_TICKS = 12

    def __init__(self):
        self._open = _TitanPolicy()
        self._counter = _CounterPolicy()
        self.reset(0)

    def initial_formation(self, field):
        return self._open.initial_formation(field)

    def reset(self, seed):
        self._open.reset(seed)
        self._counter.reset(seed)
        self._counter_mode = False
        self._wall_ticks = 0
        self._last_score = None

    def act(self, obs):
        score = tuple(obs.score)
        goal = obs.field.opponent_goal[0]
        mouth = obs.field.goal_width * 0.5
        dense_wall = sum(q.position[0] > goal-4.0 and abs(q.position[1]) < mouth+1.0
                         for q in obs.opponents) >= 4
        self._wall_ticks = self._wall_ticks+1 if dense_wall else 0
        score_changed = self._last_score is not None and score != self._last_score
        if not self._counter_mode:
            # A sustained goal-mouth wall calls for the tested counter policy.
            # At an adverse restart the whole team can rebuild cover together.
            if self._wall_ticks >= self.WALL_CONFIRM_TICKS or (score_changed and score[0] < score[1]):
                self._counter_mode = True
                self._counter.reset(0)
        self._last_score = score
        if self._counter_mode:
            actions = self._counter.act(obs)
            actions.debug["text"] = "League: covered counter and wall attack"
        else:
            actions = self._open.act(obs)
            actions.debug["text"] = "League: open build-up, passing and pressure"
        return actions
'''

OUT.write_text(titan + "\n\n" + monster + wrapper, encoding="utf-8")
print(OUT.relative_to(ROOT))
