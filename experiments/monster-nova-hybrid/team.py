import math
from time import perf_counter
from bisect import bisect_left
from itertools import permutations
from soccer import TeamController
sqrt = math.sqrt
DT = 0.05
F = 0.985
KR = 2.2
H = 64
G = tuple((DT * (1 - F ** k) / (1 - F) for k in range(H + 1)))
FK = tuple((DT * F ** k for k in range(H + 1)))
D = tuple((0.45 * (1 - 0.9 ** k) for k in range(H + 1)))
_r = [0.0]
_v = 0.0
for _k in range(H):
    _v = min(8.0, 0.9 * _v + 1.0)
    _r.append(_r[-1] + _v * DT)
R = tuple(_r)
INF = 999
PERM4 = tuple(permutations(range(4)))
PERM3 = tuple(permutations(range(3)))
NOOP = {'movement': (0.0, 0.0)}
G14 = G[1:5]
D14 = D[1:5]
P9 = tuple((0.9 ** k for k in range(H + 1)))
R18 = tuple((r + 1.8 for r in R))
R20 = tuple((r + 2.0 for r in R))
RKR = tuple((r + KR for r in R))
_RO = {}
RGRID = tuple(((dx_, dy_, 0.004 * (abs(dx_) + abs(dy_))) for dx_ in (-6.0, 0.0, 6.0) for dy_ in (-6.0, 0.0, 6.0)))

def ro_table(r, delay):
    """(R[k - delay] if k > delay else 0) + r for every k: an opponent's reach on a kicked path."""
    t = _RO.get((r, delay))
    if t is None:
        t = _RO[r, delay] = tuple(((R[k - delay] if k - delay > 0 else 0.0) + r for k in range(H + 1)))
    return t

def ball_path(bx, by, vx, vy, G=G, H=H, range=range, DT=DT, F=F):
    ex = bx + vx * G[H]
    ey = by + vy * G[H]
    if -49.5 < ex < 49.5 and -29.5 < ey < 29.5:
        return [(bx + vx * g, by + vy * g) for g in G]
    out = [(bx, by)]
    for _ in range(H):
        bx += vx * DT
        by += vy * DT
        vx *= F
        vy *= F
        if bx > 49.55:
            if -7.0 < by < 7.0:
                vx = vy = 0.0
                bx = 51.0
            else:
                bx, vx = (99.1 - bx, -vx * 0.75)
        elif bx < -49.55:
            if -7.0 < by < 7.0:
                vx = vy = 0.0
                bx = -51.0
            else:
                bx, vx = (-99.1 - bx, -vx * 0.75)
        if by > 29.55:
            by, vy = (59.1 - by, -vy * 0.75)
        elif by < -29.55:
            by, vy = (-59.1 - by, -vy * 0.75)
        out.append((bx, by))
    return out

def arrive(px, py, vx, vy, path, sp, r, delay, kmax=H, kmin=0, len=len, D=D, R=R, sqrt=sqrt, int=int, FK=FK, INF=INF):
    """First tick >= kmin at which a player can be within r of the ball on `path`."""
    k = kmin
    n = len(path) - 1
    if kmax > n:
        kmax = n
    while k <= kmax:
        qx, qy = path[k]
        dk = D[k]
        dx = qx - px - vx * dk
        dy = qy - py - vy * dk
        kk = k - delay
        reach = (R[kk] if kk > 0 else 0.0) + r
        g = sqrt(dx * dx + dy * dy) - reach
        if g <= 0.0:
            return k
        k += 1 + int(g / (sp * FK[k] + 0.85))
    return INF

def arrive0(px, py, vx, vy, path, sp, RR, kmax, kmin, D=D, FK=FK, P9=P9, sqrt=sqrt, int=int, INF=INF):
    """arrive() with no reaction delay and RR[k] = R[k] + r. Per tick the gap closes by at
    most the ball's step, the coast's step (0.045 |v| 0.9^k) and the reach's (0.4), so the
    skip bound is tighter than arrive()'s 0.85 and finds the same first tick."""
    k = kmin
    cvk = 0.045 * sqrt(vx * vx + vy * vy)
    while k <= kmax:
        qx, qy = path[k]
        dk = D[k]
        dx = qx - px - vx * dk
        dy = qy - py - vy * dk
        g = sqrt(dx * dx + dy * dy) - RR[k]
        if g <= 0.0:
            return k
        k += 1 + int(g / (sp * FK[k] + 0.4 + cvk * P9[k]))
    return INF

def line_arrive(sx, sy, wx, wy, sp, px, py, vx, vy, r, delay, kmax, kmin=1, G=G, D=D, R=R, FK=FK, sqrt=sqrt, int=int, INF=INF):
    """Same as arrive() for a straight kicked path s + w*G[k].

    The gap can close by at most the ball's step, the coast's step
    (0.045 |v| 0.9^k) and the reach's step (0.4) per tick, so whole stretches
    that cannot contain the first touch are skipped."""
    k = kmin
    cv = 0.4 + 0.045 * sqrt(vx * vx + vy * vy)
    while k <= kmax:
        g_ = G[k]
        dk = D[k]
        dx = sx + wx * g_ - px - vx * dk
        dy = sy + wy * g_ - py - vy * dk
        kk = k - delay
        reach = (R[kk] if kk > 0 else 0.0) + r
        g = sqrt(dx * dx + dy * dy) - reach
        if g <= 0.0:
            return k
        k += 1 + int(g / (sp * FK[k] + cv))
    return INF

def line_gap(sx, sy, wx, wy, px, py, vx, vy, r, delay, kmax, stop=-1000000000.0, range=range, G=G, D=D, R=R, sqrt=sqrt):
    """Smallest clearance (units) a player has to a straight path up to kmax; returns
    early with any clearance below `stop` (the caller then drops the shot anyway)."""
    best = 99.0
    for k in range(1, kmax + 1):
        g_ = G[k]
        dk = D[k]
        dx = sx + wx * g_ - px - vx * dk
        dy = sy + wy * g_ - py - vy * dk
        kk = k - delay
        reach = (R[kk] if kk > 0 else 0.0) + r
        g = sqrt(dx * dx + dy * dy) - reach
        if g < best:
            best = g
            if g < stop:
                return g
    return best

def solve_kick(ux, uy, speed, bvx, bvy, sqrt=sqrt, min=min):
    """Kick so the ball leaves along (ux, uy) at `speed` (or the most it can)."""
    ud = ux * bvx + uy * bvy
    disc = ud * ud - (bvx * bvx + bvy * bvy) + 484.0
    smax = ud + sqrt(disc) if disc > 0.0 else 0.0
    if smax > 30.0:
        smax = 30.0
    s = speed if speed < smax else smax
    if s < 0.5:
        return None
    ix = s * ux - bvx
    iy = s * uy - bvy
    m = sqrt(ix * ix + iy * iy)
    if m < 1e-06:
        return None
    return (ix / m, iy / m, min(1.0, m / 22.0), s * ux, s * uy, s)

def unit(dx, dy, sqrt=sqrt):
    d = sqrt(dx * dx + dy * dy)
    if d < 1e-09:
        return (1.0, 0.0)
    return (dx / d, dy / d)

def self_clear(bx, by, wx, wy, px, py, vx, vy, G=G, D=D):
    """Does a kicked ball clear the kicker's own (coasting) body for 4 ticks?"""
    for k in (1, 2, 3, 4):
        g_ = G[k]
        dk = D[k]
        dx = bx + wx * g_ - px - vx * dk
        dy = by + wy * g_ - py - vy * dk
        if dx * dx + dy * dy < 2.4:
            return False
    return True

def deflect_path(bx, by, wx, wy, px, py, vx, vy):
    """Path of a kicked ball that may run into the kicker's own (coasting) body.

    Measured from the engine: on contact the part of the ball's velocity
    (relative to the player) that points into the body is removed and the
    rest carries on."""
    for k in (1, 2, 3, 4):
        g_ = G[k]
        dk = D[k]
        qx = bx + wx * g_
        qy = by + wy * g_
        dx = qx - px - vx * dk
        dy = qy - py - vy * dk
        d2 = dx * dx + dy * dy
        if d2 < 2.4:
            d = sqrt(d2) or 1.0
            nx = dx / d
            ny = dy / d
            fb = F ** k
            fp = 0.9 ** k
            rx = wx * fb - vx * fp
            ry = wy * fb - vy * fp
            vn = rx * nx + ry * ny
            if vn < 0.0:
                rx -= vn * nx
                ry -= vn * ny
            head = [(bx + wx * G[j], by + wy * G[j]) for j in range(k)]
            return ((head + ball_path(qx, qy, vx * fp + rx, vy * fp + ry))[:H + 1], True)
    return (ball_path(bx, by, wx, wy), False)
DRIB_ANG = (0, 6, 12, 18, 24, 30, 37, 44, 52, 60, 70, 80, 92, 105, 120, 140, 160, 180)
PASS_ANG = (0, 12, 24, 37, 52, 70, 92, 120, 160)
DRIB_SPEEDS = (6.0, 9.0, 12.0)
PASS_SPEEDS = (14.0, 19.0, 24.0, 30.0)

def _cands():
    out = []
    for a in sorted(set(DRIB_ANG) | set(PASS_ANG)):
        sp = (DRIB_SPEEDS if a in DRIB_ANG else ()) + (PASS_SPEEDS if a in PASS_ANG else ())
        for s in (a, -a) if 0 < a < 180 else (a,):
            r = math.radians(s)
            out.append((math.cos(r), math.sin(r), sp))
    return tuple(out)
CANDS = _cands()
CACHE_N = 3
SP_BND = 0
KS_ORD = 0
KICK_BUDGET = 0.014
OPEN_W = 0.04
PK0 = 0.3
PK1 = 0.1
OPP_R = 2.2
OPP_DELAY = 1
SHOT_MIN = 0.3
CLR_X = 99.0
SB_X = 20.0
SB_W = 0.0
KC_X = -16.0
KC_M = 0.05
CLR_T = 0.002
CLR_SPEEDS = (30.0, 20.0)
CLR_DIRS = tuple(((math.cos(math.radians(a)), math.sin(math.radians(a))) for a in (0, 10, -10, 20, -20, 30, -30, 40, -40, 50, -50, 60, -60, 70, -70, 80, -80, 90, -90, 105, -105, 120, -120)))
SHOT_REL = 0.75
PRESS = 4.0
LANE_D = 30
LANE_Y = 5.0
LANE_FIRST = 'near'
LANE_COV = 3.5
COVD = 29.0
MARKX = 20.0
GOAL_YS = (-6.5, 6.5, -5.8, 5.8, -4.5, 4.5, -3.0, 3.0, -1.5, 1.5, 0.0)
CT_ATT = 20
CT_OWN = 15
KP_PRED = 30
WALL_N = 4
WALL_D = 6
WALL_R = 2.2
WALL_YS = (-6.4, 6.4, -4.2, 4.2, -1.4, 1.4)
PB_N = 5
PB_LN = 4
PB_L = 48.0
PB_SPAN = 9.0
PB_X = 30.0
PB_FX = 46.5
PB_DY = 2.0
SHOT_GD = 62.0
MK_G = 2.0
MK_B = 1.5
KD_F = 0.27
KD_MAX = 12.0
SR_ADD = 0.0
KP_R = 2.0
KP_FB = 1
LL_T = 0.0
LL_SMIN = 0.15
LL_REL = 0.4
LL_RCAP = 0.0
LL_REST = 0.0
BYL_X = 0.0
BYL_Y = 18.0
BYL_Q = 15.0
FAR_DX = 0.0
WIDE_X = -99.0
WIDE_Y = 24.0
RUN_YF = 10.0
RUN_YN = 8.0
SUP_DX = 8.0
SUP_Y = 7.0
REST_DX = 22.0
REST_MAX = 5.0
PS_T = 0
PS_P = 0.05
WB_X = -99.0
WB_Y = 12.0
WB_D = 4.0
SHV = 0.0
RUN_DX = 22.0
RUN_CAP = 41.0
ES_X = 0.0
ES_Y = 8.0
KB0 = 0.0
KB_M = 2.0
CB_X = -36.0
CB_Y = 8.0
CB_ZX = -40.0
CB_ZYF = 0.2
TEMPO = 0.0
TEMPO_T = 0.001
DEF2 = 0
D2_LOOK = 10
D2_BLK = 1.5
D2_COV = 0.12
D2_MKMIN = 0.06
D2_ZX = -41.0
D2_COVH = 0.3
D2_MG = 2.0
D2_MB = 1.5
CR_N = 99
CR_X = 38.0
CR_Y = 14.0
CR_T = 120
CR_P = 0.0
CR_PIN = 1
FAR_YS = (-4.5, 4.5, 0.0)
CNT_B = 1.0
TB_M = 0
TB_B = 0.05
TB_BT = 1.0
TB_T = 0.0
TB_SMIN = 0.15
TB_REL = 0.4
TB_X = 0.0
KG_Y = 14.0
BL_T = 0.0
BL_SMIN = 0.15
BL_REL = 0.4
BL_RCAP = 0.0
BL_REST = 0.0
OPP_R_T = 2.4
PK1_T = 0.0
ORT_BH = 0
ORT_LT = 0.0
DRB_B = 0.0
PAS_B = 0.0
PLEN_B = 0.0
CS_B = 0.0
CS_X = 12.0
CS_U = 0.6
HSP_B = 0.0
BK_N = 0
BK_T = 60
BK_TEMPO = 0.0
BK_SMIN = 0.3
BK_REL = 0.75
BK_SHARP = 0
RU_D = 0
RU_SMIN = 0.3
RU_REL = 0.75
RU_RCAP = 0.0
RU_REST = 0.0
TK_R = 0.0
TK_L = 1.0
TR_T = 0
TR_TEMPO = 0.0
TR_SMIN = 0.3
TR_REL = 0.75
HP_Q = 15.0
HP_X = 35.0
MK2_X = -99.0
MK_LEAD = 0.3
CNT_X = 0
CNT_PW = (1.0, 0.8, 0.6)
KO_T = 0
KO_KD = 0.0
KO_ENG = 0
KO_SCR = 0.0
KO_SHP = 0
KO_SD = (10.0, 16.0, 22.0)
KO_SW = 4.0
CH_X = -99.0
CH_N = 3
ED_R = 0.0
ED_D = 4.0
SW_B = 0.0
SW_DY = 6.0
SW_N = 4
LB_X = 99.0
LB_Y = 12.0
LB_PX = 38.0
LB_PY = 0.15
BA_X = 99.0
BA_Y = 16.0
BA_N = 1
BA_SMIN = 0.3
BA_REL = 0.75
SP_MODE = 0
SP_C = 0.1
SP_S = 0.4
SP_TIGHT = 0
GX = ((-9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0), (-9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0), (-9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0), (-9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0), (-9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0), (-9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0), (-9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0), (-9.0, -8.85, -8.87, -8.9, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0), (-8.03, -8.06, -7.68, -7.71, -8.16, -8.33, -8.81, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0), (-6.84, -6.87, -6.49, -6.52, -7.05, -7.5, -7.71, -8.22, -8.47, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0, -9.0), (-5.66, -5.69, -5.74, -5.81, -6.22, -6.42, -6.65, -7.17, -7.72, -8.28, -8.86, -9.0, -9.0, -9.0, -9.0, -9.0), (-4.84, -4.5, -4.55, -4.61, -5.16, -5.38, -5.88, -6.16, -6.71, -7.28, -7.87, -8.46, -9.0, -9.0, -9.0, -9.0), (-3.68, -3.72, -3.8, -3.89, -4.36, -4.62, -4.89, -5.44, -6.01, -6.6, -7.2, -7.8, -8.71, -9.0, -9.0, -9.0), (-2.87, -2.93, -2.61, -2.68, -3.38, -3.65, -4.19, -4.75, -5.08, -5.67, -6.56, -7.17, -7.77, -8.69, -9.0, -9.0), (-2.05, -1.79, -1.88, -1.98, -2.62, -2.93, -3.48, -3.85, -4.43, -5.06, -5.68, -6.57, -7.17, -8.1, -9.0, -9.0), (-1.23, -1.02, -1.14, -1.28, -1.92, -2.27, -2.62, -3.23, -3.84, -4.48, -5.11, -5.99, -6.59, -7.52, -8.44, -9.0), (-0.41, -0.26, -0.42, -0.08, -1.09, -1.59, -2.02, -2.63, -3.28, -3.94, -4.57, -5.5, -6.41, -6.93, -7.84, -8.71), (0.39, 0.47, 0.68, 0.55, -0.43, -1.01, -1.48, -2.1, -2.76, -3.41, -4.37, -4.98, -5.91, -6.83, -7.74, -8.62), (1.14, 1.14, 1.27, 1.1, 0.1, -0.48, -1.02, -1.66, -2.33, -3.24, -3.87, -4.8, -5.33, -6.22, -7.08, -7.89), (1.8, 1.78, 1.74, 1.54, 0.37, -0.05, -0.76, -1.32, -2.12, -2.87, -3.77, -4.36, -5.27, -6.15, -6.99, -7.78), (2.31, 2.3, 2.05, 1.83, 0.4, 0.02, -0.49, -1.21, -1.88, -2.77, -3.42, -4.32, -5.21, -6.06, -6.87, -7.6), (2.54, 2.53, 2.31, 1.92, 0.17, -0.12, -0.52, -1.16, -1.94, -2.58, -3.43, -4.28, -5.13, -5.93, -6.67, -7.33), (2.43, 2.42, 2.19, 1.76, -0.36, -0.45, -0.78, -1.33, -2.08, -2.67, -3.41, -4.19, -4.96, -5.67, -6.31, -7.9), (1.75, 1.75, 1.61, 1.29, -0.75, -0.97, -1.13, -1.64, -2.28, -2.98, -3.83, -3.87, -5.51, -6.23, -6.84, -7.37), (3.0, 3.0, 0.36, 0.25, -0.67, -1.33, -1.67, -2.03, -2.57, -3.16, -3.81, -4.39, -4.97, -5.52, -7.25, -7.72), (3.0, 3.0, 3.0, 3.0, -1.16, -1.63, -1.91, -2.31, -2.84, -3.45, -4.03, -4.56, -5.1, -5.63, -6.11, -7.82))
XG = tuple((tuple((1.0 / (1.0 + math.exp(-(g - 0.1) / 0.4)) for g in row)) for row in GX))

def xg(x, y, int=int, XG=XG):
    """Chance that an unhurried shot from (x, y) scores (bilinear on the grid)."""
    if x <= 0.0:
        return 0.0
    fx = x * 0.5
    if fx >= 24.999:
        fx = 24.999
    fy = (y if y > 0.0 else -y) * 0.5
    if fy >= 14.999:
        fy = 14.999
    i = int(fx)
    j = int(fy)
    ax = fx - i
    ay = fy - j
    r0 = XG[i]
    r1 = XG[i + 1]
    return (r0[j] * (1 - ay) + r0[j + 1] * ay) * (1 - ax) + (r1[j] * (1 - ay) + r1[j + 1] * ay) * ax
VUS = ((-0.037, -0.031, -0.024, -0.015, -0.025, -0.037), (-0.025, -0.003, 0.012, 0.005, -0.006, -0.013), (0.004, 0.028, 0.045, 0.047, 0.022, 0.012), (0.028, 0.051, 0.065, 0.067, 0.057, 0.035), (0.052, 0.066, 0.078, 0.083, 0.077, 0.076), (0.074, 0.076, 0.086, 0.085, 0.094, 0.092), (0.084, 0.094, 0.09, 0.091, 0.089, 0.1), (0.111, 0.1, 0.115, 0.105, 0.097, 0.089), (0.123, 0.124, 0.113, 0.115, 0.098, 0.098), (0.124, 0.129, 0.138, 0.112, 0.107, 0.098), (0.122, 0.138, 0.156, 0.141, 0.109, 0.103), (0.144, 0.143, 0.167, 0.152, 0.123, 0.107), (0.175, 0.178, 0.169, 0.156, 0.131, 0.115), (0.229, 0.213, 0.186, 0.159, 0.138, 0.129), (0.337, 0.285, 0.217, 0.178, 0.154, 0.141), (0.446, 0.379, 0.293, 0.215, 0.177, 0.154), (0.541, 0.476, 0.368, 0.265, 0.193, 0.161), (0.629, 0.549, 0.391, 0.268, 0.198, 0.157), (0.722, 0.544, 0.342, 0.242, 0.184, 0.154), (0.823, 0.423, 0.272, 0.225, 0.173, 0.146))
VOP = ((-0.129, -0.116, -0.113, -0.122, -0.122, -0.113), (-0.101, -0.099, -0.097, -0.107, -0.114, -0.116), (-0.07, -0.065, -0.071, -0.078, -0.093, -0.092), (-0.041, -0.043, -0.048, -0.059, -0.069, -0.07), (-0.019, -0.021, -0.029, -0.044, -0.057, -0.057), (0.005, 0.004, -0.007, -0.024, -0.034, -0.03), (0.026, 0.016, 0.011, 0.002, -0.009, -0.014), (0.029, 0.02, 0.018, 0.015, -0.003, -0.007), (0.019, 0.02, 0.021, 0.02, 0.011, 0.001), (0.017, 0.015, 0.029, 0.036, 0.023, 0.021), (0.014, 0.02, 0.029, 0.04, 0.034, 0.029), (0.024, 0.026, 0.038, 0.046, 0.039, 0.034), (0.063, 0.059, 0.059, 0.06, 0.05, 0.047), (0.12, 0.107, 0.092, 0.07, 0.057, 0.052), (0.185, 0.171, 0.128, 0.081, 0.058, 0.058), (0.304, 0.258, 0.179, 0.097, 0.067, 0.061), (0.432, 0.364, 0.229, 0.118, 0.078, 0.07), (0.525, 0.438, 0.253, 0.12, 0.088, 0.079), (0.614, 0.412, 0.187, 0.111, 0.084, 0.082), (0.634, 0.239, 0.117, 0.089, 0.084, 0.076))

def vtab(T, x, y, int=int):
    fx = (x + 47.5) * 0.2
    if fx < 0.0:
        fx = 0.0
    elif fx > 18.999:
        fx = 18.999
    fy = ((y if y > 0.0 else -y) - 2.5) * 0.2
    if fy < 0.0:
        fy = 0.0
    elif fy > 4.999:
        fy = 4.999
    i = int(fx)
    j = int(fy)
    ax = fx - i
    ay = fy - j
    r0 = T[i]
    r1 = T[i + 1]
    return (r0[j] * (1 - ay) + r0[j + 1] * ay) * (1 - ax) + (r1[j] * (1 - ay) + r1[j + 1] * ay) * ax

def _rectmax(T):
    ni, nj = (len(T) - 1, len(T[0]) - 1)
    cm = [[max(T[i][j], T[i + 1][j], T[i][j + 1], T[i + 1][j + 1]) for j in range(nj)] for i in range(ni)]
    rm = {}
    for i0 in range(ni):
        for j0 in range(nj):
            for i1 in range(i0, ni):
                for j1 in range(j0, nj):
                    rm[i0, i1, j0, j1] = max((cm[i][j] for i in range(i0, i1 + 1) for j in range(j0, j1 + 1)))
    return rm
VUS_RECT = _rectmax(VUS)

def vus_bound(xa, ya, xb, yb, int=int, min=min, max=max, VUS_RECT=VUS_RECT):
    return _vus_bound_impl(xa, ya, xb, yb, VUS_RECT)

def _vus_bound_impl(xa, ya, xb, yb, VUS_RECT, int=int, min=min, max=max):
    """An upper bound of pos_value over the segment (xa, ya)-(xb, yb) in the pitch."""
    if xa > xb:
        xa, xb = (xb, xa)
    if xa < -49.0:
        xa = -49.0
    if xb > 49.0:
        xb = 49.0
    if xb < xa:
        return -9.0
    if ya > yb:
        ya, yb = (yb, ya)
    if ya < -29.0:
        ya = -29.0
    if yb > 29.0:
        yb = 29.0
    if yb < ya:
        return -9.0
    if ya <= 0.0 <= yb:
        lo = 0.0
        hi = yb if yb > -ya else -ya
    elif ya > 0.0:
        lo, hi = (ya, yb)
    else:
        lo, hi = (-yb, -ya)
    i0 = int(min(18.999, max(0.0, (xa + 47.5) * 0.2)))
    i1 = int(min(18.999, max(0.0, (xb + 47.5) * 0.2)))
    j0 = int(min(4.999, max(0.0, (lo - 2.5) * 0.2)))
    j1 = int(min(4.999, max(0.0, (hi - 2.5) * 0.2)))
    return VUS_RECT[i0, i1, j0, j1]

def pos_value(x, y, vtab=vtab, VUS=VUS):
    return vtab(VUS, x, y)
OS_F = 0.0

def open_shot(qx, qy, tm, O, sp=None):
    """Chance a shot from a reception point (qx, qy) at tick tm would score:
    the widest of four lanes to goal, against defenders that coast until the
    ball arrives and then close at full reach while the shot flies."""
    best = -9.0
    dt = D[tm] if tm < H else D[H]
    for gy in (-5.5, 5.5, -2.0, 2.0):
        dx = 50.0 - qx
        dy = gy - qy
        L = sqrt(dx * dx + dy * dy) or 1.0
        ux = dx / L
        uy = dy / L
        gap = 99.0
        for ox, oy, ovx, ovy, cd in O:
            ex = ox + ovx * dt - qx
            ey = oy + ovy * dt - qy
            s = ex * ux + ey * uy
            if s < 0.0:
                s = 0.0
            elif s > L:
                s = L
            px = ex - ux * s
            py = ey - uy * s
            kk = int(s * 0.8 + OS_F * tm)
            if kk > H:
                kk = H
            g = sqrt(px * px + py * py) - R[kk] - 1.8
            if g < gap:
                gap = g
                if gap <= best:
                    break
        if gap > best:
            best = gap
    return shot_p(best) if sp is None else sp(best)

def shot_p(gap):
    if gap > 3.0:
        return 0.999
    if gap < -4.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-(gap - 0.1) / 0.4))
VUS_OLD = VUS
VUS_RECT_OLD = VUS_RECT
VT_SWITCH = 2
VUS = ((-0.037, -0.0237, 0.015, 0.0263, 0.0017, -0.0053), (0.0021, 0.0238, 0.0609, 0.0626, 0.0192, 0.0102), (0.0525, 0.0678, 0.0839, 0.073, 0.0384, 0.0158), (0.0823, 0.0999, 0.1027, 0.096, 0.0653, 0.0413), (0.1055, 0.1183, 0.1289, 0.12, 0.0961, 0.0796), (0.1325, 0.1111, 0.1239, 0.122, 0.1285, 0.0992), (0.1588, 0.1607, 0.1669, 0.1354, 0.1394, 0.1235), (0.2191, 0.2189, 0.2364, 0.2121, 0.1744, 0.1379), (0.2873, 0.2817, 0.2392, 0.217, 0.1928, 0.167), (0.2625, 0.2928, 0.2884, 0.2483, 0.2114, 0.1627), (0.2538, 0.2975, 0.3043, 0.2852, 0.2396, 0.1785), (0.2993, 0.3124, 0.3163, 0.2738, 0.2283, 0.1887), (0.3247, 0.3355, 0.3267, 0.2693, 0.2319, 0.1837), (0.3717, 0.3569, 0.313, 0.2665, 0.2261, 0.1855), (0.4309, 0.3963, 0.3225, 0.2741, 0.2306, 0.184), (0.4792, 0.431, 0.359, 0.2825, 0.2287, 0.1904), (0.5365, 0.4831, 0.3886, 0.2971, 0.2374, 0.1956), (0.6369, 0.5536, 0.4088, 0.3095, 0.2422, 0.1968), (0.7693, 0.6049, 0.3962, 0.3049, 0.2352, 0.1997), (0.8213, 0.5534, 0.323, 0.2798, 0.2264, 0.1938))
VUS_RECT = _rectmax(VUS)

def shot_p2(gap, exp=math.exp):
    if gap > 3.0:
        return 0.999
    if gap < -4.0:
        return 0.0
    return 1.0 / (1.0 + exp(-(gap - SP_C) / SP_S))
XG2 = tuple((tuple((1.0 / (1.0 + math.exp(-(g - SP_C) / SP_S)) for g in row)) for row in GX)) if SP_MODE >= 2 else XG
CANDS = _cands()

class _NovaPolicy:
    name = 'nova_fc'
    version = '31s'

    def __init__(self):
        self._chaser = None
        self._plan = None
        self._roles = {}
        self._ko_wait = 0
        self._cache = None
        self._own_since = 0
        self._crowd = False
        self._sh = [0, 0]
        self._tbb = 0.0
        self._tbl = False
        self._oko = None
        self._oko_k = None
        self._kod = False

    def reset(self, seed):
        self._chaser = None
        self._plan = None
        self._roles = {}
        self._ko_wait = 0
        self._cache = None
        self._own_since = 0
        self._crowd = False
        self._sh = [0, 0]
        self._tbb = 0.0
        self._tbl = False
        self._oko = None
        self._oko_k = None
        self._kod = False
        self._kt = [False, False, 0, -999]
        self._kt_sc = 0

    def act(self, obs):
        try:
            return self._act(obs)
        except Exception:
            self._cache = None
            ball = obs.ball.position
            acts = {i: NOOP for i in range(len(obs.my_players))}
            p = obs.closest_my_player_to(ball)
            if p is not None:
                d = unit(ball[0] - p.position[0], ball[1] - p.position[1])
                if obs.can_kick(p.id):
                    acts[p.id] = {'movement': d, 'kick_direction': unit(50.0 - ball[0], -ball[1]), 'kick_power': 1.0}
                else:
                    acts[p.id] = {'movement': d}
            return acts

    def _act(self, obs, CT_ATT=CT_ATT, CT_OWN=CT_OWN, KP_PRED=KP_PRED, F=F, sqrt=sqrt, ball_path=ball_path, arrive=arrive, H=H, KR=KR, min=min, len=len, range=range, unit=unit, D=D, R=R, list=list, NOOP=NOOP, CACHE_N=CACHE_N, INF=INF, arrive0=arrive0, R20=R20, RKR=RKR):
        self._t_act = perf_counter()
        tick = obs.tick
        self._late = LL_T > 0.0 and obs.time_remaining < LL_T and (obs.score[0] == obs.score[1])
        self._behind = BL_T > 0.0 and obs.time_remaining < BL_T and (obs.score[0] < obs.score[1])
        self._alt = VT_SWITCH > 0 and obs.score[0] - obs.score[1] >= VT_SWITCH
        dsc = obs.score[0] - obs.score[1]
        self._ruth = RU_D > 0 and dsc >= RU_D
        self._sharp = self._alt or (ORT_BH and dsc < 0) or (dsc == 0 and obs.time_remaining < ORT_LT)
        ball = obs.ball
        bvx, bvy = ball.velocity
        if ball.controlling_team != 0:
            self._own_since = tick
        self._trans = TR_T > 0 and tick - self._own_since < TR_T
        if BK_N:
            bx0 = ball.position[0]
            if ball.controlling_team != 1 and 0.0 <= bx0 < 30.0:
                nb = 0
                for o in obs.opponents:
                    if o.position[0] > bx0:
                        nb += 1
                if nb - 1 >= BK_N:
                    if getattr(self, '_bk_since', None) is None:
                        self._bk_since = tick
                else:
                    self._bk_since = None
            else:
                self._bk_since = None
            self._block = self._bk_since is not None and tick - self._bk_since >= BK_T
        else:
            self._block = False
        cache = self._cache
        if cache is not None:
            self._cache = None
            if tick <= cache[0] and (not obs.events):
                dvx = bvx - cache[1]
                dvy = bvy - cache[2]
                if -0.25 < dvx < 0.25 and -0.25 < dvy < 0.25:
                    bx, by = ball.position
                    for p in obs.my_players:
                        px, py = p.position
                        px -= bx
                        py -= by
                        if px * px + py * py < 7.3:
                            break
                    else:
                        self._cache = (cache[0], bvx * F, bvy * F, cache[3])
                        return cache[3]
        bx, by = ball.position
        me = obs.my_players
        P = [p.position + p.velocity + (p.kick_cooldown_ticks,) for p in me]
        O = [o.position + o.velocity + (o.kick_cooldown_ticks,) for o in obs.opponents]
        sp = sqrt(bvx * bvx + bvy * bvy)
        path = ball_path(bx, by, bvx, bvy)
        if CR_N < 9:
            nb = 0
            for o in O:
                if o[0] > CR_X and -CR_Y < o[1] < CR_Y:
                    nb += 1
            self._crowd = nb >= CR_N and tick - self._own_since >= CR_T
        for ev in obs.events:
            kind = ev.get('kind')
            if kind == 'kick':
                team = ev.get('team')
                if team == 1:
                    self._plan = None
                    self._opp_kick = tick
                if KO_T and self._oko is not None:
                    if team == 1:
                        if self._oko_k is None:
                            self._oko_k = ev.get('player')
                        elif ev.get('player') != self._oko_k:
                            self._oko = None
                    else:
                        self._oko = None
                if ev.get('power', 0.0) >= 0.5:
                    pid = ev.get('player')
                    dr = ev.get('direction') or {}
                    dx = dr.get('x', 0.0)
                    dy = dr.get('y', 0.0)
                    sg = 1.0 if team == 0 else -1.0
                    for q in me if team == 0 else obs.opponents:
                        if q.id == pid:
                            qx, qy = q.position
                            if sg * qx > 0.0 and sg * dx > 1e-09 and (-7.0 <= qy + (sg * 50.0 - qx) / dx * dy <= 7.0):
                                self._sh[0 if team == 0 else 1] += 1
                            break
            elif kind == 'goal':
                self._opp_kick = tick
        tb = (TB_B or TB_T) and obs.score[0] == obs.score[1] and (self._sh[0] <= self._sh[1] + TB_M)
        self._tbb = TB_B if tb and obs.time_remaining < TB_BT else 0.0
        self._tbl = bool(tb) and obs.time_remaining < TB_T
        my_t = [INF] * 5
        m_ = H
        prev_ = self._chaser
        for i in (prev_,) + tuple((j for j in (1, 2, 3, 4) if j != prev_)) if prev_ in (1, 2, 3, 4) else (1, 2, 3, 4):
            px, py, vx, vy, cd = P[i]
            t = arrive0(px, py, vx, vy, path, sp, R20, m_ + 4 if m_ + 4 < H else H, cd)
            my_t[i] = t
            if t < m_:
                m_ = t
        px, py, vx, vy, cd = P[0]
        my_t[0] = arrive0(px, py, vx, vy, path, sp, R20, m_ + 4 if m_ + 4 < H else H, cd)
        t_them, j_them = (INF, 0)
        j = 0
        for px, py, vx, vy, cd in O:
            t = arrive0(px, py, vx, vy, path, sp, RKR, H if t_them >= INF else t_them - 1, cd)
            if t < t_them:
                t_them, j_them = (t, j)
            j += 1
        c = 1
        for i in (2, 3, 4):
            if my_t[i] < my_t[c]:
                c = i
        plan = self._plan
        if plan is not None:
            if tick > plan[1]:
                self._plan = plan = None
            elif plan[0] != 0 and my_t[plan[0]] <= my_t[c] + 3:
                c = plan[0]
        prev = self._chaser
        if plan is None and prev is not None and (prev != 0) and (my_t[prev] <= my_t[c] + 1):
            c = prev
        keeper_goes = False
        if my_t[0] < my_t[c] - 1 and my_t[0] < t_them:
            kq = path[my_t[0]] if my_t[0] < len(path) else path[-1]
            keeper_goes = kq[0] < -30.0 and -KG_Y < kq[1] < KG_Y and (my_t[0] < t_them - 2 or kq[0] < -38.0)
        if keeper_goes:
            c = 0
        self._chaser = c
        t_us = my_t[c]
        ctl = ball.controlling_team
        at_spot = bx * bx + by * by < 0.25 and sp < 0.1
        their_ko = at_spot and ctl == 1
        if their_ko:
            self._ko_wait += 1
            if self._ko_wait > 61:
                their_ko = False
        else:
            self._ko_wait = 0
        if KO_T:
            if their_ko:
                self._oko = tick
                self._oko_k = None
            elif self._oko is not None and tick - self._oko > KO_T:
                self._oko = None
            self._kod = self._oko is not None and (not their_ko)
        ours = t_us < t_them or (t_us == t_them and ctl == 0)
        acts = {}
        targets = {}
        kick_ids = [i for i in range(5) if P[i][4] == 0 and (P[i][0] - bx) ** 2 + (P[i][1] - by) ** 2 <= KR * KR]
        qtx = path[t_them][0] if t_them < len(path) else path[-1][0]
        contest = ours or c == 0 or t_us <= t_them + (CT_ATT if qtx > 0.0 else CT_OWN)
        if kick_ids and (not their_ko):
            k = c if c in kick_ids else min(kick_ids, key=lambda i: (P[i][0] - bx) ** 2 + (P[i][1] - by) ** 2)
            acts[k] = self._kick(k, bx, by, bvx, bvy, P, O, tick)
            c = k
            ours = True
        elif contest:
            if t_us < len(path):
                qx, qy = path[t_us]
                margin = t_them - t_us
                if margin >= 4 and t_us > 0 and (sp < 3.0):
                    ex, ey = unit(50.0 - qx, -qy * 0.5)
                    ox_, oy_ = (qx - ex * 1.6, qy - ey * 1.6)
                    px, py, vx, vy, _ = P[c]
                    dx = ox_ - px - vx * D[t_us]
                    dy = oy_ - py - vy * D[t_us]
                    if dx * dx + dy * dy <= (R[t_us] + 0.5) ** 2:
                        qx, qy = (ox_, oy_)
                targets[c] = (qx, qy, True, t_us)
            else:
                qx, qy = path[-1]
                targets[c] = (qx, qy, True, None)
        else:
            c = -1
        eng = KO_ENG and self._kod
        if not eng and bx < CH_X and (t_them <= 2):
            gs = 0
            for i in range(5):
                if P[i][0] < bx - 1.0:
                    gs += 1
            eng = gs > CH_N
        if eng and c != 0 and (not kick_ids) and (not ours):
            ox_, oy_, ovx_, ovy_ = (O[j_them][0], O[j_them][1], O[j_them][2], O[j_them][3])
            bi, bd = (1, 1000000000.0)
            for i in (1, 2, 3, 4):
                dx_ = P[i][0] - bx
                dy_ = P[i][1] - by
                d_ = dx_ * dx_ + dy_ * dy_
                if d_ < bd:
                    bi, bd = (i, d_)
            gx_, gy_ = unit(-50.0 - bx, -by)
            px_, py_, pvx_, pvy_ = (P[bi][0], P[bi][1], P[bi][2], P[bi][3])
            tg_ = None
            for k_ in range(0, 41, 2):
                cx_ = bx + ovx_ * 0.05 * k_ + gx_ * 1.5
                cy_ = by + ovy_ * 0.05 * k_ + gy_ * 1.5
                dx_ = cx_ - px_ - pvx_ * D[k_]
                dy_ = cy_ - py_ - pvy_ * D[k_]
                if dx_ * dx_ + dy_ * dy_ <= R[k_] * R[k_] or k_ == 40:
                    tg_ = (cx_, cy_, True, k_)
                    break
            if c > 0 and c != bi:
                targets.pop(c, None)
            c = bi
            targets[c] = tg_
        if TK_R > 0.0 and c != 0 and (not kick_ids) and (not their_ko) and (ball.controlling_team == 1):
            ovx_, ovy_ = (O[j_them][2], O[j_them][3])
            bi, bd = (-1, TK_R)
            for i in (1, 2, 3, 4):
                dx_ = P[i][0] - bx
                dy_ = P[i][1] - by
                d_ = sqrt(dx_ * dx_ + dy_ * dy_)
                if d_ < bd:
                    bi, bd = (i, d_)
            if bi > 0:
                if c > 0 and c != bi:
                    targets.pop(c, None)
                c = bi
                tt = bd / 8.0 * TK_L
                targets[c] = (bx + ovx_ * tt, by + ovy_ * tt, True, None)
        if 0 not in acts and c != 0:
            if not ours and t_them < KP_PRED:
                kq = path[t_them]
                targets[0] = self._keeper(bx, by, bvx, bvy, path, ours, P, kq[0], kq[1])
            else:
                targets[0] = self._keeper(bx, by, bvx, bvy, path, ours, P, bx, by)
        free = [i for i in range(1, 5) if i != c and i not in acts]
        if ours:
            nw = nl = 0
            ylo, yhi = (9.0, -9.0)
            for o in O:
                if o[0] > 46.0 and -8.0 < o[1] < 8.0:
                    nw += 1
                    if o[0] > PB_L:
                        nl += 1
                        ylo = min(ylo, o[1])
                        yhi = max(yhi, o[1])
            pin = nw >= PB_N or (nl >= PB_LN and yhi - ylo >= PB_SPAN)
            spots = self._attack_spots(bx, by, path, t_us, O, len(free), pin or (self._crowd and CR_PIN))
        elif DEF2:
            spots = self._defend_spots2(bx, by, path, t_them, j_them, O, P, len(free))
        else:
            spots = self._defend_spots(bx, by, path, t_them, j_them, O, P, len(free))
        self._assign(free, spots, P, targets)
        if their_ko:
            lim = 10.2
            for pid, tg in list(targets.items()):
                tx, ty = (tg[0], tg[1])
                d = sqrt(tx * tx + ty * ty)
                if d < lim:
                    ux, uy = unit(tx, ty) if d > 0.5 else (-1.0, 0.0)
                    targets[pid] = (ux * lim, uy * lim, tg[2])
        for pid, tg in targets.items():
            acts[pid] = self._steer(P[pid], tg, their_ko)
        for i in range(5):
            if i not in acts:
                acts[i] = NOOP
        if not kick_ids and (not their_ko):
            near = min(min(my_t), t_them) - 2
            if near > CACHE_N:
                near = CACHE_N
            if near > 0:
                self._cache = (tick + near, bvx * F, bvy * F, acts)
        return acts

    def _steer(self, p, tg, guard, len=len, D=D, sqrt=sqrt, NOOP=NOOP):
        px, py, vx, vy, _ = p
        tx, ty, full = (tg[0], tg[1], tg[2])
        if len(tg) > 3 and tg[3] is not None and (not guard):
            k = tg[3]
            dx = tx - px - vx * D[k]
            dy = ty - py - vy * D[k]
            d = sqrt(dx * dx + dy * dy)
            if d < 1e-06:
                return NOOP
            return {'movement': (dx / d, dy / d)}
        if tx > 49.0:
            tx = 49.0
        elif tx < -49.5:
            tx = -49.5
        if ty > 29.0:
            ty = 29.0
        elif ty < -29.0:
            ty = -29.0
        dx = tx - px - 0.45 * vx
        dy = ty - py - 0.45 * vy
        d2 = dx * dx + dy * dy
        if d2 < 0.04:
            return NOOP
        d = sqrt(d2)
        if full or d > 2.0:
            mx, my = (dx / d, dy / d)
        else:
            mx, my = (dx / 2.0, dy / 2.0)
        if guard:
            pr = sqrt(px * px + py * py)
            if pr < 11.0:
                ux, uy = (px / pr, py / pr) if pr > 0.1 else (-1.0, 0.0)
                rad = mx * ux + my * uy
                if rad < 0.0:
                    mx, my = (mx - rad * ux, my - rad * uy)
                if pr < 10.0:
                    mx, my = (ux, uy)
        return {'movement': (mx, my)}

    def _keeper(self, bx, by, bvx, bvy, path, ours, P, sx, sy, G=G, H=H, range=range, len=len, D=D, sqrt=sqrt, R=R, max=max, min=min, unit=unit):
        if bvx < -8.0 and bvx * G[H] < -50.0 - bx:
            yc = by + bvy * (-50.0 - bx) / bvx
            if -8.5 < yc < 8.5 and bx < 10.0:
                px, py, vx, vy, _ = P[0]
                for k in range(1, len(path)):
                    qx, qy = path[k]
                    if qx < -49.5:
                        break
                    dx = qx - px - vx * D[k]
                    dy = qy - py - vy * D[k]
                    if sqrt(dx * dx + dy * dy) <= R[k] + KP_R:
                        return (qx, qy, True, k)
                if KP_FB:
                    bk, bg = (None, 1000000000.0)
                    for k in range(1, len(path)):
                        qx, qy = path[k]
                        if qx < -49.5:
                            break
                        dx = qx - px - vx * D[k]
                        dy = qy - py - vy * D[k]
                        g = sqrt(dx * dx + dy * dy) - R[k]
                        if g < bg:
                            bk, bg = (k, g)
                    if bk is not None:
                        qx, qy = path[bk]
                        return (qx, qy, True, bk)
                return (-49.0, max(-6.5, min(6.5, yc)), True)
        bx, by = (sx, sy)
        gx, gy = (bx + 50.0, by)
        dg = sqrt(gx * gx + gy * gy) or 1.0
        a1x, a1y = unit(-50.0 - bx, -7.0 - by)
        a2x, a2y = unit(-50.0 - bx, 7.0 - by)
        ux, uy = unit(a1x + a2x, a1y + a2y)
        if ux > -0.05:
            ux, uy = (-0.05, uy)
        tl = (-50.0 - bx) / ux
        lx, ly = (bx + ux * tl, by + uy * tl)
        depth = dg * KD_F
        if depth < 0.6:
            depth = 0.6
        elif depth > KD_MAX:
            depth = KD_MAX
        if KO_KD and self._kod and (depth > KO_KD):
            depth = KO_KD
        tx = lx - ux * depth
        ty = ly - uy * depth
        if ty > 6.5:
            ty = 6.5
        elif ty < -6.5:
            ty = -6.5
        return (max(tx, -49.4), ty, dg < 30.0)

    def _attack_spots(self, bx, by, path, t_us, O, n, pin=False, PB_FX=PB_FX, PB_DY=PB_DY, len=len, min=min, max=max, enumerate=enumerate, OPEN_W=OPEN_W, vtab=vtab, VUS=VUS, sqrt=sqrt, abs=abs, unit=unit, RGRID=RGRID, int=int):
        qx, qy = path[t_us] if t_us < len(path) else path[-1]
        spots = []
        rcap = LL_RCAP if self._late and LL_RCAP > 0.0 else RUN_CAP
        rmax = LL_REST if self._late and LL_REST != 0.0 else REST_MAX
        if getattr(self, '_behind', False):
            if BL_RCAP > 0.0:
                rcap = BL_RCAP
            if BL_REST != 0.0:
                rmax = BL_REST
        if getattr(self, '_ruth', False):
            if RU_RCAP > 0.0:
                rcap = RU_RCAP
            if RU_REST != 0.0:
                rmax = RU_REST
        fx = min(qx + RUN_DX, rcap)
        adv = min((o[0] for o in O[1:])) if len(O) > 1 else 0.0
        side = 1.0 if qy <= 0 else -1.0
        if pin and qx > 20.0:
            s_ = 1.0 if qy >= 0.0 else -1.0
            yb = max(-7.0, min(7.0, qy))
            cand = [(PB_FX, yb + s_ * PB_DY), (PB_FX, yb - s_ * 3.0 * PB_DY), (max(-38.0, min(qx - 22.0, 5.0)), qy * 0.3), (qx - 8.0, qy * 0.5 - s_ * 7.0)]
            return [(x, max(-27.0, min(27.0, y)), False, 'p%d' % i) for i, (x, y) in enumerate(cand[:n])]
        ffx = min(qx + FAR_DX, RUN_CAP) if FAR_DX > 0.0 else fx
        fy_ = qy * 0.3 + side * RUN_YF
        if qx < WIDE_X:
            fy_ = side * WIDE_Y
        cand = [(ffx, fy_), ((BYL_X, -side * BYL_Y) if BYL_X > 0.0 and qx > BYL_Q else (fx - 2.0, qy * 0.3 - side * RUN_YN)) if ES_X <= 0.0 else (min(qx + 12.0, ES_X), -side * ES_Y), (max(-38.0, min(qx - REST_DX, rmax, adv - 4.0)), qy * 0.3), (qx - SUP_DX, qy * 0.5 + side * SUP_Y)]
        if qx > LB_X and (qy > LB_Y or qy < -LB_Y):
            cand[1] = (LB_PX, qy * LB_PY)
        vt_ = VUS_OLD if getattr(self, '_alt', False) else VUS
        oxy = [(o[0], o[1]) for o in O]
        ow8 = OPEN_W * 8.0
        for ci, (x, y) in enumerate(cand[:n]):
            if ci < 2 and OPEN_W > 0.0:
                bsx, bsy, bsc = (x, y, -1000000000.0)
                for dx_, dy_, pen in RGRID:
                    cx_ = x + dx_
                    cy_ = y + dy_
                    if cx_ > 46.0 or cy_ > 27.0 or cy_ < -27.0:
                        continue
                    ex = cx_ - qx
                    ey = cy_ - qy
                    db = ex * ex + ey * ey
                    pdb = 0.1 if db < 36.0 or db > 900.0 else 0.0
                    fx = (cx_ + 47.5) * 0.2
                    if fx < 0.0:
                        fx = 0.0
                    elif fx > 18.999:
                        fx = 18.999
                    fy = ((cy_ if cy_ > 0.0 else -cy_) - 2.5) * 0.2
                    if fy < 0.0:
                        fy = 0.0
                    elif fy > 4.999:
                        fy = 4.999
                    i_ = int(fx)
                    j_ = int(fy)
                    ax = fx - i_
                    ay = fy - j_
                    r0 = vt_[i_]
                    r1 = vt_[i_ + 1]
                    vv = (r0[j_] * (1 - ay) + r0[j_ + 1] * ay) * (1 - ax) + (r1[j_] * (1 - ay) + r1[j_ + 1] * ay) * ax
                    if vv + ow8 - pdb - pen <= bsc:
                        continue
                    dmin = 64.0
                    for ox, oy in oxy:
                        ex = ox - cx_
                        ey = oy - cy_
                        d2 = ex * ex + ey * ey
                        if d2 < dmin:
                            dmin = d2
                    sc_ = vv + OPEN_W * sqrt(dmin) - pdb - pen
                    if sc_ > bsc:
                        bsx, bsy, bsc = (cx_, cy_, sc_)
                x, y = (bsx, bsy)
            for ox, oy, _, _, _ in O:
                ex, ey = (x - ox, y - oy)
                d2 = ex * ex + ey * ey
                if d2 < 16.0:
                    ux, uy = unit(ex, ey)
                    x += ux * 3.0
                    y += uy * 3.0
            ex, ey = (x - qx, y - qy)
            d2 = ex * ex + ey * ey
            if d2 < 25.0:
                ux, uy = unit(ex, ey)
                x, y = (qx + ux * 5.0, qy + uy * 5.0)
            spots.append((max(-45.0, min(46.0, x)), max(-27.0, min(27.0, y)), False, 'a%d' % len(spots)))
        return spots

    def _defend_spots(self, bx, by, path, t_them, j_them, O, P, n, len=len, sqrt=sqrt, enumerate=enumerate, MARKX=MARKX, PRESS=PRESS, LANE_D=LANE_D, LANE_Y=LANE_Y, LANE_FIRST=LANE_FIRST, unit=unit, COVD=COVD, LANE_COV=LANE_COV):
        """A compact block: a tight presser, a cover behind him, marks in our half."""
        qx, qy = path[t_them] if t_them < len(path) else path[-1]
        gx, gy = (-50.0 - qx, -qy)
        dg = sqrt(gx * gx + gy * gy) or 1.0
        ux, uy = (gx / dg, gy / dg)
        threats = []
        mlim = HP_X if qx > HP_Q else 10.0
        for j, (ox, oy, ovx, ovy, _) in enumerate(O):
            if j == j_them or ox > qx + MARKX or ox > mlim:
                continue
            threats.append(((ox + 50.0) ** 2 + oy * oy, ox, oy, j, ovx, ovy))
        threats.sort()
        bd = PRESS if PRESS < dg * 0.3 else dg * 0.3
        if dg < ED_R and bd > ED_D:
            bd = ED_D
        spots = [(qx + ux * bd, qy + uy * bd, True, 'blk')]
        lane = None
        if dg < LANE_D:
            sgn = -1.0 if qy <= 0.0 else 1.0
            pa = sgn * LANE_Y * (1.0 if LANE_FIRST == 'near' else -1.0)
            lx, ly = unit(-50.0 - qx, pa - qy)
            spots[0] = (qx + lx * bd, qy + ly * bd, True, 'blk')
            lane = unit(-50.0 - qx, -pa - qy)
        if qx < WB_X and (qy > WB_Y or qy < -WB_Y) and (O[j_them][2] < -3.0):
            wy = qy if -28.0 < qy < 28.0 else 28.0 if qy > 0 else -28.0
            spots[0] = (max(-49.0, qx - WB_D), wy - (1.0 if qy > 0 else -1.0), True, 'blk')
        marks = []
        for _, ox, oy, j, ovx, ovy in threats:
            if MK_LEAD:
                ox = max(-49.0, ox + ovx * MK_LEAD)
                oy = oy + ovy * MK_LEAD
            mx, my = unit(-50.0 - ox, -oy)
            vx, vy = unit(qx - ox, qy - oy)
            marks.append((ox + mx * MK_G + vx * MK_B, oy + my * MK_G + vy * MK_B, False, 'm%d' % j))
        cd = COVD if COVD < dg * 0.5 else dg * 0.5
        cx, cy = (qx + ux * cd, qy + uy * cd)
        if threats:
            tx, ty = (threats[0][1], threats[0][2])
            sx, sy = unit(tx - cx, ty - cy)
            cx += sx * 2.0
            cy += sy * 2.0
        if lane is not None:
            cl = LANE_COV if LANE_COV < dg * 0.5 else dg * 0.5
            cx, cy = (qx + lane[0] * cl, qy + lane[1] * cl)
        if qx < CB_X and (qy > CB_Y or qy < -CB_Y):
            cx, cy = (CB_ZX, qy * CB_ZYF)
            lane = None
        if KO_SHP and self._kod:
            px_, py_ = (-uy, ux)
            out = [spots[0]]
            for i_, d_ in enumerate(KO_SD):
                d_ = d_ if d_ < dg - 3.0 else dg - 3.0
                w_ = KO_SW * (1.0 if i_ % 2 == 0 else -1.0) if i_ < 2 else 0.0
                out.append((max(-46.0, qx + ux * d_ + px_ * w_), qy + uy * d_ + py_ * w_, False, 'ks%d' % i_))
            return out[:n]
        if KO_SCR and self._kod:
            if qx > KO_SCR + 4.0:
                cx, cy = (KO_SCR, qy * (KO_SCR + 50.0) / (qx + 50.0))
            else:
                cx, cy = (qx + ux * 6.0, qy + uy * 6.0)
            lane = None
        cov = (cx, cy, lane is not None, 'cov')
        if qx < MK2_X and len(marks) >= 2:
            spots = [marks[0], cov, marks[1]] + spots + marks[2:]
        else:
            if marks:
                spots.append(marks[0])
            spots.append(cov)
            spots.extend(marks[1:])
        k = 0
        while len(spots) < n:
            k += 1
            spots.append((qx + ux * (cd + 5.0 * k), qy + uy * (cd + 5.0 * k) + (4.0 if k % 2 else -4.0), False, 'z%d' % k))
        return spots[:n]

    def _defend_spots2(self, bx, by, path, t_them, j_them, O, P, n, len=len, sqrt=sqrt, unit=unit, vtab=vtab, VUS=VUS, D=D):
        """Danger-ranked defence: every candidate job is worth what it denies them.

        blk   stands in the carrier's shot lane, worth his threat from where he receives
        m<j>  goal side of attacker j, worth j's threat from where he is going
        cov   zonal guard of the space in front of goal (the cut-back zone)
        The n most valuable jobs are kept and assigned by travel cost."""
        qx, qy = path[t_them] if t_them < len(path) else path[-1]
        gx, gy = (-50.0 - qx, -qy)
        dg = sqrt(gx * gx + gy * gy) or 1.0
        ux, uy = (gx / dg, gy / dg)
        jobs = []
        thr_q = vtab(VUS, -qx, qy)
        bd = PRESS if PRESS < dg * 0.3 else dg * 0.3
        if dg < LANE_D:
            sgn = -1.0 if qy <= 0.0 else 1.0
            lx, ly = unit(-50.0 - qx, sgn * LANE_Y - qy)
            blk = (qx + lx * bd, qy + ly * bd)
        else:
            blk = (qx + ux * bd, qy + uy * bd)
        jobs.append((thr_q * D2_BLK, blk[0], blk[1], True, 'blk'))
        dk = D[D2_LOOK]
        for j, (ox, oy, ovx, ovy, _) in enumerate(O):
            if j == j_them:
                continue
            fx = ox + ovx * dk
            fy = oy + ovy * dk
            if fx > 25.0:
                continue
            thr = vtab(VUS, -fx, fy)
            if thr < D2_MKMIN:
                continue
            mx, my = unit(-50.0 - fx, -fy)
            vx, vy = unit(qx - fx, qy - fy)
            jobs.append((thr, fx + mx * D2_MG + vx * D2_MB, fy + my * D2_MG + vy * D2_MB, False, 'm%d' % j))
        cv = D2_COV
        if qx < -25.0:
            cx, cy = (D2_ZX, qy * 0.25)
            cv = D2_COVH
        else:
            cd = COVD if COVD < dg * 0.5 else dg * 0.5
            cx, cy = (qx + ux * cd, qy + uy * cd)
        jobs.append((cv, cx, cy, False, 'cov'))
        jobs.sort(key=lambda t: -t[0])
        spots = [(x, y, f, nm) for _, x, y, f, nm in jobs[:n]]
        k = 0
        while len(spots) < n:
            k += 1
            spots.append((cx + 5.0 * k, cy + (4.0 if k % 2 else -4.0), False, 'z%d' % k))
        return spots

    def _assign(self, free, spots, P, targets, len=len, sqrt=sqrt, PERM4=PERM4, PERM3=PERM3, enumerate=enumerate):
        """Exact minimum of summed squared travel, with a bonus for keeping a job."""
        n = len(free)
        if n == 0:
            return
        prev = self._roles
        cost = []
        for i in free:
            p = P[i]
            px = p[0]
            py = p[1]
            pl = prev.get(i)
            row = []
            for sp_ in spots:
                dx = px - sp_[0]
                dy = py - sp_[1]
                d2 = dx * dx + dy * dy
                if sp_[3] == pl:
                    d = sqrt(d2) - 3.0
                    d2 = d * d if d > 0.0 else 0.0
                row.append(d2)
            cost.append(row)
        if n == 4:
            c0, c1, c2, c3 = cost
            best = 1e+18
            for a in (0, 1, 2, 3):
                sa = c0[a]
                for b in (0, 1, 2, 3):
                    if b == a:
                        continue
                    sb = sa + c1[b]
                    for c in (0, 1, 2, 3):
                        if c == a or c == b:
                            continue
                        d = 6 - a - b - c
                        s = sb + c2[c] + c3[d]
                        if s < best:
                            best = s
                            bp = (a, b, c, d)
        elif n == 3:
            c0, c1, c2 = cost
            best = 1e+18
            for a in (0, 1, 2):
                sa = c0[a]
                for b in (0, 1, 2):
                    if b == a:
                        continue
                    c = 3 - a - b
                    s = sa + c1[b] + c2[c]
                    if s < best:
                        best = s
                        bp = (a, b, c)
        elif n == 2:
            c0, c1 = cost
            bp = (0, 1) if c0[0] + c1[1] <= c0[1] + c1[0] else (1, 0)
        else:
            bp = (0,)
        roles = {}
        for a, b in enumerate(bp):
            sp_ = spots[b]
            targets[free[a]] = (sp_[0], sp_[1], sp_[2])
            roles[free[a]] = sp_[3]
        self._roles = roles

    def _shoot(self, s):
        self._plan = None
        return {'movement': (0.0, 0.0), 'kick_direction': (s[0], s[1]), 'kick_power': s[2]}

    def _original_kick(self, k, bx, by, bvx, bvy, P, O, tick, PB_N=PB_N, PB_LN=PB_LN, PB_L=PB_L, PB_SPAN=PB_SPAN, PB_X=PB_X, WALL_N=WALL_N, WALL_D=WALL_D, WALL_R=WALL_R, WALL_YS=WALL_YS, CNT_B=CNT_B, SHOT_GD=SHOT_GD, sqrt=sqrt, GOAL_YS=GOAL_YS, unit=unit, solve_kick=solve_kick, self_clear=self_clear, G=G, H=H, R=R, KR=KR, zip=zip, line_gap=line_gap, shot_p=shot_p, max=max, tuple=tuple, CANDS=CANDS, KICK_BUDGET=KICK_BUDGET, OPP_R=OPP_R, OPP_DELAY=OPP_DELAY, vus_bound=vus_bound, D14=D14, G14=G14, INF=INF, line_arrive=line_arrive, pos_value=pos_value, PK0=PK0, PK1=PK1, vtab=vtab, VOP=VOP, xg=xg, SHOT_MIN=SHOT_MIN, SHOT_REL=SHOT_REL, sorted=sorted, bisect_left=bisect_left, TEMPO=TEMPO, TEMPO_T=TEMPO_T, KB0=KB0, KB_M=KB_M, D=D, SHV=SHV, SB_X=SB_X, SB_W=SB_W, FK=FK, int=int, P9=P9, R18=R18, ro_table=ro_table):
        kx, ky, kvx, kvy, _ = P[k]
        if getattr(self, '_trans', False) and TR_TEMPO:
            TEMPO = TR_TEMPO
        blk = getattr(self, '_block', False)
        if blk and BK_TEMPO:
            TEMPO = BK_TEMPO
        if not getattr(self, '_sharp', False) and (not (blk and BK_SHARP)):
            if OPP_R_T:
                OPP_R = OPP_R_T
            if PK1_T:
                PK1 = PK1_T
        tkx = kx + 0.045 * kvx
        tky = ky + 0.045 * kvy
        VUx, VRx = (VUS_OLD, VUS_RECT_OLD) if getattr(self, '_alt', False) else (VUS, VUS_RECT)
        odrift = [0.45 * sqrt(o[2] * o[2] + o[3] * o[3]) for o in O]
        mdrift = [0.45 * sqrt(p[2] * p[2] + p[3] * p[3]) for p in P]
        sp2 = SP_MODE and (not (SP_TIGHT and getattr(self, '_alt', False)))
        sp2r = sp2 and SP_MODE >= 2
        gd = sqrt((50.0 - bx) ** 2 + by * by)
        sdelay, srad, gys = (1, KR - 0.4 + SR_ADD, GOAL_YS)
        nw = nl = 0
        ylo, yhi = (9.0, -9.0)
        for o in O:
            if o[0] > 46.0 and -8.0 < o[1] < 8.0:
                nw += 1
                if o[0] > PB_L:
                    nl += 1
                    if o[1] < ylo:
                        ylo = o[1]
                    if o[1] > yhi:
                        yhi = o[1]
        pin = nw >= PB_N or (nl >= PB_LN and yhi - ylo >= PB_SPAN)
        if nw >= WALL_N:
            sdelay, srad, gys = (WALL_D, WALL_R, WALL_YS + GOAL_YS)
        if gd < SHOT_GD:
            best_g, best_s, best_key = (-99.0, None, -99.0)
            best_cnt = False
            shots = []
            for gy in gys if gd < 38.0 else FAR_YS:
                ux, uy = unit(50.0 - bx, gy - by)
                s = solve_kick(ux, uy, 30.0, bvx, bvy)
                if s is not None:
                    shots.append((s, ux, uy))
                if CNT_X and tkx > 0.3 and (s is None or s[2] < 0.5 or s[0] <= 0.05 or (not -6.9 < tky + s[1] * (50.0 - tkx) / s[0] < 6.9)):
                    cx_, cy_ = unit(50.0 - tkx, gy - tky)
                    for pw in CNT_PW:
                        wx_ = bvx + 22.0 * pw * cx_
                        wy_ = bvy + 22.0 * pw * cy_
                        ws_ = sqrt(wx_ * wx_ + wy_ * wy_)
                        if ws_ > 30.0:
                            wx_ *= 30.0 / ws_
                            wy_ *= 30.0 / ws_
                            ws_ = 30.0
                        if ws_ > 15.0 and wx_ > 1.0 and (-6.3 < by + wy_ * (50.0 - bx) / wx_ < 6.3):
                            shots.append(((cx_, cy_, pw, wx_, wy_, ws_), wx_ / ws_, wy_ / ws_))
                            break
            for s, ux, uy in shots:
                bonus = CNT_B if kx > 0.0 and s[2] >= 0.5 and (s[0] > 0.05) and (-6.9 < ky + s[1] * (50.0 - kx) / s[0] < 6.9) else 0.0
                wx, wy = (s[3], s[4])
                if not self_clear(bx, by, wx, wy, kx, ky, kvx, kvy):
                    continue
                need = (50.0 - bx) / wx if wx > 0.1 else 99.0
                if need >= G[H]:
                    continue
                K = bisect_left(G, need, 1, H)
                worst = 99.0
                rk = (R[K - sdelay] if K > sdelay else 0.0) + srad
                for (ox, oy, ovx, ovy, _), drift in zip(O, odrift):
                    ex = ox - bx
                    ey = oy - by
                    pj = ex * ux + ey * uy
                    if pj > 0.0:
                        ex -= pj * ux
                        ey -= pj * uy
                    if sqrt(ex * ex + ey * ey) - drift - rk >= worst:
                        continue
                    g = line_gap(bx, by, wx, wy, ox, oy, ovx, ovy, srad, sdelay, K, best_key - bonus)
                    if g < worst:
                        worst = g
                        if worst + bonus < best_key:
                            break
                if worst + bonus > best_key:
                    best_g, best_s, best_key = (worst, s, worst + bonus)
                    best_cnt = bonus > 0.0
            if best_s is not None:
                p_shot = shot_p2(best_g) if sp2 else shot_p(best_g)
        else:
            best_s, best_g = (None, -99.0)
            best_cnt = False
        if best_s is None:
            p_shot = 0.0
        if p_shot > 0.85 or (best_s is not None and pin and (bx > PB_X)):
            return self._shoot(best_s)
        if self._crowd and best_s is not None and (bx > PB_X) and (p_shot >= CR_P):
            return self._shoot(best_s)
        if PS_T and best_s is not None and (bx > 0.0) and (p_shot >= PS_P) and (tick - getattr(self, '_opp_kick', 0) > PS_T):
            return self._shoot(best_s)
        gx, gy = unit(50.0 - bx, -by * 0.6)
        best_v, best, binfo = (-1000000000.0, None, None)
        best_x = 0.0
        cd_min = [p[4] if p[4] > 1 else 1 for p in P]
        pcv = [0.045 * sqrt(p[2] * p[2] + p[3] * p[3]) for p in P]
        ocv = [0.045 * sqrt(o[2] * o[2] + o[3] * o[3]) for o in O]
        ocd = [o[4] if o[4] > 1 else 1 for o in O]
        Oi = list(zip(O, ocv, ocd))
        RO = ro_table(OPP_R, OPP_DELAY)
        pe = [(p[0] - bx, p[1] - by, sqrt((p[0] - bx) ** 2 + (p[1] - by) ** 2), d_) for p, d_ in zip(P, mdrift)]
        oe = [(o[0] - bx, o[1] - by, sqrt((o[0] - bx) ** 2 + (o[1] - by) ** 2), d_) for o, d_ in zip(O, odrift)]
        if k == 0:
            order_d = order_p = (1, 2, 3, 4)
        else:
            order_d = (k,) + tuple((i for i in (1, 2, 3, 4) if i != k))
            order_p = tuple((i for i in (1, 2, 3, 4) if i != k)) + (k,)
        bv2 = bvx * bvx + bvy * bvy
        t_start = self._t_act
        tbb = self._tbb if tkx > 0.3 and bx > TB_X else 0.0
        swk = False
        if SW_B:
            nbs = 0
            for o in O:
                if o[1] > 2.0 and by > 0.0 or (o[1] < -2.0 and by < 0.0):
                    nbs += 1
            swk = nbs >= SW_N
        xbb = tbb + HSP_B + (DRB_B if DRB_B > PAS_B + PLEN_B * 60.0 else PAS_B + PLEN_B * 60.0) + (CS_B if bx > CS_X else 0.0) + (SW_B if swk else 0.0)
        G48 = G[48]
        rays = []
        for c, s_, speeds in CANDS:
            ux = gx * c - gy * s_
            uy = gx * s_ + gy * c
            ud = ux * bvx + uy * bvy
            disc = ud * ud - bv2 + 484.0
            smax = ud + sqrt(disc) if disc > 0.0 else 0.0
            if smax > 30.0:
                smax = 30.0
            reach = (smax if smax < speeds[-1] else speeds[-1]) * G[48]
            vb_ = _vus_bound_impl(bx, by, bx + ux * reach, by + uy * reach, VRx)
            if SHV > vb_ and bx + ux * reach > SB_X:
                vb_ = SHV
            rays.append((vb_ + SB_W + KB0 + xbb + (TEMPO * ux * reach if ux > 0.0 else 0.0), ux, uy, smax, speeds))
        if KS_ORD:
            rays.sort(key=lambda r_: -r_[0])
        for vbound, ux, uy, smax, speeds in rays:
            if perf_counter() - t_start > KICK_BUDGET:
                break
            if vbound <= best_v:
                if KS_ORD:
                    break
                continue
            ka = (kx - bx) * ux + (ky - by) * uy
            kp = (ky - by) * ux - (kx - bx) * uy
            kva = kvx * ux + kvy * uy
            kvp = kvy * ux - kvx * uy
            lbs = []
            for ex, ey, e1, drift in pe:
                if ex * ux + ey * uy > 0.0:
                    d_ = ey * ux - ex * uy
                    lbs.append(((d_ if d_ > 0.0 else -d_) - drift - 1.8) * 2.5)
                else:
                    lbs.append((e1 - drift - 1.8) * 2.5)
            lbo = []
            for ex, ey, e1, drift in oe:
                if ex * ux + ey * uy > 0.0:
                    d_ = ey * ux - ex * uy
                    lbo.append(((d_ if d_ > 0.0 else -d_) - drift - OPP_R) * 2.5 + OPP_DELAY)
                else:
                    lbo.append((e1 - drift - OPP_R) * 2.5 + OPP_DELAY)
            lbo = sorted(zip(lbo, Oi))
            body = [(ka + kva * dk, kp + kvp * dk) for dk in D14]
            bhit = False
            for ba, bp in body:
                if bp * bp < 2.4:
                    bhit = True
                    break
            k_from = 5
            last_s = -1.0
            smax_r = smax if smax < speeds[-1] else speeds[-1]
            for spd in speeds:
                ws = spd if spd < smax else smax
                if ws < 0.5 or ws == last_s:
                    continue
                last_s = ws
                if SP_BND and ws < smax_r:
                    reach_s = ws * G48
                    vb_s = _vus_bound_impl(bx, by, bx + ux * reach_s, by + uy * reach_s, VRx)
                    if SHV > vb_s and bx + ux * reach_s > SB_X:
                        vb_s = SHV
                    if vb_s + SB_W + KB0 + xbb + (TEMPO * ux * reach_s if ux > 0.0 else 0.0) <= best_v:
                        continue
                ix = ws * ux - bvx
                iy = ws * uy - bvy
                m = sqrt(ix * ix + iy * iy)
                if m < 1e-06:
                    continue
                wx = ws * ux
                wy = ws * uy
                if bhit:
                    for ga, (ba, bp) in zip(G14, body):
                        da = ws * ga - ba
                        if da * da + bp * bp < 2.4:
                            break
                    else:
                        ga = None
                    if ga is not None:
                        continue
                t_me, who = (INF, 9)
                drib = spd < 13.0
                for i in order_d if drib else order_p:
                    if i == k:
                        if not drib:
                            continue
                        lim = 30
                        kmin_ = k_from
                    else:
                        lim = (t_me if i < who else t_me - 1) if t_me < INF else 48
                        kmin_ = cd_min[i]
                    lb_ = lbs[i]
                    if lb_ > lim:
                        continue
                    px, py, pvx, pvy, cd = P[i]
                    cv_ = pcv[i]
                    t = INF
                    kq = kmin_
                    if lb_ > kq:
                        kq = int(lb_)
                    while kq <= lim:
                        g_ = G[kq]
                        dk = D[kq]
                        dx = bx + wx * g_ - px - pvx * dk
                        dy = by + wy * g_ - py - pvy * dk
                        g = sqrt(dx * dx + dy * dy) - R18[kq]
                        if g <= 0.0:
                            t = kq
                            break
                        kq += 1 + int(g / (ws * FK[kq] + 0.4 + cv_ * P9[kq]))
                    if i == k:
                        k_from = t if t < INF else 31
                    if t < INF and (t < t_me or i < who):
                        t_me, who = (t, i)
                if t_me >= INF:
                    continue
                qx = bx + wx * G[t_me]
                qy = by + wy * G[t_me]
                if qx > 49.0 or qx < -49.0 or qy > 29.0 or (qy < -29.0):
                    continue
                pv = vtab(VUx, qx, qy)
                if TEMPO or TEMPO_T:
                    pv += TEMPO * (qx - bx) - TEMPO_T * t_me
                if KB0 and qx > 0.0:
                    dk_ = D[t_me] if t_me < H else D[H]
                    nb_ = 0
                    for ox, oy, ovx, ovy, _ in O:
                        if ox + ovx * dk_ > qx - KB_M:
                            nb_ += 1
                    if nb_ <= 1:
                        pv += KB0
                osv = -1.0
                if qx > SB_X:
                    if (pv if pv > SHV else SHV) + SB_W + xbb <= best_v:
                        continue
                    osv = open_shot(qx, qy, t_me, O, shot_p2 if sp2r else None)
                    pv += SB_W * osv
                    if SHV * osv > pv:
                        pv = SHV * osv
                if pv + xbb <= best_v:
                    continue
                lim = t_me + 12
                if lim > H:
                    lim = H
                t_op = INF
                for lb, ((ox, oy, ovx, ovy, cd), cv_, kq) in lbo:
                    if lb > lim:
                        break
                    t = INF
                    if lb > kq:
                        kq = int(lb)
                    while kq <= lim:
                        g_ = G[kq]
                        dk = D[kq]
                        dx = bx + wx * g_ - ox - ovx * dk
                        dy = by + wy * g_ - oy - ovy * dk
                        g = sqrt(dx * dx + dy * dy) - RO[kq]
                        if g <= 0.0:
                            t = kq
                            break
                        kq += 1 + int(g / (ws * FK[kq] + 0.4 + cv_ * P9[kq]))
                    if t < t_op:
                        t_op = t
                        if t <= t_me:
                            break
                        lim = t - 1
                margin = t_op - t_me if t_op < INF else 30
                if margin < 1:
                    continue
                pk = PK0 + PK1 * margin
                if pk >= 1.0:
                    v = pv
                else:
                    v = pk * pv - (1.0 - pk) * vtab(VOP, -qx, qy)
                kk = (ix / m, iy / m, m / 22.0 if m < 22.0 else 1.0)
                if tbb and kk[2] >= 0.5 and (kk[0] > 0.05) and (-6.6 < tky + kk[1] * (50.0 - tkx) / kk[0] < 6.6):
                    v += tbb
                if who == k:
                    v += DRB_B
                    if CS_B and bx > CS_X and (ux > CS_U):
                        v += CS_B
                else:
                    if PAS_B or PLEN_B:
                        v += PAS_B + PLEN_B * sqrt((qx - bx) ** 2 + (qy - by) ** 2)
                    if HSP_B and qx > 30.0 and (4.0 < (qy if qy > 0.0 else -qy) < 16.0):
                        v += HSP_B
                    if swk and (qy < -SW_DY if by > 0.0 else qy > SW_DY):
                        v += SW_B
                if v > best_v:
                    best_v, best = (v, kk)
                    best_x = (osv if osv >= 0.0 else xg(qx, qy, XG=XG2) if sp2r else xg(qx, qy)) * (pk if pk < 1.0 else 1.0)
                    binfo = (t_me, who)
        if self._late:
            SHOT_MIN, SHOT_REL = (LL_SMIN, LL_REL)
        elif self._behind:
            SHOT_MIN, SHOT_REL = (BL_SMIN, BL_REL)
        elif self._tbl and bx > TB_X and best_cnt:
            SHOT_MIN, SHOT_REL = (TB_SMIN, TB_REL)
        if getattr(self, '_block', False):
            SHOT_MIN = SHOT_MIN if SHOT_MIN < BK_SMIN else BK_SMIN
            SHOT_REL = SHOT_REL if SHOT_REL < BK_REL else BK_REL
        if getattr(self, '_ruth', False):
            SHOT_MIN = SHOT_MIN if SHOT_MIN < RU_SMIN else RU_SMIN
            SHOT_REL = SHOT_REL if SHOT_REL < RU_REL else RU_REL
        if getattr(self, '_trans', False):
            SHOT_MIN = SHOT_MIN if SHOT_MIN < TR_SMIN else TR_SMIN
            SHOT_REL = SHOT_REL if SHOT_REL < TR_REL else TR_REL
        if bx > BA_X and -BA_Y < by < BA_Y:
            ngs = 0
            for o in O:
                if o[0] > bx:
                    ngs += 1
            if ngs <= BA_N:
                SHOT_MIN = SHOT_MIN if SHOT_MIN < BA_SMIN else BA_SMIN
                SHOT_REL = SHOT_REL if SHOT_REL < BA_REL else BA_REL
        if best_s is not None and p_shot >= SHOT_MIN and (p_shot >= SHOT_REL * best_x):
            return self._shoot(best_s)
        if best is not None and bx < KC_X:
            cb, cv = self._clear(k, bx, by, bvx, bvy, P, O, t_start)
            if cb is not None and cv > best_v + KC_M:
                self._plan = None
                return {'movement': (0.0, 0.0), 'kick_direction': (cb[0], cb[1]), 'kick_power': cb[2]}
        if best is not None:
            self._plan = (binfo[1], tick + binfo[0] + 3)
            return {'movement': (0.0, 0.0), 'kick_direction': (best[0], best[1]), 'kick_power': best[2]}
        self._plan = None
        if bx < CLR_X:
            best, cv = self._clear(k, bx, by, bvx, bvy, P, O, t_start)
            if best is not None and cv < -4.0:
                return {'movement': unit(bx - P[k][0], by - P[k][1])}
            if best is not None:
                return {'movement': (0.0, 0.0), 'kick_direction': (best[0], best[1]), 'kick_power': best[2]}
        best_v, best = (-1000000000.0, None)
        for cx, cy in ((1.0, 0.0), (0.8, 0.6), (0.8, -0.6), (0.5, 0.86), (0.5, -0.86), (0.0, 1.0), (0.0, -1.0)):
            kk = solve_kick(cx, cy, 30.0, bvx, bvy)
            if kk is None:
                continue
            wx, wy, ws = (kk[3], kk[4], kk[5])
            t_op = INF
            for ox, oy, ovx, ovy, cd in O:
                t = line_arrive(bx, by, wx, wy, ws, ox, oy, ovx, ovy, KR, 1, 30)
                if t < t_op:
                    t_op = t
            v = t_op + wx * 0.3 + (0.0 if self_clear(bx, by, wx, wy, kx, ky, kvx, kvy) else -20.0)
            if v > best_v:
                best_v, best = (v, kk)
        if best is None:
            ux, uy = unit(50.0 - bx, -by)
            return {'movement': (0.0, 0.0), 'kick_direction': (ux, uy), 'kick_power': 1.0}
        return {'movement': (0.0, 0.0), 'kick_direction': (best[0], best[1]), 'kick_power': best[2]}

    def _clear(self, k, bx, by, bvx, bvy, P, O, t_start):
        """Nothing keeps the ball: kick it where losing it costs least.

        Each clearance is raced on its true path (walls included); the value is
        what keep() would give it, with the ball surely lost when they arrive
        first, at the point where they collect it."""
        kx, ky, kvx, kvy, _ = P[k]
        best_v, best = (-1000000000.0, None)
        RKD = ro_table(KR, 1)
        for cx, cy in CLR_DIRS:
            if best is not None and perf_counter() - t_start > KICK_BUDGET:
                break
            for spd in CLR_SPEEDS:
                kk = solve_kick(cx, cy, spd, bvx, bvy)
                if kk is None:
                    continue
                wx, wy, ws = (kk[3], kk[4], kk[5])
                path, touched = deflect_path(bx, by, wx, wy, kx, ky, kvx, kvy)
                hit = -0.1 if touched else 0.0
                if path[-1][0] < -50.5:
                    hit -= 5.0
                t_op = INF
                if touched:
                    for ox, oy, ovx, ovy, cd in O:
                        t = arrive(ox, oy, ovx, ovy, path, ws, KR, 1, t_op - 1 if t_op < INF else H, max(1, cd))
                        if t < t_op:
                            t_op = t
                    t_me = INF
                    lim = t_op if t_op < INF else H
                    for i in range(5):
                        px, py, pvx, pvy, cd = P[i]
                        t = arrive(px, py, pvx, pvy, path, ws, 1.8, 0, lim, 5 if i == k else max(1, cd))
                        if t < t_me:
                            t_me = t
                            lim = t
                else:
                    for ox, oy, ovx, ovy, cd in O:
                        t = arrive0(ox, oy, ovx, ovy, path, ws, RKD, t_op - 1 if t_op < INF else H, cd if cd > 1 else 1)
                        if t < t_op:
                            t_op = t
                    t_me = INF
                    lim = t_op if t_op < INF else H
                    for i in range(5):
                        px, py, pvx, pvy, cd = P[i]
                        t = arrive0(px, py, pvx, pvy, path, ws, R18, lim, 5 if i == k else cd if cd > 1 else 1)
                        if t < t_me:
                            t_me = t
                            lim = t
                if t_me < t_op:
                    qx, qy = path[t_me]
                    margin = t_op - t_me if t_op < INF else 30
                    pk = PK0 + PK1 * margin
                    VUx = VUS_OLD if getattr(self, '_alt', False) else VUS
                    if pk >= 1.0:
                        v = vtab(VUx, qx, qy)
                    else:
                        v = pk * vtab(VUx, qx, qy) - (1.0 - pk) * vtab(VOP, -qx, qy)
                else:
                    qx, qy = path[t_op] if t_op < len(path) else path[-1]
                    v = -vtab(VOP, -qx, qy)
                v += CLR_T * (t_op if t_op < 40 else 40) + hit
                if v > best_v:
                    best_v, best = (v, kk)
        return (best, best_v)

    def _kick(self, k, bx, by, bvx, bvy, P, O, tick):
        m = self._hybrid_monster
        wall = bx > 20.0 and sum((q[0] > m.right - 3.5 and abs(q[1]) < m.goal + 1 for q in O)) >= 4
        if not wall:
            return self._original_kick(k, bx, by, bvx, bvy, P, O, tick)
        opponents = [(i + 5, *q) for i, q in enumerate(O)]
        candidates = m.goal_aims((bx, by, bvx, bvy), opponents, True)
        extra = []
        for f in candidates:
            y = f * m.goal
            if all((abs(y - old) > 0.08 for old in GOAL_YS + WALL_YS + tuple(extra))):
                extra.append(y)
            if len(extra) >= 3:
                break
        self._hybrid_counts['extra_aims'] += len(extra)
        return self._original_kick(k, bx, by, bvx, bvy, P, O, tick, GOAL_YS=tuple(extra) + GOAL_YS)
from soccer import TeamAction, PlayerAction

def _m_clip(v, lo, hi):
    return max(lo, min(hi, v))

def _m_unit(x, y):
    d = math.hypot(x, y)
    return (x / d, y / d) if d > 1e-09 else (0.0, 0.0)

class _MonsterPolicy:
    name = 'MONSTER LEAGUE'
    version = 'league-v1-13a91e8f755c'
    PRESSERS = 2
    CARRY_SPEED = 9.0
    SHOT_MARGIN = -0.08
    LOCK_LEAD = 0
    LOCK_DEPTH = 3.3
    FORMATION = 0
    WIDTH = 11.0
    PASS_WEIGHT = 1.0
    SWEEP = True
    DEFENSE = 0
    KEEPER_DEPTH = 1.6
    DUELS = True
    TWIN_KEEPERS = False
    SHELL = True
    SHELL_DEPTH = 1.2
    SHELL_RELEASE = False
    SHELL_BANK = False
    SHELL_LOCK_FIVE = False
    KEEPER_MODEL = False
    FIXED_OUTLET = True
    OUTLET_X = -20.0
    ADAPTIVE_POSTS = True
    POST_MAX = 7.3
    PREDICT_POST = False
    SUPPORT = False
    SHOT_FIRST = False
    AIM_DUEL = False
    SMART_CLEAR = False
    COVER_SHIFT = False
    BREAKAWAY_TOUCH = False

    def __init__(self):
        self.reset(0)

    def reset(self, seed):
        self.ready = False
        self.last_score = None
        self.restart_until = -1
        self.restart_owner = 0
        self.receiver = None
        self.previous_chaser = None
        self.deadline = math.inf
        self.outlet_side = None

    def initial_formation(self, f):
        front = -f.centre_circle_radius - 0.3
        if self.SHELL:
            return [(f.my_goal[0] + 1.2, 5.4), (f.my_goal[0] + 1.2, -1.8), (f.my_goal[0] + 1.2, 1.8), (f.my_goal[0] + 1.2, -5.4), (front, 0)]
        if self.TWIN_KEEPERS:
            return [(f.my_goal[0] + 1.5, -3.2), (f.my_goal[0] + 1.5, 3.2), (-21, 0), (front, 0), (front, 10)]
        if self.FORMATION == 1:
            return [(f.my_goal[0] + 1.5, 0), (-24, 0), (front, -9), (front, 0), (front, 9)]
        if self.FORMATION == 2:
            return [(f.my_goal[0] + 1.5, 0), (front, -7.5), (front, -2.5), (front, 2.5), (front, 7.5)]
        return [(f.my_goal[0] + 1.5, 0), (-18, -11), (-18, 11), (front, -3.2), (front, 3.2)]

    def setup(self, f):
        self.dt = 1.0 / f.simulation_hz
        self.hz = f.simulation_hz
        self.speed = f.max_speed
        self.acc = f.acceleration * self.dt
        self.drag = f.ball_friction
        self.impulse = f.kick_impulse
        self.kr = f.kick_range
        self.body = f.player_radius + f.ball_radius
        self.pr = f.player_radius
        self.br = f.ball_radius
        self.left, self.right = (f.my_goal[0], f.opponent_goal[0])
        self.half = f.height / 2
        self.goal = f.goal_width / 2
        self.circle = f.centre_circle_radius
        self.damp, self.wall, self.ballcap = (0.9, 0.75, 30.0)
        self.roll = [self.dt * (1 - self.drag ** n) / (1 - self.drag) for n in range(151)]
        self.reach = []
        for n in range(151):
            coast = self.dt * self.damp * (1 - self.damp ** n) / (1 - self.damp)
            push = self.acc * self.dt / (1 - self.damp) * (n - self.damp * (1 - self.damp ** n) / (1 - self.damp))
            self.reach.append((coast, push))
        self.ready = True

    def bound(self, x, y):
        return (_m_clip(x, self.left + self.pr + 0.05, self.right - self.pr - 0.05), _m_clip(y, -self.half + self.pr + 0.05, self.half - self.pr - 0.05))

    def move(self, p, target):
        dx, dy = (target[0] - p[1], target[1] - p[2])
        d = math.hypot(dx, dy)
        gain = min(self.speed, d * 6.0) / max(d, 1e-09)
        ax = (dx * gain - p[3] * self.damp) / self.acc
        ay = (dy * gain - p[4] * self.damp) / self.acc
        norm = max(1.0, math.hypot(ax, ay))
        return (ax / norm, ay / norm)

    def player_step(self, p, movement):
        vx, vy = (p[3] * self.damp + movement[0] * self.acc, p[4] * self.damp + movement[1] * self.acc)
        norm = max(1.0, math.hypot(vx, vy) / self.speed)
        vx, vy = (vx / norm, vy / norm)
        x, y = self.bound(p[1] + vx * self.dt, p[2] + vy * self.dt)
        return (p[0], x, y, vx, vy, max(0, p[5] - 1))

    def travel_gap(self, p, x, y, n, radius):
        coast, acceleration = self.reach[min(n, 150)]
        dx, dy = (x - p[1], y - p[2])
        return max(math.hypot(dx, dy) - self.speed * n * self.dt, math.hypot(dx - p[3] * coast, dy - p[4] * coast) - acceleration) - radius

    def stream_path(self, x, y, vx, vy, steps=65):
        yield (0, x, y)
        for n in range(1, steps + 1):
            x, y = (x + vx * self.dt, y + vy * self.dt)
            vx, vy = (vx * self.drag, vy * self.drag)
            if abs(y) > self.half - self.br:
                s = 1 if y > 0 else -1
                y = s * 2 * (self.half - self.br) - y
                vy = -s * abs(vy) * self.wall
            if abs(x) > self.right - self.br:
                if abs(y) <= self.goal and abs(x) > self.right:
                    yield (n, x, y)
                    break
                if abs(y) > self.goal:
                    s = 1 if x > 0 else -1
                    x = s * 2 * (self.right - self.br) - x
                    vx = -s * abs(vx) * self.wall
            yield (n, x, y)
        return

    def path(self, x, y, vx, vy, steps=65):
        return list(self.stream_path(x, y, vx, vy, steps))

    def race(self, p, path):
        best = None
        for n, x, y in path:
            if n > 0 and n % 2 and (n > 8):
                continue
            gap = self.travel_gap(p, x, y, n, self.kr * 0.86)
            if gap <= 0 and p[5] <= n:
                return (n * self.dt, (x, y))
            cost = n * self.dt + max(0, gap) / self.speed
            if best is None or cost < best[0]:
                best = (cost, (x, y))
        return best

    def velocity_kick(self, vx, vy, tx, ty):
        dx, dy = (tx - vx, ty - vy)
        length = math.hypot(dx, dy)
        if length < 0.015:
            return None
        return ((dx / length, dy / length), min(1.0, length / self.impulse))

    def forward_duel(self, p, ball, opponents, movement):
        bx, by, vx, vy = ball
        active = [q for q in opponents if q[5] == 0 and math.hypot(q[1] - bx, q[2] - by) < self.kr + 0.45]
        if not self.DUELS or not active:
            return None
        ex, ey = _m_unit(self.left - bx, -by)
        enemy_impulses = [(ex * self.impulse, ey * self.impulse), (-8.0 - vx, -vy), (0, 0)]
        best = None
        angles = (0, -0.35, 0.35, -0.7, 0.7)
        if self.AIM_DUEL and bx > self.right - 18:
            goal_angle = math.atan2(_m_clip(by, -self.goal + 0.3, self.goal - 0.3) - by, self.right + 0.2 - bx)
            angles = (goal_angle, goal_angle - 0.2, goal_angle + 0.2, 0, -0.7, 0.7)
        for angle in angles:
            ux, uy = (math.cos(angle), math.sin(angle))
            worst = 100.0
            for evx, evy in enemy_impulses:
                for enemy_first in (False, True):
                    sx, sy = (vx, vy)
                    impulses = [(ux * self.impulse, uy * self.impulse), (evx, evy)]
                    if enemy_first:
                        impulses.reverse()
                    for dx, dy in impulses:
                        sx, sy = (sx + dx, sy + dy)
                        scale = max(1, math.hypot(sx, sy) / self.ballcap)
                        sx, sy = (sx / scale, sy / scale)
                    value = sx * 0.2 - abs(by + sy * 0.3) * 0.015
                    worst = min(worst, value)
            if best is None or worst > best[0]:
                best = (worst, ((ux, uy), 1.0), movement, None)
        return best

    def duel(self, p, ball, opponents, movement):
        bx, by, vx, vy = ball
        default = self.forward_duel(p, ball, opponents, movement)
        if default is None or bx < self.right - 6.0 or abs(by) < self.goal - 0.7:
            return default
        side = 1 if by >= 0 else -1
        targets = (side * (self.goal - 0.22), side * self.goal * 0.55, 0.0, -side * self.goal * 0.65)
        angles = [math.atan2(ty - by, self.right + 0.3 - bx) for ty in targets]
        angles.extend((0.0, -0.35, 0.35))
        ex, ey = _m_unit(self.left - bx, -by)
        enemy_impulses = ((ex * self.impulse, ey * self.impulse), (-8.0 - vx, -vy), (0.0, 0.0))
        start_gap = math.hypot(self.right + 0.1 - bx, max(0.0, abs(by) - self.goal + 0.12))
        best = None
        for angle in angles:
            if perf_counter() > self.deadline:
                break
            ux, uy = (math.cos(angle), math.sin(angle))
            values = []
            for evx, evy in enemy_impulses:
                for enemy_first in (False, True):
                    sx, sy = (vx, vy)
                    impulses = [(ux * self.impulse, uy * self.impulse), (evx, evy)]
                    if enemy_first:
                        impulses.reverse()
                    for dx, dy in impulses:
                        sx, sy = (sx + dx, sy + dy)
                        scale = max(1.0, math.hypot(sx, sy) / self.ballcap)
                        sx, sy = (sx / scale, sy / scale)
                    scored, blocked = (False, False)
                    x, y = (bx, by)
                    for n, x, y in self.stream_path(bx, by, sx, sy, steps=18):
                        if n == 0:
                            continue
                        coast = self.reach[n][0]
                        if any((math.hypot(x - q[1] - q[3] * coast, y - q[2] - q[4] * coast) < self.body - 0.02 for q in opponents)):
                            blocked = True
                            break
                        if x > self.right and abs(y) < self.goal:
                            scored = True
                            break
                    gap = math.hypot(self.right + 0.1 - x, max(0.0, abs(y) - self.goal + 0.12))
                    value = 25.0 if scored else (start_gap - gap) * 0.75 + (x - bx) * 0.06 - (2.0 if blocked else 0.0)
                    values.append(value)
            value = sum(values) / len(values) + 0.25 * min(values)
            if best is None or value > best[0]:
                best = (value, ((ux, uy), 1.0), movement, None)
        return best if best is not None else default

    def launch(self, p, ball, kick, movement):
        bx, by, vx, vy = ball
        next_p = self.player_step(p, movement)
        if math.hypot(next_p[1] - bx, next_p[2] - by) > self.kr - 0.04:
            return None
        if kick:
            vx += kick[0][0] * kick[1] * self.impulse
            vy += kick[0][1] * kick[1] * self.impulse
        norm = max(1.0, math.hypot(vx, vy) / self.ballcap)
        vx, vy = (vx / norm, vy / norm)
        x, y = (bx + vx * self.dt, by + vy * self.dt)
        vx, vy = (vx * self.drag, vy * self.drag)
        dx, dy = (x - next_p[1], y - next_p[2])
        distance = math.hypot(dx, dy)
        if 1e-08 < distance < self.body:
            nx, ny = (dx / distance, dy / distance)
            x, y = (next_p[1] + nx * self.body, next_p[2] + ny * self.body)
            closing = (vx - next_p[3]) * nx + (vy - next_p[4]) * ny
            if closing < 0:
                vx -= 1.25 * closing * nx
                vy -= 1.25 * closing * ny
        return ((x, y, vx, vy), next_p)

    def goal_aims(self, ball, opponents, wall):
        """Project visible blocker bodies onto the goal plane, then aim gaps.

        The full existing shot forecast still validates every new aim point.
        The projection proposes at most five extra candidates; it does not
        assume that a moving defender will remain stationary during a shot.
        """
        bx, by, vx, vy = ball
        fixed = (-0.97, 0.97, -0.85, 0.85, -0.6, 0.6, -0.3, 0.3, 0.0)
        if not wall or bx >= self.right - 0.2:
            return fixed
        distance = self.right + 0.25 - bx
        low, high = (-self.goal + 0.07, self.goal - 0.07)
        intervals = []
        for q in opponents:
            if q[1] <= bx + 0.8:
                continue
            horizon = min(0.45, max(0.0, (q[1] - bx) / max(14.0, vx + 16.0)))
            coast = self.dt * self.damp * (1 - self.damp ** (horizon * self.hz)) / (1 - self.damp)
            qx, qy = (q[1] + q[3] * coast, q[2] + q[4] * coast)
            scale = distance / max(0.8, qx - bx)
            centre = by + (qy - by) * scale
            extent = (self.body + 0.14) * scale
            a, b = (max(low, centre - extent), min(high, centre + extent))
            if a < b:
                intervals.append((a, b))
        gaps = []
        cursor = low
        for a, b in sorted(intervals):
            if a > cursor + 0.12:
                gaps.append((a - cursor, (a + cursor) * 0.5))
            cursor = max(cursor, b)
        if high > cursor + 0.12:
            gaps.append((high - cursor, (high + cursor) * 0.5))
        extra = []
        for width, centre in sorted(gaps, reverse=True):
            fraction = centre / self.goal
            if min((abs(fraction - old) for old in fixed + tuple(extra))) > 0.018:
                extra.append(fraction)
            if len(extra) == 5:
                break
        return tuple(extra) + fixed

    def shot(self, p, ball, opponents, movement, wall):
        bx, by, vx, vy = ball
        if bx < self.right - (65 if self.KEEPER_MODEL else 42):
            return None
        best = None
        for fraction in self.goal_aims(ball, opponents, wall):
            if perf_counter() > self.deadline:
                return best
            ux, uy = _m_unit(self.right + 0.25 - bx, self.goal * fraction - by)
            along = vx * ux + vy * uy
            sideways = max(0.0, vx * vx + vy * vy - along * along)
            if sideways >= self.impulse ** 2:
                continue
            speed = min(self.ballcap, along + math.sqrt(self.impulse ** 2 - sideways))
            if speed < 10:
                continue
            kick = self.velocity_kick(vx, vy, ux * speed, uy * speed)
            launch = self.launch(p, ball, kick, movement)
            if launch is None:
                continue
            (x, y, sx, sy), _ = launch
            modeled_keeper = opponents[0]
            previous_ball = ball
            margin = 100.0
            scored = False
            for n in range(1, 141 if self.KEEPER_MODEL else 61):
                oldx, oldy, oldvx, oldvy = previous_ball
                if self.KEEPER_MODEL and (not wall):
                    depth = 2.2
                    tx = self.right - depth
                    ty = oldy * depth / max(3.0, self.right - oldx)
                    if oldvx > 8 and math.hypot(oldvx, oldvy) >= 12 and (oldx < tx):
                        tau = (tx - oldx) / oldvx
                        if 0 < tau < 1.25:
                            ty = oldy + oldvy * tau
                    ty = _m_clip(ty, -self.goal + 0.6, self.goal - 0.6)
                    if oldx > self.right - 10:
                        own_eta = max(0, math.hypot(modeled_keeper[1] - oldx, modeled_keeper[2] - oldy) - self.kr * 0.8) / self.speed + 0.3
                        field_eta = min((max(0, math.hypot(q[1] - oldx, q[2] - oldy) - self.kr * 0.8) / self.speed + 0.3 for q in opponents[1:]), default=20)
                        if own_eta < field_eta * 0.85:
                            tx, ty = (min(self.right - 2, oldx), _m_clip(oldy, -self.half + 2, self.half - 2))
                    before = math.hypot(modeled_keeper[1] - oldx, modeled_keeper[2] - oldy)
                    moved = self.player_step(modeled_keeper, self.move(modeled_keeper, (tx, ty)))
                    if n > opponents[0][5] and before <= self.kr and (math.hypot(moved[1] - oldx, moved[2] - oldy) < self.kr - 0.18):
                        margin = -100
                        break
                    modeled_keeper = moved
                if n > 1:
                    x, y = (x + sx * self.dt, y + sy * self.dt)
                    sx, sy = (sx * self.drag, sy * self.drag)
                if abs(y) > self.half - self.br or (x > self.right - self.br and abs(y) > self.goal):
                    break
                for q in opponents:
                    if self.KEEPER_MODEL and (not wall) and (q[0] == opponents[0][0]):
                        margin = min(margin, (math.hypot(x - modeled_keeper[1], y - modeled_keeper[2]) - self.body) / self.speed)
                        continue
                    radius = self.kr if q[5] < n else self.body
                    reach_limit = self.speed * n * self.dt + radius + self.speed * 0.7
                    if (x - q[1]) ** 2 + (y - q[2]) ** 2 > reach_limit * reach_limit:
                        continue
                    gap = self.travel_gap(q, x, y, n, radius)
                    if wall and q[1] > self.right - 3.5:
                        coast = self.reach[n][0]
                        gap = math.hypot(x - q[1] - q[3] * coast, y - q[2] - q[4] * coast) - self.body - 0.12
                        if n == 1 and q[5] == 0 and (math.hypot(bx - q[1], by - q[2]) < self.kr + 0.15):
                            gap = -10.0
                    margin = min(margin, gap / self.speed)
                if margin < self.SHOT_MARGIN:
                    break
                if x > self.right:
                    scored = abs(y) < self.goal - 0.025
                    break
                previous_ball = (x, y, sx, sy)
            if scored and margin >= self.SHOT_MARGIN:
                score = 12 + min(margin, 0.7) * 5 - n * self.dt * 0.8
                if best is None or score > best[0]:
                    best = (score, kick, movement, None)
        return best

    def touch(self, p, ball, opponents, stage):
        bx, by, vx, vy = ball
        angle = math.atan2(stage[1] - by, stage[0] - bx)
        best = None
        old_distance = math.hypot(stage[0] - bx, stage[1] - by)
        for offset in (0, -0.35, 0.35, -0.75, 0.75, -1.2, 1.2):
            if perf_counter() > self.deadline:
                return best
            ux, uy = (math.cos(angle + offset), math.sin(angle + offset))
            for speed in (self.CARRY_SPEED, 5.5):
                movement = self.move(p, self.bound(bx + ux * 2, by + uy * 2))
                kick = self.velocity_kick(vx, vy, ux * speed, uy * speed)
                launched = self.launch(p, ball, kick, movement)
                if launched is None:
                    continue
                (x, y, sx, sy), own = launched
                risk = 1.0
                for n in range(1, 7):
                    if n > 1:
                        own = self.player_step(own, self.move(own, self.bound(x + sx * 0.12, y + sy * 0.12)))
                        x, y = (x + sx * self.dt, y + sy * self.dt)
                        sx, sy = (sx * self.drag, sy * self.drag)
                        dx, dy = (x - own[1], y - own[2])
                        d = math.hypot(dx, dy)
                        if 1e-08 < d < self.body:
                            nx, ny = (dx / d, dy / d)
                            x, y = (own[1] + nx * self.body, own[2] + ny * self.body)
                            closing = (sx - own[3]) * nx + (sy - own[4]) * ny
                            if closing < 0:
                                sx -= 1.25 * closing * nx
                                sy -= 1.25 * closing * ny
                    for q in opponents:
                        radius = self.kr if q[5] < n else self.body
                        risk = min(risk, self.travel_gap(q, x, y, n, radius) / self.speed)
                if abs(y) > self.half - self.br or abs(x) > self.right - self.br:
                    continue
                progress = old_distance - math.hypot(stage[0] - x, stage[1] - y)
                gap = math.hypot(x - own[1], y - own[2])
                score = progress * 1.0 + min(risk, 0.5) * 7 - max(0, gap - self.kr + 0.1) * 2
                if x < self.left + 4:
                    score -= 3
                if best is None or score > best[0]:
                    best = (score, kick, movement, None)
        return best

    def passing(self, p, ball, friends, opponents):
        bx, by, vx, vy = ball
        best = None
        for q in friends[1:]:
            if perf_counter() > self.deadline:
                return best
            if q[0] == p[0] or q[1] < bx + 3:
                continue
            gap = math.hypot(q[1] - bx, q[2] - by)
            if not 5 < gap < 33:
                continue
            for speed in (16.0, 23.0):
                lead = min(0.8, gap / speed)
                tx, ty = self.bound(q[1] + q[3] * lead + 2, q[2] + q[4] * lead)
                ux, uy = _m_unit(tx - bx, ty - by)
                kick = self.velocity_kick(vx, vy, ux * speed, uy * speed)
                movement = self.move(p, (bx + 0.3, by))
                launch = self.launch(p, ball, kick, movement)
                if launch is None:
                    continue
                route = self.path(*launch[0], steps=40)
                ours = self.race(q, route)
                theirs = min((self.race(o, route)[0] for o in opponents))
                if ours[0] > 1.8 or theirs < ours[0] + 0.18 or ours[1][0] < bx + 4:
                    continue
                score = self.PASS_WEIGHT * (0.3 * (ours[1][0] - bx) + min(0.7, theirs - ours[0]) * 3 - ours[0] * 0.7)
                if best is None or score > best[0]:
                    best = (score, kick, movement, (q[0], ours[1], 2.0))
        return best

    def lock(self, obs):
        actions = TeamAction(debug={'text': 'MONSTER lead screen'})
        for i, v in enumerate(obs.my_players):
            p = (v.id, *v.position, *v.velocity, v.kick_cooldown_ticks)
            target = (self.left + self.LOCK_DEPTH, (i - 2) * 2.75)
            movement = self.move(p, target)
            if obs.can_kick(v.id):
                actions.kick(v.id, (1, 0), 1.0, movement=movement)
            else:
                actions.move(v.id, movement)
        return actions

    def clearance(self, p, ball, outlet, opponents, movement, default):
        bx, by, vx, vy = ball
        best = None
        for ty in (outlet[2], outlet[2] + 6, outlet[2] - 6, 0):
            if perf_counter() > self.deadline:
                break
            tx = max(bx + 15, outlet[1] + 8)
            ux, uy = _m_unit(tx - bx, _m_clip(ty, -25, 25) - by)
            for compensate in (False, True):
                kick = self.velocity_kick(vx, vy, ux * 24, uy * 24) if compensate else ((ux, uy), 1.0)
                launched = self.launch(p, ball, kick, movement)
                if launched is None:
                    continue
                state = launched[0]
                if state[2] < 0.5:
                    continue
                route = self.path(*state, steps=32)
                ours = self.race(outlet, route)
                enemy = min((self.race(q, route)[0] for q in opponents))
                score = min(1.5, enemy - ours[0]) * 3 - ours[0] * 0.2 + (route[-1][1] - bx) * 0.07
                if best is None or score > best[0]:
                    best = (score, kick)
        return best[1] if best is not None else default

    def shell_act(self, obs, protected):
        """Four covering players and one fast outlet; no opponent identity test."""
        ball = (*obs.ball.position, *obs.ball.velocity)
        bx, by, vx, vy = ball
        if self.FIXED_OUTLET and self.outlet_side is None and (bx < self.left + 25) and (abs(by) > 3):
            self.outlet_side = 1 if by > 0 else -1
        release_side = self.outlet_side if self.FIXED_OUTLET and self.outlet_side is not None else 1 if by >= 0 else -1
        friends = [(p.id, *p.position, *p.velocity, p.kick_cooldown_ticks) for p in obs.my_players]
        opponents = [(p.id, *p.position, *p.velocity, p.kick_cooldown_ticks) for p in obs.opponents]
        outlet = friends[4]
        if bx < self.left + 20 and (not obs.can_kick(4)):
            side = release_side
            target = self.bound(self.OUTLET_X if self.FIXED_OUTLET else max(-7.0, outlet[1]), side * 21.0)
        else:
            path = self.stream_path(*ball)
            target = self.bound(*self.race(outlet, path)[1])
        wall = sum((q[1] > self.right - 3.5 and abs(q[2]) < self.goal + 1 for q in opponents)) >= 4
        depth = self.LOCK_DEPTH if obs.score[0] > obs.score[1] else self.SHELL_DEPTH
        if self.SHELL_LOCK_FIVE and obs.score[0] > obs.score[1]:
            return self.lock(obs)
        support_id = 3 if self.SUPPORT and wall and (bx > 0) and (not protected) else None
        slots = (5.4, -1.8, 1.8, -5.4)
        shot_guard = None
        shot_y = 0.0
        if self.PREDICT_POST and vx < -2 and (bx > self.left + 1.2):
            dx = bx - self.left - 1.2
            if dx < -vx * self.dt / (1 - self.drag):
                shot_y = by + vy * dx / -vx
                if abs(shot_y) < self.goal + 0.25:
                    shot_guard = min(range(4), key=lambda j: abs(slots[j] - shot_y))
        actions = TeamAction(debug={'text': 'MONSTER four-cover counter'})
        for i, p in enumerate(friends):
            aim = target if i == 4 else (self.left + depth, (5.4, -1.8, 1.8, -5.4)[i])
            if self.ADAPTIVE_POSTS and bx < self.left + 12 and (abs(by) > 4.0) and (i == (0 if by > 0 else 3)):
                side = 1 if by > 0 else -1
                aim = (max(self.left + self.pr + 0.02, min(self.left + depth, bx - 0.6)), side * _m_clip(abs(by), 5.4, self.POST_MAX))
            if i < 4 and self.left + depth + 1.0 < bx < self.left + 25.0:
                distance = max(3.0, bx - self.left)
                ratio = _m_clip((bx - self.left - depth) / distance, 0.6, 1.0)
                centre = by * _m_clip(depth / distance, 0.0, 0.4)
                limit = self.goal + 1.5
                centre = _m_clip(centre, -limit + 5.4 * ratio, limit - 5.4 * ratio)
                aim = (self.left + depth, centre + slots[i] * ratio)
            if self.COVER_SHIFT and i < 4 and (abs(by) > 6) and (bx < self.left + 15):
                aim = (aim[0], aim[1] + (0.55 if by > 0 else -0.55))
            if i == shot_guard:
                aim = (self.left + min(depth, 1.4), _m_clip(shot_y, -self.goal + 0.3, self.goal - 0.3))
            if support_id is not None and i < 4:
                if i == support_id:
                    aim = self.bound(max(12.0, bx - 6.0), (-1 if by >= 0 else 1) * 5.5)
                else:
                    aim = (self.left + depth, (-4.9, 0.0, 4.9)[i])
            movement = self.move(p, aim)
            kick = None
            if i == 4 and (not protected) and obs.can_kick(i):
                movement = self.move(p, (bx + 0.3, by))
                stage = (self.right + 1, (1 if by >= 0 else -1) * (self.goal + 1.3)) if wall else (self.right, 0)
                best = self.shot(p, ball, opponents, movement, wall) if self.SHOT_FIRST else None
                if best is None:
                    best = self.duel(p, ball, opponents, movement)
                if best is None:
                    best = self.shot(p, ball, opponents, movement, wall)
                if best is None:
                    old_speed = self.CARRY_SPEED
                    if self.BREAKAWAY_TOUCH and bx < self.right - 12 and (min((math.hypot(q[1] - bx, q[2] - by) for q in opponents)) > 9):
                        self.CARRY_SPEED = 11.0
                    best = self.touch(p, ball, opponents, stage)
                    self.CARRY_SPEED = old_speed
                if self.SUPPORT and support_id is not None and (best is None or best[0] < 10):
                    passed = self.passing(p, ball, friends, opponents)
                    if passed is not None and (best is None or passed[0] > best[0] + 0.3):
                        best = passed
                if best:
                    _, kick, movement, _ = best
            elif i == support_id and (not protected) and obs.can_kick(i):
                movement = self.move(p, (bx + 0.3, by))
                best = self.shot(p, ball, opponents, movement, wall)
                if best is None:
                    best = self.duel(p, ball, opponents, movement)
                if best is None:
                    best = self.touch(p, ball, opponents, (self.right, 0))
                if best:
                    _, kick, movement, _ = best
            elif i < 4 and (not protected) and obs.can_kick(i):
                side = release_side
                tx, ty = (max(-4.0, outlet[1] + 5), side * 22.0)
                if self.SHELL_BANK:
                    boundary = side * (self.half - self.br)
                    ty = boundary + (boundary - ty) / self.wall
                ux, uy = _m_unit(tx - bx, ty - by)
                kick = ((ux, uy), 1.0)
                if self.SMART_CLEAR:
                    kick = self.clearance(p, ball, outlet, opponents, movement, kick)
            if protected and i == 4 and (math.hypot(p[1], p[2]) < self.circle + 4):
                ux, uy = _m_unit(p[1], p[2])
                movement = self.move(p, (ux * (self.circle + 2.5), uy * (self.circle + 2.5)))
            if kick:
                actions.kick(i, kick[0], kick[1], movement=movement)
            else:
                actions.move(i, movement)
        return actions

    def act(self, obs):
        self.deadline = perf_counter() + 0.007
        if not self.ready:
            self.setup(obs.field)
        score = tuple(obs.score)
        if self.last_score is None or score != self.last_score:
            self.restart_until = obs.tick + int(3 * self.hz)
            self.restart_owner = obs.ball.controlling_team
            self.receiver = None
        self.last_score = score
        ball = (*obs.ball.position, *obs.ball.velocity)
        bx, by, vx, vy = ball
        if math.hypot(bx, by) > 0.5 or math.hypot(vx, vy) > 0.1:
            self.restart_until = -1
        protected = obs.tick < self.restart_until and self.restart_owner == 1
        visible_enemy_wall = self.SHELL_RELEASE and sum((q.position[0] > self.right - 3.5 and abs(q.position[1]) < self.goal + 1 for q in obs.opponents)) >= 4
        if self.SHELL and (not (self.SHELL_RELEASE and (visible_enemy_wall or score[0] < score[1]))):
            return self.shell_act(obs, protected)
        if self.LOCK_LEAD and score[0] - score[1] >= self.LOCK_LEAD and (not protected):
            return self.lock(obs)
        friends = [(p.id, *p.position, *p.velocity, p.kick_cooldown_ticks) for p in obs.my_players]
        opponents = [(p.id, *p.position, *p.velocity, p.kick_cooldown_ticks) for p in obs.opponents]
        trajectory = self.path(*ball)
        races = {p[0]: self.race(p, trajectory) for p in friends}
        enemy_time = min((self.race(q, trajectory)[0] for q in opponents))
        field_players = friends[2:] if self.TWIN_KEEPERS else friends[1:]
        order = sorted(field_players, key=lambda p: races[p[0]][0] - (0.07 if p[0] == self.previous_chaser else 0))
        chaser = order[0]
        self.previous_chaser = chaser[0]
        wall = sum((q[1] > self.right - 3.5 and abs(q[2]) < self.goal + 1 for q in opponents)) >= 4
        targets = {chaser[0]: self.bound(*races[chaser[0]][1])}
        free = order[1:]
        ours = races[chaser[0]][0] + 0.1 < enemy_time
        if wall:
            for p, q in zip(sorted(free, key=lambda p: p[2]), sorted(opponents, key=lambda p: abs(p[2] - by))[:len(free)]):
                targets[p[0]] = self.bound(q[1] + 0.1, q[2])
        elif not ours:
            if self.PRESSERS >= 2 and free and (bx > self.left + 15):
                q = free.pop(0)
                targets[q[0]] = self.bound(bx - 3.5, by * 0.8)
            if self.PRESSERS >= 3 and len(free) >= 2 and (bx > -10):
                q = free.pop(0)
                targets[q[0]] = self.bound(bx + 1.5, by + (3.0 if q[2] >= by else -3.0))
            threats = sorted(opponents, key=lambda q: q[1] + abs(q[2]) * 0.15)
            for p in free:
                threat = next((q for q in threats if math.hypot(q[1] - bx, q[2] - by) > 4), None)
                if threat:
                    threats.remove(threat)
                    ux, uy = _m_unit(self.left - threat[1], -threat[2])
                    targets[p[0]] = self.bound(threat[1] + 3 * ux, threat[2] + 3 * uy)
                else:
                    targets[p[0]] = self.bound(bx - 9, by * 0.4)
        else:
            cover = min(free, key=lambda p: p[1])
            targets[cover[0]] = self.bound(bx - 8, by * 0.45)
            runners = sorted((p for p in free if p[0] != cover[0]), key=lambda p: p[2])
            for i, p in enumerate(runners):
                targets[p[0]] = self.bound(bx + 10 + 3 * i, (-1 if i == 0 else 1) * self.WIDTH + by * 0.15)
        keeper = friends[0]
        if self.DEFENSE and bx < 12 and (not ours or self.DEFENSE >= 2):
            guards = sorted((p for p in friends[1:] if p[0] != chaser[0]), key=lambda p: p[1])[:2]
            guards.sort(key=lambda p: p[2])
            for index, guard in enumerate(guards):
                targets[guard[0]] = (self.left + 2.0, (-1 if index == 0 else 1) * 4.6)
        kx = self.left + self.KEEPER_DEPTH
        ky = by * self.KEEPER_DEPTH / max(3, bx - self.left)
        if vx < -1:
            scale = (kx - bx) / vx
            stop = abs(vx) * self.dt / (1 - self.drag)
            if 0 < scale < 2.2 and bx - kx < stop:
                gy = by + vy * (self.left - bx) / vx
                if abs(gy) < self.goal + 0.2:
                    ky = by + vy * scale
        targets[0] = (kx, _m_clip(ky, -self.goal + 0.25, self.goal - 0.25))
        if self.TWIN_KEEPERS:
            threatening = vx < -1 and bx - kx < abs(vx) * self.dt / (1 - self.drag) and (abs(by + vy * (self.left - bx) / vx) < self.goal + 0.3)
            gy = by + vy * (kx - bx) / vx if threatening else None
            targets[0] = (kx, _m_clip(gy, -self.goal + 0.2, -0.5) if gy is not None else -3.2)
            targets[1] = (kx, _m_clip(gy, 0.5, self.goal - 0.2) if gy is not None else 3.2)
        if self.SWEEP and bx < self.left + 12 and (races[0][0] + 0.35 < enemy_time) and (races[0][0] < 0.8):
            targets[0] = self.bound(*races[0][1])
        if self.receiver:
            rid, passer, expiry = self.receiver
            if obs.tick > expiry or obs.ball.last_touch not in (passer, None):
                self.receiver = None
            else:
                targets[rid] = self.bound(*races[rid][1])
        actions = TeamAction(debug={'text': 'MONSTER wall siege' if wall else 'MONSTER predictive pressure'})
        carrier = min((p for p in friends if obs.can_kick(p[0])), key=lambda p: math.hypot(p[1] - bx, p[2] - by), default=None)
        for p in friends:
            movement = self.move(p, targets.get(p[0], p[1:3]))
            if protected and math.hypot(p[1], p[2]) < self.circle + 4:
                ux, uy = _m_unit(p[1], p[2])
                movement = self.move(p, (ux * (self.circle + 2.5), uy * (self.circle + 2.5)))
            kick = None
            if carrier is not None and p[0] == carrier[0] and (not protected):
                movement = self.move(p, (bx + 0.3, by))
                stage = (self.right, 0)
                if wall:
                    stage = (self.right + 1.0, (1 if by >= 0 else -1) * (self.goal + 1.3))
                best = self.duel(p, ball, opponents, movement)
                if best is None:
                    best = self.shot(p, ball, opponents, movement, wall)
                if best is None:
                    best = self.touch(p, ball, opponents, stage)
                    passed = self.passing(p, ball, friends, opponents) if not wall else None
                    if passed is not None and (best is None or passed[0] > best[0] + 0.5):
                        best = passed
                if best:
                    _, kick, movement, plan = best
                    if plan:
                        rid, point, seconds = plan
                        self.receiver = (rid, p[0], obs.tick + int(seconds * self.hz))
                        targets[rid] = self.bound(*point)
                if (p[0] == 0 or (self.TWIN_KEEPERS and p[0] == 1)) and (best is None or best[0] < 0):
                    kick = self.velocity_kick(vx, vy, 22, -8 if by > 0 else 8)
            if kick:
                actions.kick(p[0], kick[0], kick[1], movement=movement)
            else:
                actions.move(p[0], movement)
        if self.receiver:
            rid = self.receiver[0]
            if carrier is None or rid != carrier[0]:
                p = friends[rid]
                actions.move(rid, self.move(p, targets[rid]))
        return actions

class MonsterNovaHybrid(TeamController):
    name = 'MONSTER NOVA Hybrid'
    version = 'dev1-gaps'

    def __init__(self):
        self._nova = _NovaPolicy()
        self._monster = _MonsterPolicy()
        self.reset(0)

    def reset(self, seed):
        self._nova.reset(seed)
        self._monster.reset(seed)
        self._hybrid_counts = {'cover_updates': 0, 'extra_aims': 0, 'corner_checks': 0, 'corner_overrides': 0}
        self._nova._hybrid_counts = self._hybrid_counts
        self._nova._hybrid_monster = self._monster

    def initial_formation(self, field):
        return None

    def act(self, obs):
        started = perf_counter()
        if not self._monster.ready:
            self._monster.setup(obs.field)
        self._monster.deadline = started + 0.017
        self._nova._hybrid_tick = obs.tick
        self._nova._hybrid_lead = obs.score[0] - obs.score[1]
        return self._nova._act(obs)
