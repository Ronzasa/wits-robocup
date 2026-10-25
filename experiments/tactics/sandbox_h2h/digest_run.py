"""Fingerprint a team file: hash of every action on every tick across a fixed list of matches."""
import sys, hashlib, importlib.util, multiprocessing as mp, json
sys.path.insert(0,'/home/claude/wits-robocup/experiments/tactics/harness')
import common; from common import soccer
from soccer import TeamController
OPPS=['/home/claude/sandbox/challenger_stiff_wall.py','/home/claude/sandbox/champion_candidate.py',
      common.OPPONENTS['lock_no_breaker'],common.OPPONENTS['bus_wall'],common.OPPONENTS['press_formation'],
      common.OPPONENTS['dribbler'],'ball_chaser','structured_attack','balanced','man_marking']
def load(path):
    spec=importlib.util.spec_from_file_location('tm_'+hashlib.md5(path.encode()).hexdigest()[:6],path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    for v in vars(m).values():
        if isinstance(v,type) and issubclass(v,TeamController) and v is not TeamController: return v
def one(a):
    path,opp,seed,side=a
    cls=load(path); c=cls(); h=hashlib.sha1(); orig=c.act
    def act(obs,orig=orig):
        r=orig(obs)
        h.update(repr(sorted((i,tuple(round(x,6) for x in (p.movement or ())),
            tuple(round(x,6) for x in (p.kick_direction or ())),round(p.kick_power or 0,6)) for i,p in r.players.items())).encode())
        return r
    c.act=act
    x,y=(c,opp) if side==0 else (opp,c)
    m=soccer.play_match(x,y,seed=seed,kickoff_team=side,max_ticks=2400)
    active=getattr(c,'_active',None)
    return opp.split('/')[-1],seed,side,list(m.score),h.hexdigest()[:16],active
if __name__=='__main__':
    path=sys.argv[1]; out=sys.argv[2]
    off=int(sys.argv[3]) if len(sys.argv)>3 else 0
    if off: jobs=[(path,o,off+i,sd) for i,o in enumerate(OPPS) for sd in (0,1)]
    else: jobs=[(path,o,50+i,i%2) for i,o in enumerate(OPPS)]+[(path,OPPS[0],70,0),(path,OPPS[0],71,1),(path,OPPS[1],72,1),(path,OPPS[1],73,0)]
    with mp.Pool(2) as p: R=p.map(one,jobs)
    json.dump(R,open(out,'w'),indent=0)
    for r in R: print(r)
