import re
import textwrap
from collections import deque
from itertools import islice

"""
START:
From erikrose's more-itertools/recipes.py
Github - https://github.com/erikrose/more-itertools/blob/master/more_itertools/recipes.py
"""
def consume(iterator, n=None):
    # Use functions that consume iterators at C speed.
    if n is None:
        # feed the entire iterator into a zero-length deque
        deque(iterator, maxlen=0)
    else:
        # advance to the empty slice starting at position n
        next(islice(iterator, n, n), None)
"""
END
"""

"""
START:
From jaraco's stream/buffer.py
Github - https://github.com/jaraco/jaraco.stream/blob/master/jaraco/stream/buffer.py
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
        msg = textwrap.dedent("""
            Unknown encoding encountered. See 'Decoding Input'
            in https://pypi.python.org/pypi/irc for details.
            """)
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