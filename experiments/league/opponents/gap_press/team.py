"""Independent close-pressure stress opponent, motivated by public replay geometry.

Targets observed shooting gaps with two advanced players. This is an original
synthetic test opponent, not a reconstruction of any student's private code.
"""
import math
from soccer import TeamController, TeamAction


def clamp(value, lower, upper):
    return max(lower, min(upper, value))


def direction(x, y):
    length = math.hypot(x, y)
    return (x/length, y/length) if length > 1e-9 else (1, 0)


class GapPress(TeamController):
    name = "Gap Press Stress"
    version = "1"

    def reset(self, seed):
        self.previous_score = None
        self.restart_owner = None
        self.restart_until = -1
        self.previous_chaser = None

    def initial_formation(self, field):
        front = -field.centre_circle_radius-1
        return [(field.my_goal[0]+3.5, 0), (-20, 0), (-7, -8), (front, -3), (front, 3)]

    def move(self, player, target, field):
        dx, dy = target[0]-player.position[0], target[1]-player.position[1]
        distance = math.hypot(dx, dy)
        gain = min(field.max_speed, distance*6)/max(distance, 1e-9)
        acceleration = field.acceleration/field.simulation_hz
        ax = (dx*gain-player.velocity[0]*.9)/acceleration
        ay = (dy*gain-player.velocity[1]*.9)/acceleration
        norm = max(1, math.hypot(ax, ay))
        return ax/norm, ay/norm

    def intercept(self, player, obs):
        field = obs.field
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        best = (1e6, bx, by)
        for ticks in (0, 3, 6, 10, 16, 24, 36):
            elapsed = ticks/field.simulation_hz
            roll = (1-field.ball_friction**ticks)/(1-field.ball_friction)/field.simulation_hz
            x = clamp(bx+vx*roll, field.my_goal[0]+1.1, field.opponent_goal[0]-1.1)
            y = clamp(by+vy*roll, -field.height/2+1.1, field.height/2-1.1)
            distance = math.hypot(x-player.position[0]-player.velocity[0]*.15,
                                  y-player.position[1]-player.velocity[1]*.15)
            eta = max(0, distance-field.kick_range)/field.max_speed
            value = max(elapsed, eta)
            if value < best[0]:
                best = value, x, y
        return best

    def gap_shot(self, obs):
        field = obs.field
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        right, goal = field.opponent_goal[0], field.goal_width/2
        ys = [-goal+.35, -.75*goal, -.5*goal, -.25*goal, 0,
              .25*goal, .5*goal, .75*goal, goal-.35]
        guards = sorted(q.position[1] for q in obs.opponents
                        if q.position[0] > right-8 and abs(q.position[1]) < goal+1)
        for lower, upper in zip(guards, guards[1:]):
            ys.append(clamp((lower+upper)/2, -goal+.25, goal-.25))
        best = None
        for target_y in ys:
            ux, uy = direction(right+.2-bx, target_y-by)
            desired = (ux*26-vx, uy*26-vy)
            kx, ky = direction(*desired)
            power = min(1, math.hypot(*desired)/field.kick_impulse)
            sx, sy = vx+kx*power*field.kick_impulse, vy+ky*power*field.kick_impulse
            scale = max(1, math.hypot(sx, sy)/30)
            sx, sy = sx/scale, sy/scale
            if sx < 3:
                continue
            crossing_y = by+sy*(right-bx)/sx
            if abs(crossing_y) > goal-.1:
                continue
            lane_x, lane_y = direction(sx, sy)
            clearance = 20
            for opponent in obs.opponents:
                dx, dy = opponent.position[0]-bx, opponent.position[1]-by
                along = dx*lane_x+dy*lane_y
                if along < -.2:
                    continue
                flight = max(0, along)/max(3, math.hypot(sx, sy))
                lookahead = min(.25, flight)
                ox = dx+opponent.velocity[0]*lookahead
                oy = dy+opponent.velocity[1]*lookahead
                gap = abs(ox*lane_y-oy*lane_x)-field.player_radius-field.ball_radius
                # A stationary line guard is already in position; a mobile
                # defender may also run toward the flight before it arrives.
                if math.hypot(*opponent.velocity) > .7:
                    gap -= min(2, max(0, flight-.12)*3)
                if opponent.kick_cooldown_ticks <= flight*field.simulation_hz:
                    gap -= .16
                clearance = min(clearance, gap)
            value = clearance-.015*abs(crossing_y)-.008*(right-bx)
            if best is None or value > best[0]:
                best = value, (kx, ky), power
        return best

    def act(self, obs):
        field = obs.field
        left, right = field.my_goal[0], field.opponent_goal[0]
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        if self.previous_score is None or self.previous_score != tuple(obs.score):
            self.restart_owner = obs.ball.controlling_team
            self.restart_until = obs.tick+3*field.simulation_hz
        self.previous_score = tuple(obs.score)
        if math.hypot(bx, by) > .5 or math.hypot(vx, vy) > .1:
            self.restart_until = -1
        protected = obs.tick < self.restart_until and self.restart_owner == 1
        races = {p.id: self.intercept(p, obs) for p in obs.my_players[1:]}
        players = sorted(obs.my_players[1:], key=lambda p:races[p.id][0]-(.04 if p.id == self.previous_chaser else 0))
        chaser, support = players[:2]
        self.previous_chaser = chaser.id
        targets = {chaser.id: races[chaser.id][1:]}
        if bx > right-22:
            # Maintain a second close attacker on the other side of the mouth.
            targets[support.id] = (max(right-9, bx-3), -7.8 if by > 0 else 7.8)
        else:
            targets[support.id] = (bx+2, by+(3 if support.position[1] > by else -3))
        cover, runner = players[2:]
        targets[cover.id] = (clamp(bx-15, -25, 12), by*.15)
        targets[runner.id] = (clamp(bx-7, -18, right-10), -9 if by > 0 else 9)
        keeper_y = clamp(by*3.5/max(5, bx-left), -field.goal_width/2+.4, field.goal_width/2-.4)
        if vx < -2 and bx > left+3.5:
            predicted = by+vy*(left+3.5-bx)/vx
            if abs(predicted) < field.goal_width/2+1:
                keeper_y = clamp(predicted, -field.goal_width/2+.3, field.goal_width/2-.3)
        targets[0] = (left+3.5, keeper_y)
        actions = TeamAction()
        shot = None
        if bx > right-27 and any(obs.can_kick(p.id) for p in obs.my_players):
            shot = self.gap_shot(obs)
        for player in obs.my_players:
            target = targets[player.id]
            target = (clamp(target[0], left+1.1, right-1.1), clamp(target[1], -field.height/2+1.1, field.height/2-1.1))
            if protected and math.hypot(*target) < field.centre_circle_radius+2:
                target = (-field.centre_circle_radius-2, target[1])
            movement = self.move(player, target, field)
            if protected or not obs.can_kick(player.id):
                actions.move(player.id, movement)
                continue
            if player.id == 0 or bx < left+8:
                kick_direction = direction(28-vx, (10 if by >= 0 else -10)-vy)
                power = 1
            elif shot is not None and (shot[0] > -.8 or bx > right-9):
                _, kick_direction, power = shot
                movement = self.move(player, (bx+.4, by), field)
            else:
                # Carry into the mouth rather than firing from every distance.
                aim_y = clamp(by*.65, -field.goal_width/2+1, field.goal_width/2-1)
                ux, uy = direction(right-bx, aim_y-by)
                kick_direction = direction(ux*8.5-vx, uy*8.5-vy)
                power = min(1, math.hypot(ux*8.5-vx, uy*8.5-vy)/field.kick_impulse)
                movement = self.move(player, (bx+.4, by), field)
            actions.kick(player.id, kick_direction, power, movement=movement)
        return actions
