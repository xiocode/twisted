# -*- test-case-name: twisted.python.logger.test.test_format -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tools for formatting logging events.
"""

__all__ = [
    "formatEvent",
]

from string import Formatter

from twisted.python.compat import unicode
from twisted.python.failure import Failure
from twisted.python.reflect import safe_repr



def formatEvent(event):
    """
    Formats an event as a L{unicode}, using the format in
    C{event["log_format"]}.

    This implementation should never raise an exception; if the formatting
    cannot be done, the returned string will describe the event generically so
    that a useful message is emitted regardless.

    @param event: a logging event
    @type event: L{dict}

    @return: a formatted string
    @rtype: L{unicode}
    """
    try:
        if "log_flattened" in event:
            return flatFormat(event)

        format = event.get("log_format", None)

        if format is None:
            return u""

        # Make sure format is unicode.
        if isinstance(format, bytes):
            # If we get bytes, assume it's UTF-8 bytes
            format = format.decode("utf-8")

        elif isinstance(format, unicode):
            pass

        else:
            raise TypeError("Log format must be unicode or bytes, not {0!r}"
                            .format(format))

        return formatWithCall(format, event)

    except Exception as e:
        return formatUnformattableEvent(event, e)



def flatFormat(event):
    """
    Format an event which has been flattened with flattenEvent.

    @param event: a logging event
    @type event: L{dict}

    @return: a formatted string
    @rtype: L{unicode}
    """
    fields = event["log_flattened"]
    s = u""

    for (
        literalText, fieldName, formatSpec, conversion
    ) in theFormatter.parse(event["log_format"]):

        s += literalText

        key = flatKey(fieldName, formatSpec, conversion)
        value = fields[key]

        s += unicode(value)

    return s



def flatKey(fieldName, formatSpec, conversion):
    """
    Compute a string key for a given field/format/conversion.

    @param fieldName: a format field name
    @type fieldName: L{str}

    @param fieldName: a format spec
    @type fieldName: L{str}

    @param fieldName: a format field conversion type
    @type fieldName: L{str}

    @return: a key specific to the given field, format and conversion
    @rtype: L{str}
    """
    return (
        "{fieldName}!{conversion}:{formatSpec}"
        .format(
            fieldName=fieldName,
            formatSpec=(formatSpec or ""),
            conversion=(conversion or ""),
        )
    )



def flattenEvent(event):
    """
    Flatten the given event by pre-associating format fields with specific
    objects and callable results in a L{dict} put into the C{"log_flattened"}
    key in the event.

    @param event: a logging event
    @type event: L{dict}
    """
    fields = {}

    for (
        literalText, fieldName, formatSpec, conversion
    ) in theFormatter.parse(event["log_format"]):

        key = flatKey(fieldName, formatSpec, conversion)
        if key in fields:
            # We've already seen and handled this key
            continue

        if fieldName.endswith(u"()"):
            fieldName = fieldName[:-2]
            callit = True
        else:
            callit = False

        field = theFormatter.get_field(fieldName, (), event)
        fieldValue = field[0]
        if callit:
            fieldValue = fieldValue()

        fields[key] = fieldValue

    event["log_flattened"] = fields



def formatUnformattableEvent(event, error):
    """
    Formats an event as a L{unicode} that describes the event generically and a
    formatting error.

    @param event: a logging event
    @type event: L{dict}

    @param error: the formatting error
    @type error: L{Exception}

    @return: a formatted string
    @rtype: L{unicode}
    """
    try:
        return (
            u"Unable to format event {event!r}: {error}"
            .format(event=event, error=error)
        )
    except Exception:
        # Yikes, something really nasty happened.
        #
        # Try to recover as much formattable data as possible; hopefully at
        # least the namespace is sane, which will help you find the offending
        # logger.
        failure = Failure()

        text = u", ".join(u" = ".join((safe_repr(key), safe_repr(value)))
                          for key, value in event.items())

        return (
            u"MESSAGE LOST: unformattable object logged: {error}\n"
            u"Recoverable data: {text}\n"
            u"Exception during formatting:\n{failure}"
            .format(error=safe_repr(error), failure=failure, text=text)
        )



class CallMapping(object):
    """
    Read-only mapping that turns a C{()}-suffix in key names into an invocation
    of the key rather than a lookup of the key.

    Implementation support for L{formatWithCall}.
    """
    def __init__(self, submapping):
        """
        @param submapping: Another read-only mapping which will be used to look
            up items.
        """
        self._submapping = submapping


    def __getitem__(self, key):
        """
        Look up an item in the submapping for this L{CallMapping}, calling it
        if C{key} ends with C{"()"}.
        """
        callit = key.endswith(u"()")
        realKey = key[:-2] if callit else key
        value = self._submapping[realKey]
        if callit:
            value = value()
        return value



def formatWithCall(formatString, mapping):
    """
    Format a string like L{unicode.format}, but:

        - taking only a name mapping; no positional arguments

        - with the additional syntax that an empty set of parentheses
          correspond to a formatting item that should be called, and its result
          C{str}'d, rather than calling C{str} on the element directly as
          normal.

    For example::

        >>> formatWithCall("{string}, {function()}.",
        ...                dict(string="just a string",
        ...                     function=lambda: "a function"))
        'just a string, a function.'

    @param formatString: A PEP-3101 format string.
    @type formatString: L{unicode}

    @param mapping: A L{dict}-like object to format.

    @return: The string with formatted values interpolated.
    @rtype: L{unicode}
    """
    return unicode(
        theFormatter.vformat(formatString, (), CallMapping(mapping))
    )

theFormatter = Formatter()
