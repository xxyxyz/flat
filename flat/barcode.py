from itertools import groupby




edge, center = (1, 0, 1), (0, 1, 0, 1, 0)

patterns = [
    ((0, 0, 0, 1, 1, 0, 1), (0, 1, 0, 0, 1, 1, 1)),
    ((0, 0, 1, 1, 0, 0, 1), (0, 1, 1, 0, 0, 1, 1)),
    ((0, 0, 1, 0, 0, 1, 1), (0, 0, 1, 1, 0, 1, 1)),
    ((0, 1, 1, 1, 1, 0, 1), (0, 1, 0, 0, 0, 0, 1)),
    ((0, 1, 0, 0, 0, 1, 1), (0, 0, 1, 1, 1, 0, 1)),
    ((0, 1, 1, 0, 0, 0, 1), (0, 1, 1, 1, 0, 0, 1)),
    ((0, 1, 0, 1, 1, 1, 1), (0, 0, 0, 0, 1, 0, 1)),
    ((0, 1, 1, 1, 0, 1, 1), (0, 0, 1, 0, 0, 0, 1)),
    ((0, 1, 1, 0, 1, 1, 1), (0, 0, 0, 1, 0, 0, 1)),
    ((0, 0, 0, 1, 0, 1, 1), (0, 0, 1, 0, 1, 1, 1))]

encodings = [
    (0, 0, 0, 0, 0, 0),
    (0, 0, 1, 0, 1, 1),
    (0, 0, 1, 1, 0, 1),
    (0, 0, 1, 1, 1, 0),
    (0, 1, 0, 0, 1, 1),
    (0, 1, 1, 0, 0, 1),
    (0, 1, 1, 1, 0, 0),
    (0, 1, 0, 1, 0, 1),
    (0, 1, 0, 1, 1, 0),
    (0, 1, 1, 0, 1, 0)]




def checksum(digits):
    even, odd = sum(digits[0::2]), sum(digits[1::2])
    return (10 - (3*even + odd))%10

def structure(digits):
    encoding, first, second = encodings[digits[0]], digits[1:7], digits[7:13]
    yield from edge
    for digit, selector in zip(first, encoding):
        yield from patterns[digit][selector]
    yield from center
    for digit in second:
        yield from (1-x for x in patterns[digit][0])
    yield from edge

def ean13(string):
    digits = list(map(int, string))
    if len(digits) != 13:
        raise ValueError('Invalid number of digits.')
    if checksum(digits[:12]) != digits[12]:
        raise ValueError('Invalid checksum.')
    for key, group in groupby(structure(digits)):
        yield len(list(group))




