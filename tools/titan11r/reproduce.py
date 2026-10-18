"""Instrumented native repetitions of the two known reception-gap matches."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'student-sdk'))
from soccer import play_match


def load(source):
    spec=importlib.util.spec_from_file_location('repair_diagnostic',source)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original-replays',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();assert not a.out.exists();a.out.mkdir(parents=True)
    summary=[]
    for index,path in enumerate(sorted(a.original_replays.glob('*challenger.report.json'))):
        fixture=json.loads(path.read_text())['original_fixture']
        for name,source in [('frozen',ROOT/'experiments/titan-11/team.py'),('repair',ROOT/'experiments/titan-11-r/team.py')]:
            module=load(source);slow=[];receptions=[];pending=None
            class Trace(module.Guardiola2011):
                def act(self,obs):
                    nonlocal pending
                    if pending is not None:
                        if obs.ball.last_touch==pending['receiver']:
                            receptions.append({**pending,'outcome':'intended_touch','end':obs.tick});pending=None
                        elif obs.ball.last_touch not in (None,pending['passer']) or obs.tick-pending['tick']>52:
                            receptions.append({**pending,'outcome':'opponent_touch' if obs.ball.last_touch is not None and obs.ball.last_touch>=5 else 'other_or_uncollected','end':obs.tick});pending=None
                    action=super().act(obs)
                    for q in obs.my_players:
                        command=action.players[q.id]
                        if command.kick_direction is None or self._pass_plan is None:continue
                        launch=self._carrier_contact((q.id,*q.position,*q.velocity),*obs.ball.position,
                            *self._requested_velocity(*obs.ball.velocity,(command.kick_direction,command.kick_power)),command.movement)
                        if launch is None or math.hypot(launch[2],launch[3])>10.5:continue
                        receiver=next((p for p in obs.my_players if p.id==self._pass_plan[0]),None)
                        coordinated=self._receive_plan is not None and self._receive_plan[:2]==(self._pass_plan[0],q.id)
                        item={'tick':obs.tick,'passer':q.id,'receiver':self._pass_plan[0],
                            'launch':launch,'speed':math.hypot(launch[2],launch[3]),'coordinated':coordinated,
                            'receiver_command':command.movement if receiver is None else action.players[receiver.id].movement}
                        if coordinated:
                            expected=self._move((receiver.id,*receiver.position,*receiver.velocity),self._target(*self._receive_aim[1]))
                            assert action.players[receiver.id].movement==expected
                            item['verified_aim']=self._receive_aim[1]
                        slow.append(item)
                        if pending is not None:receptions.append({**pending,'outcome':'superseded','end':obs.tick})
                        pending=item
                    return action
            side=fixture['candidate_slot'];teams=[Trace(),fixture['opponent']]
            if side:teams.reverse()
            label=f'{index}-{name}';native=a.out/(label+'.native.json')
            result=play_match(*teams,seed=fixture['seed'],kickoff_team=side if fixture['candidate_takes_kickoff'] else 1-side,
                config_path=str(ROOT/'configs/default.toml'),max_ticks=2400,per_decision_timeout_ms=20.,record_replay=str(native)).result
            if pending is not None:receptions.append({**pending,'outcome':'pending_at_end'})
            report={'source':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                'fixture':fixture,'result':result,'canonical_score':[result['score'][side],result['score'][1-side]],
                'slow_named_passes':slow,'receptions':receptions,
                'scope':'Fixed instrumented development reproduction; excluded from strength, latency and promotion inference.'}
            (a.out/(label+'.json')).write_text(json.dumps(report,indent=2)+'\n')
            with gzip.open(str(native)+'.gz','wb') as f:f.write(native.read_bytes())
            native.unlink()
            summary.append({'label':label,'score':report['canonical_score'],'slow_passes':len(slow),'coordinated':sum(x['coordinated'] for x in slow),
                'intended_touches':sum(x['outcome']=='intended_touch' for x in receptions)})
            print(summary[-1],flush=True)
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')


if __name__=='__main__':main()
