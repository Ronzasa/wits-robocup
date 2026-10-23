"""Exact action/state comparison of the runtime-only repair on public traces."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace as S
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'student-sdk'))
from soccer import SoccerEnv


def load(path):
    m=types.ModuleType('repair_verification');exec(compile(path.read_text(),'team.py','exec'),m.__dict__)
    return m


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--traces',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();assert not a.out.exists()
    sources=[ROOT/'experiments/titan-11/team.py',ROOT/'experiments/titan-11-r-runtime/team.py']
    modules=[load(path) for path in sources];counts=[0,0];decisions=0
    with SoccerEnv(config_path=str(ROOT/'configs/default.toml')) as env:field=env.field
    for game in json.load(gzip.open(a.traces,'rt')):
        policies=[m.Guardiola2011() for m in modules]
        for i,c in enumerate(policies):
            original=c._eta
            def eta(*args,i=i,original=original):
                counts[i]+=1
                return original(*args)
            c._eta=eta
        for raw in game['trace']:
            def player(q):return S(id=q[0],position=q[1:3],velocity=q[3:5],kick_cooldown_ticks=q[5])
            obs=S(tick=raw['tick'],score=tuple(raw['score']),field=field,
                my_players=[player(q) for q in raw['friends']],opponents=[player(q) for q in raw['opponents']],
                can_kick=set(raw['kickers']).__contains__,ball=S(position=raw['ball'][:2],velocity=raw['ball'][2:],
                controlling_player=raw['holder'],controlling_team=0 if raw['features'][3] else 1 if raw['features'][4] else None,last_touch=raw['last_touch']))
            actions=[{k:v.as_dict() for k,v in c.act(obs).players.items()} for c in policies]
            assert actions[0]==actions[1],(game['seed'],raw['tick'],'action divergence')
            for key in ('_receive_plan','_receive_aim','_bank_receive','_chaser','_ti_selected'):
                assert getattr(policies[0],key)==getattr(policies[1],key),(game['seed'],raw['tick'],key)
            decisions+=1
    report={'identical_decisions_and_reception_states':decisions,'eta_calls':dict(zip(('original','runtime'),counts)),
        'eta_calls_avoided':counts[0]-counts[1],
        'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'scope':'Exact shared public observations. Timing and on-policy match qualification are separate.'}
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
