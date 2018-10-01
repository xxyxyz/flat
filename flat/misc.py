from math import copysign




from math import inf




def similar(x, y, absolute=1e-10, relative=1e-10):
    return abs(x - y) <= absolute + relative*max(abs(x), abs(y))




def iround(x):
    return int(x + copysign(0.5, x))




def clamp(x):
    return 0 if x < 0 else 255 if x > 255 else x




def chunks(sequence, size):
    for i in range(0, len(sequence), size):
        yield sequence[i:i+size]




def dump(number):
    return (b'%.4f' % number).rstrip(b'0').rstrip(b'.')




def save(path, data):
    if path:
        with open(path, 'wb') as f:
            f.write(data)
    return data




def scale(units):
    if units == 'pt':
        return 1.0
    if units == 'mm':
        return 72.0/25.4
    if units == 'cm':
        return 72.0/2.54
    if units == 'in':
        return 72.0
    raise ValueError('Invalid units.')




class rmq(object):
    # Ref.: Bender, M. A., Farach-Colton, M. (2000). The LCA Problem Revisited.
    
    def __init__(self, sequence):
        self.table = [sequence]
        length = len(sequence)
        for j in range(length.bit_length() - 1):
            size = 1 << j
            length -= size
            row = sequence[:length]
            i = size
            for item in row:
                if item < sequence[i]:
                    row[i - size] = sequence[i]
                i += 1
            self.table.append(row)
            sequence = row
    
    def max(self, i, j):
        k = (j - i).bit_length() - 1
        row = self.table[k]
        return max(row[i], row[j - (1 << k)])




