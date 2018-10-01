from .misc import inf




class tree(object):
    
    __slots__ = 'item', 'parent', 'children', 'x', 'y', '_ancestor', \
        '_number', '_thread', '_prelim', '_change', '_shift', '_mod'
    
    def __init__(self, item):
        self.item = item
        self.parent = None
        self.children = []
        self.x, self.y = 0.0, 0.0
        self._ancestor = self
        self._number = 0
        self._thread = None
        self._prelim = 0.0
        self._change = 0.0
        self._shift = 0.0
        self._mod = 0.0
    
    def add(self, item):
        t = tree(item)
        t.parent = self
        t._number = len(self.children)
        self.children.append(t)
        return t
    
    def layout(self):
        # Ref.: Buchheim, Ch., Junger, M., Leipert, S. (2002).
        # Improving Walker's algorithm to run in linear time.
        _first_walk(self, None)
        _second_walk(self, -self._prelim, 0.0)
        return self
    
    def transpose(self):
        for node in self.nodes():
            node.x, node.y = node.y, node.x
        return self
    
    def frame(self, x, y, width, height):
        minx, miny, maxx, maxy = inf, inf, 0.0, 0.0
        for node in self.nodes():
            if node.x < minx:
                minx = node.x
            elif node.x > maxx:
                maxx = node.x
            if node.y < miny:
                miny = node.y
            elif node.y > maxy:
                maxy = node.y
        width /= maxx - minx
        height /= maxy - miny
        x -= minx*width
        y -= miny*height
        for node in self.nodes():
            node.x, node.y = node.x*width+x, node.y*height+y
        return self
    
    def nodes(self):
        yield self
        for child in self.children:
            for node in child.nodes():
                yield node




def _first_walk(v, left):
    if not v.children:
        w = left
        if w:
            v._prelim = w._prelim + _distance(v, w)
    else:
        default = v.children[0]
        previous = None
        for w in v.children:
            _first_walk(w, previous)
            default = _apportion(w, default, previous)
            previous = w
        _execute_shifts(v)
        midpoint = 0.5*(v.children[0]._prelim + v.children[-1]._prelim)
        w = left
        if w:
            v._prelim = w._prelim + _distance(v, w)
            v._mod = v._prelim - midpoint
        else:
            v._prelim = midpoint

def _distance(v, w):
    if v.parent == w.parent:
        return 1.0
    return 2.0

def _apportion(v, default, left):
    w = left
    if w:
        vir = vor = v
        vil = w
        vol = vir.parent.children[0]
        sir = vir._mod
        sor = vor._mod
        sil = vil._mod
        sol = vol._mod
        while _next_right(vil) and _next_left(vir):
            vil = _next_right(vil)
            vir = _next_left(vir)
            vol = _next_left(vol)
            vor = _next_right(vor)
            vor._ancestor = v
            shift = (vil._prelim + sil) - (vir._prelim + sir) + _distance(vil, vir)
            if shift > 0.0:
                _move_subtree(_ancestor(vil, v, default), v, shift)
                sir += shift
                sor += shift
            sil += vil._mod
            sir += vir._mod
            sol += vol._mod
            sor += vor._mod
        if _next_right(vil) and not _next_right(vor):
            vor._thread = _next_right(vil)
            vor._mod += sil - sor
        if _next_left(vir) and not _next_left(vol):
            vol._thread = _next_left(vir)
            vol._mod += sir - sol
            default = v
    return default

def _next_left(v):
    if v.children:
        return v.children[0]
    return v._thread

def _next_right(v):
    if v.children:
        return v.children[-1]
    return v._thread

def _move_subtree(wl, wr, shift):
    subtrees = wr._number - wl._number
    wr._change -= shift/subtrees
    wr._shift += shift
    wl._change += shift/subtrees
    wr._prelim += shift
    wr._mod += shift

def _execute_shifts(v):
    shift = 0.0
    change = 0.0
    for w in reversed(v.children):
        w._prelim += shift
        w._mod += shift
        change += w._change
        shift += w._shift + change

def _ancestor(vil, v, default):
    if vil._ancestor.parent == v.parent:
        return vil._ancestor
    return default

def _second_walk(v, m, level):
    v.x = v._prelim + m
    v.y = level
    for w in v.children:
        _second_walk(w, m + v._mod, level + 1.0)




