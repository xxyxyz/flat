
from . import stl




class mesh(object):
    
    @staticmethod
    def openstl(path):
        with open(path, 'rb') as f:
            data = f.read()
            parse = stl.parseascii if stl.isascii(data) else stl.parse
            return mesh(*parse(data))
    
    def __init__(self, *triplets):
        self.triplets = triplets
    
    def stl(self, path=''):
        data = stl.dump(self.triplets)
        if path:
            with open(path, 'wb') as f:
                f.write(data)
        return data




