
from copy import copy

from .utils import dump




class gray(object):
    
    __slots__ = 'intensity',
    
    kind = 'g'
    
    def __init__(self, intensity):
        self.intensity = intensity
    
    def __ne__(self, other):
        return type(other) != gray or self.intensity != other.intensity
    
    def pdf(self):
        return dump(self.intensity / 255.0)
    
    def pdfstroke(self):
        return '%s G' % self.pdf()
    
    def pdffill(self):
        return '%s g' % self.pdf()
    
    def svg(self):
        raise NotImplementedError('SVG does not support grayscale.')


class ga(object):
    
    __slots__ = 'intensities',
    
    kind = 'ga'
    
    def __init__(self, g, a):
        self.intensities = g, a
    
    def __ne__(self, other):
        return type(other) != ga or self.intensities != other.intensities
    
    def pdf(self):
        raise NotImplementedError('PDF transparency not supported.')
    
    def pdfstroke(self):
        raise NotImplementedError('PDF transparency not supported.')
    
    def pdffill(self):
        raise NotImplementedError('PDF transparency not supported.')
    
    def svg(self):
        raise NotImplementedError('SVG does not support grayscale.')


class rgb(object):
    
    __slots__ = 'intensities',
    
    kind = 'rgb'
    
    def __init__(self, r, g, b):
        self.intensities = r, g, b
    
    def __ne__(self, other):
        return type(other) != rgb or self.intensities != other.intensities
    
    def pdf(self):
        return ' '.join(dump(i / 255.0) for i in self.intensities)
    
    def pdfstroke(self):
        return '%s RG' % self.pdf()
    
    def pdffill(self):
        return '%s rg' % self.pdf()
    
    def svg(self):
        r, g, b = self.intensities
        return 'rgb(%s,%s,%s)' % (dump(r), dump(g), dump(b))


class rgba(object):
    
    __slots__ = 'intensities',
    
    kind = 'rgba'
    
    def __init__(self, r, g, b, a):
        self.intensities = r, g, b, a
    
    def __ne__(self, other):
        return type(other) != rgba or self.intensities != other.intensities
    
    def pdf(self):
        raise NotImplementedError('PDF transparency not supported.')
    
    def pdfstroke(self):
        raise NotImplementedError('PDF transparency not supported.')
    
    def pdffill(self):
        raise NotImplementedError('PDF transparency not supported.')
    
    def svg(self):
        raise NotImplementedError('SVG does not yet support "rgba".')


class cmyk(object):
    
    __slots__ = 'tints',
    
    kind = 'cmyk'
    
    def __init__(self, c, m, y, k):
        self.tints = c, m, y, k
    
    def __ne__(self, other):
        return type(other) != cmyk or self.tints != other.tints
    
    def pdf(self):
        return ' '.join(dump(t * 0.01) for t in self.tints)
    
    def pdfstroke(self):
        return '%s K' % self.pdf()
    
    def pdffill(self):
        return '%s k' % self.pdf()
    
    def svg(self):
        raise NotImplementedError('SVG does not yet support "device-cmyk".')


class spot(object):
    
    __slots__ = 'name', 'fallback', 'tint'
    
    kind = 'spot'
    
    def __init__(self, name, fallback):
        assert type(fallback) == cmyk, 'Invalid fallback kind.'
        self.name, self.fallback, self.tint = name, fallback, 100.0
    
    def __ne__(self, other):
        return type(other) != spot or \
            self.name != other.name or self.tint != other.tint
    
    def thinned(self, tint):
        other = copy(self)
        other.tint = tint
        return other
    
    def pdf(self):
        return dump(self.tint * 0.01)
    
    def pdfstroke(self, name):
        return '/%s CS %s SCN' % (name, self.pdf())
    
    def pdffill(self, name):
        return '/%s cs %s scn' % (name, self.pdf())
    
    def svg(self):
        raise NotImplementedError('SVG does not yet support "device-nchannel".')


class devicen(object):
    
    __slots__ = 'names', 'fallbacks', 'tints'
    
    kind = 'devicen'
    
    def __init__(self, *spots):
        self.names, self.fallbacks, self.tints = zip(*(
            (spot.name, spot.fallback, spot.tint) for spot in spots))
    
    def __ne__(self, other):
        return type(other) != devicen or \
            self.names != other.names or self.tints != other.tints
    
    def thinned(self, *tints):
        other = copy(self)
        other.tints = tints
        return other
    
    def pdf(self):
        return ' '.join(dump(tint * 0.01) for tint in self.tints)
    
    def pdfstroke(self, name):
        return '/%s CS %s SCN' % (name, self.pdf())
    
    def pdffill(self, name):
        return '/%s cs %s scn' % (name, self.pdf())
    
    def svg(self):
        raise NotImplementedError('SVG does not yet support "device-nchannel".')


class overprint(object):
    
    __slots__ = 'color',
    
    kind = 'overprint'
    
    def __init__(self, color):
        assert type(color) in (cmyk, spot, devicen), 'Invalid color kind.'
        self.color = color
    
    def __ne__(self, other):
        return type(other) != overprint or self.color != other.color
    
    def svg(self):
        raise NotImplementedError('SVG does not support overprint.')




_default_color = gray(0)




