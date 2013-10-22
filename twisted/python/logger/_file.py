# -*- test-case-name: twisted.python.logger.test.test_file -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
File log observer.
"""

__all__ = [
    "FileLogObserver",
]

from zope.interface import implementer

from twisted.python.compat import ioType, unicode
from twisted.python.logger._observer import ILogObserver
from twisted.python.logger._format import formatEventAsLine
from twisted.python.logger._format import timeFormatRFC3339




@implementer(ILogObserver)
class FileLogObserver(object):
    """
    Log observer that writes to a file-like object.
    """
    def __init__(self, textOutput, formatEvent):
        """
        @param textOutput: a file-like object.  Ideally one should be passed
            which accepts unicode; if not, utf-8 will be used as the encoding.
        @type textOutput: L{io.IOBase}

        @param formatEvent: a callable formats an event
        @type formatEvent: L{callable} that takes an C{event} argument and
            returns a formatted event as L{unicode}.
        """
        if ioType(textOutput) is not unicode:
            self._encoding = "utf-8"
        else:
            self._encoding = None
        self._outputStream = textOutput
        self.formatEvent = formatEvent


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



def textFileLogObserver(textOutput, timeFormat=timeFormatRFC3339):
    """
    Create a L{FileLogObserver} that emits text.

    @param textOutput: a file-like object.  Ideally one should be passed
        which accepts unicode; if not, utf-8 will be used as the encoding.
    @type textOutput: L{io.IOBase}

    @param timeFormat: the format to use when adding timestamp prefixes to
        logged events.  If C{None}, no timestamp prefix is added.

    @return
    """
    if timeFormat is None:
        formatEvent = formatEventAsLine
    else:
        formatEvent = lambda e: formatEventAsLine(e, timeFormat=timeFormat)

    return FileLogObserver(textOutput, formatEvent)
