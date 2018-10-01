import os, socket, struct




def view(data):
    port = os.environ.get('EVEN_SERVER_PORT')
    if port:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', int(port)))
        s.sendall(struct.pack('>L', len(data)))
        s.sendall(data)
        s.recv(1)
        s.close()




