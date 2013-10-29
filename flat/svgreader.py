
import re

from .command import moveto, lineto, quadto, curveto, closepath




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
    if m:
        assert m.lastindex == 2, 'Invalid path.' # moveto
    while m:
        index = m.lastindex
        count = counts[index]
        relative = m.group(index).islower()
        while True:
            for i in range(count - len(arguments)):
                m = tokens.search(data, m.end())
                assert m and m.lastindex == 1, 'Invalid argument.' # number
                arguments.append(float(m.group(1)))
            
            if index == 2: # moveto
                x, y = arguments
                if relative:
                    x += px; y += py
                mx, my = px, py = x, y
                previous = moveto(x, y)
            
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
            arguments = [] # TODO python 3: arguments.clear()
            m = tokens.search(data, m.end())
            if not m or m.lastindex > 1: # number
                break
            arguments.append(float(m.group(1)))
    
    return result




