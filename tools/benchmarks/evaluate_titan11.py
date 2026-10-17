"""Audit TITAN-11 paired comparisons; raw deadline failures always enter gates."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from benchmark import aggregate


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def evaluate(root):
    root=Path(root)
    metadata=json.loads((root/'metadata.json').read_text())
    assert metadata.get('finished_utc'), 'Incomplete run'
    protocol=metadata['protocol']
    assert hashlib.sha256((root/'sources/champion/team.py').read_bytes()).hexdigest()==protocol['sources']['champion']['sha256']
    names=list(protocol['sources'])
    assert protocol['sources']['champion']['sha256']=='5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6'
    if set(protocol['seeds'])!={'development'}:
        assert len(names)==2
        challenger=next(n for n in names if n!='champion')
        registry_path=Path(__file__).resolve().parents[2]/'docs/titan-11/seed-registry.json'
        registry=json.loads(registry_path.read_text())['validation']
        assert challenger in registry
        actual_seeds=[s for values in protocol['seeds'].values() for s in values]
        assert sorted(actual_seeds)==sorted(registry[challenger])
        assert len(protocol['opponents'])==12 and len(set(actual_seeds))==12
    expected=len(protocol['opponents'])*sum(map(len,protocol['seeds'].values()))*4
    for name in names:
        source=root/'sources'/name/'team.py'
        assert hashlib.sha256(source.read_bytes()).hexdigest()==protocol['sources'][name]['sha256']
        expected_keys={(split, seed, style, side, kickoff)
            for split, seeds in protocol['seeds'].items() for seed in seeds
            for style in protocol['opponents'] for side in (0,1) for kickoff in (True,False)}
        for label in ('raw','accepted'):
            rows=read_rows(root/label/name/'matches.jsonl')
            assert len(rows)==len({r['fixture_id'] for r in rows})==expected
            actual_keys={(r['split'],r['seed'],Path(r['opponent']).parent.name,r['candidate_slot'],r['candidate_takes_kickoff']) for r in rows}
            assert actual_keys==expected_keys, ('Missing or extra fixture arrangement', name, label)
    repeats=read_rows(root/'timing-repeats.jsonl')
    reports={}
    for name in names:
        if name=='champion':continue
        dest=root/(name+'-comparison.json')
        if not dest.exists():
            subprocess.run([sys.executable,str(Path(__file__).with_name('compare.py')),
                str(root/'accepted/champion'),str(root/'accepted'/name),'--out',str(dest)],check=True)
        comparison=json.loads(dest.read_text())
        raw0=aggregate(read_rows(root/'raw/champion/matches.jsonl'))
        raw1=aggregate(read_rows(root/'raw'/name/'matches.jsonl'))
        def repeated_failures(source):
            answer=[]
            for row in repeats:
                if row['source']!=source:continue
                repeated=row['result'];slot=repeated['candidate_slot']
                if repeated['result']['stats'][slot]['policy_timeouts']:
                    answer.append({'fixture':row['original_fixture_id'],'attempt':row['attempt']})
            return answer
        reproducible=repeated_failures(name)
        n=comparison['paired_fixtures']
        ceiling=raw0['decision_mean_ms']*1.35+.04
        gates={
            'more_points':comparison['challenger']['points']>comparison['baseline']['points'],
            'positive_paired_95_lower':comparison['paired_seed_block_bootstrap_95'][0]>0.,
            'zero_policy_exceptions':raw1['policy_errors']==0,
            'no_repeated_candidate_deadlines':not reproducible,
            'mean_runtime_ceiling':raw1['decision_mean_ms']<=ceiling,
            'raw_deadline_delta_at_most_2_per_1000':(raw1['policy_timeouts']-raw0['policy_timeouts'])*1000/n<=2.,
            'official_acceptance':json.loads((root/(name+'-validation.json')).read_text())['ok'],
        }
        reports[name]={'stage':str(root),'source':protocol['sources'][name],
            'paired_fixtures':n,'paired_95':comparison['paired_seed_block_bootstrap_95'],
            'points':{'champion':comparison['baseline']['points'],'challenger':comparison['challenger']['points']},
            'raw':{'champion':raw0,'challenger':raw1},'mean_ceiling_ms':ceiling,
            'raw_extra_misses_per_1000':(raw1['policy_timeouts']-raw0['policy_timeouts'])*1000/n,
            'repeated_candidate_failures':reproducible,'gates':gates,'all_gates_pass':all(gates.values()),
            'status':'DEVELOPMENT ONLY' if set(protocol['seeds'])=={'development'} else ('PASS' if all(gates.values()) else 'REJECT')}
    (root/'gate-audit.json').write_text(json.dumps(reports,indent=2)+'\n')
    return reports


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);args=p.parse_args()
    reports=evaluate(args.run)
    for name,r in reports.items():print(name,r['status'],r['points'],r['paired_95'],r['gates'])


if __name__=='__main__':main()
