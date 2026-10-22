"""External observation of actual native events; never alters an action."""
from collections import Counter
import math


class Telemetry:
    def __init__(self):
        self.counts=Counter()
        self.pending={}
        self.previous=None
        self.previous_launch=None
        self.previous_moves={}
        self.examples=[]

    def note(self,event,obs,plan=None):
        if len(self.examples)>=32:
            return
        row={'event':event,'tick':obs.tick,'ball':[*obs.ball.position,*obs.ball.velocity],
             'last_touch':obs.ball.last_touch,'holder':obs.ball.controlling_player,
             'score':list(obs.score)}
        if plan:
            row.update({'kind':plan['kind'],'player':plan['player'],'started':plan['started']})
            if 'recipient' in plan:row['recipient']=plan['recipient']
        self.examples.append(row)

    def close(self,kind,reason,obs):
        p=self.pending.pop(kind)
        self.counts[kind+'_'+reason]+=1
        self.note(reason,obs,p)

    def observe(self,obs,answer,controller=None):
        action,elapsed,error=answer
        events=tuple(obs.events)
        for pid,(tick,x,y) in self.previous_moves.items():
            player=next((p for p in obs.my_players if p.id==pid),None)
            if player is not None and obs.tick==tick+1 and math.hypot(player.position[0]-x,player.position[1]-y)>1e-6:
                self.counts['ambush_native_movement_steps']+=1
        self.previous_moves={}
        # Observation events use the same normalized IDs as the controller.
        wall=False
        if self.previous is not None:
            px,py,pvx,pvy,last,tick=self.previous
            launch=self.previous_launch
            kicked=launch is not None and any(e.get('kind')=='kick' and e.get('player')==launch[0]
                and abs(e.get('tick',-100)-tick)<=1 for e in events)
            if obs.tick==tick+1 and (obs.ball.last_touch==last or kicked):
                dt=1./obs.field.simulation_hz
                if kicked:x,y,vx,vy=launch[1]
                else:x,y,vx,vy=px+pvx*dt,py+pvy*dt,pvx,pvy
                xb=obs.field.width*.5-obs.field.ball_radius
                yb=obs.field.height*.5-obs.field.ball_radius
                if abs(y)>yb:
                    side=1. if y>0. else -1.
                    y=side*2.*yb-y;vy=-side*abs(vy)*.75;wall=True
                if abs(x)>xb:
                    if abs(y)>obs.field.goal_width*.5:
                        side=1. if x>0. else -1.
                        x=side*2.*xb-x;vx=-side*abs(vx)*.75;wall=True
                    else:wall=False
                if not kicked:
                    vx*=obs.field.ball_friction;vy*=obs.field.ball_friction
                wall=wall and max(abs(x-obs.ball.position[0]),abs(y-obs.ball.position[1]),
                    abs(vx-obs.ball.velocity[0]),abs(vy-obs.ball.velocity[1]))<.002
        for kind,p in list(self.pending.items()):
            if obs.tick<=p['started']:
                continue
            kick=any(e.get('kind')=='kick' and e.get('player')==p['player']
                     and abs(e.get('tick',-100)-p['started'])<=1 for e in events)
            if kind!='ambush' and not p.get('kicked'):
                if kick:
                    p['kicked']=True
                    self.counts[kind+'_native_kicks']+=1;self.note('native_kick',obs,p)
                elif obs.tick>p['started']+2:
                    self.close(kind,'unexecuted',obs);continue
            if wall and not p.get('bounced'):
                p['bounced']=True
                self.counts[kind+'_native_bounces']+=1;self.note('native_wall',obs,p)
            goals=[e for e in events if e.get('kind')=='goal']
            if goals:
                if kind=='rebound-shot' and p.get('kicked') and p.get('bounced') and any(e.get('team')==0
                    and e.get('scorer')==p['player'] and not e.get('own_goal') for e in goals):
                    self.close(kind,'rebound_goals',obs)
                else:self.close(kind,'goal_ended',obs)
                continue
            last=obs.ball.last_touch
            recipient=p.get('recipient',p['player'])
            if kind!='rebound-shot' and p.get('bounced') and last==recipient:
                self.counts[kind+'_postwall_contacts']+=1
                if obs.ball.controlling_player==recipient:
                    self.counts[kind+'_controlled_receptions']+=1
                self.close(kind,'collected',obs);continue
            if last!=p['source_touch']:
                self.close(kind,'opponent_touch' if last is not None and last>=5 else 'other_touch',obs)
                continue
            intervening=[e for e in events if e.get('kind')=='kick' and e.get('tick',-1)>p['started']+1]
            if intervening:
                self.close(kind,'new_kick',obs);continue
            if obs.tick>p['expires']:
                self.close(kind,'uncollected',obs)
        debug=getattr(action,'debug',None) or {}
        intents=debug.get('physics_tactics',()) if error is None and elapsed<20. else ()
        self.previous_launch=None
        for item in intents:
            kind=item['kind'];self.counts[kind+'_command_ticks']+=1
            if item['phase']=='follow':
                continue
            player=next((p for p in obs.my_players if p.id==item['player']),None)
            if kind=='ambush' and player is not None:
                self.previous_moves[player.id]=(obs.tick,*player.position)
            if item['phase']=='launch' and controller is not None and player is not None:
                command=action.players[item['player']]
                velocity=controller._requested_velocity(*obs.ball.velocity,(command.kick_direction,command.kick_power))
                predicted=controller._carrier_contact((player.id,*player.position,*player.velocity),
                    *obs.ball.position,*velocity,command.movement)
                if predicted is not None:self.previous_launch=(player.id,predicted)
            existing=self.pending.get(kind)
            if kind=='ambush' and existing and existing['player']==item['player']:
                continue
            if existing:
                self.close(kind,'superseded',obs)
            plan={**item,'started':obs.tick,'expires':obs.tick+60,
                  'source_touch':obs.ball.last_touch if kind=='ambush' else item['player']}
            self.pending[kind]=plan
            self.counts[kind+'_plans']+=1
            self.note('plan',obs,plan)
        self.previous=(*obs.ball.position,*obs.ball.velocity,obs.ball.last_touch,obs.tick)

    def result(self):
        return {'counts':dict(self.counts),'open_at_end':len(self.pending),'examples':self.examples,
                'scope':'Raw native observations; command ticks are not executions. Wall contacts require the reflected native position and velocity, with no intervening touch. Goals are attributed only to an uninterrupted confirmed rebound shot.'}
