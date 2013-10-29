
from struct import pack, unpack
from math import hypot, log
from unicodedata import normalize

from .cff import cff
from .command import moveto, lineto, quadto, closepath
from .readable import readable
from .utils import lazy, record




char, byte = 'b', 'B'
short, ushort = 'h', 'H'
slong, ulong = 'l', 'L'
fixed = 'l'
longdatetime = 'q'
fword, ufword = short, ushort




class otf(object):
    
    @staticmethod
    def valid(data):
        return data[0:4] in ('\0\1\0\0', 'OTTO', 'true', 'typ1', 'ttcf')
    
    @staticmethod
    def collection(data):
        return data.startswith('ttcf')
    
    def __init__(self, data, index=0):
        self.readable = readable(data)
        if self.collection(data):
            self.readable.skip(8) # TTCTag, Version
            numFonts = self.readable.uint32()
            assert index < numFonts, 'Invalid collection index.'
            self.readable.skip(index * 4)
            self.readable.jump(self.readable.uint32())
        self.offset = self.parse((
            '4s', 'version',
            ushort, 'numTables',
            ushort, 'searchRange',
            ushort, 'entrySelector',
            ushort, 'rangeShift'), self.readable.position)
        self.records = {}
        for i in range(self.offset.numTables):
            r = self.parse((
                '4s', 'tag',
                ulong, 'checkSum',
                ulong, 'offset',
                ulong, 'length'), self.readable.position)
            self.records[r.tag] = r
    
    def parse(self, layout, position):
        self.readable.jump(position)
        entries = self.readable.parse('>' + ''.join(layout[0::2]))
        return record(**dict(zip(layout[1::2], entries)))
    
    # required tables
    
    @lazy
    def cmap(self):
        t = self.parse((
            ushort, 'version',
            ushort, 'numTables'), self.records['cmap'].offset)
        encodingRecord = self.readable.parse(
            '>' + (ushort + ushort + ulong) * t.numTables)
        return record(
            platformID = encodingRecord[0::3],
            encodingID = encodingRecord[1::3],
            offset = encodingRecord[2::3])
    
    @lazy
    def head(self):
        return self.parse((
            fixed, 'version',
            fixed, 'fontRevision',
            ulong, 'checkSumAdjustment',
            ulong, 'magicNumber',
            ushort, 'flags',
            ushort, 'unitsPerEm',
            longdatetime, 'created',
            longdatetime, 'modified',
            short, 'xMin',
            short, 'yMin',
            short, 'xMax',
            short, 'yMax',
            ushort, 'macStyle',
            ushort, 'lowestRecPPEM',
            short, 'fontDirectionHint',
            short, 'indexToLocFormat',
            short, 'glyphDataFormat'), self.records['head'].offset)
    
    @lazy
    def hhea(self):
        return self.parse((
            fixed, 'version',
            fword, 'Ascender',
            fword, 'Descender',
            fword, 'LineGap',
            ufword, 'advanceWidthMax',
            fword, 'minLeftSideBearing',
            fword, 'minRightSideBearing',
            fword, 'xMaxExtent',
            short, 'caretSlopeRise',
            short, 'caretSlopeRun',
            short, 'caretOffset',
            short, 'reserved1',
            short, 'reserved2',
            short, 'reserved3',
            short, 'reserved4',
            short, 'metricDataFormat',
            ushort, 'numberOfHMetrics'), self.records['hhea'].offset)
    
    @lazy
    def hmtx(self):
        g = self.maxp.numGlyphs
        h = self.hhea.numberOfHMetrics
        self.readable.jump(self.records['hmtx'].offset)
        longHorMetric = self.readable.parse('>' + (ushort + short) * h)
        return record(
            advanceWidth = longHorMetric[0::2],
            leftSideBearing = longHorMetric[1::2] + self.readable.parse(
                '>%d' % (g - h) + short))
    
    @lazy
    def maxp(self):
        return self.parse((
            fixed, 'version',
            ushort, 'numGlyphs'), self.records['maxp'].offset)
    
    @lazy
    def name(self):
        t = self.parse((
            ushort, 'format',
            ushort, 'count',
            ushort, 'stringOffset'), self.records['name'].offset)
        nameRecord = self.readable.parse('>%d' % (6 * t.count) + ushort)
        return record(
            stringOffset = t.stringOffset,
            platformID = nameRecord[0::6],
            encodingID = nameRecord[1::6],
            languageID = nameRecord[2::6],
            nameID = nameRecord[3::6],
            length = nameRecord[4::6],
            offset = nameRecord[5::6])
    
    @lazy
    def os2(self):
        return self.parse((
            ushort, 'version',
            short, 'xAvgCharWidth',
            ushort, 'usWeightClass',
            ushort, 'usWidthClass',
            ushort, 'fsType',
            short, 'ySubscriptXSize',
            short, 'ySubscriptYSize',
            short, 'ySubscriptXOffset',
            short, 'ySubscriptYOffset',
            short, 'ySuperscriptXSize',
            short, 'ySuperscriptYSize',
            short, 'ySuperscriptXOffset',
            short, 'ySuperscriptYOffset',
            short, 'yStrikeoutSize',
            short, 'yStrikeoutPosition',
            short, 'sFamilyClass',
            byte, 'bFamilyType',
            byte, 'bSerifStyle',
            byte, 'bWeight',
            byte, 'bProportion',
            byte, 'bContrast',
            byte, 'bStrokeVariation',
            byte, 'bArmStyle',
            byte, 'bLetterform',
            byte, 'bMidline',
            byte, 'bXHeight',
            ulong, 'ulUnicodeRange1',
            ulong, 'ulUnicodeRange2',
            ulong, 'ulUnicodeRange3',
            ulong, 'ulUnicodeRange4',
            '4s', 'achVendID',
            ushort, 'fsSelection',
            ushort, 'usFirstCharIndex',
            ushort, 'usLastCharIndex',
            short, 'sTypoAscender',
            short, 'sTypoDescender',
            short, 'sTypoLineGap',
            ushort, 'usWinAscent',
            ushort, 'usWinDescent',
            ulong, 'ulCodePageRange1',
            ulong, 'ulCodePageRange2',
            short, 'sxHeight',
            short, 'sCapHeight',
            ushort, 'usDefaultChar',
            ushort, 'usBreakChar',
            ushort, 'usMaxContext'), self.records['OS/2'].offset)
    
    @lazy
    def post(self):
        return self.parse((
            fixed, 'version',
            fixed, 'italicAngle',
            fword, 'underlinePosition',
            fword, 'underlineThickness',
            ulong, 'isFixedPitch',
            ulong, 'minMemType42',
            ulong, 'maxMemType42',
            ulong, 'minMemType1',
            ulong, 'maxMemType1'), self.records['post'].offset)
    
    # truetype tables
    
    def glyf(self, index):
        
        location = self.loca.offsets[index]
        if self.loca.offsets[index+1] - location == 0:
            return []
        
        r = self.readable
        
        r.jump(self.records['glyf'].offset + location)
        numberOfContours = r.int16()
        
        result = []
        
        r.skip(8) # xMin, yMin, xMax, yMax
        if numberOfContours > 0:
            endPtsOfContours = r.parse('>%d' % numberOfContours + ushort)
            instructionLength = r.uint16()
            r.skip(instructionLength) # instructions
            count = endPtsOfContours[-1] + 1
            
            flags = bytearray(count)
            f = repeat = 0
            for i in range(count):
                if repeat == 0:
                    f = r.uint8()
                    if f & 8: # Repeat
                        repeat = r.uint8()
                else:
                    repeat -= 1
                flags[i] = f
            
            x, xs = 0, [0] * count
            for i, f in enumerate(flags):
                f &= 18 # x-Short Vector + This x is same
                if f == 18:
                    x += r.uint8()
                elif f == 2:
                    x -= r.uint8()
                elif f == 0:
                    x += r.int16()
                xs[i] = x
            y, ys = 0, [0] * count
            for i, f in enumerate(flags):
                f &= 36 # y-Short Vector + This y is same
                if f == 36:
                    y += r.uint8()
                elif f == 4:
                    y -= r.uint8()
                elif f == 0:
                    y += r.int16()
                ys[i] = y
            
            end = -1
            for i in range(numberOfContours):
                start, end = end+1, endPtsOfContours[i]
                ax, ay, af = xs[end], ys[end], flags[end] & 1 # On Curve
                first = moveto(0.0, 0.0)
                result.append(first)
                for i in range(start, end+1):
                    bx, by, bf = xs[i], ys[i], flags[i] & 1
                    if bf:
                        result.append(lineto(bx, by) if af else quadto(ax, ay, bx, by))
                    elif not af:
                        result.append(quadto(ax, ay, (ax+bx)*0.5, (ay+by)*0.5))
                    ax, ay, af = bx, by, bf
                last = result[-1]
                first.x, first.y = last.x, last.y
                result.append(closepath)
        
        elif numberOfContours < 0:
            flags = 32
            while flags & 32: # MORE_COMPONENTS
                flags, glyphIndex = r.parse('>2' + ushort)
                assert flags & 2, 'ARGS_ARE_XY_VALUES not implemented.'
                a, b, c, d = 1.0, 0.0, 0.0, 1.0
                e, f = r.parse('>2' + (short if flags & 1 else char)) # ARG_1_AND_2_ARE_WORDS
                if flags & 8: # WE_HAVE_A_SCALE
                    a = d = r.int16() / 16384.0
                elif flags & 64: # WE_HAVE_AN_X_AND_Y_SCALE
                    a = r.int16() / 16384.0
                    d = r.int16() / 16384.0
                elif flags & 128: # WE_HAVE_A_TWO_BY_TWO
                    a = r.int16() / 16384.0
                    b = r.int16() / 16384.0
                    c = r.int16() / 16384.0
                    d = r.int16() / 16384.0
                
                p = r.position
                component = self.glyf(glyphIndex)
                r.position = p
                
                if flags & 200: # 8 + 64 + 128
                    if flags & 2048: # SCALED_COMPONENT_OFFSET
                        e *= hypot(a, c)
                        f *= hypot(b, d)
                
                for command in component:
                    command.transform(a, b, c, d, e, f)
                
                result.extend(component)
            
        return result
    
    @lazy
    def loca(self):
        n = self.maxp.numGlyphs + 1
        self.readable.jump(self.records['loca'].offset)
        if self.head.indexToLocFormat == 0:
            offsets = self.readable.parse('>%d' % n + ushort)
            offsets = tuple(offset * 2 for offset in offsets)
        else:
            offsets = self.readable.parse('>%d' % n + ulong)
        return record(offsets=offsets)
    
    # postscript tables
    
    @lazy
    def cff(self):
        if 'CFF ' in self.records:
            cff = self.records['CFF ']
            return buffer(self.readable.data, cff.offset, cff.length) # TODO python 3: buffer is no more
        return None
    
    def vorg(self):
        raise NotImplementedError
    
    # advanced typographic tables
    
    # other tables
    
    def kern(self):
        t = self.parse((
            ushort, 'version',
            ushort, 'nTables'), self.records['kern'].offset)
        left, right, value = [], [], []
        for i in range(t.nTables):
            self.readable.skip(4) # version, length
            coverage = self.readable.uint16()
            assert coverage >> 8 == 0, 'Unsupported subtable format.'
            nPairs = self.readable.uint16()
            self.readable.skip(6) # searchRange, entrySelector, rangeShift
            p = self.readable.parse('>' + (ushort + ushort + fword) * nPairs)
            left.extend(p[0::3])
            right.extend(p[1::3])
            value.extend(p[2::3])
        return record(
            left = left,
            right = right,
            value = value)
    
    #
    
    @lazy
    def glyph(self):
        if self.cff:
            return cff(self.cff).type2
        return self.glyf
    
    def string(self, nameid):
        name = self.name
        start = self.records['name'].offset + name.stringOffset
        for i, nameID in enumerate(name.nameID):
            if nameID == nameid:
                kind = name.platformID[i], name.encodingID[i], name.languageID[i]
                offset, length = name.offset[i], name.length[i]
                if kind == (1, 0, 0):
                    self.readable.jump(start + offset)
                    return self.readable.read(length)
                elif kind == (3, 1, 0x409):
                    self.readable.jump(start + offset)
                    string = self.readable.read(length).decode('utf-16be')
                    return normalize('NFKD', string).encode('ascii', 'ignore')
        raise AssertionError('String not found.')
    
    def psname(self):
        return self.string(6)
    
    def unitsperem(self):
        return self.head.unitsPerEm
    
    def density(self):
        return 1.0 / self.head.unitsPerEm
    
    def ascender(self):
        if 'OS/2' in self.records:
            return self.os2.sTypoAscender
        return self.hhea.Ascender
    
    def descender(self):
        if 'OS/2' in self.records:
            return self.os2.sTypoDescender
        return self.hhea.Descender
    
    def charmap(self):
        r, cmap = self.readable, self.cmap
        start = self.records['cmap'].offset
        for i, kind in enumerate(zip(cmap.platformID, cmap.encodingID)):
            if kind == (3, 1) or kind == (0, 3):
                offset = cmap.offset[i]
                r.jump(start + offset)
                if r.uint16() == 4: # format
                    break
        else:
            raise AssertionError('Unicode BMP encoding not found.')
        length = r.uint16()
        r.skip(2) # language
        segCountX2 = r.uint16()
        r.skip(6) # searchRange, entrySelector, rangeShift
        segCount = segCountX2 // 2
        u, s = '>%d' % segCount + ushort, '>%d' % segCount + short
        endCode = r.parse(u)
        r.skip(2) # reservedPad
        startCode = r.parse(u)
        idDelta = r.parse(s)
        idRangeOffset = r.parse(u)
        count = (start + offset + length - r.position) // 2
        glyphIdArray = r.parse('>%d' % count + ushort)
        charmap = {}
        for i in range(segCount):
            start = startCode[i]
            end = endCode[i]
            delta = idDelta[i]
            rangeoffset = idRangeOffset[i]
            if rangeoffset == 0:
                for code in range(start, end + 1):
                    charmap[code] = (code + delta) & 0xffff
            else:
                for code in range(start, end + 1):
                    index = rangeoffset // 2 + (code - start) - (segCount - i)
                    if index < count:
                        charmap[code] = (glyphIdArray[index] + delta) & 0xffff
                    else:
                        charmap[code] = 0
        return charmap
    
    def kerning(self):
        result = [{} for i in range(self.maxp.numGlyphs)]
        if 'kern' in self.records:
            kern = self.kern()
            for left, right, value in zip(kern.left, kern.right, kern.value):
                result[left][right] = -value
        return result
    
    def advances(self):
        a = self.hmtx.advanceWidth
        return a + a[-1:] * (self.maxp.numGlyphs - self.hhea.numberOfHMetrics)
    
    def defaultadvance(self):
        return self.hmtx.advanceWidth[-1]
    
    def embed(self):
        
        if self.cff:
            return self.cff
        
        checksum = lambda s: sum(unpack('>%dL' % (len(s) // 4), s))
        
        tags = [tag for tag in ('cvt ', 'fpgm', 'glyf', 'head', 'hhea',
            'hmtx', 'loca', 'maxp', 'prep') if tag in self.records]
        
        records, tables = [], []
        position, head = 12 + len(tags) * 16, 0
        total = 0
        
        for tag in tags:
            if tag == 'head':
                head = position
            r = self.records[tag]
            checkSum, length = r.checkSum, r.length
            padding = 4 - length & 3
            self.readable.jump(r.offset)
            data = self.readable.read(length)
            records.append(pack('>4s3L', tag, checkSum, position, length))
            tables.append(data + '\0' * padding)
            position += length + padding
            total += checkSum
        
        numTables = len(tables)
        entrySelector = int(log(numTables, 2))
        searchRange = 16 << entrySelector
        rangeShift = 16 * numTables - searchRange
        offset = pack('>4s4H', self.offset.version,
            numTables, entrySelector, searchRange, rangeShift)
        
        data = bytearray(offset)
        data += ''.join(records)
        total += checksum(buffer(data)) # TODO python 3: buffer is no more
        data += ''.join(tables)
        data[head+8:head+12] = pack('>L', 0xb1b0afba - total & 0xffffffff)
        
        return data
    
    @staticmethod
    def dump(font):
        raise NotImplementedError




