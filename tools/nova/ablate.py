"""Registered development-only diagnostics after source selection.

Same learned geometry/weights with and without response evaluation separates
the response-model contribution; the untrained same-framework joint planner
measures whether native optimization helped. This is not a new selector and
does not read or use qualification styles/seeds.
"""
import argparse, hashlib, json, sys
from pathlib import Path
from build import build,framework_for
from protocol import write, digest
from train import run, scores

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'docs/nova-1'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', type=Path, required=True)
    a = p.parse_args()
    registration = json.loads((DOC / 'ablation-registration.json').read_text())
    reg = json.loads((DOC / 'registration.json').read_text())
    assert registration['seeds'] == reg['development'][16:18]
    assert registration['styles'] == reg['qualification_styles'][:8]
    chosen = json.loads((DOC / 'selected-policy.json').read_text())
    selected = chosen['selected'];v = selected['vector']
    framework = selected.get('framework') or framework_for(selected['name'])
    parameters = {'config': v[:8], 'weights': v[8:] + [.4], 'framework': framework}
    assert digest(ROOT / chosen['candidate_path']) == chosen['candidate_sha256']
    assert hashlib.sha256(build(parameters, True).encode()).hexdigest() == chosen['candidate_sha256']
    sources = {'v10': 'my-team/team.py', 'learned-joint': chosen['candidate_path']}
    for name, params, joint in [('learned-open', parameters, False), ('untrained-joint', {'framework': framework}, True)]:
        dest = ROOT / 'experiments/nova-1-ablation' / name / 'team.py'
        assert not dest.exists();dest.parent.mkdir(parents=True)
        dest.write_text(build(params, joint));sources[name] = str(dest.relative_to(ROOT))
    protocol = DOC / 'ablation-protocol.json'
    write(protocol, sources, registration['seeds'], registration['styles'], 'development-ablation')
    out = a.work / 'ablation'
    run(protocol, out)
    result = {'diagnostic_only': True, 'candidate_not_reselected': True,
              'candidate_sha256': chosen['candidate_sha256'],
              'fixtures_per_source': len(registration['seeds']) * len(registration['styles']) * 4,
              'models': {name: scores(out, name) for name in sources if name != 'v10'}}
    dest = DOC / 'ablation-results.json';assert not dest.exists()
    dest.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
