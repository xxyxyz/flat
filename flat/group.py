
from .utils import dump, scale




class group(object):
    
    __slots__ = 'items', 'k'
    
    @staticmethod
    def open(path):
        raise NotImplementedError
    
    def __init__(self, units='mm'):
        self.items = []
        self.k = scale(units)
    
    def units(self, units='mm'):
        self.k = scale(units)
    
    def place(self, item):
        placed = item.placed(self.k)
        self.items.append(placed)
        return placed
    
    def placed(self, scale):
        return placedgroup(self, scale)




class placedgroup(object):
    
    __slots__ = 'item', 'k', 'x', 'y', 'factor'
    
    def __init__(self, item, k):
        self.item = item
        self.k = k
        self.x, self.y = 0.0, 0.0
        self.factor = 1.0
    
    def position(self, x, y):
        self.x, self.y = x*self.k, y*self.k
        return self
    
    def scale(self, factor):
        self.factor = factor
        return self
    
    def pdf(self, previous, resources, spaces, fonts, images, states, height):
        dummy = previous.copy()
        commands = '\n'.join([
            item.pdf(
                dummy,
                resources,
                spaces, fonts, images, states,
                0.0) for item in self.item.items])
        factor = dump(self.factor)
        return 'q %s 0 0 %s %s %s cm\n%s\nQ' % (
            factor, factor, dump(self.x), dump(height-self.y),
            commands)
    
    def svg(self):
        elements = '\n'.join([item.svg() for item in self.item.items])
        factor = dump(self.factor)
        return '<g transform="matrix(%s, 0, 0, %s, %s, %s)">%s</g>' % (
            factor, factor, dump(self.x), dump(self.y),
            elements)
    
    def rasterize(self, rasterizer, k, x, y):
        for item in self.item.items:
            item.rasterize(rasterizer, self.factor*k, self.x*k+x, self.y*k+y)




