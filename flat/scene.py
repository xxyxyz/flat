from math import cos, pi, sin, sqrt
from multiprocessing import Pool
from random import choice, random
from time import time
from .image import raw




def _vector(x, y, z):
    return float(x), float(y), float(z)

def _vector_neg(a):
    x, y, z = a
    return -x, -y, -z

def _vector_add(a, b):
    ax, ay, az = a
    bx, by, bz = b
    return ax+bx, ay+by, az+bz

def _vector_addadd(a, b, c):
    ax, ay, az = a
    bx, by, bz = b
    cx, cy, cz = c
    return ax+bx+cx, ay+by+cy, az+bz+cz

def _vector_addmul(a, b, c):
    ax, ay, az = a
    bx, by, bz = b
    cx, cy, cz = c
    return ax+bx*cx, ay+by*cy, az+bz*cz

def _vector_addscale(a, b, factor):
    ax, ay, az = a
    bx, by, bz = b
    return ax+bx*factor, ay+by*factor, az+bz*factor

def _vector_sub(a, b):
    ax, ay, az = a
    bx, by, bz = b
    return ax-bx, ay-by, az-bz

def _vector_subsub(a, b, c):
    ax, ay, az = a
    bx, by, bz = b
    cx, cy, cz = c
    return ax-bx-cx, ay-by-cy, az-bz-cz

def _vector_mul(a, b):
    ax, ay, az = a
    bx, by, bz = b
    return ax*bx, ay*by, az*bz

def _vector_mulscale(a, b, factor):
    ax, ay, az = a
    bx, by, bz = b
    return ax*bx*factor, ay*by*factor, az*bz*factor

def _vector_scale(a, factor):
    x, y, z = a
    return x*factor, y*factor, z*factor

def _vector_length(a):
    x, y, z = a
    return sqrt(x*x + y*y + z*z)

def _vector_length2(a):
    x, y, z = a
    return x*x + y*y + z*z

def _vector_unit(a):
    x, y, z = a
    factor = 1.0/sqrt(x*x + y*y + z*z)
    return x*factor, y*factor, z*factor

def _vector_dot(a, b):
    ax, ay, az = a
    bx, by, bz = b
    return ax*bx + ay*by + az*bz

def _vector_cross(a, b): 
    ax, ay, az = a
    bx, by, bz = b
    return ay*bz - az*by, az*bx - ax*bz, ax*by - ay*bx

_zero = 0.0, 0.0, 0.0




class triangle(object):
    
    def __init__(self, a, b, c, material):
        a, b, c = _vector(*a), _vector(*b), _vector(*c)
        u, v = _vector_sub(b, a), _vector_sub(c, a)
        self.a, self.b, self.c = a, b, c
        self.ax, self.ay, self.az = a
        self.ux, self.uy, self.uz = u
        self.vx, self.vy, self.vz = v
        self.normal = _vector_unit(_vector_cross(u, v))
        self.tangent = _vector_unit(u)
        self.leg = _vector_cross(self.normal, self.tangent)
        self.area = _vector_length(_vector_cross(u, v))*0.5
        self.material = material
    
    def intersect(self, origin, direction):
        # Ref.: Moller, T., Trumbore, B. (1997).
        # Fast, Minimum Storage Ray/Triangle Intersection.
        ox, oy, oz = origin
        dx, dy, dz = direction
        px = dy*self.vz - dz*self.vy
        py = dz*self.vx - dx*self.vz
        pz = dx*self.vy - dy*self.vx
        det = self.ux*px + self.uy*py + self.uz*pz
        if det == 0.0:
            return -1.0
        inv_det = 1.0/det
        tx = ox - self.ax
        ty = oy - self.ay
        tz = oz - self.az
        u = (tx*px + ty*py + tz*pz)*inv_det
        if u < 0.0 or u > 1.0:
            return -1.0
        qx = ty*self.uz - tz*self.uy
        qy = tz*self.ux - tx*self.uz
        qz = tx*self.uy - ty*self.ux
        v = (dx*qx + dy*qy + dz*qz)*inv_det
        if v < 0.0 or u + v > 1.0:
            return -1.0
        return (self.vx*qx + self.vy*qy + self.vz*qz)*inv_det
    
    def sample(self):
        r = sqrt(random())
        u = 1.0 - r
        v = random()*r
        return (
            self.ax + self.ux*u + self.vx*v,
            self.ay + self.uy*u + self.vy*v,
            self.az + self.uz*u + self.vz*v)
    
    def bbox(self):
        x, y, z = zip(self.a, self.b, self.c)
        return bbox(min(x), min(y), min(z), max(x), max(y), max(z))




class bbox(object):
    
    @staticmethod
    def union(bboxes):
        b = bboxes[0]
        minx, miny, minz, maxx, maxy, maxz = \
            b.minx, b.miny, b.minz, b.maxx, b.maxy, b.maxz
        for b in bboxes:
            if b.minx < minx:
                minx = b.minx
            if b.maxx > maxx:
                maxx = b.maxx
            if b.miny < miny:
                miny = b.miny
            if b.maxy > maxy:
                maxy = b.maxy
            if b.minz < minz:
                minz = b.minz
            if b.maxz > maxz:
                maxz = b.maxz
        return bbox(minx, miny, minz, maxx, maxy, maxz)
    
    def __init__(self, minx, miny, minz, maxx, maxy, maxz):
        self.minx, self.miny, self.minz = minx, miny, minz
        self.maxx, self.maxy, self.maxz = maxx, maxy, maxz
    
    def axis(self):
        x, y, z = self.maxx-self.minx, self.maxy-self.miny, self.maxz-self.minz
        return 0 if x > y and x > z else 1 if y > z else 2
    
    def centroid(self):
        return (
            (self.minx + self.maxx)*0.5,
            (self.miny + self.maxy)*0.5,
            (self.minz + self.maxz)*0.5)
    
    def intersect(self, origin, inverse, minimum):
        # Ref.: Williams, A., Barrus, S., Morley, R. K., Shirley, P. (2003).
        # An Efficient and Robust Ray-Box Intersection Algorithm.
        ox, oy, oz = origin
        ix, iy, iz = inverse
        if ix >= 0:
            tmin = (self.minx - ox)*ix
            tmax = (self.maxx - ox)*ix
        else:
            tmin = (self.maxx - ox)*ix
            tmax = (self.minx - ox)*ix
        if iy >= 0:
            tymin = (self.miny - oy)*iy
            tymax = (self.maxy - oy)*iy
        else:
            tymin = (self.maxy - oy)*iy
            tymax = (self.miny - oy)*iy
        if tmin > tymax or tymin > tmax:
            return False
        if tymin > tmin:
            tmin = tymin
        if tymax < tmax:
            tmax = tymax
        if iz >= 0:
            tzmin = (self.minz - oz)*iz
            tzmax = (self.maxz - oz)*iz
        else:
            tzmin = (self.maxz - oz)*iz
            tzmax = (self.minz - oz)*iz
        if tmin > tzmax or tzmin > tmax:
            return False
        if tzmin > tmin:
            tmin = tzmin
        if tzmax < tmax:
            tmax = tzmax
        return tmin < minimum and tmax > 0.0




class diffuse(object):
    
    def __init__(self, reflectance, emittance=None):
        self.reflectance = _vector(*reflectance)
        self.emittance = _vector(*emittance) if emittance else _zero
        self.max = max(reflectance)
    
    def scatter(self, direction, tangent, leg, normal, u0, u1):
        phi = 2.0*pi*u0
        r = sqrt(u1)
        x = r*cos(phi)
        y = r*sin(phi)
        z = sqrt(1.0 - u1)
        if _vector_dot(normal, direction) > 0.0:
            return _vector_subsub(
                _vector_scale(tangent, x),
                _vector_scale(leg, y),
                _vector_scale(normal, z))
        return _vector_addadd(
            _vector_scale(tangent, x),
            _vector_scale(leg, y),
            _vector_scale(normal, z))




def _bvh_build(items):
    if len(items) > 1:
        bounds = bbox.union([item[1] for item in items])
        axis = bounds.axis()
        center = bounds.centroid()[axis]
        left, right = [], []
        for item in items:
            (left if item[2][axis] < center else right).append(item)
        if not left or not right:
            half = len(items)//2
            left, right = items[:half], items[half:]
        return _bvh_build(left), _bvh_build(right), bounds, axis
    else:
        return items[0][0], None, None, 0


class bvh(object):
    
    def __init__(self, items):
        items = [(i, b, b.centroid()) for i, b in [
            (i, i.bbox()) for i in items]]
        self.tree = _bvh_build(items)
        self.stack = [None]*32
    
    def intersect(self, origin, direction, previous):
        dx, dy, dz = direction
        inversed = 1.0/dx, 1.0/dy, 1.0/dz
        item = None
        minimum = 1e100
        stack = self.stack
        stack[0] = self.tree
        index = 0
        while index >= 0:
            left, right, bbox, axis = stack[index]
            index -= 1
            if right:
                if bbox.intersect(origin, inversed, minimum):
                    if direction[axis] < 0.0:
                        stack[index+1], stack[index+2] = left, right
                    else:
                        stack[index+1], stack[index+2] = right, left
                    index += 2
            else:
                if left != previous:
                    t = left.intersect(origin, direction)
                    if 0.0 < t < minimum:
                        item, minimum = left, t
        if item:
            return item, _vector_addscale(origin, direction, minimum)
        return None, None




class scene(object):
    
    def __init__(self):
        self.sky = 0.09, 0.09, 0.11
        self.ground = 0.10, 0.09, 0.07
        self.origin = 1.0, 1.0, 1.0
        self.target = 0.0, 0.0, 0.0
        self.length = 50.0
        self.items = []
    
    def environment(self, sky, ground):
        self.sky, self.ground = _vector(*sky), _vector(*ground)
    
    def camera(self, origin, target, length=50.0):
        self.origin, self.target = _vector(*origin), _vector(*target)
        self.length = float(length)
    
    def view(self):
        direction = _vector_unit(_vector_sub(self.target, self.origin))
        up = 0.0, 1.0, 0.0
        right = _vector_cross(direction, up)
        if _vector_length2(right) > 0.0:
            right = _vector_unit(right)
        else:
            right = 1.0 if direction[1] < 0.0 else -1.0, 0.0, 0.0
        up = _vector_unit(_vector_cross(right, direction))
        forward = _vector_scale(direction, self.length/18.0) # 1/tan((2*atan(36/(2*length)))/2)
        return up, right, forward
    
    def clear(self):
        self.items.clear()
    
    def add(self, mesh, material):
        self.items.append((mesh, material))
    
    def render(self, width, height, samples=10, multiprocessing=True, info=True):
        if info:
            print('Rendering...')
        start = time()
        triangles, emitters = [], []
        for mesh, material in self.items:
            t = [triangle(a, b, c, material) for a, b, c in mesh.triplets]
            triangles.extend(t)
            if max(material.emittance) > 0.0:
                emitters.extend(t)
        if info:
            print('Mesh done.')
        accelerator = bvh(triangles)
        if info:
            print('Accelerator done.')
        up, right, forward = self.view()
        skyground = _vector_mul(self.sky, self.ground)
        context = (width, height, samples, accelerator, emitters,
            self.origin, up, right, forward, self.sky, skyground),
        if multiprocessing:
            pool = Pool(initializer=_render_initializer, initargs=context)
            result = pool.imap(_pathtracing_row, range(height))
        else:
            result = map(_pathtracing_row, range(height), context*height)
        rows = []
        step = 0
        for y, row in enumerate(result):
            rows.append(row)
            if info:
                s = (y + 1)*100//height
                if s > step:
                    step = s
                    print('%d%%' % step)
        rows.reverse()
        if info:
            print('...done in %.2f seconds.' % (time() - start))
        r = raw(width, height)
        for y in range(height):
            i = y*width*3
            r.data[i:i+width*3] = rows[y]
        return r




_global_context = None


def _render_initializer(context):
    global _global_context
    _global_context = context


def _pathtracing_row(y, context=None):
    width, height, samples, accelerator, emitters, \
        origin, up, right, forward, sky, skyground = context or _global_context
    intersect = accelerator.intersect
    count = len(emitters)
    row = [0.0]*width*3
    ratio = 1.0/max(width, height)
    inv = 1.0/samples
    fix = 1.0/(samples*samples)
    for x in range(width):
        r, g, b = 0.0, 0.0, 0.0
        for j in range(samples):
            for i in range(samples):
                dx = (2.0*(x + random()) - width)*ratio
                dy = (2.0*(y + random()) - height)*ratio
                direction = _vector_unit(_vector_addadd(
                    forward, _vector_scale(right, dx), _vector_scale(up, dy)))
                u0 = (i + random())*inv
                u1 = (j + random())*inv
                color = _radiance(intersect, emitters, count, sky, skyground,
                    origin, direction, u0, u1)
                r += color[0]
                g += color[1]
                b += color[2]
        offset = x*3
        row[offset], row[offset+1], row[offset+2] = r*fix, g*fix, b*fix
    return row


def _radiance(intersect, emitters, count, sky, skyground,
    origin, direction, u0, u1):
    # Ref.: Ainsworth, H. / HXA7241. (2008). MiniLight.
    color = 0.0, 0.0, 0.0
    attenuation = 1.0, 1.0, 1.0
    previous = None
    while True:
        item, position = intersect(origin, direction, previous)
        if not item:
            background = sky if direction[1] > 0.0 else skyground
            return _vector_addmul(color, background, attenuation)
        material = item.material
        if not previous and _vector_dot(direction, item.normal) < 0.0:
            color = _vector_addmul(color, material.emittance, attenuation)
        if emitters:
            emitter = choice(emitters)
            d = _vector_sub(emitter.sample(), position)
            into = _vector_dot(emitter.normal, d)
            if into < 0.0:
                away = _vector_dot(item.normal, d)
                side = _vector_dot(item.normal, direction)
                if away < 0.0:
                    away = -away
                    side = -side
                if side < 0.0:
                    i, p = intersect(position, d, item)
                    if emitter == i:
                        illumination = _vector_mulscale(
                            material.reflectance,
                            emitter.material.emittance,
                            count*emitter.area*away*-into/(
                                pi*_vector_length2(d)**2))
                        color = _vector_addmul(color, illumination, attenuation)
        if random() > material.max:
            return color
        origin = position
        direction = material.scatter(
            direction, item.tangent, item.leg, item.normal, u0, u1)
        u0, u1 = random(), random()
        attenuation = _vector_mulscale(
            attenuation, material.reflectance, 1.0/material.max)
        previous = item




