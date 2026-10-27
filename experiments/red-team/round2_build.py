"""Build immutable round-two policies from the exact first-release snapshot."""
from pathlib import Path
import hashlib
import sys

LAB = Path(__file__).resolve().parent
if '--audit' in sys.argv:
    from round2_audit import main
    main()
    sys.exit()
if '--verify-stream' in sys.argv:
    import json
    import math
    import random
    import time
    sys.path.insert(0,str(LAB.parents[1]))
    import bootstrap
    bootstrap.ensure_engine(LAB.parents[1])
    from soccer import SoccerEnv
    from soccer.helpers import load_controller
    before = load_controller(str(LAB/'pool/v36-post-seven/team.py'))
    after = load_controller(str(LAB/'pool/v51-stream-post/team.py'))
    env = SoccerEnv(config_path=str(LAB.parents[1]/'configs/default.toml'))
    before.setup(env.field)
    after.setup(env.field)
    env.close()
    rng = random.Random(465103)
    cases = 1000
    started = time.perf_counter()
    for index in range(cases):
        vx,vy = rng.uniform(-30,30),rng.uniform(-30,30)
        scale = max(1,math.hypot(vx,vy)/30)
        ball = (rng.uniform(-49.5,49.5),rng.uniform(-29.5,29.5),vx/scale,vy/scale)
        old_path = before.path(*ball)
        assert old_path == after.path(*ball), ('path',index,ball)
        p = (4,rng.uniform(-49,49),rng.uniform(-29,29),rng.uniform(-5,5),rng.uniform(-5,5),rng.randrange(6))
        assert before.race(p,old_path) == after.race(p,after.stream_path(*ball)), ('race',index,ball,p)
    result = {'ok':True,'cases':cases,'path_samples_exactly_equal':True,'intercept_targets_exactly_equal':True,
              'before_sha256':hashlib.sha256((LAB/'pool/v36-post-seven/team.py').read_bytes()).hexdigest(),
              'after_sha256':hashlib.sha256((LAB/'pool/v51-stream-post/team.py').read_bytes()).hexdigest(),
              'elapsed_seconds':time.perf_counter()-started,
              'note':'Deterministic physics-refactor check; not a competitive match or latency benchmark.'}
    (LAB/'checks/stream-equivalence.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
    sys.exit()
baseline = (LAB/'pool/v25-fast-post/team.py').read_bytes()
assert hashlib.sha256(baseline).hexdigest() == '1bf09f5fcab940eae8f387ef36030d302dfe9e52aa6ae0fe82f48742ea6e85b7'
source = baseline.decode('utf-8').replace('\r\n', '\n')

def replace_once(text, before, after):
    assert text.count(before) == 1, before[:100]
    return text.replace(before, after)

source = replace_once(source, '    ADAPTIVE_POSTS = True\n', '''    ADAPTIVE_POSTS = True
    POST_MAX = 9.5
    PREDICT_POST = False
    SUPPORT = False
    SHOT_FIRST = False
    AIM_DUEL = False
''')
source = replace_once(source, '        for angle in (0, -0.35, 0.35, -0.7, 0.7):', '''        angles = (0, -0.35, 0.35, -0.7, 0.7)
        if self.AIM_DUEL and bx>self.right-18:
            goal_angle = math.atan2(clip(by,-self.goal+0.3,self.goal-0.3)-by,self.right+0.2-bx)
            angles = (goal_angle, goal_angle-0.2, goal_angle+0.2, 0, -0.7, 0.7)
        for angle in angles:''')
source = replace_once(source, '            worst = 100.0\n', '''            worst = 100.0
''')
source = replace_once(source, '        actions = TeamAction(debug={"text": "MONSTER four-cover counter"})', '''        support_id = 3 if self.SUPPORT and wall and bx>0 and not protected else None
        slots = (5.4,-1.8,1.8,-5.4)
        shot_guard = None
        shot_y = 0.0
        if self.PREDICT_POST and vx<-2 and bx>self.left+1.2:
            dx = bx-self.left-1.2
            if dx < -vx*self.dt/(1-self.drag):
                shot_y = by+vy*dx/(-vx)
                if abs(shot_y)<self.goal+0.25:
                    shot_guard = min(range(4),key=lambda j:abs(slots[j]-shot_y))
        actions = TeamAction(debug={"text": "MONSTER four-cover counter"})''')
source = replace_once(source, 'side*clip(abs(by),5.4,self.goal+2.5))', 'side*clip(abs(by),5.4,self.POST_MAX))')
source = replace_once(source, '''            movement = self.move(p, aim)
            kick = None
            if i==4''', '''            if i==shot_guard:
                aim = (self.left+min(depth,1.4),clip(shot_y,-self.goal+0.3,self.goal-0.3))
            if support_id is not None and i<4:
                if i==support_id:
                    aim = self.bound(max(12.0,bx-6.0),(-1 if by>=0 else 1)*5.5)
                else:
                    aim = (self.left+depth,(-4.9,0.0,4.9)[i])
            movement = self.move(p, aim)
            kick = None
            if i==4''')
source = replace_once(source, '''                best = self.duel(p, ball, opponents, movement)
                if best is None:
                    best = self.shot(p, ball, opponents, movement, wall)
                if best is None:
                    best = self.touch(p, ball, opponents, stage)
                if best:
''', '''                best = self.shot(p, ball, opponents, movement, wall) if self.SHOT_FIRST else None
                if best is None:
                    best = self.duel(p, ball, opponents, movement)
                if best is None:
                    best = self.shot(p, ball, opponents, movement, wall)
                if best is None:
                    best = self.touch(p, ball, opponents, stage)
                if self.SUPPORT and support_id is not None and (best is None or best[0]<10):
                    passed = self.passing(p,ball,friends,opponents)
                    if passed is not None and (best is None or passed[0]>best[0]+0.3):
                        best = passed
                if best:
''')
source = replace_once(source, '''            elif i<4 and not protected and obs.can_kick(i):
                side = release_side''', '''            elif i==support_id and not protected and obs.can_kick(i):
                movement = self.move(p,(bx+0.3,by))
                best = self.shot(p,ball,opponents,movement,wall)
                if best is None:
                    best = self.duel(p,ball,opponents,movement)
                if best is None:
                    best = self.touch(p,ball,opponents,(self.right,0))
                if best:
                    _,kick,movement,_ = best
            elif i<4 and not protected and obs.can_kick(i):
                side = release_side''')

if '--stream' in sys.argv:
    source = (LAB/'pool/v36-post-seven/team.py').read_text(encoding='utf-8')
    begin,end = source.index('    def path('),source.index('    def race(')
    old = source[begin:end]
    stream = old.replace('def path(', 'def stream_path(')
    stream = replace_once(stream,'        samples = [(0, x, y)]','        yield (0, x, y)')
    assert stream.count('samples.append((n, x, y))')==2
    stream = stream.replace('samples.append((n, x, y))','yield (n, x, y)')
    stream = replace_once(stream,'        return samples','        return')
    wrapper = '''    def path(self,x,y,vx,vy,steps=65):
        return list(self.stream_path(x,y,vx,vy,steps))

'''
    source = source[:begin]+stream+wrapper+source[end:]
    source = replace_once(source,'            path = self.path(*ball)\n','            path = self.stream_path(*ball)\n')
    source = replace_once(source,'        visible_enemy_wall = sum(', '        visible_enemy_wall = self.SHELL_RELEASE and sum(')
    variants = {'v51-stream-post':{}}
elif '--marking' in sys.argv:
    source = (LAB/'pool/v46-adaptive-pace/team.py').read_text(encoding='utf-8')
    source = replace_once(source,'    OUTLET_Y = 21.0\n','''    OUTLET_Y = 21.0
    MARK_WINDOW = 200
''')
    source = replace_once(source,'        self.outlet_side = None\n','        self.outlet_side = None\n        self.fast_break_until = -1\n')
    source = replace_once(source,'        outlet = friends[4]\n','''        outlet = friends[4]
        if bx<0 and outlet[1]<0 and any(q[1]>outlet[1]-2 and math.hypot(q[1]-outlet[1],q[2]-outlet[2])<7 for q in opponents):
            self.fast_break_until = obs.tick+self.MARK_WINDOW
''')
    source = replace_once(source,'if self.BREAKAWAY_TOUCH and not wall and bx<self.right-12',
                          'if self.BREAKAWAY_TOUCH and obs.tick<=self.fast_break_until and not wall and bx<self.right-12')
    source = replace_once(source,'            self.receiver = None\n        self.last_score = score',
                          '            self.receiver = None\n            self.fast_break_until = -1\n        self.last_score = score')
    variants = {
      'v48-marked-break':{},
      'v49-short-break':{'MARK_WINDOW':120},
      'v50-long-break':{'MARK_WINDOW':400},
    }
elif '--adaptive' in sys.argv:
    source = (LAB/'pool/v40-seven-fast/team.py').read_text(encoding='utf-8')
    source = replace_once(source,'if self.BREAKAWAY_TOUCH and bx<self.right-12',
                          'if self.BREAKAWAY_TOUCH and not wall and bx<self.right-12')
    source = replace_once(source,'                if self.SMART_CLEAR:\n',
                          '                if self.SMART_CLEAR and not wall and min(math.hypot(q[1]-outlet[1],q[2]-outlet[2]) for q in opponents)>9:\n')
    variants = {
      'v46-adaptive-pace':{},
      'v47-adaptive-release':{'SMART_CLEAR':True},
    }
elif '--attack' in sys.argv:
    source = (LAB/'pool/v36-post-seven/team.py').read_text(encoding='utf-8')
    source = replace_once(source,'    BREAKAWAY_TOUCH = False\n','''    BREAKAWAY_TOUCH = False
    WALL_SHOT_MARGIN = -0.08
    OUTLET_Y = 21.0
''')
    source = replace_once(source,'        bx, by, vx, vy = ball\n        if bx<self.right-(65',
                          '        bx, by, vx, vy = ball\n        margin_limit = self.WALL_SHOT_MARGIN if wall else self.SHOT_MARGIN\n        if bx<self.right-(65')
    source = replace_once(source,'if margin<self.SHOT_MARGIN:','if margin<margin_limit:')
    source = replace_once(source,'if scored and margin>=self.SHOT_MARGIN:','if scored and margin>=margin_limit:')
    source = replace_once(source,'side*21.0)','side*self.OUTLET_Y)')
    source = replace_once(source,'tx, ty = max(-4.0, outlet[1]+5), side*22.0',
                          'tx, ty = max(-4.0, outlet[1]+5), side*(self.OUTLET_Y+1)')
    variants = {
      'v40-seven-fast':{'BREAKAWAY_TOUCH':True},
      'v41-spread-fast':{'POST_MAX':6.6,'BREAKAWAY_TOUCH':True,'COVER_SHIFT':True},
      'v42-wall-risk':{'WALL_SHOT_MARGIN':-0.25},
      'v43-wall-force':{'WALL_SHOT_MARGIN':-0.45},
      'v44-inner-outlet':{'OUTLET_Y':14.0},
      'v45-touchline-outlet':{'OUTLET_Y':26.0},
    }
elif '--contact' in sys.argv:
    source = (LAB/'pool/v34-fast-break/team.py').read_text(encoding='utf-8')
    source = replace_once(source,'    BREAKAWAY_TOUCH = True\n','''    BREAKAWAY_TOUCH = True
    CONTACT_FINISH = True
''')
    source = replace_once(source,'    def shell_act(self, obs, protected):',
                          (LAB/'contact_finish.txt').read_text(encoding='utf-8').rstrip('\n')+'\n\n\n    def shell_act(self, obs, protected):')
    source = replace_once(source,'''                best = self.shot(p, ball, opponents, movement, wall) if self.SHOT_FIRST else None
''','''                best = self.contact_finish(p,ball,opponents,movement) if self.CONTACT_FINISH and wall else None
                if best is None and self.SHOT_FIRST:
                    best = self.shot(p, ball, opponents, movement, wall)
''')
    variants = {
      'v38-contact-goal':{'BREAKAWAY_TOUCH':False},
      'v39-fast-contact':{},
    }
elif '--wave2' in sys.argv:
    source = (LAB/'pool/v27-compact-post/team.py').read_text(encoding='utf-8')
    source = replace_once(source,'    AIM_DUEL = False\n','''    AIM_DUEL = False
    SMART_CLEAR = False
    COVER_SHIFT = False
    BREAKAWAY_TOUCH = False
''')
    source = replace_once(source,'    def shell_act(self, obs, protected):','''    def clearance(self,p,ball,outlet,opponents,movement,default):
        bx,by,vx,vy = ball
        best = None
        for ty in (outlet[2],outlet[2]+6,outlet[2]-6,0):
            if perf_counter()>self.deadline:
                break
            tx = max(bx+15,outlet[1]+8)
            ux,uy = unit(tx-bx,clip(ty,-25,25)-by)
            for compensate in (False,True):
                kick = self.velocity_kick(vx,vy,ux*24,uy*24) if compensate else ((ux,uy),1.0)
                launched = self.launch(p,ball,kick,movement)
                if launched is None:
                    continue
                state = launched[0]
                if state[2]<0.5:
                    continue
                route = self.path(*state,steps=32)
                ours = self.race(outlet,route)
                enemy = min(self.race(q,route)[0] for q in opponents)
                score = min(1.5,enemy-ours[0])*3-ours[0]*0.2+(route[-1][1]-bx)*0.07
                if best is None or score>best[0]:
                    best = score,kick
        return best[1] if best is not None else default

    def shell_act(self, obs, protected):''')
    source = replace_once(source,'''            if i==shot_guard:
''','''            if self.COVER_SHIFT and i<4 and abs(by)>6 and bx<self.left+15:
                aim = (aim[0],aim[1]+(0.55 if by>0 else -0.55))
            if i==shot_guard:
''')
    source = replace_once(source,'''                kick = ((ux, uy), 1.0)
            if protected''','''                kick = ((ux, uy), 1.0)
                if self.SMART_CLEAR:
                    kick = self.clearance(p,ball,outlet,opponents,movement,kick)
            if protected''')
    source = replace_once(source,'''                if best is None:
                    best = self.touch(p, ball, opponents, stage)
                if self.SUPPORT''','''                if best is None:
                    # A free runner can take a longer touch before defenders
                    # approach, rather than repeatedly slowing to 5.5 units/s.
                    old_speed = self.CARRY_SPEED
                    if self.BREAKAWAY_TOUCH and bx<self.right-12 and min(math.hypot(q[1]-bx,q[2]-by) for q in opponents)>9:
                        self.CARRY_SPEED = 11.0
                    best = self.touch(p, ball, opponents, stage)
                    self.CARRY_SPEED = old_speed
                if self.SUPPORT''')
    variants = {
      'v32-safe-distribution':{'SMART_CLEAR':True},
      'v33-spread-cover':{'COVER_SHIFT':True},
      'v34-fast-break':{'BREAKAWAY_TOUCH':True},
      'v35-compact-goal':{'SHOT_FIRST':True,'AIM_DUEL':True},
      'v36-post-seven':{'POST_MAX':7.3},
      'v37-post-tight':{'POST_MAX':5.8},
    }
else:
    variants = {
 'v26-predict-post': {'PREDICT_POST':True},
 'v27-compact-post': {'POST_MAX':6.6},
 'v28-shallow-lead': {'LOCK_DEPTH':1.2},
 'v29-two-strikers': {'SUPPORT':True},
 'v30-goal-duel': {'SHOT_FIRST':True,'AIM_DUEL':True},
 'v31-forward-outlet': {'OUTLET_X':-8.0},
    }
for name, options in variants.items():
    import re
    text,count = re.subn(r'(?m)^    version = .*$', '    version = '+repr(name),source)
    assert count==1
    for key,value in options.items():
        import re
        text, count = re.subn(r'(?m)^    '+key+r' = .*$', '    '+key+' = '+repr(value),text)
        assert count==1
    target = LAB/'pool'/name/'team.py'
    generated = text.replace('\n','\r\n').encode('utf-8')
    if '--verify-existing' in sys.argv:
        assert target.exists() and target.read_bytes()==generated, 'Build no longer reproduces '+name
        print('Verified '+name+' '+hashlib.sha256(generated).hexdigest())
        continue
    if target.exists():
        raise RuntimeError('Immutable snapshot already exists: '+name)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(generated)
    print(target)
