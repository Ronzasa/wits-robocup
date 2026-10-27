"""Build one bounded outlet escape hypothesis; frozen V1 logic stays intact."""
import ast
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE_SHA = "13a91e8f755c91a18891dad07e7ab77487d2ad191d41f0f0d6ce9fbb99268977"
base = HERE / "ray_cover2/team.py"
target = HERE / "outlet_pivot/team.py"
original = base.read_bytes()
assert hashlib.sha256(original).hexdigest() == BASE_SHA, "Frozen base changed"
source = original.decode("utf-8")
source = source.replace('name = "MONSTER RAY COVER2"', 'name = "MONSTER OUTLET PIVOT"')
source = source.replace("version = 'league-ray-cover-2'", "version = 'league-outlet-pivot-1'")
old_reset = "        self.outlet_side = None\n"
new_reset = old_reset + """        self.pivot_blocked_ticks = 0
        self.pivot_reference_x = None
        self.pivot_cooldown_until = -1
"""
assert source.count(old_reset) == 1
source = source.replace(old_reset, new_reset)
method = '''    def pivot_outlet(self, obs, ball, friends, opponents):
        """Escape a persistently marked parking lane without releasing guards."""
        outlet = friends[4]
        bx, by, vx, vy = ball
        side = self.outlet_side if self.outlet_side is not None else (1 if by >= 0 else -1)
        anchor = self.bound(self.OUTLET_X, side*21.0)
        alternate = self.bound(self.OUTLET_X, -side*21.0)
        parked = math.hypot(outlet[1]-anchor[0], outlet[2]-anchor[1]) < 5.0
        # Only the existing deep-half parking behavior is eligible. A live
        # counterattack, collection opportunity or positive lead clears state.
        eligible = (self.FIXED_OUTLET and obs.score[0] <= obs.score[1]
                    and bx < self.left+20.0 and parked and not obs.can_kick(4)
                    and obs.tick >= self.pivot_cooldown_until)
        if not eligible:
            self.pivot_blocked_ticks = 0
            self.pivot_reference_x = None
            return
        marked_distance = min(
            min(math.hypot(q[1]-anchor[0], q[2]-anchor[1]),
                math.hypot(q[1]-outlet[1], q[2]-outlet[2]))
            for q in opponents)
        if marked_distance > 6.0:
            self.pivot_blocked_ticks = 0
            self.pivot_reference_x = None
            return
        if self.pivot_reference_x is None:
            self.pivot_reference_x = outlet[1]
        if outlet[1] > self.pivot_reference_x+2.0:
            self.pivot_blocked_ticks = 0
            self.pivot_reference_x = outlet[1]
            return
        self.pivot_blocked_ticks += 1
        if self.pivot_blocked_ticks < 60:
            return
        # Short public-velocity projections reject a lane an opponent is
        # already closing. This is ten cheap distance checks, not a search.
        current_room = min(math.hypot(q[1]+q[3]*0.4-anchor[0],
                                      q[2]+q[4]*0.4-anchor[1]) for q in opponents)
        alternate_room = min(math.hypot(q[1]+q[3]*0.4-alternate[0],
                                        q[2]+q[4]*0.4-alternate[1]) for q in opponents)
        if alternate_room >= 9.0 and alternate_room >= current_room+3.0:
            self.outlet_side = -side
            self.pivot_cooldown_until = obs.tick+int(10*self.hz)
            self.pivot_blocked_ticks = 0
            self.pivot_reference_x = None

'''
assert source.count("    def shell_act(self, obs, protected):") == 1
source = source.replace("    def shell_act(self, obs, protected):", method+"    def shell_act(self, obs, protected):")
old_call = """        outlet = friends[4]
        if bx<self.left+20 and not obs.can_kick(4):
"""
new_call = """        outlet = friends[4]
        self.pivot_outlet(obs, ball, friends, opponents)
        release_side = self.outlet_side if self.FIXED_OUTLET and self.outlet_side is not None else (1 if by>=0 else -1)
        if bx<self.left+20 and not obs.can_kick(4):
"""
assert source.count(old_call) == 1
source = source.replace(old_call, new_call)
ast.parse(source)
target.parent.mkdir(parents=True, exist_ok=True)
with target.open("x", encoding="utf-8", newline="\n") as stream:
    stream.write(source)
record = {"source": str(target.relative_to(HERE)), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
          "base": str(base.relative_to(HERE)), "base_sha256": BASE_SHA,
          "hypothesis": "Tied/trailing marked deep-half outlet switches to a roomier opposite anchor after60blocked ticks,10secondcooldown; no guard release.",
          "match_evidence": "Unmeasured candidate; builder and syntax only."}
with (target.parent / "build.json").open("x", encoding="utf-8") as stream:
    json.dump(record, stream, indent=2)
print(json.dumps(record))
