"""Export all TITAN-12B native metrics and paired fixture outcomes without rewriting raw evidence."""
import argparse
import csv
import json
from pathlib import Path

from benchmark import aggregate,candidate_score,points


def rows(path):return [json.loads(l) for l in path.read_text().splitlines()]


def extras(records):
    metrics=aggregate(records)
    native=[r['result']['stats'][r['candidate_slot']] for r in records]
    distance=sum(s['pass_distance'] for s in native)
    buckets=[s['decision_time_ms']['bucket_counts'] for s in native]
    metrics['native_decision_bucket_counts']=[sum(v[i] for v in buckets) for i in range(16)]
    assert sum(metrics['native_decision_bucket_counts'])==metrics['decisions']
    metrics.update(pass_distance=distance,pass_distance_per_match=distance/len(records),
        mean_completed_pass_distance=distance/metrics['passes_completed'] if metrics['passes_completed'] else None,
        turnovers_per_match=metrics['turnovers']/len(records),
        passes_uncollected_per_match=metrics['passes_uncollected_derived']/len(records),
        attacking_territory_fraction=sum(s['territory_ticks'] for s in native)/sum(r['result']['ticks'] for r in records))
    return metrics


def quantile_bins(hist,width):
    hist={int(k):v for k,v in hist.items()};n=sum(hist.values());answer={}
    for label,q in [('p95',.95),('p99',.99),('p999',.999)]:
        wanted=int((n-1)*q);seen=0
        for bucket,count in sorted(hist.items()):
            seen+=count
            if seen>wanted:
                answer[label+'_bin_ms']=[bucket*width,(bucket+1)*width];break
    return answer


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',type=Path,nargs='+',required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():p.error('Preserve previous exported evidence.')
    args.out.mkdir(parents=True)
    reports={};flat=[];fixtures=[]
    for root in args.runs:
        meta=json.loads((root/'metadata.json').read_text());assert meta.get('finished_utc')
        hist=json.loads((root/'decision-histograms.json').read_text())
        per_source={}
        for name,spec in meta['protocol']['sources'].items():
            raw=rows(root/'raw'/name/'matches.jsonl');accepted=rows(root/'accepted'/name/'matches.jsonl')
            accepted_by_id={r['fixture_id']:r for r in accepted}
            assert len(raw)==len(accepted)==len(accepted_by_id)
            a,b=extras(raw),extras(accepted)
            measured=sum(hist['histograms'][name].values())
            assert 0<measured<=a['decisions']
            distribution=quantile_bins(hist['histograms'][name],hist['bin_width_ms'])
            distribution['histogram_coverage_fraction']=measured/a['decisions']
            per_source[name]={'source':spec,'raw':a,'strength_first_clean':b,'raw_timing':distribution,
                'by_opponent':{style:extras([r for r in accepted if Path(r['opponent']).parent.name==style])
                    for style in meta['protocol']['opponents']}}
            flat.append({'stage':root.name,'source':name,'sha256':spec['sha256'],
                **{k:v for k,v in b.items() if not isinstance(v,(dict,list))},
                'raw_timeouts':a['policy_timeouts'],'raw_mean_ms':a['decision_mean_ms'],
                'raw_max_ms':a['decision_max_ms'],
                **{k:json.dumps(v) for k,v in distribution.items()}})
            for r in raw:
                used=accepted_by_id[r['fixture_id']];gf,ga=candidate_score(r);sf,sa=candidate_score(used)
                s=r['result']['stats'][r['candidate_slot']]
                fixtures.append({'stage':root.name,'source':name,'seed':r['seed'],
                    'opponent':Path(r['opponent']).parent.name,'side':r['candidate_slot'],
                    'kickoff':r['candidate_takes_kickoff'],'raw_gf':gf,'raw_ga':ga,'raw_points':points(r),
                    'raw_deadline_misses':s['policy_timeouts'],'raw_policy_errors':s['policy_errors'],
                    'raw_max_ms':s['decision_time_ms']['max_ms'],'strength_gf':sf,'strength_ga':sa,
                    'strength_points':points(used),'exact_repeat_used':used!=r})
        reports[root.name]=per_source
    (args.out/'metrics.json').write_text(json.dumps(reports,indent=2)+'\n')
    for name,data in [('metrics.csv',flat),('paired-scores.csv',fixtures)]:
        with (args.out/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
    print('Exported',len(flat),'source summaries and',len(fixtures),'raw fixture outcomes.')


if __name__=='__main__':main()
