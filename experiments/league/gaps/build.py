"""Assemble standalone observed-gap MONSTER variants, offline only."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
source = (ROOT / "experiments/red-team/monster/team.py").read_text(encoding="utf-8")
source = source.replace('name = "MONSTER"', 'name = "MONSTER GAPS"')
source = source.replace("version = 'v51-stream-post'", "version = 'league-observed-gaps-1'")
marker = '    def shot(self, p, ball, opponents, movement, wall):'
addition = '''    def goal_aims(self, ball, opponents, wall):
        """Project visible blocker bodies onto the goal plane, then aim gaps.

        The full existing shot forecast still validates every new aim point.
        The projection proposes at most five extra candidates; it does not
        assume that a moving defender will remain stationary during a shot.
        """
        bx, by, vx, vy = ball
        fixed = (-0.97, 0.97, -0.85, 0.85, -0.6, 0.6, -0.3, 0.3, 0.0)
        if not wall or bx >= self.right-0.2:
            return fixed
        distance = self.right+0.25-bx
        low, high = -self.goal+0.07, self.goal-0.07
        intervals = []
        for q in opponents:
            if q[1] <= bx+0.8:
                continue
            # Project each observed body, retaining its short inertial coast.
            horizon = min(0.45, max(0.0, (q[1]-bx)/max(14.0, vx+16.0)))
            coast = self.dt*self.damp*(1-self.damp**(horizon*self.hz))/(1-self.damp)
            qx, qy = q[1]+q[3]*coast, q[2]+q[4]*coast
            scale = distance/max(0.8, qx-bx)
            centre = by+(qy-by)*scale
            extent = (self.body+0.14)*scale
            a, b = max(low, centre-extent), min(high, centre+extent)
            if a < b:
                intervals.append((a, b))
        gaps = []
        cursor = low
        for a, b in sorted(intervals):
            if a > cursor+0.12:
                gaps.append((a-cursor, (a+cursor)*0.5))
            cursor = max(cursor, b)
        if high > cursor+0.12:
            gaps.append((high-cursor, (high+cursor)*0.5))
        extra = []
        for width, centre in sorted(gaps, reverse=True):
            fraction = centre/self.goal
            if min(abs(fraction-old) for old in fixed+tuple(extra)) > 0.018:
                extra.append(fraction)
            if len(extra) == 5:
                break
        return tuple(extra)+fixed

'''
source = source.replace(marker, addition+marker)
source = source.replace('for fraction in (-0.97, 0.97, -0.85, 0.85, -0.6, 0.6, -0.3, 0.3, 0):',
                        'for fraction in self.goal_aims(ball, opponents, wall):')
target = Path(__file__).with_name("team.py")
target.write_text(source, encoding="utf-8")
print(target.relative_to(ROOT))

corner = source.replace('name = "MONSTER GAPS"', 'name = "MONSTER CORNER"')
corner = corner.replace("version = 'league-observed-gaps-1'", "version = 'league-corner-duel-1'")
corner = corner.replace('    def duel(self, p, ball, opponents, movement):',
                        '    def forward_duel(self, p, ball, opponents, movement):')
insert = '''    def duel(self, p, ball, opponents, movement):
        bx, by, vx, vy = ball
        default = self.forward_duel(p, ball, opponents, movement)
        if default is None or bx < self.right-6.0 or abs(by) < self.goal-0.7:
            return default
        # A duel outside the post must sometimes turn inward. Forward x alone
        # rewards a kick into the end wall even when it cannot enter the goal.
        side = 1 if by >= 0 else -1
        targets = (side*(self.goal-0.22), side*self.goal*0.55, 0.0, -side*self.goal*0.65)
        angles = [math.atan2(ty-by, self.right+0.3-bx) for ty in targets]
        angles.extend((0.0, -0.35, 0.35))
        ex, ey = unit(self.left-bx, -by)
        enemy_impulses = ((ex*self.impulse, ey*self.impulse), (-8.0-vx, -vy), (0.0, 0.0))
        start_gap = math.hypot(self.right+0.1-bx, max(0.0, abs(by)-self.goal+0.12))
        best = None
        for angle in angles:
            if perf_counter() > self.deadline:
                break
            ux, uy = math.cos(angle), math.sin(angle)
            values = []
            for evx, evy in enemy_impulses:
                for enemy_first in (False, True):
                    sx, sy = vx, vy
                    impulses = [(ux*self.impulse, uy*self.impulse), (evx, evy)]
                    if enemy_first:
                        impulses.reverse()
                    for dx, dy in impulses:
                        sx, sy = sx+dx, sy+dy
                        scale = max(1.0, math.hypot(sx, sy)/self.ballcap)
                        sx, sy = sx/scale, sy/scale
                    scored, blocked = False, False
                    x, y = bx, by
                    for n, x, y in self.stream_path(bx, by, sx, sy, steps=18):
                        if n == 0:
                            continue
                        coast = self.reach[n][0]
                        if any(math.hypot(x-q[1]-q[3]*coast, y-q[2]-q[4]*coast) < self.body-0.02
                               for q in opponents):
                            blocked = True
                            break
                        if x > self.right and abs(y) < self.goal:
                            scored = True
                            break
                    gap = math.hypot(self.right+0.1-x, max(0.0, abs(y)-self.goal+0.12))
                    value = 25.0 if scored else (start_gap-gap)*0.75 + (x-bx)*0.06 - (2.0 if blocked else 0.0)
                    values.append(value)
            # Retain a worst-case term, but accept a clearing risk deep in the
            # attacking corner to gain an actual scoring opportunity.
            value = sum(values)/len(values)+0.25*min(values)
            if best is None or value > best[0]:
                best = (value, ((ux, uy), 1.0), movement, None)
        return best if best is not None else default

'''
corner = corner.replace('    def launch(self, p, ball, kick, movement):',
                        insert+'    def launch(self, p, ball, kick, movement):')
corner_target = ROOT / "experiments/league/gaps2/team.py"
corner_target.parent.mkdir(parents=True, exist_ok=True)
corner_target.write_text(corner, encoding="utf-8")
print(corner_target.relative_to(ROOT))
