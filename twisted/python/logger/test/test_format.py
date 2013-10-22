# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Test cases for L{twisted.python.logger._format}.
"""

from os import environ
from itertools import count
import json
from time import mktime
from datetime import timedelta as TimeDelta

try:
    from time import tzset
    # We should upgrade to a version of pyflakes that does not require this.
    tzset
except ImportError:
    tzset = None

from twisted.trial import unittest
from twisted.trial.unittest import SkipTest

from twisted.python.compat import _PY3, unicode
from twisted.python.logger._format import formatEvent
from twisted.python.logger._format import formatUnformattableEvent
from twisted.python.logger._format import flattenEvent
from twisted.python.logger._format import flatKey
from twisted.python.logger._format import formatTime
from twisted.python.logger._format import formatWithCall
from twisted.python.logger._format import theFormatter
from twisted.python.logger._format import FixedOffsetTimeZone



class FormattingTests(unittest.TestCase):
    """
    Tests for basic event formatting functions.
    """

    def test_formatEvent(self):
        """
        L{formatEvent} will format an event according to several rules:

            - A string with no formatting instructions will be passed straight
              through.

            - PEP 3101 strings will be formatted using the keys and values of
              the event as named fields.

            - PEP 3101 keys ending with C{()} will be treated as instructions
              to call that key (which ought to be a callable) before
              formatting.

        L{formatEvent} will always return L{unicode}, and if given bytes, will
        always treat its format string as UTF-8 encoded.
        """
        def format(logFormat, **event):
            event["log_format"] = logFormat
            result = formatEvent(event)
            self.assertIdentical(type(result), unicode)
            return result

        self.assertEquals(u"", format(b""))
        self.assertEquals(u"", format(u""))
        self.assertEquals(u"abc", format("{x}", x="abc"))
        self.assertEquals(u"no, yes.",
                          format("{not_called}, {called()}.",
                                 not_called="no", called=lambda: "yes"))
        self.assertEquals(u"S\xe1nchez", format(b"S\xc3\xa1nchez"))
        badResult = format(b"S\xe1nchez")
        self.assertIn(u"Unable to format event", badResult)
        maybeResult = format(b"S{a!s}nchez", a=b"\xe1")
        # The behavior of unicode.format("{x}", x=bytes) differs on py2 and
        # py3.  Perhaps we should make our modified formatting more consistent
        # than this? -glyph
        if not _PY3:
            self.assertIn(u"Unable to format event", maybeResult)
        else:
            self.assertIn(u"Sb'\\xe1'nchez", maybeResult)

        xe1 = unicode(repr(b"\xe1"))
        self.assertIn(u"S" + xe1 + "nchez", format(b"S{a!r}nchez", a=b"\xe1"))


    def test_formatEventNoFormat(self):
        """
        Formatting an event with no format.
        """
        event = dict(foo=1, bar=2)
        result = formatEvent(event)

        self.assertEquals(u"", result)


    def test_formatEventWeirdFormat(self):
        """
        Formatting an event with a bogus format.
        """
        event = dict(log_format=object(), foo=1, bar=2)
        result = formatEvent(event)

        self.assertIn("Log format must be unicode or bytes", result)
        self.assertIn(repr(event), result)


    def test_formatUnformattableEvent(self):
        """
        Formatting an event that's just plain out to get us.
        """
        event = dict(log_format="{evil()}", evil=lambda: 1/0)
        result = formatEvent(event)

        self.assertIn("Unable to format event", result)
        self.assertIn(repr(event), result)


    def test_formatUnformattableEventWithUnformattableKey(self):
        """
        Formatting an unformattable event that has an unformattable key.
        """
        event = {
            "log_format": "{evil()}",
            "evil": lambda: 1/0,
            Unformattable(): "gurk",
        }
        result = formatEvent(event)
        self.assertIn("MESSAGE LOST: unformattable object logged:", result)
        self.assertIn("Recoverable data:", result)
        self.assertIn("Exception during formatting:", result)


    def test_formatUnformattableEventWithUnformattableValue(self):
        """
        Formatting an unformattable event that has an unformattable value.
        """
        event = dict(
            log_format="{evil()}",
            evil=lambda: 1/0,
            gurk=Unformattable(),
        )
        result = formatEvent(event)
        self.assertIn("MESSAGE LOST: unformattable object logged:", result)
        self.assertIn("Recoverable data:", result)
        self.assertIn("Exception during formatting:", result)


    def test_formatUnformattableEventWithUnformattableErrorOMGWillItStop(self):
        """
        Formatting an unformattable event that has an unformattable value.
        """
        event = dict(
            log_format="{evil()}",
            evil=lambda: 1/0,
            recoverable="okay",
        )
        # Call formatUnformattableEvent() directly with a bogus exception.
        result = formatUnformattableEvent(event, Unformattable())
        self.assertIn("MESSAGE LOST: unformattable object logged:", result)
        self.assertIn(repr("recoverable") + " = " + repr("okay"), result)



class FlatFormattingTests(unittest.TestCase):
    """
    Tests for flattened event formatting functions.
    """

    def test_formatFlatEvent(self):
        """
        L{flattenEvent} will "flatten" an event so that, if scrubbed of all but
        serializable objects, it will preserve all necessary data to be
        formatted once serialized.  When presented with an event thusly
        flattened, L{formatEvent} will produce the same output.
        """
        counter = count()

        class Ephemeral(object):
            attribute = "value"

        event1 = dict(
            log_format="callable: {callme()} attribute: {object.attribute} "
                       "numrepr: {number!r} strrepr: {string!r}",
            callme=lambda: next(counter), object=Ephemeral(),
            number=7, string="hello",
        )

        flattenEvent(event1)

        event2 = dict(event1)
        del event2["callme"]
        del event2["object"]
        event3 = json.loads(json.dumps(event2))
        self.assertEquals(formatEvent(event3),
                          u"callable: 0 attribute: value numrepr: 7 "
                          "strrepr: 'hello'")


    def test_flatKey(self):
        """
        Test that flatKey returns the expected keys for format fields.
        """
        def keyFromFormat(format):
            for (
                literalText,
                fieldName,
                formatSpec,
                conversion,
            ) in theFormatter.parse(format):
                return flatKey(fieldName, formatSpec, conversion)

        # No name
        self.assertEquals(keyFromFormat("{}"), "!:")

        # Just a name
        self.assertEquals(keyFromFormat("{foo}"), "foo!:")

        # Add conversion
        self.assertEquals(keyFromFormat("{foo!s}"), "foo!s:")
        self.assertEquals(keyFromFormat("{foo!r}"), "foo!r:")

        # Add format spec
        self.assertEquals(keyFromFormat("{foo:%s}"), "foo!:%s")
        self.assertEquals(keyFromFormat("{foo:!}"), "foo!:!")
        self.assertEquals(keyFromFormat("{foo::}"), "foo!::")

        # Both
        self.assertEquals(keyFromFormat("{foo!s:%s}"), "foo!s:%s")
        self.assertEquals(keyFromFormat("{foo!s:!}"), "foo!s:!")
        self.assertEquals(keyFromFormat("{foo!s::}"), "foo!s::")


    def test_formatFlatEvent_fieldNamesSame(self):
        """
        The same format field used twice is rendered twice.
        """
        counter = count()

        class CountStr(object):
            def __str__(self):
                return str(next(counter))

        event = dict(
            log_format="{x} {x}",
            x=CountStr(),
        )
        flattenEvent(event)
        self.assertEquals(formatEvent(event), u"0 1")



class TimeFormattingTests(unittest.TestCase):
    """
    Tests for time formatting functions.
    """

    def setUp(self):
        addTZCleanup(self)


    def test_formatTimeWithDefaultFormat(self):
        """
        Default time stamp format is RFC 3339 and offset respects the timezone
        as set by the standard C{TZ} environment variable and L{tzset} API.
        """
        if tzset is None:
            raise SkipTest(
                "Platform cannot change timezone; unable to verify offsets."
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

            self.assertEquals(formatTime(localDST), expectedDST)
            self.assertEquals(formatTime(localSTD), expectedSTD)

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


    def test_formatTimeWithNoTime(self):
        """
        If C{when} argument is C{None}, we should get the default output.
        """
        self.assertEquals(formatTime(None), u"-")
        self.assertEquals(formatTime(None, default=u"!"), u"!")


    def test_formatTimeWithNoFormat(self):
        """
        If C{timeFormat} argument is C{None}, we should get the default output.
        """
        t = mktime((2013, 9, 24, 11, 40, 47, 1, 267, 1))
        self.assertEquals(formatTime(t, timeFormat=None), u"-")
        self.assertEquals(formatTime(t, timeFormat=None, default=u"!"), u"!")



class ClassicLogFormattingTests(unittest.TestCase):
    """
    Tests for classic text log event formatting functions.
    """

    def test_(self):
        pass
    test_.todo = "Need some tests here"


class FormatFieldTests(unittest.TestCase):
    """
    Tests for format field functions.
    """

    def test_formatWithCall(self):
        """
        L{formatWithCall} is an extended version of L{unicode.format} that
        will interpret a set of parentheses "C{()}" at the end of a format key
        to mean that the format key ought to be I{called} rather than
        stringified.
        """
        self.assertEquals(
            formatWithCall(
                u"Hello, {world}. {callme()}.",
                dict(world="earth", callme=lambda: "maybe")
            ),
            "Hello, earth. maybe."
        )
        self.assertEquals(
            formatWithCall(
                u"Hello, {repr()!r}.",
                dict(repr=lambda: "repr")
            ),
            "Hello, 'repr'."
        )



class FixedOffsetTimeZoneTests(unittest.TestCase):
    """
    Tests for L{FixedOffsetTimeZone}.
    """

    def setUp(self):
        addTZCleanup(self)


    def test_tzinfo(self):
        """
        Test that timezone attributes respect the timezone as set by the
        standard C{TZ} environment variable and L{tzset} API.
        """
        if tzset is None:
            raise SkipTest(
                "Platform cannot change timezone; unable to verify offsets."
            )

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

        # UTC
        testForTimeZone("UTC+00", "+0000", "+0000")
        # West of UTC
        testForTimeZone("EST+05EDT,M4.1.0,M10.5.0", "-0400", "-0500")
        # East of UTC
        testForTimeZone("CEST-01CEDT,M4.1.0,M10.5.0", "+0200", "+0100")
        # No DST
        testForTimeZone("CST+06", "-0600", "-0600")



class Unformattable(object):
    """
    An object that raises an exception from C{__repr__}.
    """

    def __repr__(self):
        return str(1/0)



def setTZ(name):
    if tzset is None:
        return

    if name is None:
        try:
            del environ["TZ"]
        except KeyError:
            pass
    else:
        environ["TZ"] = name
    tzset()


def addTZCleanup(testCase):
    tzIn = environ.get("TZ", None)

    @testCase.addCleanup
    def resetTZ():
        setTZ(tzIn)
