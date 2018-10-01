from random import random
from .bezier import elevate2
from .command import moveto, lineto, quadto, curveto, closepath




def elevated(commands):
    mx, my = x, y = 0.0, 0.0
    for c in commands:
        if isinstance(c, moveto):
            mx, my = x, y = c.x, c.y
        elif isinstance(c, quadto):
            x0, y0, x1, y1, x2, y2, x, y = elevate2(x, y, c.x1, c.y1, c.x, c.y)
            c = curveto(x1, y1, x2, y2, x, y)
        elif c == closepath:
            x, y = mx, my
        else:
            x, y = c.x, c.y
        yield c




class _polygon_vertex(object):
    
    __slots__ = 'x', 'y', 'prev', 'next', 'neighbour', 'alpha', 'entry', 'visited'
    
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.prev = self.next = self
        self.neighbour = None
        self.alpha = 0.0
        self.entry = False
        self.visited = False
    
    def vertices(self):
        v = self
        yield v
        v = v.next
        while v != self:
            yield v
            v = v.next
    
    def commands(self):
        v = self
        yield moveto(v.x, v.y)
        v = v.next
        while v != self:
            yield lineto(v.x, v.y)
            v = v.next
        yield closepath
    
    def insert(self, other):
        v, w = self.next, other
        while 0.0 < v.alpha < w.alpha:
            v = v.next
        w.prev, w.next = v.prev, v
        v.prev.next = v.prev = w
    
    def intersect(self, other):
        v0, v1 = self, self.next
        w0, w1 = other, other.next
        while v1.neighbour:
            v1 = v1.next
        while w1.neighbour:
            w1 = w1.next
        x0, y0, x1, y1 = v0.x, v0.y, v1.x, v1.y
        x2, y2, x3, y3 = w0.x, w0.y, w1.x, w1.y
        d = (x0 - x1)*(y2 - y3) - (x2 - x3)*(y0 - y1)
        if d == 0.0:
            return None
        r = ((x0 - x2)*(y2 - y3) - (x2 - x3)*(y0 - y2))/d
        if r < 0.0 or r > 1.0:
            return None
        s = ((x1 - x0)*(y0 - y2) - (x0 - x2)*(y1 - y0))/d
        if s < 0.0 or s > 1.0:
            return None
        x, y = x0+(x1-x0)*r, y0+(y1-y0)*r
        v = _polygon_vertex(x, y)
        w = _polygon_vertex(x, y)
        v.alpha = r
        w.alpha = s
        v.neighbour = w
        w.neighbour = v
        v0.insert(v)
        w0.insert(w)
    
    def inside(self, polygon):
        # Ref.: Hormann, K., Alexander, A. (2001). The point in polygon problem for arbitrary polygons.
        p, r = polygon, self
        if p.x == r.x and p.y == r.y:
            return True
        inside = False
        for p in polygon.vertices():
            q = p.next
            if q.y == r.y:
                if q.x == r.x:
                    return True
                if p.y == r.y and (q.x > r.x) == (p.x < r.x):
                    return True
            if (p.y < r.y) != (q.y < r.y):
                if p.x >= r.x:
                    if q.x > r.x:
                        inside = not inside
                    else:
                        d = (p.x - r.x)*(q.y - r.y) - (q.x - r.x)*(p.y - r.y)
                        if d == 0:
                            return True
                        if (d > 0) == (q.y > p.y):
                            inside = not inside
                else:
                    if q.x > r.x:
                        d = (p.x - r.x)*(q.y - r.y) - (q.x - r.x)*(p.y - r.y)
                        if d == 0:
                            return True
                        if (d > 0) == (q.y > p.y):
                            inside = not inside
        return inside

def _make_polygon(commands, perturbation):
    v = None
    for c in commands:
        if c == closepath:
            return v
        x = c.x + (random()*2.0 - 1.0)*perturbation
        y = c.y + (random()*2.0 - 1.0)*perturbation
        if isinstance(c, moveto):
            v = _polygon_vertex(x, y)
        elif isinstance(c, lineto):
            if not v:
                raise ValueError('Missing `moveto` command.')
            w = _polygon_vertex(x, y)
            w.prev, w.next = v.prev, v
            v.prev.next = v.prev = w
        else:
            raise NotImplemented('Curved edges not supported.')

def _clip_polygons(subject, clipper, operation, se, ce, perturbation):
    # Ref.: Greiner, G., Hormann, K. (1998). Efficient clipping of arbitrary polygons.
    subject = _make_polygon(subject, perturbation)
    clipper = _make_polygon(clipper, perturbation)
    for s in subject.vertices():
        if not s.neighbour:
            for c in clipper.vertices():
                if not c.neighbour:
                    s.intersect(c)
    se ^= subject.inside(clipper)
    for s in subject.vertices():
        if s.neighbour:
            s.entry = se
            se = not se
    ce ^= clipper.inside(subject)
    for c in clipper.vertices():
        if c.neighbour:
            c.entry = ce
            ce = not ce
    result = []
    for v in subject.vertices():
        if v.neighbour and not v.visited:
            result.append(moveto(v.x, v.y))
            while True:
                v.visited = v.neighbour.visited = True
                if v.entry:
                    while True:
                        v = v.next
                        result.append(lineto(v.x, v.y))
                        if v.neighbour:
                            break
                else:
                    while True:
                        v = v.prev
                        result.append(lineto(v.x, v.y))
                        if v.neighbour:
                            break
                v = v.neighbour
                if v.visited:
                    break
            result.append(closepath)
    if not result:
        if operation == 'intersection':
            if se ^ ce:
                result.extend(subject.commands())
                result.extend(clipper.commands())
        else: # union, difference
            if not se:
                result.extend(subject.commands())
            if not ce:
                result.extend(clipper.commands())
    return result

def union(subject, clipper, perturbation=0.0):
    return _clip_polygons(subject, clipper, 'union', False, False, perturbation)

def intersection(subject, clipper, perturbation=0.0):
    return _clip_polygons(subject, clipper, 'intersection', True, True, perturbation)

def difference(subject, clipper, perturbation=0.0):
    return _clip_polygons(subject, clipper, 'difference', False, True, perturbation)




