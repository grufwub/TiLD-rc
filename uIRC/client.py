import abc
import bisect
import collections
import select
import socket
import time
import struct
import threading
import functools
import itertools
import extern_libs
from functools import Throttler
from itertools import always_iterable, infinite_call
from extern_libs import consume, 

# TODO: finish adding permanent _STR's
_ADMIN_STR = "ADMIN"
_ACTION_STR = "ACTION"
_CAP_STR = "CAP"
_GLOBOPS_STR = "GLOBOPS"
_INFO_STR = "INFO"
_STOP_STR = "NO MORE"
_CMD_NICK_STR = "nick"
_CMD_WELC_STR = "welcome"
_CMD_FTRLIST_STR = "featurelist"
_CMD_PUBMSG_STR = "pubmsg"
_CMD_PRVMSG_STR = "privmsg"
_CMD_NOTICE_STR = "notice"
_CMD_PUBNOTICE_STR = "pubnotice"
_CMD_PRVNOTICE_STR = "privnotice"
_CMD_CTCP_STR = "ctcp"
_CMD_CTCPRPLY_STR = "ctcpreply"
_CMD_MODE_STR = "mode"
_CMD_UMODE_STR = "umode"
_CMD_PING_STR = "ping"
_CMD_QUIT_STR = "quit"
_CMD_ACTION_STR = "action"

def _ping_ponger(connection, event):
    # Global handler for ping event
    connection.pong(event.target)

class Connection:
    """
    Base class for IRC connections
    """

    transmit_encoding = "utf-8"
    "Transmission used for encoding"

    @abc.abstractproperty
    def socket(self):
        "The socket for this connection"
    
    def __init__(self, reactor):
        self.reactor = reactor
    
    def encode(self, msg):
        """
        Encode a message for transmission
        """

        return msg.encode(self.transmit_encoding)

class ServerConnection(Connection):
    """
    IRC server connection.
    """

    buffer_class = extern_libs.DecodingLineBuffer
    socket = None
    connected = False

    def __init__(self, reactor):
        super(ServerConnection, self).__init__(reactor)
        self.features = features.FeatureSet()
    
    @functools.save_method_args
    def connect(self, server, port, nickname, password = None, username = None,
                    ircname = None, connect_factory = connection.Factory()):
        """
        Connect / reconnect to a server.
        Can reconnect to a closed connection!
        Returns the ServerConnection object
        """

        if self.connected: self.disconnect("Changing servers")
        self.buffer = self.buffer_class()
        self.handlers = dict()
        self.real_server_name = ""
        self.real_nickname = nickname
        self.server = server
        self.port = port
        self.server_address = (server, port)
        self.nickname = nickname
        self.username = username or nickname
        self.ircname = ircname or nickname
        self.password = password
        self.connect_factory = connect_factory

        try:
            self.socket = self.connect_factory(self.server_address)
        except socket.error as ex:
            raise ServerConnectionError("Couldn't connect to socket: %s" % ex)

        self.connected = True
        self.react._on_connect(self.socket)

        # Now to log on...
        if self.password:
            self.pass_(self.password)
        self.nick(self.nickname)
        self.user(self.username, self.ircname)

        return self
    
    def reconnect(self):
        """
        Reconnect with the last arguments passed to self.connect()
        """

        self.connect(*self._saved_connect.args, **self._saved_connect.kwargs)
    
    def close(self):
        """
        Close the connection permanently, connection object becomes unusable.
        """

        # Without thread lock, there is a window during which select()
        # can find a closed socket leading EBADF error
        with self.reactor.mutex:
            self.disconnect("Closing object")
            self.reactor._remove_connection(self)
    
    def get_server_name(self):
        """
        Get the real server name.

        Return real server, or, more specifically, what the server calls
        itself.
        """

        return self.real_server_name or ""
    
    def get_nickname(self):
        """
        Get the (real) nickname.

        Returns the (real) nickname. Library keeps track of nick changes,
        so might not be the nick name that was passed to connect() method
        """

        return self.real_nickname
    
    @contextlib.contextmanager
    def as_nick(self, name):
        """
        Set the nick for the duration of the context.
        """

        orig = self.get_nickname()
        self.nick(name)

        try:
            yield orig
        finally:
            self.nick(orig)
    
    def process_data(self):
        """
        Read and process input from self.socket
        """

        try:
            reader = getattr(self.socket, 'read', self.socket.recv)
            new_data = reader(2 ** 14)
        except socket.error:
            # The server hung up on us ):
            self.disconnect("Connection reset by peer")
            return
        
        if not new_data:
            # Read nothing: connection must be down
            self.disconnect("Connection reset by peer. No new data")
            return
        
        self.buffer.feed(new_data)

        # Process each non-empty line after logging all lines
        for line in self.buffer:
            if not line: continue
            self._process_line(line)
    
    def _process_line(self, line):
        event = Event("all_raw_messages", self.get_server_name(), None, list(line))
        self._handle_event(event)

        # Groups overflowing command lines together
        grp = _rfc_1459_command_regexp.match(line).group

        source = NickMask.from_group( grp("prefix") )
        command = self._command_from_group( grp("command") )
        arguments = message.Arguments.from_group( grp("argument") )
        tags = message.Tag.from_group( grp("tags") )

        if source and not self.real_server_name:
            self.real_server_name = source
        
        if command == _CMD_NICK_STR:
            if source.nick == self.real_nickname:
                self.real_nickname = arguments[0]
        elif command == _CMD_WELC_STR:
            # Record nickname in case client changed nick
            # in nickname callback
            self.real_nickname = arguments[0]
        elif command == _CMD_FTRLIST_STR:
            self.features.load(arguments)
        
        handler = (
            self._handle_message
            if command in [_CMD_PRVMSG_STR, _CMD_NOTICE_STR]
            else: self._handle_other
        )

        handler(arguments, command, source, tags)
    
    def _handle_message(self, arguments, command, source, tags):
        target, msg = arguments[:2]
        messages = ctcp.dequote(msg)

        if command == _CMD_PRVMSG_STR:
            if is_channel(target):
                command = _CMD_PUBMSG_STR
            else:
                if is_channel(target):
                    command = _CMD_PUBNOTICE_STR
                else:
                    command = _CMD_PRVNOTICE_STR
        
        for m in messages:
            if isinstance(m, tuple):
                if command in [_CMD_PRVMSG_STR, _CMD_PUBMSG_STR]:
                    command = _CMD_CTCP_STR
                else:
                    command = _CMD_CTCPRPLY_STR
            
                m = list(m)
                event = Event(command, source, target, m, tags)
                self._handle_event(event)

                if command == _CMD_CTCP_STR and m[0] == _ACTION_STR:
                    event = Event(_CMD_ACTION_STR, source, target, list(m), tags)
                    self._handle_event(event)
            
            else:
                event = Event(command, source, target, list(m), tags)
                self._handle_event(event)

    def _handle_other(self, arguments, command, source, tags):
        target = None

        if command == _CMD_QUIT_STR:
            arguments = list(arguments[0])
        elif command == _CMD_PING_STR:
            target = arguments[0]
        else:
            target = arguments[0] if arguments else None
            arguments = arguments[1:]
        
        if command == _CMD_MODE_STR:
            if not is_channel(target):
                command = _CMD_UMODE_STR
        
        event = Event(command, source, target, arguments, tags)
        self._handle_event(event)

    @staticmethod
    def _command_from_group(group):
        command = group.lower()
        # Translate numerics into more readable strings
        return events.numerics.get(command, command)
    
    def _handle_event(self, event):
        """
        Internal >:]
        """

        self.reactor._handle_event(self, event)
        if event.type in self.handlers:
            for func in self.handlers[event.type]:
                func(self, event)
    
    def is_connected(self):
        """
        Return connection status.
        """

        return self.connected
    
    def add_global_handler(self, *args):
        """
        Add global handler.
        """

        self.reactor.add_global_handler(*args)
    
    def action(self, target, action):
        """
        Send a CTCP ACTION command
        """

        self.ctcp(_CMD_ACTION_STR, target, action)

    def admin(self, server = ""):
        """
        Send an admin command
        """

        self.send_items(_ADMIN_STR, server)
    
    def cap(self, subcommand, *args):
        """
        Send a CAP command according to spec
        'capability negiation'
        """

        cap_subcommands = set("LS LIST REQ ACK NAK CLEAR END".split())
        client_subcommands = set(cap_subcommands) - {"NAK"}
        assert subcommand in client_subcommands, "invalid subcommand"
    
        def _multi_parameter(args):
            """
            According to the spec:
            If more than one capability is named, RFC1459 designated
            sentinel (:) for multi-parameter argument must be present.
            """

            if len(args) > 1:
                return (":" + args[0],) + args[1:]
            return args

        self.send_items(_CAP_STR, subcommand, *_multi_parameter(args))
    
    def ctcp(self, ctcptype, target, paramater = ""):
        """
        Send a CTCP command
        """

        ctcptype = ctcptype.upper()
        tmpl = (
            "\001{ctcptype} {parameter}\001" if parameter
            else "\001{ctcptype}\001"
        )

        self.privmsg(target, tmpl.format(**vars()))
    
    def ctcp_reply(self, target, paramter):
        """
        Send a CTCP REPLY command
        """

        self.notice(target, "\001%s\001" % parameter)
    
    def disconnect(self, message = ""):
        """
        Hang up the connection
        """

        try:
            del self.connected
        except AttributeError:
            # do nothing
            return

        self.quit(message)

        try:
            self.socket.shutdown(socket.SHUT_WR)
            self.socket.close()
        except socket.error:
            # Do nothing, ignore
            pass
        
        del self.socket
        self._handle_event(Event("disconnect", self.server, "", list(message)))

    def globops(self, text):
        """
        Send a GLOBOPS command
        """

        self.send_items(_GLOBOPS_STR, ":" + text)
    
    def info(self, server = ""):
        """
        Send INFO command
        """

        self.send_items(_INFO_STR, server)
    
    def invite(self, nick, channel):
        """
        Send an INVITE command
        """

        self.send_items(_INVITE_STR, server)
    
    def ison(self, nicks):
        """
        Send an ISON command
        """

        self.send_items(_ISON_STR, *tuple(nicks))
    
    def join(self, channel, key = ""):
        """
        Send a JOIN command
        """

        self.send_items(_JOIN_STR, channel, key)
    
    def kick(self, channel, nick, comment = ""):
        """
        Send a KICK command
        """

        self.send_items(_KICK_STR, channel, nick, comment and ':' + comment)
    
    def links(self, remote_server = "", server_mask = ""):
        """
        Send a LINKS command
        """

        self.send_items(_LINKS_STR, remote_server, server_mask)
    
    def list(self, channels = None, server = ""):
        """
        Send a LIST command
        """

        self.send_items(_LIST_STR, ','.join(always_iterable(channels)), server)
    
    def lusers(self, server = ""):
        """
        Send an LUSERS command
        """

        self.send_items(_LUSERS_STR, server)
    
    def mode(self, target, command):
        """
        Send a MODE command
        """

        self.send_items(_MODE_STR, target, command)
    
    def motd(self, server = ""):
        """
        Send an MOTD command
        """

        self.send_items(_MOTD_STR, server)
    
    def names(self, channels = None):
        """
        Send a NAMES command
        """

        self.send_items(_NAMES_STR, ','.join(always_iterable(channels)))

    def nick(self, new_nick):
        """
        Send a NICK command
        """

        self.send_items(_NICK_STR, new_nick)
    
    def notice(self, target, text):
        """
        Send a NOTICE command
        """

        # Should limit len(text) here!
        self.send_items(_NOTICE_STR, target, ':' + text)
    
    def oper(self, nick, password):
        """
        Send an OPER command
        """

        self.send_items(_OPER_STR, nick, password)
    
    def part(self, channels, message = ""):
        """
        Send a PART command
        """

        self.send_items(_PART_STR, ','.join(always_iterable(channels)), message)
    
    def pass_(self, password):
        """
        Send a PASS command
        """

        self.send_items(_PASS_STR, password)
    
    def ping(self, target, target2 = ""):
        """
        Send a PING command
        """

        self.send_items(_PING_STR, target, target2)
    
    def pong(self, target, target2 = ""):
        """
        Send a PONG command
        """

        self.send_items(_PONG_STR, target, target2)
    
    def privmsg(self, target, text):
        """
        Send a PRIVMSG command
        """

        self.send_items(_PRVMSG_STR, target, ':' + text)
    
    def privmsg_many(self, targets, text):
        """
        Send a PRIVMSG command to multiple targets
        """

        target = ','.join(targets)
        return self.privmsg(target, text)
    
    def quit(self, message = ""):
        """
        Send a QUIT command
        """

        # Many IRC servers don't use your quit message
        # unless you've been connected for >= 5mins
        self.send_items(_QUIT_STR, message and ':' + message)

    def _prep_message(self, string):
        # String should not contain any carriage returns
        # other than one added here
        if '\n' in string:
            raise InvalidCharacters("Carriage returns not allowed in privmsg(text)!")

        bytes = self.encode(string) + b'\r\n'
        # According to the RFC clients should not transmite >512 bytes
        if len(bytes) > 512:
            raise MessageTooLong("Messages limited to 512 bytes including CR/LF!")
        
        return bytes
    
    def send_items(self, *items):
        """
        Send all non-empty items, separated by spaces
        """

        self.send_raw(' '.join(filter(None, items)))
    
    def send_raw(self, string):
        """
        Send raw string to the server, padded with appropriate
        CR LF
        """

        if self.socket is None:
            raise ServerNotConnectedError("Not connected.")
        
        send = getattr(self.socket, "write", self.socket.send)
        try:
            sender(self._prep_message(string))
        except socket.error:
            # Ouch!
            self.disconnect("Connection reset by peer!")
        
    def squit(self, server, comment = ""):
        """
        Send an SQUIT command
        """

        self.send_items(_SQUIT_STR, server, comment and ':' + comment)
    
    def stats(self, statstype, server = ""):
        """
        Send a STATS command
        """

        self.send_items(_STATS_STR, statstype, server)
    
    def time(self, server = ""):
        """
        Send a TIME command
        """

        self.send_items(_TIME_STR, server)
    
    def topic(self, channel, new_topic = None):
        """
        Send a TOPIC command
        """

        self.send_items(_TOPIC_STR, channel, new_topic and ':' + new_topic)
    
    def trace(self, target = ""):
        """
        Send a TRACE command
        """

        self.send_items(_TRACE_STR, target)
    
    def user(self, username, realname):
        """
        Send a USER command
        """

        cmd = "USER {username} 0 * :{realname}".format(**locals())
        self.send_raw(cmd)
    
    def userhost(self, nicks):
        """
        Send a USERHOST command
        """

        self.send_items(_USRHST_STR, ",".join(nicks))
    
    def users(self, server = ""):
        """
        Send a USERS command
        """

        self.send_items(_USERS_STR, server)
    
    def version(self, server = ""):
        """
        Send a VERSION command
        """

        self.send_items(_VERSION_STR, server)
    
    def wallops(self, text):
        """
        Send a WALLOPS command
        """

        self.send_items(_WALLOPS_STR, ":" + text)
    
    def who(self, target = "", op = ""):
        """
        Send a WHO command
        """

        self.send_items(_WHO_STR, target, op and "o")
    
    def whois(self, targets):
        """
        Send a WHOIS command
        """

        self.send_items(_WHOIS_STR, ",".join(always_iterable(targets)))
    
    def whowas(self, nick, max = "", server = ""):
        """
        Send a WHOWAS command
        """

        self.send_items(_WHOWAS_STR, nick, max, server)
    
    def set_rate_limit(self, frequency):
        """
        Set 'frequency' limit (msgs per second) for this
        connection. Faster attempts will block
        """

        self.send_raw = Throttler(self.send_raw, frequency)
    
    def set_keepalive(self, interval):
        """
        Set a keepalive to occur every 'interval' on this
        connection
        """

        pinger = functools.partial(self.ping, "keep-alive")
        self.reactor.scheduler.execute_every(period = interval, func = pinger)

class PrioritizedHandler( collections.namedtuple('Base', ('priority', 'callback')) ):
    """
    Custom class to hold handlers and ensure they're sorted
    by supplied priority.
    """

    def __lt__(self, other):
        """
        When sorting prioritized handlers, onle use the priority
        """
        return self.priority < other.priority

class Reactor:
    """
    Processes events from one or more IRC server connections.
    """

    _scheduler_class = schedule.DefaultScheduler
    _connection_class = ServerConnection

    def __do_nothing(*args, **kwargs):
        # Surprise, surprise, here we do nothing!
        pass

    def __init__(self, on_connect = __do_nothing, on_disconnect = __do_nothing):
        """
        on_connect = optional callback invoked when socket connected
        on_disconnect = optional callback invoked when socket disconnected
        """

        self._on_connect = on_connect
        self._on_disconnect = on_disconnect

        sched = self.scheduler_class()
        assert isinstance(sched, schedule.IScheduler)
        self.scheduler = sched

        self.connections = list()
        self.handlers = dict()
        # Shared lists / dicts changes need to be thread safe
        self.mutex = threading.RLock()

        self.add_global_handler("ping", _ping_ponger, -42)
    
    def server(self):
        """
        Creates and returns ServerConnection object
        """
        
        conn = self.connection_class(self)
        with self.mutex: self.connections.append(conn)
        return conn
    
    def process_data(self, sockets):
        """
        Called when there's more data to read on a connection socket.
        sockets = list of socket objects
        """

        with self.mutex:
            for sock, conn in itertools.product(sockets, self.connections):
                if sock == conn.socket: conn.process_data()
    
    def process_timeout(self):
        """
        Called when a timeout notification is due
        """

        with self.mutex: self.scheduler.run_pending()

    @property
    def sockets(self):
        with self.mutex:
            return [
                conn.socket
                for conn in self.connections
                if conn is not None
                and conn.socket is not None
            ]
    
    def process_once(self, timeout = 0):
        """
        Process data from connections, once.

        Should be called periodically to check and process incoming
        data, if there is any.
        """

        sockets = self.sockets
        if sockets:
            s_in, s_out, s_err = select.select(sockets, list(), list(), timeout)
            self.process_data(s_in)
        else:
            time.sleep(timeout)
        self.process_timeout()
    
    def process_forever(self, timeout = 0.2):
        """
        Run infinite loop, processing data from connections.
        Repeatedly calls process_once
        """
        one = functools.partial(self.process_once, timeout = timeout)
        # Should specifically NOT mutex locked otherwise no other
        # thread would be able to change state of shared lists/dicts
        consume(infinite_call(one))
    
    def disconnect_all(self, message = ""):
        """
        Disconnects all connections
        """

        with self.mutex:
            for conn in self.connections:
                conn.disconnect(message)
    
    def add_global_handler(self, event, handler, priority = 0):
        """
        Adds a global handler function for specific event type.

        Supplied function called whenever specified event is triggered on any of the
        connections.

        Handler functions called in priority order (lower no. --> higher priority).
        If handler function returns "NO MORE" (_STOP_STR), no more handlers will be called
        """

        handler = PrioritizedHandler(priority, handler)
        with self.mutex:
            event_handlers = self.handlers.setdefault(event, list())
            bisect.insort(event_handlers, handler)
        
    def remove_global_handler(self, event, handler):
        """
        Removes global handler function.
        Returns --> 1 = success
                    0 = otherwise
        """

        with self.mutex:
            if event not in self.handlers: return 0

            for h in self.handlers[event]:
                if handler == h.callback:
                    self.handlers[event].remove(h)
        return 1
    
    def _handle_event(self, connection, event):
        """
        Handle an Event incoming on ServerConnection connection
        """

        with self.mutex:
            matching_handlers = sorted(
                self.handlers.get("all_events", list())
                +
                self.handlers.get(event.type, [])
            )

            for handler in matching_handlers:
                result = handler.callback(connection, event)
                if result == _STOP_STR:
                    return

class IRCError(Exception):
    "An IRC exception"

class InvalidCharacters(ValueError):
    "Invalid characters were encountered in the message"

class MessageTooLong(ValueError):
    "Message is too long"

class ServerConnectionError(IRCError):
    pass

class ServerNotConnectedError(ServerConnectionError):
    pass