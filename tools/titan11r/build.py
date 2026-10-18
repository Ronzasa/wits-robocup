"""Two isolated repairs to frozen TITAN-11; never edit a measured source."""
import argparse
import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FROZEN = '485e8dea6a7ea13fc3d881bf735662d4aabecc177681d98971193056419bac35'


def build(runtime=False, handoff=False):
    source = (ROOT / 'experiments/titan-11/team.py').read_text()
    assert hashlib.sha256(source.encode()).hexdigest() == FROZEN
    if runtime:
        # The ETA fallback cannot affect an earlier physically reachable
        # sample. Evaluate it only if no sample passes the unchanged tests.
        old = '''        best=None
        for t,x,y in samples:'''
        assert source.count(old) == 1
        source = source.replace(old, '        for t,x,y in samples:', 1)
        old = '''            cost=self._eta(p,x,y)+t*.12
            if best is None or cost<best[0]:best=(cost,(x,y))
        return best'''
        new = '''        # General chasing retains the exact original heuristic answer.
        # Most calls return above, so their unused fallback ETAs are free.
        best=None
        for t,x,y in samples:
            cost=self._eta(p,x,y)+t*.12
            if best is None or cost<best[0]:best=(cost,(x,y))
        return best'''
        assert source.count(old) == 1
        source = source.replace(old, new, 1)
    if handoff:
        old = '''                    or obs.ball.last_touch not in (None, passer)
                    or math.hypot(vx, vy) < 9.0):'''
        new = '''                    or obs.ball.last_touch not in (None, passer)):'''
        assert source.count(old) == 1
        source = source.replace(old, new, 1)
        old = '''if launch is not None and receiver is not None and math.hypot(launch[2],launch[3])>10.5:'''
        assert source.count(old) == 1
        source = source.replace(old, '''if launch is not None and receiver is not None:
                            # A named pass is coordinated only after the actual
                            # executable race below. Speed alone is not a
                            # reason to abandon a physically safe reception.''', 1)
    source = source.replace('11.0-tactical-intelligence-experimental', '11.1-reception-repair-experimental', 1)
    ast.parse(source)
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', action='store_true')
    parser.add_argument('--handoff', action='store_true')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Preserve measured sources; choose a new destination.')
    assert args.out.name == 'team.py'
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build(args.runtime, args.handoff))
    print(args.out, hashlib.sha256(args.out.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
