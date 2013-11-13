# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Test cases for L{twisted.python.logger._global}.
"""

import io

from twisted.trial import unittest

from twisted.python.logger._observer import LogPublisher
from twisted.python.logger import Logger
from twisted.python.logger._global import LogStartupBuffer



class LogStartupBufferTests(unittest.TestCase):
    """
    Tests for L{LogStartupBuffer}.
    """

    def setUp(self):
        self.publisher = LogPublisher()
        self.errorStream = io.StringIO()
        self.buffer = LogStartupBuffer(self.publisher, self.errorStream)


    def test_beginLoggingTo_addObservers(self):
        """
        Test that C{beginLoggingTo()} adds observers.
        """
        event = dict(foo=1, bar=2)

        events1 = []
        events2 = []

        o1 = lambda e: events1.append(e)
        o2 = lambda e: events2.append(e)

        self.buffer.beginLoggingTo((o1, o2))
        self.publisher(event)

        self.assertEquals([event], events1)
        self.assertEquals([event], events2)


    def test_beginLoggingTo_bufferedEvents(self):
        """
        Test that events are buffered until C{beginLoggingTo()} is
        called.
        """
        event = dict(foo=1, bar=2)

        events1 = []
        events2 = []

        o1 = lambda e: events1.append(e)
        o2 = lambda e: events2.append(e)

        self.publisher(event)  # Before beginLoggingTo; this is buffered
        self.buffer.beginLoggingTo((o1, o2))

        self.assertEquals([event], events1)
        self.assertEquals([event], events2)


    def test_beginLoggingTo_twice(self):
        """
        Test that C{beginLoggingTo()} complains when called twice.
        """
        self.buffer.beginLoggingTo([])

        self.assertRaises(
            AssertionError,
            self.buffer.beginLoggingTo, []
        )


    def test_criticalLogging(self):
        """
        Critical messages will be written as text to the error stream.
        """
        log = Logger(observer=self.publisher)
        log.info('ignore this')
        log.critical('a critical {message}', message="message")
        self.assertEquals(self.errorStream.getvalue(), u'a critical message\n')


    def test_criticalLoggingStops(self):
        """
        Once logging has begun with C{beginLoggingTo}, critical messages are no
        longer written to the output stream.
        """
        log = Logger(observer=self.publisher)
        self.buffer.beginLoggingTo(())
        log.critical("another critical message")
        self.assertEquals(self.errorStream.getvalue(), u'')
