
from weakref import proxy
from xml.sax.saxutils import escape
import re

from .color import _default_color
from .shape import shape, _rasterize_commands, _strokefill_pdf
from .utils import dump, equal, memoize, rmq, scale




linebreaks = re.compile(ur'\r\n|[\n\v\f\r\x85\u2028\u2029]') # TODO python 3: ur -> r




def _strike_textoutlines(cls, strike, string):
    empty = paragraph(span(strike, ''))
    return cls(*[paragraph(span(strike, part)) if part else empty
        for part in linebreaks.split(string)])


class strike(object):
    
    __slots__ = 'font', 'textsize', 'leading', 'textcolor'
    
    def __init__(self, font):
        self.font = font
        self.textsize, self.leading = 10.0, 12.0
        self.textcolor = _default_color
    
    def size(self, textsize, leading, units='pt'):
        assert textsize > 0, 'Invalid text size.'
        k = scale(units)
        self.textsize, self.leading = textsize*k, leading*k
        return self
    
    def color(self, color):
        self.textcolor = color
        return self
    
    @memoize
    def width(self, string):
        kerning, width, left = self.font.relativewidth(string, 0, self.textsize)
        return width
    
    @memoize
    def relativewidth(self, string, left):
        return self.font.relativewidth(string, left, self.textsize)
    
    def defaultadvance(self):
        return self.textsize * self.font.density * self.font.defaultadvance
    
    def ascender(self):
        return self.textsize * self.font.density * self.font.ascender
    
    def descender(self):
        return self.textsize * self.font.density * self.font.descender
    
    def span(self, string):
        return span(self, linebreaks.sub(' ', string))
    
    def paragraph(self, string):
        return paragraph(self.span(string))
    
    def text(self, string):
        return _strike_textoutlines(text, self, string)
    
    def outlines(self, string):
        return _strike_textoutlines(outlines, self, string)
    
    def pdffont(self, name):
        return '/%s %s Tf' % (name, dump(self.textsize))




class span(object):
    
    __slots__ = 'strike', 'string'
    
    def __init__(self, strike, string):
        self.strike = strike
        self.string = string
    
    def left(self, previous):
        s, p = self.strike, previous.strike
        if s.font.name == p.font.name and s.textsize == p.textsize:
            return p.font.charmap.get(ord(previous.string[-1]), 0)
        return 0
    
    def run(self, start, end, left):
        charmap = self.strike.font.charmap
        kerning = self.strike.font.kerning
        advances = self.strike.font.advances
        string = self.string
        for i in range(start, end):
            code = ord(string[i])
            right = charmap.get(code, 0)
            yield kerning[left].get(right, 0), advances[right], right
            left = right




class paragraph(object):
    
    def __init__(self, *spans):
        self.spans = spans
        self.alignment = 'left'
        
        self.words = words = [] # span index, character index
        self.offsets = offsets = [] # word offset, whitespace width
        
        last = ''
        position = 0.0
        
        oldname, oldsize = '', 0.0
        fix, left = 0.0, 0
        
        boundaries = re.compile(ur'([^ -]+-*|-+|^)(\s*)') # word, whitespace # TODO python 3: ur -> r
        for i, span in enumerate(spans):
            
            string, strike = span.string, span.strike
            
            if not string:
                continue
            
            if strike.font.name != oldname or strike.textsize != oldsize:
                oldname, oldsize = strike.font.name, strike.textsize
                left = 0
            
            w = []
            o = []
            for m in boundaries.finditer(string):
                start, end1, end2 = m.start(), m.end(1), m.end(2)
                
                fix, width, left = strike.relativewidth(string[start:end1], left)
                fixgap, gap, left = strike.relativewidth(string[end1:end2], left)
                
                if o:
                    o[-1] -= fix
                elif offsets:
                    offsets[-1] -= fix
                position -= fix
                gap -= fixgap
                
                w.extend((i, start))
                o.extend((position, gap))
                position += width + gap
            
            first = string[0]
            if last == first or last == '-' and first == ' ' or last not in ' -':
                w[0], w[1] = words[-2], words[-1]
                o[0], o[1] = offsets[-2], offsets[-1] + o[1] + (fix if len(w) == 2 else 0.0)
                del words[-2:]
                del offsets[-2:]
            last = string[-1]
            
            words.extend(w)
            offsets.extend(o)
        
        words.extend((len(spans), 0))
        offsets.extend((position, 0))
        
        leadings = []
        for j in range(0, len(words) - 2, 2):
            span0, span1 = words[j], words[j + 2]
            leadings.append(
                spans[span0].strike.leading if span0 == span1 else
                max(spans[i].strike.leading for i in range(span0, span1)))
        self.leadings = rmq(leadings)
    
    def count(self):
        return len(self.words) // 2 - 1
    
    def align(self, alignment):
        assert alignment in (
            'left', 'right', 'center', 'justify'), 'Invalid alignment.'
        self.alignment = alignment
    
    def width(self, i, j):
        offsets = self.offsets
        return offsets[j * 2] - offsets[i * 2] - offsets[j * 2 - 1]
    
    def ascender(self, i, j):
        spans, words = self.spans, self.words
        span0, span1 = words[i * 2], words[j * 2]
        if span0 == span1:
            return spans[span0].strike.ascender()
        return max(spans[i].strike.ascender() for i in range(span0, span1))
    
    def descender(self, i, j):
        spans, words = self.spans, self.words
        span0, span1 = words[i * 2], words[j * 2]
        if span0 == span1:
            return spans[span0].strike.descender()
        return min(spans[i].strike.descender() for i in range(span0, span1))
    
    def run(self, i, j):
        spans, words = self.spans, self.words
        span0, char0 = words[i * 2], words[i * 2 + 1]
        span1, char1 = words[j * 2], words[j * 2 + 1]
        result = []
        if span0 == span1:
            result.append((spans[span0], char0, char1, 0))
        else:
            previous = spans[span0]
            result.append((previous, char0, len(previous.string), 0))
            for i in range(span0+1, span1):
                if spans[i].string:
                    left = spans[i].left(previous)
                    previous = spans[i]
                else:
                    left = 0
                result.append((spans[i], 0, len(spans[i].string), left))
            if char1 > 0:
                left = spans[span1].left(previous)
                result.append((spans[span1], 0, char1, left))
        return result




class text(object):
    
    @classmethod
    def open(cls, path, substitutes):
        raise NotImplementedError
    
    def __init__(self, *paragraphs):
        self.paragraphs = paragraphs
    
    def placed(self, scale):
        return placedtext(layout(self), scale)




class placedtext(object):
    
    def __init__(self, layout, k):
        self.layout = layout
        self.index = layout.add(self)
        self.k = k
        self.x, self.y = 0.0, 0.0
        self.width, self.height = 1e100, 1e100
    
    def chained(self, scale):
        return placedtext(self.layout, scale)
    
    def position(self, x, y):
        self.x, self.y = x*self.k, y*self.k
        return self
    
    def frame(self, x, y, width, height):
        self.x, self.y = x*self.k, y*self.k
        self.width, self.height = width*self.k, height*self.k
        self.layout.reflow(self.index)
        return self
    
    def paragraphs(self):
        return self.layout.item.paragraphs
    
    def overflow(self):
        return self.layout.overflow
    
    def lines(self):
        for para, start, end, height in self.layout.lines(self.index):
            if end == 0:
                yield [(para.spans[0], 0, 0, 0)], height
            else:
                yield para.run(start, end), height
    
    def bboxes(self):
        result = []
        scale = 1.0 / self.k
        y = self.y
        for para, start, end, height in self.layout.lines(self.index):
            x = self.x
            y += height
            for i in range(start, end):
                advance = para.offsets[i * 2 + 2] - para.offsets[i * 2]
                gap = para.offsets[i * 2 + 1]
                if not equal(advance - gap, 0.0):
                    ascender = para.ascender(i, i + 1)
                    descender = para.descender(i, i + 1)
                    result.append((
                        x * scale, (y - ascender) * scale,
                        (advance - gap) * scale, (ascender - descender) * scale))
                x += advance
        return result
    
    def pdf(self, previous, resources, colors, fonts, images, states, height):
        oldstroke, oldcolor = previous.strokecolor, previous.fillcolor
        oldname, oldsize = previous.fontname, previous.textsize
        commands = ['BT\n1 0 0 1 %s %s Tm' % (dump(self.x), dump(height - self.y))]
        for line, height in self.lines():
            commands.append('0 %s Td' % dump(-height))
            for span, start, end, left in line:
                strike = span.strike
                chunk, cs, fs, gs = _strike_pdf(resources,
                    strike, oldname, oldsize, oldcolor, oldstroke)
                if chunk:
                    colors |= cs
                    fonts |= fs
                    states |= gs
                    oldname, oldsize, oldcolor = \
                        strike.font.name, strike.textsize, strike.textcolor
                    commands.append(chunk)
                if start < end:
                    thousandths = strike.font.density * 1000.0
                    run = span.run(start, end, left)
                    kerning, advance, index = next(run)
                    row = [
                        '[%d' % round(kerning * thousandths) if kerning != 0 else '[',
                        '<%04x' % index]
                    for kerning, advance, index in run:
                        if kerning != 0:
                            row.append('>%d<' % round(kerning * thousandths))
                        row.append('%04x' % index)
                    row.append('>] TJ')
                    commands.append(''.join(row))
        commands.append('ET')
        previous.fillcolor = oldcolor
        previous.fontname, previous.textsize = oldname, oldsize
        return '\n'.join(commands)
    
    def svg(self):
        y = self.y
        elements = []
        for line, height in self.lines():
            x = self.x
            y += height
            row = ['<text x="%s" y="%s">' % (dump(x), dump(y))]
            for span, start, end, left in line:
                if start < end:
                    strike = span.strike
                    k = strike.textsize * strike.font.density
                    kerning, advance, index = next(span.run(start, end, left))
                    dx = ' dx="%s"' % dump(-kerning * k) if kerning != 0 else ''
                    fill = strike.textcolor.svg()
                    row.append((
                        '<tspan font-family="%s" font-size="%s" fill="%s"%s '
                            'xml:space="preserve">%s</tspan>') % (
                            strike.font.name, strike.textsize, fill, dx,
                            escape(span.string[start:end]).encode('utf-8')))
            row.append('</text>')
            elements.append(''.join(row))
        return '\n'.join(elements)
    
    def rasterize(self, rasterizer, k, x, y):
        yy = self.y
        dummy = shape().nostroke()
        for line, height in self.lines():
            xx = self.x
            yy += height
            for span, start, end, left in line:
                strike = span.strike
                kk = strike.textsize * strike.font.density
                dummy.fillcolor = strike.textcolor
                for kerning, advance, index in span.run(start, end, left):
                    xx -= kerning * kk
                    _rasterize_commands(rasterizer,
                        strike.font.glyph2(index, kk*k).commands,
                        kk*k, xx*k+x, yy*k+y, dummy, 1.0/kk)
                    xx += advance * kk




class outlines(text):
    
    def placed(self, scale):
        return placedoutlines(layout(self), scale)




class placedoutlines(placedtext):
    
    def chained(self, scale):
        return placedoutlines(self.layout, scale)
    
    def pdf(self, previous, resources, colors, fonts, images, states, height):
        oldstroke = previous.strokecolor
        y = height - self.y
        commands = []
        for line, height in self.lines():
            x = self.x
            y -= height
            for span, start, end, left in line:
                strike = span.strike
                k = strike.textsize * strike.font.density
                chunk, cs, gs = _strokefill_pdf(resources,
                    oldstroke, strike.textcolor, oldstroke, previous.fillcolor)
                if chunk:
                    colors |= cs
                    states |= gs
                    previous.fillcolor = strike.textcolor
                    commands.append(chunk)
                for kerning, advance, index in span.run(start, end, left):
                    x -= kerning * k
                    g = strike.font.glyph3(index)
                    if g.commands:
                        commands.append(g.pdf(k, x, y, 'f'))
                    x += advance * k
        return '\n'.join(commands)
    
    def svg(self):
        y = self.y
        elements = []
        for line, height in self.lines():
            x = self.x
            y += height
            for span, start, end, left in line:
                strike = span.strike
                k = strike.textsize * strike.font.density
                fill = ' fill="%s"' % strike.textcolor.svg()
                for kerning, advance, index in span.run(start, end, left):
                    x -= kerning * k
                    g = strike.font.glyph(index)
                    if g.commands:
                        elements.append(g.svg(k, x, y, fill))
                    x += advance * k
        return '\n'.join(elements)




@memoize
def _strike_pdf(resources, strike, oldname, oldsize, oldcolor, oldstroke):
    chunk, spaces, states = _strokefill_pdf(resources,
        oldstroke, strike.textcolor, oldstroke, oldcolor)
    fonts = set()
    if strike.font.name != oldname or strike.textsize != oldsize:
        resource = resources.font(strike.font)
        chunk += (' ' if chunk else '') + strike.pdffont(resource.name)
        fonts.add(resource)
    return chunk, spaces, fonts, states




class layout(object):
    
    def __init__(self, item):
        self.item = item
        self.overflow = False
        self.blocks = []
        self.breaks = [[0] * (p.count() + 1) for p in item.paragraphs]
        self.costs = [[0.0] + [1e100] * p.count() for p in item.paragraphs]
        self.offsets = [[0.0] * (p.count() + 1) for p in item.paragraphs]
        self.ends = [(0, 0)] # paragraph, word
    
    def add(self, block):
        paragraphs = self.item.paragraphs
        self.blocks.append(proxy(block))
        self.ends.append((len(paragraphs)-1, paragraphs[-1].count()))
        return len(self.blocks) - 1
    
    def reflow(self, index):
        paragraphs = self.item.paragraphs
        
        heights = [0.0]
        for b in self.blocks:
            heights.append(b.height + heights[-1])
        maxheight = heights[-1]
        
        highestindex = index
        
        para, word = self.ends[index]
        word = self.breaks[para][word]
        previousoffset = self.offsets[para][word]
        while para < len(paragraphs):
            paragraph = paragraphs[para]
            breaks = self.breaks[para]
            costs = self.costs[para]
            offsets = self.offsets[para]
            offsets[word] = previousoffset
            n = paragraph.count()
            
            if n == 0:
                leading = paragraph.spans[0].strike.leading
                if offsets[word] + leading > maxheight:
                    self.overflow = True
                    self.ends[-1] = para, word
                    return
                
                if heights[highestindex] < offsets[word]:
                    highestindex += 1
                currentindex = highestindex
                if heights[currentindex] > offsets[word]:
                    currentindex -= 1
                
                if offsets[word] + leading > heights[currentindex + 1]:
                    offsets[word] = heights[currentindex + 1] + leading
                else:
                    offsets[word] += leading
                
            else:
                for i in range(word, n):
                    costsi = costs[i]
                    offsetsi = offsets[i]
                    
                    if heights[highestindex] < offsetsi:
                        highestindex += 1
                    currentindex = highestindex
                    if heights[currentindex] > offsetsi:
                        currentindex -= 1
                    
                    j = i + 1
                    while j <= n:
                        leading = paragraph.leadings.max(i, j) 
                        offset = offsetsi + leading
                        if offset > heights[currentindex + 1]:
                            if currentindex + 1 == len(self.blocks):
                                break
                            width = self.blocks[currentindex + 1].width
                            offset = heights[currentindex + 1] + leading
                        else:
                            width = self.blocks[currentindex].width
                        dist = paragraph.width(i, j)
                        if dist > width:
                            break
                        cost = costsi + (width - dist) ** 2 if j < n else costsi # align left
                        # cost = costsi + (width - dist) ** 2 # justified
                        if cost < costs[j]:
                            breaks[j] = i
                            costs[j] = cost
                            offsets[j] = offset
                        j += 1
                    
                    if costs[i + 1] == 1e100:
                        self.overflow = True
                        self.ends[-1] = para, i
                        return
                    
            previousoffset = offsets[-1]
            para, word = para + 1, 0
        
        para, word = self.ends[-1]
        previous = para, word
        i = len(self.ends) - 2
        while para >= 0:
            while True:
                if self.offsets[para][word] < heights[i]:
                    self.ends[i] = previous
                    i -= 1
                word = self.breaks[para][word]
                previous = para, word
                if word == 0:
                    break
            para, word = para - 1, self.item.paragraphs[para - 1].count()
        self.overflow = False
    
    def lines(self, index):
        paragraphs = self.item.paragraphs
        para0, word0 = self.ends[index]
        para1, word1 = self.ends[index + 1]
        p = paragraphs[para1]
        result = []
        while para0 != para1 or word0 != word1:
            if word1 == 0:
                para1, word1 = para1 - 1, paragraphs[para1 - 1].count()
                p = paragraphs[para1]
                if word1 == 0:
                    result.append((p, 0, 0, p.spans[0].strike.leading))
                    continue
            previous = self.breaks[para1][word1]
            result.append((p, previous, word1, p.leadings.max(previous, word1)))
            word1 = previous
        if result:
            result.reverse()
            p, start, end, height = result[0]
            if end > 0:
                result[0] = p, start, end, p.ascender(start, end)
        return result




