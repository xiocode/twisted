# -*- test-case-name: twisted.python.logger.test.test_global -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
This module includes process-global state associated with the logging system,
and implementation of logic for managing that global state.
"""

import sys

from twisted.python.compat import currentframe

from ._buffer import LimitedHistoryLogObserver
from ._observer import LogPublisher
from ._filter import (FilteringLogObserver,
                                           LogLevelFilterPredicate)
from ._logger import Logger
from ._format import formatEvent
from ._levels import LogLevel
from ._file import FileLogObserver

MORE_THAN_ONCE_WARNING = (
    "Warning: primary log target selected twice at <{fileNow}:{lineNow}> - "
    "previously selected at <{fileThen:logThen}>.  Remove one of the calls to "
    "beginLoggingTo."
)

class LogBeginner(object):
    """
    A L{LogBeginner} holds state related to logging before logging has begun,
    and begins logging when told to do so.  Logging "begins" when someone has
    selected a set of observers, like, for example, a L{FileLogObserver} that
    writes to a file on disk, or to standard output.

    Applications will not typically need to instantiate this class, except
    those which intend to initialize the global logging system themselves,
    which may wish to instantiate this for testing.  The global instance for
    the current process is exposed as
    L{twisted.python.logger.globalLogBeginner}.

    Before logging has begun, a L{LogBeginner} will:

        1. Log any critical messages (e.g.: unhandled exceptions) to the given
           file-like object.

        2. Save (a limited number of) log events in a
           L{LimitedHistoryLogObserver}.

    @ivar _initialBuffer: A buffer of messages logged before logging began.
    @type _initialBuffer: L{LimitedHistoryLogObserver}

    @ivar _publisher: The log publisher passed in to L{LogBeginner}'s
        constructor.
    @type _publisher: L{LogPublisher}

    @ivar _log: The logger used to log messages about the operation of the
        L{LogBeginner} itself.
    @type _log: L{Logger}

    @ivar _temporaryObserver: If not C{None}, an L{ILogObserver} that observes
        events on C{_publisher} for this L{LogBeginner}.
    @type _temporaryObserver: L{ILogObserver} or L{NoneType}
    """

    def __init__(self, publisher, errorStream):
        self._initialBuffer = LimitedHistoryLogObserver()
        self._publisher = publisher
        self._log = Logger(observer=publisher)
        fileObserver = FileLogObserver(errorStream,
                                       lambda event: formatEvent(event)+"\n")
        predicate = LogLevelFilterPredicate(defaultLogLevel=LogLevel.critical)
        self._temporaryObserver = LogPublisher(
            self._initialBuffer,
            FilteringLogObserver(fileObserver, [predicate])
        )
        publisher.addObserver(self._temporaryObserver)


    def beginLoggingTo(self, observers):
        """
        Begin logging to the given set of observers.  This will:

            1. Add all the observers given in C{observers} to the
               L{LogPublisher} associated with this L{LogBeginner}.

            2. Re-play any messages that were previously logged to that
               publisher to the new observers.

            3. Stop logging critical errors from the L{LogPublisher} as strings
               to the C{errorStream} associated with this L{LogBeginner}, and
               allow them to be logged normally.

        @note: Since a L{LogBeginner} is designed to encapsulate the transition
            between process-startup and log-system-configuration, this method
            is intended to be invoked I{once}.

        @param observers: The observers to register.
        @type observers: iterable of L{ILogObserver}s
        """
        caller = currentframe(1)
        filename, lineno = caller.f_code.co_filename, caller.f_lineno
        for observer in observers:
            self._publisher.addObserver(observer)
        if self._temporaryObserver is not None:
            self._publisher.removeObserver(self._temporaryObserver)
            self._initialBuffer.replayTo(self._publisher)
            self._temporaryObserver = None
        else:
            previousFile, previousLine = self._previousBegin
            self._log.warn(MORE_THAN_ONCE_WARNING,
                           fileNow=filename, lineNow=lineno,
                           fileThen=previousFile, lineThen=previousLine)
        self._previousBegin = filename, lineno



globalLogPublisher = LogPublisher()
globalLogBeginner = LogBeginner(globalLogPublisher, sys.stderr)
