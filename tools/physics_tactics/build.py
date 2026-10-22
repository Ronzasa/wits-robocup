"""Build isolated physics tactics from the frozen v10.0 champion."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = '5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6'
VARIANTS = {'ambush': (True, False, False),
            'wall-brake': (False, True, False),
            'rebound-shot': (False, False, True),
            'off': (False, False, False)}


def build(name):
    data = (ROOT / 'champions/v10.0/team.py').read_bytes()
    assert hashlib.sha256(data).hexdigest() == BASE_SHA
    code = data.decode()
    code = code.replace('version = "10.0-titan10b-r"',
                        'version = "physics-' + name + '-experimental"', 1)
    needle = '        self._ready = False\n'
    assert code.count(needle) == 1
    code = code.replace(needle, needle +
        '        self._physics_receive = None\n'
        '        self._physics_ambush = None\n'
        '        self._physics_pending = None\n'
        '        self._physics_events = []\n'
        '        self._physics_tick = -1\n'
        '        self._physics_targets = {}\n', 1)
    code = code.replace('    def act(self, obs):',
                        '    def _physics_v10_act(self, obs):', 1)
    needle = '        carrier = None\n        carrier_gap = None'
    assert code.count(needle) == 1
    code = code.replace(needle, '        self._physics_targets = targets\n\n' + needle, 1)
    code = code.replace('    def _choose_kick(self,p,bx,by,vx,vy,friends,opponents):',
                        '    def _physics_v10_kick(self,p,bx,by,vx,vy,friends,opponents):', 1)
    code = code.replace('def _pass_path(self, launch, origin=None, until=4.0):',
                        'def _pass_path(self, launch, origin=None, until=4.0, capture_motion=False):', 1)
    code = code.replace('if self.FIRST_TOUCH else None\n',
                        'if self.FIRST_TOUCH or capture_motion else None\n', 1)
    code = code.replace('def _carrier_contact(self, p, bx, by, sx, sy, movement):',
                        'def _carrier_contact(self, p, bx, by, sx, sy, movement, moved=None):', 1)
    needle = '        px, py = p[1] + pvx * self._dt, p[2] + pvy * self._dt\n'
    assert code.count(needle) == 1
    code = code.replace(needle, needle +
        '        if moved is not None:\n'
        '            moved.append((p[0],px,py,pvx,pvy))\n', 1)
    code += '\n' + (ROOT / 'tools/physics_tactics/tactics.pyfrag').read_text()
    for flag, value in zip(('PHYSICS_AMBUSH', 'PHYSICS_WALL_BRAKE', 'PHYSICS_REBOUND_SHOT'), VARIANTS[name]):
        code = code.replace('    ' + flag + ' = False', '    ' + flag + ' = ' + repr(value), 1)
    dest = ROOT / 'experiments' / ('physics-' + name) / 'team.py'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(code)
    return dest


if __name__ == '__main__':
    for name in VARIANTS:
        print(build(name).relative_to(ROOT))
