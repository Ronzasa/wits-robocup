from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[2]; source=r/'my-team/team.py'; s=source.read_text()
assert hashlib.sha256(source.read_bytes()).hexdigest()=='27b3ef88ddede6267fd0583278b821c2abcd27de38772dfe9051307778e880ce'
# Only the experimental specialist and public wall detector change.
s=s.replace('    SIEGE_PRESS = False','    SIEGE_PRESS = True')
s=s.replace("    name = 'TITAN Adaptive Counter'\n    version = 'champion-hunt-adaptive-1.0'", "    name = 'TITAN Three Player Push'\n    version = 'three-player-push-0.1'")
old='''        target_x = obs.opponent_goal[0] - 1.2
        matches = 0
        keeper_matches = False
        for opponent in obs.opponents:
            pid = opponent.id
            if 5 <= pid <= 9:
                x, y = opponent.position
                if abs(x - target_x) < 0.9 and abs(y - (7 - pid) * 2.8) < 1.0:
                    matches += 1
                    if pid == 5:
                        keeper_matches = True
'''
new='''        matches = sum(q.position[0] > obs.opponent_goal[0] - 3.0
                      and abs(q.position[1]) < 9.0 for q in obs.opponents)
        keeper_matches = True
'''
assert old in s;s=s.replace(old,new)
old='''        if self.SIEGE_PRESS:
            chosen = sorted(wall, key=lambda q: side * q.position[1])[:2]
            for p, q in zip(free, chosen):
                targets[p[0]] = (self._right + 0.3, q.position[1] - side * 1.8)
'''
new='''        pushing = {}
        if self.SIEGE_PRESS:
            # All three spare outfield players apply legal maximum movement.
            # Assign the three defenders nearest the carrier's side of the wall.
            chosen = sorted(wall, key=lambda q: -side * q.position[1])[:3]
            chosen.sort(key=lambda q: q.position[1])
            for p, q in zip(free, chosen):
                approach = (q.position[0] - 1.2, q.position[1] + side * 1.7)
                if math.hypot(p[1] - approach[0], p[2] - approach[1]) > 2.6:
                    target = approach
                else:
                    target = (q.position[0] + 0.5, q.position[1] - side * 2.4)
                pushing[p[0]] = _unit(target[0] - p[1], target[1] - p[2])
'''
assert old in s;s=s.replace(old,new)
# Replace only the specialist siege carrier's shot selection, not general shooting.
old='''                    kick = self._siege_goal(p, bx, by, vx, vy, movement, wall)
                    if kick is None:
                        kick = self._kick_to_velocity(vx, vy, tx, ty)
'''
new='''                    kick = None
                    if self.SIEGE_PRESS and bx > self._right - 24.0:
                        enemies = [(q.id, *q.position, *q.velocity) for q in obs.opponents]
                        self._enemy_cooldowns = {q.id: q.kick_cooldown_ticks for q in obs.opponents}
                        shots = []
                        for gy in (-5.7, -3.0, 0.0, 3.0, 5.7):
                            option = self._shot_option(p, bx, by, vx, vy, enemies, gy)
                            if option is not None:
                                sx, sy = self._requested_velocity(vx, vy, option[1])
                                launch = self._carrier_contact(p, bx, by, sx, sy, option[2])
                                forecast = self._goal_path(launch) if launch is not None else None
                                own = [q for q in friends if q[0] != p[0]]
                                if forecast is not None and self._early_body_margin(forecast[0], own, forecast[1][0]) >= 0.05:
                                    shots.append(option)
                        if shots:
                            option = max(shots, key=lambda item: item[0])
                            kick, movement = option[1], option[2]
                    if kick is None:
                        kick = self._siege_goal(p, bx, by, vx, vy, movement, wall)
                    if kick is None:
                        kick = self._kick_to_velocity(vx, vy, tx, ty)
'''
assert old in s;s=s.replace(old,new)
old='''                movement = self._move(p, targets.get(p[0], p[1:3]))
                if p[0] == 0 and obs.can_kick(p[0]):'''
new='''                movement = pushing.get(p[0], self._move(p, targets.get(p[0], p[1:3])))
                if p[0] == 0 and obs.can_kick(p[0]):'''
assert old in s;s=s.replace(old,new)
compile(s,'team.py','exec'); (r/'experiments/three-player-push/team.py').write_text(s)
print('Built',len(s.encode()),hashlib.sha256(s.encode()).hexdigest())
