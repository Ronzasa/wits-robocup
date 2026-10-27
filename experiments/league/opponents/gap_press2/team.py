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


class GapPressTwo(TeamController):
    name = "Gap Press Three Guard Stress"
    version = "2"

    def reset(self, seed):
        self.previous_score = None
        self.restart_owner = None
        self.restart_until = -1
        self.previous_chaser = None

    def initial_formation(self, field):
        front = -field.centre_circle_radius-1
        return [(field.my_goal[0]+1.3, 0), (field.my_goal[0]+2, -4.8), (field.my_goal[0]+2, 4.8), (front, -3), (front, 3)]

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

    def forward_pass(self, player, receiver, obs):
        field = obs.field
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        tx = receiver.position[0]+receiver.velocity[0]*.25
        ty = receiver.position[1]+receiver.velocity[1]*.25
        dx, dy = tx-bx, ty-by
        distance = math.hypot(dx, dy)
        if not 4 < distance < 26 or tx < bx-5:
            return None
        ux, uy = direction(dx, dy)
        clearance = 100
        for q in obs.opponents:
            qx, qy = q.position[0]-bx, q.position[1]-by
            along = qx*ux+qy*uy
            if .3 < along < distance:
                flight = along/16
                gap = abs((qx+q.velocity[0]*min(.3, flight))*uy
                          -(qy+q.velocity[1]*min(.3, flight))*ux)
                clearance = min(clearance, gap-field.player_radius-field.ball_radius-min(2, flight*2))
        if clearance < .6:
            return None
        speed = min(20, max(9, distance*.5+5))
        dx, dy = ux*speed-vx, uy*speed-vy
        return direction(dx, dy), min(1, math.hypot(dx, dy)/field.kick_impulse)

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

        # Three guards remain goalside while two distinct attackers chase and
        # offer a close passing option. Slots are observation-independent roles.
        attackers = list(obs.my_players[3:])
        races = {p.id: self.intercept(p, obs) for p in attackers}
        attackers.sort(key=lambda p:races[p.id][0]-(.05 if p.id == self.previous_chaser else 0))
        chaser, support = attackers
        self.previous_chaser = chaser.id
        targets = {chaser.id: races[chaser.id][1:]}
        if bx > right-23:
            targets[support.id] = (max(right-9, bx-4), -7.2 if by > 0 else 7.2)
        else:
            targets[support.id] = (clamp(bx+5, -18, right-9),
                                   clamp(by+(-5 if by > 0 else 5), -12, 12))

        # A middle keeper tracks both the current side and an inbound crossing.
        # The near-side outer guard challenges a lone corner runner while the
        # other two preserve the mouth; no all-player retreat or chasing switch.
        keeper_y = clamp(by*.5, -3.2, 3.2) if bx < left+20 else 0
        keeper_x = left+1.3
        if vx < -1.5 and bx > keeper_x:
            flight = (keeper_x-bx)/vx
            if 0 < flight < 1.8:
                projected = by+vy*flight
                if abs(projected) < field.goal_width/2+1:
                    keeper_y = clamp(projected, -field.goal_width/2+.25, field.goal_width/2-.25)
        targets[0] = (keeper_x, keeper_y)
        targets[1] = (left+2, -4.8)
        targets[2] = (left+2, 4.8)
        if bx < left+14 and abs(by) > 2.8:
            near_guard = 1 if by < 0 else 2
            targets[near_guard] = (clamp(bx-.7, left+1.1, left+5),
                                   clamp(by, -field.goal_width/2-1.5, field.goal_width/2+1.5))
        # If the ball is nearly stationary and loose beside the line, the
        # closest guard may collect it rather than waiting for a shot.
        if bx < left+8 and abs(by) < field.goal_width/2+1 and math.hypot(vx, vy) < 5:
            collector = min(obs.my_players[:3], key=lambda p:math.hypot(p.position[0]-bx,p.position[1]-by))
            if math.hypot(collector.position[0]-bx,collector.position[1]-by) < 5:
                targets[collector.id] = (bx+.25, by)

        shot = None
        if bx > right-28 and any(obs.can_kick(p.id) for p in attackers):
            shot = self.gap_shot(obs)
        actions = TeamAction()
        for player in obs.my_players:
            target = targets[player.id]
            target = (clamp(target[0], left+1.05, right-1.05),
                      clamp(target[1], -field.height/2+1.1, field.height/2-1.1))
            if protected and math.hypot(*target) < field.centre_circle_radius+2:
                target = (-field.centre_circle_radius-2, target[1])
            movement = self.move(player, target, field)
            if protected or not obs.can_kick(player.id):
                actions.move(player.id, movement)
                continue
            if player.id < 3:
                # Emergency impulses favor reversal over a blind far-wide kick.
                kick_direction = direction(max(20, 24-vx), -vy)
                power = 1
            elif shot is not None and (shot[0] > -.75 or bx > right-9):
                _, kick_direction, power = shot
                movement = self.move(player, (bx+.4, by), field)
            else:
                receiver = support if player.id == chaser.id else chaser
                passed = self.forward_pass(player, receiver, obs)
                if passed is not None and (shot is None or shot[0] < .05):
                    kick_direction, power = passed
                else:
                    aim_y = clamp(by*.65, -field.goal_width/2+1, field.goal_width/2-1)
                    ux, uy = direction(right-bx, aim_y-by)
                    kick_direction = direction(ux*8.5-vx, uy*8.5-vy)
                    power = min(1, math.hypot(ux*8.5-vx, uy*8.5-vy)/field.kick_impulse)
                movement = self.move(player, (bx+.4, by), field)
            actions.kick(player.id, kick_direction, power, movement=movement)
        return actions
