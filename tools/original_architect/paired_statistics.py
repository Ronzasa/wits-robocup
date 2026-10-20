"""Balanced whole-seed statistics with integer point sums until final division."""
from collections import defaultdict
import itertools
import random


def points(row):
    i=row['candidate_slot'];a,b=row['result']['score'][i],row['result']['score'][1-i]
    return 3 if a>b else 1 if a==b else 0


def paired(base,candidate,resamples=10000):
    before={r['fixture_id']:r for r in base};after={r['fixture_id']:r for r in candidate}
    assert len(before)==len(base)==len(after)==len(candidate) and set(before)==set(after)
    blocks=defaultdict(list)
    for key in sorted(before):
        b,c=before[key],after[key]
        for k in ('seed','split','opponent','candidate_slot','candidate_takes_kickoff'):assert b[k]==c[k]
        for k in ('engine_version','config_hash','ticks','kickoff_team'):assert b['result'][k]==c['result'][k]
        blocks[b['seed']].append(points(c)-points(b))
    sizes={len(v) for v in blocks.values()};assert len(sizes)==1
    size=sizes.pop();totals=[sum(v) for _,v in sorted(blocks.items())];n=len(totals)
    rng=random.Random(719331)
    samples=sorted(sum(rng.choices(totals,k=n))/(n*size) for _ in range(resamples))
    exact=sum(sum(sign*x for sign,x in zip(signs,totals))>=sum(totals)
              for signs in itertools.product((-1,1),repeat=n))/(2**n)
    return {'ppm_change':sum(totals)/(n*size),'seed_blocks':n,'fixtures_per_seed':size,
        'seed_point_differences':dict(zip(sorted(blocks),totals)),
        'bootstrap_95':[samples[int(.025*resamples)],samples[int(.975*resamples)-1]],
        'bootstrap_97_5':[samples[int(.0125*resamples)],samples[int(.9875*resamples)-1]],
        'exact_one_sided_sign_flip_p':exact,'resamples':resamples}
