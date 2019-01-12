from .misc import dump




class gray(object):
    
    __slots__ = 'intensity',
    
    def __init__(self, intensity):
        self.intensity = intensity
    
    def __ne__(self, other):
        return not isinstance(other, gray) or \
            self.intensity != other.intensity
    
    def pdfstroke(self):
        return b'%s G' % dump(self.intensity/255.0)
    
    def pdffill(self):
        return b'%s g' % dump(self.intensity/255.0)
    
    def svg(self):
        raise NotImplementedError('SVG does not support grayscale.')
    
    def rasterize(self, rasterizer):
        if rasterizer.image.kind != 'g':
            raise ValueError('Invalid color kind.')
        rasterizer.rasterize(self.intensity)

class ga(object):
    
    __slots__ = 'g', 'a'
    
    def __init__(self, g, a):
        self.g, self.a = g, a
    
    def __ne__(self, other):
        return not isinstance(other, ga) or \
            self.g != other.g or \
            self.a != other.a
    
    def pdfstroke(self):
        raise NotImplementedError('PDF does not support grayscale + alpha.')
    
    def pdffill(self):
        raise NotImplementedError('PDF does not support grayscale + alpha.')
    
    def svg(self):
        raise NotImplementedError('SVG does not support grayscale + alpha.')
    
    def rasterize(self, rasterizer):
        if rasterizer.image.kind != 'ga':
            raise ValueError('Invalid color kind.')
        rasterizer.rasterize(self.g, self.a)

class rgb(object):
    
    __slots__ = 'r', 'g', 'b'
    
    def __init__(self, r, g, b):
        self.r, self.g, self.b = r, g, b
    
    def __ne__(self, other):
        return not isinstance(other, rgb) or \
            self.r != other.r or \
            self.g != other.g or \
            self.b != other.b
    
    def pdfstroke(self):
        return b'%s %s %s RG' % (
            dump(self.r/255.0),
            dump(self.g/255.0),
            dump(self.b/255.0))
    
    def pdffill(self):
        return b'%s %s %s rg' % (
            dump(self.r/255.0),
            dump(self.g/255.0),
            dump(self.b/255.0))
    
    def svg(self):
        return b'rgb(%s,%s,%s)' % (
            dump(self.r),
            dump(self.g),
            dump(self.b))
    
    def rasterize(self, rasterizer):
        if rasterizer.image.kind != 'rgb':
            raise ValueError('Invalid color kind.')
        rasterizer.rasterize(self.r, self.g, self.b)

class rgba(object):
    
    __slots__ = 'r', 'g', 'b', 'a'
    
    def __init__(self, r, g, b, a):
        self.r, self.g, self.b, self.a = r, g, b, a
    
    def __ne__(self, other):
        return not isinstance(other, rgb) or \
            self.r != other.r or \
            self.g != other.g or \
            self.b != other.b or \
            self.a != other.a
    
    def pdfstroke(self):
        raise NotImplementedError('PDF does not support RGB + alpha.')
    
    def pdffill(self):
        raise NotImplementedError('PDF does not support RGB + alpha.')

    def svg(self):
        return b'rgba(%s,%s,%s,%s)' % (
            dump(self.r),
            dump(self.g),
            dump(self.b),
            dump(self.a/255.0))
    
    def rasterize(self, rasterizer):
        if rasterizer.image.kind != 'rgba':
            raise ValueError('Invalid color kind.')
        rasterizer.rasterize(self.r, self.g, self.b, self.a)

class cmyk(object):
    
    __slots__ = 'c', 'm', 'y', 'k'
    
    def __init__(self, c, m, y, k):
        self.c, self.m, self.y, self.k = c, m, y, k
    
    def __ne__(self, other):
        return not isinstance(other, cmyk) or \
            self.c != other.c or \
            self.m != other.m or \
            self.y != other.y or \
            self.k != other.k
    
    def pdfstroke(self):
        return b'%s %s %s %s K' % (
            dump(self.c/255.0),
            dump(self.m/255.0),
            dump(self.y/255.0),
            dump(self.k/255.0))
    
    def pdffill(self):
        return b'%s %s %s %s k' % (
            dump(self.c/255.0),
            dump(self.m/255.0),
            dump(self.y/255.0),
            dump(self.k/255.0))
    
    def svg(self):
        raise NotImplementedError('SVG does not yet support "device-cmyk".')
    
    def rasterize(self, rasterizer):
        raise NotImplementedError('Rasterizer does not support CMYK.')

class spot(object):
    
    __slots__ = 'name', 'fallback', 'tint'
    
    def __init__(self, name, fallback):
        if not isinstance(fallback, cmyk):
            raise ValueError('Invalid fallback kind.')
        self.name, self.fallback, self.tint = name, fallback, 100.0
    
    def __ne__(self, other):
        return not isinstance(other, spot) or \
            self.name != other.name or \
            self.tint != other.tint
    
    def thinned(self, tint):
        other = spot(self.name, self.fallback)
        other.tint = tint
        return other
    
    def pdfstroke(self, name):
        return b'/%s CS %s SCN' % (name, dump(self.tint/100.0))
    
    def pdffill(self, name):
        return b'/%s cs %s scn' % (name, dump(self.tint/100.0))
    
    def svg(self):
        raise NotImplementedError('SVG does not yet support "device-nchannel".')
    
    def rasterize(self, rasterizer):
        raise NotImplementedError('Rasterizer does not support spot colors.')




class overprint(object):
    
    __slots__ = 'color',
    
    def __init__(self, color):
        if not isinstance(color, (cmyk, spot)):
            raise ValueError('Invalid color kind.')
        self.color = color
    
    def __ne__(self, other):
        return not isinstance(other, overprint) or \
            self.color != other.color
    
    def svg(self):
        raise NotImplementedError('SVG does not support overprint.')
    
    def rasterize(self, rasterizer):
        raise NotImplementedError('Rasterizer does not support overprint.')




