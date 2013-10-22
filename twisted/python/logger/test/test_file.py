# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Test cases for L{twisted.python.logger._file}.
"""

from os import environ
from io import StringIO
from time import mktime
from datetime import timedelta as TimeDelta

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
from twisted.python.logger._format import FixedOffsetTimeZone
from twisted.python.logger.test.test_format import Unformattable



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

        def setTZ(name):
            if name is None:
                del environ["TZ"]
            else:
                environ["TZ"] = name
            tzset()

        def testObserver(timeInt, timeText):
            self._testObserver(
                timeInt, u"XYZZY",
                dict(),
                self.buildOutput(
                    timeText, self.DEFAULT_SYSTEM,
                    u"XYZZY", "utf-8",
                ),
            )

        def testForTimeZone(name, expectedDST, expectedSTD):
            setTZ(name)

            # On some rare platforms (FreeBSD 8?  I was not able to reproduce
            # on FreeBSD 9) 'mktime' seems to always fail once tzset() has been
            # called more than once in a process lifetime.  I think this is
            # just a platform bug, so let's work around it.  -glyph
            try:
                localDST = mktime((2006, 6, 30, 0, 0, 0, 4, 181, 1))
            except OverflowError:
                raise SkipTest(
                    "Platform cannot construct time zone for {0!r}"
                    .format(name)
                )
            localSTD = mktime((2007, 1, 31, 0, 0, 0, 2,  31, 0))

            testObserver(localDST, expectedDST)
            testObserver(localSTD, expectedSTD)

        tzIn = environ.get("TZ", None)

        @self.addCleanup
        def resetTZ():
            setTZ(tzIn)

        # UTC
        testForTimeZone(
            "UTC+00",
            u"2006-06-30T00:00:00+0000",
            u"2007-01-31T00:00:00+0000",
        )

        # West of UTC
        testForTimeZone(
            "EST+05EDT,M4.1.0,M10.5.0",
            u"2006-06-30T00:00:00-0400",
            u"2007-01-31T00:00:00-0500",
        )

        # East of UTC
        testForTimeZone(
            "CEST-01CEDT,M4.1.0,M10.5.0",
            u"2006-06-30T00:00:00+0200",
            u"2007-01-31T00:00:00+0100",
        )

        # No DST
        testForTimeZone(
            "CST+06",
            u"2006-06-30T00:00:00-0600",
            u"2007-01-31T00:00:00-0600",
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



class FixedOffsetTimeZoneTests(unittest.TestCase):
    """
    Tests for L{FixedOffsetTimeZone}.
    """

    def test_tzinfo(self):
        """
        Test that timezone attributes respect the timezone as set by the
        standard C{TZ} environment variable and L{tzset} API.
        """
        if tzset is None:
            raise SkipTest(
                "Platform cannot change timezone; unable to verify offsets."
            )

        def setTZ(name):
            if name is None:
                del environ["TZ"]
            else:
                environ["TZ"] = name
            tzset()

        def testForTimeZone(name, expectedOffsetDST, expectedOffsetSTD):
            setTZ(name)

            # On some rare platforms (FreeBSD 8?  I was not able to reproduce
            # on FreeBSD 9) 'mktime' seems to always fail once tzset() has been
            # called more than once in a process lifetime.  I think this is
            # just a platform bug, so let's work around it.  -glyph
            try:
                localDST = mktime((2006, 6, 30, 0, 0, 0, 4, 181, 1))
            except OverflowError:
                raise SkipTest(
                    "Platform cannot construct time zone for {0!r}"
                    .format(name)
                )
            localSTD = mktime((2007, 1, 31, 0, 0, 0, 2,  31, 0))

            tzDST = FixedOffsetTimeZone.fromTimeStamp(localDST)
            tzSTD = FixedOffsetTimeZone.fromTimeStamp(localSTD)

            self.assertEquals(
                tzDST.tzname(localDST),
                "UTC{0}".format(expectedOffsetDST)
            )
            self.assertEquals(
                tzSTD.tzname(localSTD),
                "UTC{0}".format(expectedOffsetSTD)
            )

            self.assertEquals(tzDST.dst(localDST), TimeDelta(0))
            self.assertEquals(tzSTD.dst(localSTD), TimeDelta(0))

            def timeDeltaFromOffset(offset):
                assert len(offset) == 5

                sign = offset[0]
                hours = int(offset[1:3])
                minutes = int(offset[3:5])

                if sign == "-":
                    hours = -hours
                    minutes = -minutes
                else:
                    assert sign == "+"

                return TimeDelta(hours=hours, minutes=minutes)

            self.assertEquals(
                tzDST.utcoffset(localDST),
                timeDeltaFromOffset(expectedOffsetDST)
            )
            self.assertEquals(
                tzSTD.utcoffset(localSTD),
                timeDeltaFromOffset(expectedOffsetSTD)
            )

        tzIn = environ.get("TZ", None)

        @self.addCleanup
        def resetTZ():
            setTZ(tzIn)

        # UTC
        testForTimeZone("UTC+00", "+0000", "+0000")
        # West of UTC
        testForTimeZone("EST+05EDT,M4.1.0,M10.5.0", "-0400", "-0500")
        # East of UTC
        testForTimeZone("CEST-01CEDT,M4.1.0,M10.5.0", "+0200", "+0100")
        # No DST
        testForTimeZone("CST+06", "-0600", "-0600")
