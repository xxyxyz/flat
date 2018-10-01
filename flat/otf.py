from math import hypot
from struct import pack
from unicodedata import normalize
from .cff import cff
from .command import moveto, lineto, quadto, closepath
from .readable import readable




class otf(object):
    
    @staticmethod
    def valid(data):
        for version in (b'\0\1\0\0', b'OTTO', b'true', b'typ1', b'ttcf'):
            if data.startswith(version):
                return True
        return False
    
    def __init__(self, data, index=0):
        self.readable = r = readable(data)
        if data.startswith(b'ttcf'):
            r.skip(4 + 4) # TTCTag, Version
            numFonts = r.uint32()
            if index >= numFonts:
                raise ValueError('Invalid collection index.')
            r.skip(index*4)
            r.jump(r.uint32()) # offset
        self.offset = offset(r)
        self.records = [record(r) for i in range(self.offset.numTables)]
        self.records.sort(key=lambda entry: entry.tag)
        if data.startswith(b'OTTO'):
            self.find(b'CFF ')
            self.cff = cff(r)
        else:
            self.cff = None
        self.indexToLocFormat = self.head().indexToLocFormat
        self.numGlyphs = self.maxp().numGlyphs
    
    def find(self, tag):
        records = self.records
        i, j = 0, len(records)
        if i < j:
            while i < j:
                m = (i + j)//2
                if records[m].tag < tag:
                    i = m + 1
                else:
                    j = m
            entry = records[i]
            if entry.tag == tag:
                self.readable.jump(entry.offset)
                return entry
        raise ValueError('`%s` table not found.' % tag.decode())
    
    def psname(self):
        return self.name(6) # Postscript name
    
    def density(self):
        return self.head().unitsPerEm
    
    def ascender(self):
        return self.os2().sTypoAscender
    
    def descender(self):
        return self.os2().sTypoDescender
    
    def glyph(self, index):
        if self.cff:
            return self.cff.type2(index)
        return self.glyf(index)
    
    def charmap(self):
        r = self.readable
        cmap = self.find(b'cmap')
        r.skip(2) # version
        numTables = r.uint16()
        for i in range(numTables):
            platformID = r.uint16()
            encodingID = r.uint16()
            offset = r.uint32()
            kind = platformID, encodingID
            if kind == (3, 1) or kind == (0, 3):
                r.jump(cmap.offset + offset)
                if r.uint16() == 4: # format
                    break
        else:
            raise ValueError('Unicode BMP encoding not found.')
        length = r.uint16()
        r.skip(2) # language
        segCountX2 = r.uint16()
        segCount = segCountX2//2
        r.skip(2 + 2 + 2) # searchRange, entrySelector, rangeShift
        endCount = [r.uint16() for i in range(segCount)]
        r.skip(2) # reservedPad
        startCount = [r.uint16() for i in range(segCount)]
        idDelta = [r.int16() for i in range(segCount)]
        idRangeOffset = [r.uint16() for i in range(segCount)]
        count = (cmap.offset + offset + length - r.position)//2
        glyphIdArray = [r.uint16() for i in range(count)]
        result = {}
        for i in range(segCount):
            start = startCount[i]
            end = endCount[i]
            delta = idDelta[i]
            rangeoffset = idRangeOffset[i]
            if rangeoffset == 0:
                for code in range(start, end + 1):
                    result[code] = (code + delta) & 0xffff
            else:
                for code in range(start, end + 1):
                    index = rangeoffset//2 + (code - start) - (segCount - i)
                    if index < count:
                        result[code] = (glyphIdArray[index] + delta) & 0xffff
                    else:
                        result[code] = 0
        return result
    
    def advances(self):
        r = self.readable
        numberOfHMetrics = self.hhea().numberOfHMetrics
        result = []
        hmtx = self.find(b'hmtx')
        advanceWidth = 0
        for i in range(numberOfHMetrics):
            advanceWidth = r.uint16()
            r.skip(2) # lsb
            result.append(advanceWidth)
        result.extend([advanceWidth]*(self.numGlyphs - numberOfHMetrics))
        return result
    
    def kerning(self):
        r = self.readable
        result = [{} for i in range(self.numGlyphs)]
        for entry in self.records:
            if entry.tag == b'kern':
                r.jump(entry.offset)
                r.skip(2) # version
                nTables = r.uint16()
                for i in range(nTables):
                    r.skip(2 + 2) # version, length
                    coverage = r.uint16()
                    if coverage >> 8 != 0:
                        raise ValueError('Unsupported kern subtable format.')
                    nPairs = r.uint16()
                    r.skip(2 + 2 + 2) # searchRange, entrySelector, rangeShift
                    for j in range(nPairs):
                        left, right, value = r.uint16(), r.uint16(), r.int16()
                        result[left][right] = value
                break
            if entry.tag == b'GPOS':
                r.jump(entry.offset)
                r.skip(2 + 2) # MajorVersion, MinorVersion
                ScriptList = r.uint16()
                FeatureList = r.uint16()
                LookupList = r.uint16()
                r.jump(entry.offset + LookupList)
                LookupCount = r.uint16()
                Lookup = [r.uint16() for i in range(LookupCount)]
                r.jump(entry.offset + FeatureList)
                FeatureCount = r.uint16()
                for i in range(FeatureCount):
                    FeatureTag = r.read(4)
                    Feature = r.uint16()
                    if FeatureTag == b'kern':
                        r.jump(entry.offset + FeatureList + Feature)
                        break
                else:
                    continue
                r.skip(2) # FeatureParams
                LookupCount = r.uint16()
                LookupListIndex = [r.uint16() for i in range(LookupCount)]
                for index in LookupListIndex:
                    lookup = Lookup[index]
                    r.jump(entry.offset + LookupList + lookup)
                    LookupType = r.uint16()
                    if LookupType == 2: # Pair adjustment
                        r.skip(2) # LookupFlag
                        SubTableCount = r.uint16()
                        SubTable = [r.uint16() for i in range(SubTableCount)]
                        for subtable in SubTable:
                            PairPos = entry.offset + LookupList + lookup + subtable
                            r.jump(PairPos)
                            PosFormat = r.uint16()
                            Coverage = r.uint16()
                            ValueFormat1 = r.uint16()
                            ValueFormat2 = r.uint16()
                            if ValueFormat1 == 4 and ValueFormat2 == 0: # XAdvance
                                s = r.clone()
                                s.jump(PairPos + Coverage)
                                coverage = _parse_coverage(s)
                                if PosFormat == 1:
                                    PairSetCount = r.uint16()
                                    if PairSetCount != len(coverage):
                                        raise ValueError('Invalid GPOS PairSetCount.')
                                    for first in coverage:
                                        PairSetOffset = r.uint16()
                                        s.jump(PairPos + PairSetOffset)
                                        PairValueCount = s.uint16()
                                        for i in range(PairValueCount):
                                            SecondGlyph, Value1 = s.uint16(), s.int16()
                                            result[first][SecondGlyph] = Value1
                                elif PosFormat == 2:
                                    ClassDef1 = r.uint16()
                                    ClassDef2 = r.uint16()
                                    Class1Count = r.uint16()
                                    Class2Count = r.uint16()
                                    if Class1Count == 0:
                                        continue
                                    s.jump(PairPos + ClassDef1)
                                    definition1 = _parse_classdefinition(s, Class1Count)
                                    s.jump(PairPos + ClassDef2)
                                    definition2 = _parse_classdefinition(s, Class2Count)
                                    definition1[0].extend(coverage)
                                    for i in range(Class1Count):
                                        for j in range(Class2Count):
                                            Value1 = r.int16()
                                            if Value1 != 0:
                                                for first in definition1[i]:
                                                    for second in definition2[j]:
                                                        result[first][second] = Value1
                break
        return result
    
    def embed(self):
        r = self.readable
        if self.cff:
            entry = self.find(b'CFF ')
            return r.read(entry.length)
        tags = {b'cvt ', b'fpgm', b'glyf', b'head', b'hhea', b'hmtx', b'loca',
             b'maxp', b'prep'}
        numTables = 0
        for entry in self.records:
            if entry.tag in tags:
                numTables += 1
        records, tables = [], []
        position = 4+2+2+2+2 + numTables*(4+4+4+4) # offset table + records
        head = 0
        total = 0
        for entry in self.records:
            if entry.tag in tags:
                if entry.tag == b'head':
                    head = position
                r.jump(entry.offset)
                length = entry.length
                padding = 4 - length & 3
                data = r.read(length)
                records.append(pack('>4s3L', entry.tag,
                    entry.checkSum, position, length))
                tables.append(data)
                tables.append(b'\0'*padding)
                position += length + padding
                total += entry.checkSum
        entrySelector = numTables.bit_length() - 1
        searchRange = 16 << entrySelector
        rangeShift = 16*numTables - searchRange
        offset = pack('>L4H', self.offset.sfntVersion,
            numTables, entrySelector, searchRange, rangeShift)
        data = bytearray(offset)
        data += bytearray().join(records)
        r = readable(data)
        for i in range(len(data)//4):
            total += r.uint32()
        data += bytearray().join(tables)
        data[head+8:head+12] = pack('>L', 0xb1b0afba - total & 0xffffffff)
        return bytes(data)
    
    def name(self, nameid):
        r = self.readable
        name = self.find(b'name')
        r.skip(2) # format
        count = r.uint16()
        stringOffset = r.uint16()
        for i in range(count):
            platformID = r.uint16()
            encodingID = r.uint16()
            languageID = r.uint16()
            nameID = r.uint16()
            length = r.uint16()
            offset = r.uint16()
            if nameid == nameID:
                kind = platformID, encodingID, languageID
                if kind == (1, 0, 0):
                    r.jump(name.offset + stringOffset + offset)
                    return r.read(length)
                if kind == (3, 1, 0x409):
                    r.jump(name.offset + stringOffset + offset)
                    s = r.read(length).decode('utf-16be')
                    return normalize('NFKD', s).encode('ascii', 'ignore')
        raise ValueError('String not found.')
    
    def loca(self, index):
        r = self.readable
        loca = self.find(b'loca')
        if self.indexToLocFormat == 0:
            r.skip(index*2)
            offset = r.uint16()*2
        else:
            r.skip(index*4)
            offset = r.uint32()
        return offset
    
    def glyf(self, index):
        r = self.readable
        result = []
        location = self.loca(index)
        if location == self.loca(index + 1):
            return result
        glyf = self.find(b'glyf')
        r.skip(location)
        numberOfContours = r.int16()
        r.skip(8) # xMin, yMin, xMax, yMax
        if numberOfContours > 0:
            endPtsOfContours = [r.uint16() for i in range(numberOfContours)]
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
            x, xs = 0, [0]*count
            i = 0
            for f in flags:
                f &= 18 # x-Short Vector + This x is same
                if f == 18:
                    x += r.uint8()
                elif f == 2:
                    x -= r.uint8()
                elif f == 0:
                    x += r.int16()
                xs[i] = x
                i += 1
            y, ys = 0, [0]*count
            i = 0
            for f in flags:
                f &= 36 # y-Short Vector + This y is same
                if f == 36:
                    y += r.uint8()
                elif f == 4:
                    y -= r.uint8()
                elif f == 0:
                    y += r.int16()
                ys[i] = y
                i += 1
            end = -1
            for i in range(numberOfContours):
                start, end = end+1, endPtsOfContours[i]
                ax, ay, af = xs[end], ys[end], flags[end] & 1 # On Curve
                first = moveto(0.0, 0.0)
                result.append(first)
                for j in range(start, end+1):
                    bx, by, bf = xs[j], ys[j], flags[j] & 1
                    if bf:
                        result.append(lineto(bx, by) if af else quadto(ax, ay, bx, by))
                    elif not af:
                        result.append(quadto(ax, ay, (ax+bx)*0.5, (ay+by)*0.5))
                    ax, ay, af = bx, by, bf
                last = result[-1]
                first.x, first.y = last.x, last.y
                result.append(closepath)
        elif numberOfContours < 0:
            s = r.clone()
            while True:
                flags = s.uint16()
                glyphIndex = s.uint16()
                if flags & 2 == 0:
                     raise NotImplementedError('ARGS_ARE_XY_VALUES not implemented.')
                a, b, c, d = 1.0, 0.0, 0.0, 1.0
                if flags & 1: # ARG_1_AND_2_ARE_WORDS
                    e, f = s.int16(), s.int16()
                else:
                    e, f = s.int8(), s.int8()
                if flags & 8: # WE_HAVE_A_SCALE
                    a = d = s.int16()/16384.0
                elif flags & 64: # WE_HAVE_AN_X_AND_Y_SCALE
                    a = s.int16()/16384.0
                    d = s.int16()/16384.0
                elif flags & 128: # WE_HAVE_A_TWO_BY_TWO
                    a = s.int16()/16384.0
                    b = s.int16()/16384.0
                    c = s.int16()/16384.0
                    d = s.int16()/16384.0
                if flags & 200: # 8 + 64 + 128
                    if flags & 2048: # SCALED_COMPONENT_OFFSET
                        e *= hypot(a, c)
                        f *= hypot(b, d)
                component = self.glyf(glyphIndex)
                for command in component:
                    command.transform(a, b, c, d, e, f)
                result.extend(component)
                if flags & 32 == 0: # MORE_COMPONENTS
                    break
        return result
    
    def head(self):
        self.find(b'head')
        return head(self.readable)
    
    def hhea(self):
        self.find(b'hhea')
        return hhea(self.readable)
    
    def maxp(self):
        self.find(b'maxp')
        return maxp(self.readable)
    
    def os2(self):
        self.find(b'OS/2')
        return os2(self.readable)
        
    def post(self):
        self.find(b'post')
        return post(self.readable)




class offset(object):
    
    def __init__(self, readable):
        self.sfntVersion = readable.uint32()
        self.numTables = readable.uint16()
        self.searchRange = readable.uint16()
        self.entrySelector = readable.uint16()
        self.rangeShift = readable.uint16()

class record(object):
    
    def __init__(self, readable):
        self.tag = readable.read(4)
        self.checkSum = readable.uint32()
        self.offset = readable.uint32()
        self.length = readable.uint32()




class head(object):
    
    def __init__(self, readable):
        self.majorVersion = readable.uint16()
        self.minorVersion = readable.uint16()
        self.fontRevision = readable.int32()
        self.checkSumAdjustment = readable.uint32()
        self.magicNumber = readable.uint32()
        self.flags = readable.uint16()
        self.unitsPerEm = readable.uint16()
        self.created = readable.parse('>q') # int64
        self.modified = readable.parse('>q')
        self.xMin = readable.int16()
        self.yMin = readable.int16()
        self.xMax = readable.int16()
        self.yMax = readable.int16()
        self.macStyle = readable.uint16()
        self.lowestRecPPEM = readable.uint16()
        self.fontDirectionHint = readable.int16()
        self.indexToLocFormat = readable.int16()
        self.glyphDataFormat = readable.int16()

class hhea(object):
    
    def __init__(self, readable):
        self.majorVersion = readable.uint16()
        self.minorVersion = readable.uint16()
        self.Ascender = readable.int16()
        self.Descender = readable.int16()
        self.LineGap = readable.int16()
        self.advanceWidthMax = readable.uint16()
        self.minLeftSideBearing = readable.int16()
        self.minRightSideBearing = readable.int16()
        self.xMaxExtent = readable.int16()
        self.caretSlopeRise = readable.int16()
        self.caretSlopeRun = readable.int16()
        self.caretOffset = readable.int16()
        readable.skip(2 + 2 + 2 + 2) # reserved
        self.metricDataFormat = readable.int16()
        self.numberOfHMetrics = readable.uint16()

class maxp(object):
    
    def __init__(self, readable):
        self.version = readable.int32()
        self.numGlyphs = readable.uint16()

class os2(object):
    
    def __init__(self, readable):
        self.version = readable.uint16()
        self.xAvgCharWidth = readable.int16()
        self.usWeightClass = readable.uint16()
        self.usWidthClass = readable.uint16()
        self.fsType = readable.uint16()
        self.ySubscriptXSize = readable.int16()
        self.ySubscriptYSize = readable.int16()
        self.ySubscriptXOffset = readable.int16()
        self.ySubscriptYOffset = readable.int16()
        self.ySuperscriptXSize = readable.int16()
        self.ySuperscriptYSize = readable.int16()
        self.ySuperscriptXOffset = readable.int16()
        self.ySuperscriptYOffset = readable.int16()
        self.yStrikeoutSize = readable.int16()
        self.yStrikeoutPosition = readable.int16()
        self.sFamilyClass = readable.int16()
        self.bFamilyType = readable.uint8()
        self.bSerifStyle = readable.uint8()
        self.bWeight = readable.uint8()
        self.bProportion = readable.uint8()
        self.bContrast = readable.uint8()
        self.bStrokeVariation = readable.uint8()
        self.bArmStyle = readable.uint8()
        self.bLetterform = readable.uint8()
        self.bMidline = readable.uint8()
        self.bXHeight = readable.uint8()
        self.ulUnicodeRange1 = readable.uint32()
        self.ulUnicodeRange2 = readable.uint32()
        self.ulUnicodeRange3 = readable.uint32()
        self.ulUnicodeRange4 = readable.uint32()
        self.achVendID = readable.read(4)
        self.fsSelection = readable.uint16()
        self.usFirstCharIndex = readable.uint16()
        self.usLastCharIndex = readable.uint16()
        self.sTypoAscender = readable.int16()
        self.sTypoDescender = readable.int16()
        self.sTypoLineGap = readable.int16()
        self.usWinAscent = readable.uint16()
        self.usWinDescent = readable.uint16()
        self.ulCodePageRange1 = readable.uint16()
        self.ulCodePageRange2 = readable.uint16()
        self.sxHeight = readable.int16()
        self.sCapHeight = readable.int16()
        self.usDefaultChar = readable.uint16()
        self.usBreakChar = readable.uint16()
        self.usMaxContext = readable.uint16()
        self.usLowerOpticalPointSize = readable.uint16()
        self.usUpperOpticalPointSize = readable.uint16()

class post(object):
    
    def __init__(self, readable):
        self.version = readable.int32()
        self.italicAngle = readable.int32()
        self.underlinePosition = readable.int16()
        self.underlineThickness = readable.int16()
        self.isFixedPitch = readable.uint32()
        self.minMemType42 = readable.uint32()
        self.maxMemType42 = readable.uint32()
        self.minMemType1 = readable.uint32()
        self.maxMemType1 = readable.uint32()




def _parse_coverage(readable):
    coverage = []
    CoverageFormat = readable.uint16()
    if CoverageFormat == 1:
        GlyphCount = readable.uint16()
        for i in range(GlyphCount):
            Glyph = readable.uint16()
            coverage.append(Glyph)
    elif CoverageFormat == 2:
        RangeCount = readable.uint16()
        for i in range(RangeCount):
            StartGlyphID = readable.uint16()
            EndGlyphID = readable.uint16()
            readable.skip(2) # StartCoverageIndex
            coverage.extend(range(StartGlyphID, EndGlyphID + 1))
    else:
        raise ValueError('Invalid CoverageFormat.')
    return coverage

def _parse_classdefinition(readable, count):
    definition = [[] for i in range(count)]
    ClassFormat = readable.uint16()
    if ClassFormat == 1:
        StartGlyphID = readable.uint16()
        GlyphCount = readable.uint16()
        for i in range(StartGlyphID, StartGlyphID + GlyphCount):
            ClassValue = readable.uint16()
            definition[ClassValue].append(i)
    elif ClassFormat == 2:
        ClassRangeCount = readable.uint16()
        for i in range(ClassRangeCount):
            StartGlyphID = readable.uint16()
            EndGlyphID = readable.uint16()
            Class = readable.uint16()
            definition[Class].extend(range(StartGlyphID, EndGlyphID + 1))
    else:
        raise ValueError('Invalid ClassFormat.')
    return definition




