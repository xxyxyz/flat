from __future__ import division
from struct import Struct
from zlib import compress, crc32, decompress
from .readable import readable




def _paeth_predictor(a, b, c):
    pa = abs(b - c)
    pb = abs(a - c)
    pc = abs(a + b - c - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c

def _adaptive_filtering(image):
    wn, n = image.width*image.n, image.n
    s, t = bytearray(wn), bytearray(wn)
    previous = bytearray(wn)
    cache = [i if i < 128 else 256-i for i in range(256)]
    content = []
    for y in range(image.height):
        offset = y*wn
        row = image.data[offset:offset+wn]
        
        minimum = 0 # none
        for v in row:
            minimum += cache[v]
        code, scanline = '\0', row
        
        m = 0 # sub
        for i in range(0, n):
            s[i] = v = row[i]
            m += cache[v]
        for i in range(n, wn):
            s[i] = v = (row[i] - row[i - n]) & 0xff
            m += cache[v]
            if m >= minimum:
                break
        else:
            minimum = m
            code, scanline = '\1', s
            s, t = t, s
        
        m = 0 # up
        for i in range(0, wn):
            s[i] = v = (row[i] - previous[i]) & 0xff
            m += cache[v]
            if m >= minimum:
                break
        else:
            minimum = m
            code, scanline = '\2', s
            s, t = t, s
        
        m = 0 # average
        for i in range(0, n):
            s[i] = v = (row[i] - previous[i]//2) & 0xff
            m += cache[v]
        for i in range(n, wn):
            s[i] = v = (row[i] - (row[i - n] + previous[i])//2) & 0xff
            m += cache[v]
            if m >= minimum:
                break
        else:
            minimum = m
            code, scanline = '\3', s
            s, t = t, s
        
        m = 0 # paeth
        for i in range(0, n):
            s[i] = v = (row[i] - previous[i]) & 0xff
            m += cache[v]
        for i in range(n, wn):
            a, b, c = row[i - n], previous[i], previous[i - n]
            s[i] = v = (row[i] - _paeth_predictor(a, b, c)) & 0xff
            m += cache[v]
            if m >= minimum:
                break
        else:
            code, scanline = '\4', s
        
        content.append(code)
        content.append(bytes(scanline)) # TODO python 3: remove bytes
        previous = row
    return ''.join(content)




class png(object):
    
    @staticmethod
    def valid(data):
        return data.startswith('\x89PNG\r\n\x1a\n')
    
    def __init__(self, data):
        self.readable = r = readable(data)
        r.skip(8) # header
        length, name = r.parse('>L4s')
        if length != 13 or name != 'IHDR':
            raise ValueError('Invalid IHDR chunk.')
        self.width, self.height, \
            depth, color, compression, fltr, interlace = r.parse('>LLBBBBB') # IHDR
        if depth != 8:
            raise ValueError('Unsupported bit depth.')
        if color == 0:
            self.kind, self.n = 'g', 1
        elif color == 4:
            self.kind, self.n = 'ga', 2
        elif color == 2:
            self.kind, self.n = 'rgb', 3
        elif color == 6:
            self.kind, self.n = 'rgba', 4
        else:
            raise ValueError('Unsupported color type.')
        if compression != 0:
            raise ValueError('Invalid compression method.')
        if fltr != 0:
            raise ValueError('Invalid filter method.')
        if interlace != 0:
            raise ValueError('Unsupported interlace method.')
    
    def idat(self):
        r = self.readable
        r.jump(8 + 4 + 4 + 13 + 4) # header, length, name, IHDR, CRC
        parts = []
        while True:
            length, name = r.parse('>L4s')
            if name == 'IEND':
                break
            if name == 'IDAT':
                parts.append(r.read(length))
            else:
                r.skip(length)
            r.skip(4) # CRC
        return bytearray().join(parts)
    
    def decompress(self):
        wn, n = self.width*self.n, self.n
        content = bytearray(decompress(bytes(self.idat()))) # TODO python 3: remove bytearray/bytes
        if (wn + 1)*self.height != len(content):
            raise ValueError('Invalid content length.')
        rows = []
        previous = bytearray(wn)
        for y in range(self.height):
            offset = y*(wn + 1)
            kind = content[offset]
            row = content[offset+1:offset+(wn + 1)]
            if kind == 0: # none
                pass
            elif kind == 1: # sub
                for i in range(n, wn):
                    row[i] = (row[i] + row[i - n]) & 0xff
            elif kind == 2: # up
                for i in range(wn):
                    row[i] = (row[i] + previous[i]) & 0xff
            elif kind == 3: # average
                for i in range(0, n):
                    row[i] = (row[i] + previous[i]//2) & 0xff
                for i in range(n, wn):
                    row[i] = (row[i] + (row[i - n] + previous[i])//2) & 0xff
            elif kind == 4: # paeth
                for i in range(0, n):
                    row[i] = (row[i] + previous[i]) & 0xff
                for i in range(n, wn):
                    a, b, c = row[i - n], previous[i], previous[i - n]
                    row[i] = (row[i] + _paeth_predictor(a, b, c)) & 0xff
            else:
                raise ValueError('Invalid filter method.')
            rows.append(row)
            previous = row
        return bytearray().join(rows)




def serialize(image, optimized):
    if image.kind not in ('g', 'ga', 'rgb', 'rgba'):
        raise ValueError('Invalid image kind.')
    L = Struct('>L').pack # unsigned long
    color = '\0\4\2\6'[image.n - 1]
    ihdr = L(image.width) + L(image.height) + '\10' + color + '\0\0\0'
    if optimized:
        content = _adaptive_filtering(image)
    else:
        parts = []
        wn, n = image.width*image.n, image.n
        for y in range(image.height):
            offset = y*wn
            parts.append('\0')
            parts.append(bytes(image.data[offset:offset+wn])) # TODO python 3: remove bytes
        content = ''.join(parts)
    idat = compress(content, 9 if optimized else 6)
    return ''.join((
        '\x89PNG\r\n\x1a\n',
        L(len(ihdr)), 'IHDR', ihdr, L(crc32(ihdr, crc32('IHDR')) & 0xffffffff),
        L(len(idat)), 'IDAT', idat, L(crc32(idat, crc32('IDAT')) & 0xffffffff),
        L(0), 'IEND', L(crc32('IEND') & 0xffffffff)))




