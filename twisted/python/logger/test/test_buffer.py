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

        outEvents = []
        observer.replayTo(outEvents.append)
        self.assertEquals(events, outEvents)


    def test_size(self):
        """
        When more events than a L{RingBufferLogObserver}'s maximum size are
        buffered, older events will be dropped.
        """
        size = 4
        events = [dict(n=n) for n in range(size*2)]
        observer = RingBufferLogObserver(size)

        for event in events:
            observer(event)
        outEvents = []
        observer.replayTo(outEvents.append)
        self.assertEquals(events[-size:], outEvents)
