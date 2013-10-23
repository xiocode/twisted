# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Test cases for L{twisted.python.logger._file}.
"""

from io import StringIO

from zope.interface.verify import verifyObject, BrokenMethodImplementation

from twisted.trial import unittest

from twisted.python.logger._observer import ILogObserver
from twisted.python.logger._file import FileLogObserver
from twisted.python.logger._file import textFileLogObserver



class FileLogObserverTests(unittest.TestCase):
    """
    Tests for L{FileLogObserver}.
    """

    def test_interface(self):
        """
        L{FileLogObserver} is an L{ILogObserver}.
        """
        try:
            fileHandle = StringIO()
            observer = FileLogObserver(fileHandle, lambda e: unicode(e))
            try:
                verifyObject(ILogObserver, observer)
            except BrokenMethodImplementation as e:
                self.fail(e)

        finally:
            fileHandle.close()


    def test_observeWrites(self):
        """
        L{FileLogObserver} writes to the given file when it observes events.
        """
        try:
            fileHandle = StringIO()
            observer = FileLogObserver(fileHandle, lambda e: unicode(e))
            event = dict(x=1)
            observer(event)
            self.assertEquals(fileHandle.getvalue(), unicode(event))

        finally:
            fileHandle.close()


    def test_observeFlushes(self):
        """
        L{FileLogObserver} calles C{flush()} on the output file when it
        observes an event.
        """

        class DummyFile(object):
            def __init__(self):
                self.flushes = 0

            def write(self, data):
                pass

            def flush(self):
                self.flushes += 1

            def close(self):
                pass

        try:
            fileHandle = DummyFile()
            observer = FileLogObserver(fileHandle, lambda e: unicode(e))
            event = dict(x=1)
            observer(event)
            self.assertEquals(fileHandle.flushes, 1)

        finally:
            fileHandle.close()



class textFileLogObserverTests(unittest.TestCase):
    """
    Tests for L{textFileLogObserver}.
    """

    def test_returnsFileLogObserver(self):
        """
        L{textFileLogObserver} returns a L{FileLogObserver}.
        """
        fileHandle = StringIO()
        try:
            observer = textFileLogObserver(fileHandle)
            self.assertIsInstance(observer, FileLogObserver)
        finally:
            fileHandle.close()


    def test_outFile(self):
        """
        Returned L{FileLogObserver} has the correct outFile.
        """
        fileHandle = StringIO()
        try:
            observer = textFileLogObserver(fileHandle)
            self.assertIdentical(observer._outFile, fileHandle)
        finally:
            fileHandle.close()


    def test_timeFormat(self):
        """
        Returned L{FileLogObserver} has the correct outFile.
        """
        fileHandle = StringIO()
        try:
            observer = textFileLogObserver(fileHandle, timeFormat=u"%f")
            observer(dict(log_format=u"XYZZY", log_time=1.23456))
            self.assertEquals(fileHandle.getvalue(), u"234560 [-#-] XYZZY\n")
        finally:
            fileHandle.close()
