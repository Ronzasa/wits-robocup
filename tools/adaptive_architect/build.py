"""Build adaptive Architect while preserving frozen v10 and original Architect."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
CHAMPION='5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6'


def build():
    base=(ROOT/'my-team/team.py').read_bytes()
    assert hashlib.sha256(base).hexdigest()==CHAMPION
    old=json.loads((ROOT/'docs/titan-v11/registration.json').read_text())['sources']['architect']
    assert hashlib.sha256((ROOT/old['path']).read_bytes()).hexdigest()==old['sha256']
    code=base.decode()
    needle='        carrier = None\n        carrier_gap = None'
    assert code.count(needle)==1
    code=code.replace(needle,'''        if self.PASSING_LANE_ARCHITECT:
            self._v11_targets(obs, friends, opponents, chaser, targets,
                              protected, receive_target, actions)

'''+needle)
    finish='        return actions\n\n    def _option_path'
    assert code.count(finish)==1
    code=code.replace(finish,'        if self.PASSING_LANE_ARCHITECT:\n            self._v11_executions(actions)\n'+finish)
    fragment=(ROOT/'tools/titan_v11/tactics.pyfrag').read_text()
    fragment=fragment.replace('    PASSING_LANE_ARCHITECT = False','    PASSING_LANE_ARCHITECT = True')
    fragment=fragment.replace('    def _v11_targets(', '    def _original_architect_targets(')
    fragment=fragment.replace('    def _v11_executions(', '    def _original_architect_executions(')
    code+='\n'+fragment+'\n'+(ROOT/'tools/adaptive_architect/tactics.pyfrag').read_text()
    dest=ROOT/'experiments/titan-adaptive-architect/team.py'
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(code)
    return dest


if __name__=='__main__':build()
