from .otf import otf




class font(object):
    
    @staticmethod
    def open(path, index=0):
        with open(path, 'rb') as f:
            data = f.read()
            if otf.valid(data):
                source = otf(data, index)
                return font(source)
            raise ValueError('Unsupported font format.')
    
    def __init__(self, source):
        self.source = source
        self.name = source.psname()
        self.density = source.density()
        self.ascender = source.ascender()
        self.descender = source.descender()
        self.charmap = source.charmap()
        self.advances = source.advances()
        self.kerning = source.kerning()
        self.glyphs = {}
    
    def glyph(self, index):
        if index not in self.glyphs:
            commands = self.source.glyph(index)
            for c in commands:
                c.transform(1, 0, 0, -1, 0, 0)
            self.glyphs[index] = commands
        return self.glyphs[index]
    
    def glyphmap(self):
        result = [(i, c) for c, i in self.charmap.items() if i != 0]
        result.sort()
        i = 0
        for j in range(1, len(result)):
            if result[i][0] != result[j][0]:
                i += 1
                if i < j:
                    result[i] = result[j]
        result[i+1:] = []
        return result




