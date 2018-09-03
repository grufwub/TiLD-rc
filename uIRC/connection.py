import socket

__metaclass__ = type

def identity(x):
    return x

class Factory:
    """
    A class for creating custom socket connection
    """

    family = socket.AF_INET

    def __init__(self, bind_address = None, wrapper = identity, ipv6 = False):
        self.bind_address = bind_address
        self.wrapper = wrapper
        if ipv6: self.family = socket.AF_INET6
    
    def connect(self, server_address):
        sock = self.wrapper(socket.socket(self.family, socket.SOCK_STREAM))
        self.bind_address and sock.bind(self.bind_address)
        sock.connect(server_address)
        return sock
    
    __call__ = connect