from .misc import save, scale
from .pdf import serialize as pdfserialize
from .rasterizer import rasterizer
from .svg import serialize as svgserialize




class page(object):
    
    __slots__ = 'title', 'k', 'width', 'height', 'items'
    
    def __init__(self, document):
        self.title = document.title
        self.k = document.k
        self.width, self.height = document.width, document.height
        self.items = []
    
    def meta(self, title):
        self.title = title
        return self
    
    def size(self, width, height, units='mm'):
        self.k = scale(units)
        self.width, self.height = width*self.k, height*self.k
        return self
    
    def place(self, item):
        entity = item.placed(self.k)
        self.items.append(entity)
        return entity
    
    def chain(self, block):
        block = block.chained(self.k)
        self.items.append(block)
        return block
    
    def svg(self, path='', compress=False):
        data = svgserialize(self, compress)
        return save(path, data)
    
    def image(self, ppi=72, kind='g'):
        k = ppi/72.0
        w, h = int(self.width*k + 0.5), int(self.height*k + 0.5)
        r = rasterizer(w, h, kind)
        for item in self.items:
            item.rasterize(r, k, 0.0, 0.0)
        return r.image




class document(object):
    
    __slots__ = 'title', 'k', 'width', 'height', 'pages'
    
    @staticmethod
    def open(path):
        raise NotImplementedError
    
    def __init__(self, width=210.0, height=297.0, units='mm'):
        self.meta('Untitled')
        self.size(width, height, units)
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
    
    def pdf(self, path='', compress=False, bleed=False, cropmarks=False):
        data = pdfserialize(self, compress, bleed, cropmarks)
        return save(path, data)




