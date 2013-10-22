# -*- test-case-name: twisted.python.logger.test.test_file -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
File log observer.
"""

__all__ = [
    "FileLogObserver",
]

from datetime import datetime as DateTime, tzinfo as TZInfo
from datetime import timedelta as TimeDelta

from zope.interface import implementer

from twisted.python.compat import ioType, unicode
from twisted.python.logger._format import formatEvent
from twisted.python.logger._observer import ILogObserver




@implementer(ILogObserver)
class FileLogObserver(object):
    """
    Log observer that writes to a file-like object.
    """

    timeFormatRFC3339 = "%Y-%m-%dT%H:%M:%S%z"


    def __init__(self, textOutput, timeFormat=timeFormatRFC3339):
        """
        @param textOutput: a file-like object.  Ideally one should be passed
            which accepts unicode; if not, utf-8 will be used as the encoding.
        @type textOutput: L{io.IOBase}

        @param timeFormat: the format to use when adding timestamp prefixes to
            logged events.  If C{None}, no timestamp prefix is added.
        """
        if ioType(textOutput) is not unicode:
            self._encoding = "utf-8"
        else:
            self._encoding = None
        self._outputStream = textOutput
        self._timeFormat = timeFormat


    def formatTime(self, when):
        """
        Format a timestamp as text.

        @param when: a timestamp.
        @type then: L{float}

        @return: a formatted time.
        @rtype: L{unicode}
        """
        if (
            self._timeFormat is not None and
            when is not None
        ):
            tz = FixedOffsetTimeZone.fromTimeStamp(when)
            datetime = DateTime.fromtimestamp(when, tz)
            return unicode(datetime.strftime(self._timeFormat))
        else:
            return u"-"


    def formatEvent(self, event):
        """
        Format an event for output.

        @param event: an event.
        @type event: L{dict}

        @return: a formatted event, or C{None} if no output is appropriate.
        @rtype: L{unicode} or C{None}
        """
        eventText = formatEvent(event)
        if not eventText:
            return None

        eventText = eventText.replace(u"\n", u"\n\t")
        timeStamp = self.formatTime(event.get("log_time", None))

        system = event.get("log_system", None)

        if system is None:
            system = u"{namespace}#{level}".format(
                namespace=event.get("log_namespace", u"-"),
                level=event.get("log_level", u"-"),
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


    def __call__(self, event):
        """
        Write event to file.

        @param event: an event.
        @type event: L{dict}
        """
        text = self.formatEvent(event)
        if text is None:
            return
        if self._encoding is not None:
            text = text.encode(self._encoding)
        self._outputStream.write(text)
        self._outputStream.flush()



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
