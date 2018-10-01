from math import sqrt
from .color import gray, spot, overprint
from .command import moveto, lineto, curveto, closepath
from .misc import dump, scale
from .path import elevated




class style(object):
    
    __slots__ = 'stroke', 'fill', 'width', 'cap', 'join', 'limit'
    
    def __init__(self):
        self.stroke = gray(0)
        self.fill = None
        self.width = 1.0
        self.cap = 'butt'
        self.join = 'miter'
        self.limit = 10.0
    
    def pdf(self, state, resources):
        fragments = []
        s, ss = self.stroke, state.stroke
        f, ff = self.fill, state.fill
        so, sso = isinstance(s, overprint), isinstance(ss, overprint)
        fo, ffo = isinstance(f, overprint), isinstance(ff, overprint)
        if s and so != sso or f and fo != ffo:
            resource = resources.overprint(so, fo)
            fragments.append(b'/%s gs' % resource.name)
        if so:
            s = s.color
        if fo:
            f = f.color
        if sso:
            ss = ss.color
        if ffo:
            ff = ff.color
        if s and s != ss:
            if isinstance(s, spot):
                resource = resources.space(s)
                fragments.append(s.pdfstroke(resource.name))
            else:
                fragments.append(s.pdfstroke())
            state.stroke = s
        if f and f != ff:
            if isinstance(f, spot):
                resource = resources.space(f)
                fragments.append(f.pdffill(resource.name))
            else:
                fragments.append(f.pdffill())
            state.fill = f
        if self.width != state.width:
            fragments.append(b'%s w' % dump(self.width))
            state.width = self.width
        if self.cap != state.cap:
            fragments.append(b'%d J' % (
                0 if self.cap == 'butt' else
                1 if self.cap == 'round' else 2))
            state.cap = self.cap
        if self.join != state.join:
            fragments.append(b'%d j' % (
                0 if self.join == 'miter' else
                1 if self.join == 'round' else 2))
            state.join = self.join
        if self.limit != state.limit:
            fragments.append(b'%s M' % dump(self.limit))
            state.limit = self.limit
        return b' '.join(fragments)
    
    def pdfpaint(self):
        if self.stroke:
            return b'B' if self.fill else b'S'
        return b'f' if self.fill else b'n'
    
    def svg(self):
        if self.fill:
            attributes = [b'fill="%s"' % self.fill.svg()]
        else:
            attributes = [b'fill="none"']
        if self.stroke:
            attributes.append(b'stroke="%s"' % self.stroke.svg())
            if self.width != 1.0:
                attributes.append(b'stroke-width="%s"' % dump(self.width))
            if self.cap != 'butt':
                attributes.append(b'stroke-linecap="%s"' % (
                    b'round' if self.cap == 'round' else b'square'))
            if self.join != 'miter':
                attributes.append(b'stroke-linejoin="%s"' % (
                    b'round' if self.join == 'round' else b'bevel'))
            elif self.limit != 4.0:
                attributes.append(b'stroke-miterlimit="%s"' % dump(self.limit))
        return b' '.join(attributes)




class shape(object):
    
    __slots__ = 'style',
    
    def __init__(self):
        self.style = style()
    
    def stroke(self, color):
        self.style.stroke = color
        return self
    
    def fill(self, color):
        self.style.fill = color
        return self
    
    def nostroke(self):
        self.style.stroke = None
        return self
    
    def nofill(self):
        self.style.fill = None
        return self
    
    def width(self, value, units='pt'):
        self.style.width = value*scale(units)
        return self
    
    def cap(self, kind):
        if kind not in ('butt', 'round', 'square'):
            raise ValueError('Invalid stroke cap.')
        self.style.cap = kind
        return self
    
    def join(self, kind):
        if kind not in ('miter', 'round', 'bevel'):
            raise ValueError('Invalid stroke join.')
        self.style.join = kind
        return self
    
    def limit(self, value, units='pt'):
        if value < 1.0:
            raise ValueError('Invalid miter limit.')
        self.style.limit = value*scale(units)
        return self
    
    def line(self, x0, y0, x1, y1):
        return line(self.style, x0, y0, x1, y1)
    
    def polyline(self, coordinates):
        return polyline(self.style, coordinates)
    
    def polygon(self, coordinates):
        return polygon(self.style, coordinates)
    
    def rectangle(self, x, y, width, height):
        return rectangle(self.style, x, y, width, height)
    
    def circle(self, x, y, r):
        return circle(self.style, x, y, r)
    
    def ellipse(self, x, y, rx, ry):
        return ellipse(self.style, x, y, rx, ry)
    
    def path(self, commands):
        return path(self.style, commands)




class line(object):
    
    __slots__ = 'style', 'x0', 'y0', 'x1', 'y1'
    
    def __init__(self, style, x0, y0, x1, y1):
        self.style = style
        self.x0, self.y0 = x0, y0
        self.x1, self.y1 = x1, y1
    
    def commands(self):
        return (
            moveto(self.x0, self.y0),
            lineto(self.x1, self.y1))
    
    def pdf(self, k, x, y):
        return b'%s %s m %s %s l %s' % (
            dump(self.x0*k+x), dump(y-self.y0*k),
            dump(self.x1*k+x), dump(y-self.y1*k),
            self.style.pdfpaint())
    
    def svg(self, k, x, y):
        return b'<line x1="%s" y1="%s" x2="%s" y2="%s" %s />' % (
            dump(self.x0*k+x), dump(self.y0*k+y),
            dump(self.x1*k+x), dump(self.y1*k+y),
            self.style.svg())
    
    def placed(self, k):
        return placedshape(self, k)




class polyline(object):
    
    __slots__ = 'style', 'coordinates'
    
    def __init__(self, style, coordinates):
        self.style = style
        self.coordinates = coordinates
    
    def commands(self):
        coordinates = self.coordinates
        commands = []
        for i in range(0, len(coordinates), 2):
            cx, cy = coordinates[i], coordinates[i+1]
            if i == 0:
                commands.append(moveto(cx, cy))
            else:
                commands.append(lineto(cx, cy))
        return commands
    
    def pdf(self, k, x, y):
        coordinates = self.coordinates
        fragments = []
        for i in range(0, len(coordinates), 2):
            cx, cy = coordinates[i], coordinates[i+1]
            fragments.append(dump(cx*k + x))
            fragments.append(dump(y - cy*k))
            if i == 0:
                fragments.append(b'm')
            else:
                fragments.append(b'l')
        fragments.append(self.style.pdfpaint())
        return b' '.join(fragments)
    
    def svg(self, k, x, y):
        fragments = []
        for c in self.coordinates:
            fragments.append(dump(c*k + x))
            x, y = y, x
        return b'<polyline points="%s" %s />' % (
            b' '.join(fragments), self.style.svg())
    
    def placed(self, k):
        return placedshape(self, k)




class polygon(object):
    
    __slots__ = 'style', 'coordinates'
    
    def __init__(self, style, coordinates):
        self.style = style
        self.coordinates = coordinates
    
    def commands(self):
        coordinates = self.coordinates
        commands = []
        for i in range(0, len(coordinates), 2):
            cx, cy = coordinates[i], coordinates[i+1]
            if i == 0:
                commands.append(moveto(cx, cy))
            else:
                commands.append(lineto(cx, cy))
        commands.append(closepath)
        return commands
    
    def pdf(self, k, x, y):
        coordinates = self.coordinates
        fragments = []
        for i in range(0, len(coordinates), 2):
            cx, cy = coordinates[i], coordinates[i+1]
            fragments.append(dump(cx*k + x))
            fragments.append(dump(y - cy*k))
            if i == 0:
                fragments.append(b'm')
            else:
                fragments.append(b'l')
        fragments.append(b'h')
        fragments.append(self.style.pdfpaint())
        return b' '.join(fragments)
    
    def svg(self, k, x, y):
        fragments = []
        for c in self.coordinates:
            fragments.append(dump(c*k + x))
            x, y = y, x
        return b'<polygon points="%s" %s />' % (
            b' '.join(fragments), self.style.svg())
    
    def placed(self, k):
        return placedshape(self, k)




class rectangle(object):
    
    __slots__ = 'style', 'x', 'y', 'width', 'height'
    
    def __init__(self, style, x, y, width, height):
        self.style = style
        self.x, self.y = x, y
        self.width, self.height = width, height
    
    def commands(self):
        x, y = self.x, self.y
        width, height = self.width, self.height
        return (
            moveto(x, y),
            lineto(x+width, y),
            lineto(x+width, y+height),
            lineto(x, y+height),
            closepath)
    
    def pdf(self, k, x, y):
        return b'%s %s %s %s re %s' % (
            dump(self.x*k+x), dump(y-(self.y+self.height)*k),
            dump(self.width*k), dump(self.height*k),
            self.style.pdfpaint())
    
    def svg(self, k, x, y):
        return b'<rect x="%s" y="%s" width="%s" height="%s" %s />' % (
            dump(self.x*k+x), dump(self.y*k+y),
            dump(self.width*k), dump(self.height*k),
            self.style.svg())
    
    def placed(self, k):
        return placedshape(self, k)




class circle(object):
    
    __slots__ = 'style', 'x', 'y', 'r'
    
    def __init__(self, style, x, y, r):
        self.style = style
        self.x, self.y, self.r = x, y, r
    
    def commands(self):
        return ellipse(self.style, self.x, self.y, self.r, self.r).commands()
    
    def pdf(self, k, x, y):
        return ellipse(self.style, self.x, self.y, self.r, self.r).pdf(k, x, y)
    
    def svg(self, k, x, y):
        return b'<circle cx="%s" cy="%s" r="%s" %s />' % (
            dump(self.x*k+x), dump(self.y*k+y),
            dump(self.r*k),
            self.style.svg())
    
    def placed(self, k):
        return placedshape(self, k)




class ellipse(object):
    
    __slots__ = 'style', 'x', 'y', 'rx', 'ry'
    
    def __init__(self, style, x, y, rx, ry):
        self.style = style
        self.x, self.y, self.rx, self.ry = x, y, rx, ry
    
    def commands(self):
        x, y, rx, ry = self.x, self.y, self.rx, self.ry
        k = 4.0/3.0*(sqrt(2.0) - 1.0)
        dx = rx*k
        dy = ry*k
        return (
            moveto(x+rx, y),
            curveto(x+rx, y-dy, x+dx, y-ry, x, y-ry),
            curveto(x-dx, y-ry, x-rx, y-dy, x-rx, y),
            curveto(x-rx, y+dy, x-dx, y+ry, x, y+ry),
            curveto(x+dx, y+ry, x+rx, y+dy, x+rx, y),
            closepath)
    
    def pdf(self, k, x, y):
        x, y, rx, ry = self.x*k+x, y-self.y*k, self.rx*k, self.ry*k
        k = 4.0/3.0*(sqrt(2.0) - 1.0)
        dx = rx*k
        dy = ry*k
        x2, y2 = dump(x), dump(y)
        x3, x1 = dump(x+dx), dump(x-dx)
        y3, y1 = dump(y+dy), dump(y-dy)
        x4, x0 = dump(x+rx), dump(x-rx)
        y4, y0 = dump(y+ry), dump(y-ry)
        return (
            b'%s %s m '
            b'%s %s %s %s %s %s c '
            b'%s %s %s %s %s %s c '
            b'%s %s %s %s %s %s c '
            b'%s %s %s %s %s %s c '
            b'h %s') % (
            x4, y2,
            x4, y1, x3, y0, x2, y0,
            x1, y0, x0, y1, x0, y2,
            x0, y3, x1, y4, x2, y4,
            x3, y4, x4, y3, x4, y2,
            self.style.pdfpaint())
    
    def svg(self, k, x, y):
        return b'<ellipse cx="%s" cy="%s" rx="%s" ry="%s" %s />' % (
            dump(self.x*k+x), dump(self.y*k+y),
            dump(self.rx*k), dump(self.ry*k),
            self.style.svg())
    
    def placed(self, k):
        return placedshape(self, k)




class path(object):
    
    __slots__ = 'style', 'cs'
    
    def __init__(self, style, commands):
        self.style = style
        self.cs = commands
    
    def commands(self):
        return self.cs
    
    def pdf(self, k, x, y):
        fragments = [c.pdf(k, x, y) for c in elevated(self.cs)]
        fragments.append(self.style.pdfpaint())
        return b' '.join(fragments)
    
    def svg(self, k, x, y):
        return b'<path d="%s" %s />' % (
            b' '.join(c.svg(k, x, y) for c in self.cs),
            self.style.svg())
    
    def placed(self, k):
        return placedshape(self, k)




class placedshape(object):
    
    __slots__ = 'item', 'k', 'x', 'y'
    
    def __init__(self, item, k):
        self.item = item
        self.k = k
        self.x, self.y = 0.0, 0.0
    
    def position(self, x, y):
        self.x, self.y = x*self.k, y*self.k
        return self
    
    def pdf(self, height, state, resources):
        setup = self.item.style.pdf(state, resources)
        shape = self.item.pdf(self.k, self.x, height-self.y)
        if setup:
            return b'%s\n%s' % (setup, shape)
        return shape
    
    def svg(self):
        return self.item.svg(self.k, self.x, self.y)
    
    def rasterize(self, rasterizer, k, x, y):
        style, commands = self.item.style, self.item.commands()
        factor = k
        k, x, y = self.k*k, self.x*k+x, self.y*k+y
        if style.fill:
            closed = True
            for c in commands:
                if c == closepath:
                    closed = True
                elif isinstance(c, moveto):
                    if not closed:
                        rasterizer.closepath()
                    else:
                        closed = False
                c.rasterize(rasterizer, k, x, y)
            rasterizer.closepath()
            style.fill.rasterize(rasterizer)
        if style.stroke:
            distance = style.width/2.0*factor
            limit = int((style.limit*distance*256.0)**2 + 0.5)
            closed = True
            for c in commands:
                if c == closepath:
                    closed = True
                elif isinstance(c, moveto):
                    if not closed:
                        rasterizer.cap(style.cap)
                    else:
                        closed = False
                c.rasterizestroke(rasterizer, k, x, y, distance, style.join, limit)
            if not closed:
                rasterizer.cap(style.cap)
            style.stroke.rasterize(rasterizer)




