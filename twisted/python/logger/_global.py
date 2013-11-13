# -*- test-case-name: twisted.python.logger.test.test_global -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Global log publisher.
"""

import sys

from twisted.python.compat import currentframe

from twisted.python.logger._buffer import RingBufferLogObserver
from twisted.python.logger._observer import LogPublisher

from twisted.python.logger._filter import (FilteringLogObserver,
                                           LogLevelFilterPredicate)
from twisted.python.logger._logger import Logger

from twisted.python.logger._format import formatEvent
from twisted.python.logger._levels import LogLevel
from twisted.python.logger._file import FileLogObserver

MORE_THAN_ONCE_WARNING = (
    "Warning: primary log target selected twice at <{fileNow}:{lineNow}> - "
    "previously selected at <{fileThen:logThen}>.  Remove one of the calls to "
    "beginLoggingTo."
)

class LogBeginner(object):
    """
    A L{LogBeginner} holds state related to logging before logging has
    begun, and begins logging when told to do so.  Logging "begins" when
    someone has selected a set of observers, like, for example, a
    L{FileLogObserver}.
    """

    def __init__(self, publisher, errorStream):
        self._temporaryObserver = RingBufferLogObserver()
        fileObserver = FileLogObserver(errorStream,
                                       lambda event: formatEvent(event)+"\n")
        predicate = LogLevelFilterPredicate(defaultLogLevel=LogLevel.critical)
        self._temporaryTracebackReporter = FilteringLogObserver(fileObserver,
                                                                [predicate])
        self._publisher = publisher
        self._publisher.addObserver(self._temporaryObserver)
        self._publisher.addObserver(self._temporaryTracebackReporter)
        self._log = Logger(observer=self._publisher)


    def beginLoggingTo(self, observers):
        """
        Begin logging to the given set of observers.

        @param observers: The observers to register.
        @type observers: iterable of L{ILogObserver}s
        """
        caller = currentframe(1)
        filename, lineno = caller.f_code.co_filename, caller.f_lineno

        for observer in observers:
            self._publisher.addObserver(observer)

        if self._temporaryObserver is not None:
            self._publisher.removeObserver(self._temporaryObserver)
            self._publisher.removeObserver(self._temporaryTracebackReporter)
            self._temporaryObserver.replayTo(self._publisher)
            self._temporaryObserver = None
        else:
            self._log.warn(MORE_THAN_ONCE_WARNING,
                           fileNow=filename, lineNow=lineno,
                           fileThen=self._previousBeginFile,
                           lineThen=self._previousBeginLine)
        self._previousBeginFile = filename
        self._previousBeginLine = lineno



globalLogPublisher = LogPublisher()
logBeginner = LogBeginner(globalLogPublisher, sys.stderr)
