from __future__ import division
from binascii import hexlify
from os import urandom
from .color import gray
from .misc import chunks, dump, scale
from .png import png




class null(object):
    
    def pdf(self):
        return ''

class boolean(object):
    
    def __init__(self, value):
        self.value = value
    
    def pdf(self):
        return 'true' if self.value else 'false'

class number(object):
    
    def __init__(self, number):
        self.number = number
    
    def pdf(self):
        return dump(self.number)

class string(object):
    
    def __init__(self, string):
        self.string = string
    
    def pdf(self):
        return '(%s)' % self.string

class hexstring(object):

    def __init__(self, string):
        self.string = string

    def pdf(self):
        return '<%s>' % hexlify(self.string)

class name(object):
    
    def __init__(self, name):
        self.name = name
    
    def pdf(self):
        special = '#()<>[]{}/%'
        characters = ['/']
        for c in self.name:
            if c < '!' or c > '~' or c in special:
                c = '#%x' % ord(c)
            characters.append(c)
        return ''.join(characters)

class array(object):
    
    def __init__(self, array):
        self.array = array
    
    def pdf(self):
        return '[%s]' % ' '.join(item.pdf() for item in self.array)

class dictionary(object):
    
    def __init__(self, dictionary):
        self.dictionary = dictionary
    
    def pdf(self):
        return '<< %s >>' % ' '.join(
            '/%s %s' % (k, v.pdf()) for k, v in self.dictionary.items())

class obj(object):

    def __init__(self, tag, item):
        self.tag = tag
        self.item = item
    
    def pdf(self):
        return (
            '%d 0 obj\n'
            '%s\n'
            'endobj') % (self.tag, self.item.pdf())

class stream(object):
    
    def __init__(self, tag, dictionary, stream):
        self.tag = tag
        self.dictionary = dictionary
        self.stream = stream
    
    def pdf(self):
        d = dictionary(self.dictionary)
        return (
            '%d 0 obj\n'
            '%s\n'
            'stream\n'
            '%s\n'
            'endstream\n'
            'endobj') % (self.tag, d.pdf(), self.stream)

class reference(object):
    
    def __init__(self, obj):
        self.obj = obj
    
    def pdf(self):
        return '%d 0 R' % self.obj.tag




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
        self.name = ''
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
                    'C%d' % len(self.spaces),
                    obj(0, array([
                        name('Separation'),
                        name(color.name),
                        name('DeviceCMYK'),
                        dictionary({
                            'FunctionType': number(2),
                            'Domain': array([number(0), number(1)]),
                            'Range': array([number(0), number(1)]*4),
                            'C0': array([number(0)]*4),
                            'C1': array([
                                number(color.fallback.c/100.0),
                                number(color.fallback.m/100.0),
                                number(color.fallback.y/100.0),
                                number(color.fallback.k/100.0)]),
                            'N': number(1)})])))
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
                    'Length': number(len(fontfiledata)),
                    'Subtype' if cff else \
                    'Length1':
                        name('CIDFontType0C') if cff else \
                        number(len(fontfiledata))}, fontfiledata)
                descriptor = obj(0, dictionary({
                    'Type': name('FontDescriptor'),
                    'Ascent': number(ascent),
                    'CapHeight': number(capheight),
                    'Descent': number(descent),
                    'Flags': number(flags),
                    'FontBBox': array(map(number, bbox)),
                    'FontName': name(font.name),
                    'ItalicAngle': number(italic),
                    'StemV': number(stemv),
                    'FontFile3' if cff else 'FontFile2': reference(fontfile)}))
                tounicodedata = (
                    '/CIDInit /ProcSet findresource begin\n'
                    '12 dict begin\n'
                    'begincmap\n'
                    '/CIDSystemInfo << /Registry (%s) /Ordering (%s) /Supplement 0 >> def\n'
                    '/CMapName /%s def\n'
                    '/CMapType 2 def\n'
                    '1 begincodespacerange <0000><ffff> endcodespacerange\n'
                    '%s'
                    'endcmap\n'
                    'CMapName currentdict /CMap defineresource pop\n'
                    'end\n'
                    'end') % (font.name, font.name, font.name, ''.join(
                        '%d beginbfchar %s endbfchar\n' % (
                            len(chunk), ''.join('<%04x><%04x>' % c for c in chunk)
                        ) for chunk in chunks(font.glyphmap(), 100)))
                tounicode = stream(0, {
                    'Length': number(len(tounicodedata))}, tounicodedata)
                self.dependencies.extend((fontfile, descriptor, tounicode))
                self.cache[key] = _named_resource(
                    'F%d' % len(self.fonts),
                    obj(0, dictionary({
                        'Type': name('Font'),
                        'Subtype': name('Type0'),
                        'BaseFont': name(font.name),
                        'Encoding': name('Identity-H'),
                        'DescendantFonts': array([dictionary({
                            'Type': name('Font'),
                            'Subtype': name('CIDFontType0' if cff else 'CIDFontType2'),
                            'BaseFont': name(font.name),
                            'CIDSystemInfo': dictionary({
                                'Registry': string('Adobe'),
                                'Ordering': string('Identity'),
                                'Supplement': number(0)}),
                            'FontDescriptor': reference(descriptor),
                            'DW': number(defaultwidth),
                            'W': array([number(0), array(map(number, widths))]),
                            'CIDToGIDMap': name('Identity')})]),
                        'ToUnicode': reference(tounicode)})))
            self.fonts[key] = self.cache[key]
        return self.fonts[key]
    
    def image(self, image):
        if isinstance(image.source, png):
            key = data = image.source.idat()
            flate = True
        else:
            key = data = image.jpeg()
            flate = False
        key = bytes(key) # TODO python 3: remove bytes
        if key not in self.images:
            if key not in self.cache:
                setup = {
                    'Type': name('XObject'),
                    'Subtype': name('Image'),
                    'Width': number(image.width),
                    'Height': number(image.height),
                    'ColorSpace': name(
                        'DeviceGray' if image.kind == 'g' else \
                        'DeviceRGB' if image.kind == 'rgb' else 'DeviceCMYK'),
                    'BitsPerComponent': number(8),
                    'Filter': name('FlateDecode' if flate else 'DCTDecode'),
                    'Length': number(len(data))}
                if image.kind == 'cmyk':
                    setup['Decode'] = array(map(number, [1, 0, 1, 0, 1, 0, 1, 0]))
                if flate:
                    setup['DecodeParms'] = dictionary({
                        'Predictor': number(15),
                        'Colors': number(image.n),
                        'BitsPerComponent': number(8),
                        'Columns': number(image.width)})
                self.cache[key] = _named_resource(
                    'I%d' % len(self.images),
                    stream(0, setup, data))
            self.images[key] = self.cache[key]
        return self.images[key]
    
    def overprint(self, stroke, fill):
        key = stroke, fill
        if key not in self.states:
            if key not in self.cache:
                self.cache[key] = _named_resource(
                    'G%d' % len(self.states),
                    obj(0, dictionary({
                        'OP': boolean(stroke),
                        'op': boolean(fill),
                        'OPM': number(1)})))
            self.states[key] = self.cache[key]
        return self.states[key]
    
    def references(self):
        resources = {}
        procedures = ['PDF']
        if self.spaces:
            resources['ColorSpace'] = dictionary(
                {r.name: r.reference for r in self.spaces.values()})
        if self.fonts:
            resources['Font'] = dictionary(
                {r.name: r.reference for r in self.fonts.values()})
            procedures.append('Text')
        if self.images:
            resources['XObject'] = dictionary(
                {r.name: r.reference for r in self.images.values()})
            procedures.extend(['ImageB', 'ImageC', 'ImageI'])
        if self.states:
            resources['ExtGState'] = dictionary(
                {r.name: r.reference for r in self.states.values()})
        resources['ProcSet'] = array(map(name, procedures))
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
        fragments = ['q', '0.25 w']
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
            fragments.append('%s %s m %s %s l S' % (
                dump(x0), dump(y0), dump(x1), dump(y1)))
        fragments.append('Q')
        fragments.append('q 1 0 0 1 %s %s cm' % (dump(5*mm), dump(5*mm)))
        prefix = '\n'.join(fragments)
    elif bleed:
        prefix = 'q 1 0 0 1 %s %s cm' % (dump(3*mm), dump(3*mm))
    return prefix, 'Q'

def serialize(document, compress, bleed, cropmarks):
    header = '%PDF-1.3\n'
    pagesreference = reference(None)
    kids = []
    contents = []
    state, resources = _graphic_state(), _document_resources()
    for page in document.pages:
        mediabox, bleedbox, trimbox = _page_boxes(bleed, cropmarks, page)
        state.reset(); resources.reset()
        code = '\n'.join(
            item.pdf(page.height, state, resources) for item in page.items)
        if bleed or cropmarks:
            prefix, postfix = _page_fixes(bleed, cropmarks, page)
            code = '%s\n%s\n%s' % (prefix, code, postfix)
        content = stream(0, {'Length': number(len(code))}, code)
        kid = obj(0, dictionary({
            'Type': name('Page'),
            'Parent': pagesreference,
            'MediaBox': mediabox,
            'BleedBox': bleedbox,
            'TrimBox': trimbox,
            'Resources': resources.references(),
            'Contents': reference(content)}))
        kids.append(kid)
        contents.append(content)
    root = obj(0, dictionary({
        'Type': name('Catalog'),
        'Pages': pagesreference}))
    info = obj(0, dictionary({
        'Title': string(document.title),
        'Producer': string('Flat')}))
    pages = pagesreference.obj = obj(0, dictionary({
        'Type': name('Pages'),
        'Kids': array([reference(kid) for kid in kids]),
        'Count': number(len(kids))}))
    objects = [root, info, pages] + kids + resources.objects() + contents
    for i, o in enumerate(objects, 1):
        o.tag = i
    fragments = ['%s\n' % o.pdf() for o in objects]
    position = len(header)
    offsets = ['0000000000 65535 f \n']
    for fragment in fragments:
        offsets.append('%010d 00000 n \n' % position)
        position += len(fragment)
    xref = (
        'xref\n'
        '0 %d\n'
        '%s') % (len(objects) + 1, ''.join(offsets))
    trailer = (
        'trailer %s\n'
        'startxref\n'
        '%d\n'
        '%%%%EOF') % (
            dictionary({
                'ID': array([hexstring(urandom(16))]*2),
                'Root': reference(root),
                'Info': reference(info),
                'Size': number(len(offsets))}).pdf(),
            position)
    return ''.join([header] + fragments + [xref, trailer])




