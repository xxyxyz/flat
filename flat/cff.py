from collections import deque
from .command import moveto, lineto, curveto, closepath




class cff(object):
    
    def __init__(self, readable):
        self.readable = r = readable
        origin = r.position
        major, minor, hdrSize, offSize = r.parse('>4B')
        if major != 1 or minor != 0:
            raise ValueError('Invalid CFF table.')
        name = self.index()
        top = self.index()
        if len(name) != 2 or len(top) != 2:
            raise ValueError('Unsupported FontSet count.')
        string = self.index()
        self.globalsubr = self.index()
        topdict = self.dict(top[0], top[1])
        size, offset = topdict[18] # Private
        offset += origin
        privatedict = self.dict(offset, offset + size)
        self.localsubr = self.index(offset + privatedict[19][0]) \
            if 19 in privatedict else [] # Subrs
        g, l = len(self.globalsubr), len(self.localsubr)
        self.globalbias = 107 if g < 1240 else 1131 if g < 33900 else 32768
        self.localbias = 107 if l < 1240 else 1131 if l < 33900 else 32768
        self.charstrings = self.index(origin + topdict[17][0]) # CharStrings
    
    def index(self, offset=0):
        r = self.readable
        if offset > 0:
            r.jump(offset)
        offsets = []
        count = r.uint16()
        if count > 0:
            offSize = r.uint8()
            start = r.position + (count + 1)*offSize - 1
            for j in range(count + 1):
                offset = r.uint8()
                for i in range(offSize - 1):
                    offset = (offset << 8) + r.uint8()
                offsets.append(start + offset)
            r.jump(offsets[-1])
        return offsets
    
    def dict(self, start, end):
        result, operands = {}, []
        nibbles = b'0', b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9', \
            b'.', b'E', b'E-', b'', b'-'
        r = self.readable
        r.jump(start)
        while r.position < end:
            value = r.uint8()
            if value <= 21:
                if value == 12:
                    value = (value << 8) + r.uint8()
                result[value], operands = operands, []
            elif value == 28:
                operands.append(r.int16())
            elif value == 29:
                operands.append(r.int32())
            elif value == 30:
                s = b''
                while r.position < end:
                    value = r.uint8()
                    a, b = value >> 4, value & 15
                    if b == 15:
                        if a < 15:
                            s += nibbles[a]
                        operands.append(float(s))
                        break
                    s += nibbles[a] + nibbles[b]
            elif 32 <= value <= 246:
                operands.append(value - 139)
            elif 247 <= value <= 250:
                operands.append((value - 247)*256 + r.uint8() + 108)
            elif 251 <= value <= 254:
                operands.append((251 - value)*256 - r.uint8() - 108)
            else:
                raise ValueError('Reserved value.')
        if operands:
            raise ValueError('Invalid DICT.')
        return result
    
    def type2(self, index):
        start, end = self.charstrings[index], self.charstrings[index+1]
        result, stack = [], deque()
        callstack = []
        x, y = 0, 0
        hints = 0
        r = self.readable
        r.jump(start)
        while r.position < end:
            value = r.uint8()
            if value <= 31:
                if value in (1, 3, 18, 19, 20, 23): # hstem, vstem, hstemhm, hintmask, cntrmask, vstemhm
                    hints += len(stack)//2
                    if value == 19 or value == 20:
                        r.skip((hints + 7)//8)
                    stack.clear()
                elif value == 4 or value == 21 or value == 22: # vmoveto, rmoveto, hmoveto
                    if result:
                        result.append(closepath)
                    if value == 4:
                        y += stack.pop()
                    elif value == 21:
                        y += stack.pop()
                        x += stack.pop()
                    else:
                        x += stack.pop()
                    result.append(moveto(x, y))
                    stack.clear()
                elif value == 5: # rlineto
                    while stack:
                        x += stack.popleft()
                        y += stack.popleft()
                        result.append(lineto(x, y))
                elif value == 6 or value == 7: # hlineto, vlineto
                    horizontal = value == 6
                    while stack:
                        if horizontal:
                            x += stack.popleft()
                        else:
                            y += stack.popleft()
                        horizontal = not horizontal
                        result.append(lineto(x, y))
                elif value == 8 or value == 24: # rrcurveto, rcurveline
                    while len(stack) > 2:
                        a, b = x+stack.popleft(), y+stack.popleft()
                        c, d = a+stack.popleft(), b+stack.popleft()
                        x, y = c+stack.popleft(), d+stack.popleft()
                        result.append(curveto(a, b, c, d, x, y))
                    if value == 24:
                        x += stack.popleft()
                        y += stack.popleft()
                        result.append(lineto(x, y))
                elif value == 10 or value == 29: # callsubr, callgsubr
                    callstack.append((r.position, end))
                    bias = self.localbias if value == 10 else self.globalbias
                    subr = self.localsubr if value == 10 else self.globalsubr
                    index = stack.pop() + bias
                    start, end = subr[index], subr[index+1]
                    r.jump(start)
                    continue
                elif value == 11: # return
                    start, end = callstack.pop()
                    r.jump(start)
                    continue
                elif value == 12: # escape
                    value = r.uint8()
                    if value == 34: # hflex
                        a = x+stack.popleft()
                        c, d = a+stack.popleft(), y+stack.popleft()
                        x = c+stack.popleft()
                        result.append(curveto(a, y, c, d, x, d))
                        a = x+stack.popleft()
                        c = a+stack.popleft()
                        x = c+stack.popleft()
                        result.append(curveto(a, d, c, y, x, y))
                    elif value == 35: # flex
                        for i in range(2):
                            a, b = x+stack.popleft(), y+stack.popleft()
                            c, d = a+stack.popleft(), b+stack.popleft()
                            x, y = c+stack.popleft(), d+stack.popleft()
                            result.append(curveto(a, b, c, d, x, y))
                        stack.popleft()
                    elif value == 36: # hflex1
                        a, b = x+stack.popleft(), y+stack.popleft()
                        c, d = a+stack.popleft(), b+stack.popleft()
                        x = c+stack.popleft()
                        result.append(curveto(a, b, c, d, x, d))
                        a = x+stack.popleft()
                        c, b = a+stack.popleft(), y+stack.popleft()
                        x = c+stack.popleft()
                        result.append(curveto(a, d, c, b, x, y))
                    elif value == 37: # flex1
                        oldx, oldy = x, y
                        a, b = x+stack.popleft(), y+stack.popleft()
                        c, d = a+stack.popleft(), b+stack.popleft()
                        x, y = c+stack.popleft(), d+stack.popleft()
                        result.append(curveto(a, b, c, d, x, y))
                        a, b = x+stack.popleft(), y+stack.popleft()
                        c, d = a+stack.popleft(), b+stack.popleft()
                        if abs(c - oldx) > abs(d - oldy):
                            x, y = c+stack.popleft(), d
                        else:
                            x, y = c, d+stack.popleft()
                        result.append(curveto(a, b, c, d, x, y))
                    elif value == 0: # dotsection
                        pass
                    elif value in (3, 4, 5, 9, 10, 11, 12, 14, 15, 18, 20, 21,
                        22, 23, 24, 26, 27, 28, 29, 30): # aritmetic, storage, conditional operators
                        raise NotImplementedError('Unsupported Type 2 operator.')
                    else:
                        raise ValueError('Reserved value.')
                elif value == 14: # endchar
                    # stack.clear()
                    break
                elif value == 25: # rlinecurve
                    while len(stack) > 6:
                        x += stack.popleft()
                        y += stack.popleft()
                        result.append(lineto(x, y))
                    a, b = x+stack.popleft(), y+stack.popleft()
                    c, d = a+stack.popleft(), b+stack.popleft()
                    x, y = c+stack.popleft(), d+stack.popleft()
                    result.append(curveto(a, b, c, d, x, y))
                elif value == 26: # vvcurveto
                    if len(stack) & 1:
                        x += stack.popleft()
                    while stack:
                        a, b = x, y+stack.popleft()
                        c, d = a+stack.popleft(), b+stack.popleft()
                        x, y = c, d+stack.popleft()
                        result.append(curveto(a, b, c, d, x, y))
                elif value == 27: # hhcurveto
                    if len(stack) & 1:
                        y += stack.popleft()
                    while stack:
                        a, b = x+stack.popleft(), y
                        c, d = a+stack.popleft(), b+stack.popleft()
                        x, y = c+stack.popleft(), d
                        result.append(curveto(a, b, c, d, x, y))
                elif value == 28: # shortint
                    stack.append(r.int16())
                elif value == 30 or value == 31: # vhcurveto, hvcurveto
                    vertical = value == 30
                    while stack:
                        if vertical:
                            a, b = x, y+stack.popleft()
                            c, d = a+stack.popleft(), b+stack.popleft()
                            x, y = c+stack.popleft(), (
                                (d+stack.popleft()) if len(stack) == 1 else d)
                        else:
                            a, b = x+stack.popleft(), y
                            c, d = a+stack.popleft(), b+stack.popleft()
                            y, x = d+stack.popleft(), (
                                (c+stack.popleft()) if len(stack) == 1 else c)
                        vertical = not vertical
                        result.append(curveto(a, b, c, d, x, y))
                else:
                    raise ValueError('Reserved value.')
            elif value <= 246:
                stack.append(value - 139)
            elif value <= 250:
                stack.append((value - 247)*256 + r.uint8() + 108)
            elif value <= 254:
                stack.append((251 - value)*256 - r.uint8() - 108)
            else: # 255
                stack.append(r.int32()/65536.0)
        if result:
            result.append(closepath)
        return result




