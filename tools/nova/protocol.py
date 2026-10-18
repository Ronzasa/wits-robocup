"""Frozen source/fixture protocols for NOVA native competitions."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(out,sources,seeds,styles,split,archive=None,training=True):
    assert not out.exists();archive=archive or ROOT/'tests/fixtures/nova-1-training.zip'
    data={'engine_version':'0.1.0','config_hash':'372990895c7eca2a','opponents_archive':str(archive.relative_to(ROOT)),
        'opponents_archive_sha256':digest(archive),'opponents':styles,'seeds':{split:seeds},'fixture_order_seed':9011901,
        'sources':{k:{'path':str(Path(v).relative_to(ROOT) if Path(v).is_absolute() else v),'sha256':digest(ROOT/v)} for k,v in sources.items()},
        'deadline_ms':20.,'ticks':2400,'training':training,
        'timing':'Unmodified SDK wall timer/deadline; external thread CPU and GC-overlap observations applied equally. Every initial miss and failed repeat retained.'}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(data,indent=2)+'\n');return data
