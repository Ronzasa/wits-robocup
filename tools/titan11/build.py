"""Build standalone isolated challengers from the byte-frozen v10.0 source."""
import argparse,ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CHAMPION='5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6'
FLAGS=['predictive','coordinated','finishing','defence','playbooks','learning']

def method(text,name):
    cls=next(n for n in ast.parse(text).body if isinstance(n,ast.ClassDef));node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=text.splitlines(True);return node,''.join(lines[node.lineno-1:node.end_lineno])

def build(flags,params=None,runtime=True):
    base=(ROOT/'my-team/team.py').read_text();assert hashlib.sha256(base.encode()).hexdigest()==CHAMPION
    config={'risk':1.,'width':12.,'switch':.18,'value_scale':.45,'value_weights':[0.]*8,'shot_weights':[],'open_width':.18,'through_lead':1.,'shoot_bias':0.,'shot_scale':1.,'pressure':1.,'transition_aggression':1.,'rest_gap':0.,'space_gain':.065}
    config.update(params or {})
    if runtime:
        reference=(ROOT/'tools/titan11/reach_reference.pyfrag').read_text()
        node,_=method(base,'_pass_reachable');_,code=method(reference,'_pass_reachable');lines=base.splitlines(True);lines[node.lineno-1:node.end_lineno]=[code];base=''.join(lines)
    for name in ('_choose_kick','_link_option','_shot_option','_bank_release','_endwall_link','initial_formation'):
        base=base.replace('    def '+name+'(', '    def _v10'+('_' if not name.startswith('_') else '')+name+'(',1)
    base=base.replace('        self._enemy_cooldowns = {}','''        self._ti_obs = None
        self._ti_options = None
        self._ti_targets_now = {}
        self._ti_tick = -1
        self._ti_score = None
        self._ti_owner = None
        self._ti_secure = False
        self._ti_regain = -10000
        self._ti_loss = -10000
        self._ti_sequence = None
        self._ti_rebound = None
        self._ti_third = None
        self._ti_defence_ids = ()
        self._ti_rollouts = 0
        self._ti_shot_checks = 0
        self._enemy_cooldowns = {}''',1)
    base=base.replace('        actions = TeamAction(debug={"roles": self.PLAYER_ROLES})','        self._ti_observe(obs)\n        actions = TeamAction(debug={"roles": self.PLAYER_ROLES})',1)
    base=base.replace('        carrier = None\n','        self._ti_targets(obs,protected,friends,opponents,chaser,targets,attack)\n\n        carrier = None\n',1)
    flags=set(flags);assert flags<=set(FLAGS)
    attrs=''.join('    TI_'+f.upper()+' = '+str(f in flags)+'\n' for f in FLAGS)
    attrs+=''.join('    TI_'+k.upper()+' = '+repr(tuple(v) if isinstance(v,list) else v)+'\n' for k,v in config.items())
    base=base.replace('    version = "10.0-titan10b-r"','    version = "11.0-tactical-intelligence-experimental"\n'+attrs,1)
    base='"""Unpromoted TITAN-11 tactical intelligence; frozen v10.0 remains active.\nStandalone, bounded public-physics rollouts and offline fitted parameters.\n"""\n'+base[base.index('import math'):]
    fragment=(ROOT/'tools/titan11/components.pyfrag').read_text()
    if config.get('finishing_revision')==2:
        fragment=fragment.replace('        if self.TI_FINISHING and bx>self._right-32.:','        if self.TI_FINISHING:self._ti_finesse(p,bx,by,vx,vy,opponents)\n        if self.TI_FINISHING and bx>self._right-32.:')
        fragment+='\n'+(ROOT/'tools/titan11/finishing_power.pyfrag').read_text()
    if config.get('coordination_revision')==2:
        fragment=fragment.replace('        if not (self._ti_secure or follow):return', '        pending=self._receive_plan is not None and obs.ball.last_touch==self._receive_plan[1]\n        if not (self._ti_secure or follow or pending):return')
        fragment=fragment.replace('        if best is None or best[1][1]==fallback:\n', '        if best is None or best[1][1]==fallback:\n            if best is not None and best[2][0]==\'shot\':self._ti_rebound=(self._right-8.,best[2][1],self._ti_tick+20)\n')
    base+='\n'+fragment
    ast.parse(base);return base

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--features',nargs='*',choices=FLAGS,default=[]);p.add_argument('--parameters',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--no-runtime',action='store_true');a=p.parse_args()
    if a.out.exists():p.error('Preserve source snapshots; choose a new destination.')
    assert a.out.name=='team.py';a.out.parent.mkdir(parents=True,exist_ok=True)
    params=json.loads(a.parameters.read_text()) if a.parameters else None
    a.out.write_text(build(a.features,params,not a.no_runtime));print(str(a.out),hashlib.sha256(a.out.read_bytes()).hexdigest())
if __name__=='__main__':main()
