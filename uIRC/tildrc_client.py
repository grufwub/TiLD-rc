import client

class Client:
    def __init__(self):
        self.reactor = Reactor()
        self.connection = self.reactor.server()

        # TODO: more here
    
    def connect(self, server, port, nickname, password = None, username = None, ircname = None):
        self.connection.connect(server, port, nickname, password, username, ircname)
    
    def disconnect_all(self, message = ""):
        self.reactor.disconnect_all(message)

    def start(self):
        self.reactor.process_forever()