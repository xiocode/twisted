# -*- test-case-name: twisted.python.logger.test -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Classes and functions to do granular logging.

Example usage in a module C{some.module}::

    from twisted.python.logger import Logger
    log = Logger()

    def handleData(data):
        log.debug("Got data: {data!r}.", data=data)

Or in a class::

    from twisted.python.logger import Logger

    class Foo(object):
        log = Logger()

        def oops(self, data):
            self.log.error("Oops! Invalid data from server: {data!r}",
                           data=data)

C{Logger}s have namespaces, for which logging can be configured independently.
Namespaces may be specified by passing in a C{namespace} argument to L{Logger}
when instantiating it, but if none is given, the logger will derive its own
namespace by using the module name of the callable that instantiated it, or, in
the case of a class, by using the fully qualified name of the class.

In the first example above, the namespace would be C{some.module}, and in the
second example, it would be C{some.module.Foo}.
"""

__all__ = [
    # From twisted.python.logger._levels
    "InvalidLogLevelError",
    "LogLevel",

    # From twisted.python.logger._format
    "formatEvent",
    "formatEventAsClassicLogText",
    "formatTime",
    "timeFormatRFC3339",

    # From twisted.python.logger._logger
    "Logger",

    # From twisted.python.logger._observer
    "ILogObserver",
    "LogPublisher",

    # From twisted.python.logger._buffer
    "RingBufferLogObserver",

    # From twisted.python.logger._file
    "FileLogObserver",
    "textFileLogObserver",

    # From twisted.python.logger._filter
    "PredicateResult",
    "ILogFilterPredicate",
    "FilteringLogObserver",
    "LogLevelFilterPredicate",

    # From twisted.python.logger._stdlib
    "STDLibLogObserver",

    # From twisted.python.logger._io
    "LoggingFile",

    # From twisted.python.logger._legacy
    "LegacyLogger",
    "LegacyLogObserverWrapper",

    # From twisted.python.logger._global
    "globalLogPublisher",
]

from twisted.python.logger._levels import InvalidLogLevelError
from twisted.python.logger._levels import LogLevel

from twisted.python.logger._format import formatEvent
from twisted.python.logger._format import formatEventAsClassicLogText
from twisted.python.logger._format import formatTime
from twisted.python.logger._format import timeFormatRFC3339

from twisted.python.logger._logger import Logger

from twisted.python.logger._observer import ILogObserver
from twisted.python.logger._observer import LogPublisher

from twisted.python.logger._buffer import RingBufferLogObserver

from twisted.python.logger._file import FileLogObserver
from twisted.python.logger._file import textFileLogObserver

from twisted.python.logger._filter import PredicateResult
from twisted.python.logger._filter import ILogFilterPredicate
from twisted.python.logger._filter import FilteringLogObserver
from twisted.python.logger._filter import LogLevelFilterPredicate

from twisted.python.logger._stdlib import STDLibLogObserver

from twisted.python.logger._io import LoggingFile

from twisted.python.logger._legacy import LegacyLogger
from twisted.python.logger._legacy import LegacyLogObserverWrapper

from twisted.python.logger._global import globalLogPublisher
