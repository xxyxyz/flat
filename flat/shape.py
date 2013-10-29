
from math import acos, ceil, cos, hypot, pi, sqrt
from cmath import exp

from .color import spot, devicen, overprint, _default_color
from .command import moveto, lineto, quadto, curveto, closepath
from .geometry import elevate2, intersect11, offset1, offset2, reduce3
from .pdfobjects import boolean, number
from .svgreader import parsepath
from .utils import dump, equal, memoize, scale




class shape(object):
    
    __slots__ = ('strokecolor', 'fillcolor', 'strokewidth', 'strokecap',
        'strokejoin', 'miterlimit')
    
    def __init__(self):
        self.strokecolor = _default_color
        self.fillcolor = None
        self.strokewidth = 1.0
        self.strokecap = 'butt'
        self.strokejoin = 'miter'
        self.miterlimit = 4.0
    
    def stroke(self, color):
        self.strokecolor = color
        return self
    
    def fill(self, color):
        self.fillcolor = color
        return self
    
    def nostroke(self):
        self.strokecolor = None
        return self
    
    def nofill(self):
        self.fillcolor = None
        return self
    
    def width(self, value, units='pt'):
        self.strokewidth = value * scale(units)
        return self
    
    def cap(self, kind):
        assert kind in ('butt', 'round', 'square'), 'Invalid stroke cap.'
        self.strokecap = kind
        return self
    
    def join(self, kind):
        assert kind in ('miter', 'round', 'bevel'), 'Invalid stroke join.'
        self.strokejoin = kind
        return self
    
    def limit(self, value):
        assert value >= 1.0, 'Invalid miter limit.'
        self.miterlimit = value
        return self
    
    def line(self, x0, y0, x1, y1):
        return line(self, x0, y0, x1, y1)
    
    def polyline(self, *coordinates):
        return polyline(self, *coordinates)
    
    def polygon(self, *coordinates):
        return polygon(self, *coordinates)
    
    def rect(self, x, y, width, height):
        return rect(self, x, y, width, height)
    
    def circle(self, x, y, r):
        return circle(self, x, y, r)
    
    def ellipse(self, x, y, rx, ry):
        return ellipse(self, x, y, rx, ry)
    
    def path(self, *commands):
        return path(self, *commands)
    
    def pathparse(self, string):
        return path(self, *parsepath(string))




def _pdf_polyline(c, k, x, y):
    return [('%s %s m' if i == 0 else '%s %s l') % (
        dump(c[i]*k+x), dump(y-c[i+1]*k)) for i in range(0, len(c), 2)]

def _svg_polyline(c, k, x, y):
    return ' '.join([dump(c[i]*k+(y if i & 1 else x)) for i in range(len(c))])

def _commands_polyline(c):
    return [(moveto if i == 0 else lineto)(
        c[i], c[i+1]) for i in range(0, len(c), 2)]

def _pdf_ellipse(x, y, rx, ry, paint):
        k = 4.0/3.0 * (sqrt(2.0) - 1.0)
        dx = rx * k
        dy = ry * k
        x_, y_ = dump(x), dump(y)
        x_add_dx, x_sub_dx = dump(x+dx), dump(x-dx)
        y_add_dy, y_sub_dy = dump(y+dy), dump(y-dy)
        x_add_rx, x_sub_rx = dump(x+rx), dump(x-rx)
        y_add_ry, y_sub_ry = dump(y+ry), dump(y-ry)
        return (
            '%s %s m '
            '%s %s %s %s %s %s c '
            '%s %s %s %s %s %s c '
            '%s %s %s %s %s %s c '
            '%s %s %s %s %s %s c h '
            '%s') % (
            x_add_rx, y_,
            x_add_rx, y_sub_dy, x_add_dx, y_sub_ry, x_, y_sub_ry,
            x_sub_dx, y_sub_ry, x_sub_rx, y_sub_dy, x_sub_rx, y_,
            x_sub_rx, y_add_dy, x_sub_dx, y_add_ry, x_, y_add_ry,
            x_add_dx, y_add_ry, x_add_rx, y_add_dy, x_add_rx, y_,
            paint)

def _commands_ellipse(x, y, rx, ry):
        k = 4.0/3.0 * (sqrt(2.0) - 1.0)
        dx = rx * k
        dy = ry * k
        return (
            moveto(x+rx, y),
            curveto(x+rx, y-dy, x+dx, y-ry, x, y-ry),
            curveto(x-dx, y-ry, x-rx, y-dy, x-rx, y),
            curveto(x-rx, y+dy, x-dx, y+ry, x, y+ry),
            curveto(x+dx, y+ry, x+rx, y+dy, x+rx, y), closepath)




class line(object):
    
    __slots__ = 'shape', 'x0', 'y0', 'x1', 'y1'
    
    def __init__(self, shape, x0, y0, x1, y1):
        self.shape = shape
        self.x0, self.y0 = x0, y0
        self.x1, self.y1 = x1, y1
    
    def pdf(self, k, x, y, paint):
        return '%s %s m %s %s l %s' % (
            dump(self.x0*k+x), dump(y-self.y0*k),
            dump(self.x1*k+x), dump(y-self.y1*k),
            paint)
    
    def svg(self, k, x, y, attributes):
        return '<line x1="%s" y1="%s" x2="%s" y2="%s"%s />' % (
            dump(self.x0*k+x), dump(self.y0*k+y),
            dump(self.x1*k+x), dump(self.y1*k+y),
            attributes)
    
    @property
    def commands(self):
        return (
            moveto(self.x0, self.y0),
            lineto(self.x1, self.y1))
    
    def placed(self, scale):
        return placedshape(self, scale)


class polyline(object):
    
    __slots__ = 'shape', 'coordinates',

    def __init__(self, shape, *coordinates):
        self.shape = shape
        self.coordinates = coordinates
    
    def pdf(self, k, x, y, paint):
        result = _pdf_polyline(self.coordinates, k, x, y)
        result.append(paint)
        return ' '.join(result)
        
    
    def svg(self, k, x, y, attributes):
        return '<polyline points="%s"%s />' % (
            _svg_polyline(self.coordinates, k, x, y),
            attributes)
    
    @property
    def commands(self):
        return _commands_polyline(self.coordinates)
    
    def placed(self, scale):
        return placedshape(self, scale)


class polygon(object):
    
    __slots__ = 'shape', 'coordinates'

    def __init__(self, shape, *coordinates):
        self.shape = shape
        self.coordinates = coordinates
    
    def pdf(self, k, x, y, paint):
        result = _pdf_polyline(self.coordinates, k, x, y)
        result.extend(('h', paint))
        return ' '.join(result)
    
    def svg(self, k, x, y, attributes):
        return '<polygon points="%s"%s />' % (
            _svg_polyline(self.coordinates, k, x, y),
            attributes)
    
    @property
    def commands(self):
        result = _commands_polyline(self.coordinates)
        result.append(closepath)
        return result
    
    def placed(self, scale):
        return placedshape(self, scale)


class rect(object):
    
    __slots__ = 'shape', 'x', 'y', 'width', 'height'
    
    def __init__(self, shape, x, y, width, height):
        self.shape = shape
        self.x, self.y = x, y
        self.width, self.height = width, height
    
    def pdf(self, k, x, y, paint):
        return '%s %s %s %s re %s' % (
            dump(self.x*k+x), dump(y-(self.y+self.height)*k),
            dump(self.width*k), dump(self.height*k),
            paint)
    
    def svg(self, k, x, y, attributes):
        return '<rect x="%s" y="%s" width="%s" height="%s"%s />' % (
            dump(self.x*k+x), dump(self.y*k+y),
            dump(self.width*k), dump(self.height*k),
            attributes)
    
    @property
    def commands(self):
        x, y, w, h = self.x, self.y, self.width, self.height
        return (
            moveto(x, y),
            lineto(x+w, y),
            lineto(x+w, y+h),
            lineto(x, y+h),
            closepath)
    
    def placed(self, scale):
        return placedshape(self, scale)


class circle(object):
    
    __slots__ = 'shape', 'x', 'y', 'r'
    
    def __init__(self, shape, x, y, r):
        self.shape = shape
        self.x, self.y, self.r = x, y, r
    
    def pdf(self, k, x, y, paint):
        return _pdf_ellipse(self.x*k+x, y-self.y*k, self.r*k, self.r*k, paint)
    
    def svg(self, k, x, y, attributes):
        return '<circle cx="%s" cy="%s" r="%s"%s />' % (
            dump(self.x*k+x), dump(self.y*k+y),
            dump(self.r*k),
            attributes)
    
    @property
    def commands(self):
        return _commands_ellipse(self.x, self.y, self.r, self.r)
    
    def placed(self, scale):
        return placedshape(self, scale)


class ellipse(object):
    
    __slots__ = 'shape', 'x', 'y', 'rx', 'ry'

    def __init__(self, shape, x, y, rx, ry):
        self.shape = shape
        self.x, self.y, self.rx, self.ry = x, y, rx, ry
    
    def pdf(self, k, x, y, paint):
        return _pdf_ellipse(self.x*k+x, y-self.y*k, self.rx*k, self.ry*k, paint)
    
    def svg(self, k, x, y, attributes):
        return '<ellipse cx="%s" cy="%s" rx="%s" ry="%s"%s />' % (
            dump(self.x*k+x), dump(self.y*k+y),
            dump(self.rx*k), dump(self.ry*k),
            attributes)
    
    @property
    def commands(self):
        return _commands_ellipse(self.x, self.y, self.rx, self.ry)
    
    def placed(self, scale):
        return placedshape(self, scale)


class path(object):
    
    __slots__ = 'shape', 'commands'
    
    def __init__(self, shape, *commands):
        self.shape = shape
        self.commands = commands
    
    def elevated(self):
        result = []
        mx, my = px, py = 0.0, 0.0
        for c in self.commands:
            kind = type(c)
            if kind == moveto:
                mx, my = px, py = c.x, c.y
            elif kind == lineto or kind == curveto:
                px, py = c.x, c.y
            elif kind == quadto:
                x0, y0, x1, y1, x2, y2, px, py = \
                    elevate2(px, py, c.x1, c.y1, c.x, c.y)
                c = curveto(x1, y1, x2, y2, px, py)
            else: # closepath
                px, py = mx, my
            result.append(c)
        return path(self.shape, *result)
    
    def reduced(self, scale):
        result = []
        mx, my = px, py = 0.0, 0.0
        for c in self.commands:
            kind = type(c)
            if kind == moveto:
                mx, my = px, py = c.x, c.y
            elif kind == lineto or kind == quadto:
                px, py = c.x, c.y
            elif kind == curveto:
                pieces = reduce3(px, py, c.x1, c.y1, c.x2, c.y2, c.x, c.y, scale)
                for x0, y0, x1, y1, px, py in pieces:
                    result.append(quadto(x1, y1, px, py))
                continue
            else: # closepath
                px, py = mx, my
            result.append(c)
        return path(self.shape, *result)
    
    def pdf(self, k, x, y, paint):
        result = [c.pdf(k, x, y) for c in self.commands]
        result.append(paint)
        return ' '.join(result)
        
    
    def svg(self, k, x, y, attributes):
        return '<path d="%s"%s />' % (
            ' '.join([c.svg(k, x, y) for c in self.commands]),
            attributes)
    
    def placed(self, scale):
        return placedshape(self, scale)




@memoize
def _strokefill_pdf(resources, stroke, fill, oldstroke, oldfill):
    commands, spaces, states = [], set(), set()
    
    strokeoverprint = type(stroke or oldstroke) == overprint
    filloverprint = type(fill or oldfill) == overprint
    oldstrokeoverprint = type(oldstroke) == overprint
    oldfilloverprint = type(oldfill) == overprint
    if strokeoverprint != oldstrokeoverprint or filloverprint != oldfilloverprint:
        resource = resources.state((
            ('OP', boolean, strokeoverprint),
            ('op', boolean, filloverprint),
            ('OPM', number, 1)))
        commands.append('/%s gs' % resource.name)
        states.add(resource)
    
    if type(stroke) == overprint:
        stroke = stroke.color
    if type(fill) == overprint:
        fill = fill.color
    if oldstrokeoverprint:
        oldstroke = oldstroke.color
    if oldfilloverprint:
        oldfill = oldfill.color
    
    if stroke and stroke != oldstroke:
        if type(stroke) in (spot, devicen):
            resource = resources.space(stroke)
            commands.append(stroke.pdfstroke(resource.name))
            spaces.add(resource)
        else:
            commands.append(stroke.pdfstroke())
    if fill and fill != oldfill:
        if type(fill) in (spot, devicen):
            resource = resources.space(fill)
            commands.append(fill.pdffill(resource.name))
            spaces.add(resource)
        else:
            commands.append(fill.pdffill())
    
    return ' '.join(commands), spaces, states


@memoize
def _shape_pdf(resources,
    stroke, fill, width, cap, join, limit,
    oldstroke, oldfill, oldwidth, oldcap, oldjoin, oldlimit):
    chunk, spaces, states = _strokefill_pdf(resources,
        stroke, fill, oldstroke, oldfill)
    commands = [chunk] if chunk else []
    if width != oldwidth:
        commands.append('%s w' % dump(width))
    if cap != oldcap:
        commands.append('%d J' % \
            0 if cap == 'butt' else \
            1 if cap == 'round' else 2)
    if join != oldjoin:
        commands.append('%d j' % \
            0 if join == 'miter' else \
            1 if join == 'round' else 2)
    if limit != oldlimit:
        commands.append('%s M' % dump(limit))
    chunk = ' '.join(commands)
    if chunk:
        chunk += '\n'
    if stroke:
        paint = 'B' if fill else 'S'
    else:
        paint = 'f' if fill else 'n'
    return chunk, spaces, states, stroke or oldstroke, fill or oldfill, paint




@memoize
def _shape_svg(stroke, fill, width, cap, join, limit):
    attributes = ' stroke="%s" fill="%s"' % (
        stroke.svg() if stroke else 'none',
        fill.svg() if fill else 'none')
    if width != 1.0:
        attributes += ' stroke-width="%s"' % dump(width)
    if cap != 'butt':
        attributes += ' stroke-linecap="%s"' % cap
    if join != 'miter':
        attributes += ' stroke-linejoin="%s"' % join
    elif limit != 4.0:
        attributes += ' stroke-miterlimit="%s"' % limit
    return attributes




def _rasterize_commands(rasterizer, commands, _k, _x, _y, shape, inverse):
    distance = shape.strokewidth * 0.5 * inverse
    stroke = shape.strokecolor
    fill = shape.fillcolor
    cap = \
        _cap_butt if shape.strokecap == 'butt' else \
        _cap_round if shape.strokecap == 'round' else _cap_square
    join = \
        _join_miter if shape.strokejoin == 'miter' else \
        _join_round if shape.strokejoin == 'round' else _join_bevel
    limit = shape.miterlimit
    mx, my = 0.0, 0.0
    if stroke and distance > 0.0:
        outer, inner, strokes, fills = [], [], [], []
        px, py = 0.0, 0.0
        ox, oy, ix, iy = 0.0, 0.0, 0.0, 0.0
        stack = []
        end = len(commands) - 1
        for i, c in enumerate(commands):
            stack.append(c)
            while stack:
                c = stack.pop()
                kind = type(c)
                if i == end:
                    if not stack and kind in (lineto, quadto, curveto):
                        stack.append(moveto(0.0, 0.0))
                if kind == moveto:
                    if inner:
                        a, b = cap(ox, oy, outer, ix, iy, inner)
                        _reverse_contour(inner, ix, iy)
                        strokes.append(a + outer + b + inner)
                        outer, inner = [], [] # TODO python 3: temp.clear()
                    px, py = mx, my = c.x, c.y
                elif kind == lineto:
                    x0, y0, x1, y1 = offset1(px, py, c.x, c.y, distance)
                    if outer:
                        x, y = outer[-1]
                        outer.extend(join(px, py, x, y, x0, y0, limit))
                    else:
                        ox, oy = x0, y0
                    outer.extend((None, (x1, y1)))
                    x0, y0, x1, y1 = offset1(px, py, c.x, c.y, -distance)
                    if inner:
                        x, y = inner[-1]
                        inner.extend(join(px, py, x, y, x0, y0, limit))
                    else:
                        ix, iy = x0, y0
                    inner.extend((None, (x1, y1)))
                    px, py = c.x, c.y
                elif kind == quadto:
                    pieces = offset2(px, py, c.x1, c.y1, c.x, c.y, distance, _k)
                    for x0, y0, x1, y1, x2, y2 in pieces:
                        if outer:
                            x, y = outer[-1]
                            outer.extend(join(px, py, x, y, x0, y0, limit))
                        else:
                            ox, oy = x0, y0
                        outer.extend(((x1, y1), (x2, y2)))
                    pieces = offset2(px, py, c.x1, c.y1, c.x, c.y, -distance, _k)
                    for x0, y0, x1, y1, x2, y2 in pieces:
                        if inner:
                            x, y = inner[-1]
                            inner.extend(join(px, py, x, y, x0, y0, limit))
                        else:
                            ix, iy = x0, y0
                        inner.extend(((x1, y1), (x2, y2)))
                    px, py = c.x, c.y
                elif kind == curveto:
                    pieces = reduce3(px, py, c.x1, c.y1, c.x2, c.y2, c.x, c.y, _k)
                    pieces.reverse()
                    for x0, y0, x1, y1, x2, y2 in pieces:
                        stack.append(quadto(x1, y1, x2, y2))
                    continue
                else: # closepath
                    if outer:
                        if not equal(mx, px) or not equal(my, py):
                            stack.extend((c, lineto(mx, my)))
                            continue
                        x, y = outer[-1]
                        outer.extend(join(px, py, x, y, ox, oy, limit))
                        x, y = inner[-1]
                        inner.extend(join(px, py, x, y, ix, iy, limit))
                        _reverse_contour(inner, ix, iy)
                        strokes.extend((outer, inner))
                        if fill:
                            clockwise = max(inner) < max(outer)
                            fills.append(inner if clockwise else outer)
                        outer, inner = [], []
        if fill:
            rasterizer.rasterize(fills, _k, _x, _y, fill)
        rasterizer.rasterize(strokes, _k, _x, _y, stroke)
    
    elif fill:
        temp, contours = [], []
        for c in commands:
            kind = type(c)
            if kind == moveto:
                mx, my = c.x, c.y
                temp = [] # TODO python 3: temp.clear()
            elif kind == lineto:
                temp.extend((None, (c.x, c.y)))
            elif kind == quadto:
                temp.extend(((c.x1, c.y1), (c.x, c.y)))
            elif kind == curveto:
                x, y = temp[-1] if temp else (mx, my)
                for x0, y0, x1, y1, x2, y2 in reduce3(
                    x, y, c.x1, c.y1, c.x2, c.y2, c.x, c.y, _k):
                    temp.extend(((x1, y1), (x2, y2)))
            else: # closepath
                if temp:
                    x, y = temp[-1]
                    if not equal(mx, x) or not equal(my, y):
                        temp.extend((None, (mx, my)))
                    contours.append(temp)
                    temp = []
        rasterizer.rasterize(contours, _k, _x, _y, fill)

def _reverse_contour(contour, x, y):
    contour.pop()
    contour.reverse()
    contour.append((x, y))

def _cap_butt(ox, oy, outer, ix, iy, inner):
    a = [None, (ox, oy)]
    b = [None, inner[-1]]
    return a, b

def _cap_round(ox, oy, outer, ix, iy, inner):
    k = sqrt(2.0) - 1.0
    px, py = outer[-1]
    jx, jy = inner[-1]
    dx, dy = (oy-iy)*0.5, (ix-ox)*0.5
    kx, ky = dx*k, dy*k
    cx, cy = ox+dy, oy-dx
    ex, ey = cx+dx, cy+dy
    x0, y0 = ix+kx, iy+ky
    x1, y1 = ex+ky, ey-kx
    x2, y2 = ex-ky, ey+kx
    x3, y3 = ox+kx, oy+ky
    a = [
        (x0, y0), ((x0+x1)*0.5, (y0+y1)*0.5), (x1, y1), (ex, ey),
        (x2, y2), ((x2+x3)*0.5, (y2+y3)*0.5), (x3, y3), (ox, oy)]
    dx, dy = (jy-py)*0.5, (px-jx)*0.5
    kx, ky = dx*k, dy*k
    cx, cy = jx+dy, jy-dx
    ex, ey = cx+dx, cy+dy
    x0, y0 = px+kx, py+ky
    x1, y1 = ex+ky, ey-kx
    x2, y2 = ex-ky, ey+kx
    x3, y3 = jx+kx, jy+ky
    b = [
        (x0, y0), ((x0+x1)*0.5, (y0+y1)*0.5), (x1, y1), (ex, ey),
        (x2, y2), ((x2+x3)*0.5, (y2+y3)*0.5), (x3, y3), inner[-1]]
    return a, b

def _cap_square(ox, oy, outer, ix, iy, inner):
    px, py = outer[-1]
    jx, jy = inner[-1]
    dx, dy = (oy-iy)*0.5, (ix-ox)*0.5
    a = [None, (ix+dx, iy+dy), None, (ox+dx, oy+dy), None, (ox, oy)]
    dx, dy = (jy-py)*0.5, (px-jx)*0.5
    b = [None, (px+dx, py+dy), None, (jx+dx, jy+dy), None, inner[-1]]
    return a, b

def _join_miter(cx, cy, ax, ay, bx, by, miterlimit):
    if equal(ax, bx) and equal(ay, by):
        return ()
    p = intersect11(
        ax, ay, ax+(cy-ay), ay-(cx-ax),
        bx, by, bx+(cy-by), by-(cx-bx))
    if p:
        x, y = p
        if hypot(x-ax, y-ay) / (hypot(bx-ax, by-ay) * 0.5) < miterlimit:
            return None, (x, y), None, (bx, by)
    return _join_bevel(cx, cy, ax, ay, bx, by, miterlimit)

def _join_round(cx, cy, ax, ay, bx, by, miterlimit):
    if equal(ax, bx) and equal(ay, by):
        return ()
    a = hypot(ax-cx, ay-cy)
    c = hypot(bx-ax, by-ay)
    angle = acos(1.0 - c*c / (2.0*a*a))
    if (ax-cx)*(by-cy) < (ay-cy)*(bx-cx):
        angle = -angle
    n = ceil(4.0 * abs(angle) / pi)
    omega = exp(complex(0, angle / n))
    u = complex(ax-cx, ay-cy)
    ratio = cos(0.5 * angle / n)
    v = complex((ax-cx)/ratio, (ay-cy)/ratio)
    v *= exp(complex(0, 0.5 * angle / n))
    result = []
    for i in range(int(n)):
        u *= omega
        result.extend(((v.real+cx, v.imag+cy), (u.real+cx, u.imag+cy)))
        v *= omega
    return result

def _join_bevel(cx, cy, ax, ay, bx, by, miterlimit):
    if equal(ax, bx) and equal(ay, by):
        return ()
    return None, (bx, by)




class placedshape(object):
    
    __slots__ = 'item', 'k', 'x', 'y'
    
    def __init__(self, item, k):
        self.item = item
        self.k = k
        self.x, self.y = 0.0, 0.0
    
    def position(self, x, y):
        self.x, self.y = x*self.k, y*self.k
        return self
    
    def pdf(self, pre, resources, spaces, fonts, images, states, height):
        new = self.item.shape
        old = pre.shape
        pre.shape = new
        chunk, cs, gs, pre.strokecolor, pre.fillcolor, paint = _shape_pdf(
            resources,
            new.strokecolor, new.fillcolor,
                new.strokewidth, new.strokecap, new.strokejoin, new.miterlimit,
            pre.strokecolor, pre.fillcolor,
                old.strokewidth, old.strokecap, old.strokejoin, old.miterlimit)
        spaces |= cs
        states |= gs
        return chunk + self.item.pdf(self.k, self.x, height-self.y, paint)
    
    def svg(self):
        s = self.item.shape
        attributes = _shape_svg(s.strokecolor, s.fillcolor,
            s.strokewidth, s.strokecap, s.strokejoin, s.miterlimit)
        return self.item.svg(self.k, self.x, self.y, attributes)
    
    def rasterize(self, rasterizer, k, x, y):
        _rasterize_commands(rasterizer, self.item.commands,
            self.k*k, self.x*k+x, self.y*k+y, self.item.shape, 1.0/self.k)




