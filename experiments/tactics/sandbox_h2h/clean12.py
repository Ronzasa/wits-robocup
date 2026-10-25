import ast, re, sys
src=open('team12.py').read(); lines=src.split('\n'); t=ast.parse(src)
C={n.name:n for n in t.body if isinstance(n,ast.ClassDef)}
seg=lambda n:'\n'.join(lines[n.lineno-1:n.end_lineno])
def parts(c):
    consts={};meths={};order=[]
    for n in C[c].body:
        if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name): consts[n.targets[0].id]=seg(n)
        elif isinstance(n,ast.FunctionDef): meths[n.name]=seg(n); order.append(n.name)
        else: raise SystemExit('unexpected node in class')
    return consts,meths,order
Fc,Fm,Fo=parts('_FallbackPolicy'); Sc,Sm,So=parts('_SpecialistPolicy')
shared_c={k:v for k,v in Fc.items() if Sc.get(k)==v}
shared_m=[k for k in Fo if k in Sm and Sm[k]==Fm[k]]
def build(dead_m=set(),dead_c=set()):
    out=['import math','from soccer import PlayerAction, TeamAction, TeamController','']
    out.append(seg([n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_clip'][0])); out.append('')
    out.append(seg([n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_unit'][0])); out.append('')
    def cls(name,base,consts,meths,order,skipc=(),skipm=()):
        out.append('class %s%s:'%(name,'(%s)'%base if base else ''))
        for k,v in consts.items():
            if k in skipc or k in dead_c: continue
            out.append(v)
        out.append('')
        for k in order:
            if k in skipm or k in dead_m: continue
            out.append(meths[k]); out.append('')
    cls('_Core',None,{k:v for k,v in shared_c.items() if k not in('name','version')},{k:Fm[k] for k in shared_m},shared_m)
    cls('_FallbackPolicy','_Core',Fc,Fm,Fo,skipc=set(shared_c)-{'name','version'},skipm=set(shared_m))
    cls('_SpecialistPolicy','_Core',Sc,Sm,So,skipc=set(shared_c)-{'name','version'},skipm=set(shared_m))
    ad=[n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='AdaptiveChampion'][0]
    out.append(seg(ad)); out.append('')
    return '\n'.join(out)
dead_m=set();dead_c=set()
while True:
    s=build(dead_m,dead_c); cnt=lambda n:len(re.findall(r'\b%s\b'%re.escape(n),s))
    new_m={m for m in set(Fm)|set(Sm) if m not in dead_m and cnt(m)==0}   # not defined anywhere any more -> nothing
    # a method is dead when its name occurs only in its own def line(s)
    defs=lambda n:len(re.findall(r'def %s\('%re.escape(n),s))
    nm={m for m in (set(Fm)|set(Sm)) if m not in dead_m and cnt(m)==defs(m) and m not in('__init__','act','reset','initial_formation')}
    nc={c for c in (set(Fc)|set(Sc)) if c not in dead_c and cnt(c)==len(re.findall(r'^\s+%s = '%re.escape(c),s,re.M)) and c not in ('name','version')}
    if not nm and not nc: break
    dead_m|=nm; dead_c|=nc
print('shared methods',len(shared_m),'dead methods',sorted(dead_m),'dead consts',sorted(dead_c),file=sys.stderr)
s=build(dead_m,dead_c); s=re.sub(r'\n{3,}','\n\n',s)
open('team12_clean.py','w').write(s); print(len(s.split('\n')),'lines',file=sys.stderr)
