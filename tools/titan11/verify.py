"""Replay public native observations: runtime equivalence and protected-role invariants."""
import argparse,gzip,hashlib,importlib.util,json,sys
from pathlib import Path
from types import SimpleNamespace as S
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'student-sdk'));sys.path.insert(0,str(ROOT/'tools/titan11'))
from soccer import SoccerEnv
from build import build,FLAGS
import types

def mod(source):
    m=types.ModuleType('shadow_titan');exec(compile(source,'team.py','exec'),m.__dict__);return m

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--traces',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('Preserve prior evidence.')
    games=json.load(gzip.open(a.traces,'rt'));base=mod((ROOT/'my-team/team.py').read_text());runtime=mod(build([]));mapping={'predictive':'predictive','coordinated':'coordinated','finishing':'elite-finishing','defence':'threat-defence','playbooks':'playbooks','learning':'learned-value'};variants={f:mod((ROOT/('experiments/titan-11-'+mapping[f]+'/team.py')).read_text()) for f in FLAGS}
    same=0;changed={f:0 for f in FLAGS};features={f:0 for f in FLAGS};violations=[]
    with SoccerEnv(config_path=str(ROOT/'configs/default.toml')) as env:field=env.field
    cases=[]
    for game in games:
        b=base.Guardiola2011();r=runtime.Guardiola2011();policies={f:m.Guardiola2011() for f,m in variants.items()}
        for raw in game['trace']:
            def player(q):return S(id=q[0],position=q[1:3],velocity=q[3:5],kick_cooldown_ticks=q[5])
            kickers=set(raw['kickers']);holder=raw['holder'];obs=S(tick=raw['tick'],score=tuple(raw['score']),field=field,my_players=[player(q) for q in raw['friends']],opponents=[player(q) for q in raw['opponents']],can_kick=kickers.__contains__,ball=S(position=raw['ball'][:2],velocity=raw['ball'][2:],controlling_player=holder,controlling_team=None if holder is None else int(holder>=5),last_touch=raw['last_touch']))
            before=b.act(obs);control=r.act(obs)
            fingerprint=lambda action:{k:v.as_dict() for k,v in action.players.items()}
            assert fingerprint(before)==fingerprint(control),(game['style'],game['seed'],raw['tick'],'runtime divergence')
            same+=1
            for f,c in policies.items():
                action=c.act(obs);different=fingerprint(before)!=fingerprint(action);changed[f]+=different
                features[f]+=int(getattr(c,'_ti_selected','v10')!='v10' or bool(c._ti_defence_ids))
                # Movement-only coordination and defence must preserve keeper
                # safeguards. Fresh passing may deliberately change its kick.
                if f in ('coordinated','defence') and before.players[0].kick_direction is None:
                    if action.players[0].as_dict()!=before.players[0].as_dict():violations.append((f,game['seed'],raw['tick'],'keeper'))
                assert c._ti_rollouts<=3
                if different and sum(x['feature']==f for x in cases)<3:
                    cases.append({'feature':f,'style':game['style'],'seed':game['seed'],'side':game['side'],'kickoff':game['kickoff'],'frame':raw,'baseline_action':fingerprint(before),'challenger_action':fingerprint(action)})
    report={'runtime_identical_decisions':same,'feature_changed_shared_observations':changed,'selected_or_defence_ticks':features,'violations':violations,'scope':'Shared public observations, not on-policy match strength or timing. Future actions evolve internally on recorded observations.','cases':cases}
    a.out.write_text(json.dumps(report,indent=2)+'\n');assert not violations,violations
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
if __name__=='__main__':main()
