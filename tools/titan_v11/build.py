"""Assemble isolated movement tactics without editing frozen v10."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[2]
CHAMPION = '5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6'
FLAGS = ('PASSING_LANE_ARCHITECT', 'COUNTERATTACK_FIREWALL')


def build(name, enabled=()):
    original = (ROOT/'my-team/team.py').read_bytes()
    assert hashlib.sha256(original).hexdigest() == CHAMPION
    assert set(enabled) <= set(FLAGS)
    code = original.decode()
    needle = '        carrier = None\n        carrier_gap = None'
    assert code.count(needle) == 1
    code = code.replace(needle, '''        if self.PASSING_LANE_ARCHITECT or self.COUNTERATTACK_FIREWALL:
            self._v11_targets(obs, friends, opponents, chaser, targets,
                              protected, receive_target, actions)

''' + needle)
    finish = '        return actions\n\n    def _option_path'
    assert code.count(finish) == 1
    code = code.replace(finish, '        if self.PASSING_LANE_ARCHITECT or self.COUNTERATTACK_FIREWALL:\n            self._v11_executions(actions)\n' + finish)
    code += '\n' + (ROOT/'tools/titan_v11/tactics.pyfrag').read_text()
    for flag in FLAGS:
        code = code.replace('    '+flag+' = False', '    '+flag+' = '+str(flag in enabled))
    dest = ROOT/'experiments'/name/'team.py'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(code)
    return dest


if __name__ == '__main__':
    build('titan-v11-off')
    build('titan-v11-architect', FLAGS[:1])
    build('titan-v11-firewall', FLAGS[1:])
