"""Build one isolated contact-aware corner-finishing research candidate."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
source = (ROOT / "ray_cover2/team.py").read_text(encoding="utf-8")
source = source.replace('name = "MONSTER RAY COVER2"', 'name = "MONSTER CONTACT FINISH"')
source = source.replace("version = 'league-ray-cover-2'", "version = 'league-contact-finish-1'")
source = source.replace('        self.outlet_side = None\n',
                        '        self.outlet_side = None\n        self.finish_anchor = None\n        self.finish_ticks = 0\n')

methods = '''    def finish_rollout(self, p, ball, opponents, kick, movement, impulses):
        """Score short corner shots after movement, kick ordering and own contact.

        Opponents retain their observed inertial coast. This is a proposal
        model, not a claim to reproduce their future decisions or contacts.
        """
        bx, by, vx, vy = ball
        start_gap = math.hypot(self.right+0.1-bx, max(0.0, abs(by)-self.goal+0.12))
        values, goals = [], 0
        for enemy in impulses:
            for enemy_first in (False, True):
                if perf_counter() > self.deadline:
                    return None
                order = [(kick[0][0]*kick[1]*self.impulse,
                          kick[0][1]*kick[1]*self.impulse), enemy]
                if enemy_first:
                    order.reverse()
                sx, sy = vx, vy
                for dx, dy in order:
                    sx, sy = sx+dx, sy+dy
                    scale = max(1.0, math.hypot(sx, sy)/self.ballcap)
                    sx, sy = sx/scale, sy/scale
                # All simultaneous impulses precede ball integration. Reuse
                # the carrier launch model with that combined ball velocity,
                # including the player's move and first own-body collision.
                launched = self.launch(p, (bx, by, sx, sy), None, movement)
                if launched is None:
                    return None
                scored, blocked = False, False
                x, y = launched[0][:2]
                for n, x, y in self.stream_path(*launched[0], steps=18):
                    coast = self.reach[n+1][0]
                    if any(math.hypot(x-q[1]-q[3]*coast, y-q[2]-q[4]*coast) < self.body-0.02
                           for q in opponents):
                        blocked = True
                        break
                    if x > self.right and abs(y) < self.goal-0.02:
                        scored = True
                        break
                gap = math.hypot(self.right+0.1-x, max(0.0, abs(y)-self.goal+0.12))
                value = 25.0 if scored else (start_gap-gap)*0.75+(x-bx)*0.06-(2.0 if blocked else 0.0)
                # A finish from the attacking corner should not choose a
                # modeled clearance all the way out of the attacking third.
                if x < self.right-25:
                    value -= 10.0
                values.append(value)
                goals += int(scored)
        return sum(values)/len(values)+0.25*min(values), goals

    def contact_finish(self, p, ball, opponents, movement):
        """Try three carrier movements for a small set of near-post shots."""
        baseline = self.duel(p, ball, opponents, movement)
        if baseline is None:
            return None
        bx, by, vx, vy = ball
        ex, ey = unit(self.left-bx, -by)
        impulses = ((ex*self.impulse, ey*self.impulse), (-8.0-vx, -vy), (0.0, 0.0))
        original = self.finish_rollout(p, ball, opponents, baseline[1], baseline[2], impulses)
        if original is None:
            return baseline
        best, best_value, best_goals = baseline, original[0], original[1]
        side = 1 if by >= 0 else -1
        aim_y = (side*(self.goal-0.2), side*(self.goal-1.1), side*self.goal*0.45, 0.0)
        for ty in aim_y:
            if perf_counter() > self.deadline:
                return best
            ux, uy = unit(self.right+0.3-bx, ty-by)
            kick = ((ux, uy), 1.0)
            # Keep the default approach as a control, then stand behind the
            # shot direction or move outside the inward ball corridor.
            approaches = (movement,
                self.move(p, self.bound(bx-ux*self.body*1.1, by-uy*self.body*1.1)),
                self.move(p, self.bound(bx-0.1, by+side*self.body*1.1)))
            for motion in approaches:
                scored = self.finish_rollout(p, ball, opponents, kick, motion, impulses)
                if scored is None:
                    return best
                value, goals = scored
                # Override the established corner policy only for a modeled
                # scoring chance with no reduction in scored scenarios.
                if goals > 0 and goals >= best_goals and value > best_value+0.35:
                    best = (value, kick, motion, None)
                    best_value, best_goals = value, goals
        return best

'''
marker = '    def launch(self, p, ball, kick, movement):'
if source.count(marker) != 1:
    raise RuntimeError("Expected one launch model")
source = source.replace(marker, methods+marker)

wall_marker = '        depth = self.LOCK_DEPTH if obs.score[0]>obs.score[1] else self.SHELL_DEPTH'
gate = '''        # Observe a stationary attacking-corner cluster before changing the
        # one outlet's finishing. All four guards and non-level play stay as
        # in the frozen ray-cover policy.
        finishing = wall and obs.score[0] == obs.score[1] and bx > self.right-9 and abs(by) > self.goal-0.8
        if finishing:
            if self.finish_anchor is None or math.hypot(bx-self.finish_anchor[0], by-self.finish_anchor[1]) > 2.0:
                self.finish_anchor, self.finish_ticks = (bx, by), 1
            else:
                self.finish_ticks += 1
        else:
            self.finish_anchor, self.finish_ticks = None, 0
        finish_ready = finishing and self.finish_ticks >= 18
'''
if source.count(wall_marker) != 1:
    raise RuntimeError("Expected one shell gate")
source = source.replace(wall_marker, gate+wall_marker)
old = '                best = self.shot(p, ball, opponents, movement, wall) if self.SHOT_FIRST else None'
new = '''                best = self.contact_finish(p, ball, opponents, movement) if finish_ready else None
                if best is None:
                    best = self.shot(p, ball, opponents, movement, wall) if self.SHOT_FIRST else None'''
if source.count(old) != 1:
    raise RuntimeError("Expected one outlet shot selector")
source = source.replace(old, new)
target = ROOT / "contact_finish/team.py"
compile(source, str(target), "exec")
target.parent.mkdir(parents=True, exist_ok=True)
contents = source.encode("utf-8")
if target.exists():
    if target.read_bytes() != contents:
        raise RuntimeError("Existing contact_finish differs; choose a new revision")
else:
    with target.open("xb") as stream:
        stream.write(contents)
print(str(target)+"; added "+str(source.count("\n")-(ROOT/"ray_cover2/team.py").read_text(encoding="utf-8").count("\n"))+" lines")
