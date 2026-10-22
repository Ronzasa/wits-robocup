"""Summarize a completed keeper screen; never replace raw timeout results."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from benchmark import aggregate

ROOT=Path(__file__).resolve().parents[2]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():
        p.error('Use a new output directory.')
    args.out.mkdir(parents=True)
    reg=json.loads((ROOT/'docs/keeper-support/registration.json').read_text())
    data={name:[json.loads(s) for s in (args.run/'raw'/name/'matches.jsonl').read_text().splitlines()]
          for name in reg['sources']}
    expected=4*len(reg['development_seeds'])*len(reg['development_opponents'])
    assert all(len(rows)==expected for rows in data.values())
    for name,spec in reg['sources'].items():
        assert hashlib.sha256((ROOT/spec['path']).read_bytes()).hexdigest()==spec['sha256']
        assert hashlib.sha256((args.run/'sources'/name/'team.py').read_bytes()).hexdigest()==spec['sha256']
    summary={name:aggregate(rows) for name,rows in data.items()}
    telemetry={}
    for name,rows in data.items():
        counts=Counter()
        for row in rows:
            counts.update(row['physics_tactics']['counts'])
        telemetry[name]=dict(counts)
    comparisons={}
    for name in ('backpass','wall-counter','combined'):
        dest=args.out/(name+'-vs-active.json')
        subprocess.run([sys.executable,str(ROOT/'tools/benchmarks/compare.py'),
            str(args.run/'raw/active'),str(args.run/'raw'/name),'--out',str(dest)],check=True)
        comparisons[name]=json.loads(dest.read_text())
    contacts=lambda name:sum(v for k,v in telemetry[name].items() if k.endswith('_receiver_contacts'))
    priority={'backpass':0,'wall-counter':1,'combined':2}
    qualified=[name for name in priority if summary[name]['points']>summary['active']['points'] and contacts(name)>=1]
    selected=min(qualified,key=lambda name:(-summary[name]['points'],priority[name])) if qualified else None
    decision={'phase':'development only','sources':summary,'native_counts':telemetry,
              'selected_for_validation':selected,'reason':
              'Highest development points with an actual new reception.' if selected else
              'No challenger earned more raw points than active while executing a new native reception.',
              'validation_seeds_used':False,'promoted':False,'main_modified':False,
              'scope':'Two development seed blocks against six fixed local opponents; no statistical superiority claim.'}
    (args.out/'development-decision.json').write_text(json.dumps(decision,indent=2)+'\n')
    if selected:
        protocol={k:reg[k] for k in ('engine_version','config_hash','opponents_archive','opponents_archive_sha256')}
        protocol.update(sources={name:reg['sources'][name] for name in ('active',selected)},
            seeds={'validation':reg['validation_seeds']},opponents=reg['validation_opponents'],
            fixture_order_seed=23081913,deadline_ms=20.,ticks=2400)
        (args.out/'validation-protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    for name,s in summary.items():
        print(name,s['points'],s['goals_for'],s['goals_against'],s['policy_errors'],s['policy_timeouts'],telemetry[name])
    print('Selected for fresh validation:',selected)


if __name__=='__main__':
    main()
