import collections, gzip, importlib.util, json, sys
from pathlib import Path
ROOT=Path('/workspace/wits-robocup')
sys.path.insert(0,str(ROOT/'student-sdk'))
from soccer import play_match
spec=importlib.util.spec_from_file_location('frozen',ROOT/'experiments/titan-11/team.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
out=Path('/workspace/work/titan-11-repair')
records=[];counts=collections.Counter()
class Audit(m.Guardiola2011):
    def _v10_choose_kick(self,*args):
        result=super()._v10_choose_kick(*args)
        self.base=(result,self._touch_movement,self._pass_plan,self._bank_plan)
        return result
    def _ti_evaluate(self,node,*args):
        rated=super()._ti_evaluate(node,*args)
        self.ratings.append({'kind':node[0],'option':node[1],'aim':node[3],'value':rated[0] if rated else None})
        return rated
    def _pass_path(self,*args,**kw):
        key=(args,tuple(kw.items()))
        counts['path_calls']+=1
        if key in self.path_keys:counts['duplicate_paths']+=1
        self.path_keys.add(key)
        return super()._pass_path(*args,**kw)
    def act(self,obs):
        self.path_keys=set();self.ratings=[];self.base=None
        action=super().act(obs)
        if self._ti_selected!='v10':
            for q in obs.my_players:
                a=action.players[q.id]
                if a.kick_direction is None:continue
                launch=self._carrier_contact((q.id,*q.position,*q.velocity),*obs.ball.position,*self._requested_velocity(*obs.ball.velocity,(a.kick_direction,a.kick_power)),a.movement)
                future=[]
                if self._pass_plan:
                    future=[self._pass_plan,self._bank_plan]
                records.append({'fixture':fixture,'tick':obs.tick,'ball':[*obs.ball.position,*obs.ball.velocity],
                    'selected':self._ti_selected,'launch':launch,'base':self.base,'ratings':self.ratings,
                    'pass_plan':future,'receive_plan':self._receive_plan})
        return action
for file in sorted(Path('/workspace/work/titan-11-intelligence/selected-replays').glob('*challenger.report.json')):
    row=json.loads(file.read_text())['original_fixture'];fixture={k:row[k] for k in ('seed','candidate_slot','candidate_takes_kickoff','opponent')}
    c=Audit();side=row['candidate_slot'];teams=[c,row['opponent']]
    if side:teams.reverse()
    result=play_match(*teams,seed=row['seed'],kickoff_team=side if row['candidate_takes_kickoff'] else 1-side,config_path=str(ROOT/'configs/default.toml'),max_ticks=2400,per_decision_timeout_ms=20.).result
    print(file.name,'score',result['score'],flush=True)
(out/'failure-inspection.json').write_text(json.dumps({'counts':dict(counts),'decisions':records},indent=2)+'\n')
print(dict(counts))
for r in records:
    print('tick',r['tick'],'selected',r['selected'],'launch',r['launch'],'plan',r['receive_plan'],'baseline',r['base'][2:])
