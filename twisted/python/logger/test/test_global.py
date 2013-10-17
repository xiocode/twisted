# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Test cases for L{twisted.python.logger._global}.
"""

from zope.interface.verify import verifyObject, BrokenMethodImplementation

from twisted.trial import unittest

from twisted.python.logger._observer import ILogObserver
from twisted.python.logger._global import GlobalLogPublisher



class GlobalLogPublisherTests(unittest.TestCase):
    """
    Tests for L{GlobalLogPublisher}.
    """

    def test_interface(self):
        """
        L{GlobalLogPublisher} is an L{ILogObserver}.
        """
        publisher = GlobalLogPublisher()
        try:
            verifyObject(ILogObserver, publisher)
        except BrokenMethodImplementation as e:
            self.fail(e)


    def test_startLoggingWithObservers_addObservers(self):
        """
        Test that C{startLoggingWithObservers()} adds observers.
        """
        publisher = GlobalLogPublisher()

        event = dict(foo=1, bar=2)

        events1 = []
        events2 = []

        o1 = lambda e: events1.append(e)
        o2 = lambda e: events2.append(e)

        publisher.startLoggingWithObservers((o1, o2))
        publisher(event)

        self.assertEquals([event], events1)
        self.assertEquals([event], events2)


    def test_startLoggingWithObservers_bufferedEvents(self):
        """
        Test that events are buffered until C{startLoggingWithObservers()} is
        called.
        """
        publisher = GlobalLogPublisher()

        event = dict(foo=1, bar=2)

        events1 = []
        events2 = []

        o1 = lambda e: events1.append(e)
        o2 = lambda e: events2.append(e)

        publisher(event)  # Before startLoggingWithObservers; this is buffered
        publisher.startLoggingWithObservers((o1, o2))

        self.assertEquals([event], events1)
        self.assertEquals([event], events2)


    def test_startLoggingWithObservers_twice(self):
        """
        Test that C{startLoggingWithObservers()} complains when called twice.
        """
        publisher = GlobalLogPublisher()

        publisher.startLoggingWithObservers(())

        self.assertRaises(
            AssertionError,
            publisher.startLoggingWithObservers, ()
        )
