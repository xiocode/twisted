# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Test cases for L{twisted.python.logger._format}.
"""

from itertools import count
import json

from twisted.trial import unittest

from twisted.python.compat import _PY3, unicode
from twisted.python.logger._format import formatEvent
from twisted.python.logger._format import formatUnformattableEvent
from twisted.python.logger._format import flattenEvent
from twisted.python.logger._format import flatKey
from twisted.python.logger._format import formatWithCall
from twisted.python.logger._format import theFormatter



class FormattingTests(unittest.TestCase):
    """
    Tests for event formatting functions.
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
                return str(counter.next())

        event = dict(
            log_format="{x} {x}",
            x=CountStr(),
        )
        flattenEvent(event)
        self.assertEquals(formatEvent(event), u"0 1")



class Unformattable(object):
    """
    An object that raises an exception from C{__repr__}.
    """

    def __repr__(self):
        return str(1/0)
