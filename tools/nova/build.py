"""Assemble a standalone independent policy plus audited low-level physics."""
import argparse,ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PHYSICS=['_target','_move','_pass_path','_pass_reachable','_pass_steps','_verified_intercept',
         '_receiver_rollout','_first_touch_safe','_kick_to_velocity','_requested_velocity','_carrier_contact','_goal_path']
CHAMPION='5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6'
DEFAULT_CONFIG=[12.,7.,12.,3.,2.5,.10,.65,1.]
DEFAULT_WEIGHTS=[4.5,1.5,1.6,.7,.6,-.5,-.7,1.4,-2.,.5,-1.2,.4]

def methods(source):
    cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef))
    lines=source.splitlines(True)
    return {n.name:''.join(lines[n.lineno-1:n.end_lineno]) for n in cls.body if isinstance(n,ast.FunctionDef)}

def build(parameters=None,joint=False):
    base=(ROOT/'my-team/team.py').read_text();assert hashlib.sha256(base.encode()).hexdigest()==CHAMPION
    params=parameters or {}
    template={k:'framework-'+k+'.pyfrag' for k in ('r4','r5','r6')}.get(params.get('framework'),'controller.pyfrag')
    physics=methods(base);source=(ROOT/'tools/nova'/template).read_text()
    source+='\n'.join(physics[name]+'\n' for name in PHYSICS)
    source=source.replace('    JOINT_MODEL=False','    JOINT_MODEL='+str(joint),1)
    source=source.replace('    CONFIG=(12.,7.,12.,3.,2.5,.10,.65,1.0)','    CONFIG='+repr(tuple(params.get('config',DEFAULT_CONFIG))),1)
    source=source.replace('    WEIGHTS=(4.5,1.5,1.6,.7,.6,-.5,-.7,1.4,-2.0,.5,-1.2,.4)','    WEIGHTS='+repr(tuple(params.get('weights',DEFAULT_WEIGHTS))),1)
    ast.parse(source);return source

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--joint',action='store_true');p.add_argument('--parameters',type=Path);a=p.parse_args()
    assert not a.out.exists();assert a.out.name=='team.py';a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(build(json.loads(a.parameters.read_text()) if a.parameters else None,a.joint))
    print(a.out,hashlib.sha256(a.out.read_bytes()).hexdigest())
if __name__=='__main__':main()
