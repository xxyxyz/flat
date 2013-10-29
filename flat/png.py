
from struct import Struct
from zlib import compress, crc32, decompress

from .readable import readable




def _paeth(a, b, c):
    pa = abs(b - c)
    pb = abs(a - c)
    pc = abs(a + b - c - c)
    if pa <= pb and pa <= pc:
        return a
    else:
        return b if pb <= pc else c


def _heuristic(image):
    
    n = image.count
    w = image.width * n
    
    cache = [i if i < 128 else 256-i for i in range(256)]
    
    type1, type2, type3, type4 = (bytearray(w) for i in range(4))
    
    content = []
    previous = bytearray(w)
    
    for row in image.rows:
        
        minimum = 0 # up
        for i in range(0, w):
            type2[i] = (row[i] - previous[i]) & 0xff
            minimum += cache[type2[i]]
        code, scanline = '\2', type2
        
        m = 0 # none
        for i in range(0, w):
            m += cache[row[i]]
            if m >= minimum:
                break
        else:
            minimum = m
            code, scanline = '\0', row
        
        m = 0 # sub
        for i in range(0, n):
            type1[i] = row[i]
            m += cache[type1[i]]
        for i in range(n, w):
            type1[i] = (row[i] - row[i - n]) & 0xff
            m += cache[type1[i]]
            if m >= minimum:
                break
        else:
            minimum = m
            code, scanline = '\1', type1
        
        m = 0 # average
        for i in range(0, n):
            type3[i] = (row[i] - previous[i] // 2) & 0xff
            m += cache[type3[i]]
        for i in range(n, w):
            type3[i] = (row[i] - (row[i - n] + previous[i]) // 2) & 0xff
            m += cache[type3[i]]
            if m >= minimum:
                break
        else:
            minimum = m
            code, scanline = '\3', type3
        
        m = 0 # paeth
        for i in range(0, n):
            type4[i] = (row[i] - previous[i]) & 0xff
            m += cache[type4[i]]
        for i in range(n, w):
            type4[i] = (row[i] - _paeth(
                row[i - n], previous[i], previous[i - n])) & 0xff
            m += cache[type4[i]]
            if m >= minimum:
                break
        else:
            code, scanline = '\4', type4
        
        content.extend((code, str(scanline))) # TODO python 3: remove str
        
        previous = row
    
    return ''.join(content)




class png(object):
    
    @staticmethod
    def valid(data):
        return data.startswith('\x89PNG\r\n\x1a\n')
    
    def __init__(self, data):
        self.data = data
        r = readable(data)
        head, ihdr = '>L4s', '>LLBBBBBL'
        
        r.skip(8) # header
        length, name = r.parse(head)
        assert name == 'IHDR', 'Invalid chunk found.'
        self.width, self.height, self.depth, \
            color, compression, fltr, interlace, crc = r.parse(ihdr)
        assert self.depth == 8, 'Unsupported bit depth.'
        assert color in (0, 2, 4, 6), 'Unsupported color type.'
        assert compression == 0, 'Invalid compression method.'
        assert fltr == 0, 'Invalid filter method.'
        assert interlace == 0, 'Unsupported interlace method.'
        self.kind, self.count = \
            ('g', 1) if color == 0 else \
            ('ga', 2) if color == 4 else \
            ('rgb', 3) if color == 2 else ('rgba', 4)
        
        self.idats = []
        while True:
            length, name = r.parse(head)
            if name == 'IDAT':
                self.idats.append((r.position, r.position+length))
            elif name == 'IEND':
                break
            r.skip(length + 4) # crc
    
    def idat(self):
        return ''.join(self.data[s:e] for s,e in self.idats)
    
    def decompress(self):
        content = decompress(self.idat())
        n = self.count
        w, w1 = self.width * n, self.width * n + 1
        assert w1 * self.height == len(content), 'Invalid content length.'
        rows = []
        previous = bytearray(w)
        for offset in range(0, self.height * w1, w1):
            kind = ord(content[offset])
            row = bytearray(content[offset+1:offset+w1])
            if kind == 0: # none
                pass
            elif kind == 1: # sub
                for i in range(n, w):
                    row[i] = (row[i] + row[i - n]) & 0xff
            elif kind == 2: # up
                for i in range(w):
                    row[i] = (row[i] + previous[i]) & 0xff
            elif kind == 3: # average
                for i in range(0, n):
                    row[i] = (row[i] + previous[i] // 2) & 0xff
                for i in range(n, w):
                    row[i] = (row[i] + (row[i - n] + previous[i]) // 2) & 0xff
            elif kind == 4: # paeth
                for i in range(0, n):
                    row[i] = (row[i] + previous[i]) & 0xff
                for i in range(n, w):
                    row[i] = (row[i] + _paeth(
                        row[i - n], previous[i], previous[i - n])) & 0xff
            else:
                raise AssertionError('Invalid filter method.')
            rows.append(row)
            previous = row
        return rows
    
    @staticmethod
    def dump(image, optimized):
        assert image.kind in ('g', 'ga', 'rgb', 'rgba'), 'Invalid image kind.'
        L = Struct('>L').pack # unsigned long
        color = ('\0', '\4', '\2', '\6')[image.count - 1]
        ihdr = L(image.width) + L(image.height) + '\10' + color + '\0\0\0'
        if optimized:
            content = _heuristic(image)
        else:
            content = '\0'.join(map(str, [''] + image.rows)) # TODO python 3: remove str
        idat = compress(content, 9 if optimized else 6)
        return ''.join((
            '\x89PNG\r\n\x1a\n',
            L(len(ihdr)), 'IHDR', ihdr, L(crc32(ihdr, crc32('IHDR')) & 0xffffffff),
            L(len(idat)), 'IDAT', idat, L(crc32(idat, crc32('IDAT')) & 0xffffffff),
            L(0), 'IEND', L(crc32('IEND') & 0xffffffff)))




