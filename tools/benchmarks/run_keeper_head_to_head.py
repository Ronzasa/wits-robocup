"""Fresh direct matches of the frozen integrated controller and champion.

This is a diagnostic of direct dominance, not the registered league-pool
qualification. All raw SDK deadline misses and both teams' outcomes count.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys

from benchmark import aggregate,points,run_fixture

ROOT=Path(__file__).resolve().parents[2]


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():parser.error('Preserve prior evidence: use a new output directory.')
    protocol=json.loads(args.protocol.read_text())
    out=args.out.resolve();out.mkdir(parents=True)
    sys.path.insert(0,str(ROOT/'student-sdk'))
    sources={}
    for name,source in protocol['sources'].items():
        p=ROOT/source['path'];assert digest(p)==source['sha256']
        dest=out/name/'team.py';dest.parent.mkdir();shutil.copy2(p,dest)
        sources[name]=str(dest)
    fixtures=[(seed,side,kickoff) for seed in protocol['seeds'] for side in (0,1) for kickoff in (True,False)]
    random.Random(protocol['fixture_order_seed']).shuffle(fixtures)
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    rows=[];repeats=[]
    with (out/'matches.jsonl').open('w') as handle,(out/'timing-repeats.jsonl').open('w') as repeat_handle:
        for i,(seed,side,kickoff) in enumerate(fixtures):
            spec={'team':sources['integrated'],'opponent':sources['active'],'seed':seed,
                'candidate_slot':side,'candidate_takes_kickoff':kickoff,'split':'direct-validation',
                'config_path':str(ROOT/'configs/default.toml'),'config_hash':protocol['config_hash']}
            row=run_fixture(spec);rows.append(row)
            handle.write(json.dumps(row)+'\n');handle.flush()
            assert not any(s['policy_errors'] for s in row['result']['stats'])
            if any(s['policy_timeouts'] for s in row['result']['stats']):
                repeat=run_fixture(spec);repeats.append(repeat)
                repeat_handle.write(json.dumps(repeat)+'\n');repeat_handle.flush()
                assert not any(s['policy_errors'] for s in repeat['result']['stats'])
            if (i+1)%16==0:print('Fresh direct matches:',i+1,'/',len(fixtures),flush=True)
    opponents=[{**r,'candidate_slot':1-r['candidate_slot'],'opponent':sources['integrated']} for r in rows]
    a,b=aggregate(rows),aggregate(opponents)
    blocks=defaultdict(list)
    for own,other in zip(rows,opponents):blocks[own['seed']].append(points(own)-points(other))
    means=[sum(x)/len(x) for x in blocks.values()]
    rng=random.Random(231025200)
    boot=sorted(sum(rng.choices(means,k=len(means)))/len(means) for _ in range(20000))
    own_repeat_misses=sum(r['result']['stats'][r['candidate_slot']]['policy_timeouts'] for r in repeats)
    result={'integrated':a,'active':b,'raw_matches':len(rows),'seed_blocks':len(blocks),
        'direct_points_per_match_difference':a['points_per_match']-b['points_per_match'],
        'whole_seed_bootstrap_95':[boot[500],boot[19499]],
        'raw_additional_deadline_misses_per_1000':(a['policy_timeouts']-b['policy_timeouts'])*1000/len(rows),
        'own_deadline_misses_on_exact_repeats':own_repeat_misses,'promoted':False,
        'scope':'Fresh direct head-to-head against this champion only. Does not establish improvement against a league opponent pool.'}
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    for name,source in protocol['sources'].items():assert digest(ROOT/source['path'])==source['sha256']
    print('Direct result W/D/L:',a['wins'],a['draws'],a['losses'],'goals',a['goals_for'],a['goals_against'],
          'points',a['points'],b['points'],'95%',result['whole_seed_bootstrap_95'],flush=True)


if __name__=='__main__':main()
