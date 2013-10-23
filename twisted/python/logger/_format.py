# -*- test-case-name: twisted.python.logger.test.test_format -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tools for formatting logging events.
"""

__all__ = [
    "formatEvent",
    "formatEventAsClassicLogText",
    "formatTime",
    "timeFormatRFC3339",
]

from string import Formatter
from datetime import datetime as DateTime, tzinfo as TZInfo
from datetime import timedelta as TimeDelta

from twisted.python.compat import unicode
from twisted.python.failure import Failure
from twisted.python.reflect import safe_repr

timeFormatRFC3339 = "%Y-%m-%dT%H:%M:%S%z"



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

    @param formatSpec: a format spec
    @type formatSpec: L{str}

    @param conversion: a format field conversion type
    @type conversion: L{str}

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
        if conversion == "s":
            conversionFunction = str
        elif conversion == "r":
            conversionFunction = repr
        else:
            conversionFunction = lambda x: x
        if callit:
            fieldValue = fieldValue()
        fieldValue = conversionFunction(fieldValue)

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



def formatTime(when, timeFormat=timeFormatRFC3339, default=u"-"):
    """
    Format a timestamp as text.

    Example::

        >>> from time import time
        >>> from twisted.python.logger import formatTime
        >>>
        >>> t = time()
        >>> formatTime(t)
        u'2013-10-22T14:19:11-0700'
        >>> formatTime(t, timeFormat="%Y/%W")  # Year and week number
        u'2013/42'
        >>>

    @param when: a timestamp.
    @type then: L{float}

    @param timeFormat: a time format
    @type timeFormat: L{unicode} or C{None}

    @param default: text to return if C{when} or C{timeFormat} is C{None}.
    @type default: L{unicode}

    @return: a formatted time.
    @rtype: L{unicode}
    """
    if (timeFormat is None or when is None):
        return default
    else:
        tz = FixedOffsetTimeZone.fromTimeStamp(when)
        datetime = DateTime.fromtimestamp(when, tz)
        return unicode(datetime.strftime(timeFormat))



def formatEventAsClassicLogText(event, formatTime=formatTime):
    """
    Format an event as a line of human-readable text for, eg. traditional log
    file output.

    The output format is C{u"{timeStamp} [{system}] {event}\n"}, where:

      - C{timeStamp} is computed by calling the given C{formatTime} callable
        on the event's C{"log_time"} value

      - C{system} is the event's C{"log_system"} value, if set, otherwise,
        the C{"log_namespace"} and C{"log_level"}, joined by a C{u"#"}.
        Each defaults to C{u"-"} is not set.

      - C{event} is the event, as formatted by L{formatEvent}.

    Example::

        >>> from __future__ import print_function
        >>> from time import time
        >>> from twisted.python.logger import formatEventAsClassicLogText
        >>>
        >>> formatEventAsClassicLogText(dict())  # No format, returns None
        >>> formatEventAsClassicLogText(event)
        u'2013-10-22T15:09:18-0700 [-#-] Hello!\n'
        >>> formatEventAsClassicLogText(dict(
        ...     log_format=u"Hello!",
        ...     log_time=time(),
        ...     log_namespace="my.namespace",
        ...     log_level=LogLevel.info,
        ... ))
        u'2013-10-22T17:30:02-0700 [my.namespace#info] Hello!\n'
        >>>

    @param event: an event.
    @type event: L{dict}

    @param formatTime: a time formatter
    @type formatTime: a L{callable} that takes an C{event} argument and returns
        a L{unicode}

    @return: a formatted event, or C{None} if no output is appropriate.
    @rtype: L{unicode} or C{None}
    """
    eventText = formatEvent(event)
    if not eventText:
        return None

    eventText = eventText.replace(u"\n", u"\n\t")
    timeStamp = formatTime(event.get("log_time", None))

    system = event.get("log_system", None)

    if system is None:
        level = event.get("log_level", None)
        if level is None:
            levelName = u"-"
        else:
            levelName = level.name

        system = u"{namespace}#{level}".format(
            namespace=event.get("log_namespace", u"-"),
            level=levelName,
        )
    else:
        try:
            system = unicode(system)
        except Exception:
            system = u"UNFORMATTABLE"

    return u"{timeStamp} [{system}] {event}\n".format(
        timeStamp=timeStamp,
        system=system,
        event=eventText,
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



class FixedOffsetTimeZone(TZInfo):
    """
    Time zone with a fixed offset.
    """

    @classmethod
    def fromTimeStamp(cls, timeStamp):
        """
        Create a time zone with a fixed offset corresponding to a time stamp.

        @param timeStamp: a time stamp
        @type timeStamp: L{int}

        @return: a time zone
        @rtype: L{FixedOffsetTimeZone}
        """
        offset = (
            DateTime.fromtimestamp(timeStamp) -
            DateTime.utcfromtimestamp(timeStamp)
        )
        return cls(offset)


    def __init__(self, offset):
        self._offset = offset


    def utcoffset(self, dt):
        return self._offset


    def tzname(self, dt):
        dt = DateTime.fromtimestamp(0, self)
        return dt.strftime("UTC%z")


    def dst(self, dt):
        return timeDeltaZero



timeDeltaZero = TimeDelta(0)
