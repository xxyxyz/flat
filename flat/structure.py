
from weakref import proxy




class tree(object):
    # Based on "Improving Walker's algorithm to run in linear time"
    # by Christoph Buchheim, Michael Junger, and Sebastian Leipert, 2002
    
    __slots__ = ('item', 'parent', 'number', 'children', 'x', 'y', '_ancestor',
        '_thread', '_prelim', '_change', '_shift', '_mod', '__weakref__')
    
    def __init__(self, sequence, item=None, parent=None, number=0):
        self.item = item
        self.parent = parent
        self.number = number
        self.children = []
        self.x, self.y = 0.0, 0.0
        self._ancestor = self
        self._thread = None
        self._prelim = 0.0
        self._change = 0.0
        self._shift = 0.0
        self._mod = 0.0
        if not parent and sequence:
            self.item = sequence[0]
            if len(sequence) > 1:
                _parse_sequence(self, sequence[1])
            _first_walk(self)
            _second_walk(self, -self._prelim)
    
    def flip(self):
        for node in self.nodes():
            node.x, node.y = node.y, node.x
        return self
    
    def frame(self, x, y, width, height):
        minx, maxx, miny, maxy = 1e100, 0.0, 1e100, 0.0
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
        x -= minx * width
        y -= miny * height
        for node in self.nodes():
            node.x, node.y = node.x * width + x, node.y * height + y
        return self
    
    def nodes(self):
        yield self
        for child in self.children:
            for node in child.nodes():
                yield node




def _parse_sequence(parent, sequence):
    reference = proxy(parent)
    backup = parent
    for item in sequence:
        if isinstance(item, (list, tuple)):
            _parse_sequence(parent, item)
            parent = backup
        else:
            number = len(backup.children)
            parent = tree(None, item, reference, number)
            backup.children.append(parent)


def _first_walk(v, _w=None):
    if not v.children:
        if _w:
            v._prelim = _w._prelim + _distance(v, _w)
    else:
        default = v.children[0]
        _previous = None
        for w in v.children:
            _first_walk(w, _previous)
            default = _apportion(w, default, _previous)
            _previous = w
        _execute_shifts(v)
        midpoint = 0.5 * (v.children[0]._prelim + v.children[-1]._prelim)
        if _w:
            v._prelim = _w._prelim + _distance(v, _w)
            v._mod = v._prelim - midpoint
        else:
            v._prelim = midpoint


def _distance(left, right):
    if left.parent == right.parent:
        return 1.0
    return 2.0


def _apportion(v, default, _w):
    if _w:
        vir = vor = v
        vil = _w
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
    _subtrees = shift / float(wr.number - wl.number) # TODO python 3: remove float
    wr._change -= _subtrees
    wr._shift += shift
    wl._change += _subtrees
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


def _second_walk(v, m, level=0.0):
    v.x = v._prelim + m
    v.y = level
    for w in v.children:
        _second_walk(w, m + v._mod, level + 1.0)




