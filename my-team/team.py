"""Pep Guardiola 2011 FC Barcelona: close support and purposeful possession.

All positions are in the SDK's canonical frame. No seed, opponent-name,
external file, private engine attribute, or service influences decisions.
"""
import math

from soccer import PlayerAction, TeamAction, TeamController


def _clip(value, low, high):
    return low if value < low else high if value > high else value


def _unit(x, y):
    length = math.hypot(x, y)
    if length < 1e-8:
        return 0.0, 0.0
    return x / length, y / length


class Guardiola2011(TeamController):
    name = "Pep Guardiola 2011 FC Barcelona"
    version = "3.2"
    DRIBBLE_SPEED = 8.0
    SHOOT_RANGE = 34.0
    PASSING = True
    PREDICTIVE_KEEPER = True
    SAFE_RECYCLE = True

    def __init__(self):
        self.reset(0)

    def reset(self, seed):
        # The supplied seed is deliberately unused.
        self._ready = False
        self._restart_until = -1
        self._restart_owner = None
        self._chaser = -1
        self._last_score = None

    def initial_formation(self, field):
        w, h = field.width, field.height
        circle = field.centre_circle_radius
        return [
            (field.my_goal[0] + 3.0, 0.0),
            (-0.26 * w, 0.0),
            (-0.15 * w, -0.26 * h),
            (-circle - 1.8, 0.0),
            (-0.15 * w, 0.26 * h),
        ]

    def _setup(self, field):
        self._dt = 1.0 / field.simulation_hz
        self._hz = field.simulation_hz
        self._speed = field.max_speed
        self._acc = field.acceleration * self._dt
        self._friction = field.ball_friction
        self._log_friction = math.log(self._friction)
        self._impulse = field.kick_impulse
        self._range = field.kick_range
        self._left = field.my_goal[0]
        self._right = field.opponent_goal[0]
        self._half_height = field.height * 0.5
        self._mouth = max(0.0, field.goal_width * 0.5 - 0.6)
        self._circle = field.centre_circle_radius
        self._contact = field.player_radius + field.ball_radius
        # Public course profile: player damping, wall restitution, ball cap.
        self._damping = 0.9
        self._wall = 0.75
        self._ball_cap = 30.0
        # Closed-form displacements for collision-free forecast samples.
        self._drag = tuple(self._friction ** tick for tick in range(81))
        self._roll = tuple(self._dt * (1.0 - drag) / (1.0 - self._friction)
                           for drag in self._drag)
        self._forecast_steps = tuple((tick * self._dt, self._roll[tick])
                                    for tick in (0, 3, 6, 10, 15, 22, 30, 42, 58, 80))
        self._ready = True

    def _target(self, x, y):
        return (_clip(x, self._left + 2.0, self._right - 2.0),
                _clip(y, -self._half_height + 2.0, self._half_height - 2.0))

    def _move(self, p, target, friends=()):
        dx, dy = target[0] - p[1], target[1] - p[2]
        gap = math.hypot(dx, dy)
        ux, uy = _unit(dx, dy)
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

    def _eta(self, p, x, y):
        dx, dy = x - p[1], y - p[2]
        d = math.hypot(dx, dy)
        if d < 1e-6:
            return 0.0
        speed_towards = (dx * p[3] + dy * p[4]) / d
        sideways = abs(dx * p[4] - dy * p[3]) / d
        startup = max(0.0, 1.0 - speed_towards / self._speed) * 0.30
        return max(0.0, d - self._range * 0.8) / self._speed + startup + sideways * 0.025

    def _crossing_ticks(self, position, velocity, bound):
        if abs(velocity) < 1e-9:
            return 81
        distance = bound - position if velocity > 0.0 else position + bound
        fraction = 1.0 - max(0.0, distance) * (1.0 - self._friction) / (abs(velocity) * self._dt)
        if fraction <= 0.0:
            return 81
        # Boundaries reflect only after crossing, not merely touching.
        return max(1, int(math.log(fraction) / self._log_friction) + 1)

    def _trajectory(self, bx, by, vx, vy):
        radius = 0.45
        xwall, ywall = self._right - radius, self._half_height - radius
        reach = self._forecast_steps[-1][1]
        if abs(bx + vx * reach) < xwall and abs(by + vy * reach) < ywall:
            return [(t, bx + vx * distance, by + vy * distance)
                    for t, distance in self._forecast_steps]
        # Advance analytically between the few wall contacts. Each contact
        # uses the same discrete overshoot/reflection as the stepped model.
        samples = [(0.0, bx, by)]
        elapsed = 0
        hit = min(self._crossing_ticks(bx, vx, xwall),
                  self._crossing_ticks(by, vy, ywall))
        for wanted in (3, 6, 10, 15, 22, 30, 42, 58, 80):
            while hit <= wanted:
                steps = hit - elapsed
                scale = self._roll[steps]
                bx += vx * scale
                by += vy * scale
                if by > ywall:
                    by = ywall * 2.0 - by
                    vy = -abs(vy) * self._wall
                elif by < -ywall:
                    by = -ywall * 2.0 - by
                    vy = abs(vy) * self._wall
                if abs(bx) > xwall:
                    if abs(by) <= self._mouth + 0.6:
                        samples.append((hit * self._dt, _clip(bx, -xwall, xwall), by))
                        return samples
                    if bx > xwall:
                        bx = xwall * 2.0 - bx
                        vx = -abs(vx) * self._wall
                    else:
                        bx = -xwall * 2.0 - bx
                        vx = abs(vx) * self._wall
                drag = self._drag[steps]
                vx *= drag
                vy *= drag
                elapsed = hit
                hit = elapsed + min(self._crossing_ticks(bx, vx, xwall),
                                    self._crossing_ticks(by, vy, ywall))
            scale = self._roll[wanted - elapsed]
            samples.append((wanted * self._dt, bx + vx * scale, by + vy * scale))
        return samples

    def _intercept(self, p, samples):
        best = None
        for t, x, y in samples:
            eta = self._eta(p, x, y)
            if eta <= t + 0.06:
                return max(t, eta), (x, y)
            cost = eta + t * 0.12
            if best is None or cost < best[0]:
                best = (cost, (x, y))
        return best

    def _flight(self, distance, speed):
        if speed <= 0.01:
            return 20.0
        fraction = 1.0 - distance * (1.0 - self._friction) / (speed * self._dt)
        if fraction <= 0.001:
            return 20.0
        return max(0.0, math.log(fraction) / self._log_friction * self._dt)

    def _kick_to_velocity(self, vx, vy, tx, ty):
        dx, dy = tx - vx, ty - vy
        length = math.hypot(dx, dy)
        if length < 0.03:
            return None
        power = min(1.0, length / self._impulse)
        return (dx / length, dy / length), power

    def _shot_velocity(self, bx, by, vx, vy, target_y):
        ux, uy = _unit(self._right - bx, target_y - by)
        along = vx * ux + vy * uy
        perpendicular_sq = max(0.0, vx * vx + vy * vy - along * along)
        if perpendicular_sq >= self._impulse * self._impulse:
            return None
        speed = min(self._ball_cap, along + math.sqrt(self._impulse ** 2 - perpendicular_sq))
        if speed < 9.0:
            return None
        return ux * speed, uy * speed, speed

    def _pass_velocity(self, bx, by, vx, vy, tx, ty):
        # A kick adds at most one impulse: evaluate the trajectory that is
        # actually achievable, including the ball's existing sideways speed.
        ux, uy = _unit(tx - bx, ty - by)
        along = vx * ux + vy * uy
        sideways_sq = max(0.0, vx * vx + vy * vy - along * along)
        if sideways_sq >= self._impulse * self._impulse:
            return None
        reach = math.sqrt(self._impulse * self._impulse - sideways_sq)
        speed = _clip(16.0, max(0.0, along - reach), min(self._ball_cap, along + reach))
        if speed < 9.0:
            return None
        return ux * speed, uy * speed, speed

    def _lane(self, bx, by, tx, ty, speed, opponents):
        dx, dy = tx - bx, ty - by
        length = math.hypot(dx, dy)
        if length < 0.1:
            return -10.0
        ux, uy = dx / length, dy / length
        room = 12.0
        for p in opponents:
            along = (p[1] - bx) * ux + (p[2] - by) * uy
            if along < -1.0 or along > length + 1.5:
                continue
            t = self._flight(max(0.0, along), speed)
            lead = min(0.65, t)
            x, y = p[1] + p[3] * lead, p[2] + p[4] * lead
            along = _clip((x - bx) * ux + (y - by) * uy, 0.0, length)
            lateral = math.hypot(x - bx - along * ux, y - by - along * uy)
            needed = self._contact + min(3.5, t * 1.2)
            room = min(room, lateral - needed)
        return room

    def _choose_kick(self, p, bx, by, vx, vy, friends, opponents):
        goal_distance = math.hypot(self._right - bx, by)
        best_shot = None
        for fraction in (-1.0, -0.75, -0.5, 0.0, 0.5, 0.75, 1.0):
            y = self._mouth * fraction
            velocity = self._shot_velocity(bx, by, vx, vy, y)
            if velocity is None:
                continue
            sx, sy, speed = velocity
            room = self._lane(bx, by, self._right, y, speed, opponents)
            score = room - abs(y - by) * 0.025
            if best_shot is None or score > best_shot[0]:
                best_shot = (score, room, sx, sy)
        if best_shot is not None:
            _, room, sx, sy = best_shot
            if (goal_distance < self.SHOOT_RANGE and room > 0.0) or (goal_distance < 15.0 and room > -2.0):
                return self._kick_to_velocity(vx, vy, sx, sy)

        pressure = min((math.hypot(o[1] - bx, o[2] - by) for o in opponents), default=100.0)
        best_pass = None
        if self.PASSING:
            for receiver in friends:
                if receiver[0] in (p[0], 0):
                    continue
                gain = receiver[1] - bx
                recycle = gain < 3.0 and p[0] != 0
                if recycle and (not self.SAFE_RECYCLE or pressure >= 3.5 or
                                gain < -8.0 or receiver[1] < self._left + 15.0):
                    continue
                tx, ty = receiver[1], receiver[2]
                velocity = None
                for _ in range(2):
                    velocity = self._pass_velocity(bx, by, vx, vy, tx, ty)
                    if velocity is None:
                        break
                    t = min(1.6, self._flight(math.hypot(tx - bx, ty - by), velocity[2]))
                    tx, ty = self._target(receiver[1] + receiver[3] * t * 0.8,
                                          receiver[2] + receiver[4] * t * 0.8)
                if velocity is None:
                    continue
                gap = math.hypot(tx - bx, ty - by)
                if not 5.0 < gap < 35.0:
                    continue
                velocity = self._pass_velocity(bx, by, vx, vy, tx, ty)
                if velocity is None:
                    continue
                room = self._lane(bx, by, tx, ty, velocity[2], opponents)
                if room < 0.5:
                    continue
                if recycle:
                    outlet_pressure = min((math.hypot(tx - o[1] - o[3] * 0.4,
                                                     ty - o[2] - o[4] * 0.4)
                                           for o in opponents), default=100.0)
                    # Recycling must release pressure, rather than merely
                    # inflate possession or invite danger beside our keeper.
                    if outlet_pressure < max(4.5, pressure + 1.0):
                        continue
                score = (tx - bx) * 0.05 + min(room, 6.0) * 0.16 - gap * 0.02
                if best_pass is None or score > best_pass[0]:
                    best_pass = (score, velocity[0], velocity[1])
            if best_pass is not None and (pressure < 4.5 or p[0] == 0):
                return self._kick_to_velocity(vx, vy, best_pass[1], best_pass[2])

        if p[0] == 0:
            # Clear laterally out of danger when no safe outlet is available.
            side = -1.0 if by > 0.0 else 1.0
            ux, uy = _unit(1.0, side * 0.6)
            return self._kick_to_velocity(vx, vy, ux * 22.0, uy * 22.0)

        best = None
        goal_ux, goal_uy = _unit(self._right - bx, -by)
        for dx, dy in ((goal_ux, goal_uy), (1.0, 0.0), (0.85, 0.53), (0.85, -0.53)):
            tx, ty = self._target(bx + dx * 5.0, by + dy * 5.0)
            clearance = min((math.hypot(tx - o[1] - o[3] * 0.2,
                                        ty - o[2] - o[4] * 0.2) for o in opponents), default=15.0)
            score = min(clearance, 10.0) + (tx - bx) * 0.45 - abs(ty) * 0.04
            if best is None or score > best[0]:
                best = (score, dx, dy)
        return self._kick_to_velocity(vx, vy, best[1] * self.DRIBBLE_SPEED,
                                       best[2] * self.DRIBBLE_SPEED)

    def act(self, obs):
        if not self._ready:
            self._setup(obs.field)
            self._restart_until = obs.tick + int(3.0 * self._hz)
            self._restart_owner = obs.ball.controlling_team
        # A changed public score identifies a goal without copying or
        # scanning event payloads in the decision loop.
        score = obs.score
        if self._last_score is not None and score != self._last_score:
            self._restart_until = obs.tick + int(3.0 * self._hz)
            self._restart_owner = 0 if score[1] > self._last_score[1] else 1
            self._chaser = -1
        self._last_score = score
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        if math.hypot(bx, by) > 0.7 or math.hypot(vx, vy) > 0.15:
            self._restart_until = -1
        protected = (obs.tick < self._restart_until and self._restart_owner == 1)
        friends = [(p.id, *p.position, *p.velocity) for p in obs.my_players]
        opponents = [(p.id, *p.position, *p.velocity) for p in obs.opponents]
        actions = TeamAction()
        if not friends:
            return actions
        keeper = friends[0]
        outfield = friends[1:] or friends
        samples = self._trajectory(bx, by, vx, vy)
        races = {p[0]: self._intercept(p, samples) for p in outfield}
        chaser = min(outfield, key=lambda p: races[p[0]][0])
        previous = next((p for p in outfield if p[0] == self._chaser), None)
        if previous is not None and races[previous[0]][0] < races[chaser[0]][0] + 0.12:
            chaser = previous
        self._chaser = chaser[0]
        enemy_eta = min((self._intercept(o, samples)[0] for o in opponents), default=100.0)
        attack = races[chaser[0]][0] <= enemy_eta + 0.12

        keeper_x = self._left + 2.2
        keeper_y = by * 2.2 / max(3.0, bx - self._left)
        if self.PREDICTIVE_KEEPER and vx < -1.0 and bx > keeper_x:
            time_to_line = (keeper_x - bx) / vx
            if 0.0 < time_to_line < 4.0:
                keeper_y = by + vy * time_to_line
        keeper_target = (keeper_x, _clip(keeper_y, -self._mouth, self._mouth))
        if bx < self._left + 10.0 and self._eta(keeper, bx, by) < races[chaser[0]][0] * 0.85:
            keeper_target = self._target(bx, by)

        targets = {keeper[0]: keeper_target, chaser[0]: self._target(*races[chaser[0]][1])}
        free = [p for p in outfield if p[0] != chaser[0]]
        if free:
            cover_target = self._target(min(28.0, bx - 2.0),
                                        _clip(by, -self._half_height + 2.0, self._half_height - 2.0))
            cover = min(free, key=lambda p: self._eta(p, *cover_target))
            targets[cover[0]] = cover_target
            free = [p for p in free if p[0] != cover[0]]
        if attack:
            spread = max(7.0, 15.0 - max(0.0, bx - 20.0) * 0.35)
            free.sort(key=lambda p: p[2])
            for index, p in enumerate(free):
                lane = 0.0 if len(free) == 1 else -spread + 2.0 * spread * index / (len(free) - 1)
                targets[p[0]] = self._target(bx + 12.0, by * 0.2 + lane)
        else:
            threats = sorted(opponents, key=lambda p: p[1] + abs(p[2]) * 0.2)
            for threat in threats:
                if not free:
                    break
                if math.hypot(threat[1] - bx, threat[2] - by) < 3.5:
                    continue
                ux, uy = _unit(self._left - threat[1], -threat[2])
                target = self._target(threat[1] + ux * 3.0, threat[2] + uy * 3.0)
                marker = min(free, key=lambda p: self._eta(p, *target))
                targets[marker[0]] = target
                free = [p for p in free if p[0] != marker[0]]
            for p in free:
                targets[p[0]] = self._target(bx - 9.0, p[2] * 0.5)

        available = [p for p in friends if obs.can_kick(p[0])]
        carrier = min(available, key=lambda p: math.hypot(p[1] - bx, p[2] - by)) if available else None
        for p in friends:
            target = targets.get(p[0], (p[1], p[2]))
            if protected and math.hypot(p[1], p[2]) < self._circle + 5.0:
                ux, uy = _unit(p[1], p[2])
                target = (ux * (self._circle + 3.0), uy * (self._circle + 3.0))
            movement = self._move(p, target, friends if p[0] != chaser[0] and p[0] != 0 else ())
            kick = None
            if carrier is not None and p[0] == carrier[0] and not protected:
                movement = self._move(p, (bx + 0.3, by))
                nx = p[3] * self._damping + movement[0] * self._acc
                ny = p[4] * self._damping + movement[1] * self._acc
                speed = math.hypot(nx, ny)
                if speed > self._speed:
                    nx *= self._speed / speed
                    ny *= self._speed / speed
                # The engine moves players before checking kick range.
                distance_next = math.hypot(p[1] + nx * self._dt - bx,
                                           p[2] + ny * self._dt - by)
                if distance_next < self._range - 0.18:
                    kick = self._choose_kick(p, bx, by, vx, vy, friends, opponents)
            if kick is None:
                actions.set(p[0], PlayerAction(movement=movement))
            else:
                actions.set(p[0], PlayerAction(movement=movement,
                                               kick_direction=kick[0],
                                               kick_power=kick[1]))
        return actions
