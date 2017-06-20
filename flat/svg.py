from __future__ import division
from base64 import b64encode
from xml.sax.saxutils import escape
from .command import moveto, lineto, quadto, curveto, closepath
from .misc import dump
from .text import placedtext, placedoutlines
import re




def parsepath(data):
    tokens = re.compile('|'.join((
        r'([+-]?(?:\d*\.\d+|\d+\.?)(?:[eE][+-]?\d+)?)', # number
        r'([Mm])', # moveto
        r'([Zz])', # closepath
        r'([Ll])', # lineto
        r'([Hh])', # horizontal lineto
        r'([Vv])', # vertical lineto
        r'([Cc])', # curveto
        r'([Ss])', # smooth curveto
        r'([Qq])', # quadto
        r'([Tt])', # smooth quadto
        r'([Aa])'))) # elliptical arc
    counts = 0, 0, 2, 0, 2, 1, 1, 6, 4, 4, 2, 7
    
    result, arguments = [], []
    mx, my = px, py = 0.0, 0.0
    previous = None
    m = tokens.search(data)
    if not m or m.lastindex != 2: # moveto
        raise ValueError('Invalid path.')
    while m:
        index = m.lastindex
        count = counts[index]
        relative = m.group(index).islower()
        while True:
            for i in range(count - len(arguments)):
                m = tokens.search(data, m.end())
                if not m or m.lastindex != 1: # number
                    raise ValueError('Invalid argument.')
                arguments.append(float(m.group(1)))
            
            if index == 2: # moveto
                x, y = arguments
                if relative:
                    x += px; y += py
                mx, my = px, py = x, y
                previous = moveto(x, y)
                index = 4
            
            elif index == 3: # closepath
                px, py = mx, my
                previous = closepath
            
            elif index == 4: # lineto
                x, y = arguments
                if relative:
                    x += px; y += py
                px, py = x, y
                previous = lineto(x, y)
            
            elif index == 5: # horizontal lineto
                x, = arguments
                if relative:
                    x += px
                px = x
                previous = lineto(x, py)
            
            elif index == 6: # vertical lineto
                y, = arguments
                if relative:
                    y += py
                py = y
                previous = lineto(px, y)
            
            elif index == 7: # curveto
                x1, y1, x2, y2, x, y = arguments
                if relative:
                    x1 += px; y1 += py; x2 += px; y2 += py; x += px; y += py
                px, py = x, y
                previous = curveto(x1, y1, x2, y2, x, y)
            
            elif index == 8: # smooth curveto
                if type(previous) == curveto:
                    x1, y1 = px + px - previous.x2, py + py - previous.y2
                else:
                    x1, y1 = px, py
                x2, y2, x, y = arguments
                if relative:
                    x2 += px; y2 += py; x += px; y += py
                px, py = x, y
                previous = curveto(x1, y1, x2, y2, x, y)
            
            elif index == 9: # quadto
                x1, y1, x, y = arguments
                if relative:
                    x1 += px; y1 += py; x += px; y += py
                px, py = x, y
                previous = quadto(x1, y1, x, y)
            
            elif index == 10: # smooth quadto
                if type(previous) == quadto:
                    x1, y1 = px + px - previous.x1, py + py - previous.y1
                else:
                    x1, y1 = px, py
                x, y = arguments
                if relative:
                    x += px; y += py
                px, py = x, y
                previous = quadto(x1, y1, x, y)
            
            else: # elliptical arc
                raise NotImplementedError
            
            result.append(previous)
            arguments = [] # TODO python 3: list.clear()
            m = tokens.search(data, m.end())
            if not m or m.lastindex != 1: # number
                break
            arguments.append(float(m.group(1)))
    
    return result




def serialize(page, compress):
    fonts = {}
    for item in page.items:
        if isinstance(item, placedtext):
            if not isinstance(item, placedoutlines):
                for height, run in item.layout.runs():
                    for style, string in run:
                        name = style.font.name
                        data = style.font.source.readable.data
                        if name not in fonts:
                            fonts[name] = (
                                '@font-face {\n'
                                '    font-family: "%s";\n'
                                '    src: url("data:font/sfnt;base64,%s");\n'
                                '}') % (name, b64encode(data))
    if fonts:
        defs = (
            '<defs>\n'
            '<style>\n'
            '%s\n'
            '</style>\n'
            '</defs>\n') % '\n'.join(fonts.values())
    else:
        defs = ''
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!-- Flat -->\n'
        '<svg version="1.1" '
            'xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" '
            'width="%spt" height="%spt">\n'
        '<title>%s</title>\n'
        '%s%s\n'
        '</svg>') % (
            dump(page.width), dump(page.height),
            escape(page.title).encode('utf-8'),
            defs, '\n'.join(item.svg() for item in page.items))




