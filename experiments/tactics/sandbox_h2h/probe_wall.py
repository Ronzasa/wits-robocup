"""Controlled shots at the gaps of a static clearing wall (wall_shot.py geometry). Our shooter is player 4."""
import sys, math, itertools
sys.path.insert(0,'/home/claude/wits-robocup/experiments/tactics/harness')
import common; from common import soccer
from soccer import TeamController, TeamAction, PlayerAction
W='/home/claude/sandbox/wall_shot.py'
class Shooter(TeamController):
    name='shooter'; version='1'
    def __init__(self, sx, sy, power, aim_y):
        self.sx,self.sy,self.power,self.aim_y=sx,sy,power,aim_y; self.phase=0
    def initial_formation(self,f): return [(-45,0),(-20,-8),(-20,8),(-10,-10),(-5,0.0)]
    def act(self,obs):
        a=TeamAction(); bx,by=obs.ball.position
        for p in obs.my_players:
            if p.id!=4:
                a.set(p.id,PlayerAction(movement=(0,0))); continue
            px,py=p.position
            lead=2.0 if bx<self.sx else 0.0
            dx,dy=bx+lead*0.3-px,by-py; n=math.hypot(dx,dy); mv=(dx/n,dy/n) if n>1e-6 else (0,0)
            if obs.can_kick(p.id) and self.phase<2:
                if bx>=self.sx:
                    kx,ky=50.0-bx,self.aim_y-by; kn=math.hypot(kx,ky)
                    a.set(p.id,PlayerAction(movement=mv,kick_direction=(kx/kn,ky/kn),kick_power=self.power)); self.phase=2; self.shot_tick=obs.tick; continue
                ty=self.sy; kx,ky=1.0,(ty-by)*0.08; kn=math.hypot(kx,ky)
                a.set(p.id,PlayerAction(movement=mv,kick_direction=(kx/kn,ky/kn),kick_power=0.3)); continue
            a.set(p.id,PlayerAction(movement=mv if self.phase<2 else (0,0)))
        return a
def trial(sx,sy,power,aim_y):
    m=soccer.play_match(Shooter(sx,sy,power,aim_y),W,seed=1,kickoff_team=0,max_ticks=500)
    return m.score[0]
if __name__=='__main__':
    res={}
    for gap,ay in (('A',-0.9),('B',3.2)):
        for power in (0.5,1.0):
            for sx in (30.0,38.0):
                for sy in (-6.0,0.0,6.0):
                    g=trial(sx,sy,power,ay); res[(gap,power,sx,sy)]=g
                    print(gap,'aim y',ay,'power',power,'from',(sx,sy),'goals',g,flush=True)
    print('goals in',sum(1 for v in res.values() if v>0),'of',len(res))
