"""Read-only progress for the serial native campaign, including partial runs."""
import argparse, json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', type=Path, required=True)
    args = p.parse_args()
    records = []
    for path in args.work.glob('*/metadata.json'):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if 'started_utc' in data and 'protocol' in data:
            records.append((data['started_utc'], path, data))
    if not records:
        print('No native stage started.');return
    _, path, data = max(records, key=lambda q: q[0])
    protocol = data['protocol']
    expected = len(protocol['opponents']) * sum(len(v) for v in protocol['seeds'].values()) * 4
    sources = {}
    for name in protocol['sources']:
        file = path.parent / 'raw' / name / 'matches.jsonl'
        sources[name] = file.read_bytes().count(b'\n') if file.exists() else 0
    result = {'stage': path.parent.name, 'paired_configurations_complete_for_all_sources': min(sources.values()),
              'paired_configurations_required': expected, 'source_games_recorded': sum(sources.values()),
              'source_games_required': expected * len(sources), 'finished': 'finished_utc' in data}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
