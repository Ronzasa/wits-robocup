"""Public native movement probes; no state injection or rule changes.

Compare one side's restoring defenders with and without sustained attackers.
The probes are untimed mechanics experiments, not competition fixtures.
"""
import argparse,itertools,json,math
from pathlib import Path
from soccer import SoccerEnv
ROOT=Path(__file__).resolve().parents[2]
def unit(x,y):
 d=math.hypot(x,y);return (x/d,y/d) if d>1e-9 else (0.,0.)
def run(push,wall):
 with SoccerEnv(config_path=str(ROOT/'configs/default.toml'),max_ticks=700) as e:
  obs=e.reset(seed=3249100101,kickoff_team=0)
  a,b=obs['team_a'],obs['team_b'];world={p.id-5:p.position for p in a.opponents}
  frame=min(itertools.product((-1,1),repeat=2),key=lambda s:sum(math.dist(world[p.id],(s[0]*p.position[0],s[1]*p.position[1])) for p in b.my_players))
  homes={i:(49.,(2-i)*2.8) for i in range(5)} if wall else {i:(15.,15.+i*3.) for i in range(5)}
  attack={0:(-49.,0.),4:(38.,15.)}
  for i in (1,2,3):
   q=homes[i-1];attack[i]=(q[0]-3.,q[1]+1.7)
  trajectory=[]
  for tick in range(620):
   actions={}
   for side,key in enumerate(('team_a','team_b')):
    acts={};f=(1,1) if side==0 else frame
    for p in obs[key].my_players:
     x,y=p.position[0]*f[0],p.position[1]*f[1]
     target=(attack if side==0 else homes)[p.id]
     if tick<50:target=(x,20.+p.id*2.)
     elif tick<230:target=(target[0],20.+p.id*2.)
     dx,dy=target[0]-x,target[1]-y
     ux,uy=unit(dx,dy);speed=min(8.,math.hypot(dx,dy)*5.)
     vx,vy=p.velocity[0]*f[0],p.velocity[1]*f[1]
     move=((ux*speed-vx*.9), (uy*speed-vy*.9));length=max(1.,math.hypot(*move));move=(move[0]/length,move[1]/length)
     if side==0 and tick>=400 and push and p.id in (1,2,3):
      q=next(q for q in obs['team_a'].opponents if q.id==p.id-1+5)
      move=unit(q.position[0]+.5-x,q.position[1]-2.4-y)
     acts[p.id]=dict(movement=(move[0]*f[0],move[1]*f[1]))
    actions[key]=acts
   obs,_=e.step(actions)
   if tick>=390:
    trajectory.append(dict(tick=tick,defenders=[dict(id=p.id,position=p.position,velocity=p.velocity) for p in obs['team_a'].opponents]))
  return dict(push=push,wall=wall,config_hash=e.config_hash,trace=trajectory,result=e.result())
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args()
 rows=[run(push,wall) for wall in (False,True) for push in (False,True)]
 comparisons=[]
 for i in (0,2):
  control,pushed=rows[i:i+2];ds=[]
  for c,a in zip(control['trace'],pushed['trace']):
   for q,r in zip(c['defenders'],a['defenders']):
    if q['id'] in (5,6,7):ds.append(math.dist(q['position'],r['position']))
  comparisons.append(dict(wall=control['wall'],max_displacement_vs_control=max(ds),final_positions=pushed['trace'][-1]['defenders']))
 args.out.parent.mkdir(parents=True,exist_ok=True)
 with args.out.open('x') as f:json.dump(dict(scope='untimed public mechanics probes, not tournament matches',comparisons=comparisons,runs=rows),f,indent=2)
 print(json.dumps(comparisons))
if __name__=='__main__':main()
