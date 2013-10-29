
from weakref import proxy

from .rasterizer import rasterizer
from .utils import save, scale
from . import pdfwriter
from . import svgwriter




class page(object):
    
    def __init__(self, document):
        self.document = proxy(document)
        self.k = document.k
        self.width, self.height = document.width, document.height
        self.items = []
        self.append = self.items.append
    
    def size(self, width, height, units='mm'):
        self.k = scale(units)
        self.width, self.height = width*self.k, height*self.k
        return self
    
    def place(self, item):
        placed = item.placed(self.k)
        self.append(placed)
        return placed
    
    def chain(self, item):
        chained = item.chained(self.k)
        self.append(chained)
        return chained
    
    def svg(self, path='', compress=False):
        data = svgwriter.dump(self)
        return save(path, data)
    
    def image(self, ppi=72, kind='g', samples=32):
        k = ppi / 72.0
        r = rasterizer(
            int(self.width * k + 0.5),
            int(self.height * k + 0.5), kind, samples)
        for item in self.items:
            item.rasterize(r, k, 0.0, 0.0)
        return r.image




class document(object):
    
    @staticmethod
    def open(path):
        raise NotImplementedError
    
    def __init__(self, width=210, height=297, units='mm'):
        self.title = 'Untitled'
        self.k = scale(units)
        self.width, self.height = width*self.k, height*self.k
        self.bleed, self.cropmarks = False, False
        self.pages = []
    
    def meta(self, title):
        self.title = title
        return self
    
    def size(self, width, height, units='mm'):
        self.k = scale(units)
        self.width, self.height = width*self.k, height*self.k
        return self
    
    def addpage(self):
        p = page(self)
        self.pages.append(p)
        return p
    
    def page(self, index):
        return self.pages[index]
    
    def pdf(self, path='', compress=False):
        data = pdfwriter.dump(self)
        return save(path, data)




