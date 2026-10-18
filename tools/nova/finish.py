"""Continue the registered pipeline serially once native learning terminates."""
import argparse, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--training-pid', type=int, required=True)
    p.add_argument('--work', type=Path, required=True)
    a = p.parse_args()
    process = Path('/proc') / str(a.training_pid) / 'cmdline'
    while process.exists() and b'tools/nova/train.py' in process.read_bytes():
        time.sleep(10)
    assert (ROOT / 'docs/nova-1/selected-policy.json').exists(), 'Learning stopped without a selected source; preserve and investigate.'
    stages = [
        ('diagnose', ['tools/nova/diagnose.py', '--work', str(a.work)]),
        ('ablation', ['tools/nova/ablate.py', '--work', str(a.work)]),
        ('qualification', ['tools/nova/qualify.py', '--work', str(a.work)]),
        ('report', ['tools/nova/report.py', '--work', str(a.work)]),
    ]
    for name, command in stages:
        print('Starting serial stage:', name, flush=True)
        with (a.work / ('pipeline-' + name + '.log')).open('x') as log:
            answer = subprocess.run([sys.executable, *command], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        assert answer.returncode == 0, 'Stage failed; original evidence preserved: ' + name
        print('Finished serial stage:', name, flush=True)
    decision = json.loads((ROOT / 'docs/nova-1/decision.json').read_text())
    print(json.dumps(decision, indent=2), flush=True)


if __name__ == '__main__':
    main()
