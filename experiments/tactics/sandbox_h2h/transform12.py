import ast, sys, re
src=open('team12_clean.py').read(); tree=ast.parse(src)
FIX={'KEEPER_POWER_PLAY':False,'PINBALL_SLINGSHOT':False,'COOLDOWN_AMBUSH':False,'SIEGE_PRESS':False,
     'FOLLOW_RECEIVER':False,'SCOUT_OUTLET':False,'GOALKEEPER_TRAP':True,'EXECUTE_RECEIVER':True}
FIXSTR={'_x_power_state':'idle'}
# make sure none of them is ever assigned through self.X = ...
for n in ast.walk(tree):
    if isinstance(n,ast.Attribute) and n.attr in FIX and isinstance(n.ctx,ast.Store): raise SystemExit('assigned: '+n.attr)
def const(n): return isinstance(n,ast.Constant) and isinstance(n.value,bool)
def pure(n): return not any(isinstance(x,(ast.Call,ast.Await,ast.Yield,ast.NamedExpr)) for x in ast.walk(n))
class T(ast.NodeTransformer):
    def visit_Attribute(self,n):
        self.generic_visit(n)
        if n.attr in FIXSTR and isinstance(n.value,ast.Name) and n.value.id=='self' and isinstance(n.ctx,ast.Load):
            return ast.copy_location(ast.Constant(FIXSTR[n.attr]),n)
        if n.attr in FIX and isinstance(n.value,ast.Name) and n.value.id=='self' and isinstance(n.ctx,ast.Load):
            return ast.copy_location(ast.Constant(FIX[n.attr]),n)
        return n
    def visit_Compare(self,n):
        self.generic_visit(n)
        if len(n.ops)==1 and isinstance(n.left,ast.Constant) and all(isinstance(c,ast.Constant) for c in n.comparators):
            a=n.left.value; b=n.comparators[0].value; op=n.ops[0]
            if isinstance(op,ast.Eq): return ast.copy_location(ast.Constant(a==b),n)
            if isinstance(op,ast.NotEq): return ast.copy_location(ast.Constant(a!=b),n)
        if len(n.ops)==1 and isinstance(n.left,ast.Constant) and isinstance(n.comparators[0],ast.Tuple) and all(isinstance(e,ast.Constant) for e in n.comparators[0].elts):
            vals=[e.value for e in n.comparators[0].elts]
            if isinstance(n.ops[0],ast.In): return ast.copy_location(ast.Constant(n.left.value in vals),n)
            if isinstance(n.ops[0],ast.NotIn): return ast.copy_location(ast.Constant(n.left.value not in vals),n)
        return n
    def visit_UnaryOp(self,n):
        self.generic_visit(n)
        if isinstance(n.op,ast.Not) and const(n.operand): return ast.copy_location(ast.Constant(not n.operand.value),n)
        return n
    def visit_BoolOp(self,n):
        self.generic_visit(n)
        isand=isinstance(n.op,ast.And); keep=[]; 
        for i,v in enumerate(n.values):
            if const(v):
                if v.value==isand: continue          # neutral element: drop
                if all(pure(p) for p in keep):        # absorbing element, nothing impure before it
                    return ast.copy_location(ast.Constant(v.value),n)
            keep.append(v)
        if not keep: return ast.copy_location(ast.Constant(isand),n)
        if len(keep)==1: return keep[0]
        n.values=keep; return n
    def visit_If(self,n):
        self.generic_visit(n)
        if const(n.test):
            body=n.body if n.test.value else n.orelse
            return body if body else None
        return n
    def visit_IfExp(self,n):
        self.generic_visit(n)
        if const(n.test): return n.body if n.test.value else n.orelse
        return n
def fix_empty(tree):
    for n in ast.walk(tree):
        for f in ('body','orelse','finalbody'):
            b=getattr(n,f,None)
            if isinstance(b,list) and not b and f=='body': b.append(ast.Pass())
fold=T().visit(tree); ast.fix_missing_locations(fold); fix_empty(fold)
def names_loaded(t):
    s=set()
    for n in ast.walk(t):
        if isinstance(n,ast.Attribute) and isinstance(n.ctx,ast.Load): s.add(n.attr)
        if isinstance(n,ast.Constant) and isinstance(n.value,str): s.add(n.value)
        if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load): s.add(n.id)
    return s
def prune(t):
    changed=False; used=names_loaded(t)
    for c in [n for n in t.body if isinstance(n,ast.ClassDef)]:
        keepb=[]
        for n in c.body:
            if isinstance(n,ast.FunctionDef) and n.name not in used and n.name not in ('__init__','act','reset','initial_formation'):
                changed=True; continue
            if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id not in used and n.targets[0].id not in('name','version'):
                changed=True; continue
            keepb.append(n)
        c.body=keepb
    # drop pure assignments to attributes that are never read
    class D(ast.NodeTransformer):
        def visit_Assign(self,n):
            self.generic_visit(n)
            if all(isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and t.value.id=='self' and t.attr not in used for t in n.targets) and pure(n.value):
                nonlocal_changed.append(1); return None
            return n
    nonlocal_changed=[]
    D().visit(t); fix_empty(t)
    return changed or bool(nonlocal_changed)
while prune(fold): pass
for n in ast.walk(fold):
    if isinstance(n,ast.Attribute) and n.attr in FIXSTR and isinstance(n.ctx,ast.Store): pass
bad=[ (n.lineno) for n in ast.walk(fold) if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Attribute) and t.attr in FIXSTR and not (isinstance(n.value,ast.Constant) and n.value.value==FIXSTR[t.attr])]
assert not bad, bad
out=ast.unparse(fold)
open('team12_clean2.py','w').write(out+'\n'); print(len(out.split('\n')),'lines')
