"""Register a finite repair comparison and new independent qualification."""
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/titan11'))
from register import integers
from protocol import write


def main():
    out=ROOT/'docs/titan-11-repair'
    assert not out.exists()
    used=set(range(1000,1010));files=[]
    for root in (ROOT/'docs',Path('/workspace/work')):
        for p in root.rglob('*.json'):
            if p.stat().st_size>4_000_000 or not any(x in p.name for x in ('protocol','registry','registration','fresh','screen','seed-audit')):continue
            try:used.update(integers(json.loads(p.read_text())));files.append(str(p))
            except (ValueError,OSError):continue
    for branch in ('titan-11-championship','titan-12b-counter-defence'):
        for p in subprocess.check_output(['git','ls-tree','-r','--name-only',branch,'docs'],cwd=ROOT,text=True).splitlines():
            if any(x in p for x in ('seed-registry','seed-audit','protocol.json')):
                used.update(integers(json.loads(subprocess.check_output(['git','show',branch+':'+p],cwd=ROOT))));files.append(branch+':'+p)
    rng=random.Random(1111182026);chosen=[]
    while len(chosen)<28:
        n=rng.randrange(10000,2**31-1)
        if n not in used and n not in chosen:chosen.append(n)
    prior=json.loads((ROOT/'docs/titan-11-intelligence/registration.json').read_text())
    registration={
        'project':'TITAN-11 repair: deferred chase estimates and verified slow-pass handoff',
        'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'development':chosen[:4], 'validation':chosen[4:],
        'development_styles':prior['training_pool'],
        'validation_styles':prior['training_pool']+prior['heldout_styles'],
        'validation_fixtures':24*12*4,
        'excluded_values_sha256':hashlib.sha256(json.dumps(sorted(used)).encode()).hexdigest(),
        'excluded_integer_values':len(used),'excluded_sources':files,
        'fixed_candidates':['runtime','handoff','combined'],
        'selection':'No outcome-based new variants. Runtime must preserve all shared-state decisions and development football totals. Handoff must beat frozen TITAN-11 in development points. Only a combined or runtime-only source with passing non-inference reliability gates and higher points than v10 is eligible. Select highest development points, tie goal difference, tie mean time. If no repair eligible, keep v10 and do not claim repaired qualification. No tuning on new validation or pooling with old validation.',
        'gates':prior['gates'],
        'no_intake_retries':'Every original SDK validation and raw deadline event is retained. A failed candidate intake makes it ineligible.',
        'scope':'Previously used validation is diagnostic only. New fixed validation is the sole promotion inference cohort. No online-ranking claim.',
    }
    out.mkdir();(out/'registration.json').write_text(json.dumps(registration,indent=2)+'\n')
    write(out/'development-protocol.json',{
        'v10':'my-team/team.py','titan11':'experiments/titan-11/team.py',
        'runtime':'experiments/titan-11-r-runtime/team.py',
        'handoff':'experiments/titan-11-r-handoff/team.py',
        'combined':'experiments/titan-11-r-combined/team.py',
    },chosen[:4],prior['training_pool'],'repair-development')
    print({k:registration[k] for k in ('development','validation','validation_fixtures')})


if __name__=='__main__':main()
