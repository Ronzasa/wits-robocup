"""Register a finite, staged native learning budget and sealed future cohorts."""
import hashlib,json,random,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/nova-1'

def digest(data):return hashlib.sha256(data).hexdigest()
def integers(v):
    if type(v) is int:yield v
    elif isinstance(v,dict):
        for q in v.values():yield from integers(q)
    elif isinstance(v,list):
        for q in v:yield from integers(q)

def main():
    assert not (DOC/'registration.json').exists()
    used=set(range(1000,1010));excluded=[]
    for root in (Path('/workspace/wits-robocup/docs'),Path('/workspace/work')):
        for path in root.rglob('*.json'):
            if '.git' in path.parts or path.stat().st_size>4_000_000 or not any(k in path.name for k in ('protocol','registry','registration','seed-audit')):continue
            try:used.update(integers(json.loads(path.read_text())));excluded.append(str(path))
            except (ValueError,OSError):pass
    for branch in ('titan-11-championship','titan-12b-counter-defence'):
        for p in subprocess.check_output(['git','ls-tree','-r','--name-only',branch,'docs'],cwd=ROOT,text=True).splitlines():
            if any(k in p for k in ('protocol.json','seed-registry','seed-audit')):
                used.update(integers(json.loads(subprocess.check_output(['git','show',branch+':'+p],cwd=ROOT))));excluded.append(branch+':'+p)
    rng=random.Random(202610180901);chosen=[]
    while len(chosen)<64:
        n=rng.randrange(10000,2**31-1)
        if n not in used and n not in chosen:chosen.append(n)
    training=['v10','v9.1','v10-compact','v10-counter','v10-press','v10-long','long_shooter','tight_links',
              'nova-attack','nova-block','nova-press','nova-wall']
    archive=ROOT/'tests/fixtures/nova-1-training.zip';manifest=[]
    with zipfile.ZipFile('/workspace/wits-robocup/tests/fixtures/titan-11-intelligence-opponents.zip') as old,zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as new:
        for row in json.loads(old.read('manifest.json')):
            if row['style'] not in training:continue
            code=old.read(row['path']);manifest.append(row);new.writestr(row['path'],code)
        template=(ROOT/'tools/nova/opponent.pyfrag').read_text()
        for name,mode,params in [('nova-attack','attack',(13.,9.,38.,.2,2.2)),('nova-block','block',(10.,10.,38.,.5,2.2)),('nova-press','press',(6.,7.,35.,.2,3.)),('nova-wall','wall',(22.,9.,30.,.6,2.5))]:
            code=template.replace("MODE='attack'",'MODE='+repr(mode)).replace('PARAMS=(12.,10.,30.,.5,2.2)','PARAMS='+repr(params)).encode()
            row={'style':name,'path':name+'/team.py','sha256':digest(code)};manifest.append(row);new.writestr(row['path'],code)
        new.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
    # Distinct modes and randomly drawn parameters, never played by training
    # or selection. Only the sealed archive hash/style labels are exposed.
    holdout=ROOT/'tests/fixtures/nova-1-unseen.zip';held=[];hrng=random.Random(90118077)
    with zipfile.ZipFile(holdout,'x',zipfile.ZIP_DEFLATED) as z:
        for name,mode in [('unseen-asymmetric','chiral'),('unseen-counter','counter'),('unseen-swarm','swarm'),('unseen-long','long')]:
            params=(hrng.uniform(10.,22.),hrng.uniform(6.,15.),hrng.uniform(28.,45.),hrng.uniform(.1,.8),hrng.uniform(2.,3.5))
            code=template.replace("MODE='attack'",'MODE='+repr(mode)).replace('PARAMS=(12.,10.,30.,.5,2.2)','PARAMS='+repr(params)).encode()
            row={'style':name,'path':name+'/team.py','sha256':digest(code)};held.append(row);z.writestr(row['path'],code)
        z.writestr('manifest.json',json.dumps(held,indent=2)+'\n')
    reg={'project':'NOVA-1 independent model-based coordinated policy learning','base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'champion_sha256':digest((ROOT/'my-team/team.py').read_bytes()),'baseline_source':'experiments/nova-1-baseline/team.py',
        'development':chosen[:32],'qualification':chosen[32:48],'confirmation':chosen[48:64],
        'training_styles':training,'unseen_styles':[q['style'] for q in held],
        'qualification_styles':['v10','v9.1','v10-compact','v10-counter','v10-press','v10-long','long_shooter','tight_links']+[q['style'] for q in held],
        'training_archive_sha256':digest(archive.read_bytes()),'unseen_archive_sha256':digest(holdout.read_bytes()),
        'excluded_values_sha256':digest(json.dumps(sorted(used)).encode()),'excluded_sources':excluded,
        'budget':{'population':24,'generations':4,'native_configs_per_model':24,'main_variants':96,
                  'shortlist_max':8,'shortlist_configs_per_model':128,'refinement_if_not_better':{'population':24,'generations':2,'native_configs_per_model':24},
                  'qualification_pairs':768,'confirmation_pairs_if_qualified':768},
        'learner':'Native-outcome cross-entropy search over 19 active compact policy/geometry parameters; shared shuffled fixtures within generation, rotating six-style league, two elites retained; mean paired points with worst-style and strong-head-to-head penalties. Per-generation best/source/outcomes preserved. No four-point coupled grid.',
        'selection':'Select by paired league points with matchup robustness; no final/unseen evaluation before source and protocols frozen. If development remains weaker, continue only the two registered development refinement generations; publish strongest failure and still run principal qualification. No heldout-driven tuning or optional cohort expansion.',
        'gates':{'more_points':True,'paired_seed_bootstrap_95_lower_gt':0,'zero_policy_exceptions':True,'no_reproducible_deadline_failure':True,'extra_raw_misses_per_1000_max':2.,
                 'heldout_points_delta_gt':0,'heldout_paired_lower_ge':-.10,'worst_style_ppm_delta_ge':-.35,'head_to_head_ppm_delta_ge':-.15,'head_to_head_candidate_ppm_ge':1.25,
                 'official_intake':True,'deadline_ms':20.,'match_ticks':2400,'confirmation_required_if_initial_passes':True},
        'guardrails':'Do not modify main, my-team/team.py, archived controllers, SDK, engine or rules. No clocks, GC policy, affinity or unsupported imports in the controller. Mean speed never replaces raw deadline reliability.',
        'limits':'Local opponents, not access to private school leaders. Previously unseen styles are sealed from this NOVA learning/selection campaign; no online-ranking claim.'}
    (DOC/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
    print('Registered 96 primary + 48 conditional refinement policies, 768 qualification + 768 untouched confirmation pairs.')
if __name__=='__main__':main()
