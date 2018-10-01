from . import stl




class mesh(object):
    
    @staticmethod
    def openstl(path):
        with open(path, 'rb') as f:
            data = f.read()
            if stl.isascii(data):
                triplets = stl.parseascii(data)
            else:
                triplets = stl.parse(data)
            return mesh(triplets)
    
    def __init__(self, triplets):
        self.triplets = triplets
    
    def stl(self, path=''):
        data = stl.dump(self.triplets)
        if path:
            with open(path, 'wb') as f:
                f.write(data)
        return data




