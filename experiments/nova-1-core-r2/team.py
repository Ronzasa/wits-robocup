"""NOVA-1: independent joint team planning; trained parameters embedded below.

Only the explicitly listed collision/movement/flight verification utilities
come from the frozen champion. All roles, candidate generation, opponent
responses, plan evaluation and reception ownership are independently built.
"""
import math
from soccer import TeamController, TeamAction, PlayerAction


def _clip(x,lo,hi):
    return lo if x<lo else hi if x>hi else x


def _unit(x,y):
    d=math.hypot(x,y)
    return (x/d,y/d) if d>1e-8 else (0.,0.)


class NovaController(TeamController):
    name='NOVA-1 independent team planner'
    version='nova-1-development'
    FIRST_TOUCH=True
    JOINT_MODEL=True
    # Geometry and plan features are optimized by native match points.
    CONFIG=(12.0, 7.0, 12.0, 3.0, 2.5, 0.1, 0.65, 1.0)
    WEIGHTS=(4.5, 1.5, 1.6, 0.7, 0.6, -0.5, -0.7, 1.4, -2.0, 0.5, -1.2, 0.4)
    MODEL_STEPS=10
    PLAN_LIMIT=3

    def __init__(self):
        self.reset(0)

    def reset(self,seed):
        self._ready=False
        self._receive=None
        self._previous_score=None
        self._chaser_id=None
        self._cover_id=None
        self._enemy_cooldowns={}
        self._friend_cooldowns={}
        self._receive_aim=None
        self._runtime_path=None
        self._runtime_steps=None
        self._runtime_queries={}
        self._last_pass_motion=None
        self._plans_evaluated=0
        self._response_steps=0
        self._restart_tick=0

    def initial_formation(self,f):
        width=self.CONFIG[0]
        return [(f.my_goal[0]+2.5,0.),(-22.,0.),(-12.,-width),
                (-12.,width),(-f.centre_circle_radius-2.,0.)]

    def _setup(self,f):
        self._dt=1./f.simulation_hz;self._hz=f.simulation_hz
        self._speed=f.max_speed;self._acc=f.acceleration*self._dt
        self._friction=f.ball_friction;self._damping=.9;self._wall=.75
        self._impulse=f.kick_impulse;self._range=f.kick_range
        self._ball_cap=30.;self._ball_radius=f.ball_radius
        self._contact=f.player_radius+f.ball_radius
        self._left=f.my_goal[0];self._right=f.opponent_goal[0]
        self._half_height=f.height*.5;self._mouth=f.goal_width*.5-.6
        self._reach_table=tuple((self._dt*self._damping*(1.-self._damping**n)/(1.-self._damping),
            self._dt*self._acc/(1.-self._damping)*(n-self._damping*(1.-self._damping**n)/(1.-self._damping))) for n in range(83))
        self._ready=True

    def _advance_player(self,p,m):
        vx=p[3]*self._damping+m[0]*self._acc
        vy=p[4]*self._damping+m[1]*self._acc
        speed=math.hypot(vx,vy)
        if speed>self._speed:vx,vy=vx*self._speed/speed,vy*self._speed/speed
        x=_clip(p[1]+vx*self._dt,self._left+1.,self._right-1.)
        y=_clip(p[2]+vy*self._dt,-self._half_height+1.,self._half_height-1.)
        return p[0],x,y,vx,vy

    def _estimate_chase(self,p,path):
        # A movement-target estimate only. Pass acceptance never calls this.
        if not path:return 100.,p[1:3]
        best=(100.,path[-1][1:])
        for i,(t,x,y) in enumerate(path):
            if i%3 and i!=len(path)-1:continue
            dx,dy=x-p[1],y-p[2];d=math.hypot(dx,dy)
            toward=(dx*p[3]+dy*p[4])/max(d,1e-8)
            eta=max(0.,d-self._range)/self._speed+max(0.,1.-toward/self._speed)*.25
            if eta<=t:return t,(x,y)
            if eta+t*.08<best[0]:best=eta+t*.08,(x,y)
        return best

    def _keeper_target(self,keeper,ball,path,ours,theirs):
        bx,by,vx,vy=ball;depth=self.CONFIG[4]
        target=(self._left+depth,_clip(by*depth/max(depth,bx-self._left),-self._mouth,self._mouth))
        if vx< -7.:
            crossing=next((q for q in path if q[1]<=self._left+depth),None)
            if crossing is not None and crossing[0]<1.25:target=(self._left+depth,_clip(crossing[2],-self._mouth,self._mouth))
        if bx<self._left+8. and abs(by)<self._mouth+3.:
            race=self._estimate_chase(keeper,path)
            if race[0]+.18<min(ours,theirs) and not (vx>6. and bx>keeper[1]):target=self._target(*race[1])
        return target

    def _shape(self,friends,opponents,ball,path,chaser,attack,receive=None,future=None):
        bx,by,_,_=ball;width,lead,cover_gap,defend_gap,_,_,_,_=self.CONFIG
        out=friends[1:];est={p[0]:self._estimate_chase(p,path) for p in friends}
        enemy=min((self._estimate_chase(q,path)[0] for q in opponents),default=100.)
        targets={friends[0][0]:self._keeper_target(friends[0],ball,path,min(est[p[0]][0] for p in out),enemy),
                 chaser[0]:self._target(*est[chaser[0]][1])}
        locked={friends[0][0],chaser[0]}
        if receive is not None:
            targets[receive[0]]=self._target(*receive[1]);locked.add(receive[0])
        available=[p for p in out if p[0] not in locked]
        cover_target=self._target(min(25.,bx-cover_gap),by*.28)
        if not attack:
            threats=[q for q in opponents if q[0]!=opponents[0][0] and q[1]<bx+10.]
            threat=min(threats,key=lambda q:q[1]+abs(q[2])*.35,default=None)
            if threat is not None:cover_target=self._target(min(bx-cover_gap,threat[1]-defend_gap),threat[2]*.55)
        if available:
            cover=min(available,key=lambda p:(math.dist(p[1:3],cover_target)-(.8 if p[0]==self._cover_id else 0.),p[0]))
            targets[cover[0]]=cover_target;available.remove(cover)
        else:cover=None
        origin=(bx,by) if future is None else future
        available.sort(key=lambda p:p[2])
        for index,p in enumerate(available):
            sign=-1. if index==0 and len(available)>1 else 1.
            y=_clip(origin[1]*.25+sign*width,-24.,24.)
            x=origin[0]+lead*(1. if attack else .2)+(3. if index else 0.)
            if not attack and index==0:
                threats=[q for q in opponents[1:] if q[1]<bx+14.]
                threat=min(threats,key=lambda q:math.dist(p[1:3],q[1:3])+abs(q[2])*.12,default=None)
                if threat is not None:x,y=threat[1]-defend_gap,threat[2]*.85
            targets[p[0]]=self._target(x,y)
        return targets,cover[0] if cover is not None else None

    def _collect(self,p,path,opponents,after=.05,until=2.2,preferred=None):
        steps=self._pass_steps(path);cooldown=self._friend_cooldowns.get(p[0],0)
        theory=self._verified_intercept(p,path,cooldown,after,until,steps)
        if theory is None:return None
        aims=[preferred] if preferred is not None else []
        aims.append(theory[1])
        for delay in (.15,.35):
            q=next((q for q in path if q[0]>=theory[0]+delay and q[0]<=until),None)
            if q is not None and q[1:] not in aims:aims.append(q[1:])
        route=None
        for aim in aims:
            r=self._receiver_rollout(p,path,aim,cooldown,after,until,steps=steps)
            if r is not None and self._first_touch_safe(r,path,opponents,cooldown):route=r;break
        if route is None:return None
        enemy=math.inf;end=min(until,route[0]+.7)
        for q in opponents:
            r=self._verified_intercept(q,path,self._enemy_cooldowns.get(q[0],0),until=end,steps=steps)
            if r is not None:
                if r[0]<=route[0]+self.CONFIG[5]:return None
                enemy=min(enemy,r[0])
        return route,min(.7,enemy-route[0])

    def _joint_node(self,kind,carrier,kick,move,plan,launch,path,friends,opponents,ball,base_targets,quality=0.,margin=0.,arrival=.7):
        point=plan[2] if plan else path[min(len(path)-1,12)][1:]
        receive=(plan[0],plan[1]) if plan else None
        future=point if plan else None
        targets,cover=self._shape(friends,opponents,ball,path,carrier,True,receive,future)
        targets[carrier[0]]=(ball[0]+.3,ball[1])
        movements={p[0]:self._move(p,targets[p[0]]) for p in friends}
        movements[carrier[0]]=move
        if receive is not None:movements[receive[0]]=self._move(next(p for p in friends if p[0]==receive[0]),receive[1])
        space=min((math.dist(point,q[1:3]) for q in opponents),default=15.)
        progression=(math.hypot(self._right-ball[0],ball[1])-math.hypot(self._right-point[0],point[1]))/20.
        behind=sum(p[1]<min(ball[0],point[0])-3. for p in friends[1:] if p[0]!=carrier[0])
        exposed=max(0.,1.-behind)*max(0.,1.-(point[0]-self._left)/70.)
        # Features represent a whole compatible five-player plan.
        features=[quality,progression,float(kind=='pass'),margin/.7,min(space,14.)/14.,
                  abs(point[1])/30.,arrival/2.,float(kind=='carry'),exposed,
                  sum(4.<math.dist(point,targets[p[0]])<17. for p in friends if p[0] not in (0,carrier[0]))/3.,0.,1.]
        value=sum(w*x for w,x in zip(self.WEIGHTS,features))
        return {'kind':kind,'kick':kick,'move':move,'carrier':carrier[0],'receive':plan,
                'launch':launch,'path':path,'targets':targets,'movements':movements,
                'features':features,'value':value,'cover':cover}

    def _proposals(self,carrier,friends,opponents,ball,targets):
        bx,by,vx,vy=ball;nodes=[]
        move=self._move(carrier,(bx+.3,by))
        # Two legal first commands prevent a carrier's body reversing a kick.
        brake=_unit(-carrier[3],-carrier[4]) if math.hypot(carrier[3],carrier[4])>1. else (0.,0.)
        launch_moves=[move,brake] if brake!=move else [move]
        goals=[]
        if bx> -5.:
            for y in (-5.8,-2.9,0.,2.9,5.8):
                direction=_unit(self._right-bx,y-by)
                along=vx*direction[0]+vy*direction[1]
                cross_sq=max(0.,vx*vx+vy*vy-along*along)
                if cross_sq>=self._impulse*self._impulse:continue
                launch_speed=min(self._ball_cap,along+math.sqrt(self._impulse*self._impulse-cross_sq))
                if launch_speed<5.:continue
                kick=self._kick_to_velocity(vx,vy,direction[0]*launch_speed,direction[1]*launch_speed)
                if kick is None:continue
                for first in launch_moves:
                    launch=self._carrier_contact(carrier,bx,by,*self._requested_velocity(vx,vy,kick),first)
                    if launch is None:continue
                    immediate=launch[0]>=self._right-self._ball_radius and abs(launch[1])<=self._mouth+.6
                    goal=self._goal_path(launch) if not immediate else None
                    if not immediate and (goal is None or goal[1][0]>2.5):continue
                    flight,gy,speed=(self._dt,launch[1],math.hypot(*launch[2:])) if immediate else goal[1]
                    path=[(0.,bx,by),(self._dt,*launch[:2])] if immediate else self._pass_path(launch,(bx,by),min(2.6,flight+.10))
                    if len(path)<2:continue
                    first_enemy=math.inf;steps=self._pass_steps(path)
                    for q in opponents:
                        r=self._verified_intercept(q,path,self._enemy_cooldowns.get(q[0],0),until=flight,steps=steps)
                        if r is not None:first_enemy=min(first_enemy,r[0])
                    quality=1. if immediate else _clip(.7+(first_enemy-flight)*1.8 if first_enemy!=math.inf else .95,.02,.98)
                    quality*=min(1.,speed/18.)
                    node=self._joint_node('shot',carrier,kick,first,None,launch,path,friends,opponents,ball,targets,quality,arrival=flight)
                    goals.append(node)
        nodes.extend(sorted(goals,key=lambda n:-n['value'])[:3])
        options=[]
        for q in friends[1:]:
            distance=math.dist(q[1:3],(bx,by))
            if q[0]==carrier[0] or not 4.<distance<34.:continue
            for advance,speed in ((0.,14.),(self.CONFIG[1]*.6,22.)):
                tx,ty=self._target(q[1]+q[3]*.35+advance,q[2]+q[4]*.35)
                rank=(tx-bx)*.08+min((math.dist((tx,ty),o[1:3]) for o in opponents),default=15.)*.1
                options.append((rank,q,tx,ty,speed))
        options.sort(key=lambda q:(-q[0],q[1][0]))
        for _,q,tx,ty,speed in options[:5]:
            ux,uy=_unit(tx-bx,ty-by)
            kick=self._kick_to_velocity(vx,vy,ux*speed,uy*speed)
            if kick is None:continue
            launch=self._carrier_contact(carrier,bx,by,*self._requested_velocity(vx,vy,kick),move)
            if launch is None:continue
            path=self._pass_path(launch,(bx,by),2.2)
            race=self._collect(q,path,opponents)
            if race is None:continue
            route,margin=race
            plan=(q[0],route[2],route[1])
            nodes.append(self._joint_node('pass',carrier,kick,move,plan,launch,path,friends,opponents,ball,targets,margin=margin,arrival=route[0]))
        for y in (-6.,0.,6.):
            direction=_unit(9.,y)
            kick=self._kick_to_velocity(vx,vy,direction[0]*7.5,direction[1]*7.5)
            if kick is None:continue
            launch=self._carrier_contact(carrier,bx,by,*self._requested_velocity(vx,vy,kick),move)
            if launch is None:continue
            path=self._pass_path(launch,(bx,by),1.)
            if len(path)<2:continue
            nodes.append(self._joint_node('carry',carrier,kick,move,None,launch,path,friends,opponents,ball,targets))
        # Verified first movement/contact for emergency release too.
        if bx< -10. or not nodes:
            direction=_unit(self._right-bx,-by*.3)
            for first in launch_moves:
                kick=(direction,1.)
                launch=self._carrier_contact(carrier,bx,by,*self._requested_velocity(vx,vy,kick),first)
                if launch is not None:
                    path=self._pass_path(launch,(bx,by),1.2)
                    if len(path)>1:nodes.append(self._joint_node('clear',carrier,kick,first,None,launch,path,friends,opponents,ball,targets))
        return nodes

    def _response(self,node,friends,opponents,ball,mode):
        # A bounded response model, not a claim to know future opponent input.
        players=list(friends)+list(opponents);state=[list(p) for p in players]
        x,y,vx,vy=ball;own_ids={p[0] for p in friends};carrier=node['carrier']
        cooldown={**self._friend_cooldowns,**self._enemy_cooldowns}
        enemy_keeper=opponents[0][0] if opponents else -1
        touched=0;turnover=0;goal=0
        for n in range(self.MODEL_STEPS):
            self._response_steps+=1
            oldx,oldy=x,y
            for i,p in enumerate(state):
                pid=p[0]
                if pid in own_ids:
                    target=node['targets'].get(pid,(p[1],p[2]))
                    movement=node['movements'][pid] if n==0 else self._move(p,target)
                else:
                    if pid==enemy_keeper:
                        t=max(0.,(self._right-2.5-x)/max(vx,1.))
                        target=(x,y) if mode and x>self._right-13. else (self._right-2.5,_clip(y+vy*min(t,.8),-self._mouth,self._mouth))
                    elif mode:
                        target=(x+vx*self._dt*2.,y+vy*self._dt*2.)
                    else:
                        target=(x+2.,y*.8) if p[1]<x+7. else (p[1]-1.,p[2]*.9)
                    movement=self._move(p,self._target(*target))
                state[i]=list(self._advance_player(p,movement))
            # Exact equal-radius separation and restitution in the short model.
            for i in range(len(state)):
                a=state[i]
                for j in range(i+1,len(state)):
                    b=state[j];dx,dy=b[1]-a[1],b[2]-a[2];d=math.hypot(dx,dy)
                    if 1e-8<d<2.:
                        nx,ny=dx/d,dy/d;overlap=(2.-d)*.5
                        a[1]-=nx*overlap;a[2]-=ny*overlap;b[1]+=nx*overlap;b[2]+=ny*overlap
                        closing=(b[3]-a[3])*nx+(b[4]-a[4])*ny
                        if closing<0.:
                            impulse=-.675*closing
                            a[3]-=nx*impulse;a[4]-=ny*impulse;b[3]+=nx*impulse;b[4]+=ny*impulse
            if n==0 and node['kick'] is not None:
                kicker=next(p for p in state if p[0]==carrier)
                if math.hypot(kicker[1]-x,kicker[2]-y)<=self._range:
                    vx,vy=self._requested_velocity(vx,vy,node['kick'])
                else:turnover=1
            # Plausible ready opponents clear or shoot on reaching the ball.
            if n>0:
                for p in state:
                    if p[0] in own_ids or cooldown.get(p[0],0)>n:continue
                    if math.hypot(p[1]-x,p[2]-y)<=self._range:
                        ux,uy=_unit(self._left-x,-y);vx+=ux*self._impulse;vy+=uy*self._impulse
                        speed=math.hypot(vx,vy)
                        if speed>self._ball_cap:vx,vy=vx*self._ball_cap/speed,vy*self._ball_cap/speed
                        cooldown[p[0]]=n+5;turnover=1;break
            x+=vx*self._dt;y+=vy*self._dt;vx*=self._friction;vy*=self._friction
            if abs(y)>self._half_height-self._ball_radius:
                sy=1. if y>0 else -1.;y=sy*(self._half_height-self._ball_radius)*2.-y;vy=-sy*abs(vy)*self._wall
            if abs(x)>self._right-self._ball_radius:
                if abs(y)<self._mouth+.6:goal=1 if x>0 else -1;break
                sx=1. if x>0 else -1.;x=sx*(self._right-self._ball_radius)*2.-x;vx=-sx*abs(vx)*self._wall
            for p in state:
                dx,dy=x-p[1],y-p[2];d=math.hypot(dx,dy)
                if 1e-8<d<self._contact:
                    nx,ny=dx/d,dy/d;x=p[1]+nx*self._contact;y=p[2]+ny*self._contact
                    closing=(vx-p[3])*nx+(vy-p[4])*ny
                    if closing<0.:vx-=1.25*closing*nx;vy-=1.25*closing*ny
                    if p[0] in own_ids:touched=1
                    else:turnover=1
        room=min((math.hypot(x-p[1],y-p[2]) for p in state if p[0] not in own_ids),default=15.)
        return goal*8.+(x-ball[0])*.035+room*.025+touched*.25-turnover*1.4,turnover

    def _select(self,carrier,friends,opponents,ball,targets,score,time_remaining):
        nodes=self._proposals(carrier,friends,opponents,ball,targets)
        if not nodes:return None
        lead=score[0]-score[1]
        risk=1.+self.CONFIG[7]*max(-1.,min(1.,lead))*(1.-time_remaining)
        for n in nodes:n['value']-=n['features'][8]*max(0.,risk-1.)
        nodes.sort(key=lambda n:(-n['value'],n['kind'],n['kick']))
        if self.JOINT_MODEL:
            for node in nodes[:self.PLAN_LIMIT]:
                responses=[self._response(node,friends,opponents,ball,m) for m in (0,1)]
                node['value']+=self.CONFIG[6]*(min(v for v,t in responses)*.7+sum(v for v,t in responses)*.15)
                node['features'][10]=sum(t for v,t in responses)*.5
                node['value']+=self.WEIGHTS[10]*node['features'][10]
                self._plans_evaluated+=1
            # Only plans with an evaluated response compete with one another.
            return max(nodes[:self.PLAN_LIMIT],key=lambda n:n['value'])
        return nodes[0]

    def act(self,obs):
        if not self._ready:self._setup(obs.field)
        self._plans_evaluated=0;self._response_steps=0
        friends=[(p.id,*p.position,*p.velocity) for p in obs.my_players]
        opponents=[(p.id,*p.position,*p.velocity) for p in obs.opponents]
        action=TeamAction()
        if not friends:return action
        self._friend_cooldowns={p.id:p.kick_cooldown_ticks for p in obs.my_players}
        self._enemy_cooldowns={p.id:p.kick_cooldown_ticks for p in obs.opponents}
        if self._previous_score!=obs.score:self._receive=None;self._restart_tick=obs.tick
        self._previous_score=obs.score
        ball=(*obs.ball.position,*obs.ball.velocity)
        # A conservative pass forecast stops at the goal aperture before the
        # engine necessarily declares a goal. The live observed ball remains
        # a valid chase target on that intervening tick.
        path=self._pass_path(ball,until=2.5) or [(0.,ball[0],ball[1])]
        out=friends[1:] or friends
        chaser=min(out,key=lambda p:(self._estimate_chase(p,path)[0]-(.07 if p[0]==self._chaser_id else 0.),p[0]))
        enemy=min((self._estimate_chase(q,path)[0] for q in opponents),default=100.)
        attack=self._estimate_chase(chaser,path)[0]<=enemy+.05
        receive=None
        if self._receive is not None:
            pid,passer,aim,expiry=self._receive
            receiver=next((p for p in out if p[0]==pid),None)
            if receiver is not None and obs.tick<=expiry and obs.ball.last_touch in (None,passer):
                race=self._collect(receiver,path,opponents,after=0.,until=2.5,preferred=aim)
                if race is not None:receive=(pid,race[0][2]);chaser=receiver
            if receive is None:self._receive=None
        targets,cover=self._shape(friends,opponents,ball,path,chaser,attack,receive)
        protected=(obs.tick-self._restart_tick<3*self._hz and math.hypot(*ball[:2])<.7
                   and math.hypot(*ball[2:])<.2 and obs.ball.controlling_team==1)
        if protected:
            radius=obs.field.centre_circle_radius+3.
            for p in friends[1:]:
                y=_clip(p[2],-radius+1.,radius-1.)
                targets[p[0]]=self._target(-math.sqrt(max(0.,radius*radius-y*y)),y)
        self._chaser_id=chaser[0];self._cover_id=cover
        kickers=[p for p in friends if obs.can_kick(p[0])]
        carrier=min(kickers,key=lambda p:math.dist(p[1:3],ball[:2]),default=None)
        plan=None
        if carrier is not None and not protected:
            plan=self._select(carrier,friends,opponents,ball,targets,obs.score,getattr(obs,'time_remaining',1.))
            self._receive=None
            if plan is not None:
                targets=plan['targets'];self._cover_id=plan['cover']
                if plan['receive'] is not None:
                    pid,aim,point=plan['receive'];self._receive=(pid,carrier[0],aim,obs.tick+int(2.5*self._hz))
        for p in friends:
            movement=self._move(p,targets.get(p[0],p[1:3]))
            if plan is not None:movement=plan['movements'][p[0]]
            if plan is not None and p[0]==carrier[0]:
                action.set(p[0],PlayerAction(movement=movement,kick_direction=plan['kick'][0],kick_power=plan['kick'][1]))
            else:action.set(p[0],PlayerAction(movement=movement))
        return action

    def _target(self, x, y):
        return (_clip(x, self._left + 2.0, self._right - 2.0),
                _clip(y, -self._half_height + 2.0, self._half_height - 2.0))


    def _move(self, p, target, friends=()):
        dx, dy = target[0] - p[1], target[1] - p[2]
        gap = math.hypot(dx, dy)
        # Reuse exactly the norm that _unit would calculate again.
        if gap < 1e-8:
            ux, uy = 0.0, 0.0
        else:
            ux, uy = dx / gap, dy / gap
        for other in friends:
            if other[0] == p[0]:
                continue
            sx, sy = p[1] - other[1], p[2] - other[2]
            d = math.hypot(sx, sy)
            if 0.01 < d < 3.0:
                force = (3.0 - d) * 0.22 / d
                ux += sx * force
                uy += sy * force
        ux, uy = _unit(ux, uy)
        desired = min(self._speed, gap * 5.0)
        ax = (ux * desired - p[3] * self._damping) / self._acc
        ay = (uy * desired - p[4] * self._damping) / self._acc
        length = math.hypot(ax, ay)
        if length > 1.0:
            return ax / length, ay / length
        return ax, ay


    def _pass_path(self, launch, origin=None, until=4.0):
        """Every native ball step, including both legs of a wall pass.

        A carrier launch has already consumed one tick. Keep the pre-kick
        ball too: players move and can kick before that tick's ball step.
        General movement deliberately retains the sparse _trajectory.
        """
        x, y, vx, vy = launch
        samples = [] if origin is None else [(0.0, *origin)]
        motion = ([] if origin is None else [(vx,vy)]) if self.FIRST_TOUCH else None
        first = 0 if origin is None else 1
        xwall = self._right - self._ball_radius
        ywall = self._half_height - self._ball_radius
        for n in range(first, min(80,int(round(until*self._hz)))+1):
            if n > first:
                x += vx * self._dt
                y += vy * self._dt
            if abs(y) > ywall:
                side = 1.0 if y > 0.0 else -1.0
                y = side * ywall * 2.0 - y
                vy = -side * abs(vy) * self._wall
            if abs(x) > xwall:
                if abs(y) <= self._mouth + 0.6:
                    break
                side = 1.0 if x > 0.0 else -1.0
                x = side * xwall * 2.0 - x
                vx = -side * abs(vx) * self._wall
            samples.append((n * self._dt, x, y))
            if n > first:
                vx *= self._friction
                vy *= self._friction
            if motion is not None:
                motion.append((vx,vy))
        self._last_pass_motion = (samples,motion) if motion is not None else None
        return samples


    def _pass_reachable(self, p, x, y, n, radius):
        """A legal collision-free movement witness, never an ETA fallback.

        The reach disk and speed bound only reject impossible targets. A
        positive result additionally needs either a legal constant input or
        an explicitly stepped, speed-capped _move pursuit of the target.
        Other players' future collisions remain unknowable from a forecast.
        """
        dx, dy = x - p[1], y - p[2]
        distance_sq = dx*dx+dy*dy
        if n == 0:
            return distance_sq <= radius*radius
        if n >= len(self._reach_table) or distance_sq > (self._speed*n*self._dt+radius)**2:
            return False
        coast, reach = self._reach_table[n]
        rx, ry = dx - p[3]*coast, dy - p[4]*coast
        gap_sq = rx*rx+ry*ry
        if gap_sq > (reach+radius)**2:
            return False
        gap = math.sqrt(gap_sq)
        # This constant acceleration reaches the contact disk exactly.
        # Its velocities are convex combinations of the initial and final
        # velocity, so a legal final speed proves all intermediate speeds.
        scale = max(0.0, gap-radius+1e-7) / max(gap*reach, 1e-12)
        ax, ay = rx*scale, ry*scale
        decay = self._damping**n
        impulse = self._acc*(1.0-decay)/(1.0-self._damping)
        fx, fy = p[3]*decay+ax*impulse, p[4]*decay+ay*impulse
        # A generous enclosure proves the witness never touches a wall.
        inside = (abs(p[1])+abs(p[3])*coast+abs(ax)*reach < self._right-1.0
                  and abs(p[2])+abs(p[4])*coast+abs(ay)*reach < self._half_height-1.0)
        if (inside and p[3]*p[3]+p[4]*p[4]<=self._speed*self._speed
                and math.hypot(ax, ay)<=1.0 and math.hypot(fx, fy)<=self._speed):
            return True
        # Saturation can make the disk bound optimistic. Verify the actual
        # acceleration and speed cap rather than accepting that bound.
        px, py, vx, vy = p[1:]
        tx, ty = self._target(x, y)
        for _ in range(n):
            ux, uy = tx-px, ty-py
            gap = math.hypot(ux, uy)
            desired = min(self._speed, gap*5.0)
            factor = desired/gap if gap > 1e-8 else 0.0
            ax = (ux*factor-vx*self._damping)/self._acc
            ay = (uy*factor-vy*self._damping)/self._acc
            norm = math.hypot(ax, ay)
            if norm > 1.0:
                ax, ay = ax/norm, ay/norm
            vx, vy = vx*self._damping+ax*self._acc, vy*self._damping+ay*self._acc
            speed = math.hypot(vx, vy)
            if speed > self._speed:
                vx, vy = vx*self._speed/speed, vy*self._speed/speed
            px, py = px+vx*self._dt, py+vy*self._dt
            if abs(px) > self._right-1.0 or abs(py) > self._half_height-1.0:
                return False
        return math.hypot(x-px, y-py) <= radius


    def _pass_steps(self, path):
        # Share tick conversion across all six players evaluating a pass.
        # Internal pass paths are immutable. Retain one object, not an id,
        # so an allocator reuse can never return a different flight's data.
        if path is self._runtime_path:
            return self._runtime_steps
        steps=[]
        previous=None
        for t,x,y in path:
            n=int(round(t*self._hz))
            pre=previous if previous is not None and abs(t-previous[0]-self._dt)<1e-8 else None
            steps.append((t,n,x,y,pre))
            previous=t,x,y
        self._runtime_path=path
        self._runtime_steps=steps
        self._runtime_queries={}
        return steps


    def _verified_intercept(self, p, path, cooldown=0, after=0.0, until=4.0, steps=None):
        """Earliest witnessed contact, or None; requires a dense pass path.

        At tick n a ready player can kick the PRE-step ball after moving;
        its body can obstruct the POST-step ball even while on cooldown.
        """
        if steps is None:
            steps=self._pass_steps(path)
        body_radius=self._contact
        kick_radius=self._range
        for t,n,x,y,pre in steps:
            if t>until+1e-9:
                break
            if t+1e-9<after:
                continue
            # Cheap necessary bounds avoid a movement-witness call for most
            # distant players. These never turn an estimate into acceptance.
            coast,reach=self._reach_table[n]
            ex,ey=p[1]+p[3]*coast,p[2]+p[4]*coast
            if pre is not None and cooldown<=n:
                dx,dy=pre[1]-ex,pre[2]-ey
                if dx*dx+dy*dy<=(reach+kick_radius)**2 and self._pass_reachable(p,pre[1],pre[2],n,kick_radius):
                    return t,(pre[1],pre[2])
            # At observation time no new kick has occurred. A future kick
            # needs the next movement step, checked against pre above.
            radius=body_radius
            dx,dy=x-ex,y-ey
            if dx*dx+dy*dy<=(reach+radius)**2 and self._pass_reachable(p,x,y,n,radius):
                return t,(x,y)
        return None


    def _receiver_rollout(self, p, path, aim, cooldown=0, after=0.0, until=4.0, first_move=None, steps=None):
        """First touch under the commands used by a named receiver.

        A kick needs act()'s BEFORE-movement can_kick gate and its conservative
        post-movement range gate. Moving into native kick range alone is not
        enough. Before that, follow the same clipped aim with _move().
        """
        if not path or abs(path[0][0])>1e-8:
            return None
        aim=self._target(*aim)
        px,py,vx,vy=p[1:]
        dt,hz=self._dt,self._hz
        damping,acc,speed_cap=self._damping,self._acc,self._speed
        kick_range,contact=self._range,self._contact
        xbound,ybound=self._right-1.0,self._half_height-1.0
        hypot=math.hypot
        previous=path[0]
        if after<=0.0 and hypot(px-previous[1],py-previous[2])<=contact:
            return 0.0,(previous[1],previous[2]),aim,p,'body',0,0
        for index in range(1,len(path)):
            t,x,y=path[index]
            n=steps[index][1] if steps is not None else int(round(t*hz))
            if t>until+1e-9:
                break
            if abs(t-previous[0]-dt)>1e-8:
                return None
            prex,prey=previous[1:]
            ready=(cooldown<=n-1 and hypot(px-prex,py-prey)<=kick_range
                   and not (after>0.0 and n==1))
            if index==1 and first_move is not None:
                ready=False
                ax,ay=first_move
            else:
                tx,ty=(prex+0.3,prey) if ready else aim
                dx,dy=tx-px,ty-py
                gap=hypot(dx,dy)
                if gap<1e-8:
                    ux,uy=0.0,0.0
                else:
                    ux,uy=dx/gap,dy/gap
                length=hypot(ux,uy)
                if length<1e-8:
                    ux,uy=0.0,0.0
                else:
                    ux,uy=ux/length,uy/length
                desired=min(speed_cap,gap*5.0)
                ax=(ux*desired-vx*damping)/acc
                ay=(uy*desired-vy*damping)/acc
                length=hypot(ax,ay)
                if length>1.0:
                    ax,ay=ax/length,ay/length
            vx=vx*damping+ax*acc
            vy=vy*damping+ay*acc
            speed=hypot(vx,vy)
            if speed>speed_cap:
                vx,vy=vx*speed_cap/speed,vy*speed_cap/speed
            px,py=px+vx*dt,py+vy*dt
            if abs(px)>xbound or abs(py)>ybound:
                return None
            kick=ready and hypot(px-prex,py-prey)<kick_range-0.18
            body=hypot(px-x,py-y)<=contact
            if kick or body:
                if t+1e-9<after:
                    return None
                point=(prex,prey) if kick else (x,y)
                return t,point,aim,(p[0],px,py,vx,vy),'kick' if kick else 'body',index,n
            previous=t,x,y
        return None


    def _first_touch_safe(self, route, path, opponents, cooldown):
        """Keep a body reception only if control or a safe next kick is real."""
        if route[4]=='kick':
            return True
        motion=self._last_pass_motion
        if motion is None or motion[0] is not path:
            return False
        t,(x,y),aim,p,kind,index,n=route
        vx,vy=motion[1][index]
        dx,dy=x-p[1],y-p[2]
        gap=math.hypot(dx,dy)
        if gap<1e-8:
            return False
        nx,ny=dx/gap,dy/gap
        # Same ground contact position and restitution as _carrier_contact
        # and _touch_path; only the receiver's first contact is evaluated.
        x,y=p[1]+nx*self._contact,p[2]+ny*self._contact
        closing=(vx-p[3])*nx+(vy-p[4])*ny
        if closing<0.0:
            vx-=1.25*closing*nx
            vy-=1.25*closing*ny
        if math.hypot(vx-p[3],vy-p[4])<=8.0:
            return True
        if cooldown>n:
            return False
        move=self._move(p,(x+0.3,y))
        pvx=p[3]*self._damping+move[0]*self._acc
        pvy=p[4]*self._damping+move[1]*self._acc
        speed=math.hypot(pvx,pvy)
        if speed>self._speed:
            pvx,pvy=pvx*self._speed/speed,pvy*self._speed/speed
        if math.hypot(p[1]+pvx*self._dt-x,p[2]+pvy*self._dt-y)>=self._range-0.18:
            return False
        # A deflected first touch can bring the ball closer to a defender
        # than the uncollected flight. Do not approve a tied recovery.
        for q in opponents:
            radius=self._range if self._enemy_cooldowns.get(q[0],0)<=n+1 else self._contact
            if self._pass_reachable(q,x,y,n+1,radius):
                return False
        return True


    def _kick_to_velocity(self, vx, vy, tx, ty):
        dx, dy = tx - vx, ty - vy
        length = math.hypot(dx, dy)
        if length < 0.03:
            return None
        power = min(1.0, length / self._impulse)
        return (dx / length, dy / length), power


    def _requested_velocity(self, vx, vy, kick):
        direction, power = kick
        sx = vx + direction[0] * power * self._impulse
        sy = vy + direction[1] * power * self._impulse
        speed = math.hypot(sx, sy)
        if speed > self._ball_cap:
            sx *= self._ball_cap / speed
            sy *= self._ball_cap / speed
        return sx, sy


    def _carrier_contact(self, p, bx, by, sx, sy, movement):
        # One free movement step, then just the carrier's first ball contact.
        pvx = p[3] * self._damping + movement[0] * self._acc
        pvy = p[4] * self._damping + movement[1] * self._acc
        speed = math.hypot(pvx, pvy)
        if speed > self._speed:
            pvx *= self._speed / speed
            pvy *= self._speed / speed
        px, py = p[1] + pvx * self._dt, p[2] + pvy * self._dt
        if math.hypot(px - bx, py - by) >= self._range - 0.18:
            return None
        x, y = bx + sx * self._dt, by + sy * self._dt
        sx *= self._friction
        sy *= self._friction
        rx, ry = x - px, y - py
        gap = math.hypot(rx, ry)
        if 1e-8 < gap < self._contact:
            nx, ny = rx / gap, ry / gap
            x, y = px + nx * self._contact, py + ny * self._contact
            closing = (sx - pvx) * nx + (sy - pvy) * ny
            if closing < 0.0:
                # Documented ground player/ball restitution is 0.25.
                impulse = -1.25 * closing
                sx += impulse * nx
                sy += impulse * ny
        return x, y, sx, sy


    def _goal_path(self,launch):
        x,y,vx,vy=launch
        path=[(self._dt,x,y)]
        wall=self._half_height-self._ball_radius
        goal=self._right-self._ball_radius
        for tick in range(2,61):
            oldx,oldy=x,y
            x+=vx*self._dt;y+=vy*self._dt
            if abs(y)>wall:
                side=1.0 if y>0.0 else -1.0
                y=side*wall*2.0-y;vy=-side*abs(vy)*self._wall
            if x>=goal and vx>0.0:
                fraction=(goal-oldx)/max(1e-9,x-oldx)
                gy=oldy+(y-oldy)*fraction
                if abs(gy)>self._mouth+.15:
                    return None
                time=(tick-1+fraction)*self._dt
                path.append((time,goal,gy))
                return path,(time,gy,math.hypot(vx,vy))
            if x<=self._left+self._ball_radius:
                return None
            vx*=self._friction;vy*=self._friction
            if tick%2==0:
                path.append((tick*self._dt,x,y))
        return None

