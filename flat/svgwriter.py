
from itertools import groupby
from operator import itemgetter
from xml.sax.saxutils import escape

from .text import placedtext
from .utils import dump as utilsdump




def dump(page):
    fonts = ''.join(map(dumpfont, set(span.strike.font \
        for item in page.items \
            if type(item) == placedtext \
                for line, height in item.lines() \
                    for span, start, end, left in line)))
    if fonts:
        fonts = '<defs>\n%s\n</defs>\n' % fonts
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!-- flat -->\n'
        '<svg version="1.1" '
            'xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" '
            'width="%spt" height="%spt">\n'
        '<title>%s</title>\n'
        '%s%s\n'
        '</svg>') % (
            utilsdump(page.width), utilsdump(page.height),
            escape(page.document.title).encode('utf-8'),
            fonts, '\n'.join(item.svg() for item in page.items))




def _glyph_svg(source, index):
    return ' '.join([c.svg(1.0, 0.0, 0.0) for c in source.glyph(index)])

def dumpfont(font):
    source, advances = font.source, font.advances
    monospaced = len(advances) == advances.count(advances[0])
    second = itemgetter(1)
    glyphs, kerning = [], []
    for code, index in font.charmap.iteritems():
        if 31 < code < 65535:
            advance = '' if monospaced else ' horiz-adv-x="%d"' % advances[index]
            glyphs.append(
                '<glyph unicode="&#x%x;" glyph-name="%d"%s d="%s" />\n' % (
                    code, index, advance, _glyph_svg(source, index)))
            if font.kerning[index]:
                pairs = font.kerning[index].items()
                pairs.sort(key=second)
                for value, right in groupby(pairs, key=second):
                    kerning.append('<hkern g1="%d" g2="%s" k="%d" />\n' % (
                        index, ','.join(['%d' % r for r, v in right]), value))
    return (
        '<font horiz-adv-x="%d">\n'
        '<font-face font-family="%s" units-per-em="%d" ascent="%d" descent="%d" />\n'
        '<missing-glyph horiz-adv-x="%d" d="%s"/>\n'
        '%s%s'
        '</font>') % (
            font.defaultadvance,
            font.name, source.unitsperem(), font.ascender, font.descender,
            advances[0], _glyph_svg(source, 0),
            ''.join(glyphs), ''.join(kerning))




