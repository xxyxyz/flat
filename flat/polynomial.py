from math import sqrt




def evaluate1(a, b, x):
    return a*x + b

def evaluate2(a, b, c, x):
    return (a*x + b)*x + c

def evaluate3(a, b, c, d, x):
    return ((a*x + b)*x + c)*x + d




def roots1(a, b):
    if a == 0.0:
        return ()
    return -b/a,

def roots2(a, b, c):
    if a == 0.0:
        return roots1(b, c)
    if c == 0.0:
        if b == 0.0:
            return 0.0,
        return (0.0,) + roots1(a, b)
    t = b/(2.0*a)
    r = t**2 - c/a
    if r == 0.0:
        return -t,
    if r > 0.0:
        x = sqrt(r)
        return x-t, -x-t
    return ()




