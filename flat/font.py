
from .otf import otf
from .shape import path
from .utils import memoize




class font(object):
    
    @staticmethod
    def open(path, index=0):
        with open(path, 'rb') as f:
            data = f.read()
            if otf.valid(data):
                source = otf(data, index)
                return font(source)
            raise AssertionError('Unsupported font format.')
    
    def __init__(self, source):
        self.source = source
        self.name = source.psname()
        self.charmap = source.charmap()
        self.kerning = source.kerning()
        self.advances = source.advances()
        self.defaultadvance = source.defaultadvance()
        self.ascender = source.ascender()
        self.descender = source.descender()
        self.density = source.density()
    
    @memoize
    def glyph(self, index):
        commands = self.source.glyph(index)
        for c in commands:
            c.flip()
        return path(None, *commands)
    
    @memoize
    def glyph2(self, index, scale):
        return self.glyph(index).reduced(scale)
    
    @memoize
    def glyph3(self, index):
        return self.glyph(index).elevated()
    
    def relativewidth(self, string, left, size):
        charmap, kerning, advances = self.charmap, self.kerning, self.advances
        fix, first = 0.0, True
        result = 0.0
        for c in string:
            code = ord(c)
            if code in charmap:
                right = charmap[code]
                pair = kerning[left]
                if right in pair:
                    value = pair[right]
                    if first:
                        fix = value
                    else:
                        result -= value
                result += advances[right]
                left = right
            else:
                result += advances[0]
                left = 0
            first = False
        scale = size * self.density
        return fix * scale, result * scale, left




