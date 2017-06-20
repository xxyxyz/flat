from copy import copy
from struct import calcsize, unpack_from




class readable(object):
    
    __slots__ = 'data', 'position'
    
    def __init__(self, data):
        self.data = data
        self.position = 0
    
    def clone(self):
        return copy(self)
    
    def jump(self, position):
        self.position = position
    
    def skip(self, length):
        self.position += length
    
    def peek(self, prefix):
        return self.data.startswith(prefix, self.position)
    
    def read(self, length):
        p = self.position
        self.position += length
        return self.data[p:self.position]
    
    def parse(self, fmt):
        p = self.position
        self.position += calcsize(fmt)
        return unpack_from(fmt, self.data, p)
    
    def uint8(self):
        p = self.position
        self.position += 1
        return self.data[p]
    
    def uint16(self):
        d, p = self.data, self.position
        self.position += 2
        return d[p] << 8 | d[p+1]
    
    def uint32(self):
        d, p = self.data, self.position
        self.position += 4
        return d[p] << 24 | d[p+1] << 16 | d[p+2] << 8 | d[p+3]
    
    def int8(self):
        t = self.uint8()
        return t - ((t & (1 << 7)) << 1)
    
    def int16(self):
        t = self.uint16()
        return t - ((t & (1 << 15)) << 1)
    
    def int32(self):
        t = self.uint32()
        return t - ((t & (1 << 31)) << 1)
    
    def uint16le(self):
        d, p = self.data, self.position
        self.position += 2
        return d[p] | d[p+1] << 8
    
    def uint32le(self):
        d, p = self.data, self.position
        self.position += 4
        return d[p] | d[p+1] << 8 | d[p+2] << 16 | d[p+3] << 24
    
    def int16le(self):
        t = self.uint16le()
        return t - ((t & (1 << 15)) << 1)
    
    def int32le(self):
        t = self.uint32le()
        return t - ((t & (1 << 31)) << 1)




