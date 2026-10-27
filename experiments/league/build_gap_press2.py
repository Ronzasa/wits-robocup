"""Build a standalone three-guard variant; keep the original stress source intact."""
from pathlib import Path


HERE = Path(__file__).resolve().parent
original = HERE / "opponents/gap_press/team.py"
target = HERE / "opponents/gap_press2/team.py"
source = original.read_text(encoding="utf-8")
assert source.count("    def act(self, obs):") == 1
head = source.split("    def act(self, obs):", 1)[0]
head = head.replace("class GapPress(TeamController):", "class GapPressTwo(TeamController):")
head = head.replace('name = "Gap Press Stress"', 'name = "Gap Press Three Guard Stress"')
head = head.replace('version = "1"', 'version = "2"')
head = head.replace("return [(field.my_goal[0]+3.5, 0), (-20, 0), (-7, -8), (front, -3), (front, 3)]",
                    "return [(field.my_goal[0]+1.3, 0), (field.my_goal[0]+2, -4.8), (field.my_goal[0]+2, 4.8), (front, -3), (front, 3)]")
tail = '''    def forward_pass(self, player, receiver, obs):
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
'''
target.parent.mkdir(parents=True, exist_ok=True)
with target.open("x", encoding="utf-8", newline="\n") as stream:
    stream.write(head+tail)
print(target)
