# -*- test-case-name: twisted.python.logger.test.test_filter -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Filtering log observer.
"""

from zope.interface import Interface, implementer

from twisted.python.constants import NamedConstant, Names
from twisted.python.logger._levels import InvalidLogLevelError, LogLevel
from twisted.python.logger._observer import ILogObserver



class PredicateResult(Names):
    """
    Predicate results.
    """
    yes   = NamedConstant()  # Log this
    no    = NamedConstant()  # Don't log this
    maybe = NamedConstant()  # No opinion



class ILogFilterPredicate(Interface):
    """
    A predicate that determined whether an event should be logged.
    """

    def __call__(event):
        """
        Determine whether an event should be logged.

        @returns: a L{PredicateResult}.
        """



@implementer(ILogObserver)
class FilteringLogObserver(object):
    """
    L{ILogObserver} that wraps another L{ILogObserver}, but filters
    out events based on applying a series of L{ILogFilterPredicate}s.
    """

    def __init__(self, observer, predicates):
        """
        @param observer: an L{ILogObserver} to which this observer
            will forward events.

        @param predicates: an ordered iterable of predicates to apply
            to events before forwarding to the wrapped observer.
        """
        self.observer   = observer
        self.predicates = list(predicates)


    def shouldLogEvent(self, event):
        """
        Determine whether an event should be logged, based C{self.predicates}.

        @param event: an event
        @type event: L{dict}

        @return: yes, no, or maybe
        @rtype: L{NamedConstant} from L{PredicateResult}
        """
        for predicate in self.predicates:
            result = predicate(event)
            if result == PredicateResult.yes:
                return True
            if result == PredicateResult.no:
                return False
            if result == PredicateResult.maybe:
                continue
            raise TypeError("Invalid predicate result: {0!r}".format(result))
        return True


    def __call__(self, event):
        """
        Forward to next observer if predicate allows it.
        """
        if self.shouldLogEvent(event):
            if "log_trace" in event:
                event["log_trace"].append((self, self.observer))
            self.observer(event)



@implementer(ILogFilterPredicate)
class LogLevelFilterPredicate(object):
    """
    L{ILogFilterPredicate} that filters out events with a log level
    lower than the log level for the event's namespace.

    Events that not not have a log level or namespace are also dropped.
    """
    defaultLogLevel = LogLevel.info


    def __init__(self):
        self._logLevelsByNamespace = {}
        self.clearLogLevels()


    def logLevelForNamespace(self, namespace):
        """
        Determine an appropriate log level for the given namespace.

        This respects dots in namespaces; for example, if you have previously
        invoked C{setLogLevelForNamespace("mypackage", LogLevel.debug)}, then
        C{logLevelForNamespace("mypackage.subpackage")} will return
        C{LogLevel.debug}.

        @param namespace: a logging namespace, or C{None} for the default
            namespace.
        @type namespace: L{str} (native string)

        @return: the L{LogLevel} for the specified namespace.
        """
        if not namespace:
            return self._logLevelsByNamespace[None]

        if namespace in self._logLevelsByNamespace:
            return self._logLevelsByNamespace[namespace]

        segments = namespace.split(".")
        index = len(segments) - 1

        while index > 0:
            namespace = ".".join(segments[:index])
            if namespace in self._logLevelsByNamespace:
                return self._logLevelsByNamespace[namespace]
            index -= 1

        return self._logLevelsByNamespace[None]


    def setLogLevelForNamespace(self, namespace, level):
        """
        Sets the global log level for a logging namespace.

        @param namespace: a logging namespace

        @param level: the L{LogLevel} for the given namespace.
        """
        if level not in LogLevel.iterconstants():
            raise InvalidLogLevelError(level)

        if namespace:
            self._logLevelsByNamespace[namespace] = level
        else:
            self._logLevelsByNamespace[None] = level


    def clearLogLevels(self):
        """
        Clears all global log levels to the default.
        """
        self._logLevelsByNamespace.clear()
        self._logLevelsByNamespace[None] = self.defaultLogLevel


    def __call__(self, event):
        level     = event.get("log_level", None)
        namespace = event.get("log_namespace", None)

        if (
            level is None or
            namespace is None or
            LogLevel._priorityForLevel(level) <
            LogLevel._priorityForLevel(self.logLevelForNamespace(namespace))
        ):
            return PredicateResult.no

        return PredicateResult.maybe
