from math import hypot, sqrt
from .bezier import arc3, chop3, inflections3, offset2, offset3, polyline2, polyline3, segments2, segments3, subdivide2, subdivide3
from .image import image
from .misc import iround, similar




class rasterizer(object):
    
    def __init__(self, width, height, kind):
        if kind not in ('g', 'ga', 'rgb', 'rgba'):
            raise ValueError('Invalid image kind.')
        self.image = image(width, height, kind).white()
        self.scanlines = [[] for i in range(height)]
        self.top, self.bottom = height, 0
        self.mx, self.my = self.x, self.y = 0.0, 0.0
        self.mnx, self.mny = self.nx, self.ny = 0, 0
        self.first = True
    
    def edge(self, x0, y0, x1, y1):
        if y0 < y1:
            direction = 1
        elif y0 > y1:
            x0, y0, x1, y1 = x1, y1, x0, y0
            direction = -1
        else:
            return
        dx = x1 - x0
        dy = y1 - y0
        ax = abs(dx)
        if y0 < 0:
            bottom = 0
            thgir = x0 + (-y0*dx + dy//2)//dy
        else:
            bottom = y0
            thgir = x0
        y1 = min(y1, self.image.height*256)
        self.top = min(self.top, bottom)
        self.bottom = max(self.bottom, y1)
        while bottom < y1:
            top = bottom
            bottom = min((top & ~255) + 256, y1)
            tfel = thgir
            thgir = x0 + ((bottom - y0)*dx + dy//2)//dy
            scanline = self.scanlines[top//256]
            if tfel//256 == thgir//256:
                r = (tfel & ~255) + 256
                width = (r - tfel) + (r - thgir)
                height = bottom - top
                area = width*height//2
                spill = 256*height - area
                scanline.append((tfel//256, area*direction))
                scanline.append((tfel//256 + 1, spill*direction))
            else:
                left, right = min(tfel, thgir), max(tfel, thgir)
                b = top
                r = left
                previous = 0
                while r < right:
                    l = r
                    r = (l & ~255) + 256
                    if r <= right:
                        width = r - l
                        if r < right:
                            t = b
                            b = top + ((r - left)*dy + ax//2)//ax
                            height = b - t
                        else:
                            height = bottom - b
                        area = width*height//2
                        spill = 256*height - area
                    else:
                        r = right
                        width = r - l
                        height = bottom - b
                        spill = width*height//2
                        area = 256*height - spill
                    scanline.append((l//256, (area + previous)*direction))
                    previous = spill
                scanline.append(((right + 255)//256, previous*direction))
    
    def bezier2(self, x0, y0, x1, y1, x2, y2):
        steps = segments2(x0, y0, x1, y1, x2, y2, 0.25*256.0)
        if steps <= 1:
            if steps == 1:
                self.edge(x0, y0, x2, y2)
        else:
            a, b = x2-2*x1+x0, 2*(x1-x0)
            d, e = y2-2*y1+y0, 2*(y1-y0)
            m = steps**2
            x, dx, ddx = x0*m, a+b*steps, 2*a
            y, dy, ddy = y0*m, d+e*steps, 2*d
            while steps > 0:
                x += dx
                y += dy
                dx += ddx
                dy += ddy
                x1, y1 = (x+m//2)//m, (y+m//2)//m
                self.edge(x0, y0, x1, y1)
                x0, y0 = x1, y1
                steps -= 1
    
    def bezier3(self, x0, y0, x1, y1, x2, y2, x3, y3):
        steps = segments3(x0, y0, x1, y1, x2, y2, x3, y3, 0.25*256.0)
        if steps <= 1:
            if steps == 1:
                self.edge(x0, y0, x3, y3)
        else:
            a, b, c = x3-3*(x2-x1)-x0, 3*(x2-2*x1+x0), 3*(x1-x0)
            e, f, g = y3-3*(y2-y1)-y0, 3*(y2-2*y1+y0), 3*(y1-y0)
            m = steps**3
            x, dx, ddx, dddx = x0*m, a+b*steps+c*steps**2, 6*a+2*b*steps, 6*a
            y, dy, ddy, dddy = y0*m, e+f*steps+g*steps**2, 6*e+2*f*steps, 6*e
            while steps > 0:
                x += dx
                y += dy
                dx += ddx
                dy += ddy
                ddx += dddx
                ddy += dddy
                x1, y1 = (x+m//2)//m, (y+m//2)//m
                self.edge(x0, y0, x1, y1)
                x0, y0 = x1, y1
                steps -= 1
    
    def arc3(self, x, y, x0, y0, x3, y3):
        x0, y0, x1, y1, x2, y2, x3, y3 = arc3(x, y, x0, y0, x3, y3)
        x1, y1 = iround(x1), iround(y1)
        x2, y2 = iround(x2), iround(y2)
        self.bezier3(x0, y0, x1, y1, x2, y2, x3, y3)
    
    def moveto(self, x, y):
        self.mx, self.my = self.x, self.y = x, y
    
    def lineto(self, x, y):
        x0, y0 = self.x, self.y
        x1, y1 = self.x, self.y = x, y
        x0, y0 = iround(x0*256.0), iround(y0*256.0)
        x1, y1 = iround(x1*256.0), iround(y1*256.0)
        self.edge(x0, y0, x1, y1)
    
    def quadto(self, x1, y1, x, y):
        x0, y0 = self.x, self.y
        x2, y2 = self.x, self.y = x, y
        x0, y0 = iround(x0*256.0), iround(y0*256.0)
        x1, y1 = iround(x1*256.0), iround(y1*256.0)
        x2, y2 = iround(x2*256.0), iround(y2*256.0)
        self.bezier2(x0, y0, x1, y1, x2, y2)
    
    def curveto(self, x1, y1, x2, y2, x, y):
        x0, y0 = self.x, self.y
        x3, y3 = self.x, self.y = x, y
        x0, y0 = iround(x0*256.0), iround(y0*256.0)
        x1, y1 = iround(x1*256.0), iround(y1*256.0)
        x2, y2 = iround(x2*256.0), iround(y2*256.0)
        x3, y3 = iround(x3*256.0), iround(y3*256.0)
        self.bezier3(x0, y0, x1, y1, x2, y2, x3, y3)
    
    def closepath(self):
        x0, y0 = self.x, self.y
        x1, y1 = self.mx, self.my
        if x0 != x1 or y0 != y1:
            self.lineto(x1, y1)
    
    def strokemoveto(self, x, y, distance, join, limit):
        self.mx, self.my = self.x, self.y = x, y
        self.first = True
    
    def strokelineto(self, x, y, distance, join, limit):
        x0, y0 = self.x, self.y
        x1, y1 = x, y
        if x0 == x1 and y0 == y1:
            return
        self.x, self.y = x, y
        nx, ny = y1-y0, x0-x1
        n = hypot(nx, ny)
        nx, ny = nx/n*distance, ny/n*distance
        x0, y0 = iround(x0*256.0), iround(y0*256.0)
        x1, y1 = iround(x1*256.0), iround(y1*256.0)
        nx, ny = iround(nx*256.0), iround(ny*256.0)
        if self.first:
            self.mnx, self.mny = nx, ny
            self.first = False
        else:
            self.join(x0, y0, nx, ny, join, limit)
        self.edge(x0+nx, y0+ny, x1+nx, y1+ny)
        self.edge(x1-nx, y1-ny, x0-nx, y0-ny)
        self.nx, self.ny = nx, ny
    
    def strokequadto(self, x1, y1, x, y, distance, join, limit):
        x0, y0 = self.x, self.y
        x2, y2 = x, y
        if similar(x0, x1) and similar(y0, y1) or similar(x1, x2) and similar(y1, y2):
            self.strokelineto(x2, y2, distance, join, limit)
            return
        if similar((x0-x1)*(y2-y1), (y0-y1)*(x2-x1)):
            for x, y in polyline2(x0, y0, x1, y1, x2, y2):
                self.strokelineto(x, y, distance, join, limit)
                join = 'round'
            self.strokelineto(x2, y2, distance, join, limit)
            return
        self.x, self.y = x, y
        for x0, y0, x1, y1, x2, y2 in subdivide2(x0, y0, x1, y1, x2, y2):
            ax, ay, bx, by, cx, cy = offset2(x0, y0, x1, y1, x2, y2, distance)
            dx, dy, ex, ey, fx, fy = offset2(x2, y2, x1, y1, x0, y0, distance)
            x0, y0 = iround(x0*256.0), iround(y0*256.0)
            x2, y2 = iround(x2*256.0), iround(y2*256.0)
            ax, ay = iround(ax*256.0), iround(ay*256.0)
            bx, by = iround(bx*256.0), iround(by*256.0)
            cx, cy = iround(cx*256.0), iround(cy*256.0)
            ex, ey = iround(ex*256.0), iround(ey*256.0)
            nx, ny = ax-x0, ay-y0
            if self.first:
                self.mnx, self.mny = nx, ny
                self.first = False
            else:
                self.join(x0, y0, nx, ny, join, limit)
            fx, fy = x0-nx, y0-ny
            nx, ny = cx-x2, cy-y2
            dx, dy = x2-nx, y2-ny
            self.bezier2(ax, ay, bx, by, cx, cy)
            self.bezier2(dx, dy, ex, ey, fx, fy)
            self.nx, self.ny = nx, ny
    
    def strokecurveto(self, x1, y1, x2, y2, x, y, distance, join, limit):
        x0, y0 = self.x, self.y
        x3, y3 = x, y
        if similar(x0, x1) and similar(y0, y1) and similar(x1, y2) and similar(y1, y2):
            self.strokelineto(x3, y3, distance, join, limit)
            return
        if similar(x1, x2) and similar(y1, y2) and similar(x2, x3) and similar(y2, y3):
            self.strokelineto(x3, y3, distance, join, limit)
            return
        if similar((x0-x1)*(y2-y1), (y0-y1)*(x2-x1)) and similar((x3-x2)*(y1-y2), (y3-y2)*(x1-x2)):
            for x, y in polyline3(x0, y0, x1, y1, x2, y2, x3, y3):
                self.strokelineto(x, y, distance, join, limit)
                join = 'round'
            self.strokelineto(x3, y3, distance, join, limit)
            return
        self.x, self.y = x, y
        ts = []
        for t in inflections3(x0, y0, x1, y1, x2, y2, x3, y3):
            if similar(t, 0.0):
                continue
            if similar(t, 1.0):
                continue
            if 0.0 < t < 1.0:
                ts.append(t)
        segments = []
        left = None
        for right in chop3(x0, y0, x1, y1, x2, y2, x3, y3, ts):
            if left:
                x0, y0, x1, y1, x2, y2, x3, y3 = left
                x4, y4, x5, y5, x6, y6, x7, y7 = right
                if similar(x0, x1) and similar(y0, y1):
                    if similar(x1, x2) and similar(y1, y2):
                        if similar(x2, x3) and similar(y2, y3):
                            left = x0, y0, x5, y5, x6, y6, x7, y7
                            continue
                if similar(x4, x5) and similar(y4, y5):
                    if similar(x5, x6) and similar(y5, y6):
                        if similar(x6, x7) and similar(y6, y7):
                            left = x0, y0, x1, y1, x2, y2, x7, y7
                            continue
                segments.append(left)
            left = right
        segments.append(left)
        for x0, y0, x1, y1, x2, y2, x3, y3 in segments:
            for x0, y0, x1, y1, x2, y2, x3, y3 in subdivide3(x0, y0, x1, y1, x2, y2, x3, y3):
                if similar(x0, x1) and similar(y0, y1):
                    ax, ay, cx, cy, dx, dy = offset2(x0, y0, x2, y2, x3, y3, distance)
                    ex, ey, fx, fy, hx, hy = offset2(x3, y3, x2, y2, x0, y0, distance)
                    bx, by = ax, ay
                    gx, gy = hx, hy
                elif similar(x2, x3) and similar(y2, y3):
                    ax, ay, bx, by, dx, dy = offset2(x0, y0, x1, y1, x3, y3, distance)
                    ex, ey, gx, gy, hx, hy = offset2(x3, y3, x1, y1, x0, y0, distance)
                    cx, cy = dx, dy
                    fx, fy = ex, ey
                else:
                    ax, ay, bx, by, cx, cy, dx, dy = offset3(x0, y0, x1, y1, x2, y2, x3, y3, distance)
                    ex, ey, fx, fy, gx, gy, hx, hy = offset3(x3, y3, x2, y2, x1, y1, x0, y0, distance)
                x0, y0 = iround(x0*256.0), iround(y0*256.0)
                x3, y3 = iround(x3*256.0), iround(y3*256.0)
                ax, ay = iround(ax*256.0), iround(ay*256.0)
                bx, by = iround(bx*256.0), iround(by*256.0)
                cx, cy = iround(cx*256.0), iround(cy*256.0)
                dx, dy = iround(dx*256.0), iround(dy*256.0)
                fx, fy = iround(fx*256.0), iround(fy*256.0)
                gx, gy = iround(gx*256.0), iround(gy*256.0)
                nx, ny = ax-x0, ay-y0
                if self.first:
                    self.mnx, self.mny = nx, ny
                    self.first = False
                else:
                    self.join(x0, y0, nx, ny, join, limit)
                hx, hy = x0-nx, y0-ny
                nx, ny = dx-x3, dy-y3
                ex, ey = x3-nx, y3-ny
                self.bezier3(ax, ay, bx, by, cx, cy, dx, dy)
                self.bezier3(ex, ey, fx, fy, gx, gy, hx, hy)
                self.nx, self.ny = nx, ny
            join = 'round'
    
    def strokeclosepath(self, distance, join, limit):
        x0, y0 = self.x, self.y
        x1, y1 = self.mx, self.my
        if x0 != x1 or y0 != y1:
            self.strokelineto(x1, y1, distance, join, limit)
        x1, y1 = iround(x1*256.0), iround(y1*256.0)
        self.join(x1, y1, self.mnx, self.mny, join, limit)
        self.nx, self.ny = self.mnx, self.mny
    
    def cap(self, kind):
        mx, my, mnx, mny = self.mx, self.my, self.mnx, self.mny
        x, y, nx, ny = self.x, self.y, self.nx, self.ny
        mx, my = iround(mx*256.0), iround(my*256.0)
        x, y = iround(x*256.0), iround(y*256.0)
        if kind == 'butt':
            x0, y0 = mx-mnx, my-mny
            x4, y4 = mx+mnx, my+mny
            self.edge(x0, y0, x4, y4)
            x0, y0 = x+nx, y+ny
            x4, y4 = x-nx, y-ny
            self.edge(x0, y0, x4, y4)
        elif kind == 'round':
            k = 72389 # 4.0/3.0*(sqrt(2.0) - 1.0)*131072.0
            x0, y0 = mx-mnx, my-mny
            x4, y4 = mx+mnx, my+mny
            x2, y2 = mx+mny, my-mnx
            dx, dy = (mny*k + 65536)//131072, (-mnx*k + 65536)//131072
            self.bezier3(x0, y0, x0+dx, y0+dy, x2+dy, y2-dx, x2, y2)
            self.bezier3(x2, y2, x2-dy, y2+dx, x4+dx, y4+dy, x4, y4)
            x0, y0 = x+nx, y+ny
            x4, y4 = x-nx, y-ny
            x2, y2 = x-ny, y+nx
            dx, dy = (ny*k + 65536)//131072, (-nx*k + 65536)//131072
            self.bezier3(x0, y0, x0-dx, y0-dy, x2-dy, y2+dx, x2, y2)
            self.bezier3(x2, y2, x2+dy, y2-dx, x4-dx, y4-dy, x4, y4)
        else: # square
            x0, y0 = mx-mnx, my-mny
            x1, y1 = x0+mny, y0-mnx
            x4, y4 = mx+mnx, my+mny
            x3, y3 = x4+mny, y4-mnx
            self.edge(x0, y0, x1, y1)
            self.edge(x1, y1, x3, y3)
            self.edge(x3, y3, x4, y4)
            x0, y0 = x+nx, y+ny
            x1, y1 = x0-ny, y0+nx
            x4, y4 = x-nx, y-ny
            x3, y3 = x4-ny, y4+nx
            self.edge(x0, y0, x1, y1)
            self.edge(x1, y1, x3, y3)
            self.edge(x3, y3, x4, y4)
    
    def join(self, x, y, nx, ny, kind, limit):
        px, py = self.nx, self.ny
        if px == nx and py == ny:
            return
        if kind == 'miter':
            d = px*ny - py*nx
            if d == 0:
                self.edge(x+px, y+py, x+nx, y+ny)
            else:
                if d < 0:
                    px, py, nx, ny, d = -nx, -ny, -px, -py, -d
                m = px*(py-px) - py*(px+py)
                n = nx*(ny-nx) - ny*(nx+ny)
                rx = (py*n - m*ny + d//2)//d
                ry = (m*nx - px*n + d//2)//d
                if rx**2 + ry**2 < limit:
                    self.edge(x+px, y+py, x+rx, y+ry)
                    self.edge(x+rx, y+ry, x+nx, y+ny)
                else:
                    self.edge(x+px, y+py, x+nx, y+ny)
        elif kind == 'round':
            d = px*ny - py*nx
            if d < 0:
                px, py, nx, ny, d = -nx, -ny, -px, -py, -d
            a = (px - nx)**2 + (py - ny)**2
            b = (px - ny)**2 + (py + nx)**2
            c = (px + nx)**2 + (py + ny)**2
            if a <= b:
                m = px*(py-px) - py*(px+py)
                n = nx*(ny-nx) - ny*(nx+ny)
                rx = (py*n - m*ny + d//2)//d
                ry = (m*nx - px*n + d//2)//d
                self.bezier2(x+px, y+py, x+rx, y+ry, x+nx, y+ny)
            elif a <= c:
                self.arc3(x, y, x+px, y+py, x+nx, y+ny)
            else:
                u = px**2 + py**2
                v = px*nx + py*ny
                k = sqrt(u/(2.0*(u - v)))
                x3, y3 = x+iround((-py+ny)*k), y+iround((px-nx)*k)
                self.arc3(x, y, x+px, y+py, x3, y3)
                self.arc3(x, y, x3, y3, x+nx, y+ny)
        else: # bevel
            self.edge(x+px, y+py, x+nx, y+ny)
        self.edge(x-nx, y-ny, x-px, y-py)
    
    def rasterize(self, c0=0, c1=0, c2=0, c3=0):
        w, n, data = self.image.width, self.image.n, self.image.data
        top, bottom = self.top//256, (self.bottom + 255)//256
        for y in range(top, bottom):
            scanline = self.scanlines[y]
            scanline.sort()
            offset = y*w
            coverage = 0
            for x, area in scanline:
                if coverage == 0:
                    x = max(0, x)
                    i = (offset + x)*n
                else:
                    x = min(x, w)
                    j = (offset + x)*n
                    alpha = (min(abs(coverage), 65536)*255 + 32768)//65536
                    while i < j:
                        if n == 1:
                            v = 255 - alpha
                            data[i] = (c0*alpha + data[i]*v + 127)//255
                        elif n == 2:
                            u = (c1*alpha + 127)//255
                            v = (data[i+1]*(255 - u) + 127)//255
                            data[i] = (c0*u + data[i]*v + 127)//255
                            data[i+1] = u + v
                        elif n == 3:
                            v = 255 - alpha
                            data[i] = (c0*alpha + data[i]*v + 127)//255
                            data[i+1] = (c1*alpha + data[i+1]*v + 127)//255
                            data[i+2] = (c2*alpha + data[i+2]*v + 127)//255
                        else: # 4
                            u = (c3*alpha + 127)//255
                            v = (data[i+3]*(255 - u) + 127)//255
                            data[i] = (c0*u + data[i]*v + 127)//255
                            data[i+1] = (c1*u + data[i+1]*v + 127)//255
                            data[i+2] = (c2*u + data[i+2]*v + 127)//255
                            data[i+3] = u + v
                        i += n
                coverage -= area
            scanline.clear()
        self.top, self.bottom = self.image.height, 0
        return self.image




