"""Build the transition-attack research candidate from the archived Monster.

Offline tooling only; the generated team file has no filesystem dependencies.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def pressure_cover():
    """Give the fifth player a defensive job during a sustained two-man siege."""
    candidate = (ROOT / "experiments/league/gaps2/team.py").read_text(encoding="utf-8")
    candidate = candidate.replace('name = "MONSTER CORNER"', 'name = "MONSTER PRESSURE COVER"')
    candidate = candidate.replace("version = 'league-corner-duel-1'", "version = 'league-pressure-cover-1'")
    candidate = candidate.replace('        self.outlet_side = None\n',
                                  '        self.outlet_side = None\n'
                                  '        self.pressure_ticks = 0\n'
                                  '        self.pressure_until = -1\n')
    old = '''        outlet = friends[4]
        if bx<self.left+20 and not obs.can_kick(4):
'''
    new = '''        outlet = friends[4]
        # Four defenders still cover their usual goal-mouth slots. During a
        # sustained close siege, the outlet adds pressure instead of waiting
        # 25 metres away for a clearance that the attackers can recycle.
        close_attackers = sum(q[1] < self.left+18 and abs(q[2]) < self.goal+8
                              for q in opponents)
        danger = close_attackers >= 2 and bx < self.left+22 and not protected
        self.pressure_ticks = min(int(2*self.hz), self.pressure_ticks+1) if danger else max(0,self.pressure_ticks-2)
        if self.pressure_ticks >= int(0.6*self.hz):
            self.pressure_until = obs.tick+int(1.5*self.hz)
        pressing = obs.tick < self.pressure_until and bx < self.left+28 and not protected
        if pressing:
            # The normal predictive race accounts for the ball's momentum
            # and cooldown; running at the current ball loses cutbacks.
            path = self.stream_path(*ball)
            target = self.bound(*self.race(outlet,path)[1])
        elif bx<self.left+20 and not obs.can_kick(4):
'''
    if candidate.count(old) != 1:
        raise RuntimeError("Pressure-cover shell anchor changed")
    candidate = candidate.replace(old,new)
    target = ROOT / "experiments/league/pressure_cover/team.py"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(candidate,encoding="utf-8")
    print(target)


def guardian():
    """Isolate the close-goal guard launch search from other tactical changes."""
    candidate = (ROOT / "experiments/league/pressure_cover/team.py").read_text(encoding="utf-8")
    candidate = candidate.replace('name = "MONSTER PRESSURE COVER"', 'name = "MONSTER GUARDIAN"')
    candidate = candidate.replace("version = 'league-pressure-cover-1'", "version = 'league-guardian-clear-1'")
    candidate = candidate.replace('        self.deadline = perf_counter()+0.007\n',
                                  '        self.deadline = perf_counter()+0.007\n'
                                  '        self.guard_clear_until = None\n')
    method = '''    def emergency_clear(self, p, ball, friends, opponents, movement, default):
        """Compare short emergency launches, including this kicker's contact.

        This is a one-player contact model followed by free-ball trajectories.
        Other visible bodies contribute a proximity penalty; their subsequent
        kicks and contacts are not simulated, so competitive testing is needed.
        All guards share one 1.5 ms allowance within the existing act deadline.
        """
        now = perf_counter()
        if self.guard_clear_until is None:
            self.guard_clear_until = min(self.deadline, now+0.0015)
        until = self.guard_clear_until
        if now >= until:
            return None
        bx, by, vx, vy = ball
        nearby = [q for q in friends+opponents
                  if q[0] != p[0] and abs(q[1]-bx) < 10 and abs(q[2]-by) < 10]

        def route_value(state):
            x, y, sx, sy = state
            previous_x = x
            delta_x = sx*self.dt
            body_risk = 0.0
            n = 0
            for n, x, y in self.stream_path(*state, steps=12):
                if n:
                    delta_x = x-previous_x
                previous_x = x
                if x < self.left and abs(y) < self.goal+self.br*0.15:
                    return -1000.0+n*3.0
                if n < 5:
                    coast = self.reach[n][0]
                    for q in nearby:
                        gap = math.hypot(x-q[1]-q[3]*coast, y-q[2]-q[4]*coast)
                        body_risk = max(body_risk, max(0.0,self.body+0.12-gap))
            value = (x-bx)*1.2 + sx*0.08 - body_risk*10.0
            # A trajectory that has not crossed the line yet can still be
            # rolling straight into it after the short forecast expires.
            if delta_x < -0.015 and abs(y) < self.goal+self.br:
                value -= 15.0 + max(0.0,6.0-(x-self.left))*3.0
            if abs(y) > self.goal+self.br:
                value += 1.2
            return value

        launched = self.launch(p,ball,default,movement)
        best = (route_value(launched[0]),movement,default) if launched is not None else None
        # A moving guard can otherwise kick through its own body and send a
        # nominally forward clearance back toward goal. Forward and lateral
        # escape movement are considered alongside its ordinary cover action.
        peel = 1 if p[2] >= by else -1
        moves = (movement,
                 self.move(p,self.bound(p[1]+3.0,p[2])),
                 self.move(p,self.bound(p[1]+1.0,p[2]+peel*2.8)))
        angles = (math.atan2(default[0][1],default[0][0]),0.0,
                  -0.4,0.4,-0.8,0.8,-1.2,1.2)
        for candidate_move in moves:
            for angle in angles:
                if perf_counter() >= until:
                    return (best[1],best[2]) if best is not None else None
                kick = ((math.cos(angle),math.sin(angle)),1.0)
                launched = self.launch(p,ball,kick,candidate_move)
                if launched is None:
                    continue
                value = route_value(launched[0])
                if best is None or value > best[0]+0.03:
                    best = value,candidate_move,kick
        return (best[1],best[2]) if best is not None else None

'''
    marker = '    def shell_act(self, obs, protected):'
    if candidate.count(marker) != 1:
        raise RuntimeError("Guardian shell anchor changed")
    candidate = candidate.replace(marker,method+marker)
    old = '''                if self.SMART_CLEAR:
                    kick = self.clearance(p,ball,outlet,opponents,movement,kick)
            if protected and i==4'''
    new = '''                if self.SMART_CLEAR:
                    kick = self.clearance(p,ball,outlet,opponents,movement,kick)
                if bx < self.left+10:
                    emergency = self.emergency_clear(p,ball,friends,opponents,movement,kick)
                    if emergency is not None:
                        movement,kick = emergency
            if protected and i==4'''
    if candidate.count(old) != 1:
        raise RuntimeError("Guardian clearance anchor changed")
    candidate = candidate.replace(old,new)
    target = ROOT / "experiments/league/guardian/team.py"
    compile(candidate,str(target),"exec")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(candidate,encoding="utf-8")
    print(target)


def open_gap():
    """Build an auxiliary open-play adversary from our validated Titan only."""
    titan = (ROOT / "my-team/team.py").read_text(encoding="utf-8")
    candidate = titan[:titan.index('# Plays against a goal-line wall.')]
    candidate = candidate[candidate.index('import math'):]
    candidate = ('"""Auxiliary open-play gap attacker, derived from our validated Titan.\n'
                 'Uses public observations only; never imports another submission.\n"""\n' + candidate)
    addition = '''
class _OpenGapPolicy(_FallbackPolicy):
    LOCK_LEAD = 0
    WALL_BREAK = 0
    SEARCH_BUDGET_SECONDS = 0.007

    def _open_targets(self, bx, by, opponents):
        """Project observed blocker bodies and try the spaces between them."""
        low, high = -self._goal_half+0.08, self._goal_half-0.08
        intervals = []
        distance = self._right+0.1-bx
        for q in opponents:
            if q[1] < bx+0.3:
                continue
            flight = min(0.5,max(0.0,(q[1]-bx)/22.0))
            coast = self._dt*self._damping*(1-self._damping**(flight*self._hz))/(1-self._damping)
            qx,qy = q[1]+q[3]*coast,q[2]+q[4]*coast
            scale = distance/max(0.4,qx-bx)
            centre = by+(qy-by)*scale
            radius = (self._contact+0.025)*scale
            a,b = max(low,centre-radius),min(high,centre+radius)
            if a < b:
                intervals.append((a,b))
        cursor,gaps = low,[]
        for a,b in sorted(intervals):
            if a > cursor+0.05:
                gaps.append((a-cursor,(a+cursor)*0.5))
            cursor = max(cursor,b)
        if high > cursor+0.05:
            gaps.append((high-cursor,(high+cursor)*0.5))
        targets = [centre for width,centre in sorted(gaps,reverse=True)[:5]]
        for y in (0.0,-3.6,3.6,-6.7,6.7):
            if all(abs(y-old)>0.1 for old in targets):
                targets.append(y)
        return targets

    def _open_shot(self,p,bx,by,vx,vy,opponents,target_y):
        if self._search_expired() or bx < self._right-22.0:
            return None
        velocity = self._shot_velocity(bx,by,vx,vy,target_y)
        if velocity is None:
            return None
        kick = self._kick_to_velocity(vx,vy,*velocity[:2])
        if kick is None:
            return None
        movement = self._move(p,(bx+0.3,by))
        launch = self._carrier_contact(p,bx,by,*self._requested_velocity(vx,vy,kick),movement)
        forecast = self._goal_path(launch) if launch is not None else None
        if forecast is None:
            return None
        path,(flight,gy,end_speed) = forecast
        if flight > 1.6 or end_speed < 8.0:
            return None
        body,ready = 20.0,2.0
        for t,x,y in path:
            n = min(82,max(1,int(round(t*self._hz))))
            coast = self._reach_table[n][0]
            for q in opponents:
                qx,qy = q[1]+q[3]*coast,q[2]+q[4]*coast
                gap = math.hypot(x-qx,y-qy)
                body = min(body,gap-self._contact)
                if body < -0.035:
                    return None
                if self._enemy_cooldowns.get(q[0],0) < n:
                    ready = min(ready,gap-self._range)
        # Body gaps can remain shootable during a defender's cooldown. Ready
        # defenders receive a substantial penalty rather than an assumption
        # that a stationary wall can sprint toward every possible shot.
        if ready < -0.65:
            return None
        score = 7.0+min(body,0.7)*2.5+min(ready,0.5)*2.5-flight*0.7
        return score,kick,movement,None

    def _shot_option(self,p,bx,by,vx,vy,opponents,target_y,bank=False):
        if not bank and sum(q[1]>self._right-5 and abs(q[2])<self._goal_half+2 for q in opponents)>=3:
            return self._open_shot(p,bx,by,vx,vy,opponents,target_y)
        return super()._shot_option(p,bx,by,vx,vy,opponents,target_y,bank)

    def _open_search(self,p,bx,by,vx,vy,opponents):
        if bx < self._right-22:
            return None
        best = None
        for y in self._open_targets(bx,by,opponents):
            if self._search_expired():
                break
            option = self._open_shot(p,bx,by,vx,vy,opponents,y)
            if option is not None and (best is None or option[0]>best[0]):
                best = option
        return best

    def _choose_kick(self,p,bx,by,vx,vy,friends,opponents):
        option = self._open_search(p,bx,by,vx,vy,opponents) if p[0]!=0 else None
        if option is not None:
            self._touch_movement = option[2]
            self._pass_plan = self._bank_plan = None
            self._relay_proposal = self._relay_fallback = None
            return option[1]
        return super()._choose_kick(p,bx,by,vx,vy,friends,opponents)

    def _scout_support(self,obs,friends,opponents,chaser,races,enemy_eta,targets,protected):
        bx,by = obs.ball.position
        wall = sum(q[1]>self._right-6 and abs(q[2])<self._goal_half+2 for q in opponents)>=3
        if protected or bx < self._right-25 or not wall:
            return super()._scout_support(obs,friends,opponents,chaser,races,enemy_eta,targets,protected)
        recipient = self._receive_plan[0] if self._receive_plan is not None else None
        helpers = [p for p in friends[1:] if p[0] not in (chaser[0],self._shape_cover_id,recipient)]
        helpers.sort(key=lambda p:p[2])
        for index,p in enumerate(helpers):
            side = -1 if index==0 else 1
            targets[p[0]] = self._target(bx-0.8,by+side*1.95)

    def act(self,obs):
        actions = self._act_normal(obs)
        bx,by = obs.ball.position
        if bx < self._right-12:
            return actions
        opponents = [(p.id,*p.position,*p.velocity) for p in obs.opponents]
        if sum(q[1]>self._right-6 and abs(q[2])<self._goal_half+2 for q in opponents)<3:
            return actions
        # A second nearby ready attacker can continue a close shooting duel
        # while the first is on cooldown. This remains normal open play.
        for view in obs.my_players[1:]:
            old = actions.players[view.id]
            if old.kick_direction is not None or not obs.can_kick(view.id):
                continue
            p = (view.id,*view.position,*view.velocity)
            option = self._open_search(p,bx,by,*obs.ball.velocity,opponents)
            if option is not None:
                actions.set(view.id,PlayerAction(movement=option[2],kick_direction=option[1][0],kick_power=option[1][1]))
        return actions


class OpenGap(TeamController):
    name = "Open Gap Adversary"
    version = "open-fallback-gap-1"

    def __init__(self):
        self.policy = _OpenGapPolicy()

    def initial_formation(self,field):
        return self.policy.initial_formation(field)

    def reset(self,seed):
        self.policy.reset(seed)

    def act(self,obs):
        self.policy._decision_deadline = perf_counter()+self.policy.SEARCH_BUDGET_SECONDS
        return self.policy.act(obs)
'''
    if len(addition.splitlines()) > 200:
        raise RuntimeError("Keep the auxiliary attack addition bounded")
    candidate += addition
    target = ROOT / "experiments/league/opponents/open_gap/team.py"
    compile(candidate,str(target),"exec")
    if len(candidate.encode("utf-8")) >= 256*1024:
        raise RuntimeError("Auxiliary opponent exceeds single-file size allowance")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(candidate,encoding="utf-8")
    print(target)
    print("Added lines:",len(addition.splitlines()),"Source bytes:",len(candidate.encode("utf-8")))


def siege():
    """A separate late, level-score siege experiment; locked sources stay intact."""
    candidate = (ROOT / "experiments/league/ray_cover2/team.py").read_text(encoding="utf-8")
    candidate = candidate.replace('name = "MONSTER RAY COVER2"', 'name = "MONSTER LATE SIEGE"')
    candidate = candidate.replace("version = 'league-ray-cover-2'", "version = 'league-late-siege-1'")
    candidate = candidate.replace('    SUPPORT = False\n','    SUPPORT = True\n')
    candidate = candidate.replace('        self.outlet_side = None\n',
                                  '        self.outlet_side = None\n'
                                  '        self.siege_active = False\n'
                                  '        self.siege_recover = False\n'
                                  '        self.siege_ticks = 0\n'
                                  '        self.siege_frontier = None\n'
                                  '        self.siege_progress = 0\n'
                                  '        self.siege_receive = None\n')
    candidate = candidate.replace('    def passing(self, p, ball, friends, opponents):',
                                  '    def ordinary_passing(self, p, ball, friends, opponents):')
    methods = '''    def siege_mode(self,obs,ball,wall,protected):
        bx,by,vx,vy = ball
        clearing_home = vx < -8 and bx+vx*self.roll[min(150,int(1.2*self.hz))] < 5
        eligible = (not protected and wall and obs.score[0]==obs.score[1]
                    and obs.time_remaining<=0.35 and not clearing_home
                    and (bx>self.right-35 or self.siege_active and bx>10))
        if not eligible:
            if self.siege_active:
                self.siege_recover = True
            guard = obs.my_players[3]
            if self.siege_recover and guard.position[0]<self.left+6 and abs(guard.position[1]+5.4)<4:
                self.siege_recover = False
            self.siege_active = False
            self.siege_ticks = 0
            self.siege_frontier = None
            self.siege_receive = None
            return False
        self.siege_ticks += 1
        if self.siege_frontier is None or bx>self.siege_frontier+1.0:
            self.siege_frontier = bx
            self.siege_progress = obs.tick
        if self.siege_ticks>=int(4*self.hz) and obs.tick-self.siege_progress>=int(4*self.hz):
            self.siege_active = True
            self.siege_recover = False
        if self.siege_receive is not None:
            rid,expiry,pid = self.siege_receive
            if obs.tick>expiry or obs.ball.last_touch not in (None,pid,rid):
                self.siege_receive = None
        return self.siege_active

    def passing(self,p,ball,friends,opponents):
        if not self.siege_active:
            return self.ordinary_passing(p,ball,friends,opponents)
        bx,by,vx,vy = ball
        receiver = friends[3 if p[0]==4 else 4]
        distance = math.hypot(receiver[1]-bx,receiver[2]-by)
        if p[0] not in (3,4) or not 4.0<distance<20.0 or bx<self.right-20:
            return None
        # A cutback is useful when the end-line carrier has a poor angle.
        # Both backward and short diagonal passes are legal here; normal
        # passing still applies unchanged outside the late siege.
        angle_gain = abs(by)-abs(receiver[2])
        if receiver[1]<bx-12 or angle_gain<1.2 and receiver[1]<bx+1:
            return None
        best = None
        for speed in (10.0,15.0,20.0):
            if perf_counter()>self.deadline:
                break
            lead = min(0.25,distance/speed)
            tx,ty = self.bound(receiver[1]+receiver[3]*lead,receiver[2]+receiver[4]*lead)
            ux,uy = unit(tx-bx,ty-by)
            kick = self.velocity_kick(vx,vy,ux*speed,uy*speed)
            movement = self.move(p,(bx+0.3,by))
            launched = self.launch(p,ball,kick,movement)
            if launched is None:
                continue
            route = self.path(*launched[0],steps=36)
            ours = self.race(receiver,route)
            enemy = min(self.race(q,route)[0] for q in opponents)
            margin = enemy-ours[0]
            x,y = ours[1]
            gain = abs(by)-abs(y)
            if ours[0]>1.5 or margin<0.14 or x<self.right-23 or gain<0.7:
                continue
            score = 6.0+gain*0.5+min(margin,0.7)*4.0-ours[0]*0.8
            if best is None or score>best[0]:
                best = score,kick,movement,(receiver[0],ours[1],1.8)
        return best

'''
    marker = '    def shell_act(self, obs, protected):'
    if candidate.count(marker)!=1:
        raise RuntimeError("Siege shell anchor changed")
    candidate = candidate.replace(marker,methods+marker)
    old = '        support_id = 3 if self.SUPPORT and wall and bx>0 and not protected else None\n'
    new = '        support_id = 3 if self.siege_mode(obs,ball,wall,protected) else None\n'
    if candidate.count(old)!=1:
        raise RuntimeError("Siege support anchor changed")
    candidate = candidate.replace(old,new)
    old = '''                if i==support_id:
                    aim = self.bound(max(12.0,bx-6.0),(-1 if by>=0 else 1)*5.5)
                else:
                    aim = (self.left+depth,(-4.9,0.0,4.9)[i])'''
    new = '''                if i==support_id:
                    aim = self.bound(clip(bx-8.0,self.right-16,self.right-7),(-1 if by>=0 else 1)*2.0)
                elif i<3:
                    # Preserve each remaining guard's order. Moving guard0
                    # across guard2 would leave a temporary central opening.
                    ratio = 1.0
                    centre = 0.0
                    if self.left+depth+1.0<bx<self.left+25:
                        distance = max(3.0,bx-self.left)
                        ratio = clip((bx-self.left-depth)/distance,0.60,1.0)
                        centre = clip(by*clip(depth/distance,0.0,0.4),-self.goal+4.6*ratio,self.goal-4.6*ratio)
                    aim = (self.left+depth,centre+(4.6,-4.6,0.0)[i]*ratio)
            if self.siege_receive is not None and i==self.siege_receive[0] and not obs.can_kick(i):
                aim = self.bound(*self.race(p,self.stream_path(*ball))[1])'''
    if candidate.count(old)!=1:
        raise RuntimeError("Siege guard geometry anchor changed")
    candidate = candidate.replace(old,new)
    candidate = candidate.replace('            if support_id is not None and i<4:\n',
                                  '            if (support_id is not None or self.siege_recover) and i<4:\n')
    old = '                best = self.shot(p, ball, opponents, movement, wall) if self.SHOT_FIRST else None\n'
    new = '''                best = self.shot(p, ball, opponents, movement, wall) if self.SHOT_FIRST or support_id is not None else None
                if best is None and support_id is not None:
                    best = self.passing(p,ball,friends,opponents)
'''
    if candidate.count(old)!=1:
        raise RuntimeError("Siege outlet search anchor changed")
    candidate = candidate.replace(old,new)
    old = '''                best = self.shot(p,ball,opponents,movement,wall)
                if best is None:
                    best = self.duel(p,ball,opponents,movement)'''
    new = '''                best = self.shot(p,ball,opponents,movement,wall)
                if best is None:
                    best = self.passing(p,ball,friends,opponents)
                if best is None:
                    best = self.duel(p,ball,opponents,movement)'''
    if candidate.count(old)!=1:
        raise RuntimeError("Siege second attacker search anchor changed")
    candidate = candidate.replace(old,new)
    old = '                    _, kick, movement, _ = best\n'
    new = '''                    _, kick, movement, plan = best
                    if plan and self.siege_active:
                        self.siege_receive = (plan[0],obs.tick+int(plan[2]*self.hz),i)
'''
    if candidate.count(old)!=1:
        raise RuntimeError("Siege outlet receive-plan anchor changed")
    candidate = candidate.replace(old,new)
    old = '                    _,kick,movement,_ = best\n'
    new = '''                    _,kick,movement,plan = best
                    if plan and self.siege_active:
                        self.siege_receive = (plan[0],obs.tick+int(plan[2]*self.hz),i)
'''
    if candidate.count(old)!=1:
        raise RuntimeError("Siege support receive-plan anchor changed")
    candidate = candidate.replace(old,new)
    start = candidate.index('    def shell_act(self, obs, protected):')
    end = candidate.index('    def act(self, obs):',start)
    segment = candidate[start:end]
    old = '        return actions\n'
    new = '''        if self.siege_receive is not None and self.siege_active:
            rid,expiry,pid = self.siege_receive
            if rid!=pid and not obs.can_kick(rid):
                actions.move(rid,self.move(friends[rid],self.bound(*self.race(friends[rid],self.stream_path(*ball))[1])))
        return actions
'''
    if segment.count(old)!=1:
        raise RuntimeError("Siege final receive steering anchor changed")
    candidate = candidate[:start]+segment.replace(old,new)+candidate[end:]
    target = ROOT / "experiments/league/siege/team.py"
    compile(candidate,str(target),"exec")
    target.parent.mkdir(parents=True,exist_ok=True)
    contents = candidate.encode("utf-8")
    if target.exists() and target.read_bytes()!=contents:
        raise RuntimeError("Keep siege candidates immutable; use a new revision")
    if not target.exists():
        target.write_bytes(contents)
    print(target)
    print("New helper lines:",len(methods.splitlines()),"Source bytes:",len(contents))


if "--siege" in sys.argv[1:]:
    siege()
    raise SystemExit(0)

if "--open-gap" in sys.argv[1:]:
    open_gap()
    raise SystemExit(0)

if "--guardian" in sys.argv[1:]:
    guardian()
    raise SystemExit(0)

if "--pressure" in sys.argv[1:]:
    pressure_cover()
    raise SystemExit(0)

source = (ROOT / "experiments/red-team/monster/team.py").read_text(encoding="utf-8")
source = source.replace('name = "MONSTER"', 'name = "MONSTER TRANSITION"')
source = source.replace("version = 'v51-stream-post'", "version = 'league-transition-1'")
source = source.replace('self.deadline = perf_counter()+0.007', 'self.deadline = perf_counter()+0.005')
source = source.replace('    def shell_act(self, obs, protected):', '    def parked_act(self, obs, protected):')
start = source.index('    def initial_formation(self, f):')
end = source.index('    def setup(self, f):')
source = source[:start] + '''    def initial_formation(self, f):
        front = -f.centre_circle_radius - 0.5
        return [(f.my_goal[0]+1.2, -4.8), (f.my_goal[0]+1.2, 0.0),
                (f.my_goal[0]+1.2, 4.8), (front-3.0, 10.0), (front, 0.0)]

''' + source[end:]
insert = source.index('    def act(self, obs):')
source = source[:insert] + '''    def shell_act(self, obs, protected):
        """Transition between a close goal screen and a two-player attack.

        Opponent positioning and the ball race determine commitment. There is
        no opponent identity, seed lookup, or assumption about player numbers.
        """
        ball = (*obs.ball.position, *obs.ball.velocity)
        bx, by, vx, vy = ball
        friends = [(p.id, *p.position, *p.velocity, p.kick_cooldown_ticks) for p in obs.my_players]
        opponents = [(p.id, *p.position, *p.velocity, p.kick_cooldown_ticks) for p in obs.opponents]
        deep = sum(q[1]>self.right-5 and abs(q[2])<self.goal+2 for q in opponents)
        # Counter the observed parked defence with the measured four-cover
        # policy. A switch happens on position, never controller identity.
        if deep >= 3:
            return self.parked_act(obs, protected)

        route = self.path(*ball)
        attacks = friends[3:]
        races = {p[0]:self.race(p, route) for p in attacks}
        enemy_time = min(self.race(q, route)[0] for q in opponents)
        order = sorted(attacks, key=lambda p:races[p[0]][0]-(0.09 if p[0]==self.previous_chaser else 0))
        chaser, runner = order
        self.previous_chaser = chaser[0]
        target = self.bound(*races[chaser[0]][1])
        winning = races[chaser[0]][0] < enemy_time+0.15
        # A diagonal runner offers a real forward pass instead of waiting
        # behind the ball. When defending it blocks the immediate return lane.
        side = -1 if by>=0 else 1
        if bx<self.left+18:
            target = self.bound(-22, (1 if by>=0 else -1)*20) if not obs.can_kick(chaser[0]) else target
            support = self.bound(-10, side*12)
        elif winning:
            support = self.bound(bx+10, side*10+by*0.25)
        else:
            support = self.bound(bx-5, by*0.65+side*3)
        targets = {chaser[0]:target, runner[0]:support}
        # Three guards cover both posts and the centre. No guard pursues a
        # speculative midfield interception, so a lost attack leaves cover.
        depth = 1.25 if obs.score[0]<=obs.score[1] else 2.0
        for i, sy in enumerate((-4.8,0.0,4.8)):
            targets[i] = (self.left+depth,sy)
        if bx<self.left+10 and abs(by)>4:
            guard = 2 if by>0 else 0
            targets[guard] = (max(self.left+self.pr+0.02,min(self.left+depth,bx-0.6)),
                              (1 if by>0 else -1)*clip(abs(by),4.8,6.9))
        # In the final attacking third, a spare guard joins only if every
        # observed opponent is safely beyond midfield. Two guards remain.
        if bx>22 and winning and min(q[1] for q in opponents)>4:
            targets[1] = self.bound(bx-10,by*0.2)

        can_play = [p for p in friends if obs.can_kick(p[0])]
        carrier = min(can_play,key=lambda p:math.hypot(p[1]-bx,p[2]-by),default=None)
        actions = TeamAction(debug={"text":"MONSTER transition: three-cover and diagonal support"})
        pending = None
        for p in friends:
            i = p[0]
            movement = self.move(p,targets[i])
            kick = None
            if protected and math.hypot(p[1],p[2])<self.circle+4:
                ux,uy = unit(p[1],p[2])
                movement = self.move(p,(ux*(self.circle+2.5),uy*(self.circle+2.5)))
            if carrier is not None and i==carrier[0] and not protected:
                if i<3 and bx<self.left+15:
                    receiver = min(attacks,key=lambda q:math.hypot(q[1]-bx,q[2]-by))
                    tx,ty = self.bound(max(bx+22,receiver[1]+5),receiver[2])
                    ux,uy = unit(tx-bx,ty-by)
                    kick = self.velocity_kick(vx,vy,ux*25,uy*25)
                else:
                    movement = self.move(p,(bx+0.3,by))
                    # A close-range scoring chance should be evaluated before
                    # the defensive simultaneous-kick duel heuristic.
                    best = self.shot(p,ball,opponents,movement,False) if bx>self.right-20 else None
                    if best is None:
                        best = self.duel(p,ball,opponents,movement)
                    if best is None:
                        best = self.shot(p,ball,opponents,movement,False)
                    if best is None:
                        best = self.touch(p,ball,opponents,(self.right,0.0))
                        passed = self.passing(p,ball,friends,opponents)
                        if passed is not None and (best is None or passed[0]>best[0]+0.3):
                            best = passed
                    if best is not None:
                        _,kick,movement,plan = best
                        if plan:
                            pending = plan[0],plan[1]
            if kick:
                actions.kick(i,kick[0],kick[1],movement=movement)
            else:
                actions.move(i,movement)
        if pending is not None:
            rid,point = pending
            actions.move(rid,self.move(friends[rid],self.bound(*point)))
        return actions

''' + source[insert:]
variant = "attack"
if "--keeper" in sys.argv[1:]:
    variant = "attack2"
    source = source.replace("version = 'league-transition-1'", "version = 'league-transition-2-keeper'")
    source = source.replace('name = "MONSTER TRANSITION"', 'name = "MONSTER TRANSITION KEEPER"')
    source = source.replace('        if bx<self.right-(65 if self.KEEPER_MODEL else 42):',
                            '        if bx<self.right-42:')
    anchor = '        deep = sum(q[1]>self.right-5 and abs(q[2])<self.goal+2 for q in opponents)\n'
    source = source.replace(anchor, anchor + '''        # Model a conventional observed goal guard instead of granting it
        # simultaneous perfect sprints toward every hypothetical shot. The
        # original reach test is retained if the player is not guarding goal.
        self.KEEPER_MODEL = (deep < 3 and opponents[0][1] > self.right-12
                             and abs(opponents[0][2]) < self.goal+3)
''')
target = ROOT / "experiments/league" / variant / "team.py"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(source, encoding="utf-8")
print(target)
