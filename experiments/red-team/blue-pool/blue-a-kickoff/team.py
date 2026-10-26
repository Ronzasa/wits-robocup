# Experimental Blue Team candidate. The validated TITAN is unchanged.
"""TITAN Adaptive Counter (cleaned version of team 12).

How the file is organised
  _Core              code shared by both policies: ball physics, pass and shot search,
                     receiving, keeper saves, marking (identical text used to be pasted twice).
  _FallbackPolicy    the normal team: build-up play, pressing, the lead-lock goal-line wall
                     (only when ahead) and the wall breaker.
  _SpecialistPolicy  "counter lab": plays against an opponent that has parked a wall of
                     players on its goal line (clearance counters, tie bait, siege shots).
  AdaptiveChampion   the controller that is handed in. It plays the fallback policy until
                     the opponent's goal-line wall has been seen for 6 ticks in a row and the
                     team is not in the middle of a pass, then switches to the specialist
                     for the rest of the match.

Uses the broad wall detector and stiff lead-protection wall from TITAN 1.2.
The trailing-wall branch has been removed: a deficit always keeps normal play.

Keeps TITAN's existing dribbling, passing, transitions and wall specialist.
Adds a budget for optional searches and rejects unsafe shot candidates earlier.
Imports only Python's standard library
and the official SDK. Submit this file alone.
"""
import math
from time import perf_counter
from soccer import PlayerAction, TeamAction, TeamController

def _clip(value, low, high):
    return low if value < low else high if value > high else value

def _unit(x, y):
    length = math.hypot(x, y)
    if length < 1e-08:
        return (0.0, 0.0)
    return (x / length, y / length)

# Shared by both policies.
class _Core:
    # Leave time for player actions and SDK validation after optional searches.
    SEARCH_BUDGET_SECONDS = 0.007
    _decision_deadline = math.inf
    HOLD_RECEPTION = False
    FIRST_TOUCH = False
    SHOT_CONTACT_TICKS = 3
    SHOT_MARGIN = -0.04
    OPTION_SWITCH_MARGIN = 0.15
    BANK_LAUNCH_BUDGET = 12
    COVER_SHAPE = True
    KEEPER_PRIORITY = True
    KEEPER_RECOVERY = True
    WALL_PASSING = True
    BANK_MARGIN = 0.12
    MARK_HANDOFF = True
    TRANSITION_SECONDS = 1.5
    TRANSITION_LEAD = 2.0
    TRANSITION_GAIN = 4.0
    TRANSITION_ROOM = 1.2
    TRANSITION_MARGIN = 0.06
    COUNTERPRESS_SECONDS = 1.0
    COUNTERPRESS_RACE_MARGIN = 0.1
    PLAYER_ROLES = {0: 'Oliver Kahn | goalkeeper', 1: 'Beckenbauer | libero', 2: 'Iniesta | pivot', 3: 'Messi | creator', 4: 'Ronaldo Nazario | striker'}
    DRIBBLE_SPEED = 8.0
    SHOOT_RANGE = 34.0
    PASSING = True
    PREDICTIVE_KEEPER = True
    SAFE_RECYCLE = True

    def __init__(self):
        self.reset(0)

    def initial_formation(self, field):
        w, h = (field.width, field.height)
        circle = field.centre_circle_radius
        return [(field.my_goal[0] + 3.0, 0.0), (-0.26 * w, 0.0), (-0.15 * w, -0.13 * h), (-0.15 * w, 0.2 * h), (-circle - 1.8, 0.0)]

    def _target(self, x, y):
        return (_clip(x, self._left + 2.0, self._right - 2.0), _clip(y, -self._half_height + 2.0, self._half_height - 2.0))

    def _search_expired(self):
        return perf_counter() >= self._decision_deadline

    def _move(self, p, target, friends=()):
        dx, dy = (target[0] - p[1], target[1] - p[2])
        gap = math.hypot(dx, dy)
        if gap < 1e-08:
            ux, uy = (0.0, 0.0)
        else:
            ux, uy = (dx / gap, dy / gap)
        for other in friends:
            if other[0] == p[0]:
                continue
            sx, sy = (p[1] - other[1], p[2] - other[2])
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
            return (ax / length, ay / length)
        return (ax, ay)

    def _eta(self, p, x, y):
        dx, dy = (x - p[1], y - p[2])
        d = math.hypot(dx, dy)
        if d < 1e-06:
            return 0.0
        speed_towards = (dx * p[3] + dy * p[4]) / d
        sideways = abs(dx * p[4] - dy * p[3]) / d
        startup = max(0.0, 1.0 - speed_towards / self._speed) * 0.3
        return max(0.0, d - self._eta_range) / self._speed + startup + sideways * 0.025

    def _crossing_ticks(self, position, velocity, bound):
        if abs(velocity) < 1e-09:
            return 81
        distance = bound - position if velocity > 0.0 else position + bound
        fraction = 1.0 - max(0.0, distance) * (1.0 - self._friction) / (abs(velocity) * self._dt)
        if fraction <= 0.0:
            return 81
        return max(1, int(math.log(fraction) / self._log_friction) + 1)

    def _trajectory(self, bx, by, vx, vy):
        radius = 0.45
        xwall, ywall = (self._right - radius, self._half_height - radius)
        reach = self._forecast_steps[-1][1]
        if abs(bx + vx * reach) < xwall and abs(by + vy * reach) < ywall:
            return [(t, bx + vx * distance, by + vy * distance) for t, distance in self._forecast_steps]
        samples = [(0.0, bx, by)]
        elapsed = 0
        hit = min(self._crossing_ticks(bx, vx, xwall), self._crossing_ticks(by, vy, ywall))
        for wanted in (2, 4, 6, 9, 12, 16, 20, 25, 31, 38, 47, 58, 70, 80):
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
                hit = elapsed + min(self._crossing_ticks(bx, vx, xwall), self._crossing_ticks(by, vy, ywall))
            scale = self._roll[wanted - elapsed]
            samples.append((wanted * self._dt, bx + vx * scale, by + vy * scale))
        return samples

    def _pass_path(self, launch, origin=None, until=4.0):
        x, y, vx, vy = launch
        samples = [] if origin is None else [(0.0, *origin)]
        motion = ([] if origin is None else [(vx, vy)]) if self.FIRST_TOUCH else None
        first = 0 if origin is None else 1
        xwall = self._right - self._ball_radius
        ywall = self._half_height - self._ball_radius
        for n in range(first, min(80, int(round(until * self._hz))) + 1):
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
                motion.append((vx, vy))
        self._last_pass_motion = (samples, motion) if motion is not None else None
        return samples

    def _pass_reachable(self, p, x, y, n, radius):
        dx, dy = (x - p[1], y - p[2])
        distance_sq = dx * dx + dy * dy
        if n == 0:
            return distance_sq <= radius * radius
        if n >= len(self._reach_table) or distance_sq > (self._speed * n * self._dt + radius) ** 2:
            return False
        coast, reach = self._reach_table[n]
        rx, ry = (dx - p[3] * coast, dy - p[4] * coast)
        gap_sq = rx * rx + ry * ry
        if gap_sq > (reach + radius) ** 2:
            return False
        gap = math.sqrt(gap_sq)
        scale = max(0.0, gap - radius + 1e-07) / max(gap * reach, 1e-12)
        ax, ay = (rx * scale, ry * scale)
        decay = self._damping ** n
        impulse = self._acc * (1.0 - decay) / (1.0 - self._damping)
        fx, fy = (p[3] * decay + ax * impulse, p[4] * decay + ay * impulse)
        inside = abs(p[1]) + abs(p[3]) * coast + abs(ax) * reach < self._right - 1.0 and abs(p[2]) + abs(p[4]) * coast + abs(ay) * reach < self._half_height - 1.0
        if inside and p[3] * p[3] + p[4] * p[4] <= self._speed * self._speed and (math.hypot(ax, ay) <= 1.0) and (math.hypot(fx, fy) <= self._speed):
            return True
        px, py, vx, vy = p[1:]
        tx, ty = self._target(x, y)
        for _ in range(n):
            ux, uy = (tx - px, ty - py)
            gap = math.hypot(ux, uy)
            desired = min(self._speed, gap * 5.0)
            factor = desired / gap if gap > 1e-08 else 0.0
            ax = (ux * factor - vx * self._damping) / self._acc
            ay = (uy * factor - vy * self._damping) / self._acc
            norm = math.hypot(ax, ay)
            if norm > 1.0:
                ax, ay = (ax / norm, ay / norm)
            vx, vy = (vx * self._damping + ax * self._acc, vy * self._damping + ay * self._acc)
            speed = math.hypot(vx, vy)
            if speed > self._speed:
                vx, vy = (vx * self._speed / speed, vy * self._speed / speed)
            px, py = (px + vx * self._dt, py + vy * self._dt)
            if abs(px) > self._right - 1.0 or abs(py) > self._half_height - 1.0:
                return False
        return math.hypot(x - px, y - py) <= radius

    def _pass_steps(self, path):
        if path is self._runtime_path:
            return self._runtime_steps
        steps = []
        previous = None
        for t, x, y in path:
            n = int(round(t * self._hz))
            pre = previous if previous is not None and abs(t - previous[0] - self._dt) < 1e-08 else None
            steps.append((t, n, x, y, pre))
            previous = (t, x, y)
        self._runtime_path = path
        self._runtime_steps = steps
        self._runtime_queries = {}
        return steps

    def _runtime_intercept(self, p, path, cooldown=0, after=0.0, until=4.0, steps=None):
        if steps is None:
            steps = self._pass_steps(path)
        if steps is not self._runtime_steps:
            return self._verified_intercept(p, path, cooldown, after, until, steps)
        key = (tuple(p), cooldown, after, until)
        cached = self._runtime_queries.get(key, False)
        if cached is not False:
            return cached
        answer = self._verified_intercept(p, path, cooldown, after, until, steps)
        if len(self._runtime_queries) >= 32:
            self._runtime_queries.clear()
        self._runtime_queries[key] = answer
        return answer

    def _verified_intercept(self, p, path, cooldown=0, after=0.0, until=4.0, steps=None):
        if steps is None:
            steps = self._pass_steps(path)
        body_radius = self._contact
        kick_radius = self._range
        for t, n, x, y, pre in steps:
            if t > until + 1e-09:
                break
            if t + 1e-09 < after:
                continue
            coast, reach = self._reach_table[n]
            ex, ey = (p[1] + p[3] * coast, p[2] + p[4] * coast)
            if pre is not None and cooldown <= n:
                dx, dy = (pre[1] - ex, pre[2] - ey)
                if dx * dx + dy * dy <= (reach + kick_radius) ** 2 and self._pass_reachable(p, pre[1], pre[2], n, kick_radius):
                    return (t, (pre[1], pre[2]))
            radius = body_radius
            dx, dy = (x - ex, y - ey)
            if dx * dx + dy * dy <= (reach + radius) ** 2 and self._pass_reachable(p, x, y, n, radius):
                return (t, (x, y))
        return None

    def _pass_race(self, receiver, path, opponents, margin=0.0, after=0.0, until=4.0, first_move=None):
        self._next_receive_aim = None
        steps = self._pass_steps(path)
        route = None
        route = self._receiver_route(receiver, path, opponents, after, until, first_move, steps)
        own = (route[0], route[1]) if route is not None else None
        if own is None:
            return None
        enemy = math.inf
        contest_until = min(until, own[0] + max(margin, 0.8))
        for q in opponents:
            race = self._runtime_intercept(q, path, self._enemy_cooldowns.get(q[0], 0), until=contest_until, steps=steps)
            if race is not None:
                if race[0] <= own[0] + 1e-09 or race[0] - own[0] < margin - 1e-09:
                    return None
                enemy = min(enemy, race[0])
        if enemy <= own[0] + 1e-09 or enemy - own[0] < margin - 1e-09:
            return None
        self._next_receive_aim = route[2] if route is not None else own[1]
        return (own, enemy)

    def _receiver_rollout(self, p, path, aim, cooldown=0, after=0.0, until=4.0, first_move=None, steps=None):
        if not path or abs(path[0][0]) > 1e-08:
            return None
        aim = self._target(*aim)
        px, py, vx, vy = p[1:]
        dt, hz = (self._dt, self._hz)
        damping, acc, speed_cap = (self._damping, self._acc, self._speed)
        kick_range, contact = (self._range, self._contact)
        xbound, ybound = (self._right - 1.0, self._half_height - 1.0)
        hypot = math.hypot
        previous = path[0]
        if after <= 0.0 and hypot(px - previous[1], py - previous[2]) <= contact:
            return (0.0, (previous[1], previous[2]), aim, p, 'body', 0, 0)
        for index in range(1, len(path)):
            t, x, y = path[index]
            n = steps[index][1] if steps is not None else int(round(t * hz))
            if t > until + 1e-09:
                break
            if abs(t - previous[0] - dt) > 1e-08:
                return None
            prex, prey = previous[1:]
            ready = cooldown <= n - 1 and hypot(px - prex, py - prey) <= kick_range and (not (after > 0.0 and n == 1))
            if index == 1 and first_move is not None:
                ready = False
                ax, ay = first_move
            else:
                tx, ty = (prex + 0.3, prey) if ready else aim
                dx, dy = (tx - px, ty - py)
                gap = hypot(dx, dy)
                if gap < 1e-08:
                    ux, uy = (0.0, 0.0)
                else:
                    ux, uy = (dx / gap, dy / gap)
                length = hypot(ux, uy)
                if length < 1e-08:
                    ux, uy = (0.0, 0.0)
                else:
                    ux, uy = (ux / length, uy / length)
                desired = min(speed_cap, gap * 5.0)
                ax = (ux * desired - vx * damping) / acc
                ay = (uy * desired - vy * damping) / acc
                length = hypot(ax, ay)
                if length > 1.0:
                    ax, ay = (ax / length, ay / length)
            vx = vx * damping + ax * acc
            vy = vy * damping + ay * acc
            speed = hypot(vx, vy)
            if speed > speed_cap:
                vx, vy = (vx * speed_cap / speed, vy * speed_cap / speed)
            px, py = (px + vx * dt, py + vy * dt)
            if abs(px) > xbound or abs(py) > ybound:
                return None
            kick = ready and hypot(px - prex, py - prey) < kick_range - 0.18
            body = hypot(px - x, py - y) <= contact
            if kick or body:
                if t + 1e-09 < after:
                    return None
                point = (prex, prey) if kick else (x, y)
                return (t, point, aim, (p[0], px, py, vx, vy), 'kick' if kick else 'body', index, n)
            previous = (t, x, y)
        return None

    def _first_touch_safe(self, route, path, opponents, cooldown):
        if route[4] == 'kick':
            return True
        motion = self._last_pass_motion
        if motion is None or motion[0] is not path:
            return False
        t, (x, y), aim, p, kind, index, n = route
        vx, vy = motion[1][index]
        dx, dy = (x - p[1], y - p[2])
        gap = math.hypot(dx, dy)
        if gap < 1e-08:
            return False
        nx, ny = (dx / gap, dy / gap)
        x, y = (p[1] + nx * self._contact, p[2] + ny * self._contact)
        closing = (vx - p[3]) * nx + (vy - p[4]) * ny
        if closing < 0.0:
            vx -= 1.25 * closing * nx
            vy -= 1.25 * closing * ny
        if math.hypot(vx - p[3], vy - p[4]) <= 8.0:
            return True
        if cooldown > n:
            return False
        move = self._move(p, (x + 0.3, y))
        pvx = p[3] * self._damping + move[0] * self._acc
        pvy = p[4] * self._damping + move[1] * self._acc
        speed = math.hypot(pvx, pvy)
        if speed > self._speed:
            pvx, pvy = (pvx * self._speed / speed, pvy * self._speed / speed)
        if math.hypot(p[1] + pvx * self._dt - x, p[2] + pvy * self._dt - y) >= self._range - 0.18:
            return False
        for q in opponents:
            radius = self._range if self._enemy_cooldowns.get(q[0], 0) <= n + 1 else self._contact
            if self._pass_reachable(q, x, y, n + 1, radius):
                return False
        return True

    def _receiver_route(self, receiver, path, opponents, after, until, first_move=None, steps=None):
        cooldown = self._friend_cooldowns.get(receiver[0], 0)
        if steps is None:
            steps = self._pass_steps(path)
        theory = self._runtime_intercept(receiver, path, cooldown, after, until, steps)
        if theory is None:
            return None
        preferred = self._receive_aim if self.HOLD_RECEPTION and after <= 0.0 else None
        if preferred is not None and preferred[0] == receiver[0]:
            route = self._receiver_rollout(receiver, path, preferred[1], cooldown, after, until, first_move, steps)
            if route is not None and (not self.FIRST_TOUCH or self._first_touch_safe(route, path, opponents, cooldown)):
                return route
        ordinary = self._receiver_rollout(receiver, path, theory[1], cooldown, after, until, first_move, steps)
        if ordinary is not None and (not self.FIRST_TOUCH or self._first_touch_safe(ordinary, path, opponents, cooldown)):
            return ordinary
        aims = [theory[1]]
        for delay in (0.1, 0.25, 0.45):
            sample = next((s for s in path if s[0] + 1e-09 >= theory[0] + delay and s[0] <= until + 1e-09), None)
            if sample is not None:
                aim = (sample[1], sample[2])
                if aim not in aims:
                    aims.append(aim)
        best = None
        for aim in aims[1:]:
            route = self._receiver_rollout(receiver, path, aim, cooldown, after, until, first_move, steps)
            if route is None or (self.FIRST_TOUCH and (not self._first_touch_safe(route, path, opponents, cooldown))):
                continue
            if best is None or route[0] < best[0]:
                best = route
        return best

    def _closest_eta(self, players, target):
        best = None
        best_eta = None
        x, y = target
        for p in players:
            eta = self._eta(p, x, y)
            if best is None or eta < best_eta:
                best, best_eta = (p, eta)
        return best

    def _role_closest_eta(self, players, target, cover=False):
        best = None
        best_eta = None
        x, y = target
        for p in players:
            eta = self._eta(p, x, y)
            if p[0] == 1:
                eta -= 0.09 if cover else 0.045
            elif p[0] == 2:
                eta -= 0.045 if cover else 0.025
            if best is None or eta < best_eta:
                best, best_eta = (p, eta)
        return best

    def _role_support(self, p, bx, by, lane):
        if p[0] == 1:
            return self._target(bx + 6.0, by * 0.2 + lane * 0.5)
        if p[0] == 2:
            return self._target(bx + 7.0, by * 0.2 + lane * 0.7)
        if p[0] == 3:
            return self._target(bx + 10.0, by * 0.2 + lane * 0.8)
        if p[0] == 4:
            return self._target(bx + 15.0, by * 0.2 + lane * 0.3)
        return self._target(bx + 12.0, by * 0.2 + lane)

    def _flight(self, distance, speed):
        if speed <= 0.01:
            return 20.0
        fraction = 1.0 - distance * (1.0 - self._friction) / (speed * self._dt)
        if fraction <= 0.001:
            return 20.0
        return max(0.0, math.log(fraction) / self._log_friction * self._dt)

    def _kick_to_velocity(self, vx, vy, tx, ty):
        dx, dy = (tx - vx, ty - vy)
        length = math.hypot(dx, dy)
        if length < 0.03:
            return None
        power = min(1.0, length / self._impulse)
        return ((dx / length, dy / length), power)

    def _shot_velocity(self, bx, by, vx, vy, target_y):
        ux, uy = _unit(self._right - bx, target_y - by)
        along = vx * ux + vy * uy
        perpendicular_sq = max(0.0, vx * vx + vy * vy - along * along)
        if perpendicular_sq >= self._impulse * self._impulse:
            return None
        speed = min(self._ball_cap, along + math.sqrt(self._impulse ** 2 - perpendicular_sq))
        if speed < 9.0:
            return None
        return (ux * speed, uy * speed, speed)

    def _pass_velocity(self, bx, by, vx, vy, tx, ty):
        ux, uy = _unit(tx - bx, ty - by)
        along = vx * ux + vy * uy
        sideways_sq = max(0.0, vx * vx + vy * vy - along * along)
        if sideways_sq >= self._impulse * self._impulse:
            return None
        reach = math.sqrt(self._impulse * self._impulse - sideways_sq)
        speed = _clip(24.0, max(0.0, along - reach), min(self._ball_cap, along + reach))
        if speed < 9.0:
            return None
        return (ux * speed, uy * speed, speed)

    def _lane(self, bx, by, tx, ty, speed, opponents):
        dx, dy = (tx - bx, ty - by)
        length = math.hypot(dx, dy)
        if length < 0.1:
            return -10.0
        ux, uy = (dx / length, dy / length)
        room = 12.0
        for p in opponents:
            along = (p[1] - bx) * ux + (p[2] - by) * uy
            if along < -1.0 or along > length + 1.5:
                continue
            t = self._flight(max(0.0, along), speed)
            lead = min(0.65, t)
            x, y = (p[1] + p[3] * lead, p[2] + p[4] * lead)
            along = _clip((x - bx) * ux + (y - by) * uy, 0.0, length)
            lateral = math.hypot(x - bx - along * ux, y - by - along * uy)
            needed = self._contact + min(3.5, t * 1.2)
            room = min(room, lateral - needed)
        return room

    def _transition_observe(self, obs, protected, friends, opponents, race_info=None):
        score = tuple(obs.score)
        reset = self._transition_score is not None and score != self._transition_score
        reset = reset or (self._transition_tick is not None and obs.tick <= self._transition_tick)
        self._transition_score = score
        self._transition_tick = obs.tick
        last_touch = obs.ball.last_touch
        if reset or protected:
            self._transition_owner = None
            self._transition_until = -1
            self._transition_last_touch = last_touch
            self._transition_holder = obs.ball.controlling_player
            self._transition_active = False
            return
        ours = {p[0] for p in friends}
        theirs = {p[0] for p in opponents}
        holder = obs.ball.controlling_player
        changed_touch = last_touch != self._transition_last_touch and (last_touch in ours or last_touch in theirs)
        changed_holder = holder != self._transition_holder and (holder in ours or holder in theirs)
        direct = last_touch if changed_touch else holder if changed_holder else None
        self._transition_last_touch = last_touch
        self._transition_holder = holder
        owner = 0 if direct in ours else 1 if direct in theirs else None
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        if race_info is None:
            samples = self._trajectory(bx, by, vx, vy)
            our_race = min((self._intercept(p, samples)[0] for p in friends if p[0] != 0), default=100.0)
            their_race = min((self._intercept(p, samples)[0] for p in opponents), default=100.0)
        else:
            our_race, their_race = race_info
        pressure = min((math.hypot(p[1] - bx, p[2] - by) for p in opponents), default=100.0)
        favorable = bx > self._left + 12.0 and pressure >= 3.2 and (our_race + 0.1 < their_race)
        if owner is not None:
            if owner == 0 and self._transition_owner == 1:
                self._transition_until = obs.tick + int(self.TRANSITION_SECONDS * self._hz) if favorable else -1
            elif owner == 1:
                self._transition_until = -1
            self._transition_owner = owner
        self._transition_active = favorable and self._transition_owner == 0 and (obs.tick <= self._transition_until)

    def _transition_support(self, bx, by, friends, opponents, chaser_id, targets):
        if not self._transition_active:
            return
        available = [p for p in friends if p[0] not in (0, chaser_id)]
        if len(available) < 2:
            return
        cover = min(available, key=lambda p: targets[p[0]][0])
        runners = [p for p in available if p[0] != cover[0]]
        runner = max(runners, key=lambda p: p[1] + (2.0 if p[0] == 4 else 0.0))
        tx, ty = targets[runner[0]]
        nearest = min(opponents, key=lambda p: math.hypot(p[1] - tx, p[2] - ty), default=None)
        side = (1.0 if ty >= by else -1.0) if nearest is None else 1.0 if ty >= nearest[2] else -1.0
        targets[runner[0]] = self._target(tx + 3.0, ty + side * 4.0)

    def _transition_release(self, p, bx, by, vx, vy, friends, opponents):
        if not self._transition_active:
            return None
        movement = self._move(p, (bx + 0.3, by))
        best = None
        for receiver in friends:
            if receiver[0] in (0, p[0]):
                continue
            for extra in (0.0, self.TRANSITION_LEAD):
                tx, ty = (receiver[1] + extra, receiver[2])
                for _ in range(2):
                    velocity = self._pass_velocity(bx, by, vx, vy, tx, ty)
                    if velocity is None:
                        break
                    flight = self._flight(math.hypot(tx - bx, ty - by), velocity[2])
                    lead = min(0.9, flight)
                    tx, ty = self._target(receiver[1] + receiver[3] * lead * 0.8 + extra, receiver[2] + receiver[4] * lead * 0.8)
                if velocity is None:
                    continue
                gain, gap = (tx - bx, math.hypot(tx - bx, ty - by))
                if gain < self.TRANSITION_GAIN or not 5.0 < gap < 31.0:
                    continue
                velocity = self._pass_velocity(bx, by, vx, vy, tx, ty)
                if velocity is None:
                    continue
                room = self._lane(bx, by, tx, ty, velocity[2], opponents)
                if room < self.TRANSITION_ROOM:
                    continue
                kick = self._kick_to_velocity(vx, vy, velocity[0], velocity[1])
                if kick is None:
                    continue
                sx, sy = self._requested_velocity(vx, vy, kick)
                launch = self._carrier_contact(p, bx, by, sx, sy, movement)
                if launch is None or launch[2] < 5.0 or math.hypot(launch[2], launch[3]) < 10.5:
                    continue
                trajectory = self._pass_path(launch, (bx, by), 1.7)
                race = self._pass_race(receiver, trajectory, opponents, self.TRANSITION_MARGIN, self._dt, 1.7)
                if race is None:
                    continue
                (arrival, contact), enemy_arrival = race
                if contact[0] < bx + self.TRANSITION_GAIN:
                    continue
                receiver_room = min((math.hypot(contact[0] - o[1] - o[3] * min(arrival, 0.5), contact[1] - o[2] - o[4] * min(arrival, 0.5)) for o in opponents), default=100.0)
                if receiver_room < 3.0:
                    continue
                score = (contact[0] - bx) * 0.08 + min(room, 6.0) * 0.15 - arrival * 0.2
                score += min(receiver_room, 8.0) * 0.04 - abs(contact[1]) * 0.006
                if best is None or score > best[0]:
                    best = (score, kick, receiver[0], contact)
        if best is None:
            return None
        self._pass_plan = (best[2], *best[3])
        return best[1]

    def _original_choose_kick(self, p, bx, by, vx, vy, friends, opponents):
        release = self._escape_release(p, bx, by, vx, vy, opponents)
        if release is not None:
            return release
        goal_distance = math.hypot(self._right - bx, by)
        finisher = p[0] in (3, 4)
        best_shot = None
        for fraction in (-1.0, -0.75, -0.5, 0.0, 0.5, 0.75, 1.0):
            y = self._mouth * fraction
            velocity = self._shot_velocity(bx, by, vx, vy, y)
            if velocity is None:
                continue
            sx, sy, speed = velocity
            room = self._lane(bx, by, self._right, y, speed, opponents)
            if finisher:
                distance = math.hypot(self._right - bx, y - by)
                flight = self._flight(distance, speed)
                if flight >= 20.0:
                    continue
                ordinary = goal_distance < self.SHOOT_RANGE and room > 0.0 or (goal_distance < 15.0 and room > -2.0)
                extended = goal_distance < 38.0 and speed >= 24.0 and (flight <= 2.0) and (room > 1.75) and (speed * self._friction ** (flight * self._hz) >= 12.0)
                if not (ordinary or extended):
                    continue
            score = room - abs(y - by) * 0.025
            if best_shot is None or score > best_shot[0]:
                best_shot = (score, room, sx, sy)
        if best_shot is not None:
            _, room, sx, sy = best_shot
            if finisher or (goal_distance < self.SHOOT_RANGE and room > 0.0) or (goal_distance < 15.0 and room > -2.0):
                return self._kick_to_velocity(vx, vy, sx, sy)
        transition = self._transition_release(p, bx, by, vx, vy, friends, opponents)
        if transition is not None:
            return transition
        pressure = min((math.hypot(o[1] - bx, o[2] - by) for o in opponents), default=100.0)
        best_pass = None
        best_break = None
        if self.PASSING:
            for receiver in friends:
                if receiver[0] in (p[0], 0):
                    continue
                gain = receiver[1] - bx
                recycle = gain < 3.0 and p[0] != 0
                if recycle and (not self.SAFE_RECYCLE or pressure >= 3.5 or gain < -8.0 or (receiver[1] < self._left + 15.0)):
                    continue
                tx, ty = (receiver[1], receiver[2])
                velocity = None
                for _ in range(2):
                    velocity = self._pass_velocity(bx, by, vx, vy, tx, ty)
                    if velocity is None:
                        break
                    t = min(1.6, self._flight(math.hypot(tx - bx, ty - by), velocity[2]))
                    tx, ty = self._target(receiver[1] + receiver[3] * t * 0.8, receiver[2] + receiver[4] * t * 0.8)
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
                    outlet_pressure = min((math.hypot(tx - o[1] - o[3] * 0.4, ty - o[2] - o[4] * 0.4) for o in opponents), default=100.0)
                    if outlet_pressure < max(4.5, pressure + 1.0):
                        continue
                receiver_space = min((math.hypot(tx - o[1] - o[3] * 0.4, ty - o[2] - o[4] * 0.4) for o in opponents), default=100.0)
                if p[0] == 1:
                    score = (tx - bx) * 0.045 + min(room, 6.0) * 0.2 - gap * 0.023
                elif p[0] == 2:
                    score = (tx - bx) * 0.05 + min(room, 6.0) * 0.2 - gap * 0.024
                elif p[0] == 3:
                    score = (tx - bx) * 0.065 + min(room, 6.0) * 0.16 - gap * 0.02
                    if receiver[0] == 4 and gain >= 6.0 and (abs(ty) < self._half_height * 0.5):
                        score += 0.1
                elif p[0] == 4:
                    score = (tx - bx) * 0.07 + min(room, 6.0) * 0.16 - gap * 0.02
                else:
                    score = (tx - bx) * 0.05 + min(room, 6.0) * 0.16 - gap * 0.02
                candidate = (score, velocity[0], velocity[1], receiver[0], tx, ty)
                if best_pass is None or score > best_pass[0]:
                    best_pass = candidate
                if gain >= 8.0 and gap >= 9.0 and (room >= 1.75) and (receiver_space >= 4.5) and (bx < 32.0) and (best_break is None or score > best_break[0]):
                    best_break = candidate
            chosen = best_pass if pressure < 4.5 or p[0] == 0 else best_break
            if chosen is not None:
                if p[0] == 4 and bx > 5.0 and (goal_distance > 15.0) and (abs(by) < self._half_height * 0.5) and (pressure >= 6.5):
                    cx, cy, tx, ty, clearance = self._carry_velocity(p, bx, by, pressure, opponents)
                    if tx - bx >= 3.5 and clearance >= 5.0 and (self._lane(bx, by, tx, ty, math.hypot(cx, cy), opponents) > 1.0):
                        return self._kick_to_velocity(vx, vy, cx, cy)
                self._pass_plan = (chosen[3], chosen[4], chosen[5])
                return self._kick_to_velocity(vx, vy, chosen[1], chosen[2])
        if p[0] == 0:
            side = -1.0 if by > 0.0 else 1.0
            ux, uy = _unit(1.0, side * 0.6)
            return self._kick_to_velocity(vx, vy, ux * 22.0, uy * 22.0)
        cx, cy, _, _, _ = self._carry_velocity(p, bx, by, pressure, opponents)
        return self._kick_to_velocity(vx, vy, cx, cy)

    def _carry_velocity(self, p, bx, by, pressure, opponents):
        close_control = p[0] == 3 and pressure < 4.5
        lookahead = 3.5 if close_control else 5.0
        touch_speed = min(self.DRIBBLE_SPEED, 7.0) if close_control else self.DRIBBLE_SPEED
        forward_weight = 0.7 if p[0] == 4 else 0.45
        centre_weight = 0.06 if p[0] in (3, 4) else 0.04
        best = None
        goal_ux, goal_uy = _unit(self._right - bx, -by)
        for dx, dy in ((goal_ux, goal_uy), (1.0, 0.0), (0.85, 0.53), (0.85, -0.53)):
            tx, ty = self._target(bx + dx * lookahead, by + dy * lookahead)
            clearance = min((math.hypot(tx - o[1] - o[3] * 0.2, ty - o[2] - o[4] * 0.2) for o in opponents), default=15.0)
            score = min(clearance, 10.0) + (tx - bx) * forward_weight - abs(ty) * centre_weight
            if best is None or score > best[0]:
                best = (score, dx, dy, tx, ty, clearance)
        return (best[1] * touch_speed, best[2] * touch_speed, best[3], best[4], best[5])

    def _requested_velocity(self, vx, vy, kick):
        direction, power = kick
        sx = vx + direction[0] * power * self._impulse
        sy = vy + direction[1] * power * self._impulse
        speed = math.hypot(sx, sy)
        if speed > self._ball_cap:
            sx *= self._ball_cap / speed
            sy *= self._ball_cap / speed
        return (sx, sy)

    def _carrier_contact(self, p, bx, by, sx, sy, movement):
        pvx = p[3] * self._damping + movement[0] * self._acc
        pvy = p[4] * self._damping + movement[1] * self._acc
        speed = math.hypot(pvx, pvy)
        if speed > self._speed:
            pvx *= self._speed / speed
            pvy *= self._speed / speed
        px, py = (p[1] + pvx * self._dt, p[2] + pvy * self._dt)
        if math.hypot(px - bx, py - by) >= self._range - 0.18:
            return None
        x, y = (bx + sx * self._dt, by + sy * self._dt)
        sx *= self._friction
        sy *= self._friction
        rx, ry = (x - px, y - py)
        gap = math.hypot(rx, ry)
        if 1e-08 < gap < self._contact:
            nx, ny = (rx / gap, ry / gap)
            x, y = (px + nx * self._contact, py + ny * self._contact)
            closing = (sx - pvx) * nx + (sy - pvy) * ny
            if closing < 0.0:
                impulse = -1.25 * closing
                sx += impulse * nx
                sy += impulse * ny
        return (x, y, sx, sy)

    def _legacy_choose_kick(self, p, bx, by, vx, vy, friends, opponents):
        self._touch_movement = None
        kick = self._original_choose_kick(p, bx, by, vx, vy, friends, opponents)
        if kick is None or bx >= 0.0 or bx <= self._left + 3.0 or (abs(by) >= self._half_height - 3.0):
            return kick
        sx, sy = self._requested_velocity(vx, vy, kick)
        if sx <= 2.0:
            return kick
        movement = self._move(p, (bx + 0.3, by))
        original = self._carrier_contact(p, bx, by, sx, sy, movement)
        if original is None or original[2] >= -2.0:
            return kick
        brake_x = -p[3] * self._damping / self._acc
        brake_y = -p[4] * self._damping / self._acc
        brake_length = math.hypot(brake_x, brake_y)
        if brake_length > 1.0:
            brake_x /= brake_length
            brake_y /= brake_length
        away = _unit(p[1] - bx, p[2] - by)
        for alternative in ((brake_x, brake_y), away):
            outcome = self._carrier_contact(p, bx, by, sx, sy, alternative)
            if outcome is not None and outcome[2] >= -2.0:
                self._touch_movement = alternative
                return kick
        for degrees in (30.0, -30.0, 60.0, -60.0):
            angle = math.radians(degrees)
            cosine, sine = (math.cos(angle), math.sin(angle))
            tx, ty = (sx * cosine - sy * sine, sx * sine + sy * cosine)
            alternative = self._kick_to_velocity(vx, vy, tx, ty)
            if alternative is None:
                continue
            ax, ay = self._requested_velocity(vx, vy, alternative)
            outcome = self._carrier_contact(p, bx, by, ax, ay, movement)
            if ax > 2.0 and outcome is not None and (outcome[2] >= -2.0):
                return alternative
        return kick

    def _escape_release(self, p, bx, by, vx, vy, opponents):
        if p[0] == 0 or bx > 2.0:
            return None
        pressure = min((math.hypot(o[1] - bx, o[2] - by) for o in opponents), default=100.0)
        if pressure >= 4.0:
            return None
        best = None
        for width in (-16.0, -8.0, 0.0, 8.0, 16.0):
            tx, ty = self._target(bx + 28.0, by * 0.3 + width)
            ux, uy = _unit(tx - bx, ty - by)
            along = vx * ux + vy * uy
            side = max(0.0, vx * vx + vy * vy - along * along)
            if side >= self._impulse ** 2:
                continue
            speed = min(28.0, along + math.sqrt(self._impulse ** 2 - side))
            if speed < 14.0:
                continue
            room = self._lane(bx, by, tx, ty, speed, opponents)
            score = room - abs(ty) * 0.025
            if best is None or score > best[0]:
                best = (score, self._kick_to_velocity(vx, vy, ux * speed, uy * speed))
        return None if best is None else best[1]

    def _endpoint_controlled_touch(self, p, bx, by, vx, vy, opponents):
        base_angle = math.atan2(-by, self._right - bx)
        original_distance = math.hypot(self._right - bx, by)
        best = None
        for angle_offset in (0.0, -0.45, 0.45, -0.9, 0.9, -1.35, 1.35):
            angle = base_angle + angle_offset
            ux, uy = (math.cos(angle), math.sin(angle))
            for speed in (6.0, 9.0):
                kick = self._kick_to_velocity(vx, vy, ux * speed, uy * speed)
                if kick is None:
                    continue
                sx, sy = self._requested_velocity(vx, vy, kick)
                movement = self._move(p, self._target(bx + ux * 3.0, by + uy * 3.0))
                contact = self._carrier_contact(p, bx, by, sx, sy, movement)
                if contact is None:
                    continue
                x, y, rx, ry = contact
                horizon = 0.3
                drag = self._friction ** (horizon * self._hz)
                scale = self._dt * (1.0 - drag) / (1.0 - self._friction)
                tx, ty = (x + rx * scale, y + ry * scale)
                if abs(ty) > self._half_height - 1.5 or tx < self._left + 3.0:
                    continue
                own_eta = self._eta(p, tx, ty)
                enemy_eta = min((self._eta(o, tx, ty) for o in opponents), default=10.0)
                clearance = min((math.hypot(tx - o[1] - o[3] * 0.22, ty - o[2] - o[4] * 0.22) for o in opponents), default=15.0)
                progress = original_distance - math.hypot(self._right - tx, ty)
                retain = _clip(enemy_eta - own_eta, -1.0, 1.0)
                score = progress * 0.85 + min(clearance, 8.0) * 0.45 + retain * 3.5 - max(0.0, own_eta - 0.5) * 4.0
                if rx < -2.0 and bx < 0.0:
                    score -= 5.0
                if best is None or score > best[0]:
                    best = (score, kick, movement)
        return best

    def _legacy_policy_kick(self, p, bx, by, vx, vy, friends, opponents):
        self._bank_plan = None
        self._pass_plan = None
        kick = self._legacy_choose_kick(p, bx, by, vx, vy, friends, opponents)
        if kick is None:
            return kick
        sx, sy = self._requested_velocity(vx, vy, kick)
        is_shot = bx > self._right - self.SHOOT_RANGE - 4.0 and sx > 1.0 and (abs(by + sy * (self._right - bx) / sx) <= self._mouth + 0.2)
        direct_safe = False
        if self._pass_plan is not None:
            recipient = next((q for q in friends if q[0] == self._pass_plan[0]), None)
            move = self._touch_movement or self._move(p, (bx + 0.3, by))
            launch = self._carrier_contact(p, bx, by, sx, sy, move)
            if recipient is not None and launch is not None:
                path = self._pass_path(launch, (bx, by))
                direct_safe = self._pass_race(recipient, path, opponents, 0.12, self._dt) is not None
        if self.WALL_PASSING and (not direct_safe) and (not is_shot):
            bank = self._bank_release(p, bx, by, vx, vy, friends, opponents)
            if bank is not None:
                self._touch_movement = bank[2]
                self._pass_plan = bank[3]
                self._bank_plan = bank[3]
                return bank[1]
        if self._pass_plan is not None and (not direct_safe):
            self._pass_plan = None
            if p[0] == 0:
                side = -1.0 if by > 0.0 else 1.0
                ux, uy = _unit(1.0, side * 0.6)
                return self._kick_to_velocity(vx, vy, ux * 22.0, uy * 22.0)
            controlled = self._controlled_touch(p, bx, by, vx, vy, opponents)
            if controlled is not None:
                self._touch_movement = controlled[2]
                return controlled[1]
            pressure = min((math.hypot(q[1] - bx, q[2] - by) for q in opponents), default=100.0)
            cx, cy, _, _, _ = self._carry_velocity(p, bx, by, pressure, opponents)
            return self._kick_to_velocity(vx, vy, cx, cy)
        if p[0] == 0:
            return kick
        if math.hypot(sx, sy) > 10.5:
            return kick
        planned = self._controlled_touch(p, bx, by, vx, vy, opponents)
        if planned is not None:
            self._touch_movement = planned[2]
            return planned[1]
        return kick

    def _controlled_touch(self, p, bx, by, vx, vy, opponents):
        original = self._endpoint_controlled_touch(p, bx, by, vx, vy, opponents)
        pressure = min((math.hypot(q[1] - bx, q[2] - by) for q in opponents), default=100.0)
        if original is None or pressure >= 5.5:
            return original
        original_path = self._touch_path(p, bx, by, vx, vy, original[1], original[2], opponents)
        if original_path is not None and original_path[1] >= 0.1:
            return original
        best = None
        if original_path is not None:
            best = (original_path[0], original[1], original[2], original_path[1])
        base_angle = math.atan2(-by, self._right - bx)
        for offset in (0.0, -0.6, 0.6, -1.2, 1.2, -1.8, 1.8):
            angle = base_angle + offset
            ux, uy = (math.cos(angle), math.sin(angle))
            for speed in (5.0, 8.0):
                kick = self._kick_to_velocity(vx, vy, ux * speed, uy * speed)
                if kick is None:
                    continue
                move = self._move(p, self._target(bx + ux * 3.0, by + uy * 3.0))
                path = self._touch_path(p, bx, by, vx, vy, kick, move, opponents)
                if path is None or path[2] > 0.7:
                    continue
                if best is None or path[0] > best[0]:
                    best = (path[0], kick, move, path[1])
        if best is not None:
            return best[:3]
        return original

    def _keeper_reaches(self, keeper, bx, by, vx, vy, target, chase, cooldown):
        px, py, pvx, pvy = keeper[1:]
        for tick in range(1, 27):
            previous_scale = self._roll[tick - 1]
            old_x, old_y = (bx + vx * previous_scale, by + vy * previous_scale)
            aim = self._target(old_x, old_y) if chase else target
            before = math.hypot(px - old_x, py - old_y)
            movement = self._move((keeper[0], px, py, pvx, pvy), aim)
            pvx = pvx * self._damping + movement[0] * self._acc
            pvy = pvy * self._damping + movement[1] * self._acc
            speed = math.hypot(pvx, pvy)
            if speed > self._speed:
                pvx *= self._speed / speed
                pvy *= self._speed / speed
            px += pvx * self._dt
            py += pvy * self._dt
            if cooldown < tick and before <= self._range and (math.hypot(px - old_x, py - old_y) < self._range - 0.18):
                return True
            scale = self._roll[tick]
            x, y = (bx + vx * scale, by + vy * scale)
            if x < self._left + self._ball_radius:
                return False
            if math.hypot(px - x, py - y) <= self._contact:
                return True
        return False

    def _choose_marker(self, free, target, threat_id, tick):
        marker = self._role_closest_eta(free, target)
        self._mark_assignments[threat_id] = (marker[0], tick + int(0.3 * self._hz))
        return marker

    def _retain_mark(self, obs, friends, opponents, chaser, targets):
        ours = {p[0] for p in friends}
        if obs.ball.controlling_player in ours or obs.ball.last_touch in ours:
            return
        bx, by = obs.ball.position
        candidates = []
        for threat in opponents[1:]:
            old = self._mark_assignments.get(threat[0])
            if old is None or obs.tick > old[1] or threat[1] >= min(8.0, bx - 1.0) or (abs(threat[2]) > 24.0):
                continue
            marker = next((p for p in friends[1:] if p[0] == old[0] and p[0] != chaser[0]), None)
            if marker is not None and marker[1] <= threat[1] + 0.5 and (math.hypot(marker[1] - threat[1], marker[2] - threat[2]) < 6.0):
                candidates.append((threat[1] + abs(threat[2]) * 0.25, threat, marker))
        if candidates:
            _, threat, marker = min(candidates, key=lambda item: item[0])
            ux, uy = _unit(self._left - threat[1], -threat[2])
            targets[marker[0]] = self._target(threat[1] + ux * 3.0, threat[2] + uy * 3.0)

    def _cover_shape(self, obs, friends, opponents, chaser, races, enemy_eta, targets):
        bx, by = obs.ball.position
        ours = {p[0] for p in friends}
        secure = obs.ball.controlling_player in ours or (obs.ball.last_touch in ours and races[chaser[0]][0] + 0.16 < enemy_eta)
        pressure = min((math.hypot(o[1] - bx, o[2] - by) for o in opponents), default=100.0)
        if secure or abs(by) < 12.0 or pressure > 5.0:
            return
        guard_id = self._shape_cover_id
        if guard_id is None or guard_id == chaser[0]:
            return
        old = targets[guard_id]
        fraction = _clip((old[0] - self._left) / max(3.0, bx - self._left), 0.0, 1.0)
        targets[guard_id] = self._target(old[0], by * fraction)

    def _bank_path(self, bx, by, vx, vy):
        wall = self._half_height - self._ball_radius
        samples = [(self._dt, bx, by)]
        bounce = None
        for tick in range(2, 51):
            bx += vx * self._dt
            by += vy * self._dt
            if abs(by) > wall:
                if bounce is not None:
                    break
                side = 1.0 if by > 0.0 else -1.0
                by = side * wall * 2.0 - by
                vy = -side * abs(vy) * self._wall
                bounce = tick * self._dt
            vx *= self._friction
            vy *= self._friction
            if bx <= self._left + self._ball_radius or bx >= self._right - self._ball_radius:
                break
            if tick % 2 == 0 or (bounce is not None and abs(tick * self._dt - bounce) < 1e-08):
                samples.append((tick * self._dt, bx, by))
        return (samples, bounce)

    def _bank_release(self, p, bx, by, vx, vy, friends, opponents):
        if bx > 18.0 or bx < self._left + 10.0 or abs(by) < 9.0:
            return None
        wall = (self._half_height - self._ball_radius) * (1.0 if by >= 0.0 else -1.0)
        normal_move = self._move(p, (bx + 0.3, by))
        brake = _unit(-p[3], -p[4])
        best = None
        direct_cache = {}
        used = 0
        candidates = [(receiver, offset) for receiver in friends[1:] for offset in (0.0, 7.0, 13.0)]
        for receiver, wall_lead in candidates:
            if self._search_expired():
                return best
            if receiver[0] == p[0] or receiver[1] < bx + 5.0:
                continue
            if receiver[0] not in direct_cache:
                direct = self._pass_velocity(bx, by, vx, vy, receiver[1], receiver[2])
                safe = False
                if direct is not None:
                    kick = self._kick_to_velocity(vx, vy, direct[0], direct[1])
                    launch = self._carrier_contact(p, bx, by, *self._requested_velocity(vx, vy, kick), normal_move) if kick is not None else None
                    if launch is not None:
                        direct_path = self._pass_path(launch, (bx, by))
                        safe = self._pass_race(receiver, direct_path, opponents, 0.18, self._dt) is not None and self._lane(bx, by, receiver[1], receiver[2], direct[2], opponents) > 1.5
                direct_cache[receiver[0]] = safe
            if direct_cache[receiver[0]]:
                continue
            for extra in (0.0, 3.0):
                lateral = (1.0 if by >= 0.0 else -1.0) * wall_lead
                tx, ty = self._target(receiver[1] + extra, receiver[2] + lateral)
                velocity = None
                for _ in range(2):
                    virtual_y = wall + (wall - ty) / self._wall
                    velocity = self._pass_velocity(bx, by, vx, vy, tx, virtual_y)
                    if velocity is None or velocity[0] < 4.0:
                        break
                    along_distance = (tx - bx) * velocity[2] / velocity[0]
                    flight = self._flight(along_distance, velocity[2])
                    lead = min(1.1, flight)
                    tx, ty = self._target(receiver[1] + receiver[3] * lead * 0.8 + extra, receiver[2] + receiver[4] * lead * 0.8 + lateral)
                if velocity is None or velocity[0] < 4.0:
                    continue
                virtual_y = wall + (wall - ty) / self._wall
                velocity = self._pass_velocity(bx, by, vx, vy, tx, virtual_y)
                if velocity is None:
                    continue
                kick = self._kick_to_velocity(vx, vy, velocity[0], velocity[1])
                if kick is None:
                    continue
                previous_launch = None
                for movement in (normal_move, brake):
                    sx, sy = self._requested_velocity(vx, vy, kick)
                    launch = self._carrier_contact(p, bx, by, sx, sy, movement)
                    if launch is None or launch[2] <= 4.0 or launch[3] * wall <= 0.0 or (abs(launch[1]) > self._half_height - self._ball_radius):
                        continue
                    if launch == previous_launch:
                        continue
                    previous_launch = launch
                    if self.BANK_LAUNCH_BUDGET and used >= self.BANK_LAUNCH_BUDGET:
                        return best
                    used += 1
                    path, bounce = self._bank_path(*launch)
                    if bounce is None or bounce > 1.2:
                        continue
                    path = self._pass_path(launch, (bx, by), 2.2)
                    race = self._pass_race(receiver, path, opponents, self.BANK_MARGIN, bounce + self._dt, 2.2)
                    if race is None:
                        continue
                    (arrival, (x, y)), enemy = race
                    if x < bx + 5.0 or abs(y) > self._half_height - 2.0:
                        continue
                    relevant = [s for s in path if s[0] <= arrival + 0.16]
                    blocked = False
                    for t, x0, y0 in relevant:
                        if t > arrival - 0.1:
                            continue
                        for other in friends[1:]:
                            if other[0] == receiver[0] or (other[0] == p[0] and t < 0.3):
                                continue
                            if self._eta(other, x0, y0) <= t - 0.05:
                                blocked = True
                                break
                        if blocked:
                            break
                    if blocked:
                        continue
                    score = (x - bx) * 0.07 + min(enemy - arrival, 0.8) * 1.5 - arrival * 0.3
                    if best is None or score > best[0]:
                        best = (score, kick, movement, (receiver[0], x, y))
        return best

    def _counterpress_targets(self, obs, bx, by, vx, vy, outfield, opponents, races, chaser, enemy_eta, protected, baseline_targets):
        own_ids = {p[0] for p in outfield}
        own_ids.add(0)
        enemy_ids = {p[0] for p in opponents}
        touch = obs.ball.last_touch
        holder = obs.ball.controlling_player
        touch_changed = touch is not None and touch != self._press_last_ball_touch
        holder_changed = holder is not None and holder != self._press_last_ball_holder
        actual = touch if touch_changed else holder if holder_changed else None
        owner = 0 if actual in own_ids else 1 if actual in enemy_ids else None
        if owner == 0:
            self._press_own_contact_tick = obs.tick
            self._press_until = -1
        elif owner == 1 and self._press_contact_owner == 0 and (obs.tick - self._press_own_contact_tick <= int(2.5 * self._hz)) and (not protected) and (bx >= 0.0):
            self._press_until = obs.tick + int(self.COUNTERPRESS_SECONDS * self._hz)
            self._press_origin = (bx, by)
        if owner is not None:
            self._press_contact_owner = owner
        elif holder in own_ids and self._press_contact_owner == 0:
            self._press_own_contact_tick = obs.tick
        self._press_last_ball_touch = touch
        self._press_last_ball_holder = holder
        if protected or obs.tick >= self._press_until or self._press_origin is None:
            return None
        origin_x, origin_y = self._press_origin
        nearest = races[chaser[0]][0]
        local = sum((math.hypot(p[1] - bx, p[2] - by) < 16.0 for p in outfield))
        escaped = bx < 0.0 or math.hypot(vx, vy) > 12.0 or bx < origin_x - 7.0 or (math.hypot(bx - origin_x, by - origin_y) > 15.0) or (nearest > enemy_eta + self.COUNTERPRESS_RACE_MARGIN) or (local < 2) or (vx < -13.0 and abs(by) < self._mouth + 5.0)
        if escaped:
            self._press_until = -1
            return None
        targets = {chaser[0]: self._target(*races[chaser[0]][1])}
        available = [p for p in outfield if p[0] != chaser[0]]
        if len(available) < 2:
            return None
        reserve = min(available, key=lambda p: baseline_targets[p[0]][0])
        available = [p for p in available if p[0] != reserve[0]]
        outlets = [o for o in opponents if o[1] < bx + 1.0 and 4.0 < math.hypot(o[1] - bx, o[2] - by) < 27.0]
        if outlets:
            outlet = min(outlets, key=lambda o: self._eta(chaser, o[1], o[2]) * 0.35 + math.hypot(o[1] - bx, o[2] - by) * 0.03 + (o[1] - bx) * 0.025)
            ux, uy = _unit(outlet[1] - bx, outlet[2] - by)
            screen = self._target(bx + ux * 4.0, by + uy * 4.0)
        else:
            screen = self._target(bx - 3.8, by * 0.65)
        second = self._closest_eta(available, screen)
        if self._eta(second, *screen) > 0.55 or math.hypot(chaser[1] - bx, chaser[2] - by) > 8.0:
            return None
        targets[second[0]] = screen
        return targets

    def _early_body_margin(self, path, opponents, until):
        margin = 2.0
        for t, x, y in path:
            if t > min(until, 0.55):
                break
            n = max(1, int(round(t * self._hz)))
            coast, reach = self._reach_table[n]
            for q in opponents:
                radius = self._range if self._enemy_cooldowns.get(q[0], 0) <= n else self._contact
                gap = math.hypot(x - q[1] - q[3] * coast, y - q[2] - q[4] * coast)
                margin = min(margin, (gap - reach - radius) / self._speed)
        return margin

    def _link_option(self, p, bx, by, vx, vy, receiver, opponents, tx, ty, speed):
        ux, uy = _unit(tx - bx, ty - by)
        kick = self._kick_to_velocity(vx, vy, ux * speed, uy * speed)
        if kick is None:
            return None
        movement = self._move(p, (bx + 0.3, by))
        sx, sy = self._requested_velocity(vx, vy, kick)
        launch = self._carrier_contact(p, bx, by, sx, sy, movement)
        if launch is None:
            return None
        path = self._pass_path(launch, (bx, by), 1.8)
        race = self._pass_race(receiver, path, opponents, self.LINK_MARGIN, self._dt, 1.8)
        if race is None:
            return None
        (arrival, point), enemy = race
        if point[0] < self._left + 9.0 or math.hypot(point[0] - bx, point[1] - by) < 4.0:
            return None
        margin = enemy - arrival
        if margin < self.LINK_MARGIN or self._early_body_margin(path, opponents, arrival) < -0.04:
            return None
        progress = math.hypot(self._right - bx, by) - math.hypot(self._right - point[0], point[1])
        space = min((math.hypot(point[0] - q[1] - q[3] * min(arrival, 0.5), point[1] - q[2] - q[4] * min(arrival, 0.5)) for q in opponents), default=20.0)
        score = 0.9 + progress * 0.15 + min(margin, 0.8) * 3.0 + min(space, 9.0) * 0.1 - arrival * 0.7
        if abs(point[1]) < 12.0 and point[0] > self._right - 27.0:
            score += 1.0
        if p[0] == 0 or bx < self._left + 17.0:
            score += 0.7
        return (score, kick, movement, (receiver[0], point[0], point[1]))

    def _search_links(self, p, bx, by, vx, vy, friends, opponents):
        best = None
        for q in friends:
            if q[0] in (p[0], 0):
                continue
            gap = math.hypot(q[1] - bx, q[2] - by)
            if not 4.0 < gap < 39.0:
                continue
            for speed in (14.0, 20.0, 26.0):
                if self._search_expired():
                    return best
                lead = min(0.9, self._flight(gap, speed))
                tx, ty = self._target(q[1] + q[3] * lead * 0.8, q[2] + q[4] * lead * 0.8)
                option = self._link_option(p, bx, by, vx, vy, q, opponents, tx, ty, speed)
                if option is not None and (best is None or option[0] > best[0]):
                    best = option
        return best

    def _shot_option(self, p, bx, by, vx, vy, opponents, target_y, bank=False):
        if self._search_expired():
            return None
        if bank:
            wall = (self._half_height - self._ball_radius) * (1.0 if by >= 0.0 else -1.0)
            aim_y = wall + (wall - target_y) / self._wall
        else:
            aim_y = target_y
        ux, uy = _unit(self._right - bx, aim_y - by)
        along = vx * ux + vy * uy
        sideways = max(0.0, vx * vx + vy * vy - along * along)
        if sideways >= self._impulse * self._impulse:
            return None
        speed = min(self._ball_cap, along + math.sqrt(self._impulse * self._impulse - sideways))
        kick = self._kick_to_velocity(vx, vy, ux * speed, uy * speed)
        if kick is None:
            return None
        movement = self._move(p, (bx + 0.3, by))
        sx, sy = self._requested_velocity(vx, vy, kick)
        launch = self._carrier_contact(p, bx, by, sx, sy, movement)
        if launch is None:
            return None
        forecast = self._goal_path(launch)
        if forecast is None:
            return None
        path, (flight, gy, end_speed) = forecast
        if flight > 2.5 or end_speed < 6.0:
            return None
        margin = min((self._eta(q, x, y) - t for t, x, y in path for q in opponents), default=1.0)
        if margin < self.SHOT_MARGIN:
            return None
        body = self._early_body_margin(path, opponents, flight)
        if body < -0.06:
            return None
        contact = self._shot_contact_margin(bx, by, launch, opponents, flight)
        if contact < -0.02:
            return None
        score = 6.0 + min(margin, 0.5) * 4.0 - flight * 0.7 + min(end_speed, 20.0) * 0.03
        return (score, kick, movement, None)

    def _endwall_link(self, p, bx, by, vx, vy, friends, opponents):
        if bx < 15.0 or abs(by) < 8.0 or p[0] == 0:
            return None
        wall = self._right - self._ball_radius
        movement = self._move(p, (bx + 0.3, by))
        best = None
        for q in friends[1:]:
            if q[0] == p[0] or q[1] < max(bx + 2.0, self._right - 24.0):
                continue
            for extra in (-4.0, 0.0, 4.0):
                if self._search_expired():
                    return best
                tx, ty = self._target(q[1] + q[3] * 0.4, q[2] + q[4] * 0.4 + extra)
                virtual = wall + (wall - tx) / self._wall
                ux, uy = _unit(virtual - bx, ty - by)
                along = vx * ux + vy * uy
                sideways = max(0.0, vx * vx + vy * vy - along * along)
                if sideways >= self._impulse * self._impulse:
                    continue
                speed = min(self._ball_cap, along + math.sqrt(self._impulse * self._impulse - sideways))
                kick = self._kick_to_velocity(vx, vy, ux * speed, uy * speed)
                if kick is None:
                    continue
                sx, sy = self._requested_velocity(vx, vy, kick)
                launch = self._carrier_contact(p, bx, by, sx, sy, movement)
                if launch is None or launch[2] < 6.0:
                    continue
                n = self._crossing_ticks(launch[0], launch[2], wall)
                if n > 32:
                    continue
                hit_y = launch[1] + launch[3] * self._roll[n]
                if not self._mouth + 1.1 < abs(hit_y) < self._half_height - 1.0:
                    continue
                path = self._pass_path(launch, (bx, by), 2.4)
                race = self._pass_race(q, path, opponents, 0.12, (n + 2) * self._dt, 2.4)
                if race is None:
                    continue
                (arrival, point), enemy = race
                if point[0] < self._right - 25.0:
                    continue
                margin = enemy - arrival
                if margin < 0.12 or self._early_body_margin(path, opponents, arrival) < -0.04:
                    continue
                progress = math.hypot(self._right - bx, by) - math.hypot(self._right - point[0], point[1])
                space = min((math.hypot(point[0] - o[1], point[1] - o[2]) for o in opponents), default=20.0)
                score = 0.9 + progress * 0.15 + min(margin, 0.8) * 3.0 + min(space, 9.0) * 0.1 - arrival * 0.7
                if point[0] > self._right - 20.0 and abs(point[1]) < 12.0:
                    score += 1.0
                if best is None or score > best[0]:
                    best = (score, kick, movement, (q[0], point[0], point[1]))
        return best

    def _shot_contact_margin(self, bx, by, launch, opponents, until):
        x, y, vx, vy = launch
        oldx, oldy = (bx, by)
        best = 100.0
        wall = self._half_height - self._ball_radius
        steps = min(self.SHOT_CONTACT_TICKS, max(1, int(math.ceil(until * self._hz))))
        for n in range(1, steps + 1):
            coast, reach = self._reach_table[n]
            elapsed = n * self._dt
            for q in opponents:
                qx, qy = (q[1] + q[3] * coast, q[2] + q[4] * coast)
                body = max(math.hypot(x - qx, y - qy) - reach - self._contact, math.hypot(x - q[1], y - q[2]) - self._speed * elapsed - self._contact)
                best = min(best, body)
                if self._enemy_cooldowns.get(q[0], 0) <= n:
                    kick = max(math.hypot(oldx - qx, oldy - qy) - reach - self._range, math.hypot(oldx - q[1], oldy - q[2]) - self._speed * elapsed - self._range)
                    best = min(best, kick)
            if best < -0.02:
                return best
            if x >= self._right - self._ball_radius or x <= self._left + self._ball_radius:
                break
            oldx, oldy = (x, y)
            x += vx * self._dt
            y += vy * self._dt
            if abs(y) > wall:
                side = 1.0 if y > 0.0 else -1.0
                y = side * wall * 2.0 - y
                vy = -side * abs(vy) * self._wall
            vx *= self._friction
            vy *= self._friction
        return best

# Normal play, lead lock and wall breaker.
class _FallbackPolicy(_Core):
    name = 'Pep Guardiola + Jurgen Klopp Hybrid'
    version = 'replay-finishing-handoffs-v1'
    LINK_MARGIN = 0.03
    POST_AIM_INSET = 0.2
    RELAY_PRESSURE = 5.5
    RELAY_MARGIN = 0.1
    RELAY_MAX_TICKS = 4
    RELAY_LOOKAHEAD_TICKS = 8
    RELAY_RECEIVER_LIMIT = 2
    LOCK_LEAD = 1
    LOCK_TIME = 1.0
    LOCK_MAX = 99
    WALL_BREAK = 1
    LOCK_SPACING = 2.8
    SCOUT_KEEPER_CAP = 0.0
    SCOUT_CUTBACK = True

    def reset(self, seed):
        self._enemy_cooldowns = {}
        self._friend_cooldowns = {}
        self._receive_aim = None
        self._next_receive_aim = None
        self._last_pass_motion = None
        self._runtime_path = None
        self._runtime_steps = None
        self._runtime_queries = {}
        self._mark_assignments = {}
        self._bank_plan = None
        self._bank_receive = None
        self._ready = False
        self._restart_until = -1
        self._restart_owner = None
        self._chaser = -1
        self._last_score = None
        self._touch_movement = None
        self._pass_plan = None
        self._receive_plan = None
        self._relay_proposal = None
        self._relay_receive = None
        self._relay_fallback = None
        self._transition_owner = None
        self._transition_until = -1
        self._transition_last_touch = None
        self._transition_holder = None
        self._transition_score = None
        self._transition_tick = None
        self._transition_active = False
        self._press_until = -1
        self._press_origin = None
        self._press_contact_owner = None
        self._press_last_ball_touch = None
        self._press_last_ball_holder = None
        self._scout_outlet = None
        self._x_reset()
        self._press_own_contact_tick = -100000

    def _setup(self, field):
        self._dt = 1.0 / field.simulation_hz
        self._hz = field.simulation_hz
        self._tick_of = {}
        self._speed = field.max_speed
        self._acc = field.acceleration * self._dt
        self._friction = field.ball_friction
        self._log_friction = math.log(self._friction)
        self._impulse = field.kick_impulse
        self._range = field.kick_range
        self._eta_range = self._range * 0.8
        self._left = field.my_goal[0]
        self._right = field.opponent_goal[0]
        self._half_height = field.height * 0.5
        self._goal_half = field.goal_width * 0.5
        self._post_aim = max(0.0, self._goal_half - self.POST_AIM_INSET)
        self._mouth = max(0.0, field.goal_width * 0.5 - 0.6)
        self._circle = field.centre_circle_radius
        self._ball_radius = field.ball_radius
        self._contact = field.player_radius + field.ball_radius
        self._damping = 0.9
        self._wall = 0.75
        self._ball_cap = 30.0
        self._drag = tuple((self._friction ** tick for tick in range(81)))
        self._roll = tuple((self._dt * (1.0 - drag) / (1.0 - self._friction) for drag in self._drag))
        self._forecast_steps = tuple(((tick * self._dt, self._roll[tick]) for tick in (0, 2, 4, 6, 9, 12, 16, 20, 25, 31, 38, 47, 58, 70, 80)))
        self._reach_table = tuple(((self._dt * self._damping * (1.0 - self._damping ** n) / (1.0 - self._damping), self._dt * self._acc / (1.0 - self._damping) * (n - self._damping * (1.0 - self._damping ** n) / (1.0 - self._damping))) for n in range(83)))
        self._runtime_path = None
        self._runtime_steps = None
        self._runtime_queries = {}
        self._ready = True

    def _intercept(self, p, samples):
        _, px, py, pvx, pvy = p
        hypot = math.hypot
        speed = self._speed
        eta_range = self._eta_range
        reach_table = self._reach_table
        tick_of = self._tick_of
        hz = self._hz
        best_cost = None
        best_point = None
        for t, x, y in samples:
            dx, dy = (x - px, y - py)
            d = hypot(dx, dy)
            try:
                n = tick_of[t]
            except KeyError:
                n = max(0, int(round(t * hz)))
                tick_of[t] = n
            if n == 0:
                feasible = d <= eta_range
            else:
                coast, reach = reach_table[n]
                feasible = d <= speed * t + eta_range and hypot(dx - pvx * coast, dy - pvy * coast) <= reach + eta_range
            if feasible:
                return (t, (x, y))
            if d < 1e-06:
                eta = 0.0
            else:
                startup = 1.0 - (dx * pvx + dy * pvy) / d / speed
                if startup < 0.0:
                    startup = 0.0
                startup *= 0.3
                gap = d - eta_range
                if gap < 0.0:
                    gap = 0.0
                eta = gap / speed + startup + abs(dx * pvy - dy * pvx) / d * 0.025
            cost = eta + t * 0.12
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_point = (x, y)
        return None if best_cost is None else (best_cost, best_point)

    def _touch_path(self, p, bx, by, vx, vy, kick, movement, opponents):
        sx, sy = self._requested_velocity(vx, vy, kick)
        contact = self._carrier_contact(p, bx, by, sx, sy, movement)
        if contact is None:
            return None
        x, y, sx, sy = contact
        pvx = p[3] * self._damping + movement[0] * self._acc
        pvy = p[4] * self._damping + movement[1] * self._acc
        player_speed = math.hypot(pvx, pvy)
        if player_speed > self._speed:
            pvx *= self._speed / player_speed
            pvy *= self._speed / player_speed
        px, py = (p[1] + pvx * self._dt, p[2] + pvy * self._dt)
        initial_distance = math.hypot(self._right - bx, by)
        margin = 4.0
        recapture = None
        cooldowns = getattr(self, '_enemy_cooldowns', {})
        for tick in range(1, 12):
            elapsed = tick * self._dt
            if abs(y) > self._half_height - 1.0 or x < self._left + 2.0:
                return None
            steps = tick + 1
            coast = self._dt * self._damping * (1.0 - self._damping ** steps) / (1.0 - self._damping)
            reach = self._dt * self._acc / (1.0 - self._damping) * (steps - self._damping * (1.0 - self._damping ** steps) / (1.0 - self._damping))
            for enemy in opponents:
                if cooldowns.get(enemy[0], 0) > tick:
                    continue
                cx = enemy[1] + enemy[3] * coast
                cy = enemy[2] + enemy[4] * coast
                remaining = math.hypot(x - cx, y - cy) - reach - self._range
                margin = min(margin, remaining / self._speed)
            gap = math.hypot(x - px, y - py)
            if tick >= 5 and gap < self._range - 0.15:
                recapture = elapsed
                break
            if tick == 11:
                break
            player = (p[0], px, py, pvx, pvy)
            chase = self._target(x + sx * 0.15, y + sy * 0.15)
            move = self._move(player, chase)
            pvx = pvx * self._damping + move[0] * self._acc
            pvy = pvy * self._damping + move[1] * self._acc
            player_speed = math.hypot(pvx, pvy)
            if player_speed > self._speed:
                pvx *= self._speed / player_speed
                pvy *= self._speed / player_speed
            px += pvx * self._dt
            py += pvy * self._dt
            x += sx * self._dt
            y += sy * self._dt
            sx *= self._friction
            sy *= self._friction
            dx, dy = (x - px, y - py)
            gap = math.hypot(dx, dy)
            if 1e-08 < gap < self._contact:
                nx, ny = (dx / gap, dy / gap)
                x, y = (px + nx * self._contact, py + ny * self._contact)
                closing = (sx - pvx) * nx + (sy - pvy) * ny
                if closing < 0.0:
                    sx -= 1.25 * closing * nx
                    sy -= 1.25 * closing * ny
        if recapture is None:
            recapture = 0.55 + self._eta((p[0], px, py, pvx, pvy), x, y)
        progress = initial_distance - math.hypot(self._right - x, y)
        clearance = min((math.hypot(x - q[1] - q[3] * 0.25, y - q[2] - q[4] * 0.25) for q in opponents), default=15.0)
        score = progress * 0.85 + min(clearance, 8.0) * 0.25 + _clip(margin, -0.6, 0.6) * 8.0 - max(0.0, recapture - 0.25) * 8.0
        return (score, margin, recapture)

    def _v10_act(self, obs, friends=None, opponents=None):
        if not self._ready:
            self._setup(obs.field)
            self._restart_until = obs.tick + int(3.0 * self._hz)
            self._restart_owner = obs.ball.controlling_team
        score = obs.score
        if self._last_score is not None and score != self._last_score:
            self._restart_until = obs.tick + int(3.0 * self._hz)
            self._restart_owner = 0 if score[1] > self._last_score[1] else 1
            self._chaser = -1
            self._receive_plan = None
            self._relay_proposal = None
            self._relay_receive = None
            self._relay_fallback = None
            self._bank_receive = None
            self._receive_aim = None
            self._mark_assignments = {}
            self._press_until = -1
            self._press_origin = None
            self._press_contact_owner = None
            self._press_own_contact_tick = -100000
            self._press_last_ball_touch = None
            self._press_last_ball_holder = None
        self._last_score = score
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        if math.hypot(bx, by) > 0.7 or math.hypot(vx, vy) > 0.15:
            self._restart_until = -1
        protected = obs.tick < self._restart_until and self._restart_owner == 1
        if friends is None or opponents is None:
            friends = [(p.id, *p.position, *p.velocity) for p in obs.my_players]
            opponents = [(p.id, *p.position, *p.velocity) for p in obs.opponents]
            self._enemy_cooldowns = {p.id: p.kick_cooldown_ticks for p in obs.opponents}
            self._friend_cooldowns = {p.id: p.kick_cooldown_ticks for p in obs.my_players}
        actions = TeamAction(debug={'roles': self.PLAYER_ROLES})
        if not friends:
            return actions
        keeper = friends[0]
        outfield = friends[1:] or friends
        samples = self._trajectory(bx, by, vx, vy)
        races = {}
        chaser = None
        chaser_eta = None
        previous = None
        for p in outfield:
            race = self._intercept(p, samples)
            races[p[0]] = race
            if chaser is None or race[0] < chaser_eta:
                chaser, chaser_eta = (p, race[0])
            if p[0] == self._chaser:
                previous = p
        if previous is not None and races[previous[0]][0] < races[chaser[0]][0] + 0.12:
            chaser = previous
        self._chaser = chaser[0]
        enemy_eta = None
        for o in opponents:
            eta = self._intercept(o, samples)[0]
            if enemy_eta is None or eta < enemy_eta:
                enemy_eta = eta
        if enemy_eta is None:
            enemy_eta = 100.0
        self._transition_observe(obs, protected, friends, opponents, (min((v[0] for k, v in races.items() if k != 0), default=100.0), enemy_eta))
        attack = races[chaser[0]][0] <= enemy_eta + 0.12
        keeper_x = self._scout_keeper_x(obs, keeper) if self.SCOUT_KEEPER_CAP else self._left + 2.2
        keeper_y = by * 2.2 / max(3.0, bx - self._left)
        if self.PREDICTIVE_KEEPER and vx < -8.0 and (math.hypot(vx, vy) >= 12.0) and (bx > keeper_x):
            time_to_line = (keeper_x - bx) / vx
            if 0.0 < time_to_line < 1.25:
                keeper_y = by + vy * time_to_line
        keeper_limit = self._scout_keeper_limit(obs) if self.SCOUT_KEEPER_CAP else self._mouth
        keeper_target = (keeper_x, _clip(keeper_y, -keeper_limit, keeper_limit))
        sweep = bx < self._left + 10.0 and self._eta(keeper, bx, by) < races[chaser[0]][0] * 0.85
        if sweep and abs(by) > self._mouth + 1.0:
            ours = self._eta(keeper, bx, by)
            theirs = min((self._eta(o, bx, by) for o in opponents), default=100.0)
            away = obs.ball.last_touch == keeper[0] and vx > 6.0 and ((bx - keeper[1]) * vx + (by - keeper[2]) * vy > 0.0)
            sweep = not away and ours <= 1.1 and (ours + 0.2 < theirs)
        if self.KEEPER_PRIORITY and self.PREDICTIVE_KEEPER and (vx < -8.0) and (math.hypot(vx, vy) >= 12.0) and (bx > keeper_x):
            flight = (keeper_x - bx) / vx
            if 0.0 < flight < 0.55:
                goal_y = by + vy * (self._left + self._ball_radius - bx) / vx
                opposite = (keeper_target[1] - keeper[2]) * (by - keeper[2]) < 0.0
                if abs(goal_y) <= self._mouth + 0.6 and opposite:
                    cooldown = obs.my_players[0].kick_cooldown_ticks
                    line = self._keeper_reaches(keeper, bx, by, vx, vy, keeper_target, False, cooldown)
                    rush = self._keeper_reaches(keeper, bx, by, vx, vy, keeper_target, True, cooldown)
                    if line and (not rush):
                        sweep = False
        if self.KEEPER_RECOVERY:
            outgoing = obs.ball.last_touch == keeper[0] and vx > 10.0 and (self._receive_plan is not None) and (self._receive_plan[1] == keeper[0]) and (math.hypot(bx - keeper[1], by - keeper[2]) > self._range + 0.3)
            if outgoing:
                receiver_id = self._receive_plan[0]
                receiver = next((p for p in outfield if p[0] == receiver_id), None)
                safe = receiver is not None and races[receiver_id][0] + 0.12 < enemy_eta
                if safe:
                    sweep = False
        if sweep:
            keeper_target = self._target(bx, by)
        targets = {keeper[0]: keeper_target, chaser[0]: self._target(*races[chaser[0]][1])}
        free = [p for p in outfield if p[0] != chaser[0]]
        self._shape_cover_id = None
        if free:
            cover_target = self._target(min(28.0, bx - 2.0), _clip(by, -self._half_height + 2.0, self._half_height - 2.0))
            cover = self._role_closest_eta(free, cover_target, cover=True)
            if cover[0] == 1:
                cover_target = self._target(min(28.0, bx - 3.5), cover_target[1])
            elif cover[0] == 2:
                cover_target = self._target(min(28.0, bx - 2.75), cover_target[1])
            targets[cover[0]] = cover_target
            self._shape_cover_id = cover[0]
            free = [p for p in free if p[0] != cover[0]]
        if attack:
            spread = max(7.0, 15.0 - max(0.0, bx - 20.0) * 0.35)
            free.sort(key=lambda p: p[2])
            for index, p in enumerate(free):
                lane = 0.0 if len(free) == 1 else -spread + 2.0 * spread * index / (len(free) - 1)
                targets[p[0]] = self._role_support(p, bx, by, lane)
        else:
            threats = sorted(opponents, key=lambda p: p[1] + abs(p[2]) * 0.2)
            for threat in threats:
                if not free:
                    break
                if math.hypot(threat[1] - bx, threat[2] - by) < 3.5:
                    continue
                ux, uy = _unit(self._left - threat[1], -threat[2])
                target = self._target(threat[1] + ux * 3.0, threat[2] + uy * 3.0)
                marker = self._choose_marker(free, target, threat[0], obs.tick) if self.MARK_HANDOFF else self._role_closest_eta(free, target)
                targets[marker[0]] = target
                free = [p for p in free if p[0] != marker[0]]
            for p in free:
                targets[p[0]] = self._target(bx - 9.0, p[2] * 0.5)
        self._transition_support(bx, by, friends, opponents, chaser[0], targets)
        actions.debug['text'] = 'Klopp quick transition' if self._transition_active else 'Pep positional control'
        press_targets = self._counterpress_targets(obs, bx, by, vx, vy, outfield, opponents, races, chaser, enemy_eta, protected, targets)
        if press_targets is not None:
            targets.update(press_targets)
            actions.debug['text'] = 'Klopp brief counterpress; Pep cover'
        receive_target = None
        receive_path = None
        if self._receive_plan is None:
            self._relay_receive = None
        if self._receive_plan is not None:
            recipient, passer, expiry = self._receive_plan
            relay = self._relay_receive == self._receive_plan
            recipient_player = next((p for p in friends if p[0] == recipient and p[0] != 0), None)
            if recipient_player is None or obs.tick > expiry or obs.ball.last_touch not in (None, passer) or (not relay and math.hypot(vx, vy) < 9.0):
                self._receive_plan = None
                self._bank_receive = None
                self._receive_aim = None
                self._relay_receive = None
            else:
                if relay:
                    path, verified = self._relay_live_race(obs.tick, recipient_player, (bx, by, vx, vy), opponents)
                else:
                    path = self._pass_path((bx, by, vx, vy))
                    verified = self._pass_race(recipient_player, path, opponents)
                receive_path = path
                if verified is None:
                    self._receive_plan = None
                    self._bank_receive = None
                    self._receive_aim = None
                    self._relay_receive = None
                else:
                    race, _ = verified
                    aim = self._next_receive_aim or race[1]
                    targets[recipient] = self._target(*aim)
                    receive_target = (recipient, aim)
                    self._receive_aim = receive_target
                    if self._bank_receive is not None:
                        self._bank_receive = (recipient, passer, race[1])
        if self.MARK_HANDOFF and attack and (not protected) and (enemy_eta < races[chaser[0]][0] + 0.1):
            self._retain_mark(obs, friends, opponents, chaser, targets)
        if self.COVER_SHAPE and (not protected):
            self._cover_shape(obs, friends, opponents, chaser, races, enemy_eta, targets)
        if self.SCOUT_CUTBACK:
            self._scout_support(obs, friends, opponents, chaser, races, enemy_eta, targets, protected)
        carrier = None
        carrier_gap = None
        for p in friends:
            if obs.can_kick(p[0]):
                gap = math.hypot(p[1] - bx, p[2] - by)
                if carrier is None or gap < carrier_gap:
                    carrier, carrier_gap = (p, gap)
        launched_pass = None
        for p in friends:
            target = targets.get(p[0], (p[1], p[2]))
            if protected and math.hypot(p[1], p[2]) < self._circle + 5.0:
                ux, uy = _unit(p[1], p[2])
                target = (ux * (self._circle + 3.0), uy * (self._circle + 3.0))
            kick = None
            if carrier is not None and p[0] == carrier[0] and (not protected):
                movement = self._move(p, (bx + 0.3, by))
                nx = p[3] * self._damping + movement[0] * self._acc
                ny = p[4] * self._damping + movement[1] * self._acc
                speed = math.hypot(nx, ny)
                if speed > self._speed:
                    nx *= self._speed / speed
                    ny *= self._speed / speed
                distance_next = math.hypot(p[1] + nx * self._dt - bx, p[2] + ny * self._dt - by)
                if distance_next < self._range - 0.18:
                    kick = self._choose_kick(p, bx, by, vx, vy, friends, opponents)
                    if self._touch_movement is not None:
                        movement = self._touch_movement
                    self._receive_plan = None
                    self._bank_receive = None
                    self._receive_aim = None
                    self._relay_receive = None
                    plan = self._bank_plan or self._pass_plan
                    if kick is not None and plan is not None:
                        recipient = plan[0]
                        sx, sy = self._requested_velocity(vx, vy, kick)
                        launch = self._carrier_contact(p, bx, by, sx, sy, movement)
                        receiver = next((q for q in friends if q[0] == recipient and q[0] != 0), None)
                        relay = self._relay_proposal is not None and self._relay_proposal == (recipient, p[0])
                        if relay:
                            horizon = self.RELAY_LOOKAHEAD_TICKS * self._dt
                            collect = self._x_collect(p, launch, (bx, by), receiver, friends, opponents, self._dt, horizon) if launch is not None and receiver is not None else None
                            if collect is not None and collect[3] <= self.RELAY_MAX_TICKS * self._dt + 1e-09:
                                _, point, aim, arrival = collect
                                launched_pass = (recipient, aim)
                                self._receive_aim = launched_pass
                                expiry = obs.tick + max(1, int(math.ceil(arrival * self._hz))) + 2
                                self._receive_plan = (recipient, p[0], expiry)
                                self._relay_receive = self._receive_plan
                            else:
                                kick, movement = self._relay_fallback or (None, movement)
                                self._touch_movement = movement
                                self._pass_plan = None
                                self._bank_plan = None
                                self._relay_proposal = None
                        elif launch is not None and receiver is not None and (math.hypot(launch[2], launch[3]) > 10.5):
                            path = self._pass_path(launch, (bx, by), 2.6)
                            verified = self._pass_race(receiver, path, opponents, after=self._dt, until=2.6)
                            if verified is not None:
                                receiver_race, _ = verified
                                aim = self._next_receive_aim or receiver_race[1]
                                launched_pass = (recipient, aim)
                                self._receive_aim = launched_pass
                                self._receive_plan = (recipient, p[0], obs.tick + int(2.6 * self._hz))
                                if self._bank_plan is not None:
                                    self._bank_receive = (recipient, p[0], receiver_race[1])
            elif (self._x_reception is not None and self._x_reception[0] == p[0] or (self._relay_receive is not None and self._relay_receive == self._receive_plan)) and (not protected) and (receive_target is not None) and (receive_target[0] == p[0]) and (self._receive_plan is not None) and (self._receive_plan[0] == p[0]):
                movement = self._move(p, self._target(*receive_target[1]))
            else:
                movement = self._move(p, target, friends if p[0] != chaser[0] and p[0] != 0 else ())
            if p[0] != 0 and launched_pass is None and (receive_path is not None) and (self._receive_plan is not None) and (self._receive_plan[0] == p[0]) and (carrier is None or carrier[0] != p[0]):
                if self._relay_receive is not None and self._relay_receive == self._receive_plan:
                    _, check = self._relay_live_race(obs.tick, p, (bx, by, vx, vy), opponents, first_move=movement)
                else:
                    check = self._pass_race(p, receive_path, opponents, first_move=movement)
                if check is None:
                    self._receive_plan = None
                    self._bank_receive = None
                    self._receive_aim = None
                    self._relay_receive = None
            if kick is None:
                actions.set(p[0], PlayerAction(movement=movement))
            else:
                actions.set(p[0], PlayerAction(movement=movement, kick_direction=kick[0], kick_power=kick[1]))
        if launched_pass is not None:
            recipient, target = launched_pass
            receiver = next((p for p in friends if p[0] == recipient))
            actions.set(recipient, PlayerAction(movement=self._move(receiver, self._target(*target))))
        return actions

    def _goal_path(self, launch):
        x, y, vx, vy = launch
        path = []
        wall = self._half_height - self._ball_radius
        end_wall = self._right - self._ball_radius
        for tick in range(1, 61):
            if tick > 1:
                x += vx * self._dt
                y += vy * self._dt
            if abs(y) > wall:
                side = 1.0 if y > 0.0 else -1.0
                y = side * wall * 2.0 - y
                vy = -side * abs(vy) * self._wall
            if abs(x) > end_wall and abs(y) > self._goal_half:
                return None
            if x > self._right and vx > 0.0 and (abs(y) <= self._goal_half):
                time = tick * self._dt
                path.append((time, x, y))
                return (path, (time, y, math.hypot(vx, vy)))
            if x < self._left:
                return None
            if tick > 1:
                vx *= self._friction
                vy *= self._friction
            if tick == 1 or tick % 2 == 0:
                path.append((tick * self._dt, x, y))
        return None

    def _before_endwall(self, p, bx, by, vx, vy, friends, opponents):
        fallback = self._legacy_policy_kick(p, bx, by, vx, vy, friends, opponents)
        pressure = min((math.hypot(q[1] - bx, q[2] - by) for q in opponents), default=100.0)
        fallback_plan = self._pass_plan
        fallback_bank = self._bank_plan
        fallback_move = self._touch_movement
        best = None
        blocked_shot = False
        if bx > self._right - 40.0:
            for y in (-5.7, -3.0, 0.0, 3.0, 5.7, -self._post_aim, self._post_aim):
                option = self._shot_option(p, bx, by, vx, vy, opponents, y)
                if option is not None and (best is None or option[0] > best[0]):
                    best = option
        link = self._search_links(p, bx, by, vx, vy, friends, opponents)
        if link is not None and (best is None or link[0] > best[0]):
            best = link
        old_score = -2.0
        if fallback is not None:
            sx, sy = self._requested_velocity(vx, vy, fallback)
            move = fallback_move or self._move(p, (bx + 0.3, by))
            launch = self._carrier_contact(p, bx, by, sx, sy, move)
            goal = self._goal_path(launch) if launch is not None and sx > 0.0 else None
            if goal is not None:
                path, (flight, gy, end_speed) = goal
                margin = min((self._eta(q, x, y) - t for t, x, y in path for q in opponents), default=1.0)
                contact = self._shot_contact_margin(bx, by, launch, opponents, flight)
                old_score = 6.0 + min(margin, 0.5) * 4.0 - flight * 0.7 + min(end_speed, 20.0) * 0.03
                if bx > self._right - 40.0 and fallback_plan is None and (fallback_bank is None) and (contact < -0.02 or margin < self.SHOT_MARGIN or self._early_body_margin(path, opponents, flight) < -0.06):
                    old_score = -2.0
                    blocked_shot = True
            elif fallback_plan is not None:
                receiver = next((q for q in friends if q[0] == fallback_plan[0]), None)
                if receiver is not None:
                    rated = self._link_option(p, bx, by, vx, vy, receiver, opponents, fallback_plan[1], fallback_plan[2], math.hypot(sx, sy))
                    old_score = rated[0] if rated is not None else -0.5
            elif math.hypot(sx, sy) <= 10.5:
                path = self._touch_path(p, bx, by, vx, vy, fallback, move, opponents)
                old_score = path[0] * 0.55 if path is not None else -2.0
        if blocked_shot:
            controlled = self._controlled_touch(p, bx, by, vx, vy, opponents)
            if controlled is not None:
                csx, csy = self._requested_velocity(vx, vy, controlled[1])
                control_launch = self._carrier_contact(p, bx, by, csx, csy, controlled[2])
                control_path = self._touch_path(p, bx, by, vx, vy, controlled[1], controlled[2], opponents)
                if control_launch is not None and control_path is not None and (self._shot_contact_margin(bx, by, control_launch, opponents, 0.15) >= -0.02):
                    candidate = (control_path[0] * 0.55, controlled[1], controlled[2], None)
                    if best is None or candidate[0] > best[0]:
                        best = candidate
        if best is not None and best[0] > old_score + self.OPTION_SWITCH_MARGIN:
            self._touch_movement = best[2]
            self._pass_plan = best[3]
            self._bank_plan = None
            return best[1]
        self._pass_plan = fallback_plan
        self._bank_plan = fallback_bank
        self._touch_movement = fallback_move
        return fallback

    def _v10_choose_kick(self, p, bx, by, vx, vy, friends, opponents):
        fallback = self._before_endwall(p, bx, by, vx, vy, friends, opponents)
        if fallback is None or bx < 15.0 or abs(by) < 8.0:
            return fallback
        sx, sy = self._requested_velocity(vx, vy, fallback)
        move = self._touch_movement or self._move(p, (bx + 0.3, by))
        launch = self._carrier_contact(p, bx, by, sx, sy, move)
        if launch is not None:
            goal = self._goal_path(launch)
            if goal is not None:
                path, goal_details = goal
                margin = min((self._eta(q, x, y) - t for t, x, y in path for q in opponents), default=1.0)
                contact = self._shot_contact_margin(bx, by, launch, opponents, goal_details[0])
                if margin >= self.SHOT_MARGIN and contact >= -0.02 and (self._early_body_margin(path, opponents, goal_details[0]) >= -0.06):
                    return fallback
        option = self._endwall_link(p, bx, by, vx, vy, friends, opponents)
        if option is None:
            return fallback
        score = -2.0
        if self._pass_plan is not None:
            q = next((q for q in friends if q[0] == self._pass_plan[0]), None)
            rated = self._link_option(p, bx, by, vx, vy, q, opponents, self._pass_plan[1], self._pass_plan[2], math.hypot(sx, sy)) if q else None
            if rated is not None:
                score = rated[0]
        elif math.hypot(sx, sy) <= 10.5:
            rated = self._touch_path(p, bx, by, vx, vy, fallback, move, opponents)
            if rated is not None:
                score = rated[0] * 0.55
        if option[0] > score + 0.2:
            self._touch_movement = option[2]
            self._pass_plan = option[3]
            self._bank_plan = option[3]
            return option[1]
        return fallback

    def _x_reset(self):
        self._x_keeper_history = None
        self._x_rush = False
        self._x_reception = None
        self._x_proposal = None
        self._x_events = []
        self._x_last_tick = -1
        self._x_score = None

    def _x_event(self, name):
        if len(self._x_events) < 8:
            self._x_events.append(name)

    def _x_prepare(self, obs):
        if not hasattr(self, '_x_last_tick') or obs.tick <= self._x_last_tick:
            self._x_reset()
        self._x_last_tick = obs.tick
        self._x_events = []
        self._x_proposal = None
        self._x_obs = obs
        if not self._ready:
            self._setup(obs.field)
            self._restart_until = obs.tick + int(3.0 * self._hz)
            self._restart_owner = obs.ball.controlling_team
        self._enemy_cooldowns = {p.id: p.kick_cooldown_ticks for p in obs.opponents}
        self._friend_cooldowns = {p.id: p.kick_cooldown_ticks for p in obs.my_players}
        friends = [(p.id, *p.position, *p.velocity) for p in obs.my_players]
        opponents = [(p.id, *p.position, *p.velocity) for p in obs.opponents]
        if self._x_score is not None and obs.score != self._x_score:
            self._x_reception = None
        self._x_score = obs.score
        self._x_rush = False
        if opponents:
            q = opponents[0]
            old = self._x_keeper_history
            bx, by = obs.ball.position
            toward = (bx - q[1]) * q[3] + (by - q[2]) * q[4]
            self._x_rush = old is not None and obs.tick - old[0] == 1 and (self._right - q[1] > 5.5) and (bx > 12.0) and (math.hypot(q[3], q[4]) > 1.5) and (toward > 1.0) and (q[1] < old[1] - 0.035) and (math.hypot(q[1] - bx, q[2] - by) < 18.0)
            self._x_keeper_history = (obs.tick, q[1], q[2])
        return (friends, opponents)

    def _x_collect(self, p, launch, origin, receiver, friends, opponents, after, until=2.4):
        old = self.FIRST_TOUCH
        self.FIRST_TOUCH = True
        try:
            path = self._pass_path(launch, origin, until)
            race = self._pass_race(receiver, path, opponents, 0.15, after, until)
            if race is None:
                return None
            (arrival, point), enemy = race
            aim = self._next_receive_aim or point
            if self._early_body_margin(path, opponents, arrival) < -0.02:
                return None
            for other in friends:
                if other[0] == receiver[0]:
                    continue
                start = 0.3 if other[0] == p[0] else self._dt
                body = [(t, x, y) for t, x, y in path if start <= t < arrival - 0.1]
                for t, x, y in body:
                    n = int(round(t * self._hz))
                    if self._pass_reachable(other, x, y, n, self._contact):
                        return None
            progress = math.hypot(self._right - origin[0], origin[1]) - math.hypot(self._right - point[0], point[1])
            score = progress * 0.15 + min(enemy - arrival, 0.8) * 3.0 - arrival * 0.7
            if point[0] > self._right - 25.0 and abs(point[1]) < 11.0:
                score += 1.0
            return (score, point, aim, arrival)
        finally:
            self.FIRST_TOUCH = old

    def _x_direct(self, p, bx, by, vx, vy, q, friends, opponents, tx, ty, speed):
        ux, uy = _unit(tx - bx, ty - by)
        kick = self._kick_to_velocity(vx, vy, ux * speed, uy * speed)
        movement = self._move(p, (bx + 0.3, by))
        if kick is None:
            return None
        launch = self._carrier_contact(p, bx, by, *self._requested_velocity(vx, vy, kick), movement)
        if launch is None:
            return None
        collect = self._x_collect(p, launch, (bx, by), q, friends, opponents, self._dt, 1.8)
        if collect is None:
            return None
        score, point, aim, arrival = collect
        return (score, kick, movement, (q[0], *point), aim)

    def _x_trap(self, p, bx, by, vx, vy, friends, opponents):
        if not self._x_rush or p[0] == 0 or bx < 16.0:
            return None
        keeper = opponents[0]
        best = None
        receivers = sorted((q for q in friends[1:] if q[0] != p[0] and q[1] > bx - 2.0), key=lambda q: abs(q[2] + keeper[2]))[:2]
        for q in receivers:
            for lead in (3.0, 7.0):
                tx, ty = self._target(max(q[1], keeper[1] + 2.0) + lead, _clip(-keeper[2] * 0.6 + q[2] * 0.25, -8.0, 8.0))
                option = self._x_direct(p, bx, by, vx, vy, q, friends, opponents, tx, ty, 20.0)
                if option is None:
                    continue
                point = option[3][1:]
                if point[0] < keeper[1] + 1.0 or abs(point[1]) > 12.0:
                    continue
                if best is None or option[0] > best[0]:
                    best = option
        return best

    def _base_choose_kick(self, p, bx, by, vx, vy, friends, opponents):
        fallback = self._v10_choose_kick(p, bx, by, vx, vy, friends, opponents)
        if not hasattr(self, '_x_obs') or fallback is None:
            return fallback
        motion = self._touch_movement or self._move(p, (bx + 0.3, by))
        launch = self._carrier_contact(p, bx, by, *self._requested_velocity(vx, vy, fallback), motion)
        if launch is not None and self._goal_path(launch) is not None:
            return fallback
        plan = self._bank_plan or self._pass_plan
        if plan is not None and plan[1] >= bx + 4.0:
            return fallback
        option = None
        name = None
        if option is None:
            option = self._x_trap(p, bx, by, vx, vy, friends, opponents)
            name = 'trap_pass'
        if option is None:
            return fallback
        floor = 1.2
        if plan is not None:
            floor = 2.0
        elif launch is not None and math.hypot(launch[2], launch[3]) <= 10.5:
            carry = self._touch_path(p, bx, by, vx, vy, fallback, motion, opponents)
            if carry is not None:
                floor = max(floor, carry[0] * 0.55 + 0.8)
        if option[0] <= floor:
            return fallback
        self._touch_movement = option[2]
        self._pass_plan = option[3]
        self._bank_plan = option[3] if name == 'pinball_pass' else None
        self._x_proposal = (name, option[3][0], option[4], p[0])
        return option[1]

    def _relay_live_race(self, tick, receiver, ball, opponents, first_move=None):
        plan = self._relay_receive
        if plan is None or plan != self._receive_plan or tick >= plan[2]:
            return (None, None)
        until = min(self.RELAY_LOOKAHEAD_TICKS * self._dt, (plan[2] - tick) * self._dt)
        old_touch, old_hold = (self.FIRST_TOUCH, self.HOLD_RECEPTION)
        self.FIRST_TOUCH = True
        self.HOLD_RECEPTION = True
        try:
            path = self._pass_path(ball, until=until)
            race = self._pass_race(receiver, path, opponents, self.RELAY_MARGIN, until=until, first_move=first_move)
            return (path, race)
        finally:
            self.FIRST_TOUCH = old_touch
            self.HOLD_RECEPTION = old_hold

    def _cooldown_handoff(self, p, bx, by, vx, vy, friends, opponents, pressure):
        if p[0] == 0 or bx < self._left + 14.0 or bx > self._right - 6.0 or (abs(by) > self._half_height - 4.0) or (pressure > self.RELAY_PRESSURE):
            return None
        candidates = []
        for q in friends:
            if q[0] in (0, p[0], self._shape_cover_id) or self._friend_cooldowns.get(q[0], 1) != 0:
                continue
            gap = math.hypot(q[1] - bx, q[2] - by)
            if 1.2 < gap < 5.5 and math.hypot(q[1] - p[1], q[2] - p[2]) > 2.05:
                candidates.append((gap, q))
        candidates.sort(key=lambda item: item[0])
        movement = self._move(p, (bx + 0.3, by))
        horizon = self.RELAY_LOOKAHEAD_TICKS * self._dt
        best = None
        for _, q in candidates[:self.RELAY_RECEIVER_LIMIT]:
            if self._search_expired():
                return best
            tx, ty = self._target(q[1] + q[3] * 0.1, q[2] + q[4] * 0.1)
            ux, uy = _unit(tx - bx, ty - by)
            for speed in (6.0, 9.0):
                kick = self._kick_to_velocity(vx, vy, ux * speed, uy * speed)
                if kick is None:
                    continue
                launch = self._carrier_contact(p, bx, by, *self._requested_velocity(vx, vy, kick), movement)
                if launch is None:
                    continue
                collect = self._x_collect(p, launch, (bx, by), q, friends, opponents, self._dt, horizon)
                if collect is None:
                    continue
                score, point, aim, arrival = collect
                if arrival > self.RELAY_MAX_TICKS * self._dt + 1e-09 or point[0] < bx - 0.75:
                    continue
                room = min((math.hypot(point[0] - o[1] - o[3] * arrival, point[1] - o[2] - o[4] * arrival) for o in opponents), default=20.0)
                progress = math.hypot(self._right - bx, by) - math.hypot(self._right - point[0], point[1])
                if room < 2.6 or (progress < 0.6 and room < pressure + 1.0):
                    continue
                path = self._pass_path(launch, (bx, by), horizon)
                if any((self._pass_reachable(p, x, y, int(round(t * self._hz)), self._contact) for t, x, y in path if self._dt < t < arrival - 1e-09)):
                    continue
                receiver_move = self._move(q, self._target(*aim))
                projected = []
                for player, move in ((p, movement), (q, receiver_move)):
                    px = player[3] * self._damping + move[0] * self._acc
                    py = player[4] * self._damping + move[1] * self._acc
                    velocity = math.hypot(px, py)
                    if velocity > self._speed:
                        px *= self._speed / velocity
                        py *= self._speed / velocity
                    projected.append((player[1] + px * self._dt, player[2] + py * self._dt))
                if math.hypot(projected[0][0] - projected[1][0], projected[0][1] - projected[1][1]) < 2.05:
                    continue
                score += 0.25 + progress * 0.08 + min(max(0.0, room - pressure), 3.0) * 0.1
                if best is None or score > best[0]:
                    best = (score, kick, movement, (q[0], *point), aim)
        return best

    def _choose_kick(self, p, bx, by, vx, vy, friends, opponents):
        self._relay_proposal = None
        self._relay_fallback = None
        fallback = self._base_choose_kick(p, bx, by, vx, vy, friends, opponents)
        pressure = min((math.hypot(o[1] - bx, o[2] - by) for o in opponents), default=100.0)
        if p[0] == 0 or pressure > self.RELAY_PRESSURE or self._bank_plan is not None or (self._pass_plan is not None) or (self._receive_plan is not None and self._receive_plan[0] != p[0]):
            return fallback
        motion = self._touch_movement or self._move(p, (bx + 0.3, by))
        launch = None
        if fallback is not None:
            launch = self._carrier_contact(p, bx, by, *self._requested_velocity(vx, vy, fallback), motion)
            if launch is not None and self._goal_path(launch) is not None:
                return fallback
        option = self._cooldown_handoff(p, bx, by, vx, vy, friends, opponents, pressure)
        if option is None:
            return fallback
        floor = 0.75
        if launch is not None and math.hypot(launch[2], launch[3]) <= 10.5:
            carry = self._touch_path(p, bx, by, vx, vy, fallback, motion, opponents)
            if carry is not None:
                floor = max(floor, carry[0] * 0.55 + 0.25)
        if option[0] <= floor:
            return fallback
        self._touch_movement = option[2]
        self._pass_plan = option[3]
        self._bank_plan = None
        self._relay_proposal = (option[3][0], p[0])
        self._relay_fallback = (fallback, motion)
        self._x_proposal = None
        self._x_reception = None
        return option[1]

    def act(self, obs):
        lead = obs.score[0] - obs.score[1]
        if self.LOCK_LEAD > 0 and self.LOCK_LEAD <= lead <= self.LOCK_MAX and (obs.time_remaining <= self.LOCK_TIME):
            return self._lock_wall(obs)
        actions = self._act_normal(obs)
        if self.WALL_BREAK:
            self._wall_break(obs, actions)
        return actions

    def _wall_break(self, obs, actions):
        gx = obs.opponent_goal[0]
        field = obs.field
        r = field.player_radius
        wall = [q for q in obs.opponents if abs(q.position[0] - gx) <= 3.0 and abs(q.position[1]) <= 9.0]
        if len(wall) < 4:
            return
        bx, by = obs.ball.position
        if bx < 0.0:
            return
        hw = field.goal_width * 0.5
        br = field.ball_radius
        ys = sorted((q.position[1] for q in wall))
        gaps = []
        lo = -hw
        for y in ys + [hw + r]:
            hi = min(y - r, hw)
            if hi - lo > 0.0:
                gaps.append((hi - lo, (lo + hi) * 0.5))
            lo = max(lo, y + r)
        if not gaps:
            return
        width, cy = max(gaps)
        friends = sorted(obs.my_players, key=lambda q: q.id)
        shooter = None
        if width >= 2.0 * br + 0.25 and bx > gx - 40.0:
            tx, ty = (gx, cy)
            kx, ky = (tx - bx, ty - by)
            n = math.hypot(kx, ky)
            if n > 1e-06:
                ux, uy = (kx / n, ky / n)
                clear = True
                for q in obs.opponents:
                    qx, qy = (q.position[0] - bx, q.position[1] - by)
                    t = qx * ux + qy * uy
                    if t < 0.0:
                        continue
                    if t > n:
                        t = n
                    if math.hypot(qx - ux * t, qy - uy * t) < r + br + 0.12:
                        clear = False
                        break
                if clear:
                    for p in friends:
                        if obs.can_kick(p.id):
                            old = actions.players[p.id]
                            actions.set(p.id, PlayerAction(movement=old.movement, kick_direction=(ux, uy), kick_power=1.0))
                            shooter = p.id
                            break
        if shooter is not None:
            return
        outfield = friends[1:]
        if len(outfield) < 2:
            return
        chaser = min(outfield, key=lambda q: math.hypot(q.position[0] - bx, q.position[1] - by))
        pushers = [q for q in outfield if q.id != chaser.id]
        targets = sorted(wall, key=lambda q: abs(q.position[1] - cy))[:len(pushers)]
        pushers.sort(key=lambda q: q.position[1])
        targets.sort(key=lambda q: q.position[1])
        for p, q in zip(pushers, targets):
            dx, dy = (q.position[0] - p.position[0], q.position[1] - p.position[1])
            d = math.hypot(dx, dy)
            if d > 1e-06:
                actions.set(p.id, PlayerAction(movement=(dx / d, dy / d)))

    def _lock_wall(self, obs):
        actions = TeamAction()
        gx = obs.my_goal[0] + obs.field.player_radius + 0.2
        players = sorted(obs.my_players, key=lambda q: q.id)
        n = len(players)
        hypot = math.hypot
        for i, p in enumerate(players):
            ty = (i - (n - 1) * 0.5) * self.LOCK_SPACING
            dx, dy = (gx - p.position[0], ty - p.position[1])
            d = hypot(dx, dy)
            # Stiff wall: drive back to the slot at full speed until within 0.2 of it (was 1.5),
            # so attackers cannot shove the wall apart.
            s = 1.0 if d > 0.2 else d / 0.2
            move = (dx / d * s, dy / d * s) if d > 1e-06 else (0.0, 0.0)
            if obs.can_kick(p.id):
                actions.set(p.id, PlayerAction(movement=move, kick_direction=(1.0, 0.0), kick_power=1.0))
            else:
                actions.set(p.id, PlayerAction(movement=move))
        return actions

    def _act_normal(self, obs):
        enabled = True
        if not enabled:
            return self._v10_act(obs)
        friends, opponents = self._x_prepare(obs)
        actions = self._v10_act(obs, friends, opponents)
        if not friends:
            return actions
        protected = self._receive_plan[0] if self._receive_plan is not None else None
        bx, by = obs.ball.position
        if self._x_proposal is not None:
            name, rid, aim, pid = self._x_proposal
            if protected == rid and self._receive_plan[1] == pid:
                self._x_reception = (rid, pid, obs.tick + int(2.6 * self._hz), aim)
                receiver = next((p for p in friends if p[0] == rid), None)
                if receiver is not None:
                    actions.set(rid, PlayerAction(movement=self._move(receiver, self._target(*aim))))
                self._x_event(name)
        elif self._x_reception is not None:
            rid, pid, expiry, aim = self._x_reception
            if protected != rid or obs.tick > expiry or obs.ball.last_touch not in (None, pid):
                self._x_reception = None
            else:
                receiver = next((p for p in friends if p[0] == rid), None)
                if receiver is not None and actions.players[rid].kick_direction is None:
                    path = self._pass_path((*obs.ball.position, *obs.ball.velocity))
                    move = self._move(receiver, self._target(*aim))
                    race = self._pass_race(receiver, path, opponents, first_move=move)
                    if race is not None:
                        aim = self._next_receive_aim or race[0][1]
                        move = self._move(receiver, self._target(*aim))
                        if self._pass_race(receiver, path, opponents, first_move=move) is not None:
                            actions.set(rid, PlayerAction(movement=move))
                            self._x_reception = (rid, pid, expiry, aim)
                            self._x_event('tactic_receive_run')
        if self._x_rush and protected is None and (obs.ball.controlling_team == 0):
            eligible = [p for p in friends[1:] if p[0] not in (self._chaser, self._shape_cover_id) and actions.players[p[0]].kick_direction is None and (p[1] > bx - 5.0)]
            if eligible:
                q = max(eligible, key=lambda p: p[1])
                keeper = opponents[0]
                target = self._target(max(q[1], keeper[1]) + 3.0, _clip(-keeper[2] * 0.6, -7.0, 7.0))
                actions.set(q[0], PlayerAction(movement=self._move(q, target)))
                self._x_event('trap_run')
        if self._x_events:
            actions.debug['titan_x'] = tuple(self._x_events)
        return actions

    def _scout_goal_bound(self, obs):
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        if vx >= -8.0 or math.hypot(vx, vy) < 12.0:
            return False
        n = self._crossing_ticks(bx, vx, -self._left - self._ball_radius)
        if n > 26:
            return False
        gy = by + vy * (self._left + self._ball_radius - bx) / vx
        return abs(gy) <= self._mouth + 0.6

    def _scout_keeper_limit(self, obs):
        return self._half_height - 2.0 if self._scout_goal_bound(obs) and (not self._scout_home_priority) else self._mouth

    def _scout_keeper_x(self, obs, keeper):
        self._scout_home_priority = False
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        depth = _clip((bx - self._left) * 0.22, 2.2, max(2.2, self.SCOUT_KEEPER_CAP))
        x = self._left + depth
        if depth > 2.21:
            self._x_event('scout_keeper_advanced')
        if self._scout_goal_bound(obs):
            home_x = self._left + 2.2
            home_y = _clip(by + vy * (home_x - bx) / vx, -self._mouth, self._mouth)
            line_y = _clip(by + vy * (x - bx) / vx, -self._half_height + 2.0, self._half_height - 2.0)
            cooldown = obs.my_players[0].kick_cooldown_ticks
            home = self._keeper_reaches(keeper, bx, by, vx, vy, (home_x, home_y), False, cooldown)
            line = self._keeper_reaches(keeper, bx, by, vx, vy, (x, line_y), False, cooldown)
            if home and (not line):
                self._scout_home_priority = True
                return home_x
        return x

    def _scout_support(self, obs, friends, opponents, chaser, races, enemy_eta, targets, protected):
        if protected:
            return
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        recipient = self._receive_plan[0] if self._receive_plan is not None else None
        free = [p for p in friends[1:] if p[0] not in (chaser[0], self._shape_cover_id, recipient) and (not obs.can_kick(p[0]))]
        if len(free) < 2:
            self._scout_outlet = None
            return
        if self.SCOUT_CUTBACK and bx > 22.0 and (abs(by) > 12.0):
            secure = obs.ball.controlling_team == 0 or races[chaser[0]][0] + 0.15 < enemy_eta
            if secure:
                tx = min(bx - 6.0, self._right - 18.0)
                target = self._target(tx, by * 0.12)
                q = min(free, key=lambda p: self._eta(p, *target))
                targets[q[0]] = target
                self._x_event('scout_cutback')
                return
        return
        if not -25.0 < bx < 10.0 or vx < -8.0 or obs.ball.controlling_team == 0 or (sum((q[1] < self._left + 24.0 and abs(q[2]) < 14.0 for q in opponents[1:])) > 1):
            self._scout_outlet = None
            return
        eligible = [p for p in free if not (targets[p[0]][0] < -15.0 and abs(targets[p[0]][1]) < 12.0)]
        if not eligible:
            self._scout_outlet = None
            return
        old = self._scout_outlet
        q = next((p for p in eligible if old is not None and p[0] == old[0] and (obs.tick <= old[2])), None)
        if q is None:
            q = max(eligible, key=lambda p: p[1] + (2.0 if p[0] == 4 else 0.0))
            side = -1.0 if by > 0.0 else 1.0
            self._scout_outlet = (q[0], side, obs.tick + int(2.0 * self._hz))
        side = self._scout_outlet[1]
        targets[q[0]] = self._target(max(bx + 22.0, -3.0), side * 17.0)
        self._x_event('scout_outlet')

# Plays against a goal-line wall. Only used after AdaptiveChampion detects one.
class _SpecialistPolicy(_Core):
    name = 'TITAN Counter Lab'
    version = 'clearance-counter-scored-tie-bait-v1'
    LINK_MARGIN = 0.1

    def _bait_base_reset(self, seed):
        self._enemy_cooldowns = {}
        self._friend_cooldowns = {}
        self._receive_aim = None
        self._next_receive_aim = None
        self._last_pass_motion = None
        self._runtime_path = None
        self._runtime_steps = None
        self._runtime_queries = {}
        self._mark_assignments = {}
        self._bank_plan = None
        self._bank_receive = None
        self._ready = False
        self._restart_until = -1
        self._restart_owner = None
        self._chaser = -1
        self._last_score = None
        self._touch_movement = None
        self._pass_plan = None
        self._receive_plan = None
        self._transition_owner = None
        self._transition_until = -1
        self._transition_last_touch = None
        self._transition_holder = None
        self._transition_score = None
        self._transition_tick = None
        self._transition_active = False
        self._press_until = -1
        self._press_origin = None
        self._press_contact_owner = None
        self._press_last_ball_touch = None
        self._press_last_ball_holder = None
        self._press_own_contact_tick = -100000

    def _setup(self, field):
        self._dt = 1.0 / field.simulation_hz
        self._hz = field.simulation_hz
        self._speed = field.max_speed
        self._acc = field.acceleration * self._dt
        self._friction = field.ball_friction
        self._log_friction = math.log(self._friction)
        self._impulse = field.kick_impulse
        self._range = field.kick_range
        self._eta_range = self._range * 0.8
        self._left = field.my_goal[0]
        self._right = field.opponent_goal[0]
        self._half_height = field.height * 0.5
        self._goal_half = field.goal_width * 0.5
        self._mouth = max(0.0, field.goal_width * 0.5 - 0.6)
        self._circle = field.centre_circle_radius
        self._ball_radius = field.ball_radius
        self._contact = field.player_radius + field.ball_radius
        self._damping = 0.9
        self._wall = 0.75
        self._ball_cap = 30.0
        self._drag = tuple((self._friction ** tick for tick in range(81)))
        self._roll = tuple((self._dt * (1.0 - drag) / (1.0 - self._friction) for drag in self._drag))
        self._forecast_steps = tuple(((tick * self._dt, self._roll[tick]) for tick in (0, 2, 4, 6, 9, 12, 16, 20, 25, 31, 38, 47, 58, 70, 80)))
        self._reach_table = tuple(((self._dt * self._damping * (1.0 - self._damping ** n) / (1.0 - self._damping), self._dt * self._acc / (1.0 - self._damping) * (n - self._damping * (1.0 - self._damping ** n) / (1.0 - self._damping))) for n in range(83)))
        self._runtime_path = None
        self._runtime_steps = None
        self._runtime_queries = {}
        self._ready = True

    def _intercept(self, p, samples):
        _, px, py, pvx, pvy = p
        best = None
        for t, x, y in samples:
            dx, dy = (x - px, y - py)
            d = math.hypot(dx, dy)
            n = max(0, int(round(t * self._hz)))
            if n == 0:
                feasible = d <= self._eta_range
            else:
                coast, reach = self._reach_table[n]
                feasible = d <= self._speed * t + self._eta_range and math.hypot(dx - pvx * coast, dy - pvy * coast) <= reach + self._eta_range
            if feasible:
                return (t, (x, y))
            cost = self._eta(p, x, y) + t * 0.12
            if best is None or cost < best[0]:
                best = (cost, (x, y))
        return best

    def _touch_path(self, p, bx, by, vx, vy, kick, movement, opponents):
        sx, sy = self._requested_velocity(vx, vy, kick)
        contact = self._carrier_contact(p, bx, by, sx, sy, movement)
        if contact is None:
            return None
        x, y, sx, sy = contact
        pvx = p[3] * self._damping + movement[0] * self._acc
        pvy = p[4] * self._damping + movement[1] * self._acc
        player_speed = math.hypot(pvx, pvy)
        if player_speed > self._speed:
            pvx *= self._speed / player_speed
            pvy *= self._speed / player_speed
        px, py = (p[1] + pvx * self._dt, p[2] + pvy * self._dt)
        initial_distance = math.hypot(self._right - bx, by)
        margin = 4.0
        recapture = None
        cooldowns = getattr(self, '_enemy_cooldowns', {})
        for tick in range(1, 12):
            elapsed = tick * self._dt
            if abs(y) > self._half_height - 1.0 or x < self._left + 2.0:
                return None
            steps = tick + 1
            coast, reach = self._reach_table[steps]
            for enemy in opponents:
                if cooldowns.get(enemy[0], 0) > tick:
                    continue
                cx = enemy[1] + enemy[3] * coast
                cy = enemy[2] + enemy[4] * coast
                remaining = math.hypot(x - cx, y - cy) - reach - self._range
                margin = min(margin, remaining / self._speed)
            gap = math.hypot(x - px, y - py)
            if tick >= 5 and gap < self._range - 0.15:
                recapture = elapsed
                break
            if tick == 11:
                break
            player = (p[0], px, py, pvx, pvy)
            chase = self._target(x + sx * 0.15, y + sy * 0.15)
            move = self._move(player, chase)
            pvx = pvx * self._damping + move[0] * self._acc
            pvy = pvy * self._damping + move[1] * self._acc
            player_speed = math.hypot(pvx, pvy)
            if player_speed > self._speed:
                pvx *= self._speed / player_speed
                pvy *= self._speed / player_speed
            px += pvx * self._dt
            py += pvy * self._dt
            x += sx * self._dt
            y += sy * self._dt
            sx *= self._friction
            sy *= self._friction
            dx, dy = (x - px, y - py)
            gap = math.hypot(dx, dy)
            if 1e-08 < gap < self._contact:
                nx, ny = (dx / gap, dy / gap)
                x, y = (px + nx * self._contact, py + ny * self._contact)
                closing = (sx - pvx) * nx + (sy - pvy) * ny
                if closing < 0.0:
                    sx -= 1.25 * closing * nx
                    sy -= 1.25 * closing * ny
        if recapture is None:
            recapture = 0.55 + self._eta((p[0], px, py, pvx, pvy), x, y)
        progress = initial_distance - math.hypot(self._right - x, y)
        clearance = min((math.hypot(x - q[1] - q[3] * 0.25, y - q[2] - q[4] * 0.25) for q in opponents), default=15.0)
        score = progress * 0.85 + min(clearance, 8.0) * 0.25 + _clip(margin, -0.6, 0.6) * 8.0 - max(0.0, recapture - 0.25) * 8.0
        return (score, margin, recapture)

    def _opening_act(self, obs):
        if not self._ready:
            self._setup(obs.field)
            self._restart_until = obs.tick + int(3.0 * self._hz)
            self._restart_owner = obs.ball.controlling_team
        score = obs.score
        if self._last_score is not None and score != self._last_score:
            self._restart_until = obs.tick + int(3.0 * self._hz)
            self._restart_owner = 0 if score[1] > self._last_score[1] else 1
            self._chaser = -1
            self._receive_plan = None
            self._bank_receive = None
            self._receive_aim = None
            self._mark_assignments = {}
            self._press_until = -1
            self._press_origin = None
            self._press_contact_owner = None
            self._press_own_contact_tick = -100000
            self._press_last_ball_touch = None
            self._press_last_ball_holder = None
        self._last_score = score
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        if math.hypot(bx, by) > 0.7 or math.hypot(vx, vy) > 0.15:
            self._restart_until = -1
        protected = obs.tick < self._restart_until and self._restart_owner == 1
        friends = [(p.id, *p.position, *p.velocity) for p in obs.my_players]
        opponents = [(p.id, *p.position, *p.velocity) for p in obs.opponents]
        self._enemy_cooldowns = {p.id: p.kick_cooldown_ticks for p in obs.opponents}
        self._friend_cooldowns = {p.id: p.kick_cooldown_ticks for p in obs.my_players}
        actions = TeamAction(debug={'roles': self.PLAYER_ROLES})
        if not friends:
            return actions
        keeper = friends[0]
        outfield = friends[1:] or friends
        samples = self._trajectory(bx, by, vx, vy)
        races = {}
        chaser = None
        chaser_eta = None
        previous = None
        for p in outfield:
            race = self._intercept(p, samples)
            races[p[0]] = race
            if chaser is None or race[0] < chaser_eta:
                chaser, chaser_eta = (p, race[0])
            if p[0] == self._chaser:
                previous = p
        if previous is not None and races[previous[0]][0] < races[chaser[0]][0] + 0.12:
            chaser = previous
        self._chaser = chaser[0]
        enemy_eta = None
        for o in opponents:
            eta = self._intercept(o, samples)[0]
            if enemy_eta is None or eta < enemy_eta:
                enemy_eta = eta
        if enemy_eta is None:
            enemy_eta = 100.0
        self._transition_observe(obs, protected, friends, opponents, (min((v[0] for k, v in races.items() if k != 0), default=100.0), enemy_eta))
        attack = races[chaser[0]][0] <= enemy_eta + 0.12
        keeper_x = self._left + 2.2
        keeper_y = by * 2.2 / max(3.0, bx - self._left)
        if self.PREDICTIVE_KEEPER and vx < -8.0 and (math.hypot(vx, vy) >= 12.0) and (bx > keeper_x):
            time_to_line = (keeper_x - bx) / vx
            if 0.0 < time_to_line < 1.25:
                keeper_y = by + vy * time_to_line
        keeper_target = (keeper_x, _clip(keeper_y, -self._mouth, self._mouth))
        sweep = bx < self._left + 10.0 and self._eta(keeper, bx, by) < races[chaser[0]][0] * 0.85
        if sweep and abs(by) > self._mouth + 1.0:
            ours = self._eta(keeper, bx, by)
            theirs = min((self._eta(o, bx, by) for o in opponents), default=100.0)
            away = obs.ball.last_touch == keeper[0] and vx > 6.0 and ((bx - keeper[1]) * vx + (by - keeper[2]) * vy > 0.0)
            sweep = not away and ours <= 1.1 and (ours + 0.2 < theirs)
        if self.KEEPER_PRIORITY and self.PREDICTIVE_KEEPER and (vx < -8.0) and (math.hypot(vx, vy) >= 12.0) and (bx > keeper_x):
            flight = (keeper_x - bx) / vx
            if 0.0 < flight < 0.55:
                goal_y = by + vy * (self._left + self._ball_radius - bx) / vx
                opposite = (keeper_target[1] - keeper[2]) * (by - keeper[2]) < 0.0
                if abs(goal_y) <= self._mouth + 0.6 and opposite:
                    cooldown = obs.my_players[0].kick_cooldown_ticks
                    line = self._keeper_reaches(keeper, bx, by, vx, vy, keeper_target, False, cooldown)
                    rush = self._keeper_reaches(keeper, bx, by, vx, vy, keeper_target, True, cooldown)
                    if line and (not rush):
                        sweep = False
        if self.KEEPER_RECOVERY:
            outgoing = obs.ball.last_touch == keeper[0] and vx > 10.0 and (self._receive_plan is not None) and (self._receive_plan[1] == keeper[0]) and (math.hypot(bx - keeper[1], by - keeper[2]) > self._range + 0.3)
            if outgoing:
                receiver_id = self._receive_plan[0]
                receiver = next((p for p in outfield if p[0] == receiver_id), None)
                safe = receiver is not None and races[receiver_id][0] + 0.12 < enemy_eta
                if safe:
                    sweep = False
        if sweep:
            keeper_target = self._target(bx, by)
        targets = {keeper[0]: keeper_target, chaser[0]: self._target(*races[chaser[0]][1])}
        free = [p for p in outfield if p[0] != chaser[0]]
        self._shape_cover_id = None
        if free:
            cover_target = self._target(min(28.0, bx - 2.0), _clip(by, -self._half_height + 2.0, self._half_height - 2.0))
            cover = self._role_closest_eta(free, cover_target, cover=True)
            if cover[0] == 1:
                cover_target = self._target(min(28.0, bx - 3.5), cover_target[1])
            elif cover[0] == 2:
                cover_target = self._target(min(28.0, bx - 2.75), cover_target[1])
            targets[cover[0]] = cover_target
            self._shape_cover_id = cover[0]
            free = [p for p in free if p[0] != cover[0]]
        if attack:
            spread = max(7.0, 15.0 - max(0.0, bx - 20.0) * 0.35)
            free.sort(key=lambda p: p[2])
            for index, p in enumerate(free):
                lane = 0.0 if len(free) == 1 else -spread + 2.0 * spread * index / (len(free) - 1)
                targets[p[0]] = self._role_support(p, bx, by, lane)
        else:
            threats = sorted(opponents, key=lambda p: p[1] + abs(p[2]) * 0.2)
            for threat in threats:
                if not free:
                    break
                if math.hypot(threat[1] - bx, threat[2] - by) < 3.5:
                    continue
                ux, uy = _unit(self._left - threat[1], -threat[2])
                target = self._target(threat[1] + ux * 3.0, threat[2] + uy * 3.0)
                marker = self._choose_marker(free, target, threat[0], obs.tick) if self.MARK_HANDOFF else self._role_closest_eta(free, target)
                targets[marker[0]] = target
                free = [p for p in free if p[0] != marker[0]]
            for p in free:
                targets[p[0]] = self._target(bx - 9.0, p[2] * 0.5)
        self._transition_support(bx, by, friends, opponents, chaser[0], targets)
        actions.debug['text'] = 'Klopp quick transition' if self._transition_active else 'Pep positional control'
        press_targets = self._counterpress_targets(obs, bx, by, vx, vy, outfield, opponents, races, chaser, enemy_eta, protected, targets)
        if press_targets is not None:
            targets.update(press_targets)
            actions.debug['text'] = 'Klopp brief counterpress; Pep cover'
        receive_target = None
        receive_path = None
        if self._receive_plan is not None:
            recipient, passer, expiry = self._receive_plan
            recipient_player = next((p for p in outfield if p[0] == recipient), None)
            if recipient_player is None or obs.tick > expiry or obs.ball.last_touch not in (None, passer) or (math.hypot(vx, vy) < 9.0):
                self._receive_plan = None
                self._bank_receive = None
                self._receive_aim = None
            else:
                path = self._pass_path((bx, by, vx, vy))
                receive_path = path
                verified = self._pass_race(recipient_player, path, opponents)
                if verified is None:
                    self._receive_plan = None
                    self._bank_receive = None
                    self._receive_aim = None
                else:
                    race, _ = verified
                    aim = self._next_receive_aim or race[1]
                    targets[recipient] = self._target(*aim)
                    receive_target = (recipient, aim)
                    self._receive_aim = receive_target
                    if self._bank_receive is not None:
                        self._bank_receive = (recipient, passer, race[1])
        if self.MARK_HANDOFF and attack and (not protected) and (enemy_eta < races[chaser[0]][0] + 0.1):
            self._retain_mark(obs, friends, opponents, chaser, targets)
        if self.COVER_SHAPE and (not protected):
            self._cover_shape(obs, friends, opponents, chaser, races, enemy_eta, targets)
        carrier = None
        carrier_gap = None
        for p in friends:
            if obs.can_kick(p[0]):
                gap = math.hypot(p[1] - bx, p[2] - by)
                if carrier is None or gap < carrier_gap:
                    carrier, carrier_gap = (p, gap)
        launched_pass = None
        for p in friends:
            target = targets.get(p[0], (p[1], p[2]))
            if protected and math.hypot(p[1], p[2]) < self._circle + 5.0:
                ux, uy = _unit(p[1], p[2])
                target = (ux * (self._circle + 3.0), uy * (self._circle + 3.0))
            kick = None
            if carrier is not None and p[0] == carrier[0] and (not protected):
                movement = self._move(p, (bx + 0.3, by))
                nx = p[3] * self._damping + movement[0] * self._acc
                ny = p[4] * self._damping + movement[1] * self._acc
                speed = math.hypot(nx, ny)
                if speed > self._speed:
                    nx *= self._speed / speed
                    ny *= self._speed / speed
                distance_next = math.hypot(p[1] + nx * self._dt - bx, p[2] + ny * self._dt - by)
                if distance_next < self._range - 0.18:
                    kick = self._choose_kick(p, bx, by, vx, vy, friends, opponents)
                    if self._touch_movement is not None:
                        movement = self._touch_movement
                    self._receive_plan = None
                    self._bank_receive = None
                    self._receive_aim = None
                    plan = self._bank_plan or self._pass_plan
                    if kick is not None and plan is not None:
                        recipient = plan[0]
                        sx, sy = self._requested_velocity(vx, vy, kick)
                        launch = self._carrier_contact(p, bx, by, sx, sy, movement)
                        receiver = next((q for q in outfield if q[0] == recipient), None)
                        if launch is not None and receiver is not None and (math.hypot(launch[2], launch[3]) > 10.5):
                            path = self._pass_path(launch, (bx, by), 2.6)
                            verified = self._pass_race(receiver, path, opponents, after=self._dt, until=2.6)
                            if verified is not None:
                                receiver_race, _ = verified
                                aim = self._next_receive_aim or receiver_race[1]
                                launched_pass = (recipient, aim)
                                self._receive_aim = launched_pass
                                self._receive_plan = (recipient, p[0], obs.tick + int(2.6 * self._hz))
                                if self._bank_plan is not None:
                                    self._bank_receive = (recipient, p[0], receiver_race[1])
            else:
                movement = self._move(p, target, friends if p[0] != chaser[0] and p[0] != 0 else ())
            if p[0] != 0 and launched_pass is None and (receive_path is not None) and (self._receive_plan is not None) and (self._receive_plan[0] == p[0]) and (carrier is None or carrier[0] != p[0]):
                check = self._pass_race(p, receive_path, opponents, first_move=movement)
                if check is None:
                    self._receive_plan = None
                    self._bank_receive = None
                    self._receive_aim = None
            if kick is None:
                actions.set(p[0], PlayerAction(movement=movement))
            else:
                actions.set(p[0], PlayerAction(movement=movement, kick_direction=kick[0], kick_power=kick[1]))
        if launched_pass is not None:
            recipient, target = launched_pass
            receiver = next((p for p in outfield if p[0] == recipient))
            actions.set(recipient, PlayerAction(movement=self._move(receiver, self._target(*target))))
        return actions

    def _goal_path(self, launch):
        x, y, vx, vy = launch
        path = [(self._dt, x, y)]
        wall = self._half_height - self._ball_radius
        goal = self._right - self._ball_radius
        for tick in range(2, 61):
            oldx, oldy = (x, y)
            x += vx * self._dt
            y += vy * self._dt
            if abs(y) > wall:
                side = 1.0 if y > 0.0 else -1.0
                y = side * wall * 2.0 - y
                vy = -side * abs(vy) * self._wall
            if x >= goal and vx > 0.0:
                fraction = (goal - oldx) / max(1e-09, x - oldx)
                gy = oldy + (y - oldy) * fraction
                if abs(gy) > self._mouth + 0.15:
                    return None
                time = (tick - 1 + fraction) * self._dt
                path.append((time, goal, gy))
                return (path, (time, gy, math.hypot(vx, vy)))
            if x <= self._left + self._ball_radius:
                return None
            vx *= self._friction
            vy *= self._friction
            if tick % 2 == 0:
                path.append((tick * self._dt, x, y))
        return None

    def _before_endwall(self, p, bx, by, vx, vy, friends, opponents):
        fallback = self._legacy_policy_kick(p, bx, by, vx, vy, friends, opponents)
        pressure = min((math.hypot(q[1] - bx, q[2] - by) for q in opponents), default=100.0)
        fallback_plan = self._pass_plan
        fallback_bank = self._bank_plan
        fallback_move = self._touch_movement
        best = None
        blocked_shot = False
        if bx > self._right - 40.0:
            for y in (-5.7, -3.0, 0.0, 3.0, 5.7):
                option = self._shot_option(p, bx, by, vx, vy, opponents, y)
                if option is not None and (best is None or option[0] > best[0]):
                    best = option
        link = self._search_links(p, bx, by, vx, vy, friends, opponents)
        if link is not None and (best is None or link[0] > best[0]):
            best = link
        old_score = -2.0
        if fallback is not None:
            sx, sy = self._requested_velocity(vx, vy, fallback)
            move = fallback_move or self._move(p, (bx + 0.3, by))
            launch = self._carrier_contact(p, bx, by, sx, sy, move)
            goal = self._goal_path(launch) if launch is not None and sx > 0.0 else None
            if goal is not None:
                path, (flight, gy, end_speed) = goal
                margin = min((self._eta(q, x, y) - t for t, x, y in path for q in opponents), default=1.0)
                contact = self._shot_contact_margin(bx, by, launch, opponents, flight)
                old_score = 6.0 + min(margin, 0.5) * 4.0 - flight * 0.7 + min(end_speed, 20.0) * 0.03
                if bx > self._right - 40.0 and fallback_plan is None and (fallback_bank is None) and (contact < -0.02 or margin < self.SHOT_MARGIN or self._early_body_margin(path, opponents, flight) < -0.06):
                    old_score = -2.0
                    blocked_shot = True
            elif fallback_plan is not None:
                receiver = next((q for q in friends if q[0] == fallback_plan[0]), None)
                if receiver is not None:
                    rated = self._link_option(p, bx, by, vx, vy, receiver, opponents, fallback_plan[1], fallback_plan[2], math.hypot(sx, sy))
                    old_score = rated[0] if rated is not None else -0.5
            elif math.hypot(sx, sy) <= 10.5:
                path = self._touch_path(p, bx, by, vx, vy, fallback, move, opponents)
                old_score = path[0] * 0.55 if path is not None else -2.0
        if blocked_shot:
            controlled = self._controlled_touch(p, bx, by, vx, vy, opponents)
            if controlled is not None:
                csx, csy = self._requested_velocity(vx, vy, controlled[1])
                control_launch = self._carrier_contact(p, bx, by, csx, csy, controlled[2])
                control_path = self._touch_path(p, bx, by, vx, vy, controlled[1], controlled[2], opponents)
                if control_launch is not None and control_path is not None and (self._shot_contact_margin(bx, by, control_launch, opponents, 0.15) >= -0.02):
                    candidate = (control_path[0] * 0.55, controlled[1], controlled[2], None)
                    if best is None or candidate[0] > best[0]:
                        best = candidate
        if best is not None and best[0] > old_score + self.OPTION_SWITCH_MARGIN:
            self._touch_movement = best[2]
            self._pass_plan = best[3]
            self._bank_plan = None
            return best[1]
        self._pass_plan = fallback_plan
        self._bank_plan = fallback_bank
        self._touch_movement = fallback_move
        return fallback

    def _choose_kick(self, p, bx, by, vx, vy, friends, opponents):
        fallback = self._before_endwall(p, bx, by, vx, vy, friends, opponents)
        if fallback is None or bx < 15.0 or abs(by) < 8.0:
            return fallback
        sx, sy = self._requested_velocity(vx, vy, fallback)
        move = self._touch_movement or self._move(p, (bx + 0.3, by))
        launch = self._carrier_contact(p, bx, by, sx, sy, move)
        if launch is not None:
            goal = self._goal_path(launch)
            if goal is not None:
                path, goal_details = goal
                margin = min((self._eta(q, x, y) - t for t, x, y in path for q in opponents), default=1.0)
                contact = self._shot_contact_margin(bx, by, launch, opponents, goal_details[0])
                if margin >= self.SHOT_MARGIN and contact >= -0.02 and (self._early_body_margin(path, opponents, goal_details[0]) >= -0.06):
                    return fallback
        option = self._endwall_link(p, bx, by, vx, vy, friends, opponents)
        if option is None:
            return fallback
        score = -2.0
        if self._pass_plan is not None:
            q = next((q for q in friends if q[0] == self._pass_plan[0]), None)
            rated = self._link_option(p, bx, by, vx, vy, q, opponents, self._pass_plan[1], self._pass_plan[2], math.hypot(sx, sy)) if q else None
            if rated is not None:
                score = rated[0]
        elif math.hypot(sx, sy) <= 10.5:
            rated = self._touch_path(p, bx, by, vx, vy, fallback, move, opponents)
            if rated is not None:
                score = rated[0] * 0.55
        if option[0] > score + 0.2:
            self._touch_movement = option[2]
            self._pass_plan = option[3]
            self._bank_plan = option[3]
            return option[1]
        return fallback

    def _bait_counter_act(self, obs):
        wall = [q for q in obs.opponents if q.position[0] > obs.opponent_goal[0] - 3.0 and abs(q.position[1]) < 9.0]
        if len(wall) >= 4:
            if not self._ready:
                self._setup(obs.field)
                self._restart_until = obs.tick + int(3.0 * self._hz)
                self._restart_owner = obs.ball.controlling_team
            return self._siege_act(obs, wall)
        return self._opening_act(obs)

    def _siege_goal(self, p, bx, by, vx, vy, movement, opponents):
        if bx < self._right - 12.0 or abs(by) < self._goal_half - 0.5:
            return None
        obs = self._siege_obs
        opponents = obs.opponents
        qstates = [(q.id, *q.position, *q.velocity) for q in opponents]
        frames = [qstates]
        count = len(qstates)
        for n in range(1, 13):
            moved = []
            for index, q in enumerate(frames[-1]):
                tx = self._right - obs.field.player_radius - 0.2
                ty = -(index - (count - 1) * 0.5) * 2.8
                dx, dy = (tx - q[1], ty - q[2])
                distance = math.hypot(dx, dy)
                scale = min(1.0, distance / 1.5) / distance if distance > 1e-08 else 0.0
                qvx = q[3] * self._damping + dx * scale * self._acc
                qvy = q[4] * self._damping + dy * scale * self._acc
                speed = math.hypot(qvx, qvy)
                if speed > self._speed:
                    qvx *= self._speed / speed
                    qvy *= self._speed / speed
                moved.append((q[0], _clip(q[1] + qvx * self._dt, self._left + 1.0, self._right - 1.0), _clip(q[2] + qvy * self._dt, -self._half_height + 1.0, self._half_height - 1.0), qvx, qvy))
            frames.append(moved)
        cache = self._siege_clearance_cache(p, movement, frames)
        side = 1.0 if by >= 0.0 else -1.0
        best = None
        for gy in (self._goal_half - 0.02, self._goal_half - 0.3, self._goal_half - 0.7):
            for ex in (0.1, 0.5, 1.0):
                ux, uy = _unit(self._right + ex - bx, side * gy - by)
                along = vx * ux + vy * uy
                lateral = max(0.0, vx * vx + vy * vy - along * along)
                if lateral >= self._impulse * self._impulse:
                    continue
                cap = min(self._ball_cap, along + math.sqrt(self._impulse * self._impulse - lateral))
                for ratio in (1.0, 0.88):
                    if self._search_expired():
                        return None if best is None else best[1]
                    kick = self._kick_to_velocity(vx, vy, ux * cap * ratio, uy * cap * ratio)
                    if kick is None:
                        continue
                    outcomes = [self._siege_clearance_path(p, (bx, by, vx, vy), movement, kick, frames, order, cache) for order in (False, True)]
                    if any((outcome is None for outcome in outcomes)):
                        continue
                    latest = max((outcome[0] for outcome in outcomes))
                    assisted = min((outcome[1] for outcome in outcomes))
                    score = 15.0 - latest * 0.2 + assisted * 0.03
                    if best is None or score > best[0]:
                        best = (score, kick)
        return None if best is None else best[1]

    def _siege_clearance_cache(self, p, movement, frames):
        obs = self._siege_obs
        cooldowns = tuple((q.kick_cooldown_ticks for q in obs.opponents))
        own = [p[1], p[2], p[3], p[4]]
        own[2] = own[2] * self._damping + movement[0] * self._acc
        own[3] = own[3] * self._damping + movement[1] * self._acc
        speed = math.hypot(own[2], own[3])
        if speed > self._speed:
            own[2] *= self._speed / speed
            own[3] *= self._speed / speed
        own[0] = _clip(own[0] + own[2] * self._dt, self._left + 1.0, self._right - 1.0)
        own[1] = _clip(own[1] + own[3] * self._dt, -self._half_height + 1.0, self._half_height - 1.0)
        body_frames = [None]
        for n in range(1, 13):
            coast = self._dt * self._damping * (1.0 - self._damping ** n) / (1.0 - self._damping)
            damping = self._damping ** n
            bodies = []
            for friend in obs.my_players:
                if friend.id == p[0]:
                    bodies.append(None)
                else:
                    bodies.append((friend.position[0] + friend.velocity[0] * coast, friend.position[1] + friend.velocity[1] * coast, friend.velocity[0] * damping, friend.velocity[1] * damping))
            enemy_bodies = [q[1:] for q in frames[n]]
            body_frames.append((tuple(bodies + enemy_bodies), tuple(enemy_bodies + bodies)))
        return (cooldowns, tuple(own), tuple(body_frames))

    def _siege_clearance_path(self, p, ball, movement, kick, frames, enemy_first, cache=None):
        x, y, vx, vy = ball
        if cache is None:
            cache = self._siege_clearance_cache(p, movement, frames)
        cooldowns = list(cache[0])
        own = list(cache[1])
        body_frames = cache[2]
        own_kick = (kick[0][0] * self._impulse * kick[1], kick[0][1] * self._impulse * kick[1])
        wall = self._half_height - self._ball_radius
        xwall = self._right - self._ball_radius
        assists = 0
        for n in range(1, 13):
            before = frames[n - 1]
            after = frames[n]
            intents = [i for i, q in enumerate(before) if cooldowns[i] == 0 and (x - q[1]) ** 2 + (y - q[2]) ** 2 <= self._range * self._range]
            if n > 1:
                move = self._move((p[0], *own), (x + vx * 0.1, y + vy * 0.1))
                own[2] = own[2] * self._damping + move[0] * self._acc
                own[3] = own[3] * self._damping + move[1] * self._acc
                speed = math.hypot(own[2], own[3])
                if speed > self._speed:
                    own[2] *= self._speed / speed
                    own[3] *= self._speed / speed
                own[0] = _clip(own[0] + own[2] * self._dt, self._left + 1.0, self._right - 1.0)
                own[1] = _clip(own[1] + own[3] * self._dt, -self._half_height + 1.0, self._half_height - 1.0)
            if n == 1 and (x - own[0]) ** 2 + (y - own[1]) ** 2 > self._range * self._range:
                return None
            kicks = []
            for index in intents:
                q = after[index]
                if (x - q[1]) ** 2 + (y - q[2]) ** 2 <= self._range * self._range:
                    kicks.append((-self._impulse, 0.0))
                    cooldowns[index] = 5
                    assists += 1
            if n == 1:
                if enemy_first:
                    kicks.append(own_kick)
                else:
                    kicks.insert(0, own_kick)
            for dx, dy in kicks:
                vx += dx
                vy += dy
                speed = math.hypot(vx, vy)
                if speed > self._ball_cap:
                    vx *= self._ball_cap / speed
                    vy *= self._ball_cap / speed
            x += vx * self._dt
            y += vy * self._dt
            vx *= self._friction
            vy *= self._friction
            if abs(y) > wall:
                sign = 1.0 if y > 0.0 else -1.0
                y = sign * 2.0 * wall - y
                vy = -sign * abs(vy) * self._wall
            if abs(x) > xwall and abs(y) > self._goal_half:
                sign = 1.0 if x > 0.0 else -1.0
                x = sign * 2.0 * xwall - x
                vx = -sign * abs(vx) * self._wall
            for body in body_frames[n][enemy_first]:
                px, py, pvx, pvy = own if body is None else body
                dx, dy = (x - px, y - py)
                gap = math.hypot(dx, dy)
                if 1e-08 < gap < self._contact:
                    nx, ny = (dx / gap, dy / gap)
                    x, y = (px + nx * self._contact, py + ny * self._contact)
                    closing = (vx - pvx) * nx + (vy - pvy) * ny
                    if closing < 0.0:
                        vx -= 1.25 * closing * nx
                        vy -= 1.25 * closing * ny
            if x > self._right and abs(y) <= self._goal_half:
                return (n, assists)
            if x < self._left and abs(y) <= self._goal_half:
                return None
            cooldowns = [max(0, c - 1) for c in cooldowns]
        return None

    def _siege_act(self, obs, wall):
        self._siege_obs = obs
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        friends = [(p.id, *p.position, *p.velocity) for p in obs.my_players]
        outfield = friends[1:]
        path = self._trajectory(bx, by, vx, vy)
        carrier = min(outfield, key=lambda p: self._intercept(p, path)[0])
        self._receive_plan = self._receive_aim = self._bank_receive = None
        self._relay_receive = self._x_reception = None
        side = 1.0 if by >= 0.0 else -1.0
        if bx < self._right - 14.0:
            stage = (self._right - 7.0, side * (self._goal_half + 1.2))
        else:
            stage = (self._right + 4.0, side * (self._goal_half + 0.9))
        ax, ay = _unit(stage[0] - bx, stage[1] - by)
        desired_speed = 7.5
        if bx > self._right - 12.0:
            tx, ty = (7.5, _clip((side * (self._goal_half + 0.9) - by) * 5.0, -4.0, 4.0))
        else:
            tx, ty = (ax * desired_speed, ay * desired_speed)
        actions = TeamAction(debug={'text': 'Corner endpoint siege'})
        free = [p for p in outfield if p[0] != carrier[0]]
        free.sort(key=lambda p: p[2])
        targets = {}
        for index, p in enumerate(free):
            targets[p[0]] = (min(34.0, max(0.0, bx - 12.0)), (-7.0, 0.0, 7.0)[index])
        gx = self._left + 1.3
        gy = _clip(by * 0.35, -self._goal_half + 1.0, self._goal_half - 1.0)
        if vx < -0.2:
            ticks = self._crossing_ticks(bx, vx, -gx)
            if ticks is not None and 0 <= ticks < 80:
                gy = _clip(by + vy * self._roll[min(80, max(0, int(ticks)))], -self._goal_half + 0.4, self._goal_half - 0.4)
        targets[0] = (gx, gy)
        for p in friends:
            if p[0] == carrier[0]:
                target = self._intercept(p, path)[1]
                movement = self._move(p, self._target(*target))
                kick = None
                if obs.can_kick(p[0]):
                    movement = self._move(p, (bx + ax * 0.8, by + ay * 0.8))
                    kick = self._siege_goal(p, bx, by, vx, vy, movement, wall)
                    if kick is None:
                        kick = self._kick_to_velocity(vx, vy, tx, ty)
                    px = p[3] * self._damping + movement[0] * self._acc
                    py = p[4] * self._damping + movement[1] * self._acc
                    length = math.hypot(px, py)
                    if length > self._speed:
                        px *= self._speed / length
                        py *= self._speed / length
                    if math.hypot(p[1] + px * self._dt - bx, p[2] + py * self._dt - by) > self._range - 0.025:
                        kick = None
                if kick is None:
                    actions.set(p[0], PlayerAction(movement=movement))
                else:
                    actions.set(p[0], PlayerAction(movement=movement, kick_direction=kick[0], kick_power=kick[1]))
            else:
                movement = self._move(p, targets.get(p[0], p[1:3]))
                if p[0] == 0 and obs.can_kick(p[0]):
                    actions.set(p[0], PlayerAction(movement=movement, kick_direction=(1.0, 0.0), kick_power=1.0))
                else:
                    actions.set(p[0], PlayerAction(movement=movement))
        return actions

    def reset(self, seed):
        self._bait_base_reset(seed)
        self._bait_plan_score = None
        self._bait_wall_ids = None

    def act(self, obs):
        # The siege path bypasses normal-play kickoff protection. Hold legal
        # kickoff positions until the opponent actually moves its centre ball.
        if obs.ball.controlling_team == 1 and math.hypot(*obs.ball.position) < 0.5 and math.hypot(*obs.ball.velocity) < 0.15:
            return TeamAction({p.id: PlayerAction() for p in obs.my_players}, debug={'text': 'Blue: protect opponent restart'})
        lead = obs.score[0] - obs.score[1]
        eligible = lead == 1 or (lead == 0 and obs.score[0] > 0)
        enemy_wall = sum((q.position[0] > obs.opponent_goal[0] - 3.0 and abs(q.position[1]) < 9.0 for q in obs.opponents))
        if not eligible or enemy_wall >= 4:
            self._bait_plan_score = None
            self._bait_wall_ids = None
            return self._bait_counter_act(obs)
        actions = self._bait_counter_act(obs)
        if self._receive_plan is not None:
            return actions
        friends = [(p.id, *p.position, *p.velocity) for p in obs.my_players]
        if len(friends) != 5:
            return actions
        score = tuple(obs.score)
        if self._bait_plan_score != score or self._bait_wall_ids is None:
            self._bait_wall_ids = tuple((p[0] for p in sorted(friends[:4], key=lambda p: (p[2], p[0]))))
            self._bait_plan_score = score
        by_id = {p[0]: p for p in friends}
        protected = obs.tick < self._restart_until and self._restart_owner == 1
        launching = any((a.kick_direction is not None for a in actions.players.values()))
        for index, pid in enumerate(self._bait_wall_ids):
            p = by_id[pid]
            old = actions.players[pid]
            if old.kick_direction is not None:
                continue
            movement = self._move(p, (self._left + 1.2, (index - 1.5) * 3.6))
            if not protected and (not launching) and obs.can_kick(pid):
                actions.set(pid, PlayerAction(movement=movement, kick_direction=(1.0, 0.0), kick_power=1.0))
            else:
                actions.set(pid, PlayerAction(movement=movement))
        outlet = friends[4]
        if not protected and actions.players[outlet[0]].kick_direction is None:
            bx, by = obs.ball.position
            path = self._trajectory(bx, by, *obs.ball.velocity)
            target = self._intercept(outlet, path)[1]
            actions.set(outlet[0], PlayerAction(movement=self._move(outlet, self._target(*target))))
        if actions.debug is not None:
            actions.debug['text'] = 'Conditional four-wall bait and separate outlet'
        return actions

class AdaptiveChampion(TeamController):
    name = 'TITAN blue-a-kickoff'
    version = 'blue-a-kickoff-0.1'

    def __init__(self):
        self._fallback = _FallbackPolicy()
        self._specialist = _SpecialistPolicy()
        self.reset(0)

    def reset(self, seed):
        self._seed = seed
        self._fallback.reset(seed)
        self._specialist.reset(seed)
        self._active = False
        self._wall_confirmed = False
        self._wall_ticks = 0
        self._wall_last_tick = None

    def initial_formation(self, field):
        return self._fallback.initial_formation(field)

    # Wall detector (looser than the original): a wall is four or more opponents, in any slots
    # and with any ids, standing within 1.5 of the line 1.2 in front of their goal and inside
    # |y| < 7.5, seen on 6 ticks in a row. The original needed the exact five-slot lock formation
    # with the keeper in its slot, which bunkers with a central keeper never match.
    def _observe_wall(self, obs):
        if self._wall_confirmed:
            return
        target_x = obs.opponent_goal[0] - 1.2
        matches = 0
        keeper_matches = True
        for opponent in obs.opponents:
            x, y = opponent.position
            if abs(x - target_x) < 1.5 and abs(y) < 7.5:
                matches += 1
        tick = obs.tick
        if matches >= 4 and keeper_matches:
            if self._wall_last_tick is None or tick != self._wall_last_tick + 1:
                self._wall_ticks = 1
            else:
                self._wall_ticks += 1
            self._wall_last_tick = tick
            if self._wall_ticks >= 6:
                self._wall_confirmed = True
        else:
            self._wall_ticks = 0
            self._wall_last_tick = None

    def act(self, obs):
        deadline = perf_counter() + self._fallback.SEARCH_BUDGET_SECONDS
        self._fallback._decision_deadline = deadline
        self._specialist._decision_deadline = deadline
        if self._active:
            return self._specialist.act(obs)
        actions = self._fallback.act(obs)
        self._observe_wall(obs)
        if not self._wall_confirmed:
            return actions
        if self._fallback._last_score == obs.score:
            for plan in (self._fallback._receive_plan, self._fallback._relay_receive, self._fallback._x_reception):
                if plan is not None and plan[2] >= obs.tick:
                    return actions
        if any((action.kick_direction is not None for action in actions.players.values())):
            return actions
        self._specialist.reset(self._seed)
        self._specialist._last_score = obs.score
        self._active = True
        return self._specialist.act(obs)
