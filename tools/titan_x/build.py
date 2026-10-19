"""Offline single-file assembly. The frozen v10 source is never edited."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLAGS = ('KEEPER_POWER_PLAY', 'GOALKEEPER_TRAP', 'PINBALL_SLINGSHOT', 'COOLDOWN_AMBUSH')
CHAMPION = '5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6'

def build(name, enabled=()):
    original = (ROOT / 'my-team/team.py').read_bytes()
    assert hashlib.sha256(original).hexdigest() == CHAMPION
    assert set(enabled) <= set(FLAGS)
    code = original.decode()
    code = code.replace('version = "10.0-titan10b-r"','version = "titan-x-experimental"',1)
    code = code.replace('        self._press_last_ball_holder = None\n',
                        '        self._press_last_ball_holder = None\n        self._x_reset()\n', 1)
    code = code.replace('    def act(self, obs):', '    def _v10_act(self, obs):', 1)
    code = code.replace('    def _choose_kick(self,p,bx,by,vx,vy,friends,opponents):',
                        '    def _v10_choose_kick(self,p,bx,by,vx,vy,friends,opponents):', 1)
    # Only an activated power play may name the keeper as receiver. Ordinary
    # outfield role assignment and the underlying goalkeeper remain intact.
    code = code.replace('next((p for p in outfield if p[0] == recipient), None)',
                        'next((p for p in friends if p[0] == recipient and (p[0] != 0 or self._x_power_state == "active")), None)')
    code = code.replace('next((q for q in outfield if q[0]==recipient),None)',
                        'next((q for q in friends if q[0]==recipient and (q[0]!=0 or self._x_power_state=="active")),None)')
    code = code.replace('next(p for p in outfield if p[0] == recipient)',
                        'next(p for p in friends if p[0] == recipient)')
    code = code.replace('if (self.FOLLOW_RECEIVER and not protected',
                        'if ((self.FOLLOW_RECEIVER or (self._x_reception is not None and self._x_reception[0]==p[0])) and not protected')
    code += '\n' + (ROOT / 'tools/titan_x/tactics.pyfrag').read_text()
    for flag in FLAGS:
        code = code.replace('    ' + flag + ' = False', '    ' + flag + ' = ' + str(flag in enabled))
    dest = ROOT / 'experiments' / name / 'team.py'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(code)
    return dest

def main():
    build('titan-x')
    # Archived pinball/ambush standalones retain their original source. This
    # development round builds only the two authorized goalkeeper candidates.
    for name, flag in zip(('titan-x-power', 'titan-x-trap'), FLAGS[:2]):
        build(name, (flag,))

if __name__ == '__main__':
    main()
