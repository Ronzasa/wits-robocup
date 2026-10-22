"""Assemble isolated scouting hypotheses around frozen TITAN-X Trap."""
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE='90a7dcba55da2605c59b4cd08d839d94e20a68e006bf52acf9305d01efda88bb'
VARIANTS={'keeper6':(6.,False,False),'keeper10':(10.,False,False),
          'keeper14':(14.,False,False),'outlet':(0.,True,False),'cutback':(0.,False,True)}

def build(name,settings):
    data=(ROOT/'experiments/elite-scout-baseline/team.py').read_bytes()
    assert hashlib.sha256(data).hexdigest()==BASE
    code=data.decode().replace('version = "titan-x-experimental"','version = "elite-scout-experimental"',1)
    code=code.replace('        self._press_last_ball_holder = None\n',
                      '        self._press_last_ball_holder = None\n        self._scout_outlet = None\n',1)
    code=code.replace('        keeper_x = self._left + 2.2',
                      '        keeper_x = self._scout_keeper_x(obs,keeper) if self.SCOUT_KEEPER_CAP else self._left + 2.2',1)
    code=code.replace('        keeper_target = (keeper_x, _clip(keeper_y, -self._mouth, self._mouth))',
                      '        keeper_limit = self._scout_keeper_limit(obs) if self.SCOUT_KEEPER_CAP else self._mouth\n'
                      '        keeper_target = (keeper_x, _clip(keeper_y, -keeper_limit, keeper_limit))',1)
    needle='        carrier = None\n        carrier_gap = None'
    assert code.count(needle)==1
    code=code.replace(needle,
        '        if self.SCOUT_OUTLET or self.SCOUT_CUTBACK:\n'
        '            self._scout_support(obs,friends,opponents,chaser,races,enemy_eta,targets,protected)\n\n'+needle)
    code+='\n'+(ROOT/'tools/elite_scout/hypotheses.pyfrag').read_text()
    for flag,value in zip(('SCOUT_KEEPER_CAP','SCOUT_OUTLET','SCOUT_CUTBACK'),settings):
        code=code.replace('    '+flag+' = '+('0.0' if flag=='SCOUT_KEEPER_CAP' else 'False'),
                          '    '+flag+' = '+repr(value),1)
    dest=ROOT/'experiments'/('elite-scout-'+name)/'team.py'
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(code)
    return dest

def main():
    build('off',(0.,False,False))
    for name,settings in VARIANTS.items():build(name,settings)

if __name__=='__main__':main()
