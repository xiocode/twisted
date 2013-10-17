# -*- test-case-name: twisted.python.test.test_logger -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Ring buffer log observer.
"""

__all__ = [
    "RingBufferLogObserver",
]

from collections import deque

from zope.interface import implementer

from twisted.python.logger._observer import ILogObserver



@implementer(ILogObserver)
class RingBufferLogObserver(object):
    """
    L{ILogObserver} that stores events in a ring buffer of a fixed
    size::

        >>> from twisted.python.logger import RingBufferLogObserver
        >>> observer = RingBufferLogObserver(5)
        >>> for n in range(10):
        ...   observer({"n":n})
        ...
        >>> len(observer)
        5
        >>> tuple(observer)
        ({'n': 5}, {'n': 6}, {'n': 7}, {'n': 8}, {'n': 9})
        >>> observer.clear()
        >>> tuple(observer)
        ()
    """

    def __init__(self, size=None):
        """
        @param size: the maximum number of events to buffer.  If C{None}, the
            buffer is unbounded.
        """
        self._buffer = deque(maxlen=size)


    def __call__(self, event):
        self._buffer.append(event)


    def __iter__(self):
        """
        Iterate over the buffered events.
        """
        return iter(self._buffer)


    def __len__(self):
        """
        @return: the number of events in the buffer.
        """
        return len(self._buffer)


    def clear(self):
        """
        Clear the event buffer.
        """
        self._buffer.clear()
