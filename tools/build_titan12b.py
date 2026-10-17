"""Build isolated single-file TITAN-12B controllers from the frozen v10 champion.

This development tool is never imported by the submitted team.py.
"""
import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = '5af280cea6b6c8f9f66db5776ad5ce02dbcf51ee6c6e57690fea2c307ae0b1f6'
HELPERS = '''    def _counter_threats(self, obs, friends, opponents, chaser, races, enemy_eta):
        """Rank at most four public-state threats; these are positioning estimates.

        Existing verified pass races are untouched. No hypothetical enemy pass
        is treated as a physically certified interception or possession event.
        """
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        own = {p[0] for p in friends}
        enemy = {p[0] for p in opponents}
        holder, touch = obs.ball.controlling_player, obs.ball.last_touch
        ours = races[chaser[0]][0]
        # A secure carrier's successful attack always retains its original roles.
        if (holder in own or (touch in own and ours + .16 < enemy_eta)
                or any(obs.can_kick(p[0]) for p in friends)):
            return [], False
        loss = (self._press_contact_owner == 1
                and 0 <= obs.tick - self._press_own_contact_tick <= int(1.25*self._hz))
        impending = touch in own and vx < -5.0 and bx < 5.0 and enemy_eta + .25 < ours
        initiative = (holder in enemy or impending
                      or (touch in enemy and enemy_eta + .12 < ours))
        if not initiative or not (loss or impending or (vx < -5.0 and bx < 8.0)
                                  or (bx < -18.0 and holder in enemy)):
            return [], False
        guard = self._shape_cover_id
        threats = []
        for q in opponents[1:]:
            gap = math.hypot(q[1]-bx, q[2]-by)
            direct = gap < 4.0
            if not direct and (q[1] > bx-3.0 or not 4.0 < gap < 36.0):
                continue
            flight = .35 if direct else min(1.6, self._flight(gap, 22.0))
            lead = min(.6, flight)
            px, py = self._target(q[1]+q[3]*lead, q[2]+q[4]*lead)
            if px > self._left+44.0 or abs(py) > 23.0:
                continue
            # Do not send the cover toward a forward already guarded goal-side.
            covered = any(p[0] not in (0, chaser[0], guard)
                and p[1] <= px+.5 and math.hypot(p[1]-px,p[2]-py) < 4.6
                for p in friends)
            if covered:
                continue
            blocked = False
            if not direct:
                dx, dy = px-bx, py-by
                length2 = dx*dx+dy*dy
                for p in friends[1:]:
                    if p[0] == guard or length2 < 1e-8:
                        continue
                    part = ((p[1]-bx)*dx+(p[2]-by)*dy)/length2
                    if .12 < part < .92:
                        x, y = bx+dx*part, by+dy*part
                        if self._eta(p,x,y)+.12 < flight*part:
                            blocked = True
                            break
            if blocked:
                continue
            score = (max(0.0,42.0-(px-self._left))*.055
                     + max(0.0,14.0-abs(py))*.06
                     + max(0.0,-q[3])*.08 + (.5 if direct else .8))
            if score >= 1.05:
                threats.append((score, q[0], px, py, flight, direct))
        threats.sort(key=lambda item: (-item[0], item[1]))
        urgent = (bool(threats) and enemy_eta+.25 < ours
                  and ((loss and bx < 8.0) or (bx < -22.0 and holder in enemy)))
        return threats, urgent

    def _counter_cover_target(self, player, threat, bx, by):
        _, _, px, py, flight, direct = threat
        ux, uy = _unit(self._left-px, -py)
        mark = self._target(px+ux*(4.0 if direct else 3.0),
                            py+uy*(4.0 if direct else 3.0))
        if (self._eta(player,*mark) <= flight+.55
                and math.hypot(mark[0]-player[1],mark[1]-player[2]) <= 12.0):
            return mark
        # A distant receiver is not a licence for an unreachable deep retreat.
        # Screen its pass lane locally if the defender can contribute in time.
        if not direct and bx-px > 4.0:
            part = _clip((bx-player[1]+1.5)/(bx-px), .18, .82)
            lane = self._target(bx+(px-bx)*part-.6, by+(py-by)*part)
            if (self._eta(player,*lane) <= flight*part+.35
                    and math.hypot(lane[0]-player[1],lane[1]-player[2]) <= 8.0):
                return lane
        return None

    def _counter_defence(self, obs, friends, opponents, chaser, races,
                         enemy_eta, targets, receive_target, protected):
        # This hook runs after verified receiver planning and all v10 shaping.
        # Its output never changes a kick, goalkeeper, chaser or named receiver.
        self._counter_trace = {'threats': (), 'defenders': (), 'urgent': False}
        reset = (protected or self._counter_score != tuple(obs.score)
                 or obs.tick <= self._counter_tick)
        self._counter_score, self._counter_tick = tuple(obs.score), obs.tick
        if reset:
            self._counter_double_until = -1
            self._counter_double_latched = False
        if protected:
            return
        threats, urgent = self._counter_threats(obs,friends,opponents,chaser,races,enemy_eta)
        self._counter_trace['threats'] = tuple(q[1] for q in threats)
        self._counter_trace['urgent'] = urgent
        if not threats:
            self._counter_double_until = -1
            self._counter_double_latched = False
            return
        guard_id = self._shape_cover_id
        receiver = receive_target[0] if receive_target is not None else None
        locked = {0, chaser[0], receiver}
        guard = next((p for p in friends[1:] if p[0] == guard_id and p[0] not in locked), None)
        if guard is None:
            self._counter_double_until = -1
            self._counter_double_latched = False
            return
        bx, by = obs.ball.position
        assigned = None
        if self.COUNTER_COVER:
            for threat in threats:
                target = self._counter_cover_target(guard,threat,bx,by)
                if target is not None:
                    targets[guard_id] = target
                    assigned = threat[1]
                    self._counter_trace['defenders'] = (guard_id,)
                    break
        # Only the emergency variation may reduce two outlets to one, for at
        # most 0.6 seconds, never continually extending an existing emergency.
        high = urgent and len(threats) >= 2 and threats[1][0] >= 1.8
        if not high:
            return
        if not self.COUNTER_DOUBLE:
            return
        if not self._counter_double_latched:
            self._counter_double_until = obs.tick + max(1,int(.6*self._hz))
            self._counter_double_latched = True
        if obs.tick >= self._counter_double_until:
            return
        free = [p for p in friends[1:] if p[0] not in (chaser[0],guard_id)]
        if len(free) < 2:
            return
        # A live verified receiver is the reserved outlet. Otherwise retain the
        # highest existing attacking target; no new attack decision is invented.
        outlet = next((p for p in free if p[0] == receiver), None)
        if outlet is None:
            outlet = max(free,key=lambda p:(targets[p[0]][0],p[1],-p[0]))
        eligible = [p for p in free if p[0] not in locked and p[0] != outlet[0]]
        if len(free)-1 < self.EMERGENCY_OUTLETS or not eligible:
            return
        for threat in threats:
            if threat[1] == assigned:
                continue
            if math.hypot(targets[guard_id][0]-threat[2],targets[guard_id][1]-threat[3]) < 5.0:
                continue
            choices = []
            for p in eligible:
                target = self._counter_cover_target(p,threat,bx,by)
                if target is not None and self._eta(p,*target) <= .65:
                    choices.append((self._eta(p,*target),p[0],target))
            if choices:
                _, pid, target = min(choices)
                targets[pid] = target
                self._counter_trace['defenders'] = (guard_id,pid)
                return

'''


ROUTE_THREATS = '''    def _counter_threats(self, obs, friends, opponents, chaser, races, enemy_eta):
        """Anticipate real counterpasses using verified public-physics contacts.

        One 1.25-second flight, at most four opponents and the existing primary
        chaser. Explicit local steps avoid changing any passing cache or aim.
        """
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        own = {p[0] for p in friends}
        enemy = {p[0] for p in opponents}
        holder, touch = obs.ball.controlling_player, obs.ball.last_touch
        ours = races[chaser[0]][0]
        if (holder in own or holder in enemy or vx >= -6.0 or bx > 12.0
                or math.hypot(vx,vy) < 9.0
                or any(obs.can_kick(p[0]) for p in friends)
                or (touch in own and ours+.16 < enemy_eta)):
            return [], False
        if touch not in enemy and not (touch in own and enemy_eta+.25 < ours):
            return [], False
        # An already goal-bound shot belongs to the unchanged keeper/chaser
        # safeguards, not an invented off-ball pass. Common drag preserves the
        # straight-line crossing coordinate until a wall/body changes it.
        if vx < -10.0:
            goal_ticks = self._crossing_ticks(bx,vx,-self._left-self._ball_radius)
            goal_y = by+vy*(self._left+self._ball_radius-bx)/vx
            if goal_ticks*self._dt <= 1.25 and abs(goal_y) <= self._mouth+.6:
                return [], False
        path = self._pass_path((bx,by,vx,vy),until=1.25)
        steps = []
        previous = None
        for t,x,y in path:
            n = int(round(t*self._hz))
            pre = previous if previous is not None and abs(t-previous[0]-self._dt)<1e-8 else None
            steps.append((t,n,x,y,pre))
            previous = (t,x,y)
        contacts = []
        for q in opponents[1:]:
            contact = self._verified_intercept(q,path,self._enemy_cooldowns.get(q[0],0),until=1.25,steps=steps)
            if contact is not None:
                contacts.append((contact[0],q[0],contact[1],q))
        if not contacts:
            return [], False
        contacts.sort(key=lambda row:(row[0],row[1]))
        first, _, point, _ = contacts[0]
        # Preserve terminal-area cover; do not crowd or rush the goalkeeper.
        if (first < .2 or not self._left+14.0 <= point[0] <= self._left+44.0
                or abs(point[1]) > 22.0):
            return [], False
        own_contact = self._verified_intercept(chaser,path,
            self._friend_cooldowns.get(chaser[0],0),until=first-.05,steps=steps)
        if own_contact is not None:
            return [], False
        threats = []
        for arrival,pid,(px,py),q in contacts:
            if arrival > first+.25:
                break
            if not self._left+14.0 <= px <= self._left+44.0 or abs(py)>22.0:
                continue
            covered = any(p[0] not in (0,chaser[0],self._shape_cover_id)
                and p[1] <= px+.5 and math.hypot(p[1]-px,p[2]-py) < 4.6
                for p in friends)
            if covered:
                continue
            score = 2.0+max(0.0,44.0-(px-self._left))*.05+max(0.0,18.0-abs(py))*.03
            threats.append((score,pid,px,py,arrival,False))
        loss = (self._press_contact_owner == 1
                and 0 <= obs.tick-self._press_own_contact_tick <= int(1.25*self._hz))
        urgent = bool(threats) and first < 1.0 and vx < -12.0 and (loss or bx < 0.0)
        return threats, urgent

'''

PREDICTIVE_THREATS = '''    def _counter_threats(self, obs, friends, opponents, chaser, races, enemy_eta):
        """Verify one observed flight or two legal, imminent opposing releases.

        Hypothetical routes are risk scenarios, not assertions of enemy intent.
        Explicit local flight metadata never changes our passing cache or aim.
        """
        bx, by = obs.ball.position
        vx, vy = obs.ball.velocity
        own = {p[0] for p in friends}
        enemy = {p[0] for p in opponents}
        holder, touch = obs.ball.controlling_player, obs.ball.last_touch
        ours = races[chaser[0]][0]
        if (holder in own or any(obs.can_kick(p[0]) for p in friends)
                or (touch in own and ours+.16 < enemy_eta)):
            return [], False
        loss = (self._press_contact_owner == 1
                and 0 <= obs.tick-self._press_own_contact_tick <= int(1.25*self._hz))
        routes = []
        controlled = holder in enemy
        if controlled:
            # Anticipate the release, but preserve the existing shot corridor
            # for a central carrier already in dangerous shooting territory.
            if (not loss or not -20.0 <= bx <= 12.0
                    or (bx < 0.0 and abs(by) < 12.0)):
                return [], False
            carrier = next((q for q in opponents if q[0] == holder), None)
            if carrier is None or self._enemy_cooldowns.get(holder,0) > 0:
                return [], False
            choices = []
            for q in opponents[1:]:
                gap = math.hypot(q[1]-bx,q[2]-by)
                if (q[0] == holder or q[1] >= bx-4.0 or not 6.0 < gap < 35.0
                        or not self._left+17.0 <= q[1] <= self._left+48.0 or abs(q[2])>20.0):
                    continue
                choices.append(q)
            choices.sort(key=lambda q:(q[1]+abs(q[2])*.2,q[0]))
            for q in choices[:2]:
                tx,ty = self._target(q[1]+q[3]*.35,q[2]+q[4]*.35)
                ux,uy = _unit(tx-bx,ty-by)
                kick = self._kick_to_velocity(vx,vy,ux*22.0,uy*22.0)
                if kick is None:
                    continue
                movement = self._move(carrier,(bx-.3,by))
                sx,sy = self._requested_velocity(vx,vy,kick)
                launch = self._carrier_contact(carrier,bx,by,sx,sy,movement)
                if launch is not None and launch[2] < -6.0:
                    routes.append((self._pass_path(launch,(bx,by),1.25),holder))
        else:
            if (vx >= -6.0 or bx > 12.0 or math.hypot(vx,vy)<9.0
                    or (touch not in enemy and not (touch in own and enemy_eta+.25<ours))):
                return [], False
            if vx < -10.0:
                ticks = self._crossing_ticks(bx,vx,-self._left-self._ball_radius)
                goal_y = by+vy*(self._left+self._ball_radius-bx)/vx
                if ticks*self._dt <= 1.25 and abs(goal_y)<=self._mouth+.6:
                    return [], False
            routes.append((self._pass_path((bx,by,vx,vy),until=1.25),None))
        threats = {}
        for path,passer in routes:
            steps = []
            previous = None
            for t,x,y in path:
                n = int(round(t*self._hz))
                pre = previous if previous is not None and abs(t-previous[0]-self._dt)<1e-8 else None
                steps.append((t,n,x,y,pre))
                previous = (t,x,y)
            contacts = []
            for q in opponents[1:]:
                if q[0] == passer:
                    continue
                contact = self._verified_intercept(q,path,self._enemy_cooldowns.get(q[0],0),
                    after=self._dt,until=1.25,steps=steps)
                if contact is not None:
                    contacts.append((contact[0],q[0],contact[1]))
            if not contacts:
                continue
            contacts.sort(key=lambda row:(row[0],row[1]))
            first,_,point = contacts[0]
            if (first < .2 or not self._left+14.0 <= point[0] <= self._left+44.0
                    or abs(point[1])>22.0):
                continue
            own_contact = self._verified_intercept(chaser,path,
                self._friend_cooldowns.get(chaser[0],0),after=self._dt,
                until=first-.05,steps=steps)
            if own_contact is not None:
                continue
            for arrival,pid,(px,py) in contacts:
                if arrival > first+.25:
                    break
                if not self._left+14.0 <= px <= self._left+44.0 or abs(py)>22.0:
                    continue
                covered = any(p[0] not in (0,chaser[0],self._shape_cover_id)
                    and p[1] <= px+.5 and math.hypot(p[1]-px,p[2]-py)<4.6 for p in friends)
                if covered:
                    continue
                score = 2.0+max(0.0,44.0-(px-self._left))*.05+max(0.0,18.0-abs(py))*.03
                item = (score,pid,px,py,arrival,False)
                old = threats.get(pid)
                if old is None or arrival < old[4]:
                    threats[pid] = item
        answer = sorted(threats.values(),key=lambda q:(q[4],-q[0],q[1]))
        urgent = (bool(answer) and answer[0][4]<1.0
                  and ((controlled and loss) or (vx < -12.0 and (loss or bx < 0.0))))
        return answer, urgent

'''

def build(mode):
    path=ROOT/'champions/v10.0/team.py'
    raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==FROZEN
    text=raw.decode()
    end=text.index('"""',3)+3
    text='''"""TITAN-12B: experimental, threat-limited counterattack defence.

All v10.0 kicks, goalkeeper safeguards, movement physics and verified pass
races are retained. Only a bounded post-planning defensive hook is added.
A second defender is emergency-only, preserving one attacking outlet for at
most 0.6 seconds. No timer, GC, engine-setting or process controls are used.
Promotion requires fresh paired points and all original reliability gates.
"""'''+text[end:]
    text=text.replace('version = "10.0-titan10b-r"',f'version = "12b-{mode}-experimental"\n    COUNTER_COVER = {mode in ("cover","combined","refinement","route-cover","route-combined","predictive-cover","predictive-combined","verified-cover","verified-combined")}\n    COUNTER_DOUBLE = {mode in ("double","combined","route-double","route-combined","predictive-double","predictive-combined","verified-double","verified-combined")}\n    EMERGENCY_OUTLETS = 1')
    anchor='        self._press_own_contact_tick = -100000\n'
    assert text.count(anchor)==2
    text=text.replace(anchor,anchor+'''        self._counter_trace = {}
        self._counter_score = None
        self._counter_tick = -1
        self._counter_double_until = -1
        self._counter_double_latched = False
''',1)
    anchor='    def _bank_path(self, bx, by, vx, vy):\n'
    assert text.count(anchor)==1
    helpers=HELPERS
    if mode.startswith('route-'):
        helpers=ROUTE_THREATS+HELPERS[HELPERS.index('    def _counter_cover_target'):]
        helpers=helpers.replace('<= flight+.55','<= flight-.05').replace('<= flight*part+.35','<= flight*part-.05')
    if mode.startswith('predictive-'):
        helpers=PREDICTIVE_THREATS+HELPERS[HELPERS.index('    def _counter_cover_target'):]
        helpers=helpers.replace('<= flight+.55','<= flight-.05').replace('<= flight*part+.35','<= flight*part-.05')
    if mode.startswith('verified-'):
        helpers=PREDICTIVE_THREATS+HELPERS[HELPERS.index('    def _counter_cover_target'):]
    text=text.replace(anchor,helpers+anchor)
    anchor='        carrier = None\n        carrier_gap = None\n'
    assert text.count(anchor)==1
    text=text.replace(anchor,'''        self._counter_defence(obs, friends, opponents, chaser, races, enemy_eta,
                              targets, receive_target, protected)

'''+anchor)
    if mode=='refinement':
        anchor='        ours = races[chaser[0]][0]\n'
        assert text.count(anchor)==1
        text=text.replace(anchor,anchor+'''        # A fast incoming flight is already committed. Preserve the v10
        # block/interception instead of moving cover toward a hypothetical
        # next pass. A controlled opponent can still choose a new release.
        if holder not in enemy and vx < -10.0 and bx < self._left+35.0:
            return [], False
''')
    return text


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('detect','cover','double','combined','refinement','route-detect','route-cover','route-double','route-combined','predictive-detect','predictive-cover','predictive-double','predictive-combined','verified-cover','verified-double','verified-combined'))
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.name!='team.py' or args.out.exists():p.error('Choose a new team.py; do not overwrite frozen sources.')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(build(args.mode))
    print(args.out,hashlib.sha256(args.out.read_bytes()).hexdigest())

if __name__=='__main__':main()
