# -*- test-case-name: twisted.python.test.test_logger -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Integration with L{twisted.python.log}.
"""

__all__ = [
    "LegacyLogger",
    "LegacyLogObserverWrapper",
]

from zope.interface import implementer

from twisted.python.reflect import safe_str
from twisted.python.failure import Failure
from twisted.python.logger._levels import LogLevel
from twisted.python.logger._format import formatEvent
from twisted.python.logger._logger import Logger
from twisted.python.logger._observer import ILogObserver
from twisted.python.logger._stdlib import pythonLogLevelMapping
from twisted.python.logger._stdlib import StringifiableFromEvent



class LegacyLogger(object):
    """
    A logging object that provides some compatibility with the
    L{twisted.python.log} module.

    Specifically, it provides compatible C{msg()} and C{err()} which
    forwards events to a L{Logger}'s C{emit()}, which will in turn
    produce new-style events.

    This allows existing code to use this module without changes::

        from twisted.python.logger import LegacyLogger
        log = LegacyLogger()

        log.msg("blah")

        log.msg(warning=message, category=reflect.qual(category),
                filename=filename, lineno=lineno,
                format="%(filename)s:%(lineno)s: %(category)s: %(warning)s")

        try:
            1/0
        except Exception as e:
            log.err(e, "Math is hard")
    """

    def __init__(self, logger=None):
        """
        @param logger: a L{Logger}
        """
        if logger is None:
            self.newStyleLogger = Logger(Logger._namespaceFromCallingContext())
        else:
            self.newStyleLogger = logger

        import twisted.python.log as oldStyleLogger
        self.oldStyleLogger = oldStyleLogger


    def __getattribute__(self, name):
        try:
            return super(LegacyLogger, self).__getattribute__(name)
        except AttributeError:
            return getattr(self.oldStyleLogger, name)


    def msg(self, *message, **kwargs):
        """
        This method is API-compatible with L{twisted.python.log.msg} and exists
        for compatibility with that API.

        @param message: L{bytes} objects.
        @type message: L{tuple}

        @param kwargs: Fields in the legacy log message.
        @type kwargs: L{dict}
        """
        if message:
            message = " ".join(map(safe_str, message))
        else:
            message = None
        return self.newStyleLogger.emit(LogLevel.info, message, **kwargs)


    def err(self, _stuff=None, _why=None, **kwargs):
        """
        This method is API-compatible with L{twisted.python.log.err} and exists
        for compatibility with that API.

        @param _stuff: A L{Failure}, a string, or an exception.
        @type _stuff: Something that describes a problem.

        @param _why: A string describing what caused the failure.
        @type _why: L{str}

        @param kwargs: Additional fields.
        @type kwargs: L{dict}
        """
        if _stuff is None:
            _stuff = Failure()
        elif isinstance(_stuff, Exception):
            _stuff = Failure(_stuff)

        if isinstance(_stuff, Failure):
            self.newStyleLogger.emit(LogLevel.error, failure=_stuff, why=_why,
                                     isError=1, **kwargs)
        else:
            # We got called with an invalid _stuff.
            self.newStyleLogger.emit(LogLevel.error, repr(_stuff), why=_why,
                                     isError=1, **kwargs)



@implementer(ILogObserver)
class LegacyLogObserverWrapper(object):
    """
    L{ILogObserver} that wraps an L{twisted.python.log.ILogObserver}.

    Received (new-style) events are modified prior to forwarding to
    the legacy observer to ensure compatibility with observers that
    expect legacy events.
    """

    def __init__(self, legacyObserver):
        """
        @param legacyObserver: an L{twisted.python.log.ILogObserver} to which
            this observer will forward events.
        """
        self.legacyObserver = legacyObserver


    def __repr__(self):
        return (
            "{self.__class__.__name__}({self.legacyObserver})"
            .format(self=self)
        )


    def __call__(self, event):
        """
        Forward events to the legacy observer after editing them to
        ensure compatibility.
        """

        # Twisted's logging supports indicating a python log level, so let's
        # provide the equivalent to our logging levels.
        level = event.get("log_level", None)
        if level in pythonLogLevelMapping:
            event["logLevel"] = pythonLogLevelMapping[level]

        # The "message" key is required by textFromEventDict()
        if "message" not in event:
            event["message"] = ()

        system = event.get("log_system", None)
        if system is not None:
            event["system"] = system

        # Format new style -> old style
        if event.get("log_format", None) is not None and 'format' not in event:
            # Create an object that implements __str__() in order to defer the
            # work of formatting until it's needed by a legacy log observer.
            event["format"] = "%(log_legacy)s"
            event["log_legacy"] = StringifiableFromEvent(event.copy())

        # log.failure() -> isError blah blah
        if "log_failure" in event:
            event["failure"] = event["log_failure"]
            event["isError"] = 1
            event["why"] = formatEvent(event)
        elif "isError" not in event:
            event["isError"] = 0

        self.legacyObserver(event)
