from binascii import hexlify
from os import urandom
from .color import gray
from .misc import chunks, dump, scale
from .png import png




class null(object):
    
    def pdf(self):
        return b''

class boolean(object):
    
    def __init__(self, value):
        self.value = value
    
    def pdf(self):
        return b'true' if self.value else b'false'

class number(object):
    
    def __init__(self, number):
        self.number = number
    
    def pdf(self):
        return dump(self.number)

class string(object):
    
    def __init__(self, string):
        self.string = string
    
    def pdf(self):
        special = b'()\\'
        characters = [b'(']
        for c in self.string:
            if c < 0x21 or c > 0x7e: # '!', '~'
                c = b'\\%03o' % c
            elif c in special:
                c = b'\\%c' % c
            else:
                c = b'%c' % c
            characters.append(c)
        characters.append(b')')
        return b''.join(characters)

class hexstring(object):

    def __init__(self, string):
        self.string = string

    def pdf(self):
        return b'<%s>' % hexlify(self.string)

class name(object):
    
    def __init__(self, name):
        self.name = name
    
    def pdf(self):
        special = b'#()<>[]{}/%'
        characters = [b'/']
        for c in self.name:
            if c < 0x21 or c > 0x7e or c in special: # '!', '~'
                c = b'#%02x' % c
            else:
                c = b'%c' % c
            characters.append(c)
        return b''.join(characters)

class array(object):
    
    def __init__(self, array):
        self.array = array
    
    def pdf(self):
        return b'[%s]' % b' '.join(item.pdf() for item in self.array)

class dictionary(object):
    
    def __init__(self, dictionary):
        self.dictionary = dictionary
    
    def pdf(self):
        return b'<< %s >>' % b' '.join(
            b'/%s %s' % (k, v.pdf()) for k, v in self.dictionary.items())

class obj(object):

    def __init__(self, tag, item):
        self.tag = tag
        self.item = item
    
    def pdf(self):
        return (
            b'%d 0 obj\n'
            b'%s\n'
            b'endobj') % (self.tag, self.item.pdf())

class stream(object):
    
    def __init__(self, tag, dictionary, stream):
        self.tag = tag
        self.dictionary = dictionary
        self.stream = stream
    
    def pdf(self):
        d = dictionary(self.dictionary)
        return (
            b'%d 0 obj\n'
            b'%s\n'
            b'stream\n'
            b'%s\n'
            b'endstream\n'
            b'endobj') % (self.tag, d.pdf(), self.stream)

class reference(object):
    
    def __init__(self, obj):
        self.obj = obj
    
    def pdf(self):
        return b'%d 0 R' % self.obj.tag




class _graphic_state(object):
    
    __slots__ = 'stroke', 'fill', 'width', 'cap', 'join', 'limit', 'name', 'size'
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.stroke = self.fill = gray(0)
        self.width = 1.0
        self.cap = 'butt'
        self.join = 'miter'
        self.limit = 10.0
        self.name = b''
        self.size = 0.0




class _named_resource(object):
    
    __slots__ = 'name', 'reference'
    
    def __init__(self, name, obj):
        self.name, self.reference = name, reference(obj)

class _document_resources(object):
    
    def __init__(self):
        self.cache = {}
        self.spaces = {}
        self.fonts = {}
        self.images = {}
        self.states = {}
        self.dependencies = []
    
    def reset(self):
        self.spaces.clear()
        self.fonts.clear()
        self.images.clear()
        self.states.clear()
    
    def space(self, color):
        key = color.name
        if key not in self.spaces:
            if key not in self.cache:
                self.cache[key] = _named_resource(
                    b'C%d' % len(self.spaces),
                    obj(0, array([
                        name(b'Separation'),
                        name(color.name.encode('utf-8')),
                        name(b'DeviceCMYK'),
                        dictionary({
                            b'FunctionType': number(2),
                            b'Domain': array([number(0), number(1)]),
                            b'Range': array([number(0), number(1)]*4),
                            b'C0': array([number(0)]*4),
                            b'C1': array([
                                number(color.fallback.c/100.0),
                                number(color.fallback.m/100.0),
                                number(color.fallback.y/100.0),
                                number(color.fallback.k/100.0)]),
                            b'N': number(1)})])))
            self.spaces[key] = self.cache[key]
        return self.spaces[key]
    
    def font(self, font):
        key = font.name
        if key not in self.fonts:
            if key not in self.cache:
                otf, cff = font.source, font.source.cff
                head, os2, post = otf.head(), otf.os2(), otf.post()
                k = 1000.0/font.density
                ascent = os2.sTypoAscender*k
                capheight = os2.sCapHeight*k
                descent = os2.sTypoDescender*k
                flags = 4
                if post.isFixedPitch:
                    flags |= 1
                if os2.sFamilyClass >> 8 in (1, 2, 3, 4, 5, 7):
                    flags |= 2
                if os2.sFamilyClass >> 8 == 10:
                    flags |= 8
                if head.macStyle & 2:
                    flags |= 64
                bbox = head.xMin*k, head.yMin*k, head.xMax*k, head.yMax*k
                italic = post.italicAngle/65536.0
                stemv = 0
                last = max(font.charmap.values())
                widths = [font.advances[i]*k for i in range(last + 1)]
                defaultwidth = font.advances[-1]*k
                fontfiledata = otf.embed()
                fontfile = stream(0, {
                    b'Length': number(len(fontfiledata)),
                    b'Subtype' if cff else \
                    b'Length1':
                        name(b'CIDFontType0C') if cff else \
                        number(len(fontfiledata))}, fontfiledata)
                descriptor = obj(0, dictionary({
                    b'Type': name(b'FontDescriptor'),
                    b'Ascent': number(ascent),
                    b'CapHeight': number(capheight),
                    b'Descent': number(descent),
                    b'Flags': number(flags),
                    b'FontBBox': array(map(number, bbox)),
                    b'FontName': name(font.name),
                    b'ItalicAngle': number(italic),
                    b'StemV': number(stemv),
                    b'FontFile3' if cff else b'FontFile2': reference(fontfile)}))
                tounicodedata = (
                    b'/CIDInit /ProcSet findresource begin\n'
                    b'12 dict begin\n'
                    b'begincmap\n'
                    b'/CIDSystemInfo << /Registry (%s) /Ordering (%s) /Supplement 0 >> def\n'
                    b'/CMapName /%s def\n'
                    b'/CMapType 2 def\n'
                    b'1 begincodespacerange <0000><ffff> endcodespacerange\n'
                    b'%s'
                    b'endcmap\n'
                    b'CMapName currentdict /CMap defineresource pop\n'
                    b'end\n'
                    b'end') % (font.name, font.name, font.name, b''.join(
                        b'%d beginbfchar %s endbfchar\n' % (
                            len(chunk), b''.join(b'<%04x><%04x>' % c for c in chunk)
                        ) for chunk in chunks(font.glyphmap(), 100)))
                tounicode = stream(0, {
                    b'Length': number(len(tounicodedata))}, tounicodedata)
                self.dependencies.extend((fontfile, descriptor, tounicode))
                self.cache[key] = _named_resource(
                    b'F%d' % len(self.fonts),
                    obj(0, dictionary({
                        b'Type': name(b'Font'),
                        b'Subtype': name(b'Type0'),
                        b'BaseFont': name(font.name),
                        b'Encoding': name(b'Identity-H'),
                        b'DescendantFonts': array([dictionary({
                            b'Type': name(b'Font'),
                            b'Subtype': name(b'CIDFontType0' if cff else b'CIDFontType2'),
                            b'BaseFont': name(font.name),
                            b'CIDSystemInfo': dictionary({
                                b'Registry': string(b'Adobe'),
                                b'Ordering': string(b'Identity'),
                                b'Supplement': number(0)}),
                            b'FontDescriptor': reference(descriptor),
                            b'DW': number(defaultwidth),
                            b'W': array([number(0), array(map(number, widths))]),
                            b'CIDToGIDMap': name(b'Identity')})]),
                        b'ToUnicode': reference(tounicode)})))
            self.fonts[key] = self.cache[key]
        return self.fonts[key]
    
    def image(self, image):
        if isinstance(image.source, png):
            key = data = image.source.idat()
            flate = True
        else:
            key = data = image.jpeg()
            flate = False
        if key not in self.images:
            if key not in self.cache:
                setup = {
                    b'Type': name(b'XObject'),
                    b'Subtype': name(b'Image'),
                    b'Width': number(image.width),
                    b'Height': number(image.height),
                    b'ColorSpace': name(
                        b'DeviceGray' if image.kind == 'g' else \
                        b'DeviceRGB' if image.kind == 'rgb' else b'DeviceCMYK'),
                    b'BitsPerComponent': number(8),
                    b'Filter': name(b'FlateDecode' if flate else b'DCTDecode'),
                    b'Length': number(len(data))}
                if image.kind == 'cmyk':
                    setup[b'Decode'] = array(map(number, [1, 0, 1, 0, 1, 0, 1, 0]))
                if flate:
                    setup[b'DecodeParms'] = dictionary({
                        b'Predictor': number(15),
                        b'Colors': number(image.n),
                        b'BitsPerComponent': number(8),
                        b'Columns': number(image.width)})
                self.cache[key] = _named_resource(
                    b'I%d' % len(self.images),
                    stream(0, setup, data))
            self.images[key] = self.cache[key]
        return self.images[key]
    
    def overprint(self, stroke, fill):
        key = stroke, fill
        if key not in self.states:
            if key not in self.cache:
                self.cache[key] = _named_resource(
                    b'G%d' % len(self.states),
                    obj(0, dictionary({
                        b'OP': boolean(stroke),
                        b'op': boolean(fill),
                        b'OPM': number(1)})))
            self.states[key] = self.cache[key]
        return self.states[key]
    
    def references(self):
        resources = {}
        procedures = [b'PDF']
        if self.spaces:
            resources[b'ColorSpace'] = dictionary(
                {r.name: r.reference for r in self.spaces.values()})
        if self.fonts:
            resources[b'Font'] = dictionary(
                {r.name: r.reference for r in self.fonts.values()})
            procedures.append(b'Text')
        if self.images:
            resources[b'XObject'] = dictionary(
                {r.name: r.reference for r in self.images.values()})
            procedures.extend([b'ImageB', b'ImageC', b'ImageI'])
        if self.states:
            resources[b'ExtGState'] = dictionary(
                {r.name: r.reference for r in self.states.values()})
        resources[b'ProcSet'] = array(map(name, procedures))
        return dictionary(resources)
    
    def objects(self):
        objects = [resource.reference.obj for resource in self.cache.values()]
        objects.extend(self.dependencies)
        return objects

def _page_boxes(bleed, cropmarks, page):
    w, h, mm = page.width, page.height, scale('mm')
    if cropmarks:
        if bleed:
            media = 0, 0, w+10*mm, h+10*mm
            bleed = 2*mm, 2*mm, w+8*mm, h+8*mm
            trim = 5*mm, 5*mm, w+5*mm, h+5*mm
        else:
            media = 0, 0, w+10*mm, h+10*mm
            bleed = trim = 5*mm, 5*mm, w+5*mm, h+5*mm
    else:
        if bleed:
            media = bleed = 0, 0, w+6*mm, h+6*mm
            trim = 3*mm, 3*mm, w+3*mm, h+3*mm
        else:
            media = bleed = trim = 0, 0, w, h
    return (
        array(map(number, media)),
        array(map(number, bleed)),
        array(map(number, trim)))

def _page_fixes(bleed, cropmarks, page):
    w, h, mm = page.width, page.height, scale('mm')
    if cropmarks:
        fragments = [b'q', b'0.25 w']
        lines = [
            (5*mm, 0, 5*mm, 2*mm),
            (5*mm, h+8*mm, 5*mm, h+10*mm),
            (w+5*mm, 0, w+5*mm, 2*mm),
            (w+5*mm, h+8*mm, w+5*mm, h+10*mm),
            (0, 5*mm, 2*mm, 5*mm),
            (w+8*mm, 5*mm, w+10*mm, 5*mm),
            (0, h+5*mm, 2*mm, h+5*mm),
            (w+8*mm, h+5*mm, w+10*mm, h+5*mm)]
        for x0, y0, x1, y1 in lines:
            fragments.append(b'%s %s m %s %s l S' % (
                dump(x0), dump(y0), dump(x1), dump(y1)))
        fragments.append(b'Q')
        fragments.append(b'q 1 0 0 1 %s %s cm' % (dump(5*mm), dump(5*mm)))
        prefix = b'\n'.join(fragments)
    elif bleed:
        prefix = b'q 1 0 0 1 %s %s cm' % (dump(3*mm), dump(3*mm))
    return prefix, b'Q'

def serialize(document, compress, bleed, cropmarks):
    header = b'%PDF-1.3\n'
    pagesreference = reference(None)
    kids = []
    contents = []
    state, resources = _graphic_state(), _document_resources()
    for page in document.pages:
        mediabox, bleedbox, trimbox = _page_boxes(bleed, cropmarks, page)
        state.reset(); resources.reset()
        code = b'\n'.join(
            item.pdf(page.height, state, resources) for item in page.items)
        if bleed or cropmarks:
            prefix, postfix = _page_fixes(bleed, cropmarks, page)
            code = b'%s\n%s\n%s' % (prefix, code, postfix)
        content = stream(0, {b'Length': number(len(code))}, code)
        kid = obj(0, dictionary({
            b'Type': name(b'Page'),
            b'Parent': pagesreference,
            b'MediaBox': mediabox,
            b'BleedBox': bleedbox,
            b'TrimBox': trimbox,
            b'Resources': resources.references(),
            b'Contents': reference(content)}))
        kids.append(kid)
        contents.append(content)
    root = obj(0, dictionary({
        b'Type': name(b'Catalog'),
        b'Pages': pagesreference}))
    info = obj(0, dictionary({
        b'Title': string(document.title.encode('utf-8')),
        b'Producer': string(b'Flat')}))
    pages = pagesreference.obj = obj(0, dictionary({
        b'Type': name(b'Pages'),
        b'Kids': array([reference(kid) for kid in kids]),
        b'Count': number(len(kids))}))
    objects = [root, info, pages] + kids + resources.objects() + contents
    for i, o in enumerate(objects, 1):
        o.tag = i
    fragments = [b'%s\n' % o.pdf() for o in objects]
    position = len(header)
    offsets = [b'0000000000 65535 f \n']
    for fragment in fragments:
        offsets.append(b'%010d 00000 n \n' % position)
        position += len(fragment)
    xref = (
        b'xref\n'
        b'0 %d\n'
        b'%s') % (len(objects) + 1, b''.join(offsets))
    trailer = (
        b'trailer %s\n'
        b'startxref\n'
        b'%d\n'
        b'%%%%EOF') % (
            dictionary({
                b'ID': array([hexstring(urandom(16))]*2),
                b'Root': reference(root),
                b'Info': reference(info),
                b'Size': number(len(offsets))}).pdf(),
            position)
    return b''.join([header] + fragments + [xref, trailer])




