import abc
import bisect
import re
import datetime
import collections
import numbers
import time
import textwrap
import functools
import itertools

# TODO: figure this shit section out!!!
"""
START:
From Stuart Bishop's pytz
Github - https://github.com/stub42/pytz
"""
class BaseTzInfo(datetime.tzinfo):
    # Overridden in subclass
    _utcoffset = None
    _tzname = None
    zone = None

    def __str__(self):
        return self.zone

class UTC(BaseTzInfo):
    """UTC
    Optimized UTC implementation. It unpickles using the single module global
    instance defined beneath this class declaration.
    """
    zone = "UTC"

    _utcoffset = datetime.timedelta(0)
    _dst = datetime.timedelta(0)
    _tzname = zone

    def fromutc(self, dt):
        if dt.tzinfo is None:
            return self.localize(dt)
        return super(utc.__class__, self).fromutc(dt)

    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return datetime.timedelta(0)

    def __reduce__(self):
        return _UTC, ()

    def localize(self, dt, is_dst=False):
        '''Convert naive time to local time'''
        if dt.tzinfo is not None:
            raise ValueError('Not naive datetime (tzinfo is already set)')
        return dt.replace(tzinfo=self)

    def normalize(self, dt, is_dst=False):
        '''Correct the timezone information on the given datetime'''
        if dt.tzinfo is self:
            return dt
        if dt.tzinfo is None:
            raise ValueError('Naive time - no tzinfo set')
        return dt.astimezone(self)

    def __repr__(self):
        return "<UTC>"

    def __str__(self):
        return "UTC"

UTC = utc = UTC() # UTC is a singleton

def _UTC():
    """
    Factory function for utc unpickling
    """

    return utc
_UTC.__safe_for_unpickling__ = True
"""
END
"""

"""
START:
From jaraco's functools
Github - https://github.com/jaraco/jaraco.functools
"""
def save_method_args(method):
    args_and_kwargs = collections.namedtuple("args_and_kwargs", "args kwargs")

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        attr_name = "_saved" + method.__name__
        attr = args_and_kwargs(args, kwargs)
        setattr(self, attr_name, attr)
        return method(self, *args, **kwargs)
    
    return wrapper

def first_invoke(func1, func2):
    def wrapper(*args, **kwargs):
        func1()
        return func2(*args, **kwargs)
    return wrapper

class Throttler:
    """
    Rate-limit a function / other callable
    """
    
    def __init__(self, func, max_rate = float("Inf")):
        if isinstance(func, Throttler):
            func = func.func
        
        self.func = func
        self.max_rate = max_rate
        self.reset()
    
    def reset(self):
        self.last_called = 0
    
    def _wait(self):
        "ensure at least 1/max_rate seconds from last call"
        elapsed = time.time() - self.last_called
        must_wait = 1 / self.max_rate - elapsed
        time.sleep(max(0, must_wait))
        self.last_called = time.time()

    def __call__(self, *args, **kwargs):
        self._wait()
        return self.func(*args, **kwargs)
    
    def __get__(self, obj, type = None):
        return first_invoke(self._wait, functools.partial(self.func, obj))
"""
END
"""

"""
START:
From jaraco's itertools
Github - https://github.com/jaraco/jaraco.itertools
"""
def always_iterable(item):
    return (
        (item, )
        if isinstance(item, collections.Mapping)
        else _always_iterable(item)
    )

def infinite_call(f):
	return (f() for _ in itertools.repeat(None))

def infiniteCall(f, *args):
    return infinite_call(functools.partial(f, *args))
"""
END
"""

"""
START:
From erikrose's more-itertools
Github - https://github.com/erikrose/more-itertools
"""
def consume(iterator, n = None):
    # Use functions that consume iterators at C speed.
    if n is None:
        # feed the entire iterator into a zero-length deque
        collections.deque(iterator, maxlen = 0)
    else:
        # advance to the empty slice starting at position n
        next(itertools.islice(iterator, n, n), None)

def _always_iterable(obj, base_type = (str, bytes)):
    if obj is None:
        return iter(())
    
    if (base_type is not None) and isinstance(obj, base_type):
        return iter((obj, ))
    
    try:
        iter(obj)
    except TypeError:
        return iter((obj, ))
"""
END
"""

"""
START:
From jaraco's stream/buffer.py
Github - https://github.com/jaraco/jaraco.stream
"""
class LineBuffer(object):
    line_sep_exp = re.compile(b'\r?\n')

    def __init__(self):
        self.buffer = b''

    def feed(self, bytes):
        self.buffer += bytes

    def lines(self):
        lines = self.line_sep_exp.split(self.buffer)
        # save the last, unfinished, possibly empty line
        self.buffer = lines.pop()
        return iter(lines)

    def __iter__(self):
        return self.lines()

    def __len__(self):
        return len(self.buffer)


class DecodingLineBuffer(LineBuffer):
    encoding = 'utf-8'
    errors = 'strict'

    def lines(self):
        for line in super(DecodingLineBuffer, self).lines():
            try:
                yield line.decode(self.encoding, self.errors)
            except UnicodeDecodeError:
                self.handle_exception()

    def handle_exception(self):
        # msg = textwrap.dedent("""
        #     Unknown encoding encountered. See 'Decoding Input'
        #     in https://pypi.python.org/pypi/irc for details.
        #     """)
        raise


class LenientDecodingLineBuffer(LineBuffer):
    def lines(self):
        for line in super(LenientDecodingLineBuffer, self).lines():
            try:
                yield line.decode('utf-8', 'strict')
            except UnicodeDecodeError:
                yield line.decode('latin-1')
"""
END
"""

"""
START:
From jaraco's tempora/schedule.py
Github - https://github.com/jaraco/tempora
"""
def now():
    """
    Return current timezone-aware datetime
    """

    return datetime.datetime.utcnow().replace(tzinfo = utc)

def from_timestamp(ts):
    """
    Converts numeric --> location aware timestamp
    """

    return datetime.datetime.utcfromtimestamp(ts).replace(tzinfo = utc)

class DelayedCommand(datetime.datetime):
    """
    Command to be executed after some delay (seconds or timedelta)
    """

    @classmethod
    def from_datetime(cls, other):
        return cls(
            other.year, other.month, other.day, other.hour,
            other.minute, other.second, other.microsecond,
            other.tzinfo,
        )
    
    @classmethod
    def after(cls, delay, target):
        if not isinstance(delay, datetime.timedelta):
            delay = datetime.timedelta(seconds = delay)
        
        due_time = now() + delay
        cmd = cls.from_datetime(due_time)
        cmd.delay = delay
        cmd.target = target
        return cmd
    
    @staticmethod
    def _from_timestamp(input):
        if not isinstance(input, numbers.Real):
            return input
        return from_timestamp(input)
    
    @classmethod
    def at_time(cls, at, target):
        at = cls._from_timestamp(at)
        cmd = cls.from_datetime(at)
        cmd.delay = at - now()
        cmd.target = target
        return cmd
    
    def due(self):
        return now() >= self

class PeriodicCommand(DelayedCommand):
    """
    Like a delayed command, but except it to run every delay
    """

    def _next_time(self):
        return self._localize(self + self.delay)
    
    @staticmethod
    def _localize(dt):
        try:
            tz = dt.tzinfo
            return tz.localize(dt.replace(tzinfo = None))
        except AttributeError:
            return dt
    
    def next(self):
        cmd = self.__class__.from_datetime(self._next_time())
        cmd.delay = self.delay
        cmd.target = self.target
        return cmd
    
    def __setattr__(self, key, value):
        if key == "delay" and not value > datetime.timedelta():
            raise ValueError("A PeriodicCommand must have >0 delay.")
        super(PeriodicCommand, self).__setattr__(key, value)

class Scheduler:
    """
    Rudimentary abstract scheduler accepting DelayedCommands
    and dispatching them on schedule
    """

    def __init__(self):
        self.queue = list()
    
    def add(self, command):
        assert isinstance(command, DelayedCommand)
        bisect.insort(self.queue, command)
    
    def run_pending(self):
        while self.queue:
            command = self.queue[0]
            if not command.due():
                break
            
            self.run(command)
            if isinstance(command, PeriodicCommand):
                self.add(command.next())
            
            del self.queue[0]
    
    @abc.abstractmethod
    def run(self, command):
        """
        Run the command
        """

class InvokeScheduler(Scheduler):
    def run(self, command):
        command.target()
"""
END
"""

"""
START:
From benjaminp's Six
Github - https://github.com/benjaminp/six
"""
def add_metaclass(metaclass):
    """
    Class decorator for creating a class with a metaclass
    """
    def wrapper(cls):
        orig_vars = cls.__dict__.copy()
        slots = orig_vars.get("__slots__")
        if slots is not None:
            if isinstance(slots, str):
                slots = list(slots)
            for slots_var in slots:
                orig_vars.pop(slots_var)
        orig_vars.pop("__dict__", None)
        orig_vars.pop("__weakref__", None)
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    
    return wrapper
"""
END
"""