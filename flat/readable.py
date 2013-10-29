
from struct import calcsize, unpack_from




class readable(object):
    
    def __init__(self, data):
        self.data = data
        self.position = 0
    
    def jump(self, position):
        self.position = position
    
    def skip(self, length):
        self.position += length
    
    def read(self, length):
        p = self.position
        self.position += length
        return self.data[p:self.position]
    
    def parse(self, fmt):
        p = self.position
        self.position += calcsize(fmt)
        return unpack_from(fmt, self.data, p)
    
    def int8(self):
        p = self.position
        self.position += 1
        temp = ord(self.data[p]) # TODO python 3: remove ord()
        return temp - ((temp & (1 << 7)) << 1)
    
    def uint8(self):
        p = self.position
        self.position += 1
        return ord(self.data[p]) # TODO python 3: remove ord()
    
    def int16(self):
        d, p = self.data, self.position
        self.position += 2
        temp = (ord(d[p]) << 8) + ord(d[p+1]) # TODO python 3: remove ord()
        return temp - ((temp & (1 << 15)) << 1)
    
    def uint16(self):
        d, p = self.data, self.position
        self.position += 2
        return (ord(d[p]) << 8) + ord(d[p+1]) # TODO python 3: remove ord()
    
    def int32(self):
        d, p = self.data, self.position
        self.position += 4
        temp = (ord(d[p]) << 24) + (ord(d[p+1]) << 16) + (ord(d[p+2]) << 8) + ord(d[p+3]) # TODO python 3: remove ord()
        return temp - ((temp & (1 << 31)) << 1)
    
    def uint32(self):
        d, p = self.data, self.position
        self.position += 4
        return (ord(d[p]) << 24) + (ord(d[p+1]) << 16) + (ord(d[p+2]) << 8) + ord(d[p+3]) # TODO python 3: remove ord()




