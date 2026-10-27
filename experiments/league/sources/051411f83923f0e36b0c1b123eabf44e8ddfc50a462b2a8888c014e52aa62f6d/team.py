"""Independent pressure opponent for offline league testing. Not a submission."""
import math
from soccer import TeamController, TeamAction


def clip(x, lo, hi):
    return max(lo, min(hi, x))


class Counter(TeamController):
    name = "Counter"
    version = "1"
    BACKS = 3
    SHOT_RANGE = 48
    PRESS = 1

    def reset(self, seed):
        self.score = None
        self.restart = -1
        self.owner = None

    def initial_formation(self, f):
        return [(f.my_goal[0]+1.5, 0), (-23, -6), (-23, 6),
                (-f.centre_circle_radius-1, -3), (-f.centre_circle_radius-1, 3)]

    def move(self, p, target, f):
        dx, dy = target[0]-p.position[0], target[1]-p.position[1]
        d = math.hypot(dx, dy)
        gain = min(f.max_speed, d*5)/max(d, 1e-9)
        ax = (dx*gain-p.velocity[0]*0.9)/(f.acceleration/f.simulation_hz)
        ay = (dy*gain-p.velocity[1]*0.9)/(f.acceleration/f.simulation_hz)
        norm = max(1, math.hypot(ax, ay))
        return ax/norm, ay/norm

    def eta(self, p, x, y, f):
        return max(0, math.hypot(x-p.position[0]-p.velocity[0]*0.2,
                                 y-p.position[1]-p.velocity[1]*0.2)-f.kick_range)/f.max_speed

    def act(self, obs):
        f = obs.field
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        left, right = f.my_goal[0], f.opponent_goal[0]
        goal, half = f.goal_width/2, f.height/2
        if self.score is None or self.score != tuple(obs.score):
            self.restart = obs.tick+int(3*f.simulation_hz)
            self.owner = obs.ball.controlling_team
        self.score = tuple(obs.score)
        if math.hypot(bx, by)>0.5 or math.hypot(vx, vy)>0.1:
            self.restart = -1
        protected = obs.tick<self.restart and self.owner==1
        # Cheap reachable-ball prediction, independent of Monster's trajectory model.
        races = {}
        for p in obs.my_players:
            best = (100, bx, by)
            for n in (0, 3, 6, 10, 16, 24, 36, 50):
                t = n/f.simulation_hz
                roll = (1-f.ball_friction**n)/(1-f.ball_friction)/f.simulation_hz
                x = clip(bx+vx*roll, left+1.5, right-1.5)
                y = clip(by+vy*roll, -half+1.5, half-1.5)
                cost = max(t, self.eta(p, x, y, f))
                if cost < best[0]:
                    best = cost, x, y
            races[p.id] = best
        field = sorted(obs.my_players[1:], key=lambda p:races[p.id][0])
        chaser = field[0]
        targets = {chaser.id: races[chaser.id][1:]}
        free = field[1:]
        if self.PRESS>1 and bx>-36:
            p = free.pop(0)
            targets[p.id] = (bx-2, by+(3 if p.position[1]>by else -3))
        backs = sorted(free, key=lambda p:p.position[0])[:self.BACKS]
        for i, p in enumerate(backs):
            targets[p.id] = (left+2.3 if self.BACKS>1 else min(-10, bx-14),
                             (-1 if i==0 else 1)*4.5 if self.BACKS>1 else by*0.3)
        for i, p in enumerate(q for q in free if q not in backs):
            targets[p.id] = (clip(bx+9, -15, right-5), (-1 if i%2==0 else 1)*10)
        keeper_y = by*2/max(3, bx-left)
        if vx<-2 and bx>left+2:
            crossing = by+vy*(left+2-bx)/vx
            if abs(crossing)<goal+1:
                keeper_y = crossing
        targets[0] = (left+1.5, clip(keeper_y, -goal+0.4, goal-0.4))
        actions = TeamAction()
        for p in obs.my_players:
            target = targets[p.id]
            target = (clip(target[0], left+1.1, right-1.1), clip(target[1], -half+1.1, half-1.1))
            if protected and math.hypot(*target)<f.centre_circle_radius+2:
                target = (-f.centre_circle_radius-2, clip(target[1], -half+2, half-2))
            movement = self.move(p, target, f)
            if protected or not obs.can_kick(p.id):
                actions.move(p.id, movement)
                continue
            if p.id==0 or bx<left+10:
                target = (max(bx+25, 0), 20 if by>=0 else -20)
                power = 1
            else:
                # Pick a shot lane by distance from the predicted opponent positions.
                best = None
                for gy in (-goal+0.5, -goal/2, 0, goal/2, goal-0.5):
                    dx, dy = right+0.3-bx, gy-by
                    length = math.hypot(dx, dy)
                    ux, uy = dx/length, dy/length
                    clearance = 100
                    for q in obs.opponents:
                        along = (q.position[0]-bx)*ux+(q.position[1]-by)*uy
                        if 0<along<length:
                            t = along/24
                            qx, qy = q.position[0]+q.velocity[0]*min(0.3, t), q.position[1]+q.velocity[1]*min(0.3, t)
                            gap = abs((qx-bx)*uy-(qy-by)*ux)-f.player_radius-f.ball_radius
                            clearance = min(clearance, gap-min(4, t*3))
                    value = clearance-abs(gy)*0.015
                    if best is None or value>best[0]:
                        best = value, gy
                if bx>right-self.SHOT_RANGE and (best[0]>-2 or bx>right-13):
                    target, power = (right+0.3, best[1]), 1
                else:
                    # Short touch, or a safe forward pass to an unmarked runner.
                    target, power = (right, clip(by*0.7, -goal+1, goal-1)), 0.34
                    for q in obs.my_players[1:]:
                        if q.id==p.id or q.position[0]<bx+8:
                            continue
                        if min(math.hypot(q.position[0]-o.position[0], q.position[1]-o.position[1]) for o in obs.opponents)>7:
                            distance = math.hypot(q.position[0]-bx, q.position[1]-by)
                            if distance<35:
                                target, power = (q.position[0]+2, q.position[1]), clip(distance/38, 0.25, 0.9)
            dx, dy = target[0]-bx, target[1]-by
            norm = max(1e-9, math.hypot(dx, dy))
            actions.kick(p.id, (dx/norm, dy/norm), power, movement=movement)
        return actions
