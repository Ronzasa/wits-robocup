"""Paired whole-seed development analysis; never promote a failed tactic."""
import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/benchmarks'))
from benchmark import aggregate, points


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def seed_statistics(base, candidate):
    before={r['fixture_id']:r for r in base}
    assert len(before)==len(base)==len(candidate)
    assert len({r['fixture_id'] for r in candidate})==len(candidate)
    assert set(before)=={r['fixture_id'] for r in candidate}
    blocks=defaultdict(list)
    for row in candidate:
        old=before[row['fixture_id']]
        for k in ('seed','candidate_slot','candidate_takes_kickoff','split','opponent'):
            assert old[k]==row[k]
        for k in ('engine_version','config_hash','ticks','kickoff_team'):
            assert old['result'][k]==row['result'][k]
        blocks[row['seed']].append(points(row)-points(old))
    means=[sum(v)/len(v) for _,v in sorted(blocks.items())]
    observed=sum(means)
    rng=random.Random(719331)
    boot=sorted(sum(rng.choices(means,k=len(means)))/len(means) for _ in range(10000))
    p=sum(sum(s*d for s,d in zip(signs,means))>=observed-1e-12
          for signs in itertools.product((-1,1),repeat=len(means)))/(2**len(means))
    return {'ppm_change':sum(means)/len(means),'seed_mean_point_deltas':dict(zip(sorted(blocks),means)),
            'bootstrap_95':[boot[250],boot[9749]],'bootstrap_97_5':[boot[125],boot[9874]],
            'exact_one_sided_sign_flip_p':p,'seed_blocks':len(means)}


def telemetry(rows):
    out={}
    for key in ('ticks','episodes','associations'):
        c=Counter()
        for row in rows:c.update(row.get('titan_v11',{}).get(key,{}))
        out[key]=dict(c)
    out['examples']=[{'seed':r['seed'],'side':r['candidate_slot'],
        'kickoff':r['candidate_takes_kickoff'],'opponent':Path(r['opponent']).parent.name,**e}
        for r in rows for e in r.get('titan_v11',{}).get('examples',[])]
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();run=args.run.resolve();out=args.out
    assert not out.exists(), 'Preserve prior analysis.'
    metadata=json.loads((run/'metadata.json').read_text())
    assert 'finished_utc' in metadata, 'Never select from an incomplete cohort.'
    protocol=metadata['protocol'];reg=json.loads((ROOT/protocol['registration']).read_text())
    repeats=read(run/'timing-repeats.jsonl')
    raws={name:read(run/'raw'/name/'matches.jsonl') for name in protocol['sources']}
    accepted={name:read(run/'accepted'/name/'matches.jsonl') for name in protocol['sources']}
    expected=len(protocol['opponents'])*sum(map(len,protocol['seeds'].values()))*4
    for name,rows in raws.items():
        assert len(rows)==expected
        snap=run/'sources'/name/'team.py'
        assert hashlib.sha256(snap.read_bytes()).hexdigest()==protocol['sources'][name]['sha256']
        assert hashlib.sha256((ROOT/protocol['sources'][name]['path']).read_bytes()).hexdigest()==protocol['sources'][name]['sha256']
        assert all(r['result']['ticks']==2400 and r['result']['terminal_reason']=='time_limit' for r in rows)
    result={'stage':'independent development','protocol':protocol,'registration':reg,
        'raw_summary':{n:aggregate(r) for n,r in raws.items()},
        'accepted_summary':{n:aggregate(r) for n,r in accepted.items()},'candidates':{},
        'qualification_run':False,'active_champion_modified':False}
    for name in ('architect','firewall'):
        b,c=result['raw_summary']['v10'],result['raw_summary'][name]
        ab,ac=result['accepted_summary']['v10'],result['accepted_summary'][name]
        stats=seed_statistics(raws['v10'],raws[name]);astats=seed_statistics(accepted['v10'],accepted[name])
        tel=telemetry(raws[name])
        intake=json.loads((run/(name+'-validation.json')).read_text())
        candidate_repeats=[r for r in repeats if r['source']==name]
        reproduced=sum(r['result']['result']['stats'][r['result']['candidate_slot']].get('policy_timeouts',0)>0
                       for r in candidate_repeats if r['attempt']==1)
        malformed=sum(v for k,v in c['validation'].items()
                      if k not in ('actions_validated','players_validated','rejected_kicks'))
        styles={}
        for style in protocol['opponents']:
            rows0=[r for r in raws['v10'] if Path(r['opponent']).parent.name==style]
            rows1=[r for r in raws[name] if Path(r['opponent']).parent.name==style]
            styles[style]={'v10':aggregate(rows0),'candidate':aggregate(rows1)}
        extra=(c['policy_timeouts']-b['policy_timeouts'])*1000/expected
        ceiling=ab['decision_mean_ms']*1.35+.04
        key='architect_support' if name=='architect' else 'firewall_screen'
        gates={'more_raw_and_accepted_points':c['points']>b['points'] and ac['points']>ab['points'],
            'positive_raw_97_5_seed_lower':stats['bootstrap_97_5'][0]>0,
            'positive_accepted_97_5_seed_lower':astats['bootstrap_97_5'][0]>0,
            'raw_exact_sign_flip_p_at_most_0_025':stats['exact_one_sided_sign_flip_p']<=.025,
            'accepted_exact_sign_flip_p_at_most_0_025':astats['exact_one_sided_sign_flip_p']<=.025,
            'no_style_points_regression':all(s['candidate']['points']>=s['v10']['points'] for s in styles.values()),
            'five_executed_tactic_episodes':tel['episodes'].get(key,0)>=5,
            'intent_metric':(c['passes_completed']>b['passes_completed'] and c['turnovers']<=b['turnovers']) if name=='architect' else c['goals_against']<b['goals_against'],
            'zero_policy_exceptions':c['policy_errors']==0 and ac['policy_errors']==0,
            'no_reproducible_deadline_failure':reproduced==0,
            'raw_deadline_allowance':extra<=2.,'mean_runtime':ac['decision_mean_ms']<=ceiling,
            'official_sdk':intake['ok'] and not intake['folder_errors'],'legal_actions':malformed==0,
            'complete_registered_cohort':len(raws[name])==expected}
        result['candidates'][name]={'raw_seed_statistics':stats,'accepted_seed_statistics':astats,
            'gates':gates,'supported':all(gates.values()),'tactics':tel,'by_opponent':styles,
            'extra_raw_misses_per_1000':extra,'mean_runtime_ceiling_ms':ceiling,
            'reproduced_candidate_deadline_failures':reproduced}
    passing=[name for name,r in result['candidates'].items() if r['supported']]
    result['passing_candidates']=passing
    result['decision']='INTEGRATION_JUSTIFIED' if len(passing)==2 else 'QUALIFICATION_JUSTIFIED' if passing else 'RETAIN_V10_REJECT_BOTH'
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
    lines=['# TITAN v11 — Passing Lane Architect and Counterattack Firewall','',
        '**Development decision: '+result['decision']+'.** No active champion or main changes.','',
        '## Scope and method','',
        'Two independent, movement-only additions to frozen Guardiola/Klopp TITAN v10.0. The all-off source preserves v10 actions, debug and receive plans. Goalkeeper Power Play, Goalkeeper Trap, Pinball Slingshot and Cooldown Ambush are absent from these sources. No combined source was tested unless both independent candidates passed.','',
        f'Eight unused development seeds × pressing, compact and counterattacking v10 opponents × both sides × both kickoffs = {expected} paired configurations, {expected*3} native full matches. Sources, opponent archive, seeds, shuffle order and selection rules were frozen before play. Every fixture used 2,400 ticks, engine 0.1.0, configuration 372990895c7eca2a and the unchanged native 20 ms deadline. One timed worker, no concurrent tests.','',
        'An initial trial (73 completed full matches, excluded from selection) was interrupted on a code-review finding before outcome analysis: team-control metadata without a friendly holder could have bypassed the existing cover safeguard. The final source requires a friendly controlling player as well as team control and no opposing last touch. Every seed allocated to the interrupted protocol, including its reserves, was excluded before registering the final cohort. Partial raw native records, frozen old sources and protocols are retained. No interrupted score was used for tuning.','',
        'The three styles are frozen local strong v10 variants, not private league teams. Source hashes are retained in registration, protocol and native metadata; unused integration and qualification cohorts are reserved separately.','',
        '## Implementation','',
        '- **Tactic 05, Passing Lane Architect:** examines at most two free supporters, three local targets and two pass speeds. Existing carrier-contact, dense drag/trajectory simulation, defender races and executable receiver rollouts validate each prospective lane, including the exact first movement with teammate avoidance. Predicted defender separation helps rank lanes. Teammate interference is rejected. The established pass selector still chooses actual passes, and new receive plans own their movement. The carrier, keeper, both cover assignments, chaser and live receiver are excluded. Existing transition bursts, counterpress and restart restrictions take priority. Speculative receiver-aim state is restored.','- **Tactic 06, Counterattack Firewall:** projects opposing outlets 0.6 seconds from public velocity, ranks plausible pass-plus-run routes toward our goal, and screens the quickest threatening corridor using the existing cover defender. Its target never advances beyond the baseline cover line, stays within 12 metres of its depth and an 18-metre displacement budget, and requires a reachable guard position. It cannot move a carrier, chaser, goalkeeper or live receiver. At possession loss or opposing touch it releases immediately to unchanged v10 defensive interception, counterpress and cover safeguards; there is no persistent attack target.','- Every original v10 method except the two call sites in `act` is AST-identical. There is no new pass/shot policy, goalkeeper logic, physics routine, game configuration or deadline.','',
        '## Original raw native outcomes','',
        '| Source | Matches | Wins | Draws | Losses | Points | GF–GA | Completed passes | Turnovers | Deadline misses | Exceptions |',
        '|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|']
    for name,s in result['raw_summary'].items():
        lines.append(f"| {name} | {s['matches']} | {s['wins']} | {s['draws']} | {s['losses']} | {s['points']} | {s['goals_for']}–{s['goals_against']} | {s['passes_completed']} | {s['turnovers']} | {s['policy_timeouts']} | {s['policy_errors']} |")
    lines+=['','Timeout repeats never erase raw misses or original competitive outcomes. Raw and accepted/repeat comparisons are both retained; a candidate must pass both point/significance requirements.','',
        '## Statistical selection and reliability','',
        'The preregistration requires strictly positive 97.5% whole-seed bootstrap lower bounds and one-sided exact sign-flip p ≤ 0.025 for each candidate (a correction for two independent tactic hypotheses), more raw and accepted points, no points regression in any registered style, at least five executed tactic episodes, and the tactic-specific intent metric. Architect needs more completed passes without more turnovers; Firewall needs fewer concessions. All existing SDK, legality, exception, deadline/reproducibility and runtime gates also apply. The original 768-pair minimum is a qualification gate; it is not waived for promotion or treated as a development fixture requirement.','',
        '| Candidate | Raw PPM delta | 97.5% seed interval | Exact p | Accepted mean ms | Raw max ms | Episodes | Development supported |',
        '|---|---:|---|---:|---:|---:|---:|---|']
    for name,r in result['candidates'].items():
        s=r['raw_seed_statistics'];c=result['raw_summary'][name];ac=result['accepted_summary'][name]
        key='architect_support' if name=='architect' else 'firewall_screen'
        lines.append(f"| {name} | {s['ppm_change']:+.6f} | {s['bootstrap_97_5']} | {s['exact_one_sided_sign_flip_p']:.6f} | {ac['decision_mean_ms']:.6f} | {c['decision_max_ms']:.6f} | {r['tactics']['episodes'].get(key,0)} | {r['supported']} |")
    for name,r in result['candidates'].items():
        lines+=['',f'### {name} actual commands and failures','',
            'Telemetry counts (support/screen are executed movements; loss release is a state event): `'+json.dumps(r['tactics']['ticks'],sort_keys=True)+'`.','',
            'Team-level episodes: `'+json.dumps(r['tactics']['episodes'],sort_keys=True)+'`.','',
            'Failed development gates: '+(', '.join(k for k,v in r['gates'].items() if not v) or 'none')+'.','',
            '| Opponent | v10 points | Candidate points | v10 GF–GA | Candidate GF–GA |','|---|---:|---:|---|---|']
        for style,v in r['by_opponent'].items():
            b,c=v['v10'],v['candidate']
            lines.append(f"| {style} | {b['points']} | {c['points']} | {b['goals_for']}–{b['goals_against']} | {c['goals_for']}–{c['goals_against']} |")
    lines+=['','## Attribution and limitations','',
        'Support and screen labels are counted only if the final issued player movement matches the proposed tactic movement, changes the baseline movement meaningfully, and the SDK accepts the decision under 20 ms without error. The loss-release label records relinquishing tactical ownership; it is a state event, not a new movement or a prevented counterattack. Supporter commands can occur twice in a tick; episodes are team-level groups separated by more than five ticks without the same label. A movement command is not proof of a completed pass or a prevented goal. Native total passes, turnovers, goals, wins and points above are actual engine results; five-second post-command associations in JSON are explicitly non-causal. No goals are credited to a tactic simply because it activated.','',
        'Eight seed blocks limit precision and fixed local opponents limit generalization. All sources and thresholds were frozen before outcomes; these results were not used to tune the same cohort.','',
        '## Verification and reproduction','',
        '133 controller regressions passed before native testing, including original safety/physics checks and 13 new tests for method equivalence, all-off equivalence, role authority, executable lanes, defender motion, immediate loss release and telemetry command ownership. Four additional statistical-analysis regressions passed after matches, checking exact sign-flip probabilities, zero-effect intervals and paired-fixture integrity (137 tests total). Native SDK intakes and static inspection are retained for each tested source.','',
        '`python tools/titan_v11/build.py` reproduces isolated source hashes. With the bundled official native extension installed, run `PYTHONPATH=student-sdk python -m unittest discover -s tests -q`, then `PYTHONPATH=student-sdk python tools/benchmarks/run_titan_v11.py --protocol docs/titan-v11/development-protocol.json --out /new/output/path`. Analyze with `python tools/titan_v11/analyze.py --run /new/output/path --out /new/results.json`. Keep one timed worker.','',
        'The native evidence archive retains raw/accepted full-match rows, official validation, frozen sources/opponents, slow decisions, timing histograms, cgroup diagnostics and exact timeout repeats with a verified per-file SHA-256 manifest.','']
    b=result['raw_summary']['v10']
    a=result['raw_summary']['architect'];f=result['raw_summary']['firewall']
    lines+=['## Interpretation','',
        f"Architect gained {a['points']-b['points']} points, completed {a['passes_completed']-b['passes_completed']} more passes and recorded {b['turnovers']-a['turnovers']} fewer turnovers. Its gains were uneven; the per-opponent table shows the compact-opponent regression alongside the gains against pressing and counterattacking opponents. The broad seed interval and exact p-value do not establish a reliable overall advantage; the compact regression also fails the preservation gate.",'',
        f"Firewall gained {f['points']-b['points']} points but conceded {f['goals_against']-b['goals_against']} more goals and recorded {f['turnovers']-b['turnovers']} more turnovers. The screening commands did not achieve the tactic's concession-reduction objective. Its points estimate is also statistically inconclusive.",'',
        'The baseline and Firewall each had one raw native deadline miss; Architect had none. First exact repeats were clean and no candidate deadline failure reproduced. The raw misses remain counted; none was waived as environmental noise. All intakes, action-legality, exception and runtime gates passed.','']
    if not passing:
        lines+=['**Both candidates are rejected for competitive use. No combination, fresh qualification or promotion was run.** Retaining their code as experiments does not establish an improvement; v10 remains the champion.','']
    else:
        lines+=['Independent support justifies only the next registered evaluation stage; it does not authorize champion changes. See the stage decision JSON.','']
    out.with_suffix('.md').write_text('\n'.join(lines))
    print(result['decision'])
    for name,r in result['candidates'].items():
        print(name,'raw points',result['raw_summary'][name]['points'],'v10',result['raw_summary']['v10']['points'],
              'supported',r['supported'],'commands',r['tactics']['ticks'],
              'failed',[k for k,v in r['gates'].items() if not v])


if __name__=='__main__':main()
