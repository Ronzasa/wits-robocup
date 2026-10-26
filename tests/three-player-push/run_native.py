"""Frozen, balanced native development: official 20 ms loop, no promotion."""
import argparse,hashlib,json,random,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/benchmarks'))
import default_roster as driver
from benchmark import aggregate

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--registration',type=Path,required=True);args=p.parse_args()
 reg=json.loads(args.registration.read_text());folder=args.registration.parent
 for x in [reg['candidate'],reg['opponent']]:assert sha(ROOT/x['path'])==x['sha256']
 fixtures=[(seed,side,kick) for seed in reg['seeds'] for side in (0,1) for kick in (True,False)]
 random.Random(reg['order_seed']).shuffle(fixtures);rows=[]
 native=dict(config_path=str(ROOT/'configs/default.toml'),engine_version='0.1.0',config_hash='372990895c7eca2a')
 with (folder/'matches.jsonl').open('x') as f:
  for seed,side,kick in fixtures:
   saved=driver.load_controller;objects=[]
   def capture(path):
    c=saved(path);objects.append(c);return c
   driver.load_controller=capture
   try:
    result,telemetry,roster=driver.native_match(str(ROOT/reg['candidate']['path']),str(ROOT/reg['opponent']['path']),seed,side,kick,native)
   finally:driver.load_controller=saved
   c=objects[side]
   telemetry['candidate_active_at_end']=getattr(c,'_active',None)
   telemetry['candidate_siege_seen']=hasattr(getattr(c,'_specialist',None),'_siege_obs')
   row=dict(seed=seed,candidate_slot=side,candidate_takes_kickoff=kick,result=result,telemetry=telemetry,initial_roster=roster)
   rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
   print(len(rows),'/',len(fixtures),result['score'],flush=True)
 summary=aggregate(rows);opponent=aggregate([dict(r,candidate_slot=1-r['candidate_slot']) for r in rows]);blocks=defaultdict(list)
 for r in rows:
  a,b=[r['result']['score'][i] for i in (r['candidate_slot'],1-r['candidate_slot'])]
  blocks[r['seed']].append(3 if a>b else -3 if a<b else 0)
 means=[sum(v)/len(v) for _,v in sorted(blocks.items())];rng=random.Random(3249100099)
 boots=sorted(sum(rng.choices(means,k=len(means)))/len(means) for _ in range(10000))
 report=dict(siege_seen_matches=sum(r['telemetry'].get('candidate_siege_seen',False) for r in rows),harness_sha256=sha(Path(__file__)),candidate=summary,opponent=opponent,points_difference_per_fixture=(summary['points']-opponent['points'])/len(rows),seed_block_95=[boots[250],boots[9749]],additional_raw_misses_per1000=(summary['policy_timeouts']-opponent['policy_timeouts'])*1000/len(rows),promotion=False,scope=reg['scope'])
 for x in [reg['candidate'],reg['opponent']]:assert sha(ROOT/x['path'])==x['sha256']
 (folder/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print('SUMMARY',json.dumps(report),flush=True)
if __name__=='__main__':main()
