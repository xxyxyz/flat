
from base64 import b64encode
from copy import deepcopy
from itertools import izip # TODO python 3: izip -> zip
from math import ceil, exp, floor, log, pi, sin

from .png import png
from .jpeg import jpeg
from .utils import clamp, dump, equal, lazy, pascal, record, save, staircase




def _nearest(x):
    if -0.5 <= x < 0.5:
        return 1
    return 0

def _bicubic(x):
    if x < 0:
        x = -x
    if x < 1:
        return (1.25 * x - 2.25) * x * x + 1
    if x < 2:
        return ((-0.75 * x + 3.75) * x - 6) * x + 3
    return 0

def _lanczos(x):
    if x < 0:
        x = -x
    if x < 0.00001:
        return 1
    if x < 3:
        return 3 * sin(pi * x) * sin(pi * x / 3) / (pi * pi * x * x)
    return 0

def _contributions(old, new, function, size, count):
    scale = float(new) / old
    bound = old - 1
    if old > new:
        f = function
        function = lambda x: f(x * scale) * scale
        size /= scale
    result = []
    for j in range(new):
        center = (j + 0.5) / scale - 0.5
        left = int(ceil(center - size))
        right = int(floor(center + size))
        c = []
        for i in range(left, right + 1):
            pixel = (0 if i < 0 else bound if i > bound else i) * count
            weight = int(function(center - i) * (1 << 52) + 0.5)
            c.append((pixel, weight))
        result.append(tuple(c))
    return result




class image(object):
    
    @staticmethod
    def open(path):
        with open(path, 'rb') as f:
            data = f.read()
            if png.valid(data):
                source = png(data)
            elif jpeg.valid(data):
                source = jpeg(data)
            else:
                raise AssertionError('Unsupported image format.')
            return image(source.width, source.height, source.kind, source)
    
    @staticmethod
    def merge(kind, *images):
        if not images:
            return None
        a = image(images[0].width, images[0].height, kind)
        i = 0
        for b in images:
            assert a.height == b.height and \
                a.width == b.width, 'Invalid image dimensions.'
            for j in range(b.count):
                for y in range(b.height):
                    a.rows[y][i::a.count] = b.rows[y][j::b.count]
                i += 1
        assert i == a.count, 'Invalid channels count.'
        return a
    
    def __init__(self, width, height, kind='rgb', source=None):
        assert kind in ('g','ga','rgb','rgba','cmyk'), 'Invalid image kind.'
        self.width, self.height = width, height
        self.kind = kind
        self.count = \
            1 if kind == 'g' else \
            2 if kind == 'ga' else \
            3 if kind == 'rgb' else 4
        self.source = source
        self.properties = record(
            background = (255,) * (self.count - 1) + \
                (0 if kind in ('ga', 'rgba') else 255,))
    
    @lazy
    def rows(self):
        if self.source:
            return self.source.decompress()
        template = bytearray(self.width * self.properties.background)
        return [template[:] for i in range(self.height)]
    
    def touch(self):
        self.source = None
        return self
    
    def background(self, *values):
        self.properties.background = values
        return self
    
    def equal(self, other):
        return self.kind == other.kind and self.rows == other.rows
    
    def clear(self):
        try:
            delattr(self, 'rows')
        except AttributeError:
            pass
        return self.touch()
    
    def copy(self):
        return deepcopy(self)
    
    def split(self):
        others = []
        for i in range(self.count):
            other = image(self.width, self.height, 'g')
            other.rows = [row[i::self.count] for row in self.rows]
            others.append(other)
        return others
    
    def get(self, x, y):
        offset = x * self.count
        return tuple(self.rows[y][offset:offset+self.count])
    
    def put(self, x, y, *values):
        row = self.rows[y]
        for offset, value in enumerate(values, x * self.count):
            row[offset] = value
        return self.touch()
    
    def fill(self, *values):
        return self.background(*values).clear()
    
    def blit(self, other, sx=0, sy=0, ox=0, oy=0, width=0, height=0):
        assert self.kind == other.kind, 'Different image kind.'
        width = max(0, min(self.width-sx, (width or other.width)-ox))
        height = max(0, min(self.height-sy, (height or other.height)-ox))
        sx *= self.count
        ox *= self.count
        width *= self.count
        for i in range(height):
            self.rows[i+sy][sx:sx+width] = other.rows[i+oy][ox:ox+width]
        return self.touch() if width!=0 and height!=0 else self
    
    def cropped(self, x, y, width, height):
        other = image(width, height, self.kind)
        other.properties.update(self.properties)
        other.blit(self, 0, 0, x, y, width, height)
        return other
    
    def crop(self, x, y, width, height):
        other = self.cropped(x, y, width, height)
        self.width, self.height = width, height
        self.rows[:] = other.rows
        return self.touch()
    
    def flip(self, horizontal, vertical):
        if horizontal:
            n = self.count
            for row in self.rows:
                r = row[::-1]
                for i in range(n):
                    row[i::n] = r[n-i-1::n]
        if vertical:
            self.rows.reverse()
        return self.touch() if horizontal or vertical else self
    
    def rotate(self, clockwise):
        self.width, self.height = self.height, self.width
        n = self.count
        rows = [bytearray(self.width * n) for i in range(self.height)]
        transpose = izip(*(reversed(self.rows) if clockwise else self.rows))
        for row in (rows if clockwise else reversed(rows)):
            for i in range(n):
                row[i::n] = next(transpose)
        self.rows[:] = rows
        return self.touch()
    
    def resized(self, width=0, height=0, interpolation='bicubic'):
        # Based on "General Filtered Image Rescaling"
        # by Dale Schumacher in Graphics Gems 3, p. 8-16, 1992
        
        if interpolation == 'nearest':
            kernel, size = _nearest, 0.5
        elif interpolation == 'bicubic':
            kernel, size = _bicubic, 2.0
        elif interpolation == 'lanczos':
            kernel, size = _lanczos, 3.0
        else:
            raise AssertionError('Invalid interpolation.')
        
        if width == self.width and height == self.height:
            return self
        if width == height == 0:
            return self
        if width == 0:
            width = (height * self.width) // self.height
        elif height == 0:
            height = (width * self.height) // self.width
        
        n = self.count
        
        h = _contributions(self.width, width, kernel, size, n)
        v = _contributions(self.height, height, kernel, size, 1)
        
        skipx = (width + self.width) // (self.width * 2)
        skipy = (height + self.height) // (self.height * 2)
        
        inter = image(width, self.height, self.kind)
        for iy, sy in zip(inter.rows, self.rows):
            for x in range(skipx, width - skipx):
                for i in range(n):
                    p = 0
                    for pixel, weight in h[x]:
                        p += sy[pixel + i] * weight
                    iy[x * n + i] = clamp((p + (1 << 51)) >> 52)
        
        if skipx > 0:
            for iy, sy in zip(inter.rows, self.rows):
                iy[:skipx * n] = sy[:n] * skipx
                iy[-skipx * n:] = sy[-n:] * skipx
        
        final = image(width, height, self.kind)
        ir = inter.rows
        for y in range(skipy, height - skipy):
            vy, fy = v[y], final.rows[y]
            for x in range(0, width * n, n):
                for i in range(n):
                    p = 0
                    for pixel, weight in vy:
                        p += ir[pixel][x + i] * weight
                    fy[x + i] = clamp((p + (1 << 51)) >> 52)
        
        for i in range(skipy):
            final.rows[i][:] = inter.rows[0]
            final.rows[-i - 1][:] = inter.rows[-1]
        
        return final
    
    def resize(self, width=0, height=0, interpolation='bicubic'):
        other = self.resized(width, height, interpolation)
        self.rows[:] = other.rows
        self.width, self.height = other.width, other.height
        return self.touch()
    
    def scale(self, factor, interpolation='bicubic'):
        return self.resize(
            int(round(self.width * factor)),
            int(round(self.height * factor)), interpolation)
    
    def blur(self, radius):
        
        kernel = pascal(radius * 2)
        
        n = self.count
        boundx, boundy = self.width*n-1, self.height-1
        
        inter = image(self.width, self.height, self.kind)
        for iy, sy in zip(inter.rows, self.rows):
            for x in range(0, self.width*n, n):
                for i in range(n):
                    total, divisor = 0, 0
                    for offset, weight in enumerate(kernel, -radius):
                        xx = x + i + offset * n
                        if 0 <= xx <= boundx:
                            total += sy[xx] * weight
                            divisor += weight
                    iy[x + i] = (total + divisor//2) // divisor
        
        ir = inter.rows
        for y in range(self.height):
            sy = self.rows[y]
            for x in range(0, self.width*n, n):
                for i in range(n):
                    total, divisor = 0, 0
                    for offset, weight in enumerate(kernel, -radius):
                        yy = y + offset
                        if 0 <= yy <= boundy:
                            total += ir[yy][x + i] * weight
                            divisor += weight
                    sy[x + i] = (total + divisor//2) // divisor
        
        return self.touch()
    
    def dither(self, levels=2):
        # Error diffusion dithering weights by Daniel Burkes, 1988
        
        assert self.kind == 'g', 'Invalid image kind.'
        assert 1 < levels < 257, 'Invalid levels count.'
        
        index = [0] * 256
        starts = staircase(256, levels)
        shades = staircase(255, levels - 1)
        for j in range(levels - 1):
            for i in range(starts[j], starts[j+1]):
                index[i] = shades[j]
        
        below0, below1 = [0] * (self.width+4), [0] * (self.width+4)
        for row in self.rows:
            ahead0, ahead1, below1[2], below1[3] = 0, 0, 0, 0
            for x in range(self.width):
                old = row[x] + (ahead0 + below0[x+2] + 16) // 32
                new = index[clamp(old)]
                row[x] = new
                error = old - new
                ahead0 = 8 * error + ahead1
                ahead1 = 4 * error
                below1[x] += 2 * error
                below1[x+1] += 4 * error
                below1[x+2] += 8 * error
                below1[x+3] += 4 * error
                below1[x+4] = 2 * error
            below0, below1 = below1, below0
        
        return self.touch()
    
    def invert(self):
        for row in self.rows:
            for x in range(self.width * self.count):
                row[x] ^= 255
        return self.touch()
    
    def png(self, path='', optimized=False):
        if type(self.source) == png:
            data = self.source.data
        else:
            data = png.dump(self, optimized)
        return save(path, data)
    
    def jpeg(self, path='', quality=90):
        if type(self.source) == jpeg:
            data = self.source.data
        else:
            data = jpeg.dump(self, quality)
        return save(path, data)
    
    def placed(self, scale):
        return placedimage(self, scale)




class placedimage(object):
    
    def __init__(self, item, k):
        self.item = item
        self.k = k
        self.x, self.y = 0.0, 0.0
        self.width, self.height = item.width, item.height
    
    def position(self, x, y):
        self.x, self.y = x*self.k, y*self.k
        return self
    
    def frame(self, x, y, width, height):
        self.x, self.y = x*self.k, y*self.k
        self.width, self.height = width*self.k, height*self.k
        return self
    
    def fitwidth(self, width):
        image = self.item
        self.width, self.height = \
            width*self.k, width*image.height/float(image.width)*self.k # TODO python 3: remove float()
        return self
    
    def fitheight(self, height):
        image = self.item
        self.width, self.height = \
            height*image.width/float(image.height)*self.k, height*self.k # TODO python 3: remove float()
        return self
    
    def pdf(self, previous, resources, colors, fonts, images, states, height):
        resource = resources.image(self.item)
        images.add(resource)
        return 'q %s 0 0 %s %s %s cm /%s Do Q' % (
            dump(self.width), dump(self.height),
            dump(self.x), dump(height-self.y-self.height),
            resource.name)
    
    def svg(self):
        image = self.item
        if self.width < self.height:
            a, b = self.width*image.height/float(image.width), self.height # TODO python 3: remove float()
        else:
            a, b = self.width, self.height*image.width/float(image.height) # TODO python 3: remove float()
        ratio = '' if equal(a, b) else ' preserveAspectRatio="none"'
        if type(image.source) == png:
            mime, data = 'image/png', image.source.data
        else:
            mime, data = 'image/jpeg', image.jpeg()
        return (
            '<image x="%s" y="%s" width="%s" height="%s"%s '
                'xlink:href="data:%s;base64,%s" />') % (
                dump(self.x), dump(self.y),
                dump(self.width), dump(self.height), ratio,
                mime, b64encode(data))
    
    def rasterize(self, rasterizer, k, x, y):
        other = self.item.resized(
            int(self.width * k + 0.5), int(self.height * k + 0.5))
        rasterizer.image.blit(other,
            int(self.x * k + x + 0.5), int(self.y * k + y + 0.5))




class raw(object):
    
    def __init__(self, width, height, rows=None):
        self.width, self.height = width, height
        if rows is None:
            rows = [[0.0] * width * 3 for i in range(height)]
        self.rows = rows
    
    def put(self, x, y, r, g, b):
        offset = x * 3
        row = self.rows[y]
        row[offset], row[offset+1], row[offset+2] = r, g, b

    def tonemapped(self, key=0.18, white=1.0):
        # Based on "Photographic Tone Reproduction for Digital Images"
        # by Erik Reinhard, Michael Stark, Peter Shirley and James Ferwerda, 2002
        
        w, h = self.width, self.height
        average = exp(sum(log(
            max(0.0001, r[x]*0.212671 + r[x+1]*0.71516 + r[x+2]*0.072169))
                for r in self.rows for x in range(0, w*3, 3)) / (w*h))
        scale = key / average
        iwhite2 = 1.0 / (white * white)
        
        other = image(w, h, 'rgb')
        for s, o in zip(self.rows, other.rows):
            for x in range(0, w*3, 3):
                l = scale * (s[x]*0.212671 + s[x+1]*0.71516 + s[x+2]*0.072169)
                d = scale * (1.0 + l * iwhite2) / (1.0 + l)
                for i in range(x, x+3):
                    o[i] = min(int((s[i] * d) ** 0.45 * 255.0 + 0.5), 255)
        return other




