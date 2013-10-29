
from functools import reduce
from os import urandom

from .color import cmyk, spot, _default_color
from .pdfobjects import number, string, hexstring, name, safename, \
    array, dictionary, obj, stream, lazyreference
from .png import png
from .shape import shape
from .utils import chunks, powerset, record, scale




class _named_resource(object):
    
    __slots__ = 'name', 'obj', 'reference'
    
    def __init__(self, name, obj):
        self.name = name
        self.obj = obj
        self.reference = lazyreference(obj)




def _key_space(color):
    if type(color) == spot:
        return color.name
    return color.names

def _key_font(font):
    return font.name

def _key_image(image):
    if type(image.source) == png:
        return image.source.idat()
    return image.jpeg()

def _key_state(state):
    return tuple(sorted(state))


def _cmyk_samples(color):
    return ''.join(chr(int(round(tint * 2.55))) for tint in color.tints)

def _cmyk_add(left, right):
    return cmyk(*((a + b - a * b) * 100.0 for a, b in [
        (a / 100.0, b / 100.0) for a, b in zip(left.tints, right.tints)]))


class _document_resources(object):
    
    def __init__(self):
        self.items = {}
        self.spaces = {}
        self.fonts = {}
        self.images = {}
        self.states = {}
        self.dependencies = []
    
    def get(self, item, key, constructor, cache):
        if item not in self.items:
            data = key(item)
            if data not in cache:
                cache[data] = constructor(item, data)
            self.items[item] = cache[data]
        return self.items[item]
    
    def _ctor_space(self, color, data):
        samples = _cmyk_samples(cmyk(0, 0, 0, 0))
        if type(color) == spot:
            kind = name('Separation')
            colorants = safename(color.name)
            size = 1
            samples += _cmyk_samples(color.fallback)
        else:
            kind = name('DeviceN')
            colorants = array(map(safename, color.names))
            size = len(color.names)
            samples += ''.join(_cmyk_samples(reduce(_cmyk_add, s))
                for s in powerset(color.fallbacks)[1:])
        transform = stream(0, {
            'FunctionType': number(0),
            'Domain': array([number(0), number(1)] * size),
            'Range': array([number(0), number(1)] * 4),
            'Size': array([number(2)] * size),
            'BitsPerSample': number(8),
            'Length': number(len(samples))}, samples)
        self.dependencies.append(transform)
        return _named_resource(
            'C%d' % len(self.spaces),
            obj(0, array([
                kind,
                colorants,
                name('DeviceCMYK'),
                lazyreference(transform)])))
    
    def _ctor_font(self, font, data):
        advances, charmap, otf, psname = \
            font.advances, font.charmap, font.source, font.name
        cff, head, os2, post = otf.cff, otf.head, otf.os2, otf.post
        k = font.density * 1000.0
        
        ascent = os2.sTypoAscender * k
        capheight = os2.sCapHeight * k
        descent = os2.sTypoDescender * k
        flags = 4
        if post.isFixedPitch:
            flags |= 1
        if os2.sFamilyClass >> 8 in (1, 2, 3, 4, 5, 7):
            flags |= 2
        if os2.sFamilyClass >> 8 == 10:
            flags |= 8
        if head.macStyle & 2:
            flags |= 64
        bbox = head.xMin * k, head.yMin * k, head.xMax * k, head.yMax * k
        italic = post.italicAngle / 65536.0
        stemv = 0
        
        widths = [advances[i] * k for i in range(max(charmap.values()) + 1)]
        defaultwidth = font.defaultadvance
        
        glyphmap = [(index, code) for code, index in charmap.items()]
        glyphmap.sort()
        glyphmap.pop(0)
        
        fontfiledata = otf.embed()
        d = {'Length': number(len(fontfiledata))}
        if cff:
            d['Subtype'] = name('CIDFontType0C')
        else:
            d['Length1'] = number(len(fontfiledata))
        fontfile = stream(0, d, fontfiledata)
        
        descriptor = obj(0, dictionary({
            'Type': name('FontDescriptor'),
            'Ascent': number(ascent),
            'CapHeight': number(capheight),
            'Descent': number(descent),
            'Flags': number(flags),
            'FontBBox': array(map(number, bbox)),
            'FontName': name(psname),
            'ItalicAngle': number(italic),
            'StemV': number(stemv),
            'FontFile3' if cff else 'FontFile2': lazyreference(fontfile)}))
        
        tounicodedata = '\n'.join((
            '/CIDInit /ProcSet findresource begin',
            '12 dict begin',
            'begincmap',
            '/CIDSystemInfo << /Registry (%s) /Ordering (%s) /Supplement 0 >> def' % (
                psname, psname),
            '/CMapName /%s def' % psname,
            '/CMapType 2 def',
            '1 begincodespacerange <0000><ffff> endcodespacerange',
            '\n'.join('%d beginbfchar %s endbfchar' % (len(chunk), ''.join(
                '<%04x><%04x>' % c for c in chunk)) for chunk in chunks(glyphmap, 100)),
            'endcmap',
            'CMapName currentdict /CMap defineresource pop',
            'end',
            'end'))
        tounicode = stream(0, {
            'Length': number(len(tounicodedata))}, tounicodedata)
        
        self.dependencies.extend((fontfile, descriptor, tounicode))
        
        return _named_resource(
            'F%d' % len(self.fonts),
            obj(0, dictionary({
                'Type': name('Font'),
                'Subtype': name('Type0'),
                'BaseFont': name(psname),
                'Encoding': name('Identity-H'),
                'DescendantFonts': array([dictionary({
                    'Type': name('Font'),
                    'Subtype': name('CIDFontType0' if cff else 'CIDFontType2'),
                    'BaseFont': name(psname),
                    'CIDSystemInfo': dictionary({
                        'Registry': string('Adobe'),
                        'Ordering': string('Identity'),
                        'Supplement': number(0)}),
                    'FontDescriptor': lazyreference(descriptor),
                    'DW': number(defaultwidth),
                    'W': array([number(0), array(map(number, widths))]),
                    'CIDToGIDMap': name('Identity')})]),
                'ToUnicode': lazyreference(tounicode)})))
    
    def _ctor_image(self, image, data):
        assert image.kind in ('g', 'rgb', 'cmyk'), 'Unsupported image kind.'
        p = type(image.source) == png
        d = {
            'Type': name('XObject'),
            'Subtype': name('Image'),
            'Width': number(image.width),
            'Height': number(image.height),
            'ColorSpace': name(
                'DeviceGray' if image.kind == 'g' else \
                'DeviceRGB' if image.kind == 'rgb' else 'DeviceCMYK'),
            'BitsPerComponent': number(8),
            'Filter': name('FlateDecode' if p else 'DCTDecode'),
            'Length': number(len(data))}
        if image.kind == 'cmyk':
            d['Decode'] = array(map(number, [1, 0, 1, 0, 1, 0, 1, 0]))
        if p:
            d['DecodeParms'] = dictionary({
                'Predictor': number(15),
                'Colors': number(image.count),
                'BitsPerComponent': number(8),
                'Columns': number(image.width)})
        return _named_resource(
            'I%d' % len(self.images),
            stream(0, d, data))
    
    def _ctor_state(self, state, data):
        return _named_resource(
            'G%d' % len(self.states),
            obj(0, dictionary(dict(
                (key, factory(value)) for key, factory, value in state))))
    
    def space(self, color):
        return self.get(color, _key_space, self._ctor_space, self.spaces)
    
    def font(self, font):
        return self.get(font, _key_font, self._ctor_font, self.fonts)
    
    def image(self, image):
        return self.get(image, _key_image, self._ctor_image, self.images)
    
    def state(self, state):
        return self.get(state, _key_state, self._ctor_state, self.states)
    
    def pageresources(self, spaces, fonts, images, states):
        resources = {}
        procedures = ['PDF']
        if spaces:
            resources['ColorSpace'] = dictionary(dict(
                (r.name, r.reference) for r in spaces))
        if fonts:
            resources['Font'] = dictionary(dict(
                (r.name, r.reference) for r in fonts))
            procedures.append('Text')
        if images:
            resources['XObject'] = dictionary(dict(
                (r.name, r.reference) for r in images))
            procedures.extend(['ImageB', 'ImageC', 'ImageI'])
        if states:
            resources['ExtGState'] = dictionary(dict(
                (r.name, r.reference) for r in states))
        resources['ProcSet'] = array(map(name, procedures))
        return dictionary(resources)
    
    def objects(self):
        return [resource.obj for kind in (
            self.spaces,
            self.fonts,
            self.images,
            self.states) for resource in kind.values()] + self.dependencies




def _page_boxes(document, page):
    w, h, mm = page.width, page.height, scale('mm')
    if document.cropmarks:
        if document.bleed:
            media = 0, 0, w + 10*mm, h + 10*mm
            bleed = 2*mm, 2*mm, w + 8*mm, h + 8*mm
            trim = 5*mm, 5*mm, w + 5*mm, h + 5*mm
        else:
            media = 0, 0, w + 10*mm, h + 10*mm
            bleed = trim = 5*mm, 5*mm, w + 5*mm, h + 5*mm
    else:
        if document.bleed:
            media = bleed = 0, 0, w + 6*mm, h + 6*mm
            trim = 3*mm, 3*mm, w + 3*mm, h + 3*mm
        else:
            media = bleed = trim = 0, 0, w, h
    return (
        array(map(number, media)),
        array(map(number, bleed)),
        array(map(number, trim)))


def _pdf_body(document):
    
    pagesreference = lazyreference(None)
    
    root = obj(0, dictionary({
        'Type': name('Catalog'),
        'Pages': pagesreference}))
    
    info = obj(0, dictionary({
        'Title': string(document.title),
        'Producer': string('flat')}))
    
    resources = _document_resources()
    
    contents = []
    kids = []
    default = shape().stroke(_default_color).fill(_default_color)
    previous = record(
        shape=None,
        strokecolor=None, fillcolor=None,
        fontname='', textsize=0.0)
    for page in document.pages:
        previous.shape = default
        previous.strokecolor, previous.fillcolor = \
            default.strokecolor, default.fillcolor
        previous.fontname, previous.textsize = '', 0.0
        spaces, fonts, images, states = set(), set(), set(), set()
        
        height = page.height
        commands = '\n'.join([
            item.pdf(
                previous,
                resources,
                spaces, fonts, images, states,
                height) for item in page.items])
        
        content = stream(0, {'Length': number(len(commands))}, commands)
        contents.append(content)
        
        media, bleed, trim = _page_boxes(document, page)
        kids.append(obj(0, dictionary({
            'Type': name('Page'),
            'Parent': pagesreference,
            'MediaBox': media,
            'BleedBox': bleed,
            'TrimBox': trim,
            'Resources': resources.pageresources(spaces, fonts, images, states),
            'Contents': lazyreference(content)})))
    
    pages = pagesreference.obj = obj(0, dictionary({
        'Type': name('Pages'),
        'Kids': array([lazyreference(kid) for kid in kids]),
        'Count': number(len(kids))}))
    
    objects = [root, info, pages] + kids + resources.objects() + contents
    
    for i, o in enumerate(objects, 1):
        o.tag = i
    
    body = ['%s\n' % o.pdf() for o in objects]
    
    return root, info, body




def dump(document):
    
    header = '%PDF-1.3\n'
    
    root, info, body = _pdf_body(document)
    
    position = len(header)
    offsets = ['0000000000 65535 f \n']
    for chunk in body:
        offsets.append('%010d 00000 n \n' % position)
        position += len(chunk)
    xref = (
        'xref\n'
        '0 %d\n'
        '%s') % (len(body) + 1, ''.join(offsets))
    
    trailer = (
        'trailer %s \n'
        'startxref\n'
        '%d\n'
        '%%%%EOF') % (
            dictionary({
                'ID': array([hexstring(urandom(16))] * 2),
                'Root': lazyreference(root),
                'Info': lazyreference(info),
                'Size': number(len(body))}).pdf(),
            sum(len(chunk) for chunk in body))
    
    return ''.join([header] + body + [xref, trailer])




