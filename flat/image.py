from base64 import b64encode
from math import ceil, exp, floor, log, pi, sin
from .jpeg import jpeg, serialize as jpegserialize
from .misc import dump, save, similar
from .png import png, serialize as pngserialize




def nearest_kernel(x):
    if -0.5 <= x < 0.5:
        return 1.0
    return 0.0

def _bicubic_kernel(x):
    if x < 0.0:
        x = -x
    if x < 1.0:
        return (1.5*x - 2.5)*x*x + 1.0
    if x < 2.0:
        return ((-0.5*x + 2.5)*x - 4.0)*x + 2.0
    return 0.0

def _lanczos_kernel(x):
    if x < 0.0:
        x = -x
    if x < 1e-10:
        return 1.0
    if x < 5.0:
        x *= pi
        return 5.0*sin(x)*sin(x/5.0)/(x*x)
    return 0.0

def _kernel_contribution(index, scale, length, kernel, support):
    factor = max(1.0, scale)
    support *= factor
    x = (index + 0.5)*scale - 0.5
    left = max(0, int(ceil(x - support)))
    right = min(int(floor(x + support)), length - 1)
    weights = []
    total = 0.0
    i = left
    while i <= right:
        w = kernel((x - i)/factor)
        weights.append(w)
        total += w
        i += 1
    if total != 1.0:
        for i in range(len(weights)):
            weights[i] /= total
    return left, weights




class image(object):
    
    __slots__ = 'width', 'height', 'kind', 'n', 'data', 'source'
    
    @staticmethod
    def open(path):
        with open(path, 'rb') as f:
            data = f.read()
            if jpeg.valid(data):
                source = jpeg(data)
                rotation = source.rotation
            elif png.valid(data):
                source = png(data)
                rotation = 0
            else:
                raise ValueError('Unsupported image format.')
            i = image(0, 0, source.kind)
            if rotation == 90 or rotation == 270:
                i.width, i.height = source.height, source.width
            else:
                i.width, i.height = source.width, source.height
            i.source = source
            return i
    
    def __init__(self, width, height, kind='rgb'):
        self.width, self.height = width, height
        if kind == 'g':
            self.n = 1
        elif kind == 'ga':
            self.n = 2
        elif kind == 'rgb':
            self.n = 3
        elif kind == 'rgba' or kind == 'cmyk':
            self.n = 4
        else:
            raise ValueError('Invalid image kind.')
        self.kind = kind
        self.data = bytearray(width*height*self.n)
        self.source = None
    
    def __eq__(self, other):
        self.decompress(); other.decompress()
        return self.width == other.width and self.height == other.height and \
            self.kind == other.kind and self.data == other.data
    
    def __ne__(self, other):
        return not self == other
    
    def copy(self):
        i = image(0, 0, self.kind)
        i.width, i.height = self.width, self.height
        i.data[:], i.source = self.data, self.source
        return i
    
    def decompress(self):
        if self.source:
            source, self.source = self.source, None
            self.data[:] = source.decompress()
            if isinstance(source, jpeg):
                rotation = source.rotation
                if rotation == 90 or rotation == 270:
                    self.width, self.height = self.height, self.width
                    self.rotate(rotation == 90)
                elif rotation == 180:
                    self.flip(True, True)
        return self
    
    def get(self, x, y):
        self.decompress()
        n = self.n
        i = (x + y*self.width)*n
        return tuple(self.data[i:i + n])
    
    def put(self, x, y, components):
        self.decompress()
        n, data = self.n, self.data
        if n != len(components):
            raise ValueError('Different component count.')
        i, j = (x + y*self.width)*n, 0
        while n > 0:
            data[i] = components[j]
            i += 1
            j += 1
            n -= 1
        return self
    
    def fill(self, components):
        self.decompress()
        n, data = self.n, self.data
        if n != len(components):
            raise ValueError('Different component count.')
        for i in range(self.width*self.height*n):
            data[i] = components[i%n]
        return self
    
    def white(self):
        self.decompress()
        kind, data = self.kind, self.data
        for i in range(0, self.width*self.height*self.n, self.n):
            if kind == 'g':
                data[i] = 255
            elif kind == 'ga':
                data[i] = 255
                data[i+1] = 0
            elif kind == 'rgb':
                data[i] = data[i+1] = data[i+2] = 255
            elif kind == 'rgba':
                data[i] = data[i+1] = data[i+2] = 255
                data[i+3] = 0
            else: # cmyk
                data[i] = data[i+1] = data[i+2] = data[i+3] = 0
        return self
    
    def black(self):
        self.decompress()
        kind, data = self.kind, self.data
        for i in range(0, self.width*self.height*self.n, self.n):
            if kind == 'g':
                data[i] = 0
            elif kind == 'ga':
                data[i] = data[i+1] = 0
            elif kind == 'rgb':
                data[i] = data[i+1] = data[i+2] = 0
            elif kind == 'rgba':
                data[i] = data[i+1] = data[i+2] = data[i+3] = 0
            else: # cmyk
                data[i] = data[i+1] = data[i+2] = 0
                data[i+3] = 255
        return self
    
    def blit(self, x, y, source):
        self.decompress()
        if self.kind != source.kind:
            raise ValueError('Different image kind.')
        w, h, n = self.width, self.height, self.n
        width = max(0, min(w, w - x, source.width, source.width + x))
        height = max(0, min(h, h - y, source.height, source.height + y))
        r = range(height)
        if y > 0 and self.data is source.data:
            r = reversed(r)
        for k in r:
            i = (max(0, x) + (max(0, y) + k)*w)*n
            j = (max(0, -x) + (max(0, -y) + k)*source.width)*n
            self.data[i:i + width*n] = source.data[j:j + width*n]
        return self
    
    def crop(self, x, y, width, height):
        self.decompress()
        w, h, n = self.width, self.height, self.n
        width = max(0, min(w, w - x, width, width + x))
        height = max(0, min(h, h - y, height, height + y))
        if w != width:
            for k in range(height):
                i = (0 + (0 + k)*width)*n
                j = (max(0, x) + (max(0, y) + k)*w)*n
                self.data[i:i + width*n] = self.data[j:j + width*n]
        self.data[width*height*n:] = []
        self.width, self.height = width, height
        return self
    
    def flip(self, horizontal, vertical):
        self.decompress()
        w, h, n, data = self.width, self.height, self.n, self.data
        if horizontal and vertical:
            for y in range(h//2):
                for x in range(w):
                    i = (x + y*w)*n
                    j = ((w - x - 1) + (h - y - 1)*w)*n
                    k = n
                    while k > 0:
                        data[i], data[j] = data[j], data[i]
                        i += 1
                        j += 1
                        k -= 1
            if h%2 == 1:
                m = h//2
                for x in range(w//2):
                    i = (x + m*w)*n
                    j = ((w - x - 1) + m*w)*n
                    k = n
                    while k > 0:
                        data[i], data[j] = data[j], data[i]
                        i += 1
                        j += 1
                        k -= 1
        elif horizontal:
            for y in range(h):
                for x in range(w//2):
                    i = (x + y*w)*n
                    j = ((w - x - 1) + y*w)*n
                    k = n
                    while k > 0:
                        data[i], data[j] = data[j], data[i]
                        i += 1
                        j += 1
                        k -= 1
        elif vertical:
            for y in range(h//2):
                for x in range(w):
                    i = (x + y*w)*n
                    j = (x + (h - y - 1)*w)*n
                    k = n
                    while k > 0:
                        data[i], data[j] = data[j], data[i]
                        i += 1
                        j += 1
                        k -= 1
        return self
    
    def transpose(self):
        self.decompress()
        w, h, n, data = self.width, self.height, self.n, self.data
        if w == h:
            for y in range(h - 1):
                for x in range(y + 1, w):
                    i = (x + y*w)*n
                    j = (y + x*h)*n
                    k = n
                    while k > 0:
                        data[i], data[j] = data[j], data[i]
                        i += 1
                        j += 1
                        k -= 1
            return self
        result = bytearray(w*h*n)
        for y in range(h):
            for x in range(w):
                i = (x + y*w)*n
                j = (y + x*h)*n
                k = n
                while k > 0:
                    result[j] = data[i]
                    i += 1
                    j += 1
                    k -= 1
        self.width, self.height = h, w
        self.data[:] = result
        return self
    
    def rotate(self, clockwise):
        self.decompress()
        w, h, n, data = self.width, self.height, self.n, self.data
        if w == h:
            for y in range(h//2):
                for x in range(y, w - y - 1):
                    i = (x + y*w)*n
                    j = ((w - y - 1) + x*w)*n
                    k = ((w - x - 1) + (h - y - 1)*w)*n
                    l = (y + (h - x - 1)*w)*n
                    m = n
                    while m > 0:
                        t = data[i]
                        if clockwise:
                            data[i] = data[l]
                            data[l] = data[k]
                            data[k] = data[j]
                            data[j] = t
                        else:
                            data[i] = data[j]
                            data[j] = data[k]
                            data[k] = data[l]
                            data[l] = t
                        i += 1
                        j += 1
                        k += 1
                        l += 1
                        m -= 1
            return self
        result = bytearray(w*h*n)
        for y in range(h):
            for x in range(w):
                i = (x + y*w)*n
                if clockwise:
                    j = (h - y - 1 + x*h)*n
                else:
                    j = (y + (w - x - 1)*h)*n
                k = n
                while k > 0:
                    result[j] = data[i]
                    i += 1
                    j += 1
                    k -= 1
        self.width, self.height = h, w
        self.data[:] = result
        return self
    
    def resize(self, width=0, height=0, interpolation='bicubic'):
        self.decompress()
        if interpolation == 'nearest':
            kernel, support = nearest_kernel, 0.5
        elif interpolation == 'bicubic':
            kernel, support = _bicubic_kernel, 2.0
        elif interpolation == 'lanczos':
            kernel, support = _lanczos_kernel, 5.0
        else:
            raise ValueError('Invalid interpolation.')
        w, h, n, data = self.width, self.height, self.n, self.data
        if width == w and height == h:
            return self
        if width == 0 and height == 0:
            return self
        if width == 0:
            width = max(1, (height*w)//h)
        elif height == 0:
            height = max(1, (width*h)//w)
        result = bytearray(width*height*n)
        column = [0.0]*h
        sx, sy = w/width, h/height
        ycontributions = [_kernel_contribution(y, sy, h, kernel, support)
            for y in range(height)]
        for x in range(width):
            index, xweights = _kernel_contribution(x, sx, w, kernel, support)
            for component in range(n):
                for y in range(h):
                    c = 0.0
                    i = (index + y*w)*n + component
                    for weight in xweights:
                        c += data[i]*weight
                        i += n
                    column[y] = c
                for y in range(height):
                    c = 0.0
                    i, yweights = ycontributions[y]
                    for weight in yweights:
                        c += column[i]*weight
                        i += 1
                    if c < 0.5:
                        value = 0
                    elif c >= 254.5:
                        value = 255
                    else:
                        value = int(c + 0.5)
                    i = (x + y*width)*n + component
                    result[i] = value
        self.width, self.height = width, height
        self.data[:] = result
        return self
    
    def rescale(self, factor, interpolation='bicubic'):
        w, h = int(self.width*factor+0.5), int(self.height*factor+0.5)
        return self.resize(w, h, interpolation)
    
    def blur(self, radius):
        self.decompress()
        kernel = [1]*(radius*2 + 1)
        for k in range(radius*2 - 1):
            kernel[k + 1] = kernel[k]*(radius*2 - k)//(k + 1)
        w, h, n, data = self.width, self.height, self.n, self.data
        separation = bytearray(w*h*n)
        for y in range(h):
            for x in range(w):
                for component in range(n):
                    offset = -radius
                    value = total = 0
                    for weight in kernel:
                        if 0 <= x + offset < w:
                            i = (x + offset + y*w)*n + component
                            value += data[i]*weight
                            total += weight
                        offset += 1
                    i = (y + x*h)*n + component
                    separation[i] = (value + total//2)//total
        for x in range(w):
            for y in range(h):
                for component in range(n):
                    offset = -radius
                    value = total = 0
                    for weight in kernel:
                        if 0 <= y + offset < h:
                            i = (y + offset + x*h)*n + component
                            value += separation[i]*weight
                            total += weight
                        offset += 1
                    i = (x + y*w)*n + component
                    data[i] = (value + total//2)//total
        return self
    
    def dither(self, levels=2):
        self.decompress()
        # Error diffusion dithering weights by Burkes, D. (1988).
        if self.kind != 'g':
            raise ValueError('Invalid image kind.')
        if levels < 2 or levels > 256:
            raise ValueError('Invalid levels count.')
        w, h, data = self.width, self.height, self.data
        cache = [255*(i*levels//256)//(levels - 1) for i in range(256)]
        errors = [0]*(w + 4)
        for y in range(h):
            error1, error2 = errors[2], errors[3]
            errors[2] = errors[3] = 0
            for x in range(w):
                i = x + y*w
                old = data[i] + (error1 + 16)//32
                new = data[i] = cache[max(0, min(old, 255))]
                error = old - new
                error1 = 8*error + error2
                error2 = 4*error + errors[x + 4]
                errors[x] += 2*error
                errors[x + 1] += 4*error
                errors[x + 2] += 8*error
                errors[x + 3] += 4*error
                errors[x + 4] = 2*error
        return self
    
    def gamma(self, value):
        self.decompress()
        data = self.data
        cache = [int((i/255.0)**value*255.0 + 0.5) for i in range(256)]
        for i in range(self.width*self.height*self.n):
            data[i] = cache[data[i]]
        return self
    
    def invert(self):
        self.decompress()
        data = self.data
        for i in range(self.width*self.height*self.n):
            data[i] ^= 255
        return self
    
    def jpeg(self, path='', quality=95):
        if isinstance(self.source, jpeg):
            return save(path, self.source.readable.data)
        self.decompress()
        data = jpegserialize(self, quality)
        return save(path, data)
    
    def png(self, path='', optimized=False):
        if isinstance(self.source, png):
            return save(path, self.source.readable.data)
        self.decompress()
        data = pngserialize(self, optimized)
        return save(path, data)
    
    def placed(self, k):
        return placedimage(self, k)




class placedimage(object):
    
    __slots__ = 'item', 'k', 'x', 'y', 'width', 'height'
    
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
            width*self.k, width*image.height/image.width*self.k
        return self
    
    def fitheight(self, height):
        image = self.item
        self.width, self.height = \
            height*image.width/image.height*self.k, height*self.k
        return self
    
    def pdf(self, height, state, resources):
        x, y = self.x, height-self.y-self.height
        w, h = self.width, self.height
        a, b, c, d, e, f = w, 0, 0, h, x, y
        if isinstance(self.item.source, jpeg):
            rotation = self.item.source.rotation
            if rotation == 90:
                a, b, c, d, e, f = 0, -h, w, 0, x, y+h
            elif rotation == 180:
                a, b, c, d, e, f = -w, 0, 0, -h, x+w, y+h
            elif rotation == 270:
                a, b, c, d, e, f = 0, h, -w, 0, x+w, y
        resource = resources.image(self.item)
        return b'q %s %s %s %s %s %s cm /%s Do Q' % (
            dump(a), dump(b), dump(c), dump(d), dump(e), dump(f),
            resource.name)
    
    def svg(self):
        image = self.item
        if similar(self.width, self.height*(image.width/image.height)):
            ratio = b''
        else:
            ratio = b' preserveAspectRatio="none"'
        if isinstance(image.source, png):
            mime, data = b'image/png', image.source.readable.data
        else:
            mime, data = b'image/jpeg', image.jpeg()
        return (
            b'<image x="%s" y="%s" width="%s" height="%s"%s '
                b'xlink:href="data:%s;base64,%s" />') % (
                dump(self.x), dump(self.y),
                dump(self.width), dump(self.height), ratio,
                mime, b64encode(data))
    
    def rasterize(self, rasterizer, k, x, y):
        x, y = int(round(self.x*k + x)), int(round(self.y*k + y))
        w, h = int(self.width*k + 0.5), int(self.height*k + 0.5)
        source = self.item.copy().resize(w, h)
        rasterizer.image.blit(x, y, source)




class raw(object):
    
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.data = [0.0]*width*height*3
    
    def put(self, x, y, r, g, b):
        data = self.data
        i = (x + y*self.width)*3
        data[i], data[i+1], data[i+2] = r, g, b
        return self

    def tonemapped(self, key=0.18, white=1.0):
        # Ref.: Reinhard, E., Stark, M., Shirley, P., Ferwerda, J. (2002).
        # Photographic Tone Reproduction for Digital Images.
        w, h, data = self.width, self.height, self.data
        total = 0.0
        for i in range(0, w*h*3, 3):
            r, g, b = data[i], data[i+1], data[i+2]
            l = r*0.212671 + g*0.71516 + b*0.072169
            total += log(max(1e-10, l))
        average = exp(total/(w*h))
        scale = key/average
        iwhite2 = 1.0/(white*white)
        other = image(w, h, 'rgb')
        otherdata = other.data
        for i in range(0, w*h*3, 3):
            r, g, b = data[i], data[i+1], data[i+2]
            l = scale*(r*0.212671 + g*0.71516 + b*0.072169)
            d = scale*(1.0 + l*iwhite2)/(1.0 + l)
            for j in range(i, i + 3):
                otherdata[j] = min(int((data[j]*d)**0.45*255.0 + 0.5), 255)
        return other




