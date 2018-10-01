from array import array
from struct import pack
from .readable import readable
from .misc import clamp




_z_z = bytes([ # Zig-zag indices of AC coefficients
         1,  8, 16,  9,  2,  3, 10, 17, 24, 32, 25, 18, 11,  4,  5,
    12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13,  6,  7, 14, 21, 28,
    35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51,
    58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63])




_luminance_quantization = bytes([ # Luminance quantization table in zig-zag order
    16, 11, 12, 14, 12, 10, 16, 14, 13, 14, 18, 17, 16, 19, 24, 40,
    26, 24, 22, 22, 24, 49, 35, 37, 29, 40, 58, 51, 61, 60, 57, 51,
    56, 55, 64, 72, 92, 78, 64, 68, 87, 69, 55, 56, 80,109, 81, 87,
    95, 98,103,104,103, 62, 77,113,121,112,100,120, 92,101,103, 99])
_chrominance_quantization = bytes([ # Chrominance quantization table in zig-zag order
    17, 18, 18, 24, 21, 24, 47, 26, 26, 47, 99, 66, 56, 66, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99])

_ld_lengths = bytes([ # Luminance DC code lengths
    0, 1, 5, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
_ld_values = bytes([ # Luminance DC values
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
_la_lengths = bytes([ # Luminance AC code lengths
    0, 2, 1, 3, 3, 2, 4, 3, 5, 5, 4, 4, 0, 0, 1, 125])
_la_values = bytes([ # Luminance AC values
      1,  2,  3,  0,  4, 17,  5, 18, 33, 49, 65,  6, 19, 81, 97,  7, 34,113,
     20, 50,129,145,161,  8, 35, 66,177,193, 21, 82,209,240, 36, 51, 98,114,
    130,  9, 10, 22, 23, 24, 25, 26, 37, 38, 39, 40, 41, 42, 52, 53, 54, 55,
     56, 57, 58, 67, 68, 69, 70, 71, 72, 73, 74, 83, 84, 85, 86, 87, 88, 89,
     90, 99,100,101,102,103,104,105,106,115,116,117,118,119,120,121,122,131,
    132,133,134,135,136,137,138,146,147,148,149,150,151,152,153,154,162,163,
    164,165,166,167,168,169,170,178,179,180,181,182,183,184,185,186,194,195,
    196,197,198,199,200,201,202,210,211,212,213,214,215,216,217,218,225,226,
    227,228,229,230,231,232,233,234,241,242,243,244,245,246,247,248,249,250])
_cd_lengths = bytes([ # Chrominance DC code lengths
    0, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
_cd_values = bytes([ # Chrominance DC values
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
_ca_lengths = bytes([ # Chrominance AC code lengths
    0, 2, 1, 2, 4, 4, 3, 4, 7, 5, 4, 4, 0, 1, 2, 119])
_ca_values = bytes([ # Chrominance AC values
      0,  1,  2,  3, 17,  4,  5, 33, 49,  6, 18, 65, 81,  7, 97,113, 19, 34,
     50,129,  8, 20, 66,145,161,177,193,  9, 35, 51, 82,240, 21, 98,114,209,
     10, 22, 36, 52,225, 37,241, 23, 24, 25, 26, 38, 39, 40, 41, 42, 53, 54,
     55, 56, 57, 58, 67, 68, 69, 70, 71, 72, 73, 74, 83, 84, 85, 86, 87, 88,
     89, 90, 99,100,101,102,103,104,105,106,115,116,117,118,119,120,121,122,
    130,131,132,133,134,135,136,137,138,146,147,148,149,150,151,152,153,154,
    162,163,164,165,166,167,168,169,170,178,179,180,181,182,183,184,185,186,
    194,195,196,197,198,199,200,201,202,210,211,212,213,214,215,216,217,218,
    226,227,228,229,230,231,232,233,234,242,243,244,245,246,247,248,249,250])




def _inverse_dct(block, q):
    # Ref.: Independent JPEG Group's "jidctint.c", v8d
    # Copyright (C) 1994-1996, Thomas G. Lane
    # Modification developed 2003-2009 by Guido Vollbeding
    for i in range(8):
        z2 = block[16+i]*q[16+i]
        z3 = block[48+i]*q[48+i]
        z1 = (z2 + z3)*4433 # FIX_0_541196100
        tmp2 = z1 + z2*6270 # FIX_0_765366865
        tmp3 = z1 - z3*15137 # FIX_1_847759065
        z2 = block[i]*q[i]
        z3 = block[32+i]*q[32+i]
        z2 <<= 13 # CONST_BITS
        z3 <<= 13
        z2 += 1024 # 1 << CONST_BITS-PASS1_BITS-1
        tmp0 = z2 + z3
        tmp1 = z2 - z3
        tmp10 = tmp0 + tmp2
        tmp13 = tmp0 - tmp2
        tmp11 = tmp1 + tmp3
        tmp12 = tmp1 - tmp3
        tmp0 = block[56+i]*q[56+i]
        tmp1 = block[40+i]*q[40+i]
        tmp2 = block[24+i]*q[24+i]
        tmp3 = block[8+i]*q[8+i]
        z2 = tmp0 + tmp2
        z3 = tmp1 + tmp3
        z1 = (z2 + z3)*9633 # FIX_1_175875602
        z2 = z2*-16069 # FIX_1_961570560
        z3 = z3*-3196 # FIX_0_390180644
        z2 += z1
        z3 += z1
        z1 = (tmp0 + tmp3)*-7373 # FIX_0_899976223
        tmp0 = tmp0*2446 # FIX_0_298631336
        tmp3 = tmp3*12299 # FIX_1_501321110
        tmp0 += z1 + z2
        tmp3 += z1 + z3
        z1 = (tmp1 + tmp2)*-20995 # FIX_2_562915447
        tmp1 = tmp1*16819 # FIX_2_053119869
        tmp2 = tmp2*25172 # FIX_3_072711026
        tmp1 += z1 + z3
        tmp2 += z1 + z2
        block[i] = (tmp10 + tmp3) >> 11 # CONST_BITS-PASS1_BITS
        block[56+i] = (tmp10 - tmp3) >> 11
        block[8+i] = (tmp11 + tmp2) >> 11
        block[48+i] = (tmp11 - tmp2) >> 11
        block[16+i] = (tmp12 + tmp1) >> 11
        block[40+i] = (tmp12 - tmp1) >> 11
        block[24+i] = (tmp13 + tmp0) >> 11
        block[32+i] = (tmp13 - tmp0) >> 11
    for i in range(0, 64, 8):
        z2 = block[2+i]
        z3 = block[6+i]
        z1 = (z2 + z3)*4433 # FIX_0_541196100
        tmp2 = z1 + z2*6270 # FIX_0_765366865
        tmp3 = z1 - z3*15137 # FIX_1_847759065
        z2 = block[i] + 16 # 1 << (PASS1_BITS+2)
        z3 = block[4+i]
        tmp0 = (z2 + z3) << 13 # CONST_BITS
        tmp1 = (z2 - z3) << 13
        tmp10 = tmp0 + tmp2
        tmp13 = tmp0 - tmp2
        tmp11 = tmp1 + tmp3
        tmp12 = tmp1 - tmp3
        tmp0 = block[7+i]
        tmp1 = block[5+i]
        tmp2 = block[3+i]
        tmp3 = block[1+i]
        z2 = tmp0 + tmp2
        z3 = tmp1 + tmp3
        z1 = (z2 + z3)*9633 # FIX_1_175875602
        z2 = z2*-16069 # FIX_1_961570560
        z3 = z3*-3196 # FIX_0_390180644
        z2 += z1
        z3 += z1
        z1 = (tmp0 + tmp3)*-7373 # FIX_0_899976223
        tmp0 = tmp0*2446 # FIX_0_298631336
        tmp3 = tmp3*12299 # FIX_1_501321110
        tmp0 += z1 + z2
        tmp3 += z1 + z3
        z1 = (tmp1 + tmp2)*-20995 # FIX_2_562915447
        tmp1 = tmp1*16819 # FIX_2_053119869
        tmp2 = tmp2*25172 # FIX_3_072711026
        tmp1 += z1 + z3
        tmp2 += z1 + z2
        block[i] = (tmp10 + tmp3) >> 18 # (CONST_BITS+PASS1_BITS+3)
        block[7+i] = (tmp10 - tmp3) >> 18
        block[1+i] = (tmp11 + tmp2) >> 18
        block[6+i] = (tmp11 - tmp2) >> 18
        block[2+i] = (tmp12 + tmp1) >> 18
        block[5+i] = (tmp12 - tmp1) >> 18
        block[3+i] = (tmp13 + tmp0) >> 18
        block[4+i] = (tmp13 - tmp0) >> 18

def _forward_dct(block):
    # Ref.: Independent JPEG Group's "jfdctint.c", v8d
    # Copyright (C) 1994-1996, Thomas G. Lane
    # Modification developed 2003-2009 by Guido Vollbeding
    for i in range(0, 64, 8):
        tmp0 = block[i] + block[i+7]
        tmp1 = block[i+1] + block[i+6]
        tmp2 = block[i+2] + block[i+5]
        tmp3 = block[i+3] + block[i+4]
        tmp10 = tmp0 + tmp3
        tmp12 = tmp0 - tmp3
        tmp11 = tmp1 + tmp2
        tmp13 = tmp1 - tmp2
        tmp0 = block[i] - block[i+7]
        tmp1 = block[i+1] - block[i+6]
        tmp2 = block[i+2] - block[i+5]
        tmp3 = block[i+3] - block[i+4]
        block[i] = (tmp10 + tmp11 - 8*128) << 2 # PASS1_BITS
        block[i+4] = (tmp10 - tmp11) << 2
        z1 = (tmp12 + tmp13)*4433 # FIX_0_541196100
        z1 += 1024 # 1 << (CONST_BITS-PASS1_BITS-1)
        block[i+2] = (z1 + tmp12*6270) >> 11 # FIX_0_765366865
        block[i+6] = (z1 - tmp13*15137) >> 11 # FIX_1_847759065
        tmp10 = tmp0 + tmp3
        tmp11 = tmp1 + tmp2
        tmp12 = tmp0 + tmp2
        tmp13 = tmp1 + tmp3
        z1 = (tmp12 + tmp13)*9633 # FIX_1_175875602
        z1 += 1024 # 1 << (CONST_BITS-PASS1_BITS-1)
        tmp0 = tmp0*12299 # FIX_1_501321110
        tmp1 = tmp1*25172 # FIX_3_072711026
        tmp2 = tmp2*16819 # FIX_2_053119869
        tmp3 = tmp3*2446 # FIX_0_298631336
        tmp10 = tmp10*-7373 # FIX_0_899976223
        tmp11 = tmp11*-20995 # FIX_2_562915447
        tmp12 = tmp12*-3196 # FIX_0_390180644
        tmp13 = tmp13*-16069 # FIX_1_961570560
        tmp12 += z1
        tmp13 += z1
        block[i+1] = (tmp0 + tmp10 + tmp12) >> 11
        block[i+3] = (tmp1 + tmp11 + tmp13) >> 11
        block[i+5] = (tmp2 + tmp11 + tmp12) >> 11
        block[i+7] = (tmp3 + tmp10 + tmp13) >> 11
    for i in range(8):
        tmp0 = block[i] + block[i+56]
        tmp1 = block[i+8] + block[i+48]
        tmp2 = block[i+16] + block[i+40]
        tmp3 = block[i+24] + block[i+32]
        tmp10 = tmp0 + tmp3 + 2 # 1 << (PASS1_BITS-1)
        tmp12 = tmp0 - tmp3
        tmp11 = tmp1 + tmp2
        tmp13 = tmp1 - tmp2
        tmp0 = block[i] - block[i+56]
        tmp1 = block[i+8] - block[i+48]
        tmp2 = block[i+16] - block[i+40]
        tmp3 = block[i+24] - block[i+32]
        block[i] = (tmp10 + tmp11) >> 2 # PASS1_BITS
        block[i+32] = (tmp10 - tmp11) >> 2
        z1 = (tmp12 + tmp13)*4433 # FIX_0_541196100
        z1 += 16384 # 1 << (CONST_BITS+PASS1_BITS-1)
        block[i+16] = (z1 + tmp12*6270) >> 15 # FIX_0_765366865, CONST_BITS+PASS1_BITS
        block[i+48] = (z1 - tmp13*15137) >> 15 # FIX_1_847759065
        tmp10 = tmp0 + tmp3
        tmp11 = tmp1 + tmp2
        tmp12 = tmp0 + tmp2
        tmp13 = tmp1 + tmp3
        z1 = (tmp12 + tmp13)*9633 # FIX_1_175875602
        z1 += 16384 # 1 << (CONST_BITS+PASS1_BITS-1)
        tmp0 = tmp0*12299 # FIX_1_501321110
        tmp1 = tmp1*25172 # FIX_3_072711026
        tmp2 = tmp2*16819 # FIX_2_053119869
        tmp3 = tmp3*2446 # FIX_0_298631336
        tmp10 = tmp10*-7373 # FIX_0_899976223
        tmp11 = tmp11*-20995 # FIX_2_562915447
        tmp12 = tmp12*-3196 # FIX_0_390180644
        tmp13 = tmp13*-16069 # FIX_1_961570560
        tmp12 += z1
        tmp13 += z1
        block[i+8] = (tmp0 + tmp10 + tmp12) >> 15 # CONST_BITS+PASS1_BITS
        block[i+24] = (tmp1 + tmp11 + tmp13) >> 15
        block[i+40] = (tmp2 + tmp11 + tmp12) >> 15
        block[i+56] = (tmp3 + tmp10 + tmp13) >> 15




def _parse_sof(readable, components):
    depth, height, width, n = readable.parse('>BHHB')
    if depth != 8:
        raise ValueError('Unsupported sample precision.')
    if n == 1:
        kind = 'g'
    elif n == 3:
        kind = 'rgb'
    elif n == 4:
        kind = 'cmyk'
    else:
        ValueError('Unsupported color type.')
    for i in range(n):
        identifier, sampling, destination = readable.parse('>BBB')
        h, v = sampling >> 4, sampling & 15
        if h not in (1, 2, 4):
            raise ValueError('Invalid horizontal sampling factor.')
        if v not in (1, 2, 4):
            raise ValueError('Invalid vertical sampling factor.')
        if i > 0:
            if h != 1 or v != 1:
                raise ValueError('Unsupported sampling factor.')
        if n == 1:
            h, v = 1, 1
        components.append(_frame_component(identifier, h, v, destination))
    return width, height, kind, n

def _parse_dqt(readable, length, qtables):
    end = readable.position + length
    while readable.position < end:
        pqtq = readable.uint8()
        precision, destination = pqtq >> 4, pqtq & 15
        if precision != 0:
            raise ValueError('Unsuported qtable element precision.')
        if destination >= 4:
            raise ValueError('Invalid qtable destination identifier.')
        elements = readable.read(64)
        table = bytearray(64)
        table[0] = elements[0]
        i = 1
        for z in _z_z:
            table[z] = elements[i]
        qtables[destination] = table
    if readable.position != end:
        raise ValueError('Invalid DQT length.')

def _parse_dht(readable, length, htables):
    end = readable.position + length
    while readable.position < end:
        tcth = readable.uint8()
        kind, identifier = tcth >> 4, tcth & 15
        if kind >= 2:
            raise ValueError('Invalid htable class.')
        if identifier >= 2:
            raise ValueError('Unsupported htable destination identifier.')
        lengths = readable.read(16)
        values = readable.read(sum(lengths))
        htables[tcth] = _huffman_cache(lengths, values)
    if readable.position != end:
        raise ValueError('Invalid DHT length.')

def _parse_sos(readable, scans):
    n = readable.uint8()
    for i in range(n):
        selector, destinations = readable.parse('>BB')
        dc, ac = destinations >> 4, destinations & 15
        scans[selector] = _coding_destination(dc, 16|ac) # ACs always have Tc == 1
    readable.skip(3) # start, end, approximation

def _parse_dri(readable):
    interval = readable.uint16()
    return interval

def _parse_app1(readable, length, rotation):
    end = readable.position + length
    if readable.peek(b'Exif\0\0'):
        readable.skip(5 + 1) # header, padding
        order = readable.uint16()
        if order == 0x4d4d: # MM
            uint16, uint32 = readable.uint16, readable.uint32
        elif order == 0x4949: # II
            uint16, uint32 = readable.uint16le, readable.uint32le
        else:
            raise ValueError('Invalid byte order.')
        readable.skip(2) # 42
        offset = uint32()
        if offset < 8:
            raise ValueError('Invalid IFD0 offset.')
        readable.skip(offset - 8)
        n = uint16()
        for i in range(n):
            tag = uint16()
            readable.skip(2 + 4) # kind, size
            if tag == 0x112: # orientation
                orientation = uint16()
                if orientation < 1 or orientation > 8:
                    raise ValueError('Invalid orientation value.')
                if orientation == 1:
                    rotation = 0
                elif orientation == 6:
                    rotation = 90
                elif orientation == 3:
                    rotation = 180
                elif orientation == 8:
                    rotation = 270
                else:
                    raise ValueError('Unsupported orientation value.')
                break
            readable.skip(4) # value
    readable.jump(end)
    return rotation

def _parse_app14(readable):
    readable.skip(6 + 1 + 2 + 2) # tag, version, flags0, flags1
    transform = readable.uint8()
    return transform

class _frame_component(object):
    
    __slots__ = 'identifier', 'h', 'v', 'destination'
    
    def __init__(self, identifier, h, v, destination):
        self.identifier, self.h, self.v, self.destination = identifier, h, v, destination

class _coding_destination(object):
    
    __slots__ = 'dc', 'ac'
    
    def __init__(self, dc, ac):
        self.dc, self.ac = dc, ac

class _huffman_cache(object):
    
    def __init__(self, lengths, values):
        self.values = values
        self.offsets = offsets = array('H', [0])
        self.sizes = sizes = bytearray([255]*65536)
        code = index = 0
        size = 1
        for length in lengths:
            offsets.append(code - index)
            for i in range(length):
                hi = code << (16 - size)
                for lo in range(1 << (16 - size)):
                    sizes[hi|lo] = size
                code += 1
            code *= 2
            index += length
            size += 1

class _entropy_decoder(object):
    
    def __init__(self, readable):
        self.readable = readable
        self.value = 0
        self.length = 0
        self.rst = 0
    
    def restart(self):
        marker = self.readable.uint16()
        if marker != 0xffd0 + self.rst:
            raise ValueError('Invalid RST marker.')
        self.value = 0
        self.length = 0
        self.rst = (self.rst + 1) & 7
    
    def fill(self, length):
        while True:
            byte = self.readable.uint8()
            self.value = ((self.value & 0xffff) << 8) | byte
            self.length += 8
            if byte == 0xff:
                byte = self.readable.uint8()
                if byte != 0:
                    self.readable.position -= 2
            if self.length >= length:
                break
    
    def decodehuffman(self, cache):
        if self.length < 16:
            self.fill(16)
        key = (self.value >> (self.length - 16)) & 0xffff
        size = cache.sizes[key]
        if size == 255:
            raise ValueError('Corrupted Huffman sequence.')
        code = (self.value >> (self.length - size)) & ((1 << size) - 1)
        self.length -= size
        return cache.values[code - cache.offsets[size]]
    
    def receiveextend(self, length):
        if self.length < length:
            self.fill(length)
        value = (self.value >> (self.length - length)) & ((1 << length) - 1)
        self.length -= length
        if value < 1 << (length - 1):
            return value - (1 << length) + 1
        return value
    
    def decode(self, previous, block, q, dc, ac):
        i = 0
        while i < 64:
            block[i] = block[i + 1] = block[i + 2] = block[i + 3] = 0
            i += 4
        t = self.decodehuffman(dc)
        d = 0 if t == 0 else self.receiveextend(t)
        previous += d
        block[0] = previous
        i = 0
        while i < 63:
            rs = self.decodehuffman(ac)
            s = rs & 15
            r = rs >> 4
            if s == 0:
                if r != 15:
                    break
                i += 16
            else:
                i += r
                block[_z_z[i]] = self.receiveextend(s)
                i += 1
        _inverse_dct(block, q)
        return previous




def _quantization_table(table, quality):
    quality = max(0, min(quality, 100))
    if quality < 50:
        q = 5000//quality
    else:
        q = 200 - quality*2
    return bytes([max(1, min((i*q + 50)//100, 255)) for i in table])

def _huffman_table(lengths, values):
    table = [None]*(max(values) + 1)
    code = 0
    i = 0
    size = 1
    for a in lengths:
        for j in range(a):
            table[values[i]] = code, size
            code += 1
            i += 1
        code *= 2
        size += 1
    return table

def _scale_factor(table):
    factor = [0]*64
    factor[0] = table[0]*8
    i = 1
    for z in _z_z:
        factor[z] = table[i]*8
        i += 1
    return factor

def _marker_segment(marker, data):
    return b'\xff' + marker + pack('>H', len(data) + 2) + data

class _entropy_encoder(object):
    
    def __init__(self):
        c = [i for j in reversed(range(16)) for i in range(1 << j)]
        s = [j for j in range(1, 16) for i in range(1 << (j - 1))]
        s = [0] + s + list(reversed(s))
        self.codes, self.sizes = c, s
        self.value, self.length = 0, 0
        self.data = bytearray()
    
    def encode(self, previous, block, scale, dc, ac):
        _forward_dct(block)
        for i in range(64):
            block[i] = (((block[i] << 1)//scale[i]) + 1) >> 1
        d = block[0] - previous
        if d == 0:
            self.write(*dc[0])
        else:
            s = self.sizes[d]
            self.write(*dc[s])
            self.write(self.codes[d], s)
        n = 0
        for i in _z_z:
            if block[i] == 0:
                n += 1
            else:
                while n > 15:
                    self.write(*ac[0xf0])
                    n -= 16
                s = self.sizes[block[i]]
                self.write(*ac[n*16 + s])
                self.write(self.codes[block[i]], s)
                n = 0
        if n > 0:
            self.write(*ac[0])
        return block[0]
    
    def write(self, value, length):
        data = self.data
        value += (self.value << length)
        length += self.length
        while length > 7:
            length -= 8
            v = (value >> length) & 0xff
            if v == 0xff:
                data.append(0xff)
                data.append(0)
            else:
                data.append(v)
        self.value = value & 0xff
        self.length = length
    
    def dump(self):
        return self.data




class jpeg(object):
    
    @staticmethod
    def valid(data):
        return data.startswith(b'\xff\xd8\xff')
    
    def __init__(self, data):
        self.readable = r = readable(data)
        self.width, self.height, self.kind, self.n = 0, 0, '', 0
        self.components = []
        self.scans = {}
        self.qtables = {}
        self.htables = {}
        self.interval = 0
        self.rotation = 0
        self.progressive = False
        self.transform, app14 = False, False
        self.ecs = 0
        r.skip(2) # SOI
        while True:
            marker = r.uint8()
            if marker != 0xff:
                raise ValueError('Invalid marker.')
            while marker == 0xff:
                marker = r.uint8()
            if marker == 0xd9: # EOI
                raise ValueError('Invalid entropy-coded segment.')
            if 0xd0 <= marker <= 0xd7: # RST
                raise ValueError('Unexpected RST marker.')
            length = r.uint16() - 2
            if 0xc0 <= marker <= 0xc2: # SOF0, SOF1, SOF2
                self.width, self.height, self.kind, self.n = _parse_sof(r, self.components)
                self.progressive = marker == 0xc2
                if not app14:
                    self.transform = self.kind == 'rgb'
            elif marker == 0xdb: # DQT
                _parse_dqt(r, length, self.qtables)
            elif marker == 0xc4: # DHT
                _parse_dht(r, length, self.htables)
            elif marker == 0xda: # SOS:
                _parse_sos(r, self.scans)
                self.ecs = r.position
                break
            elif marker == 0xdd: # DRI
                self.interval = _parse_dri(r)
            elif marker == 0xe1: # APP1
                self.rotation = _parse_app1(r, length, self.rotation)
            elif marker == 0xee: # APP14
                self.transform, app14 = _parse_app14(r), True
            elif 0xe0 <= marker <= 0xef or marker == 0xfe: # APP, COM
                r.skip(length)
            else:
                if marker == 0xc3: # SOF3
                    raise ValueError('Lossless mode not supported.')
                if 0xc5 <= marker == 0xc7: # SOF5, SOF6, SOF7
                    raise ValueError('Differential mode not supported.')
                if 0xc8 <= marker == 0xcf: # JPG, SOF9, SOF10, SOF11, DAC, SOF13, SOF14, SOF15
                    raise ValueError('Arithmetic coding not supported.')
                if marker == 0xdc: # DNL
                    raise ValueError('Define number of lines not supported.')
                if marker == 0xde: # DHP
                    raise ValueError('Define hierarchical progression not supported.')
                if marker == 0xdf: # EXP
                    raise ValueError('Expand reference component(s) not supported.')
                raise ValueError('Unsupported marker.')
    
    def decompress(self):
        if not self.components:
            raise ValueError('Missing SOF segment.')
        if not self.scans:
            raise ValueError('Missing SOS segment.')
        if not self.qtables:
            raise ValueError('Missing DQT segment.')
        if not self.htables:
            raise ValueError('Missing DHT segment.')
        if self.progressive:
            raise ValueError('Progressive DCT not supported.')
        self.readable.jump(self.ecs)
        w, h, n = self.width, self.height, self.n
        interval, transform = self.interval, self.transform
        d = _entropy_decoder(self.readable)
        data = bytearray(w*h*n)
        predictions = [0, 0, 0, 0]
        ublock, vblock, kblock = [0]*64, [0]*64, [0]*64
        yblocks = [0]*64, [0]*64, [0]*64, [0]*64
        blocks = [yblocks, [ublock], [vblock], [kblock]]
        hs = [c.h for c in self.components]
        vs = [c.v for c in self.components]
        qs = [self.qtables[c.destination] for c in self.components]
        dcs = [self.htables[self.scans[c.identifier].dc] for c in self.components]
        acs = [self.htables[self.scans[c.identifier].ac] for c in self.components]
        h0, v0 = hs[0], vs[0]
        hb, vb = h0.bit_length()-1, v0.bit_length()-1
        count = 0
        if interval == 0:
            interval = ((w + 8*h0 - 1)//(8*h0))*((h + 8*v0 - 1)//(8*v0))
        for y in range(0, h, 8*v0):
            for x in range(0, w, 8*h0):
                count += 1
                if count > interval:
                    d.restart()
                    predictions[:] = [0, 0, 0, 0]
                    count = 1
                for i in range(n):
                    for j in range(hs[i]*vs[i]):
                        predictions[i] = d.decode(predictions[i], blocks[i][j], qs[i], dcs[i], acs[i])
                for sy in range(v0):
                    for sx in range(h0):
                        yblock = yblocks[sx + sy*h0]
                        for by in range(min(8, h - y - sy*8)):
                            for bx in range(min(8, w - x - sx*8)):
                                i = ((sx*8 + bx) >> hb) + ((sy*8 + by) >> vb)*8
                                j = (x + sx*8 + bx + (y + sy*8 + by)*w)*n
                                if n == 1:
                                    data[j] = clamp(yblock[i] + 128)
                                elif n == 3:
                                    t, u, v = yblock[bx + by*8], ublock[i], vblock[i]
                                    t = (t << 16) + 8421376
                                    data[j] = clamp((t + 91881*v) >> 16)
                                    data[j + 1] = clamp((t - 22554*u - 46802*v) >> 16)
                                    data[j + 2] = clamp((t + 116130*u) >> 16)
                                else: # n == 4
                                    t, u, v, k = yblock[bx + by*8], ublock[i], vblock[i], kblock[i]
                                    if transform:
                                        t = (t << 16) + 8421376
                                        data[j] = 255 - clamp((t + 91881*v) >> 16)
                                        data[j + 1] = 255 - clamp((t - 22554*u - 46802*v) >> 16)
                                        data[j + 2] = 255 - clamp((t + 116130*u) >> 16)
                                        data[j + 3] = clamp(k + 128)
                                    else:
                                        data[j] = clamp(t + 128)
                                        data[j + 1] = clamp(u + 128)
                                        data[j + 2] = clamp(v + 128)
                                        data[j + 3] = clamp(k + 128)
        if not self.readable.peek(b'\xff\xd9'): # EOI
            raise ValueError('Missing EOI segment.')
        return data




def serialize(image, quality):
    if image.kind not in ('g', 'rgb', 'cmyk'):
        raise ValueError('Invalid image kind.')
    w, h, n, data = image.width, image.height, image.n, image.data
    ydc = udc = vdc = kdc = 0
    yblock, ublock, vblock, kblock = [0]*64, [0]*64, [0]*64, [0]*64
    lq = _quantization_table(_luminance_quantization, quality)
    ld = _huffman_table(_ld_lengths, _ld_values)
    la = _huffman_table(_la_lengths, _la_values)
    ls = _scale_factor(lq)
    if n == 3:
        cq = _quantization_table(_chrominance_quantization, quality)
        cd = _huffman_table(_cd_lengths, _cd_values)
        ca = _huffman_table(_ca_lengths, _ca_values)
        cs = _scale_factor(cq)
    e = _entropy_encoder()
    for y in range(0, h, 8):
        for x in range(0, w, 8):
            i = 0
            for yy in range(y, y + 8):
                for xx in range(x, x + 8):
                    j = (min(xx, w - 1) + min(yy, h - 1)*w)*n
                    if n == 1:
                        yblock[i] = data[j]
                    elif n == 3:
                        r, g, b = data[j], data[j + 1], data[j + 2]
                        yblock[i] = (19595*r + 38470*g + 7471*b + 32768) >> 16
                        ublock[i] = (-11056*r - 21712*g + 32768*b + 8421376) >> 16
                        vblock[i] = (32768*r - 27440*g - 5328*b + 8421376) >> 16
                    else: # n == 4
                        yblock[i] = data[j]
                        ublock[i] = data[j + 1]
                        vblock[i] = data[j + 2]
                        kblock[i] = data[j + 3]
                    i += 1
            ydc = e.encode(ydc, yblock, ls, ld, la)
            if n == 3:
                udc = e.encode(udc, ublock, cs, cd, ca)
                vdc = e.encode(vdc, vblock, cs, cd, ca)
            elif n == 4:
                udc = e.encode(udc, ublock, ls, ld, la)
                vdc = e.encode(vdc, vblock, ls, ld, la)
                kdc = e.encode(kdc, kblock, ls, ld, la)
    e.write(0x7f, 7) # padding
    app = b'Adobe\0\144\200\0\0\0\0' # tag, version, flags0, flags1, transform
    sof = b'\10' + pack('>HHB', h, w, n) + b'\1\21\0' # depth, id, sampling, qtable
    sos = pack('B', n) + b'\1\0' # id, htable
    dqt = b'\0' + lq
    dht = b'\0' + _ld_lengths + _ld_values + b'\20' + _la_lengths + _la_values
    if n == 3:
        sof += b'\2\21\1\3\21\1'
        sos += b'\2\21\3\21'
        dqt += b'\1' + cq
        dht += b'\1' + _cd_lengths + _cd_values + b'\21' + _ca_lengths + _ca_values
    elif n == 4:
        sof += b'\2\21\0\3\21\0\4\21\0'
        sos += b'\2\0\3\0\4\0'
    sos += b'\0\77\0' # start, end, approximation
    return b''.join([
        b'\xff\xd8', # SOI
        _marker_segment(b'\xee', app) if n == 4 else b'',
        _marker_segment(b'\xdb', dqt),
        _marker_segment(b'\xc0', sof),
        _marker_segment(b'\xc4', dht),
        _marker_segment(b'\xda', sos),
        e.dump(),
        b'\xff\xd9']) # EOI




