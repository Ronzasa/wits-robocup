"""Register fresh development and fixed independent qualification cohorts."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,random,zipfile
from build import ROOT,BASE_SHA

DOC=ROOT/'docs/physics-tactics'


def save(path,value):
    assert not path.exists(),path
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ints(value):
    if type(value) is int:yield value
    elif isinstance(value,dict):
        for x in value.values():yield from ints(x)
    elif isinstance(value,list):
        for x in value:yield from ints(x)


def main():
    old=Path('/workspace/work/elite-replay/tests/fixtures/elite-scout-opponents.zip')
    archive=ROOT/'tests/fixtures/physics-tactics-opponents.zip'
    assert not archive.exists()
    with zipfile.ZipFile(old) as z:
        manifest=json.loads(z.read('manifest.json'))
        data={r['path']:z.read(r['path']) for r in manifest}
    assert next(r for r in manifest if r['style']=='v10')['sha256']==BASE_SHA
    code=(ROOT/'my-team/team.py').read_bytes()
    manifest.append({'style':'elite-cutback','path':'elite-cutback/team.py','sha256':hashlib.sha256(code).hexdigest()})
    data['elite-cutback/team.py']=code
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for name,code in data.items():z.writestr(name,code)
        z.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
    used=set(range(1000,1010))
    for root in (Path('/workspace/work'),Path('/workspace/wits-robocup/docs')):
        for path in root.rglob('*.json'):
            if path.stat().st_size>4_000_000 or not any(x in path.name for x in ('protocol','registration','registry')):continue
            try:used.update(ints(json.loads(path.read_text())))
            except (UnicodeDecodeError,ValueError):pass
    rng=random.Random(10229391);seeds=[]
    while len(seeds)<18:
        s=rng.randrange(10_000_000,2_000_000_000)
        if s not in used and s not in seeds:seeds.append(s)
    record={'base_commit':'40b2787fc1bc447e9ab90aa78c3bb15aaf5c87ca','registered_utc':datetime.now(timezone.utc).isoformat(),
      'baseline':{'path':'champions/v10.0/team.py','sha256':BASE_SHA},
      'active':{'path':'my-team/team.py','sha256':sha(ROOT/'my-team/team.py')},
      'opponents_archive':str(archive.relative_to(ROOT)),'opponents_archive_sha256':sha(archive),
      'development_seeds':seeds[:2],'qualification_seeds':seeds[2:],
      'development_styles':['v10','v9.1','v10-compact','v10-counter','v10-press','quick_wall','aggressive-keeper','depth14-proxy'],
      'qualification_styles':['v10','v9.1','v10-compact','v10-counter','v10-press','quick_wall','tight_links','wide_switch','long_shooter','aggressive-keeper','depth14-proxy','elite-cutback'],
      'sources':{'v10':'champions/v10.0/team.py','active':'my-team/team.py',
                 'ambush':'experiments/physics-ambush/team.py','wall-brake':'experiments/physics-wall-brake/team.py','rebound-shot':'experiments/physics-rebound-shot/team.py'},
      'initial_hashes':{name:sha(ROOT/'experiments'/('physics-'+name)/'team.py') for name in ('ambush','wall-brake','rebound-shot')},
      'physics':{'engine_version':'0.1.0','config_hash':'372990895c7eca2a','ground_friction':.985,'wall_restitution':.75,'player_restitution':.25,'aerial':False},
      'development':'64 matched configurations/source. Inspect execution failures and public-physics witnesses; at most one documented revision per tactic after this development cohort. Never use qualification outcomes to modify/select/extend a tactic. All three isolated final variants receive the same fixed qualification even if development is weak. No combinations.',
      'qualification':'768 configurations/source:12styles*16unused seed blocks*2sides*2kickoffs. Serial native worker,2400ticks,20ms,rotating source order. Freeze sources and protocol in git before opening this cohort.',
      'gates':{'primary':'Raw native outcomes against frozen v10; clean exact repeats are diagnostic only.',
        'more_raw_points':True,'paired_95_lower_positive':True,
        'familywise_lower_positive':'3 registered v10 comparisons, 20,000 whole-seed bootstrap resamples, 98.333333% two-sided Bonferroni interval (quantiles .05/6 and 1-.05/6), lower>0.',
        'zero_policy_exceptions':True,'zero_reproduced_own_deadline_failures':True,'additional_raw_misses_per_1000_max':2.,
        'mean_runtime_max':'v10_raw_mean*1.35+.04ms','sdk_intake_pass':True,'legal_actions':True,'fixtures_per_source':768,
        'native_execution':'At least one confirmed postwall contact for ambush, collected wall-brake reception, or uninterrupted rebound-shot goal. Report plans, native executions and successes separately.'},
      'telemetry':'Native kicks require matching events. Native bounces require reflected positions and velocities without an intervening body touch. Receptions require observed recipient contact after the confirmed wall. Shot goals require a native goal event on an uninterrupted confirmed rebound flight. Goal associations following an ambush are descriptive, not causal.',
      'preservation':'No changes to main, active my-team, any champion, SDK, engine or config. Even a passing tactic remains experimental until explicit approval.',
      'excluded_seed_values_sha256':hashlib.sha256(json.dumps(sorted(used)).encode()).hexdigest()}
    save(DOC/'registration.json',record)


if __name__=='__main__':main()
