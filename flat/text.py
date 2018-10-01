from xml.sax.saxutils import escape
from .color import gray, spot, overprint
from .misc import dump, inf, rmq, scale
from .path import elevated
import re




linebreaks = re.compile(r'\r\n|[\n\v\f\r\x85\u2028\u2029]')
boundaries = re.compile(r'([^\s-]+-?|-|^)(\s*)')




class style(object):
    
    __slots__ = 'font', 'size', 'leading', 'color'
    
    def __init__(self, font):
        self.font = font
        self.size, self.leading = 10.0, 12.0
        self.color = gray(0)
    
    def ascender(self):
        return self.font.ascender/self.font.density*self.size
    
    def descender(self):
        return self.font.descender/self.font.density*self.size
    
    def width(self, string):
        result = 0
        previous = 0
        for character in string:
            code = ord(character)
            index = self.font.charmap.get(code, 0)
            result += self.font.kerning[previous].get(index, 0)
            result += self.font.advances[index]
            previous = index
        return result/self.font.density*self.size
    
    def boundaries(self, string, start):
        previous = 0
        for m in boundaries.finditer(string, start):
            word = 0
            space = 0
            length = m.end(2) - m.start(1)
            for character in m.group(1):
                code = ord(character)
                index = self.font.charmap.get(code, 0)
                word += self.font.kerning[previous].get(index, 0)
                word += self.font.advances[index]
                previous = index
            for character in m.group(2):
                code = ord(character)
                index = self.font.charmap.get(code, 0)
                space += self.font.kerning[previous].get(index, 0)
                space += self.font.advances[index]
                previous = index
            word = word/self.font.density*self.size
            space = space/self.font.density*self.size
            yield word, space, length
    
    def pdf(self, state, resources, text):
        fragments = []
        if text:
            n, s = self.font.name, self.size
            if n != state.name or s != state.size:
                resource = resources.font(self.font)
                fragments.append(b'/%s %s Tf' % (resource.name, dump(s)))
                state.name, state.size = n, s
        f, ff = self.color, state.fill
        fo, ffo = isinstance(f, overprint), isinstance(ff, overprint)
        if f and fo != ffo:
            sso = isinstance(state.stroke, overprint)
            resource = resources.overprint(sso, fo)
            fragments.append(b'/%s gs' % resource.name)
        if fo:
            f = f.color
        if ffo:
            ff = ff.color
        if f and f != ff:
            if isinstance(f, spot):
                resource = resources.space(f)
                fragments.append(f.pdffill(resource.name))
            else:
                fragments.append(f.pdffill())
            state.fill = f
        return b' '.join(fragments)




class strike(object):
    
    __slots__ = 'style',
    
    def __init__(self, font):
        self.style = style(font)
    
    def size(self, size, leading=0.0, units='pt'):
        if leading == 0.0:
            leading = 1.1*size + 1.0
        k = scale(units)
        self.style.size, self.style.leading = size*k, leading*k
        return self
    
    def color(self, color):
        self.style.color = color
        return self
    
    def width(self, string, units='pt'):
        return self.style.width(string)/scale(units)
    
    def span(self, string):
        return span(self.style, string)
    
    def paragraph(self, string):
        return paragraph((self.span(string),))
    
    def text(self, string):
        return text(list(map(self.paragraph, linebreaks.split(string))))
    
    def outlines(self, string):
        return outlines(list(map(self.paragraph, linebreaks.split(string))))




class span(object):
    
    __slots__ = 'style', 'string'
    
    def __init__(self, style, string):
        if linebreaks.search(string):
            raise ValueError('Unexpected newline character.')
        self.style = style
        self.string = string
    
    def boundaries(self, start):
        return self.style.boundaries(self.string, start)




class paragraph(object):
    
    __slots__ = 'spans', 'leadings', 'ascenders'
    
    def __init__(self, spans):
        if not spans:
            raise ValueError('No spans.')
        self.spans = spans
        self.leadings = rmq([s.style.leading for s in spans])
        self.ascenders = rmq([s.style.ascender() for s in spans])




class text(object):
    
    __slots__ = 'paragraphs',
    
    def __init__(self, paragraphs):
        if not paragraphs:
            raise ValueError('No paragraphs.')
        self.paragraphs = paragraphs
    
    def placed(self, k):
        return placedtext(layout(self.paragraphs), k)




class outlines(text):
    
    __slots__ = 'paragraphs',
    
    def placed(self, k):
        return placedoutlines(layout(self.paragraphs), k)




class layout(object):
    
    __slots__ = 'paragraphs', 'start', 'lines'
    
    def __init__(self, paragraphs, start=(0, 0, 0)):
        self.paragraphs = paragraphs
        self.start = start
        self.lines = lines = []
        i, j, k = start
        u = len(paragraphs)
        while i < u:
            paragraph = paragraphs[i]
            spans = paragraph.spans
            string = spans[-1].string
            n = len(spans)
            if lines:
                height = paragraph.ascenders.max(j, n)
            else:
                height = paragraph.leadings.max(j, n)
            end = len(lines), n-1, len(string)
            lines.append((height, end))
            j = 0
            i += 1
    
    def reflow(self, width, height):
        self.lines.clear()
        i, j, k = self.start
        u = len(self.paragraphs)
        y = 0.0
        while i < u:
            paragraph = self.paragraphs[i]
            v = len(paragraph.spans) - 1
            x = 0.0
            dy = 0.0
            while True:
                span = paragraph.spans[j]
                style = span.style
                if self.lines:
                    dy = max(dy, style.leading)
                else:
                    dy = max(dy, style.ascender())
                if y + dy > height:
                    return
                for word, space, length in span.boundaries(k):
                    if x + word > width:
                        end = i, j, k
                        self.lines.append((dy, end))
                        if word > width:
                            return
                        x = word + space
                        y += dy
                        dy = style.leading
                        if y + dy > height:
                            return
                    else:
                        x += word + space
                    k += length
                if j == v:
                    break
                j += 1
                k = 0
            end = i, j, k
            self.lines.append((dy, end))
            i += 1
            j = 0
            k = 0
            y += dy
    
    def run(self, start, end):
        i, j, k = start
        u, v, w = end
        paragraph = self.paragraphs[i]
        while True:
            span = paragraph.spans[j]
            style, string = span.style, span.string
            if j == v:
                yield style, string[k:w]
                break
            if k > 0:
                string = string[k:]
            yield style, string
            j += 1
            k = 0
    
    def runs(self):
        start = self.start
        for height, end in self.lines:
            yield height, self.run(start, end)
            start = self.norm(end)
    
    def norm(self, end):
        i, j, k = end
        spans = self.paragraphs[i].spans
        if len(spans[j].string) == k:
            if len(spans) - 1 == j:
                return i+1, 0, 0
            return i, j+1, 0
        return end
    
    def end(self):
        if self.lines:
            height, end = self.lines[-1]
            return end
        return self.tail()
    
    def tail(self):
        paragraphs = self.paragraphs
        spans = paragraphs[-1].spans
        string = spans[-1].string
        return len(paragraphs)-1, len(spans)-1, len(string)
    
    def overflow(self):
        return self.end() != self.tail()
    
    def chain(self):
        start = self.norm(self.end())
        return layout(self.paragraphs, start)
    
    def clear(self):
        self.start = self.norm(self.tail())
        self.lines.clear()
    
    def link(self, following):
        start = self.norm(self.end())
        if start == following.start:
            return True
        following.start = start
        return False




class placedtext(object):
    
    __slots__ = 'layout', 'k', 'x', 'y', 'width', 'height', 'next'
    
    def __init__(self, layout, k):
        self.layout = layout
        self.k = k
        self.x, self.y = 0.0, 0.0
        self.width, self.height = inf, inf
        self.next = None
    
    def position(self, x, y):
        self.x, self.y = x*self.k, y*self.k
        return self
    
    def frame(self, x, y, width, height):
        self.x, self.y = x*self.k, y*self.k
        self.width, self.height = width*self.k, height*self.k
        block = self
        while True:
            block.layout.reflow(block.width, block.height)
            if not block.next:
                break
            if block.layout.link(block.next.layout):
                break
            block = block.next
        return self
    
    def overflow(self):
        return self.layout.overflow()
    
    def chained(self, k):
        layout = self.layout.chain()
        block = type(self)(layout, k)
        block.next = self.next
        self.next = block
        block = block.next
        while block:
            block.layout.clear()
            block = block.next
        return self.next
    
    def lines(self):
        return [''.join(string for style, string in run)
            for height, run in self.layout.runs()]
    
    def pdf(self, height, state, resources):
        fragments = [b'BT',
            b'1 0 0 1 %s %s Tm' % (dump(self.x), dump(height-self.y))]
        for height, run in self.layout.runs():
            fragments.append(b'0 %s Td' % dump(-height))
            for style, string in run:
                setup = style.pdf(state, resources, True)
                if setup:
                    fragments.append(setup)
                line = []
                previous = 0
                factor = -1000.0/style.font.density
                for character in string:
                    code = ord(character)
                    index = style.font.charmap.get(code, 0)
                    kerning = style.font.kerning[previous].get(index, 0)
                    if kerning != 0:
                        line.append(b'%d' % round(kerning*factor))
                    line.append(b'<%04x>' % index)
                    previous = index
                if line:
                    fragments.append(b'[%s] TJ' % b''.join(line))
        fragments.append(b'ET')
        return b'\n'.join(fragments)
    
    def svg(self):
        fragments = []
        y = self.y
        for height, run in self.layout.runs():
            x = self.x
            y += height
            line = [b'<text x="%s" y="%s" xml:space="preserve">' % (dump(x), dump(y))]
            for style, string in run:
                line.append(
                    b'<tspan font-family="%s" font-size="%s" fill="%s">%s</tspan>' % (
                        style.font.name, dump(style.size), style.color.svg(),
                        escape(string).encode('utf-8')))
            line.append(b'</text>')
            fragments.append(b''.join(line))
        return b'\n'.join(fragments)
    
    def rasterize(self, rasterizer, k, x, y):
        origin, y = self.x*k+x, self.y*k+y
        for height, run in self.layout.runs():
            x = origin
            y += height*k
            for style, string in run:
                previous = 0
                factor = style.size/style.font.density*k
                for character in string:
                    code = ord(character)
                    index = style.font.charmap.get(code, 0)
                    x += style.font.kerning[previous].get(index, 0)*factor
                    for c in style.font.glyph(index):
                        c.rasterize(rasterizer, factor, x, y)
                    style.color.rasterize(rasterizer)
                    x += style.font.advances[index]*factor
                    previous = index




class placedoutlines(placedtext):
    
    __slots__ = 'layout', 'k', 'x', 'y', 'width', 'height', 'next'
    
    def pdf(self, height, state, resources):
        fragments = []
        y = height - self.y
        for height, run in self.layout.runs():
            x = self.x
            y -= height
            for style, string in run:
                setup = style.pdf(state, resources, False)
                if setup:
                    fragments.append(setup)
                previous = 0
                factor = style.size/style.font.density
                for character in string:
                    code = ord(character)
                    index = style.font.charmap.get(code, 0)
                    x += style.font.kerning[previous].get(index, 0)*factor
                    commands = style.font.glyph(index)
                    if commands:
                        tokens = [c.pdf(factor, x, y) for c in elevated(commands)]
                        tokens.append(b'f')
                        fragments.append(b' '.join(tokens))
                    x += style.font.advances[index]*factor
                    previous = index
        return b'\n'.join(fragments)
    
    def svg(self):
        fragments = []
        y = self.y
        for height, run in self.layout.runs():
            x = self.x
            y += height
            for style, string in run:
                previous = 0
                factor = style.size/style.font.density
                for character in string:
                    code = ord(character)
                    index = style.font.charmap.get(code, 0)
                    x += style.font.kerning[previous].get(index, 0)*factor
                    commands = style.font.glyph(index)
                    if commands:
                        fragments.append(b'<path d="%s" fill="%s" />' % (
                            b' '.join(c.svg(factor, x, y) for c in commands),
                            style.color.svg()))
                    x += style.font.advances[index]*factor
                    previous = index
        return b'\n'.join(fragments)




