"""Replay a frozen NOVA protocol without overwriting its original evidence.

Rebuild omitted population snapshots with rebuild_population.py first, then
use --population to locate them. Every relocated source must have the exact
original registered hash; seeds, styles, SDK limits and order are unchanged.
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--protocol', type=Path, required=True)
    p.add_argument('--population', type=Path)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    assert not args.out.exists(), 'Keep original evidence; select a new output path.'
    original = json.loads(args.protocol.read_text())
    relocated = json.loads(json.dumps(original))
    for name, spec in relocated['sources'].items():
        path = ROOT / spec['path']
        if not path.exists():
            assert args.population, 'Reconstruct population sources and provide --population.'
            path = args.population / Path(spec['path']).parent.name / 'team.py'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == original['sources'][name]['sha256'], name
        spec['path'] = str(path.resolve())
    dest = args.out.parent / (args.out.name + '-relocated-protocol.json')
    assert not dest.exists(), dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(relocated, indent=2) + '\n')
    subprocess.run([sys.executable, 'tools/benchmarks/run_nova.py', '--protocol', str(dest),
                    '--out', str(args.out)], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
