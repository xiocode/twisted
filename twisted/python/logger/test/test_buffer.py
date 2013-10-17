# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Test cases for L{twisted.python.logger._buffer}.
"""

from zope.interface.verify import verifyObject, BrokenMethodImplementation

from twisted.trial import unittest

from twisted.python.logger._observer import ILogObserver
from twisted.python.logger._buffer import RingBufferLogObserver



class RingBufferLogObserverTests(unittest.TestCase):
    """
    Tests for L{RingBufferLogObserver}.
    """

    def test_interface(self):
        """
        L{RingBufferLogObserver} is an L{ILogObserver}.
        """
        observer = RingBufferLogObserver(0)
        try:
            verifyObject(ILogObserver, observer)
        except BrokenMethodImplementation as e:
            self.fail(e)


    def test_buffering(self):
        """
        Events are buffered in order.
        """
        size = 4
        events = [dict(n=n) for n in range(size//2)]
        observer = RingBufferLogObserver(size)

        for event in events:
            observer(event)
        self.assertEquals(events, list(observer))
        self.assertEquals(len(events), len(observer))


    def test_size(self):
        """
        Size of ring buffer is honored.
        """
        size = 4
        events = [dict(n=n) for n in range(size*2)]
        observer = RingBufferLogObserver(size)

        for event in events:
            observer(event)
        self.assertEquals(events[-size:], list(observer))
        self.assertEquals(size, len(observer))


    def test_clear(self):
        """
        Events are cleared by C{observer.clear()}.
        """
        size = 4
        events = [dict(n=n) for n in range(size//2)]
        observer = RingBufferLogObserver(size)

        for event in events:
            observer(event)
        self.assertEquals(len(events), len(observer))
        observer.clear()
        self.assertEquals(0, len(observer))
        self.assertEquals([], list(observer))
