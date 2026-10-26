"""Create small, separate Blue Team patches. Never writes the validated team."""
from pathlib import Path
import hashlib

LAB = Path(__file__).resolve().parent
source = (LAB/"frozen-titan/team.py").read_text(encoding="utf-8")
assert hashlib.sha256((LAB/"frozen-titan/team.py").read_bytes()).hexdigest()=="5c73068b5e574093e9e1afce972ff8b3546b484c103505c9e79d80772ac6299d"

entry = """    def act(self, obs):
        lead = obs.score[0] - obs.score[1]
        eligible = lead == 1 or (lead == 0 and obs.score[0] > 0)
"""
guarded = """    def act(self, obs):
        # The siege path bypasses normal-play kickoff protection. Hold legal
        # kickoff positions until the opponent actually moves its centre ball.
        if obs.ball.controlling_team == 1 and math.hypot(*obs.ball.position) < 0.5 and math.hypot(*obs.ball.velocity) < 0.15:
            return TeamAction({p.id: PlayerAction() for p in obs.my_players}, debug={'text': 'Blue: protect opponent restart'})
        lead = obs.score[0] - obs.score[1]
        eligible = lead == 1 or (lead == 0 and obs.score[0] > 0)
"""
slots = """        for index, p in enumerate(free):
            targets[p[0]] = (min(34.0, max(0.0, bx - 12.0)), (-7.0, 0.0, 7.0)[index])
        gx = self._left + 1.3
"""
reserved = """        for index, p in enumerate(free):
            targets[p[0]] = (min(34.0, max(0.0, bx - 12.0)), (-7.0, 0.0, 7.0)[index])
        # A wall can have a distant outlet. Keep one supporting player goal-side
        # of that observed outlet instead of leaving every runner ahead of it.
        outlets = [q for q in obs.opponents if q.position[0] < self._right - 10.0]
        if outlets and free:
            outlet = min(outlets, key=lambda q: q.position[0])
            mark = self._target(outlet.position[0] - 3.0, outlet.position[1])
            reserve = min(free, key=lambda p: self._eta(p, *mark))
            targets[reserve[0]] = mark
        gx = self._left + 1.3
"""
assert source.count(entry)==1 and source.count(slots)==1
for name, kickoff, cover in (("blue-a-kickoff",True,False),("blue-b-reserve",False,True),("blue-c-combined",True,True)):
    text = source.replace(entry,guarded) if kickoff else source
    if cover:
        text = text.replace(slots,reserved)
    text = text.replace("version = 'champion-hunt-adaptive-1.3'", "version = '"+name+"-0.1'")
    text = text.replace("name = 'TITAN Adaptive Counter'", "name = 'TITAN "+name+"'")
    text = "# Experimental Blue Team candidate. The validated TITAN is unchanged.\n"+text
    target = LAB/"blue-pool"/name/"team.py"
    if target.exists():
        raise RuntimeError("Do not overwrite an experiment: "+name)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(text,encoding="utf-8")
    print(target)
