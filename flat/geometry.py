
from math import acos, cos, hypot, pi, sqrt




def cbrt(x):
    if x < 0.0:
        return -(-x) ** (1.0 / 3.0)
    return x ** (1.0 / 3.0)




def roots2(a, b, c):
    if a == 0.0:
        if b == 0.0:
            return ()
        return -c / float(b), # TODO python 3: remove float()
    u = 0.5 * b / a
    v = u*u - c / float(a) # TODO python 3: remove float()
    if v > 0.0:
        x = sqrt(v)
        return x - u, -x - u
    if v == 0.0:
        return -u,
    return ()


def roots3(a, b, c, d):
    if a == 0.0:
        return roots2(b, c, d)
    a, b, c = b / float(a), c / float(a), d / float(a) # TODO python 3: remove float()
    a3 = a / 3.0
    q = (3.0 * b - a*a) / 9.0
    qqq = q*q*q
    r = (9.0 * a * b - 27.0 * c - 2 * a*a*a) / 54.0
    d = qqq + r*r
    if d > 0.0:
        x = sqrt(d)
        s = cbrt(r + x)
        t = cbrt(r - x)
        return s + t - a3,
    if d == 0.0:
        if r == 0.0:
            return -a3,
        s = cbrt(r)
        return s + s - a3, -s - a3
    theta3 = acos(r / sqrt(-qqq)) / 3.0
    x = 2.0 * sqrt(-q)
    return (
        x * cos(theta3) - a3,
        -x * cos(theta3 + pi / 3.0) - a3,
        -x * cos(theta3 - pi / 3.0) - a3)




def bezier2(x0, y0, x1, y1, x2, y2, t):
    u = 1.0 - t
    tt, uu = t*t, u*u
    x = uu*x0 + 2.0*u*t*x1 + tt*x2
    y = uu*y0 + 2.0*u*t*y1 + tt*y2
    return x, y


def bezier3(x0, y0, x1, y1, x2, y2, x3, y3, t):
    u = 1.0 - t
    tt, uu = t*t, u*u
    ttt, uuu = tt*t, uu*u
    x = uuu*x0 + 3.0*uu*t*x1 + 3.0*u*tt*x2 + ttt*x3
    y = uuu*y0 + 3.0*uu*t*y1 + 3.0*u*tt*y2 + ttt*y3
    return x, y




def tangent2(x0, y0, x1, y1, x2, y2, t):
    t = 2.0 * t
    u = 2.0 - t
    dx = u*(x1-x0) + t*(x2-x1)
    dy = u*(y1-y0) + t*(y2-y1)
    return dx, dy


def tangent3(x0, y0, x1, y1, x2, y2, x3, y3, t):
    u = 1.0 - t
    tt, uu = t*t, u*u
    dx = 3.0 * (uu*(x1-x0) + 2.0*t*u*(x2-x1) + tt*(x3-x2))
    dy = 3.0 * (uu*(y1-y0) + 2.0*t*u*(y2-y1) + tt*(y3-y2))
    return dx, dy




def split2(x0, y0, x1, y1, x2, y2, t):
    x01 = x0 + (x1 - x0) * t
    y01 = y0 + (y1 - y0) * t
    x12 = x1 + (x2 - x1) * t
    y12 = y1 + (y2 - y1) * t
    x02 = x01 + (x12 - x01) * t
    y02 = y01 + (y12 - y01) * t
    a = x0, y0, x01, y01, x02, y02
    b = x02, y02, x12, y12, x2, y2
    return a, b


def split3(x0, y0, x1, y1, x2, y2, x3, y3, t):
    x01 = x0 + (x1 - x0) * t
    y01 = y0 + (y1 - y0) * t
    x12 = x1 + (x2 - x1) * t
    y12 = y1 + (y2 - y1) * t
    x23 = x2 + (x3 - x2) * t
    y23 = y2 + (y3 - y2) * t
    x0112 = x01 + (x12 - x01) * t
    y0112 = y01 + (y12 - y01) * t
    x1223 = x12 + (x23 - x12) * t
    y1223 = y12 + (y23 - y12) * t
    x01121223 = x0112 + (x1223 - x0112) * t
    y01121223 = y0112 + (y1223 - y0112) * t
    a = x0, y0, x01, y01, x0112, y0112, x01121223, y01121223
    b = x01121223, y01121223, x1223, y1223, x23, y23, x3, y3
    return a, b


def halves2(x0, y0, x1, y1, x2, y2):
    x01 = (x0 + x1) * 0.5
    y01 = (y0 + y1) * 0.5
    x12 = (x1 + x2) * 0.5
    y12 = (y1 + y2) * 0.5
    x02 = (x01 + x12) * 0.5
    y02 = (y01 + y12) * 0.5
    a = x0, y0, x01, y01, x02, y02
    b = x02, y02, x12, y12, x2, y2
    return a, b


def halves3(x0, y0, x1, y1, x2, y2, x3, y3):
    x01 = (x0 + x1) * 0.5
    y01 = (y0 + y1) * 0.5
    x12 = (x1 + x2) * 0.5
    y12 = (y1 + y2) * 0.5
    x23 = (x2 + x3) * 0.5
    y23 = (y2 + y3) * 0.5
    x0112 = (x01 + x12) * 0.5
    y0112 = (y01 + y12) * 0.5
    x1223 = (x12 + x23) * 0.5
    y1223 = (y12 + y23) * 0.5
    x01121223 = (x0112 + x1223) * 0.5
    y01121223 = (y0112 + y1223) * 0.5
    a = x0, y0, x01, y01, x0112, y0112, x01121223, y01121223
    b = x01121223, y01121223, x1223, y1223, x23, y23, x3, y3
    return a, b




def elevate2(x0, y0, x1, y1, x2, y2):
    cx1 = x0 + 2.0/3.0 * (x1 - x0)
    cy1 = y0 + 2.0/3.0 * (y1 - y0)
    cx2 = x2 + 2.0/3.0 * (x1 - x2)
    cy2 = y2 + 2.0/3.0 * (y1 - y2)
    return x0, y0, cx1, cy1, cx2, cy2, x2, y2


def reduce3(x0, y0, x1, y1, x2, y2, x3, y3, scale):
    ts = inflections3(x0, y0, x1, y1, x2, y2, x3, y3)
    ts = [t for t in ts if 0.0 < t < 1.0]
    ts.sort()
    if len(ts) == 0:
        parts = (x0, y0, x1, y1, x2, y2, x3, y3),
    elif len(ts) == 1:
        parts = split3(x0, y0, x1, y1, x2, y2, x3, y3, ts[0])
    else: # 2
        t0, t1 = ts
        a, (x0, y0, x1, y1, x2, y2, x3, y3) = split3(
            x0, y0, x1, y1, x2, y2, x3, y3, t0)
        b, c = split3(x0, y0, x1, y1, x2, y2, x3, y3, (t1-t0)/(1.0-t0))
        parts = a, b, c
    result = []
    for p in parts:
        _reduce3_subdivide(p, result, scale)
    return result

def _reduce3_subdivide(coordinates, result, scale, depth=3):
    x0, y0, x1, y1, x2, y2, x3, y3 = coordinates
    p = intersect11(x0, y0, x1, y1, x2, y2, x3, y3)
    px, py = p if p else ((x1+x2)*0.5, (y1+y2)*0.5)
    if p or side1(x0, y0, x3, y3, x1, y1) == side1(x0, y0, x3, y3, x2, y2):
        qx, qy = bezier3(x0, y0, x1, y1, x2, y2, x3, y3, 0.5)
        error = nearest2(x0, y0, px, py, x3, y3, qx, qy)
    else:
        error = 1e100
    if error * scale * scale > 0.25 and depth > 0:
        a, b = halves3(x0, y0, x1, y1, x2, y2, x3, y3)
        _reduce3_subdivide(a, result, scale, depth-1)
        _reduce3_subdivide(b, result, scale, depth-1)
    else:
        result.append((x0, y0, px, py, x3, y3))




def offset1(x0, y0, x1, y1, distance):
    dx, dy = x1 - x0, y1 - y0
    d = distance / hypot(dx, dy)
    nx, ny = dy * d, -dx * d
    return x0+nx, y0+ny, x1+nx, y1+ny


def offset2(x0, y0, x1, y1, x2, y2, distance, scale):
    result = []
    _offset2_subdivide((x0, y0, x1, y1, x2, y2), distance, result, scale)
    return result

def _offset2_subdivide(coordinates, distance, result, scale, depth=3):
    x0, y0, x1, y1, x2, y2 = coordinates
    dx0, dy0 = x1 - x0, y1 - y0
    dx2, dy2 = x2 - x1, y2 - y1
    d0 = hypot(dx0, dy0)
    d2 = hypot(dx2, dy2)
    nx0, ny0 = dy0 / d0, -dx0 / d0
    nx2, ny2 = dy2 / d2, -dx2 / d2
    dot1 = nx0 * nx2 + ny0 * ny2 + 1.0
    x3 = x0 + distance * nx0
    y3 = y0 + distance * ny0
    x4 = x1 + distance * (nx0 + nx2) / dot1
    y4 = y1 + distance * (ny0 + ny2) / dot1
    x5 = x2 + distance * nx2
    y5 = y2 + distance * ny2
    px, py = bezier2(x0, y0, x1, y1, x2, y2, 0.5)
    qx, qy = bezier2(x3, y3, x4, y4, x5, y5, 0.5)
    error = hypot(qx-px, qy-py) - abs(distance)
    if error * scale > 0.5 and depth > 0:
        a, b = halves2(x0, y0, x1, y1, x2, y2)
        _offset2_subdivide(a, distance, result, scale, depth-1)
        _offset2_subdivide(b, distance, result, scale, depth-1)
    else:
        result.append((x3, y3, x4, y4, x5, y5))




def inflections3(x0, y0, x1, y1, x2, y2, x3, y3):
    cx = x1 - x0
    cy = y1 - y0
    bx = x2 - x1 - cx
    by = y2 - y1 - cy
    ax = x3 - x0 + 3.0*(x1 - x2)
    ay = y3 - y0 + 3.0*(y1 - y2)
    a = ay*bx - ax*by
    b = ay*cx - ax*cy
    c = by*cx - bx*cy
    return roots2(a, b, c)




def nearest2(x0, y0, x1, y1, x2, y2, px, py):
    ax, ay = x1 - x0, y1 - y0
    bx, by = x2 - x1 - ax, y2 - y1 - ay
    dx, dy = x0 - px, y0 - py
    a = bx*bx + by*by
    b = 3 * (ax * bx + ay * by)
    c = 2 * (ax*ax + ay*ay) + dx * bx + dy * by
    d = dx * ax + dy * ay
    roots = roots3(a, b, c, d)
    minimum, t = (px-x0)**2 + (py-y0)**2, 0.0
    m = (px-x2)**2 + (py-y2)**2
    if m < minimum:
        minimum, t = m, 1.0
    for r in roots:
        if 0.0 <= r <= 1.0:
            x, y = bezier2(x0, y0, x1, y1, x2, y2, r)
            m = (px-x)**2 + (py-y)**2
            if m < minimum:
                minimum, t = m, r
    return minimum




def side1(x0, y0, x1, y1, px, py):
    return (x1 - x0) * (py - y0) > (y1 - y0) * (px - x0)




def intersect11(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):
    ax10 = ax1 - ax0
    ay10 = ay1 - ay0
    bx10 = bx1 - bx0
    by10 = by1 - by0
    det = ax10 * by10 - ay10 * bx10
    if det == 0.0:
        return None
    else:
        t = (bx10 * (ay0 - by0) - by10 * (ax0 - bx0)) / float(det) # TODO python 3: remove float()
        x = ax0 + t * ax10
        y = ay0 + t * ay10
        return x, y




