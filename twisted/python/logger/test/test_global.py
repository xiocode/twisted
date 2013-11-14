# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Test cases for L{twisted.python.logger._global}.
"""

import io

from twisted.trial import unittest

from .._observer import LogPublisher
from twisted.python.logger import Logger
from .._global import LogBeginner
from .._global import MORE_THAN_ONCE_WARNING
from twisted.python.logger import LogLevel
from ..test.test_stdlib import nextLine



class LogBeginnerTests(unittest.TestCase):
    """
    Tests for L{LogBeginner}.
    """

    def setUp(self):
        self.publisher = LogPublisher()
        self.errorStream = io.StringIO()
        self.buffer = LogBeginner(self.publisher, self.errorStream)


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
        When invoked twice, L{LogBeginner.beginLoggingTo} will emit a log
        message warning the user that they previously began logging, and add
        the new log observers.
        """
        events1 = []
        events2 = []
        self.publisher(dict(event="prebuffer"))
        firstFilename, firstLine = nextLine()
        self.buffer.beginLoggingTo([events1.append])
        self.publisher(dict(event="postbuffer"))
        secondFilename, secondLine = nextLine()
        self.buffer.beginLoggingTo([events2.append])
        self.publisher(dict(event="postwarn"))
        warning = dict(log_format=MORE_THAN_ONCE_WARNING,
                       log_level=LogLevel.warn,
                       fileNow=secondFilename, lineNow=secondLine,
                       fileThen=firstFilename, lineThen=firstLine)

        def compareEvents(actualEvents, expectedEvents):
            if len(actualEvents) != len(expectedEvents):
                self.assertEquals(actualEvents, expectedEvents)
            allMergedKeys = set()
            for event in expectedEvents:
                allMergedKeys |= set(event.keys())
            def simplify(event):
                copy = event.copy()
                for key in event.keys():
                    if key not in allMergedKeys:
                        copy.pop(key)
                return copy
            simplifiedActual = [simplify(event) for event in actualEvents]
            self.assertEquals(simplifiedActual, expectedEvents)

        compareEvents(events1,
                      [dict(event="prebuffer"), dict(event="postbuffer"),
                       warning, dict(event="postwarn")])
        compareEvents(events2, [warning, dict(event="postwarn")])


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
