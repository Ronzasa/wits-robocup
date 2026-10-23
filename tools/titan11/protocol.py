"""Build a hashed native paired protocol from the preregistered seed cohorts."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def write(out,sources,seeds,styles,split):
    assert not out.exists(),out
    archive=ROOT/'tests/fixtures/titan-11-intelligence-opponents.zip'
    protocol={'engine_version':'0.1.0','config_hash':'372990895c7eca2a','opponents_archive':str(archive.relative_to(ROOT)),
        'opponents_archive_sha256':digest(archive),'opponents':styles,'seeds':{split:seeds},'fixture_order_seed':110108,
        'sources':{name:{'path':str(Path(path).relative_to(ROOT) if Path(path).is_absolute() else path),'sha256':digest(ROOT/path)} for name,path in sources.items()},
        'deadline_ms':20.,'ticks':2400,'scope':'Both pitch sides and kickoff arrangements. All raw timeouts kept; first clean exact repeats stored separately.'}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(protocol,indent=2)+'\n');return protocol

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    reg=json.loads((ROOT/'docs/titan-11-intelligence/registration.json').read_text())
    sources={'v10':'my-team/team.py','runtime':'experiments/titan-11-runtime-control/team.py','predictive':'experiments/titan-11-predictive/team.py','coordinated':'experiments/titan-11-coordinated/team.py','finishing':'experiments/titan-11-elite-finishing/team.py','defence':'experiments/titan-11-threat-defence/team.py','playbooks':'experiments/titan-11-playbooks/team.py','learning':'experiments/titan-11-learned-value/team.py'}
    write(a.out,sources,reg['development'][:2],reg['training_pool'],'development')
if __name__=='__main__':main()
