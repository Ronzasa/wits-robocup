"""Apply the registered development rule, then freeze one repair for validation."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/titan11'))
from evaluate import evaluate,load_rows
from protocol import write,digest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True)
    a=p.parse_args();run=a.work/'development';doc=ROOT/'docs/titan-11-repair'
    assert not (doc/'selection.json').exists()
    gates=evaluate(run)
    rows={n:load_rows(run,'accepted',n) for n in ('titan11','runtime','handoff','combined')}
    signatures={n:{q['fixture_id']:(q['result']['score'],q['result']['stats'][q['candidate_slot']]['passes_attempted'],q['result']['stats'][q['candidate_slot']]['passes_completed']) for q in data} for n,data in rows.items()}
    equivalent=signatures['runtime']==signatures['titan11']
    equivalent_combined=signatures['combined']==signatures['handoff']
    assert equivalent and equivalent_combined,'Runtime-only change altered football on clean native fixtures.'
    original=gates['titan11']['accepted']['challenger']
    runtime=gates['runtime']['accepted']['challenger']
    handoff=gates['handoff']['accepted']['challenger']
    assert json.loads((doc/'runtime-equivalence.json').read_text())['identical_decisions_and_reception_states']==9600
    runtime_ok=runtime['decision_mean_ms']<=original['decision_mean_ms']
    handoff_ok=handoff['points']>original['points']
    allowed=[n for n in ('runtime','combined') if gates[n]['development_eligible'] and runtime_ok and (n=='runtime' or handoff_ok)]
    chosen=max(allowed,key=lambda n:(gates[n]['accepted']['challenger']['points'],gates[n]['accepted']['challenger']['goal_difference'],-gates[n]['accepted']['challenger']['decision_mean_ms'])) if allowed else None
    selection={'selected':chosen,'runtime_native_football_identical':equivalent,
        'combined_matches_handoff_football':equivalent_combined,'runtime_mean_improved':runtime_ok,
        'handoff_points_improved_over_frozen_titan11':handoff_ok,
        'development_summary':{n:{'points':r['accepted']['challenger']['points'],'goals_for':r['accepted']['challenger']['goals_for'],'goals_against':r['accepted']['challenger']['goals_against'],'mean_ms':r['accepted']['challenger']['decision_mean_ms'],'raw_misses':r['raw']['challenger']['policy_timeouts'],'failed':[k for k,v in r['flags'].items() if not v]} for n,r in gates.items()},
        'scope':'Registered development selection only, not independent promotion evidence.'}
    if chosen:
        source=ROOT/gates[chosen]['source']['path'];dest=ROOT/'experiments/titan-11-r/team.py'
        assert not dest.exists();dest.parent.mkdir();shutil.copyfile(source,dest)
        selection.update({'candidate_path':str(dest.relative_to(ROOT)),'candidate_sha256':digest(dest)})
        reg=json.loads((doc/'registration.json').read_text())
        write(doc/'validation-protocol.json',{'v10':'my-team/team.py','repair':str(dest.relative_to(ROOT))},reg['validation'],reg['validation_styles'],'repair-validation')
    (doc/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    (doc/'development-gates.json').write_text(json.dumps(gates,indent=2)+'\n')
    print(json.dumps(selection,indent=2))


if __name__=='__main__':main()
