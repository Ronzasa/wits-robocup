"""Select a frozen integrated development source, then apply held-out gates."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]


def read_rows(run,name):
    return [json.loads(s) for s in (run/'raw'/name/'matches.jsonl').read_text().splitlines()]


def compare(run,out):
    subprocess.run([sys.executable,str(ROOT/'tools/benchmarks/compare.py'),
        str(run/'raw/active'),str(run/'raw/integrated'),'--out',str(out)],check=True)
    return json.loads(out.read_text())


def telemetry(rows):
    counts=Counter();phases={name:Counter() for name in ('normal','moderate','ultra')}
    for r in rows:
        t=r['physics_tactics'];counts.update(t['counts'])
        for name,c in t['phases'].items():phases[name].update(c)
    return {'counts':dict(counts),'phases':{name:dict(c) for name,c in phases.items()}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--validation',type=Path)
    p.add_argument('--generation-count',type=int,choices=(3,4),default=3)
    args=p.parse_args()
    if args.out.exists():p.error('Use a new output directory.')
    args.out.mkdir(parents=True)
    reg=json.loads((ROOT/'docs/keeper-width/registration.json').read_text())
    if args.validation:
        report=compare(args.validation,args.out/'validation-vs-active.json')
        a,b=report['baseline'],report['challenger']
        assert a['matches']==b['matches']==384
        assert report['independent_seed_blocks']==12
        repeats=[json.loads(s) for s in (args.validation/'timing-repeats.jsonl').read_text().splitlines()]
        own_repeat_misses=sum(r['result']['result']['stats'][r['result']['candidate_slot']]['policy_timeouts']
            for r in repeats if r['source']=='integrated')
        extra=(b['policy_timeouts']-a['policy_timeouts'])*1000/b['matches']
        intake=json.loads((args.validation/'integrated-validation.json').read_text())
        t=telemetry(read_rows(args.validation,'integrated'))
        gates={'more_points':b['points']>a['points'],
            'positive_paired_95_lower_bound':report['paired_seed_block_bootstrap_95'][0]>0,
            'zero_policy_exceptions':b['policy_errors']==0,
            'raw_deadline_gate':extra<=reg['gates']['additional_raw_deadline_misses_per_1000_max'],
            'no_own_deadline_failure_on_exact_repeats':own_repeat_misses==0,
            'runtime_gate':b['decision_mean_ms']<=a['decision_mean_ms']*1.35+.04,
            'official_intake':bool(intake['ok']),
            'keeper_backpass_executed':t['counts'].get('backpass_native_kicks',0)>0,
            'keeper_collected':t['counts'].get('backpass_receiver_contacts',0)>0,
            'legal_engine_actions':not any(b['validation'].values())}
        decision={'phase':'held-out validation','all_gates_pass':all(gates.values()),'gates':gates,
            'additional_raw_deadline_misses_per_1000':extra,'own_repeat_deadline_misses':own_repeat_misses,
            'promoted':False,'main_modified':False,'telemetry':t,
            'baseline_telemetry':telemetry(read_rows(args.validation,'active')),
            'scope':report['scope']}
        (args.out/'validation-decision.json').write_text(json.dumps(decision,indent=2)+'\n')
        print('Held-out validation gates:',gates)
        return
    results={}
    for generation in range(1,args.generation_count+1):
        run=args.runs/f'generation-{generation}'
        report=compare(run,args.out/f'generation-{generation}-vs-active.json')
        assert report['paired_fixtures']==(96 if generation==4 else 48)
        metadata=json.loads((run/'metadata.json').read_text())
        spec=metadata['protocol']['sources']['integrated']
        assert hashlib.sha256((ROOT/spec['path']).read_bytes()).hexdigest()==spec['sha256']
        t=telemetry(read_rows(run,'integrated'))
        results[str(generation)]={'comparison':report,'source':spec,'telemetry':t,
            'baseline_telemetry':telemetry(read_rows(run,'active'))}
    eligible=[g for g,x in results.items() if x['comparison']['points_per_match_difference']>0
              and x['telemetry']['counts'].get('backpass_native_kicks',0)>0]
    selected=max(eligible,key=lambda g:results[g]['comparison']['points_per_match_difference']) if eligible else None
    decision={'selected_generation':selected,'generations':results,'validation_seeds_used':False,
        'promoted':False,'main_modified':False,'scope':'Development selection across frozen integrated revisions. R4 extends development with four fresh seed blocks under the archived amendment. No superiority claim before untouched validation.'}
    (args.out/'development-decision.json').write_text(json.dumps(decision,indent=2)+'\n')
    if selected:
        spec=results[selected]['source']
        protocol={k:reg[k] for k in ('engine_version','config_hash','opponents_archive','opponents_archive_sha256')}
        protocol.update(sources={'active':reg['sources']['active'],'integrated':spec},
            seeds={'validation':reg['validation_seeds']},opponents=reg['validation_opponents'],
            fixture_order_seed=231025197,deadline_ms=20.,ticks=2400)
        (args.out/'validation-protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    print('Selected frozen integrated generation:',selected)


if __name__=='__main__':main()
