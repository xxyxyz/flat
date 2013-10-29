
def memoize(function):
    cache = {}
    def memoized(*args):
        if args not in cache:
            cache[args] = function(*args)
        return cache[args]
    return memoized


@memoize
def dump(number):
    return ('%.4f' % number).rstrip('0').rstrip('.')


def save(path, data):
    if path:
        with open(path, 'wb') as f:
            f.write(data)
    return data


class lazy(object):
    def __init__(self, function):
        self.function = function
    def __get__(self, instance, owner):
        if instance is None:
            return None
        value = self.function(instance)
        setattr(instance, self.function.__name__, value)
        return value


def scale(units):
    if units == 'pt':
        return 1.0
    elif units == 'mm':
        return 72.0 / 25.4
    elif units == 'cm':
        return 72.0 / 2.54
    elif units == 'in':
        return 72.0
    raise AssertionError('Invalid units.')


def equal(a, b):
    return -1e-10 <= a - b < 1e-10


def clamp(x):
    return 0 if x < 0 else 255 if x > 255 else x


def powerset(sequence): # ordered
    result = [[]]
    for item in sequence:
        result += [subset+[item] for subset in result]
    return result


def pascal(n):
    row = [1]
    for k in range(n):
        row.append(row[k] * (n-k) // (k+1))
    return row


def chunks(sequence, size):
    return [sequence[i:i+size] for i in range(0, len(sequence), size)]


def staircase(height, count):
    step, remainder = divmod(height, count)
    result = []
    accumulator = 0
    for i in range(count):
        if i < remainder:
            accumulator += step + 1
        else:
            accumulator += step
        result.append(accumulator)
    return result


class record(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
    def copy(self):
        return record(**self.__dict__)
    def update(self, other):
        self.__dict__.update(other.__dict__)


class rmq(object):
    # Based on "The LCA Problem Revisited"
    # by Michael A. Bender and Martin Farach-Colton, 2000
    def __init__(self, sequence):
        self.table = [sequence]
        length = len(sequence)
        for j in range(length.bit_length() - 1):
            size = 1 << j
            length -= size
            new = sequence[:length]
            for i, item in enumerate(new, size):
                if item < sequence[i]:
                    new[i - size] = sequence[i]
            self.table.append(new)
            sequence = new
    def max(self, i, j):
        k = (j - i).bit_length() - 1
        row = self.table[k]
        return max(row[i], row[j - (1 << k)])




