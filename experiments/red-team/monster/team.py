"""MONSTER: independent predictive pressure and close-control soccer.

Single-file controller; runtime inputs are exclusively public observations.
Physics constants come from FieldView or the published course profile.

perf: behaviour-preserving speed pass. Same decisions, same physics:
lookup tables are tuples, hot-loop invariants are hoisted to locals,
reachability gaps are inlined, and wall/bound constants are precomputed.
"""
import math
from time import perf_counter
from soccer import TeamController, TeamAction, PlayerAction


def clip(v, lo, hi):
    return max(lo, min(hi, v))


def unit(x, y):
    d = math.hypot(x, y)
    return (x/d, y/d) if d > 1e-9 else (0.0, 0.0)


class Monster(TeamController):
    name = "MONSTER"
    version = 'v25-fast-post-perf'
    PRESSERS = 2
    CARRY_SPEED = 9.0
    SHOT_MARGIN = -0.08
    LOCK_LEAD = 0
    LOCK_DEPTH = 3.3
    FORMATION = 0
    WIDTH = 11.0
    PASS_WEIGHT = 1.0
    SWEEP = True
    DEFENSE = 0
    KEEPER_DEPTH = 1.6
    DUELS = True
    TWIN_KEEPERS = False
    SHELL = True
    SHELL_DEPTH = 1.2
    SHELL_RELEASE = False
    SHELL_BANK = False
    SHELL_LOCK_FIVE = False
    KEEPER_MODEL = False
    FIXED_OUTLET = True
    OUTLET_X = -20.0
    ADAPTIVE_POSTS = True

    def __init__(self):
        self.reset(0)

    def reset(self, seed):
        self.ready = False
        self.last_score = None
        self.restart_until = -1
        self.restart_owner = 0
        self.receiver = None
        self.previous_chaser = None
        self.deadline = math.inf
        self.outlet_side = None

    def initial_formation(self, f):
        front = -f.centre_circle_radius - 0.3
        if self.SHELL:
            return [(f.my_goal[0]+1.2, 5.4), (f.my_goal[0]+1.2, -1.8),
                    (f.my_goal[0]+1.2, 1.8), (f.my_goal[0]+1.2, -5.4), (front, 0)]
        if self.TWIN_KEEPERS:
            return [(f.my_goal[0]+1.5, -3.2), (f.my_goal[0]+1.5, 3.2),
                    (-21, 0), (front, 0), (front, 10)]
        if self.FORMATION == 1:
            return [(f.my_goal[0]+1.5, 0), (-24, 0), (front, -9), (front, 0), (front, 9)]
        if self.FORMATION == 2:
            return [(f.my_goal[0]+1.5, 0), (front, -7.5), (front, -2.5), (front, 2.5), (front, 7.5)]
        return [(f.my_goal[0]+1.5, 0), (-18, -11), (-18, 11), (front, -3.2), (front, 3.2)]

    def setup(self, f):
        self.dt = 1.0/f.simulation_hz
        self.hz = f.simulation_hz
        self.speed = f.max_speed
        self.acc = f.acceleration*self.dt
        self.drag = f.ball_friction
        self.impulse = f.kick_impulse
        self.kr = f.kick_range
        self.body = f.player_radius+f.ball_radius
        self.pr = f.player_radius
        self.br = f.ball_radius
        self.left, self.right = f.my_goal[0], f.opponent_goal[0]
        self.half = f.height/2
        self.goal = f.goal_width/2
        self.circle = f.centre_circle_radius
        self.damp, self.wall, self.ballcap = 0.90, 0.75, 30.0
        # Precomputed, tuple-backed lookup tables (unchanged values).
        self.roll = tuple(self.dt*(1-self.drag**n)/(1-self.drag) for n in range(151))
        reach = []
        for n in range(151):
            coast = self.dt*self.damp*(1-self.damp**n)/(1-self.damp)
            push = self.acc*self.dt/(1-self.damp)*(n-self.damp*(1-self.damp**n)/(1-self.damp))
            reach.append((coast, push))
        self.reach = tuple(reach)
        # Hoisted constants used every tick in hot loops.
        self.ywall = self.half-self.br
        self.xwall = self.right-self.br
        self.xlo = self.left+self.pr+0.05
        self.xhi = self.right-self.pr-0.05
        self.yhi = self.half-self.pr-0.05
        self.kr86 = self.kr*0.86
        self.speed_dt = self.speed*self.dt
        self.ready = True

    def bound(self, x, y):
        return (clip(x, self.xlo, self.xhi), clip(y, -self.yhi, self.yhi))

    def move(self, p, target):
        damp = self.damp
        acc = self.acc
        dx, dy = target[0]-p[1], target[1]-p[2]
        d = math.hypot(dx, dy)
        gain = min(self.speed, d*6.0)/max(d, 1e-9)
        ax = (dx*gain-p[3]*damp)/acc
        ay = (dy*gain-p[4]*damp)/acc
        norm = max(1.0, math.hypot(ax, ay))
        return ax/norm, ay/norm

    def player_step(self, p, movement):
        damp = self.damp
        acc = self.acc
        vx, vy = p[3]*damp+movement[0]*acc, p[4]*damp+movement[1]*acc
        norm = max(1.0, math.hypot(vx, vy)/self.speed)
        vx, vy = vx/norm, vy/norm
        x, y = self.bound(p[1]+vx*self.dt, p[2]+vy*self.dt)
        return (p[0], x, y, vx, vy, max(0, p[5]-1))

    def travel_gap(self, p, x, y, n, radius):
        coast, push = self.reach[n if n < 151 else 150]
        dx, dy = x-p[1], y-p[2]
        return max(math.hypot(dx, dy)-self.speed_dt*n,
                   math.hypot(dx-p[3]*coast, dy-p[4]*coast)-push)-radius

    def path(self, x, y, vx, vy, steps=65):
        dt = self.dt
        drag = self.drag
        wall = self.wall
        ywall = self.ywall
        xwall = self.xwall
        right = self.right
        goal = self.goal
        samples = [(0, x, y)]
        append = samples.append
        for n in range(1, steps+1):
            x += vx*dt
            y += vy*dt
            vx *= drag
            vy *= drag
            if y > ywall or y < -ywall:
                s = 1 if y > 0 else -1
                y = s*2*ywall-y
                vy = -s*abs(vy)*wall
            if x > xwall or x < -xwall:
                if abs(y) <= goal and abs(x) > right:
                    append((n, x, y))
                    break
                if abs(y) > goal:
                    s = 1 if x > 0 else -1
                    x = s*2*xwall-x
                    vx = -s*abs(vx)*wall
            append((n, x, y))
        return samples

    def race(self, p, path):
        reach = self.reach
        kr86 = self.kr86
        speed = self.speed
        speed_dt = self.speed_dt
        dt = self.dt
        cooldown = p[5]
        px, py, pvx, pvy = p[1], p[2], p[3], p[4]
        hypot = math.hypot
        best = None
        for n, x, y in path:
            if n > 0 and n % 2 and n > 8:
                continue
            # Inlined travel_gap(p, x, y, n, kr*0.86) with clamped index.
            coast, push = reach[n if n < 151 else 150]
            dx, dy = x-px, y-py
            gap = max(hypot(dx, dy)-speed_dt*n, hypot(dx-pvx*coast, dy-pvy*coast)-push)-kr86
            if gap <= 0 and cooldown <= n:
                return n*dt, (x, y)
            cost = n*dt+max(0, gap)/speed
            if best is None or cost < best[0]:
                best = (cost, (x, y))
        return best

    def velocity_kick(self, vx, vy, tx, ty):
        dx, dy = tx-vx, ty-vy
        length = math.hypot(dx, dy)
        if length < 0.015:
            return None
        return ((dx/length, dy/length), min(1.0, length/self.impulse))

    def duel(self, p, ball, opponents, movement):
        bx, by, vx, vy = ball
        active = [q for q in opponents if q[5] == 0 and math.hypot(q[1]-bx, q[2]-by) < self.kr+0.45]
        if not self.DUELS or not active:
            return None
        # Robust against either legal ordering of simultaneous opponent kicks.
        ex, ey = unit(self.left-bx, -by)
        enemy_impulses = [(ex*self.impulse, ey*self.impulse), (-8.0-vx, -vy), (0, 0)]
        best = None
        for angle in (0, -0.35, 0.35, -0.7, 0.7):
            ux, uy = math.cos(angle), math.sin(angle)
            worst = 100.0
            for evx, evy in enemy_impulses:
                for enemy_first in (False, True):
                    sx, sy = vx, vy
                    impulses = [(ux*self.impulse, uy*self.impulse), (evx, evy)]
                    if enemy_first:
                        impulses.reverse()
                    for dx, dy in impulses:
                        sx, sy = sx+dx, sy+dy
                        scale = max(1, math.hypot(sx, sy)/self.ballcap)
                        sx, sy = sx/scale, sy/scale
                    value = sx*0.2-abs(by+sy*0.3)*0.015
                    worst = min(worst, value)
            if best is None or worst > best[0]:
                best = (worst, ((ux, uy), 1.0), movement, None)
        return best

    def launch(self, p, ball, kick, movement):
        bx, by, vx, vy = ball
        next_p = self.player_step(p, movement)
        if math.hypot(next_p[1]-bx, next_p[2]-by) > self.kr-0.04:
            return None
        if kick:
            vx += kick[0][0]*kick[1]*self.impulse
            vy += kick[0][1]*kick[1]*self.impulse
        norm = max(1.0, math.hypot(vx, vy)/self.ballcap)
        vx, vy = vx/norm, vy/norm
        x, y = bx+vx*self.dt, by+vy*self.dt
        vx, vy = vx*self.drag, vy*self.drag
        dx, dy = x-next_p[1], y-next_p[2]
        distance = math.hypot(dx, dy)
        if 1e-8 < distance < self.body:
            nx, ny = dx/distance, dy/distance
            x, y = next_p[1]+nx*self.body, next_p[2]+ny*self.body
            closing = (vx-next_p[3])*nx+(vy-next_p[4])*ny
            if closing < 0:
                vx -= 1.25*closing*nx
                vy -= 1.25*closing*ny
        return (x, y, vx, vy), next_p

    def shot(self, p, ball, opponents, movement, wall):
        bx, by, vx, vy = ball
        if bx < self.right-(65 if self.KEEPER_MODEL else 42):
            return None
        best = None
        deadline = self.deadline
        perf = perf_counter
        goal = self.goal
        right = self.right
        dt = self.dt
        drag = self.drag
        hypot = math.hypot
        ywall = self.ywall
        xwall = self.xwall
        speed = self.speed
        speed_dt = self.speed_dt
        kr = self.kr
        body = self.body
        reach = self.reach
        shot_margin = self.SHOT_MARGIN
        impulse_sq = self.impulse*self.impulse
        max_ticks = 141 if self.KEEPER_MODEL else 61
        for fraction in (-0.97, 0.97, -0.85, 0.85, -0.6, 0.6, -0.3, 0.3, 0):
            if perf() > deadline:
                return best
            ux, uy = unit(right+0.25-bx, goal*fraction-by)
            along = vx*ux+vy*uy
            sideways = max(0.0, vx*vx+vy*vy-along*along)
            if sideways >= impulse_sq:
                continue
            launch_speed = min(self.ballcap, along+math.sqrt(impulse_sq-sideways))
            if launch_speed < 10:
                continue
            kick = self.velocity_kick(vx, vy, ux*launch_speed, uy*launch_speed)
            launch = self.launch(p, ball, kick, movement)
            if launch is None:
                continue
            (x, y, sx, sy), _ = launch
            modeled_keeper = opponents[0]
            previous_ball = ball
            margin = 100.0
            scored = False
            for n in range(1, max_ticks):
                oldx, oldy, oldvx, oldvy = previous_ball
                if self.KEEPER_MODEL and not wall:
                    # A public-observation model of a line keeper who sweeps
                    # nearby balls. No controller import or hidden state.
                    depth = 2.2
                    tx = right-depth
                    ty = oldy*depth/max(3.0, right-oldx)
                    if oldvx > 8 and hypot(oldvx, oldvy) >= 12 and oldx < tx:
                        tau = (tx-oldx)/oldvx
                        if 0 < tau < 1.25:
                            ty = oldy+oldvy*tau
                    ty = clip(ty, -goal+0.6, goal-0.6)
                    if oldx > right-10:
                        own_eta = max(0, hypot(modeled_keeper[1]-oldx, modeled_keeper[2]-oldy)-kr*0.8)/speed+0.3
                        field_eta = min((max(0, hypot(q[1]-oldx, q[2]-oldy)-kr*0.8)/speed+0.3 for q in opponents[1:]), default=20)
                        if own_eta < field_eta*0.85:
                            tx, ty = min(right-2, oldx), clip(oldy, -self.half+2, self.half-2)
                    before = hypot(modeled_keeper[1]-oldx, modeled_keeper[2]-oldy)
                    moved = self.player_step(modeled_keeper, self.move(modeled_keeper, (tx, ty)))
                    if n > opponents[0][5] and before <= kr and hypot(moved[1]-oldx, moved[2]-oldy) < kr-0.18:
                        margin = -100
                        break
                    modeled_keeper = moved
                if n > 1:
                    x += sx*dt
                    y += sy*dt
                    sx *= drag
                    sy *= drag
                if y > ywall or y < -ywall or (x > xwall and abs(y) > goal):
                    break
                for q in opponents:
                    if self.KEEPER_MODEL and not wall and q[0] == opponents[0][0]:
                        margin = min(margin, (hypot(x-modeled_keeper[1], y-modeled_keeper[2])-body)/speed)
                        continue
                    radius = kr if q[5] < n else body
                    reach_limit = speed_dt*n+radius+speed*0.7
                    if (x-q[1])**2+(y-q[2])**2 > reach_limit*reach_limit:
                        continue
                    gap = self.travel_gap(q, x, y, n, radius)
                    if wall and q[1] > right-3.5:
                        # Observed stationary walls cannot sprint toward every
                        # hypothetical target at once. Retain a body margin and
                        # forbid launches from within their immediate kick range.
                        coast = reach[n][0]
                        gap = hypot(x-q[1]-q[3]*coast, y-q[2]-q[4]*coast)-body-0.12
                        if n == 1 and q[5] == 0 and hypot(bx-q[1], by-q[2]) < kr+0.15:
                            gap = -10.0
                    margin = min(margin, gap/speed)
                if margin < shot_margin:
                    break
                if x > right:
                    scored = abs(y) < goal-0.025
                    break
                previous_ball = (x, y, sx, sy)
            if scored and margin >= shot_margin:
                score = 12+min(margin, 0.7)*5-n*dt*0.8
                if best is None or score > best[0]:
                    best = (score, kick, movement, None)
        return best

    def touch(self, p, ball, opponents, stage):
        bx, by, vx, vy = ball
        angle = math.atan2(stage[1]-by, stage[0]-bx)
        best = None
        old_distance = math.hypot(stage[0]-bx, stage[1]-by)
        deadline = self.deadline
        perf = perf_counter
        dt = self.dt
        drag = self.drag
        hypot = math.hypot
        body = self.body
        kr = self.kr
        ywall = self.ywall
        xwall = self.xwall
        player_step = self.player_step
        move = self.move
        bound = self.bound
        travel_gap = self.travel_gap
        speed = self.speed
        for offset in (0, -0.35, 0.35, -0.75, 0.75, -1.2, 1.2):
            if perf() > deadline:
                return best
            ux, uy = math.cos(angle+offset), math.sin(angle+offset)
            for carry in (self.CARRY_SPEED, 5.5):
                movement = move(p, bound(bx+ux*2, by+uy*2))
                kick = self.velocity_kick(vx, vy, ux*carry, uy*carry)
                launched = self.launch(p, ball, kick, movement)
                if launched is None:
                    continue
                (x, y, sx, sy), own = launched
                risk = 1.0
                for n in range(1, 7):
                    if n > 1:
                        own = player_step(own, move(own, bound(x+sx*0.12, y+sy*0.12)))
                        x += sx*dt
                        y += sy*dt
                        sx *= drag
                        sy *= drag
                        dx, dy = x-own[1], y-own[2]
                        d = hypot(dx, dy)
                        if 1e-8 < d < body:
                            nx, ny = dx/d, dy/d
                            x, y = own[1]+nx*body, own[2]+ny*body
                            closing = (sx-own[3])*nx+(sy-own[4])*ny
                            if closing < 0:
                                sx -= 1.25*closing*nx
                                sy -= 1.25*closing*ny
                    for q in opponents:
                        radius = kr if q[5] < n else body
                        risk = min(risk, travel_gap(q, x, y, n, radius)/speed)
                    if y > ywall or y < -ywall or x > xwall or x < -xwall:
                        continue
                    progress = old_distance-math.hypot(stage[0]-x, stage[1]-y)
                    gap = hypot(x-own[1], y-own[2])
                    score = progress*1.0+min(risk, 0.5)*7-max(0, gap-kr+0.1)*2
                    if x < self.left+4:
                        score -= 3
                    if best is None or score > best[0]:
                        best = (score, kick, movement, None)
        return best

    def passing(self, p, ball, friends, opponents):
        bx, by, vx, vy = ball
        best = None
        deadline = self.deadline
        perf = perf_counter
        bound = self.bound
        move = self.move
        race = self.race
        launch_fn = self.launch
        path_fn = self.path
        velocity_kick = self.velocity_kick
        for q in friends[1:]:
            if perf() > deadline:
                return best
            if q[0] == p[0] or q[1] < bx+3:
                continue
            gap = math.hypot(q[1]-bx, q[2]-by)
            if not 5 < gap < 33:
                continue
            for speed in (16.0, 23.0):
                lead = min(0.8, gap/speed)
                tx, ty = bound(q[1]+q[3]*lead+2, q[2]+q[4]*lead)
                ux, uy = unit(tx-bx, ty-by)
                kick = velocity_kick(vx, vy, ux*speed, uy*speed)
                movement = move(p, (bx+0.3, by))
                launch = launch_fn(p, ball, kick, movement)
                if launch is None:
                    continue
                route = path_fn(*launch[0], steps=40)
                ours = race(q, route)
                theirs = min(race(o, route)[0] for o in opponents)
                if ours[0] > 1.8 or theirs < ours[0]+0.18 or ours[1][0] < bx+4:
                    continue
                score = self.PASS_WEIGHT*(0.3*(ours[1][0]-bx)+min(0.7, theirs-ours[0])*3-ours[0]*0.7)
                if best is None or score > best[0]:
                    best = (score, kick, movement, (q[0], ours[1], 2.0))
        return best

    def lock(self, obs):
        actions = TeamAction(debug={"text": "MONSTER lead screen"})
        for i, v in enumerate(obs.my_players):
            p = (v.id, *v.position, *v.velocity, v.kick_cooldown_ticks)
            target = (self.left+self.LOCK_DEPTH, (i-2)*2.75)
            movement = self.move(p, target)
            if obs.can_kick(v.id):
                actions.kick(v.id, (1, 0), 1.0, movement=movement)
            else:
                actions.move(v.id, movement)
        return actions

    def shell_act(self, obs, protected):
        """Four covering players and one fast outlet; no opponent identity test."""
        ball = (*obs.ball.position, *obs.ball.velocity)
        bx, by, vx, vy = ball
        if self.FIXED_OUTLET and self.outlet_side is None and bx < self.left+25 and abs(by) > 3:
            self.outlet_side = 1 if by > 0 else -1
        release_side = self.outlet_side if self.FIXED_OUTLET and self.outlet_side is not None else (1 if by >= 0 else -1)
        friends = [(p.id, *p.position, *p.velocity, p.kick_cooldown_ticks) for p in obs.my_players]
        opponents = [(p.id, *p.position, *p.velocity, p.kick_cooldown_ticks) for p in obs.opponents]
        outlet = friends[4]
        if bx < self.left+20 and not obs.can_kick(4):
            side = release_side
            target = self.bound(self.OUTLET_X if self.FIXED_OUTLET else max(-7.0, outlet[1]), side*21.0)
        else:
            path = self.path(*ball)
            target = self.bound(*self.race(outlet, path)[1])
        wall = sum(q[1] > self.right-3.5 and abs(q[2]) < self.goal+1 for q in opponents) >= 4
        depth = self.LOCK_DEPTH if obs.score[0] > obs.score[1] else self.SHELL_DEPTH
        if self.SHELL_LOCK_FIVE and obs.score[0] > obs.score[1]:
            return self.lock(obs)
        actions = TeamAction(debug={"text": "MONSTER four-cover counter"})
        for i, p in enumerate(friends):
            aim = target if i == 4 else (self.left+depth, (5.4, -1.8, 1.8, -5.4)[i])
            if self.ADAPTIVE_POSTS and bx < self.left+12 and abs(by) > 4.0 and i == (0 if by > 0 else 3):
                side = 1 if by > 0 else -1
                aim = (max(self.left+self.pr+0.02, min(self.left+depth, bx-0.6)),
                       side*clip(abs(by), 5.4, self.goal+2.5))
            movement = self.move(p, aim)
            kick = None
            if i == 4 and not protected and obs.can_kick(i):
                movement = self.move(p, (bx+0.3, by))
                stage = (self.right+1, (1 if by >= 0 else -1)*(self.goal+1.3)) if wall else (self.right, 0)
                best = self.duel(p, ball, opponents, movement)
                if best is None:
                    best = self.shot(p, ball, opponents, movement, wall)
                if best is None:
                    best = self.touch(p, ball, opponents, stage)
                if best:
                    _, kick, movement, _ = best
            elif i < 4 and not protected and obs.can_kick(i):
                side = release_side
                tx, ty = max(-4.0, outlet[1]+5), side*22.0
                if self.SHELL_BANK:
                    boundary = side*(self.half-self.br)
                    ty = boundary+(boundary-ty)/self.wall
                ux, uy = unit(tx-bx, ty-by)
                kick = ((ux, uy), 1.0)
            if protected and i == 4 and math.hypot(p[1], p[2]) < self.circle+4:
                ux, uy = unit(p[1], p[2])
                movement = self.move(p, (ux*(self.circle+2.5), uy*(self.circle+2.5)))
            if kick:
                actions.kick(i, kick[0], kick[1], movement=movement)
            else:
                actions.move(i, movement)
        return actions

    def act(self, obs):
        self.deadline = perf_counter()+0.007
        if not self.ready:
            self.setup(obs.field)
        score = tuple(obs.score)
        if self.last_score is None or score != self.last_score:
            self.restart_until = obs.tick+int(3*self.hz)
            self.restart_owner = obs.ball.controlling_team
            self.receiver = None
        self.last_score = score
        ball = (*obs.ball.position, *obs.ball.velocity)
        bx, by, vx, vy = ball
        if math.hypot(bx, by) > 0.5 or math.hypot(vx, vy) > 0.1:
            self.restart_until = -1
        protected = obs.tick < self.restart_until and self.restart_owner == 1
        visible_enemy_wall = sum(q.position[0] > self.right-3.5 and abs(q.position[1]) < self.goal+1 for q in obs.opponents) >= 4
        if self.SHELL and not (self.SHELL_RELEASE and (visible_enemy_wall or score[0] < score[1])):
            return self.shell_act(obs, protected)
        if self.LOCK_LEAD and score[0]-score[1] >= self.LOCK_LEAD and not protected:
            return self.lock(obs)
        friends = [(p.id, *p.position, *p.velocity, p.kick_cooldown_ticks) for p in obs.my_players]
        opponents = [(p.id, *p.position, *p.velocity, p.kick_cooldown_ticks) for p in obs.opponents]
        trajectory = self.path(*ball)
        races = {p[0]: self.race(p, trajectory) for p in friends}
        enemy_time = min(self.race(q, trajectory)[0] for q in opponents)
        field_players = friends[2:] if self.TWIN_KEEPERS else friends[1:]
        order = sorted(field_players, key=lambda p: races[p[0]][0]-(0.07 if p[0] == self.previous_chaser else 0))
        chaser = order[0]
        self.previous_chaser = chaser[0]
        wall = sum(q[1] > self.right-3.5 and abs(q[2]) < self.goal+1 for q in opponents) >= 4
        targets = {chaser[0]: self.bound(*races[chaser[0]][1])}
        free = order[1:]
        ours = races[chaser[0]][0]+0.1 < enemy_time
        if wall:
            for p, q in zip(sorted(free, key=lambda p: p[2]), sorted(opponents, key=lambda p: abs(p[2]-by))[:len(free)]):
                targets[p[0]] = self.bound(q[1]+0.1, q[2])
        elif not ours:
            if self.PRESSERS >= 2 and free and bx > self.left+15:
                q = free.pop(0)
                targets[q[0]] = self.bound(bx-3.5, by*0.8)
            if self.PRESSERS >= 3 and len(free) >= 2 and bx > -10:
                q = free.pop(0)
                targets[q[0]] = self.bound(bx+1.5, by+(3.0 if q[2] >= by else -3.0))
            threats = sorted(opponents, key=lambda q: q[1]+abs(q[2])*0.15)
            for p in free:
                threat = next((q for q in threats if math.hypot(q[1]-bx, q[2]-by) > 4), None)
                if threat:
                    threats.remove(threat)
                    ux, uy = unit(self.left-threat[1], -threat[2])
                    targets[p[0]] = self.bound(threat[1]+3*ux, threat[2]+3*uy)
                else:
                    targets[p[0]] = self.bound(bx-9, by*0.4)
        else:
            cover = min(free, key=lambda p: p[1])
            targets[cover[0]] = self.bound(bx-8, by*0.45)
            runners = sorted((p for p in free if p[0] != cover[0]), key=lambda p: p[2])
            for i, p in enumerate(runners):
                targets[p[0]] = self.bound(bx+10+3*i, (-1 if i == 0 else 1)*self.WIDTH+by*0.15)
        keeper = friends[0]
        if self.DEFENSE and bx < 12 and (not ours or self.DEFENSE >= 2):
            guards = sorted((p for p in friends[1:] if p[0] != chaser[0]), key=lambda p: p[1])[:2]
            guards.sort(key=lambda p: p[2])
            for index, guard in enumerate(guards):
                targets[guard[0]] = (self.left+2.0, (-1 if index == 0 else 1)*4.6)
        kx = self.left+self.KEEPER_DEPTH
        ky = by*self.KEEPER_DEPTH/max(3, bx-self.left)
        if vx < -1:
            scale = (kx-bx)/vx
            stop = abs(vx)*self.dt/(1-self.drag)
            if 0 < scale < 2.2 and bx-kx < stop:
                gy = by+vy*(self.left-bx)/vx
                if abs(gy) < self.goal+0.2:
                    ky = by+vy*scale
        targets[0] = (kx, clip(ky, -self.goal+0.25, self.goal-0.25))
        if self.TWIN_KEEPERS:
            threatening = vx < -1 and bx-kx < abs(vx)*self.dt/(1-self.drag) and abs(by+vy*(self.left-bx)/vx) < self.goal+0.3
            gy = by+vy*(kx-bx)/vx if threatening else None
            targets[0] = (kx, clip(gy, -self.goal+0.2, -0.5) if gy is not None else -3.2)
            targets[1] = (kx, clip(gy, 0.5, self.goal-0.2) if gy is not None else 3.2)
        if self.SWEEP and bx < self.left+12 and races[0][0]+0.35 < enemy_time and races[0][0] < 0.8:
            targets[0] = self.bound(*races[0][1])
        if self.receiver:
            rid, passer, expiry = self.receiver
            if obs.tick > expiry or obs.ball.last_touch not in (passer, None):
                self.receiver = None
            else:
                targets[rid] = self.bound(*races[rid][1])
        actions = TeamAction(debug={"text": "MONSTER wall siege" if wall else "MONSTER predictive pressure"})
        carrier = min((p for p in friends if obs.can_kick(p[0])), key=lambda p: math.hypot(p[1]-bx, p[2]-by), default=None)
        for p in friends:
            movement = self.move(p, targets.get(p[0], p[1:3]))
            if protected and math.hypot(p[1], p[2]) < self.circle+4:
                ux, uy = unit(p[1], p[2])
                movement = self.move(p, (ux*(self.circle+2.5), uy*(self.circle+2.5)))
            kick = None
            if carrier is not None and p[0] == carrier[0] and not protected:
                movement = self.move(p, (bx+0.3, by))
                stage = (self.right, 0)
                if wall:
                    stage = (self.right+1.0, (1 if by >= 0 else -1)*(self.goal+1.3))
                best = self.duel(p, ball, opponents, movement)
                if best is None:
                    best = self.shot(p, ball, opponents, movement, wall)
                if best is None:
                    best = self.touch(p, ball, opponents, stage)
                    passed = self.passing(p, ball, friends, opponents) if not wall else None
                    if passed is not None and (best is None or passed[0] > best[0]+0.5):
                        best = passed
                if best:
                    _, kick, movement, plan = best
                    if plan:
                        rid, point, seconds = plan
                        self.receiver = (rid, p[0], obs.tick+int(seconds*self.hz))
                        targets[rid] = self.bound(*point)
                if (p[0] == 0 or self.TWIN_KEEPERS and p[0] == 1) and (best is None or best[0] < 0):
                    kick = self.velocity_kick(vx, vy, 22, -8 if by > 0 else 8)
            if kick:
                actions.kick(p[0], kick[0], kick[1], movement=movement)
            else:
                actions.move(p[0], movement)
        if self.receiver:
            rid = self.receiver[0]
            if carrier is None or rid != carrier[0]:
                p = friends[rid]
                actions.move(rid, self.move(p, targets[rid]))
        return actions