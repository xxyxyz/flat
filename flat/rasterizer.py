
from collections import defaultdict

from .image import image




# Sampling patterns based on "PolygonFiller.h"
# of "Scanline edge-flag algorithm for antialiasing"
# Copyright (c) 2005-2007 Kiia Kallio
_pattern_1 = [0]
_pattern_8 = [5, 0, 3, 6, 1, 4, 7, 2]
_pattern_16 = [1, 8, 4, 15, 11, 2, 6, 14, 10, 3, 7, 12, 0, 9, 5, 13]
_pattern_32 = [28, 13, 6, 23, 0, 17, 10, 27, 4, 21, 14, 31, 8, 25, 18, 3,
    12, 29, 22, 7, 16, 1, 26, 11, 20, 5, 30, 15, 24, 9, 2, 19]




def line(flags, x0, y0, x1, y1, samples, pattern, step):
    if x0 == x1:
        if y0 > y1:
            y0, y1 = y1, y0
            step = -step
        for y in range(y0, y1):
            flags[y // samples][(x0 + pattern[y]) // samples] += step
    else:
        if y0 > y1:
            x0, y0, x1, y1 = x1, y1, x0, y0
            step = -step
        dx = x1 - x0
        dy = y1 - y0
        x0 = x0 * dy + dy // 2
        for y in range(y0, y1):
            flags[y // samples][(x0 // dy + pattern[y]) // samples] += step
            x0 += dx


def curve(flags, x0, y0, x1, y1, x2, y2, samples, pattern, step, depth=8):
    x01 = (x0 + x1) * 0.5
    y01 = (y0 + y1) * 0.5
    x12 = (x1 + x2) * 0.5
    y12 = (y1 + y2) * 0.5
    x02 = (x01 + x12) * 0.5
    y02 = (y01 + y12) * 0.5
    dx = (x0 + x2) * 0.5 - x02
    dy = (y0 + y2) * 0.5 - y02
    if depth > 0 and dx*dx+dy*dy > samples*samples*0.01:
        curve(flags, x0, y0, x01, y01, x02, y02, samples, pattern, step, depth-1)
        curve(flags, x02, y02, x12, y12, x2, y2, samples, pattern, step, depth-1)
    else:
        line(flags, int(x0+0.5), int(y0+0.5), int(x2+0.5), int(y2+0.5), samples, pattern, step)




def nonzero(image, flags, color, miny, maxy):
    n = image.count
    intensities = (color.intensity,) if n == 1 else color.intensities
    opacity = 255 if n in (1, 3) else intensities[-1]
    rows = image.rows
    for y in range(miny, maxy):
        row, edges = rows[y], flags[y]
        transparency = 255
        xs = edges.keys()
        xs.sort()
        for j in range(len(xs) - 1):
            x0, x1 = xs[j], xs[j+1]
            transparency += edges[x0]
            if transparency == 255:
                continue
            inverse = transparency if transparency <= 255 else 510-transparency # 255 + 255
            if inverse <= 0:
                if opacity == 255:
                    row[x0*n:x1*n] = intensities * (x1 - x0)
                    continue
                inverse = 0
            blend(row, n, x0, x1, intensities, inverse)
        edges.clear()




def blend(row, n, x0, x1, intensities, inverse):
    if n == 1:
        alpha = 255 - inverse
        g = intensities[0] * alpha + 127
        for x in range(x0, x1):
            row[x] = (g + row[x] * inverse) // 255
    elif n == 3:
        alpha = 255 - inverse
        r = intensities[0] * alpha + 127
        g = intensities[1] * alpha + 127
        b = intensities[2] * alpha + 127
        for x in range(x0*3, x1*3, 3):
            row[x] = (r + row[x] * inverse) // 255
            row[x+1] = (g + row[x+1] * inverse) // 255
            row[x+2] = (b + row[x+2] * inverse) // 255
    elif n == 2:
        alpha = ((255 - inverse) * intensities[1] + 127) // 255
        alpha255 = alpha * 255
        inverse = 255 - alpha
        g = intensities[0] * alpha + 127
        g255 = intensities[0] * alpha255
        for x in range(x0*2, x1*2, 2):
            if row[x+1] == 255:
                row[x] = (g + row[x] * inverse) // 255
            else:
                a = alpha255 + row[x+1] * inverse
                if a == 0:
                    row[x] = 0
                    row[x+1] = 0
                else:
                    inv = row[x+1] * inverse
                    a2 = a // 2
                    row[x] = (g255 + row[x] * inv + a2) // a
                    row[x+1] = (a + 127) // 255
    else: # 4
        alpha = ((255-inverse) * intensities[3] + 127) // 255
        alpha255 = alpha * 255
        inverse = 255 - alpha
        r = intensities[0] * alpha + 127
        g = intensities[1] * alpha + 127
        b = intensities[2] * alpha + 127
        r255 = intensities[0] * alpha255
        g255 = intensities[1] * alpha255
        b255 = intensities[2] * alpha255
        for x in range(x0*4, x1*4, 4):
            if row[x+3] == 255:
                row[x] = (r + row[x] * inverse) // 255
                row[x+1] = (g + row[x+1] * inverse) // 255
                row[x+2] = (b + row[x+2] * inverse) // 255
            else:
                a = alpha255 + row[x+3] * inverse
                if a == 0:
                    row[x] = 0
                    row[x+1] = 0
                    row[x+2] = 0
                    row[x+3] = 0
                else:
                    inv = row[x+3] * inverse
                    a2 = a // 2
                    row[x] = (r255 + row[x] * inv + a2) // a
                    row[x+1] = (g255 + row[x+1] * inv + a2) // a
                    row[x+2] = (b255 + row[x+2] * inv + a2) // a
                    row[x+3] = (a + 127) // 255




class rasterizer(object):
    
    def __init__(self, width, height, kind, samples):
        assert kind in ('g', 'ga', 'rgb', 'rgba'), 'Unsupported image kind.'
        if samples == 32:
            pattern = _pattern_32
        elif samples == 16:
            pattern = _pattern_16
        elif samples == 8:
            pattern = _pattern_8
        elif samples == 1:
            pattern = _pattern_1
        else:
            raise AssertionError('Invalid samples count.')
        self.image = image(width, height, kind)
        self.flags = [defaultdict(int) for i in range(height)]
        self.samples = samples
        self.pattern = pattern * height
        self.step = 256 // samples
    
    def rasterize(self, countours, k, x, y, color):
        image, flags, samples, pattern, step = \
            self.image, self.flags, self.samples, self.pattern, self.step
        assert image.kind == color.kind, 'Invalid color kind.'
        if not countours:
            return
        k, x, y = k*samples, x*samples+0.5, y*samples+0.5
        miny = maxy = int(countours[0][-1][1] * k + y)
        for contour in countours:
            x2, y2 = contour[-1]
            x2, y2 = int(x2 * k + x), int(y2 * k + y)
            for i in range(0, len(contour), 2):
                x0, y0 = x2, y2
                x2, y2 = contour[i + 1]
                x2, y2 = int(x2 * k + x), int(y2 * k + y)
                if y2 < miny:
                    miny = y2
                elif y2 > maxy:
                    maxy = y2
                if contour[i]:
                    x1, y1 = contour[i]
                    x1, y1 = int(x1 * k + x), int(y1 * k + y)
                    if y1 < miny:
                        miny = y1
                    elif y1 > maxy:
                        maxy = y1
                    curve(flags, x0, y0, x1, y1, x2, y2, samples, pattern, step)
                else:
                    line(flags, x0, y0, x2, y2, samples, pattern, step)
        miny, maxy = max(0, miny//samples), min(maxy//samples+1, image.height)
        nonzero(image, flags, color, miny, maxy)




