"""Seal seed cohorts, fixed opponents and decision rules before native play."""
import hashlib
import json
from pathlib import Path
import random
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT/'docs/tactics'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def integers(value):
    if type(value) is int:
        yield value
    elif isinstance(value,dict):
        for v in value.values():
            yield from integers(v)
    elif isinstance(value,list):
        for v in value:
            yield from integers(v)

def main():
    assert not (DOC/'registration.json').exists()
    excluded = set(range(1000,1010))
    paths = []
    for root in (Path('/workspace/wits-robocup/docs'),Path('/workspace/work')):
        for path in root.rglob('*.json'):
            if path.stat().st_size > 4_000_000 or not any(w in path.name for w in ('protocol','registration','registry')):
                continue
            try:
                excluded.update(integers(json.loads(path.read_text())))
                paths.append(str(path))
            except (ValueError,UnicodeDecodeError):
                continue
    rng = random.Random(10182026)
    seeds = []
    while len(seeds)<24:
        n = rng.randrange(10_000_000,2_000_000_000)
        if n not in excluded and n not in seeds:
            seeds.append(n)
    # Reuse frozen, known local style implementations. No leader/private
    # source access and no engine changes are involved.
    rows = []
    archive = ROOT/'tests/fixtures/titan-x-opponents.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        with zipfile.ZipFile(ROOT/'tests/fixtures/titan-10b-opponents.zip') as old:
            for row in json.loads(old.read('manifest.json')):
                code = old.read(row['path'])
                rows.append(row)
                z.writestr(row['path'],code)
        with zipfile.ZipFile('/workspace/work/nova-1/tests/fixtures/nova-1-training.zip') as old:
            for row in json.loads(old.read('manifest.json')):
                if row['style'] in ('v10','v10-compact','v10-counter','v10-press','v10-long'):
                    rows.append(row)
                    z.writestr(row['path'],old.read(row['path']))
        code = (ROOT/'my-team/team.py').read_text().replace(
            'sweep = bx < self._left+10.0 and self._eta(keeper,bx,by)<races[chaser[0]][0]*0.85',
            'sweep = bx > 8.0 and self._eta(keeper,bx,by) < 5.0').encode()
        rows.append({'style':'aggressive-keeper','path':'aggressive-keeper/team.py','sha256':sha(code)})
        z.writestr(rows[-1]['path'],code)
        z.writestr('manifest.json',json.dumps(rows,indent=2)+'\n')
    record = {
        'project':'TITAN-X four isolated special tactics',
        'base_commit':'0a7a3aeba3950eb1b2ed0deeb7a06f2f9b3563e5',
        'champion_path':'my-team/team.py','champion_sha256':sha((ROOT/'my-team/team.py').read_bytes()),
        'opponents_archive':str(archive.relative_to(ROOT)),'opponents_archive_sha256':sha(archive.read_bytes()),
        'targeted':seeds[:2], 'development':seeds[2:6], 'qualification':seeds[6:22], 'reserve_unused':seeds[22:],
        'excluded_values_sha256':sha(json.dumps(sorted(excluded)).encode()),'excluded_sources':paths,
        'development_styles':['v10','v10-compact','v10-counter','v10-press','aggressive-keeper','quick_wall'],
        'targeted_styles':{'power':['v10-counter','v10-compact'],'trap':['aggressive-keeper','high_press'],
                           'pinball':['v10-compact','tight_links'],'ambush':['v10-press','fast_counter']},
        'qualification_styles':['v10','v9.1','v10-compact','v10-counter','v10-press','v10-long',
                                'long_shooter','tight_links','quick_wall','aggressive-keeper','relay_legacy','wide_switch'],
        'selection':'No outcome tuning. Four initial flags off; standalone one-flag sources frozen before matches. A tactic is promising only with >v10 development points, positive goal-difference delta, zero exceptions, <=2 extra raw misses/1000 and mean<=v10*1.35+.04ms. It must execute at least 5 distinct tactical episodes or passes across targeted+development. Integrate only qualifying tactics; if multiple qualify test combination on 2 unused reserve seeds then select by points (tie: fewer flags). If none qualify, freeze the highest development points standalone as an explicitly rejected best-failure challenger for required fresh qualification; tie: goal difference then flag order. No source/flag selection after qualification.',
        'qualification_pairs':768,'deadline_ms':20.0,'match_ticks':2400,
        'gates':{'more_points':True,'whole_seed_bootstrap_95_lower_strictly_positive':True,
                 'zero_policy_exceptions':True,'no_reproducible_deadline_failure':True,
                 'extra_raw_deadline_misses_per_1000_max':2.,'accepted_mean_max':'v10*1.35+0.04ms',
                 'official_sdk_validation':True,'legal_actions':True,'fixtures_min':768},
        'timing':'Serial native worker, stock 20ms SDK decision timing. Preserve raw rows. Timeout-containing fixtures repeat identically at most3 times, first clean regardless of score. A candidate timeout on its first exact repeat counts as reproducible even if a later repeat is clean. Exceptions never repaired. No engine, GC, affinity or controller timing controls.',
        'attribution':'Activation/execution counts from bounded debug telemetry. Goals/turnovers in a 5-second post-opportunity window are associations, not causal attribution. Report matched v10 outcomes and all failures.',
        'guardrails':'Feature branch only. No main/current champion/frozen source/SDK/config changes. No ranking claim.'}
    (DOC/'registration.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Registered 4 independent tactics, 96 development pairs/source, 768 fresh qualification pairs.')

if __name__ == '__main__':
    main()
