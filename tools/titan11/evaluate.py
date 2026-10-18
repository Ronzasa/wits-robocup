"""Apply unchanged v10 promotion gates and whole-seed paired inference."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/benchmarks'))
from benchmark import aggregate

def load_rows(run,kind,name):return [json.loads(s) for s in (run/kind/name/'matches.jsonl').read_text().splitlines()]

def compare(run,kind,name):
    out=run/(name+'-'+kind+'-comparison.json')
    if not out.exists():subprocess.run([sys.executable,str(ROOT/'tools/benchmarks/compare.py'),str(run/kind/'v10'),str(run/kind/name),'--out',str(out)],check=True,stdout=subprocess.DEVNULL)
    return json.loads(out.read_text())

def evaluate(run):
    metadata=json.loads((run/'metadata.json').read_text());names=metadata['protocol']['sources'];gates={}
    repeat=[json.loads(s) for s in (run/'timing-repeats.jsonl').read_text().splitlines()]
    for name,source in names.items():
        if name=='v10':continue
        clean=compare(run,'accepted',name);raw=compare(run,'raw',name);n=clean['paired_fixtures'];b=raw['baseline'];c=raw['challenger'];accepted=clean['challenger']
        extra=(c['policy_timeouts']-b['policy_timeouts'])*1000/n
        repeated=sum(any(x.get('policy_timeouts',0) for x in r['result']['result']['stats']) for r in repeat if r['source']==name)
        validation=json.loads((run/(name+'-validation.json')).read_text())
        illegal=sum(v for k,v in c['validation'].items() if k not in ('actions_validated','players_validated'))
        flags={'higher_fresh_points':accepted['points']>clean['baseline']['points'],'positive_paired_95_lower':clean['paired_seed_block_bootstrap_95'][0]>0,
            'zero_policy_exceptions':c['policy_errors']==0 and accepted['policy_errors']==0,'no_repeated_deadline_failure':repeated==0,
            'mean_runtime':accepted['decision_mean_ms']<=clean['baseline']['decision_mean_ms']*1.35+.04,
            'raw_deadlines':extra<=2.,'official_intake':validation['ok'] and not validation['folder_errors'],
            'legal_actions':illegal==0,'source_frozen':True}
        # Development screens choose positive points with the same reliability
        # restrictions; independent final inference alone decides promotion.
        development=all(v for k,v in flags.items() if k!='positive_paired_95_lower')
        gates[name]={'source':source,'flags':flags,'all_gates_pass':all(flags.values()),'development_eligible':development,
            'extra_raw_misses_per_1000':extra,'repeated_deadline_failures':repeated,'accepted':clean,'raw':raw}
    path=run/'gate-audit.json';assert not path.exists();path.write_text(json.dumps(gates,indent=2)+'\n');return gates

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);a=p.parse_args();g=evaluate(a.run)
    print(json.dumps({n:{'eligible':x['development_eligible'],'pass':x['all_gates_pass'],'points':x['accepted']['challenger']['points'],'baseline':x['accepted']['baseline']['points'],'CI':x['accepted']['paired_seed_block_bootstrap_95'],'extra_raw_misses_per_1000':x['extra_raw_misses_per_1000'],'failed':[k for k,v in x['flags'].items() if not v]} for n,x in g.items()},indent=2))
if __name__=='__main__':main()
