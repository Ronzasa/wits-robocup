"""Interleaved runtime equivalence on the 40 frozen slow public decisions.

Diagnostic only: no tournament points or controller deadline controls. Restore
identical public states, rotate source order, compare actions/non-cache state,
and report CPU and wall times with default garbage collection.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace as S

from profile_titan11 import ROOT,decode,restore,timing


def load(path,index):
    spec=importlib.util.spec_from_file_location('runtime_compare_'+str(index),path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.Guardiola2011


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources',type=Path,nargs='+',required=True)
    p.add_argument('--repeats',type=int,default=12)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():p.error('Preserve previous evidence; choose a new output.')
    if len(args.sources)<2 or args.repeats<1:p.error('Use at least two sources and one repeat.')
    classes=[load(path,i) for i,path in enumerate(args.sources)]
    with gzip.open(ROOT/'tests/fixtures/titan-11-worst.json.gz','rt') as f:cases=json.load(f)
    samples=[[] for _ in classes];comparisons=0
    for index,case in enumerate(cases):
        obs=decode(case['observation'],S(**case['field']));obs.score=tuple(obs.score)
        for repeat in range(args.repeats):
            expected=None;offset=(index+repeat)%len(classes)
            for source in [(offset+j)%len(classes) for j in range(len(classes))]:
                c=classes[source]();c.__dict__.update(restore(case['state_before']))
                cpu,wall=time.process_time_ns(),time.perf_counter_ns();action=c.act(obs)
                elapsed_wall=(time.perf_counter_ns()-wall)*1e-6
                elapsed_cpu=(time.process_time_ns()-cpu)*1e-6
                samples[source].append((elapsed_cpu,elapsed_wall))
                value=({str(k):v.as_dict() for k,v in action.players.items()},action.debug,
                       {k:v for k,v in vars(c).items() if not k.startswith('_runtime_')})
                if expected is None:expected=value
                else:
                    assert value==expected,('Action/state mismatch',index,repeat,str(args.sources[source]))
                    comparisons+=1
    report={'scope':__doc__,'cases':len(cases),'repeats':args.repeats,'exact_comparisons':comparisons,
        'sources':[{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'cpu_ms':timing([x[0] for x in data]),'wall_ms':timing([x[1] for x in data])}
                   for path,data in zip(args.sources,samples)]}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print('All actions/non-cache states matched;',comparisons,'comparisons.')


if __name__=='__main__':main()
