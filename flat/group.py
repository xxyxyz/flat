from copy import copy
from .misc import dump, scale




class group(object):
    
    __slots__ = 'k', 'items'
    
    @staticmethod
    def open(path):
        raise NotImplementedError
    
    def __init__(self, units='mm'):
        self.k = scale(units)
        self.items = []
    
    def units(self, units='mm'):
        self.k = scale(units)
    
    def place(self, item):
        entity = item.placed(self.k)
        self.items.append(entity)
        return entity
    
    def chain(self, block):
        block = block.chained(self.k)
        self.items.append(block)
        return block
    
    def placed(self, k):
        return placedgroup(self, k)




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
    
    def pdf(self, height, state, resources):
        dummy = copy(state)
        code = b'\n'.join(
            item.pdf(0.0, dummy, resources) for item in self.item.items)
        return b'q %s 0 0 %s %s %s cm\n%s\nQ' % (
            dump(self.factor), dump(self.factor),
            dump(self.x), dump(height-self.y),
            code)
    
    def svg(self):
        code = b'\n'.join(item.svg() for item in self.item.items)
        return b'<g transform="matrix(%s, 0, 0, %s, %s, %s)">%s</g>' % (
            dump(self.factor), dump(self.factor),
            dump(self.x), dump(self.y),
            code)
    
    def rasterize(self, rasterizer, k, x, y):
        for item in self.item.items:
            item.rasterize(rasterizer, self.factor*k, self.x*k+x, self.y*k+y)




