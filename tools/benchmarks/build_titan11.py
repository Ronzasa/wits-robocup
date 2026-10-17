"""Assemble only independently validated TITAN-11 tactical features.

This writes an experimental candidate, never the active submission. A separate
fresh combined tournament must pass before any promotion. Sources are complete
single-file controllers; no generated helper modules are submission dependencies.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FEATURES={
    'passing':{'_link_option','_search_links','_transition_release'},
    'passing-r':{'_link_option','_search_links','_transition_release'},
    'movement':{'_role_support','_nominal_support','act'},
    'cover-r':{'_cover_shape','_baseline_cover_shape'},
    'lookahead':{'_touch_path'},
}
CHAMPION='5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def methods(text):
    tree=ast.parse(text)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
    lines=text.splitlines(keepends=True)
    return {n.name:(''.join(lines[n.lineno-1:n.end_lineno]),n)
            for n in cls.body if isinstance(n,ast.FunctionDef)}


def assemble(text,replacements,selected):
    lines=text.splitlines(keepends=True)
    original=methods(text)
    for name,(code,node) in sorted(original.items(),key=lambda x:x[1][1].lineno,reverse=True):
        if name in replacements:lines[node.lineno-1:node.end_lineno]=[replacements[name]]
    result=''.join(lines)
    for name,code in replacements.items():
        if name not in original:result+='\n'+code
    result=result[result.index('import math'):]
    header='''"""TITAN-11: validated progressive play with bounded physical verification.

Selected tactical experiments: %s.
Every new pass uses executable receiver trajectories and full opponent races.
Runtime changes reuse exact chase arithmetic and rule out impossible movement
witnesses before fallback simulation. Only math and the official SDK are used.
The goalkeeper and all unselected tactical hooks remain frozen-v10 behavior.
No timer, GC, scheduling, deadline or hidden-state controls are used.
"""\n''' % ', '.join(selected)
    return header+result.replace('version = "10.0-titan10b-r"','version = "11.0-titan11"',1)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--validation',type=Path,nargs='+',required=True)
    p.add_argument('--runtime',type=Path,default=ROOT/'experiments/titan-11-reach-runtime/team.py')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    args=p.parse_args()
    for path in (args.out,args.reference):
        if path.name!='team.py':p.error('The standalone source must be named team.py.')
        if path.exists() and digest(path)!=CHAMPION:p.error('Preserve existing challenger evidence; choose a new destination.')
    if args.manifest.exists():p.error('Preserve prior assembly metadata.')
    assert digest(ROOT/'champions/v10.0/team.py')==CHAMPION
    equivalent=args.runtime.read_text();common=(ROOT/'experiments/titan-11-runtime/team.py').read_text()
    selected=[];replacements={};records={}
    for run in args.validation:
        audit=json.loads((run/'gate-audit.json').read_text())
        for name,record in audit.items():
            if not record['all_gates_pass'] or record['status']!='PASS':continue
            assert name in FEATURES
            path=run/'sources'/name/'team.py'
            assert digest(path)==record['source']['sha256']
            feature=methods(path.read_text());base=methods(common)
            changed={n for n in base if ast.dump(feature[n][1],include_attributes=False)!=ast.dump(base[n][1],include_attributes=False)}
            if name in ('passing-r','cover-r'):
                runtime=methods(equivalent)
                assert ast.dump(feature['_pass_reachable'][1],include_attributes=False)==ast.dump(runtime['_pass_reachable'][1],include_attributes=False)
                changed.discard('_pass_reachable')
            assert changed==FEATURES[name]&set(base),(name,changed)
            for n in FEATURES[name]:
                assert n not in replacements
                replacements[n]=feature[n][0]
            selected.append(name);records[name]=record
    if not selected:p.error('No independently validated tactical feature: retain v10.0.')
    for path,base in ((args.out,equivalent),(args.reference,(ROOT/'champions/v10.0/team.py').read_text())):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(assemble(base,replacements,selected))
    manifest={'selected':selected,'individual_gate_records':records,
        'runtime_source':str(args.runtime),'runtime_sha256':digest(args.runtime),
        'candidate':str(args.out),'candidate_sha256':digest(args.out),
        'tactical_reference':str(args.reference),'reference_sha256':digest(args.reference),
        'status':'UNPROMOTED: requires new combined-seed validation'}
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='individual_gate_records'},indent=2))


if __name__=='__main__':main()
