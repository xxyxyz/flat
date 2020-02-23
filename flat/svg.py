from base64 import b64encode
from xml.sax.saxutils import escape
from .command import moveto, lineto, quadto, curveto, closepath
from .misc import dump
from .text import placedtext, placedoutlines
import re




def parsepath(data):
    tokens = re.compile(br'|'.join((
        br'([+-]?(?:\d*\.\d+|\d+\.?)(?:[eE][+-]?\d+)?)', # number
        br'([Mm])', # moveto
        br'([Zz])', # closepath
        br'([Ll])', # lineto
        br'([Hh])', # horizontal lineto
        br'([Vv])', # vertical lineto
        br'([Cc])', # curveto
        br'([Ss])', # smooth curveto
        br'([Qq])', # quadto
        br'([Tt])', # smooth quadto
        br'([Aa])'))) # elliptical arc
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
            arguments.clear()
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
                                b'@font-face {\n'
                                b'    font-family: "%s";\n'
                                b'    src: url("data:font/sfnt;base64,%s");\n'
                                b'}') % (name, b64encode(data))
    if fonts:
        defs = (
            b'<defs>\n'
            b'<style>\n'
            b'%s\n'
            b'</style>\n'
            b'</defs>\n') % b'\n'.join(fonts.values())
    else:
        defs = b''
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<!-- Flat -->\n'
        b'<svg version="1.1" '
            b'xmlns="http://www.w3.org/2000/svg" '
            b'xmlns:xlink="http://www.w3.org/1999/xlink" '
            b'width="%spt" height="%spt" '
            b'viewBox="0 0 %s %s">\n'
        b'<title>%s</title>\n'
        b'%s%s\n'
        b'</svg>') % (
            dump(page.width), dump(page.height),
            dump(page.width), dump(page.height),
            escape(page.title).encode('utf-8'),
            defs, b'\n'.join(item.svg() for item in page.items))




