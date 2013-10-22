# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Test cases for L{twisted.python.logger._file}.
"""

from io import StringIO
from time import mktime

try:
    from time import tzset
    # We should upgrade to a version of pyflakes that does not require this.
    tzset
except ImportError:
    tzset = None

from zope.interface.verify import verifyObject, BrokenMethodImplementation

from twisted.trial import unittest
from twisted.trial.unittest import SkipTest

from twisted.python.logger._observer import ILogObserver
from twisted.python.logger._file import textFileLogObserver
from twisted.python.logger.test.test_format import Unformattable
from twisted.python.logger.test.test_format import addTZCleanup, setTZ



class FileLogObserverTests(unittest.TestCase):
    """
    Tests for L{FileLogObserver}.
    """
    DEFAULT_TIMESTAMP = u"-"
    DEFAULT_SYSTEM = u"[-#-]"

    def buildOutput(self, timeStamp, system, text, encoding):
        """
        Build an expected output string from components.

        @param timeStamp: time stamp text
        @type timeStamp: unicode

        @param system: a system name
        @type system: unicode

        @param text: a text message
        @type text: unicode

        @param encoding: an encoding
        @type encoding: str

        @return: a formatted output string that I{should} match the format
            emitted by L{FileLogObserver}.
        @rtype: L{unicode}
        """
        return (u" ".join((timeStamp, system, text)) + u"\n")


    def buildDefaultOutput(self, text, encoding="utf-8"):
        """
        Build an expected output string with the default time stamp
        and system.

        @param text: a text message
        @type text: unicode

        @param encoding: an encoding
        @type encoding: str

        @return: a L{FileLogObserver}-formatted output string.
        @rtype: bytes
        """
        return self.buildOutput(
            self.DEFAULT_TIMESTAMP,
            self.DEFAULT_SYSTEM,
            text,
            encoding
        )


    def test_interface(self):
        """
        L{FileLogObserver} is an L{ILogObserver}.
        """
        try:
            fileHandle = StringIO()
            observer = textFileLogObserver(fileHandle)
            try:
                verifyObject(ILogObserver, observer)
            except BrokenMethodImplementation as e:
                self.fail(e)
        finally:
            fileHandle.close()


    def _testObserver(
        self, logTime, logFormat,
        observerKwargs, expectedOutput
    ):
        """
        Default time stamp format is RFC 3339

        @param logTime: a time stamp
        @type logTime: int

        @param logFormat: a format string
        @type logFormat: unicode

        @param observerKwargs: keyword arguments for constructing the observer
        @type observerKwargs: dict

        @param expectedOutput: the expected output from the observer
        @type expectedOutput: bytes
        """
        event = dict(log_time=logTime, log_format=logFormat)
        fileHandle = StringIO()
        try:
            observer = textFileLogObserver(fileHandle, **observerKwargs)
            observer(event)
            output = fileHandle.getvalue()
            self.assertEquals(
                output, expectedOutput,
                "{0!r} != {1!r}".format(expectedOutput, output)
            )
        finally:
            fileHandle.close()


    def test_defaultTimeStamp(self):
        """
        Default time stamp format is RFC 3339 and offset respects the timezone
        as set by the standard C{TZ} environment variable and L{tzset} API.
        """
        if tzset is None:
            raise SkipTest(
                "Platform cannot change timezone; unable to verify offsets."
            )

        # We only test "UTC+00" here, and rely on formatTime's tests for others

        addTZCleanup(self)
        setTZ("UTC+00")

        # On some rare platforms (FreeBSD 8?  I was not able to reproduce
        # on FreeBSD 9) 'mktime' seems to always fail once tzset() has been
        # called more than once in a process lifetime.  I think this is
        # just a platform bug, so let's work around it.  -glyph
        try:
            localDST = mktime((2006, 6, 30, 0, 0, 0, 4, 181, 1))
        except OverflowError:
            raise SkipTest(
                "Platform cannot construct time zone for 'UTC+00'"
            )

        self._testObserver(
            localDST, u"XYZZY",
            dict(),
            self.buildOutput(
                u"2006-06-30T00:00:00+0000", self.DEFAULT_SYSTEM,
                u"XYZZY", "utf-8",
            ),
        )


    def test_emptyFormat(self):
        """
        Empty format == empty log output == nothing to log.
        """
        t = mktime((2013, 9, 24, 11, 40, 47, 1, 267, 1))
        self._testObserver(t, u"", dict(), u"")


    def test_noTimeFormat(self):
        """
        Time format is None == no time stamp.
        """
        t = mktime((2013, 9, 24, 11, 40, 47, 1, 267, 1))
        self._testObserver(
            t, u"XYZZY",
            dict(timeFormat=None),
            self.buildDefaultOutput(u"XYZZY"),
        )


    def test_alternateTimeFormat(self):
        """
        Alternate time format in output.
        """
        t = mktime((2013, 9, 24, 11, 40, 47, 1, 267, 1))
        self._testObserver(
            t, u"XYZZY",
            dict(timeFormat="%Y/%W"),
            self.buildOutput(
                u"2013/38",
                self.DEFAULT_SYSTEM,
                u"XYZZY",
                "utf-8",
            )
        )


    def test_timeFormat_f(self):
        """
        "%f" supported in time format.
        """
        self._testObserver(
            1.23456, u"XYZZY",
            dict(timeFormat="%f"),
            self.buildOutput(
                u"234560",
                self.DEFAULT_SYSTEM,
                u"XYZZY",
                "utf-8",
            ),
        )


    def test_noEventTime(self):
        """
        Event lacks a time == no time stamp.
        """
        self._testObserver(
            None, u"XYZZY",
            dict(),
            self.buildDefaultOutput(u"XYZZY"),
        )


    def test_multiLine(self):
        """
        Additional lines are indented.
        """
        self._testObserver(
            None, u'XYZZY\nA hollow voice says:\n"Plugh"',
            dict(),
            self.buildDefaultOutput(
                u'XYZZY\n\tA hollow voice says:\n\t"Plugh"'
            ),
        )


    def test_unformattableSystem(self):
        """
        System string is not formattable.
        """
        event = dict(
            log_time=None,
            log_format=u"XYZZY",
            log_system=Unformattable(),
        )
        fileHandle = StringIO()
        try:
            observer = textFileLogObserver(fileHandle)
            observer(event)
            output = fileHandle.getvalue()
            expectedOutput = u"- [UNFORMATTABLE] XYZZY\n"
            self.assertEquals(
                output, expectedOutput,
                "{0!r} != {1!r}".format(expectedOutput, output)
            )
        finally:
            fileHandle.close()
