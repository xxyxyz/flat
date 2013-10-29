
from .utils import dump




class moveto(object):
    
    __slots__ = 'x', 'y'
    
    def __init__(self, x, y):
        self.x, self.y = x, y
    
    def transform(self, a, b, c, d, e, f):
        x, y = self.x, self.y
        self.x, self.y = x*a + y*c + e, x*b + y*d + f
        return self
    
    def flip(self):
        self.y = -self.y
        return self
    
    def pdf(self, k, x, y):
        return '%s %s m' % (dump(self.x*k+x), dump(y-self.y*k))
    
    def svg(self, k, x, y):
        return 'M%s,%s' % (dump(self.x*k+x), dump(self.y*k+y))


class lineto(object):
    
    __slots__ = 'x', 'y'
    
    def __init__(self, x, y):
        self.x, self.y = x, y
    
    def transform(self, a, b, c, d, e, f):
        x, y = self.x, self.y
        self.x, self.y = x*a + y*c + e, x*b + y*d + f
        return self
    
    def flip(self):
        self.y = -self.y
        return self
    
    def pdf(self, k, x, y):
        return '%s %s l' % (dump(self.x*k+x), dump(y-self.y*k))
    
    def svg(self, k, x, y):
        return 'L%s,%s' % (dump(self.x*k+x), dump(self.y*k+y))


class quadto(object):
    
    __slots__ = 'x1', 'y1', 'x', 'y'
    
    def __init__(self, x1, y1, x, y):
        self.x1, self.y1 = x1, y1
        self.x, self.y = x, y
    
    def transform(self, a, b, c, d, e, f):
        x1, y1 = self.x1, self.y1
        x, y = self.x, self.y
        self.x1, self.y1 = x1*a + y1*c + e, x1*b + y1*d + f
        self.x, self.y = x*a + y*c + e, x*b + y*d + f
        return self
    
    def flip(self):
        self.y1 = -self.y1
        self.y = -self.y
        return self
    
    def pdf(self, k, x, y):
        raise NotImplementedError('Not available in PDF.')
    
    def svg(self, k, x, y):
        return 'Q%s,%s,%s,%s' % (
            dump(self.x1*k+x), dump(self.y1*k+y),
            dump(self.x*k+x), dump(self.y*k+y))


class curveto(object):
    
    __slots__ = 'x1', 'y1', 'x2', 'y2', 'x', 'y'
    
    def __init__(self, x1, y1, x2, y2, x, y):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.x, self.y = x, y
    
    def transform(self, a, b, c, d, e, f):
        x1, y1 = self.x1, self.y1
        x2, y2 = self.x2, self.y2
        x, y = self.x, self.y
        self.x1, self.y1 = x1*a + y1*c + e, x1*b + y1*d + f
        self.x2, self.y2 = x2*a + y2*c + e, x2*b + y2*d + f
        self.x, self.y = x*a + y*c + e, x*b + y*d + f
        return self
    
    def flip(self):
        self.y1 = -self.y1
        self.y2 = -self.y2
        self.y = -self.y
        return self
    
    def pdf(self, k, x, y):
        return '%s %s %s %s %s %s c' % (
            dump(self.x1*k+x), dump(y-self.y1*k),
            dump(self.x2*k+x), dump(y-self.y2*k),
            dump(self.x*k+x), dump(y-self.y*k))
    
    def svg(self, k, x, y):
        return 'C%s,%s,%s,%s,%s,%s' % (
            dump(self.x1*k+x), dump(self.y1*k+y),
            dump(self.x2*k+x), dump(self.y2*k+y),
            dump(self.x*k+x), dump(self.y*k+y))


class closepath(object):
    
    def __call__(self):
        return self
    
    def transform(self, a, b, c, d, e, f):
        return self
    
    def flip(self):
        return self
    
    def pdf(self, k, x, y):
        return 'h'
    
    def svg(self, k, x, y):
        return 'z'

closepath = closepath()




