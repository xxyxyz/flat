from math import ceil, hypot, sqrt
from .misc import similar
from .polynomial import evaluate2, evaluate3, roots1, roots2




def power1(x0, y0, x1, y1):
    x1 = x1-x0
    y1 = y1-y0
    return x1, x0, y1, y0

def power2(x0, y0, x1, y1, x2, y2):
    x2, x1 = x2-2.0*x1+x0, 2.0*(x1-x0)
    y2, y1 = y2-2.0*y1+y0, 2.0*(y1-y0)
    return x2, x1, x0, y2, y1, y0

def power3(x0, y0, x1, y1, x2, y2, x3, y3):
    x3, x2, x1 = x3-3.0*(x2-x1)-x0, 3.0*(x2-2*x1+x0), 3.0*(x1-x0)
    y3, y2, y1 = y3-3.0*(y2-y1)-y0, 3.0*(y2-2*y1+y0), 3.0*(y1-y0)
    return x3, x2, x1, x0, y3, y2, y1, y0




def bezier1(x0, y0, x1, y1, t):
    x0, y0 = x0+(x1-x0)*t, y0+(y1-y0)*t
    return x0, y0

def bezier2(x0, y0, x1, y1, x2, y2, t):
    x0, y0 = x0+(x1-x0)*t, y0+(y1-y0)*t
    x1, y1 = x1+(x2-x1)*t, y1+(y2-y1)*t
    x0, y0 = x0+(x1-x0)*t, y0+(y1-y0)*t
    return x0, y0

def bezier3(x0, y0, x1, y1, x2, y2, x3, y3, t):
    x0, y0 = x0+(x1-x0)*t, y0+(y1-y0)*t
    x1, y1 = x1+(x2-x1)*t, y1+(y2-y1)*t
    x2, y2 = x2+(x3-x2)*t, y2+(y3-y2)*t
    x0, y0 = x0+(x1-x0)*t, y0+(y1-y0)*t
    x1, y1 = x1+(x2-x1)*t, y1+(y2-y1)*t
    x0, y0 = x0+(x1-x0)*t, y0+(y1-y0)*t
    return x0, y0




def halve1(x0, y0, x1, y1):
    x2, y2 = (x0+x1)*0.5, (y0+y1)*0.5
    return (
        (x0, y0, x2, y2),
        (x2, y2, x1, y1))
    
def halve2(x0, y0, x1, y1, x2, y2):
    x4, y4 = x1+x2, y1+y2
    x1, y1 = x0+x1, y0+y1
    x5, y5 = (x1+x4)*0.25, (y1+y4)*0.25
    return (
        (x0, y0, x1*0.5, y1*0.5, x5, y5),
        (x5, y5, x4*0.5, y4*0.5, x2, y2))

def halve3(x0, y0, x1, y1, x2, y2, x3, y3):
    x6, y6 = x2+x3, y2+y3
    x5, y5 = x1+x2, y1+y2
    x1, y1 = x0+x1, y0+y1
    x8, y8 = x5+x6, y5+y6
    x2, y2 = x1+x5, y1+y5
    x9, y9 = (x2+x8)*0.125, (y2+y8)*0.125
    return (
        (x0, y0, x1*0.5, y1*0.5, x2*0.25, y2*0.25, x9, y9),
        (x9, y9, x8*0.25, y8*0.25, x6*0.5, y6*0.5, x3, y3))




def split1(x0, y0, x1, y1, t):
    x2, y2 = x0+(x1-x0)*t, y0+(y1-y0)*t
    return (
        (x0, y0, x2, y2),
        (x2, y2, x1, y1))

def split2(x0, y0, x1, y1, x2, y2, t):
    x4, y4 = x1+(x2-x1)*t, y1+(y2-y1)*t
    x1, y1 = x0+(x1-x0)*t, y0+(y1-y0)*t
    x5, y5 = x1+(x4-x1)*t, y1+(y4-y1)*t
    return (
        (x0, y0, x1, y1, x5, y5),
        (x5, y5, x4, y4, x2, y2))

def split3(x0, y0, x1, y1, x2, y2, x3, y3, t):
    x6, y6 = x2+(x3-x2)*t, y2+(y3-y2)*t
    x5, y5 = x1+(x2-x1)*t, y1+(y2-y1)*t
    x1, y1 = x0+(x1-x0)*t, y0+(y1-y0)*t
    x8, y8 = x5+(x6-x5)*t, y5+(y6-y5)*t
    x2, y2 = x1+(x5-x1)*t, y1+(y5-y1)*t
    x9, y9 = x2+(x8-x2)*t, y2+(y8-y2)*t
    return (
        (x0, y0, x1, y1, x2, y2, x9, y9),
        (x9, y9, x8, y8, x6, y6, x3, y3))




def chop1(x0, y0, x1, y1, ts):
    ts = [t for t in ts if 0.0 < t < 1.0]
    ts.sort()
    stack = []
    while True:
        if ts:
            m = len(ts)//2
            t = ts[m]
            vs = [(v-t)/(1.0-t) for v in ts[m+1:] if v > t]
            ts = [u/t for u in ts[:m] if u < t]
            x2, y2 = x0+(x1-x0)*t, y0+(y1-y0)*t
            stack.append((x2, y2, x1, y1, vs))
            x1, y1 = x2, y2
        else:
            yield x0, y0, x1, y1
            if not stack:
                break
            x0, y0, x1, y1, ts = stack.pop()

def chop2(x0, y0, x1, y1, x2, y2, ts):
    ts = [t for t in ts if 0.0 < t < 1.0]
    ts.sort()
    stack = []
    while True:
        if ts:
            m = len(ts)//2
            t = ts[m]
            vs = [(v-t)/(1.0-t) for v in ts[m+1:] if v > t]
            ts = [u/t for u in ts[:m] if u < t]
            x4, y4 = x1+(x2-x1)*t, y1+(y2-y1)*t
            x1, y1 = x0+(x1-x0)*t, y0+(y1-y0)*t
            x5, y5 = x1+(x4-x1)*t, y1+(y4-y1)*t
            stack.append((x5, y5, x4, y4, x2, y2, vs))
            x2, y2 = x5, y5
        else:
            yield x0, y0, x1, y1, x2, y2
            if not stack:
                break
            x0, y0, x1, y1, x2, y2, ts = stack.pop()

def chop3(x0, y0, x1, y1, x2, y2, x3, y3, ts):
    ts = [t for t in ts if 0.0 < t < 1.0]
    ts.sort()
    stack = []
    while True:
        if ts:
            m = len(ts)//2
            t = ts[m]
            vs = [(v-t)/(1.0-t) for v in ts[m+1:] if v > t]
            ts = [u/t for u in ts[:m] if u < t]
            x6, y6 = x2+(x3-x2)*t, y2+(y3-y2)*t
            x5, y5 = x1+(x2-x1)*t, y1+(y2-y1)*t
            x1, y1 = x0+(x1-x0)*t, y0+(y1-y0)*t
            x8, y8 = x5+(x6-x5)*t, y5+(y6-y5)*t
            x2, y2 = x1+(x5-x1)*t, y1+(y5-y1)*t
            x9, y9 = x2+(x8-x2)*t, y2+(y8-y2)*t
            stack.append((x9, y9, x8, y8, x6, y6, x3, y3, vs))
            x3, y3 = x9, y9
        else:
            yield x0, y0, x1, y1, x2, y2, x3, y3
            if not stack:
                break
            x0, y0, x1, y1, x2, y2, x3, y3, ts = stack.pop()




def _angle_cosine(x0, y0, x1, y1, x2, y2):
    ax, ay = x0-x1, y0-y1
    bx, by = x2-x1, y2-y1
    a = hypot(ax, ay)
    b = hypot(bx, by)
    ax, ay = ax/a, ay/a
    bx, by = bx/b, by/b
    return ax*bx + ay*by

def subdivide2(x0, y0, x1, y1, x2, y2, threshold=-sqrt(2.0+sqrt(2.0))/2.0):
    stack = []
    while True:
        theta = _angle_cosine(x0, y0, x1, y1, x2, y2)
        if theta > threshold:
            u = (x0-x1)**2 + (y0-y1)**2
            v = (x2-x1)**2 + (y2-y1)**2
            if similar(u, v):
                first, second = halve2(x0, y0, x1, y1, x2, y2)
            else:
                t = (u - sqrt(u*v))/(u - v)
                first, second = split2(x0, y0, x1, y1, x2, y2, t)
            x0, y0, x1, y1, x2, y2 = first
            stack.append(second)
        else:
            yield x0, y0, x1, y1, x2, y2
            if not stack:
                break
            x0, y0, x1, y1, x2, y2 = stack.pop()

def subdivide3(x0, y0, x1, y1, x2, y2, x3, y3, threshold=-sqrt(2.0+sqrt(2.0))/2.0):
    stack = []
    while True:
        if similar(x0, x1) and similar(y0, y1):
            theta = _angle_cosine(x0, y0, x2, y2, x3, y3)
        elif similar(x1, x2) and similar(y1, y2):
            theta = _angle_cosine(x0, y0, (x1+x2)/2.0, (y1+y2)/2.0, x3, y3)
        elif similar(x2, x3) and similar(y2, y3):
            theta = _angle_cosine(x0, y0, x1, y1, x3, y3)
        else:
            theta = max(_angle_cosine(x0, y0, x1, y1, x2, y2), _angle_cosine(x1, y1, x2, y2, x3, y3))
        if theta > threshold:
            first, second = halve3(x0, y0, x1, y1, x2, y2, x3, y3)
            x0, y0, x1, y1, x2, y2, x3, y3 = first
            stack.append(second)
        else:
            yield x0, y0, x1, y1, x2, y2, x3, y3
            if not stack:
                break
            x0, y0, x1, y1, x2, y2, x3, y3 = stack.pop()




def bbox1(x0, y0, x1, y1):
    minx, maxx = min(x0, x1), max(x0, x1)
    miny, maxy = min(y0, y1), max(y0, y1)
    return minx, miny, maxx, maxy

def bbox2(x0, y0, x1, y1, x2, y2):
    minx, maxx = min(x0, x2), max(x0, x2)
    miny, maxy = min(y0, y2), max(y0, y2)
    x2, x1, x0, y2, y1, y0 = power2(x0, y0, x1, y1, x2, y2)
    for t in roots1(2.0*x2, x1):
        if 0.0 < t < 1.0:
            x = evaluate2(x2, x1, x0, t)
            if x < minx:
                minx = x
            elif x > maxx:
                maxx = x
    for t in roots1(2.0*y2, y1):
        if 0.0 < t < 1.0:
            y = evaluate2(y2, y1, y0, t)
            if y < miny:
                miny = y
            elif y > maxy:
                maxy = y
    return minx, miny, maxx, maxy

def bbox3(x0, y0, x1, y1, x2, y2, x3, y3):
    minx, maxx = min(x0, x3), max(x0, x3)
    miny, maxy = min(y0, y3), max(y0, y3)
    x3, x2, x1, x0, y3, y2, y1, y0 = power3(x0, y0, x1, y1, x2, y2, x3, y3)
    for t in roots2(3.0*x3, 2.0*x2, x1):
        if 0.0 < t < 1.0:
            x = evaluate3(x3, x2, x1, x0, t)
            if x < minx:
                minx = x
            elif x > maxx:
                maxx = x
    for t in roots2(3.0*y3, 2.0*y2, y1):
        if 0.0 < t < 1.0:
            y = evaluate3(y3, y2, y1, y0, t)
            if y < miny:
                miny = y
            elif y > maxy:
                maxy = y
    return minx, miny, maxx, maxy




def polyline2(x0, y0, x1, y1, x2, y2):
    minx, maxx = min(x0, x1, x2), max(x0, x1, x2)
    miny, maxy = min(y0, y1, y2), max(y0, y1, y2)
    if maxx - minx > maxy - miny:
        ts = roots1(x2-2.0*x1+x0, x1-x0)
    else:
        ts = roots1(y2-2.0*y1+y0, y1-y0)
    for t in ts:
        if 0.0 < t < 1.0:
            yield bezier2(x0, y0, x1, y1, x2, y2, t)

def polyline3(x0, y0, x1, y1, x2, y2, x3, y3):
    minx, maxx = min(x0, x1, x2, x3), max(x0, x1, x2, x3)
    miny, maxy = min(y0, y1, y2, y3), max(y0, y1, y2, y3)
    if maxx - minx > maxy - miny:
        ts = roots2(x3-3.0*(x2-x1)-x0, 2.0*(x2-2*x1+x0), x1-x0)
    else:
        ts = roots2(y3-3.0*(y2-y1)-y0, 2.0*(y2-2*y1+y0), y1-y0)
    for t in sorted(ts):
        if 0.0 < t < 1.0:
            yield bezier3(x0, y0, x1, y1, x2, y2, x3, y3, t)




def segments2(x0, y0, x1, y1, x2, y2, error=0.25):
    # Ref.: Sederberg, T. W. (2016). Computer Aided Geometric Design, 10.6 Error Bounds.
    lx = abs(x2 - 2.0*x1 + x0)
    ly = abs(y2 - 2.0*y1 + y0)
    m = sqrt(sqrt(lx**2 + ly**2)/(4.0*error))
    return int(ceil(m))

def segments3(x0, y0, x1, y1, x2, y2, x3, y3, error=0.25):
    lx = max(abs(x3 - 2.0*x2 + x1), abs(x2 - 2.0*x1 + x0))
    ly = max(abs(y3 - 2.0*y2 + y1), abs(y2 - 2.0*y1 + y0))
    m = sqrt(3.0*sqrt(lx**2 + ly**2)/(4.0*error))
    return int(ceil(m))




def inflections3(x0, y0, x1, y1, x2, y2, x3, y3):
    x3, x2, x1 = x3-3.0*(x2-x1)-x0, x2-2.0*x1+x0, x1-x0
    y3, y2, y1 = y3-3.0*(y2-y1)-y0, y2-2.0*y1+y0, y1-y0
    a = x2*y3 - x3*y2
    b = x1*y3 - x3*y1
    c = x1*y2 - x2*y1
    return roots2(a, b, c)




def elevate2(x0, y0, x1, y1, x2, y2):
    x3, y3 = x0+2.0/3.0*(x1-x0), y0+2.0/3.0*(y1-y0)
    x4, y4 = x2+2.0/3.0*(x1-x2), y2+2.0/3.0*(y1-y2)
    return x0, y0, x3, y3, x4, y4, x2, y2

def reduce3(x0, y0, x1, y1, x2, y2, x3, y3):
    x, y = (3.0*(x1+x2)-x0-x3)/4.0, (3.0*(y1+y2)-y0-y3)/4.0
    return x0, y0, x, y, x3, y3




def offset1(x0, y0, x1, y1, distance):
    dx, dy = x1-x0, y1-y0
    d = hypot(dx, dy)
    ux, uy = dy/d, -dx/d
    x0, y0 = x0+ux*distance, y0+uy*distance
    x1, y1 = x1+ux*distance, y1+uy*distance
    return x0, y0, x1, y1

def offset2(x0, y0, x1, y1, x2, y2, distance):
    dx, dy = x1-x0, y1-y0
    ex, ey = x2-x1, y2-y1
    d = hypot(dx, dy)
    e = hypot(ex, ey)
    ux, uy = dy/d, -dx/d
    vx, vy = ey/e, -ex/e
    uv = ux*vx + uy*vy + 1.0
    x0, y0 = x0+ux*distance, y0+uy*distance
    x2, y2 = x2+vx*distance, y2+vy*distance
    x1, y1 = x1+(ux+vx)*distance/uv, y1+(uy+vy)*distance/uv
    return x0, y0, x1, y1, x2, y2

def offset3(x0, y0, x1, y1, x2, y2, x3, y3, distance):
    dx, dy = x1-x0, y1-y0
    fx, fy = x3-x2, y3-y2
    d = hypot(dx, dy)
    f = hypot(fx, fy)
    ux, uy = dy/d, -dx/d
    wx, wy = fy/f, -fx/f
    k = hypot(x3-x0, y3-y0)
    x0, y0 = x0+ux*distance, y0+uy*distance
    x3, y3 = x3+wx*distance, y3+wy*distance
    k = hypot(x3-x0, y3-y0)/k
    x1, y1 = x0+dx*k, y0+dy*k
    x2, y2 = x3-fx*k, y3-fy*k
    return x0, y0, x1, y1, x2, y2, x3, y3




def arc3(x, y, x0, y0, x3, y3):
    ax, ay = x0-x, y0-y
    dx, dy = x3-x, y3-y
    u = ax*dy - ay*dx
    v = dx*dx + dy*dy
    w = ax*dx + ay*dy - v
    k = 4.0/3.0*(u - sqrt(-2.0*v*w))/w
    x1, y1 = x0-ay*k, y0+ax*k
    x2, y2 = x3+dy*k, y3-dx*k
    return x0, y0, x1, y1, x2, y2, x3, y3




