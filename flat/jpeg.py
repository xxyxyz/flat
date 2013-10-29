
from struct import Struct

from .readable import readable
from .utils import chunks, clamp, record




def _idct(block, q):
    # Based on Independent JPEG Group's "jidctint.c", v8d
    # Copyright (C) 1994-1996, Thomas G. Lane
    # Modification developed 2003-2009 by Guido Vollbeding
    
    for i in range(8):
        z2 = block[16+i] * q[16+i]
        z3 = block[48+i] * q[48+i]
        
        z1 = (z2 + z3) * 4433 # FIX_0_541196100
        tmp2 = z1 + z2 * 6270 # FIX_0_765366865
        tmp3 = z1 - z3 * 15137 # FIX_1_847759065
        
        z2 = block[i] * q[i]
        z3 = block[32+i] * q[32+i]
        z2 <<= 13 # CONST_BITS
        z3 <<= 13
        z2 += 1024 # 1 << CONST_BITS-PASS1_BITS-1
        
        tmp0 = z2 + z3
        tmp1 = z2 - z3
        
        tmp10 = tmp0 + tmp2
        tmp13 = tmp0 - tmp2
        tmp11 = tmp1 + tmp3
        tmp12 = tmp1 - tmp3
        
        tmp0 = block[56+i] * q[56+i]
        tmp1 = block[40+i] * q[40+i]
        tmp2 = block[24+i] * q[24+i]
        tmp3 = block[8+i] * q[8+i]
        
        z2 = tmp0 + tmp2
        z3 = tmp1 + tmp3
        
        z1 = (z2 + z3) * 9633 # FIX_1_175875602
        z2 = z2 * -16069 # FIX_1_961570560
        z3 = z3 * -3196 # FIX_0_390180644
        z2 += z1
        z3 += z1
        
        z1 = (tmp0 + tmp3) * -7373 # FIX_0_899976223
        tmp0 = tmp0 * 2446 # FIX_0_298631336
        tmp3 = tmp3 * 12299 # FIX_1_501321110
        tmp0 += z1 + z2
        tmp3 += z1 + z3

        z1 = (tmp1 + tmp2) * -20995 # FIX_2_562915447
        tmp1 = tmp1 * 16819 # FIX_2_053119869
        tmp2 = tmp2 * 25172 # FIX_3_072711026
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
        
        z1 = (z2 + z3) * 4433 # FIX_0_541196100
        tmp2 = z1 + z2 * 6270 # FIX_0_765366865
        tmp3 = z1 - z3 * 15137 # FIX_1_847759065
        
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
        
        z1 = (z2 + z3) * 9633 # FIX_1_175875602
        z2 = z2 * -16069 # FIX_1_961570560
        z3 = z3 * -3196 # FIX_0_390180644
        z2 += z1
        z3 += z1

        z1 = (tmp0 + tmp3) * -7373 # FIX_0_899976223
        tmp0 = tmp0 * 2446 # FIX_0_298631336
        tmp3 = tmp3 * 12299 # FIX_1_501321110
        tmp0 += z1 + z2
        tmp3 += z1 + z3

        z1 = (tmp1 + tmp2) * -20995 # FIX_2_562915447
        tmp1 = tmp1 * 16819 # FIX_2_053119869
        tmp2 = tmp2 * 25172 # FIX_3_072711026
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


def _fdct(block):
    # Based on Independent JPEG Group's "jfdctint.c", v8d
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
        
        block[i] = (tmp10 + tmp11 - 8 * 128) << 2 # PASS1_BITS
        block[i+4] = (tmp10 - tmp11) << 2
        
        z1 = (tmp12 + tmp13) * 4433 # FIX_0_541196100
        z1 += 1024 # 1 << (CONST_BITS-PASS1_BITS-1)
        block[i+2] = (z1 + tmp12 * 6270) >> 11 # FIX_0_765366865
        block[i+6] = (z1 - tmp13 * 15137) >> 11 # FIX_1_847759065
        
        tmp10 = tmp0 + tmp3
        tmp11 = tmp1 + tmp2
        tmp12 = tmp0 + tmp2
        tmp13 = tmp1 + tmp3
        z1 = (tmp12 + tmp13) * 9633 # FIX_1_175875602
        z1 += 1024 # 1 << (CONST_BITS-PASS1_BITS-1)
        
        tmp0 = tmp0 * 12299 # FIX_1_501321110
        tmp1 = tmp1 * 25172 # FIX_3_072711026
        tmp2 = tmp2 * 16819 # FIX_2_053119869
        tmp3 = tmp3 * 2446 # FIX_0_298631336
        tmp10 = tmp10 * -7373 # FIX_0_899976223
        tmp11 = tmp11 * -20995 # FIX_2_562915447
        tmp12 = tmp12 * -3196 # FIX_0_390180644
        tmp13 = tmp13 * -16069 # FIX_1_961570560
        
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
        
        z1 = (tmp12 + tmp13) * 4433 # FIX_0_541196100
        z1 += 16384 # 1 << (CONST_BITS+PASS1_BITS-1)
        block[i+16] = (z1 + tmp12 * 6270) >> 15 # FIX_0_765366865, CONST_BITS+PASS1_BITS
        block[i+48] = (z1 - tmp13 * 15137) >> 15 # FIX_1_847759065
        
        tmp10 = tmp0 + tmp3
        tmp11 = tmp1 + tmp2
        tmp12 = tmp0 + tmp2
        tmp13 = tmp1 + tmp3
        z1 = (tmp12 + tmp13) * 9633 # FIX_1_175875602
        z1 += 16384 # 1 << (CONST_BITS+PASS1_BITS-1)
        
        tmp0 = tmp0 * 12299 # FIX_1_501321110
        tmp1 = tmp1 * 25172 # FIX_3_072711026
        tmp2 = tmp2 * 16819 # FIX_2_053119869
        tmp3 = tmp3 * 2446 # FIX_0_298631336
        tmp10 = tmp10 * -7373 # FIX_0_899976223
        tmp11 = tmp11 * -20995 # FIX_2_562915447
        tmp12 = tmp12 * -3196 # FIX_0_390180644
        tmp13 = tmp13 * -16069 # FIX_1_961570560
        
        tmp12 += z1
        tmp13 += z1
        
        block[i+8] = (tmp0 + tmp10 + tmp12) >> 15 # CONST_BITS+PASS1_BITS
        block[i+24] = (tmp1 + tmp11 + tmp13) >> 15
        block[i+40] = (tmp2 + tmp11 + tmp12) >> 15
        block[i+56] = (tmp3 + tmp10 + tmp13) >> 15




_zz = [ # Zig-zag indices of AC coefficients
         1,  8, 16,  9,  2,  3, 10, 17, 24, 32, 25, 18, 11,  4,  5,
    12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13,  6,  7, 14, 21, 28,
    35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51,
    58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63]




# writer


_lq = bytearray([ # Luminance quantization table in zig-zag order
    16, 11, 12, 14, 12, 10, 16, 14, 13, 14, 18, 17, 16, 19, 24, 40,
    26, 24, 22, 22, 24, 49, 35, 37, 29, 40, 58, 51, 61, 60, 57, 51,
    56, 55, 64, 72, 92, 78, 64, 68, 87, 69, 55, 56, 80,109, 81, 87,
    95, 98,103,104,103, 62, 77,113,121,112,100,120, 92,101,103, 99])
_cq = bytearray([ # Chrominance quantization table in zig-zag order
    17, 18, 18, 24, 21, 24, 47, 26, 26, 47, 99, 66, 56, 66, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99])

# Huffman table-specification
_ld0 = bytearray([ # Luminance DC code lengths
    0, 1, 5, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
_ld1 = bytearray([ # Luminance DC values
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
_la0 = bytearray([ # Luminance AC code lengths
    0, 2, 1, 3, 3, 2, 4, 3, 5, 5, 4, 4, 0, 0, 1, 125])
_la1 = bytearray([ # Luminance AC values
      1,  2,  3,  0,  4, 17,  5, 18, 33, 49, 65,  6, 19, 81, 97,  7, 34,113,
     20, 50,129,145,161,  8, 35, 66,177,193, 21, 82,209,240, 36, 51, 98,114,
    130,  9, 10, 22, 23, 24, 25, 26, 37, 38, 39, 40, 41, 42, 52, 53, 54, 55,
     56, 57, 58, 67, 68, 69, 70, 71, 72, 73, 74, 83, 84, 85, 86, 87, 88, 89,
     90, 99,100,101,102,103,104,105,106,115,116,117,118,119,120,121,122,131,
    132,133,134,135,136,137,138,146,147,148,149,150,151,152,153,154,162,163,
    164,165,166,167,168,169,170,178,179,180,181,182,183,184,185,186,194,195,
    196,197,198,199,200,201,202,210,211,212,213,214,215,216,217,218,225,226,
    227,228,229,230,231,232,233,234,241,242,243,244,245,246,247,248,249,250])
_cd0 = bytearray([ # Chrominance DC code lengths
    0, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
_cd1 = bytearray([ # Chrominance DC values
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
_ca0 = bytearray([ # Chrominance AC code lengths
    0, 2, 1, 2, 4, 4, 3, 4, 7, 5, 4, 4, 0, 1, 2, 119])
_ca1 = bytearray([ # Chrominance AC values
      0,  1,  2,  3, 17,  4,  5, 33, 49,  6, 18, 65, 81,  7, 97,113, 19, 34,
     50,129,  8, 20, 66,145,161,177,193,  9, 35, 51, 82,240, 21, 98,114,209,
     10, 22, 36, 52,225, 37,241, 23, 24, 25, 26, 38, 39, 40, 41, 42, 53, 54,
     55, 56, 57, 58, 67, 68, 69, 70, 71, 72, 73, 74, 83, 84, 85, 86, 87, 88,
     89, 90, 99,100,101,102,103,104,105,106,115,116,117,118,119,120,121,122,
    130,131,132,133,134,135,136,137,138,146,147,148,149,150,151,152,153,154,
    162,163,164,165,166,167,168,169,170,178,179,180,181,182,183,184,185,186,
    194,195,196,197,198,199,200,201,202,210,211,212,213,214,215,216,217,218,
    226,227,228,229,230,231,232,233,234,242,243,244,245,246,247,248,249,250])


def _quantization_table(table, quality):
    if quality < 50:
        q = 5000 / max(1, quality)
    else:
        q = 200 - min(quality, 100) * 2
    return bytearray([max(1, min((i * q + 50) // 100, 255)) for i in table])


def _huffman_table(lengths, values):
    table = [None] * (max(values) + 1)
    code = 0
    i = 0
    for size, a in enumerate(lengths, 1):
        for j in range(a):
            table[values[i]] = code, size
            code += 1
            i += 1
        code *= 2
    return table


def _scale_factor(table):
    result = [0] * 64
    for i, z in enumerate([0] + _zz):
        result[z] = table[i] * 8
    return result


class _encoder(object):
    
    def __init__(self):
        c = [i for j in reversed(range(16)) for i in range(1 << j)]
        s = [j for j in range(1, 16) for i in range(1 << (j - 1))]
        s = [0] + s + list(reversed(s))
        self.codes, self.sizes = c, s
        self.value, self.length = 0, 0
        self.data = []
    
    def encode(self, previous, block, scale, dc, ac):
        _fdct(block)
        for i in range(64):
            block[i] = (((block[i] << 1) // scale[i]) + 1) >> 1
        d = block[0] - previous
        if d == 0:
            self.write(*dc[0])
        else:
            s = self.sizes[d]
            self.write(*dc[s])
            self.write(self.codes[d], s)
        n = 0
        for i in _zz:
            if block[i] == 0:
                n += 1
            else:
                while n > 15:
                    self.write(*ac[0xf0])
                    n -= 16
                s = self.sizes[block[i]]
                self.write(*ac[n * 16 + s])
                self.write(self.codes[block[i]], s)
                n = 0
        if n > 0:
            self.write(*ac[0])
        return block[0]
    
    def write(self, value, length):
        value += (self.value << length)
        length += self.length
        while length > 7:
            length -= 8
            v = (value >> length) & 0xff
            self.data.append('\xff\0' if v == 0xff else chr(v))
        self.value = value & 0xff
        self.length = length
        
    def dump(self):
        return ''.join(self.data)




# reader


class _huffman_table_cache(object):
    
    def __init__(self, lengths, values):
        self.lengths, self.values = lengths, values
        offsets = [0]
        sizes = [255] * 65536
        code = index = 0
        for size, length in enumerate(lengths, 1):
            offsets.append(index - code)
            for i in range(length):
                hi = code << (16 - size)
                for lo in range(1 << (16 - size)):
                    sizes[hi|lo] = size
                code += 1
            code *= 2
            index += length
        self.offsets = tuple(offsets)
        self.sizes = bytearray(sizes)


class _decoder(object):
    
    def __init__(self, readable):
        self.readable = readable
        self.value = 0
        self.length = 0
        self.rst = 0
    
    def restart(self):
        marker = self.readable.uint16()
        assert marker == (0xffd0 + self.rst), 'Invalid RST marker.'
        self.value = 0
        self.length = 0
        self.rst = (self.rst + 1) & 7
    
    def fill(self, length):
        while self.length < length:
            byte = self.readable.uint8()
            self.value = ((self.value & 0xffff) << 8) | byte
            self.length += 8
            if byte == 0xff:
                byte = self.readable.uint8()
                if byte != 0:
                    self.readable.position -= 2
    
    def decodehuffman(self, table):
        self.fill(16)
        key = (self.value >> (self.length - 16)) & 0xffff
        size = table.sizes[key]
        assert size < 255, 'Corrupted Huffman sequence.'
        code = (self.value >> (self.length - size)) & ((1 << size) - 1)
        self.length -= size
        return table.values[code + table.offsets[size]]
    
    def receiveextend(self, length):
        self.fill(length)
        value = (self.value >> (self.length - length)) & ((1 << length) - 1)
        self.length -= length
        if value < 1 << (length - 1):
            return value - (1 << length) + 1
        return value
    
    def decode(self, previous, block, q, dc, ac):
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
                block[_zz[i]] = self.receiveextend(s)
                i += 1
        _idct(block, q)
        return previous


def _parse_sof0(self, r, frames):
    self.depth, self.height, self.width, self.count = r.parse('>BHHB')
    assert self.depth == 8, 'Unsupported sample precision.'
    assert self.count in (1, 3, 4), 'Unsupported color type.'
    self.kind = \
        'g' if self.count == 1 else \
        'rgb' if self.count == 3 else 'cmyk'
    for i in range(self.count):
        component, sampling, destination = r.parse('>BBB')
        h, v = sampling >> 4, sampling & 15
        assert 1 <= h <= 4, 'Invalid horizontal sampling factor.'
        assert 1 <= v <= 4, 'Invalid vertical sampling factor.'
        if i > 0:
            assert h == v == 1, 'Unsupported sampling factor.'
        if self.count == 1:
            h, v = 1, 1
        frames.append(record(i=component, h=h, v=v, q=destination))


def _parse_dqt(r, length, qtables):
    end = r.position + length
    while r.position < end:
        pqtq = r.uint8()
        precision, destination = pqtq >> 4, pqtq & 15
        assert precision == 0, 'Unsuported qtable element precision.'
        assert destination < 4, 'Invalid qtable destination identifier.'
        elements = bytearray(r.read(64))
        table = [0] * 64
        for i, z in enumerate([0] + _zz):
            table[z] = elements[i]
        qtables[destination] = table
    assert r.position == end


def _parse_dht(r, length, htables):
    end = r.position + length
    while r.position < end:
        tcth = r.uint8()
        kind, identifier = tcth >> 4, tcth & 15
        assert kind < 2, 'Invalid htable class.'
        assert identifier < 2, 'Unsupported htable destination identifier.'
        lengths = bytearray(r.read(16))
        values = bytearray(r.read(sum(lengths)))
        htables[tcth] = _huffman_table_cache(lengths, values)
    assert r.position == end


def _parse_sos(r, scans):
    n = r.uint8()
    for i in range(n):
        component, destinations = r.parse('>BB')
        dc, ac = destinations >> 4, destinations & 15
        scans[component] = record(dc=dc, ac=16|ac) # ACs always have Tc == 1
    start, end, approximation = r.parse('>BBB')


def _parse_ecs(self, r, frames, scans, qtables, htables, interval, transform, rows):
    
    assert frames, 'Missing SOF0 segment.'
    assert scans, 'Missing SOS segment.'
    assert qtables, 'Missing DQT segment.'
    assert htables, 'Missing DHT segment.'
    
    d = _decoder(r)
    
    w, h, n = self.width, self.height, self.count
    
    rows[:] = [bytearray(w*n) for y in range(h)]
    
    hs, vs, qs, dcs, acs = zip(*[(
        f.h,
        f.v,
        qtables[f.q],
        htables[scans[f.i].dc],
        htables[scans[f.i].ac]) for f in frames])
    
    mx, my = 8 * hs[0], 8 * vs[0]
    
    counter = 0
    if interval == 0:
        interval = ((w + mx-1) // mx) * ((h + my-1) // my)
    
    zeros = [0] * 64
    preds = [0, 0, 0, 0]
    yblocks = [[0] * 64 for i in range(hs[0] * vs[0])]
    yblock, ublock, vblock, kblock = yblocks[0], [0] * 64, [0] * 64, [0] * 64
    blocks = yblocks, [ublock], [vblock], [kblock]
    
    selector, samples, subsamples = zip(*[(
        yblocks[(y//8) * hs[0] + x//8],
        (y%8) * 8 + x%8,
        (y//vs[0]) * 8 + x//hs[0]) for y in range(my) for x in range(mx)])
    
    for by in range(0, h, my):
        dy = min(h - by, my)
        for bx in range(0, w, mx):
            dx = min(w - bx, mx)
            
            counter += 1
            if counter > interval:
                preds[:] = [0, 0, 0, 0]
                d.restart()
                counter = 1
            
            for j in range(n):
                for i in range(hs[j] * vs[j]):
                    blocks[j][i][:] = zeros
                    preds[j] = d.decode(
                        preds[j], blocks[j][i], qs[j], dcs[j], acs[j])
            
            for y in range(dy):
                row = rows[by + y]
                for x in range(dx):
                    i = y * mx + x
                    if n == 1:
                        row[bx + x] = clamp(yblock[i] + 128)
                    elif n == 3:
                        yy = (selector[i][samples[i]] << 16) + 8421376
                        cb = ublock[subsamples[i]]
                        cr = vblock[subsamples[i]]
                        r = clamp((yy + 91881*cr) >> 16)
                        g = clamp((yy - 22554*cb - 46802*cr) >> 16)
                        b = clamp((yy + 116130*cb) >> 16)
                        offset = (bx + x) * 3
                        row[offset] = r
                        row[offset + 1] = g
                        row[offset + 2] = b
                    else: # 4
                        if transform:
                            yy = (selector[i][samples[i]] << 16) + 8421376
                            cb = ublock[subsamples[i]]
                            cr = vblock[subsamples[i]]
                            kk = kblock[subsamples[i]]
                            r = clamp((yy + 91881*cr) >> 16)
                            g = clamp((yy - 22554*cb - 46802*cr) >> 16)
                            b = clamp((yy + 116130*cb) >> 16)
                            offset = (bx + x) * 4
                            row[offset] = 255 - r
                            row[offset + 1] = 255 - g
                            row[offset + 2] = 255 - b
                            row[offset + 3] = clamp(kk + 128)
                        else:
                            cc = selector[i][samples[i]]
                            mm = ublock[subsamples[i]]
                            yy = vblock[subsamples[i]]
                            kk = kblock[subsamples[i]]
                            offset = (bx + x) * 4
                            row[offset] = clamp(cc + 128)
                            row[offset + 1] = clamp(mm + 128)
                            row[offset + 2] = clamp(yy + 128)
                            row[offset + 3] = clamp(kk + 128)
    
    return rows




# jpeg


class jpeg(object):
    
    @staticmethod
    def valid(data):
        return data.startswith('\xff\xd8') # SOI
    
    def __init__(self, data):
        self.data = data
        self.width, self.height = 0, 0
        self.depth, self.count, self.kind = 0, 0, ''
        self.parse(readable(data), False)
    
    def decompress(self):
        return self.parse(readable(self.data), True)
    
    def parse(self, r, decompress):
        
        frames, scans, qtables, htables = [], {}, {}, {}
        interval, transform, adobe = 0, False, False
        rows, done = [], False
        
        r.skip(2) # header
        
        while True:
            
            marker = r.uint8()
            assert marker == 0xff, 'Invalid marker.'
            while marker == 0xff:
                marker = r.uint8()
            
            if marker == 0xd9: # EOI
                done = True
                break
            
            length = r.uint16() - 2
            
            if marker == 0xc0: # SOF0
                _parse_sof0(self, r, frames)
                if not decompress:
                    return
                if not adobe:
                    transform = self.kind == 'rgb'
            elif marker == 0xdb: # DQT
                _parse_dqt(r, length, qtables) if decompress else r.skip(length)
            elif marker == 0xc4: # DHT
                _parse_dht(r, length, htables) if decompress else r.skip(length)
            elif marker == 0xda: # SOS:
                _parse_sos(r, scans)
                _parse_ecs(self, r, frames, scans, qtables, htables,
                    interval, transform, rows)
            elif marker == 0xdd: # DRI
                interval = r.uint16()
            elif marker == 0xee: # APPE
                r.skip(11) # 'Adobe', version, flags0, flags1
                transform, adobe = r.uint8() != 0, True
            elif 0xe0 <= marker <= 0xef or marker == 0xfe: # APP, COM
                r.skip(length)
            else:
                assert not (0xd0 <= marker <= 0xd7), 'Unexpected RST marker.' # RST
                assert marker != 0xc2, 'Progressive DCT not supported.' # SOF2
                assert marker != 0xde, 'Hierarchical mode not supported.' # DHP
                raise AssertionError('Invalid marker.')
        
        assert rows, 'Invalid entropy coded segment.'
        assert done, 'Missing EOI marker.'
        return rows
    
    @staticmethod
    def dump(image, quality):
        
        assert image.kind in ('g', 'rgb', 'cmyk'), 'Invalid image kind.'
        
        w, h, n = image.width, image.height, image.count
        
        lq = _quantization_table(_lq, quality) # luminance
        ld = _huffman_table(_ld0, _ld1)
        la = _huffman_table(_la0, _la1)
        ls = _scale_factor(lq)
        if n == 3:
            cq = _quantization_table(_cq, quality) # chrominance
            cd = _huffman_table(_cd0, _cd1)
            ca = _huffman_table(_ca0, _ca1)
            cs = _scale_factor(cq)
        
        e = _encoder()
        
        xr = chunks(tuple(range(0, w * n, n)) + ((w - 1) * n,) * (8 - w & 7), 8)
        yr = chunks(tuple(range(0, h)) + (h - 1,) * (8 - h & 7), 8)
        
        yblock, ublock, vblock, kblock = [0] * 64, [0] * 64, [0] * 64, [0] * 64
        ydc, udc, vdc, kdc = 0, 0, 0, 0
        
        for ys in yr:
            for xs in xr:
                
                i = 0
                for y in ys:
                    row = image.rows[y]
                    for x in xs:
                        if n == 1:
                            yblock[i] = row[x]
                        elif n == 3:
                            r = row[x]
                            g = row[x + 1]
                            b = row[x + 2]
                            yblock[i] = (19595*r + 38470*g + 7471*b + 32768) >> 16
                            ublock[i] = (-11056*r - 21712*g + 32768*b + 8421376) >> 16
                            vblock[i] = (32768*r - 27440*g - 5328*b + 8421376) >> 16
                        else: # 4
                            yblock[i] = row[x]
                            ublock[i] = row[x + 1]
                            vblock[i] = row[x + 2]
                            kblock[i] = row[x + 3]
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
        
        B = Struct('>B').pack # unsigned char
        H = Struct('>H').pack # unsigned short
        
        sof = '\1\21\0' # id, sampling, qtable
        sos = '\1\0' # id, htable
        dqt = '\0' + lq
        dht = '\0' + _ld0 + _ld1 + '\20' + _la0 + _la1
        if n == 3:
            sof += '\2\21\1\3\21\1'
            sos += '\2\21\3\21'
            dqt += '\1' + cq
            dht += '\1' + _cd0 + _cd1 + '\21' + _ca0 + _ca1
        elif n == 4:
            sof += '\2\21\0\3\21\0\4\21\0'
            sos += '\2\0\3\0\4\0'
        
        return ''.join((
            '\xff\xd8', # SOI
            '\xff\xe0\0\20JFIF\0\1\1\0\0\1\0\1\0\0', # APP0
            '\xff\xee\0\16Adobe\0\144\200\0\0\0\0' if n == 4 else '', # APP14
            '\xff\xdb', H(2 + len(dqt)), str(dqt), # DQT # TODO python 3: remove str
            '\xff\xc0', H(8 + 3 * n), '\10', H(h), H(w), B(n), sof, # SOF0
            '\xff\xc4', H(2 + len(dht)), str(dht), # DHT # TODO python 3: remove str
            '\xff\xda', H(6 + 2 * n), B(n), sos, '\0\77\0', # SOS
            e.dump(),
            '\xff\xd9')) # EOI




