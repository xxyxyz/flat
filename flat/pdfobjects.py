
from binascii import hexlify

from .utils import dump




class null(object):
    
    def pdf(self):
        return ''


class boolean(object):
    
    def __init__(self, value):
        self.value = value
    
    def pdf(self):
        return 'true' if self.value else 'false'


class number(object):
    
    def __init__(self, number):
        self.number = number
    
    def pdf(self):
        return dump(self.number)


class string(object):
    
    def __init__(self, string):
        self.string = string
    
    def pdf(self):
        return '(%s)' % self.string


class hexstring(object):

    def __init__(self, string):
        self.string = string

    def pdf(self):
        return '<%s>' % hexlify(self.string)


class name(object):
    
    def __init__(self, name):
        self.name = name
    
    def pdf(self):
        return '/%s' % self.name


class safename(object):
    
    def __init__(self, name):
        self.name = name
    
    def pdf(self):
        special = '#', '(', ')', '<', '>', '[', ']', '{', '}', '/', '%'
        return '/%s' % ''.join(
            c if '!' <= c <= '~' and c not in special else \
            '#%x' % ord(c) for c in self.name)


class array(object):
    
    def __init__(self, array):
        self.array = array
    
    def pdf(self):
        return '[%s]' % ' '.join(item.pdf() for item in self.array)


class dictionary(object):
    
    def __init__(self, dictionary):
        self.dictionary = dictionary
    
    def pdf(self):
        return '<< %s >>' % ' '.join(
            '/%s %s' % (k, v.pdf()) for k, v in self.dictionary.items())


class obj(object):

    def __init__(self, tag, item):
        self.tag = tag
        self.item = item
    
    def pdf(self):
        return (
            '%d 0 obj\n'
            '%s\n'
            'endobj') % (self.tag, self.item.pdf())


class stream(object):
    
    def __init__(self, tag, dictionary, stream):
        self.tag = tag
        self.dictionary = dictionary
        self.stream = stream
    
    def pdf(self):
        return (
            '%d 0 obj\n'
            '%s\n'
            'stream\n'
            '%s\n'
            'endstream\n'
            'endobj') % (
                self.tag, dictionary(self.dictionary).pdf(), self.stream)


class reference(object):
    
    def __init__(self, tag):
        self.tag = tag
    
    def pdf(self):
        return '%d 0 R' % self.tag


class lazyreference(object):
    
    def __init__(self, obj):
        self.obj = obj
    
    def pdf(self):
        return '%d 0 R' % self.obj.tag




