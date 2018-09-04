import collections
import uIRC.client as client

_MAX_BUFFER = 50

class Client:
    """
    Very simple client wrapper for IRC
    """

    def __init__(self):
        self.reactor = client.Reactor()
        self.conn = None
        self.channel = None
        # set other variables?
    
    def connect(self, server, port, ssl, nick, user, realname, password, channel):
        try:
            self.conn = self.reactor.server().connect(
                server, port, nick, password, user, realname
            )
            self.conn.join(self.channel or channel)
        except client.ServerConnectionError:
            raise RuntimeError(
                "Unable to connect to server %s on port %d"
                % (server, port)
            )
    
    def process_forever(self):
        self.reactor.process_forever()
    
    def disconnect(self):
        # In the future handle individual disconnects?
        self.reactor.server().disconnect_all()
    
    def channel_list(self):
        return self.conn.list()
    
    def set_channel(self, channel):
        self.channel = channel
    
    def on_pubmsg(self, func):
        self.reactor.add_global_handler("pubmsg", func)
    
    def on_privmsg(self, func):
        self.reactor.add_global_handler("privmsg", func)
    
    def on_quit(self, func):
        self.reactor.add_global_handler("quit", func)
    
    def on_join(self, func):
        self.reactor.add_global_handler("join", func)
    
    def on_nick(self, func):
        self.reactor.add_global_handler("nick", func)
    
    def on_kick(self, func):
        self.reactor.add_global_handler("kick", func)
    
