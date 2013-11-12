# -*- test-case-name: twisted.python.logger.test.test_global -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Global log publisher.
"""

from twisted.python.logger._observer import LogPublisher
from twisted.python.logger._buffer import RingBufferLogObserver



class GlobalLogPublisher(LogPublisher):
    """
    Class for the (singleton) default log publisher.

    Received events are buffered until
    L{GlobalLogPublisher.startLoggingWithObservers} is called.
    """

    def __init__(self):
        self._temporaryObserver = RingBufferLogObserver()
        LogPublisher.__init__(self, self._temporaryObserver)


    def startLoggingWithObservers(self, observers):
        """
        Register the given observers and send any events that may have been
        previously buffered.

        @param observers: The observers to register.
        @type observers: iterable of L{ILogObserver}s
        """
        if self._temporaryObserver is None:
            raise AssertionError(
                "startLoggingWithObservers() may only be called once."
            )
        for observer in observers:
            self.addObserver(observer)
        self.removeObserver(self._temporaryObserver)
        self._temporaryObserver.replayTo(self)
        self._temporaryObserver = None


globalLogPublisher = GlobalLogPublisher()
