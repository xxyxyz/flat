import re
import struct




def isascii(data):
    return data.startswith(b'solid ')

def parseascii(data):
    triplets = []
    pattern = re.compile(3*r'vertex\s+(\S+)\s+(\S+)\s+(\S+)\s+')
    m = pattern.search(data)
    while m:
        ax, ay, az, bx, by, bz, cx, cy, cz = map(float, m.groups())
        triplets.append(((ax, az, ay), (bx, bz, by), (cx, cz, cy)))
        m = pattern.search(data, m.end())
    return triplets

def parse(data):
    triplets = []
    count, = struct.unpack_from('<L', data, 80)
    unpack = struct.Struct('<9f').unpack_from
    offset = 80 + 4 + 12
    for i in range(count):
        ax, ay, az, bx, by, bz, cx, cy, cz = unpack(data, offset)
        triplets.append(((ax, az, ay), (bx, bz, by), (cx, cz, cy)))
        offset += 50
    return triplets

def dump(triplets):
    count = len(triplets)
    data = bytearray(80 + 4 + 50*count)
    data[0:4] = b'Flat'
    struct.pack_into('<L', data, 80, count)
    pack = struct.Struct('<9f').pack_into
    offset = 80 + 4 + 12
    for (ax, ay, az), (bx, by, bz), (cx, cy, cz) in triplets:
        pack(data, offset, ax, az, ay, bx, bz, by, cx, cz, cy)
        offset += 50
    return bytes(data)




