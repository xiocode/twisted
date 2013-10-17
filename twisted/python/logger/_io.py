# -*- test-case-name: twisted.python.logger.test.test_io -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
File-like object that logs.
"""

__all__ = [
    "LoggingFile",
]

import sys

from twisted.python.logger._levels import LogLevel
from twisted.python.logger._logger import Logger



class LoggingFile(object):
    """
    File-like object that turns C{write()} calls into logging events.

    Note that because event formats are C{unicode}, C{bytes} received via
    C{write()} are converted to C{unicode}, which is the opposite of what
    C{file} does.

    @cvar defaultLogger: The default L{Logger} instance to use when none is
        supplied to L{LoggingFile.__init__}.
    @type defaultLogger: L{Logger}

    @ivar softspace: File-like L{'softspace' attribute <file.softspace>}; zero
        or one.
    @type softspace: C{int}
    """

    defaultLogger = Logger()
    softspace = 0


    def __init__(self, level=LogLevel.info, encoding=None, logger=None):
        """
        @param level: the log level to emit events with.

        @param encoding: the encoding to expect when receiving bytes via
            C{write()}.  If C{None}, use C{sys.getdefaultencoding()}.

        @param log: the L{Logger} to send events to.  If C{None}, use
            L{LoggingFile.defaultLogger}.
        """
        self.level = level

        if logger is None:
            self.log = self.defaultLogger
        else:
            self.log = logger

        if encoding is None:
            self._encoding = sys.getdefaultencoding()
        else:
            self._encoding = encoding

        self._buffer = ""
        self._closed = False


    @property
    def closed(self):
        """
        Read-only property.  Is the file closed?
        """
        return self._closed


    @property
    def encoding(self):
        """
        Read-only property.  Does the file have an encoding?
        """
        return self._encoding


    @property
    def mode(self):
        """
        Read-only property.  Does the file have an encoding?
        """
        return "w"


    @property
    def newlines(self):
        """
        Read-only property.  Does the file have an encoding?
        """
        return None


    @property
    def name(self):
        """
        The name of this file; a repr-style string giving information about its
        namespace.
        """
        return (
            "<{0} {1}#{2}>".format(
                self.__class__.__name__,
                self.log.namespace,
                self.level.name,
            )
        )


    def close(self):
        """
        Close this file so it can no longer be written to.
        """
        self._closed = True


    def flush(self):
        """
        No-op; this file does not buffer.
        """


    def fileno(self):
        """
        Returns an invalid file descriptor, since this is not backed by an FD.
        """
        return -1


    def isatty(self):
        """
        A L{LoggingFile} is not a TTY.

        @return: False
        """
        return False


    def write(self, string):
        """
        Log the given message.
        """
        if self._closed:
            raise ValueError("I/O operation on closed file")

        if isinstance(string, bytes):
            string = string.decode(self._encoding)

        lines = (self._buffer + string).split("\n")
        self._buffer = lines[-1]
        lines = lines[0:-1]

        for line in lines:
            self.log.emit(self.level, format=u"{message}", message=line)


    def writelines(self, lines):
        """
        Log each of the given lines as a separate message.
        """
        for line in lines:
            self.write(line)


    def _unsupported(self, *args):
        """
        Template for unsupported operations.
        """
        raise IOError("unsupported operation")

    read       = _unsupported
    next       = _unsupported
    readline   = _unsupported
    readlines  = _unsupported
    xreadlines = _unsupported
    seek       = _unsupported
    tell       = _unsupported
    truncate   = _unsupported
