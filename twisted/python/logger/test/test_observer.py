# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Test cases for L{twisted.python.logger._observer}.
"""

from zope.interface.verify import verifyObject, BrokenMethodImplementation

from twisted.trial import unittest

from twisted.python.logger._logger import Logger
from twisted.python.logger._observer import ILogObserver
from twisted.python.logger._observer import LogPublisher
from twisted.python.logger._util import formatTrace



class LogPublisherTests(unittest.TestCase):
    """
    Tests for L{LogPublisher}.
    """

    def test_interface(self):
        """
        L{LogPublisher} is an L{ILogObserver}.
        """
        publisher = LogPublisher()
        try:
            verifyObject(ILogObserver, publisher)
        except BrokenMethodImplementation as e:
            self.fail(e)


    def test_observers(self):
        """
        L{LogPublisher.observers} returns the observers.
        """
        o1 = lambda e: None
        o2 = lambda e: None

        publisher = LogPublisher(o1, o2)
        self.assertEquals(set((o1, o2)), set(publisher._observers))


    def test_addObserver(self):
        """
        L{LogPublisher.addObserver} adds an observer.
        """
        o1 = lambda e: None
        o2 = lambda e: None
        o3 = lambda e: None

        publisher = LogPublisher(o1, o2)
        publisher.addObserver(o3)
        self.assertEquals(set((o1, o2, o3)), set(publisher._observers))


    def test_addObserverNotCallable(self):
        """
        L{LogPublisher.addObserver} refuses to add an observer that's
        not callable.
        """
        publisher = LogPublisher()
        self.assertRaises(TypeError, publisher.addObserver, object())


    def test_removeObserver(self):
        """
        L{LogPublisher.removeObserver} removes an observer.
        """
        o1 = lambda e: None
        o2 = lambda e: None
        o3 = lambda e: None

        publisher = LogPublisher(o1, o2, o3)
        publisher.removeObserver(o2)
        self.assertEquals(set((o1, o3)), set(publisher._observers))


    def test_removeObserverNotRegistered(self):
        """
        L{LogPublisher.removeObserver} removes an observer that is not
        registered.
        """
        o1 = lambda e: None
        o2 = lambda e: None
        o3 = lambda e: None

        publisher = LogPublisher(o1, o2)
        publisher.removeObserver(o3)
        self.assertEquals(set((o1, o2)), set(publisher._observers))


    def test_fanOut(self):
        """
        L{LogPublisher} calls its observers.
        """
        event = dict(foo=1, bar=2)

        events1 = []
        events2 = []
        events3 = []

        o1 = lambda e: events1.append(e)
        o2 = lambda e: events2.append(e)
        o3 = lambda e: events3.append(e)

        publisher = LogPublisher(o1, o2, o3)
        publisher(event)
        self.assertIn(event, events1)
        self.assertIn(event, events2)
        self.assertIn(event, events3)


    def test_observerRaises(self):
        """
        Observer raises an exception during fan out: a failure should be
        logged, but not re-raised.  Life goes on.
        """
        event = dict(foo=1, bar=2)
        exception = RuntimeError("ARGH! EVIL DEATH!")

        events = []

        def observer(event):
            shouldRaise = not events
            events.append(event)
            if shouldRaise:
                raise exception

        collector = []

        publisher = LogPublisher(observer, collector.append)
        publisher(event)

        # Verify that the observer saw my event
        self.assertIn(event, events)

        # Verify that the observer raised my exception
        errors = [
            e["log_failure"] for e in collector
            if "log_failure" in e
        ]
        self.assertEquals(len(errors), 1)
        self.assertIdentical(errors[0].value, exception)
        # Make sure the exceptional observer does not receive its own error.
        self.assertEquals(len(events), 1)


    def test_observerRaisesAndLoggerHatesMe(self):
        """
        Observer raises an exception during fan out and the publisher's Logger
        pukes when the failure is reported.  Exception should still not
        propagate back to the caller.
        """

        event = dict(foo=1, bar=2)
        exception = RuntimeError("ARGH! EVIL DEATH!")

        def observer(event):
            raise RuntimeError("Sad panda")

        class GurkLogger(Logger):
            def failure(self, *args, **kwargs):
                raise exception

        publisher = LogPublisher(observer)
        publisher.log = GurkLogger()
        publisher(event)

        # Here, the lack of an exception thus far is a success, of sorts


    def test_trace(self):
        """
        Tracing keeps track of forwarding done by the publisher.
        """
        publisher = LogPublisher()

        event = dict(log_trace=[])

        o1 = lambda e: None

        def o2(e):
            self.assertIdentical(e, event)
            self.assertEquals(
                e["log_trace"],
                [
                    (publisher, o1),
                    (publisher, o2),
                    # Event hasn't been sent to o3 yet
                ]
            )

        def o3(e):
            self.assertIdentical(e, event)
            self.assertEquals(
                e["log_trace"],
                [
                    (publisher, o1),
                    (publisher, o2),
                    (publisher, o3),
                ]
            )

        publisher.addObserver(o1)
        publisher.addObserver(o2)
        publisher.addObserver(o3)
        publisher(event)


    def test_formatTrace(self):
        """
        Format trace as string.
        """
        event = dict(log_trace=[])

        o1 = lambda e: None
        o2 = lambda e: None
        o3 = lambda e: None
        o4 = lambda e: None
        o5 = lambda e: None

        o1.name = "root/o1"
        o2.name = "root/p1/o2"
        o3.name = "root/p1/o3"
        o4.name = "root/p1/p2/o4"
        o5.name = "root/o5"

        def testObserver(e):
            self.assertIdentical(e, event)
            trace = formatTrace(e["log_trace"])
            self.assertEquals(
                trace,
                (
                    u"{root} ({root.name})\n"
                    u"  -> {o1} ({o1.name})\n"
                    u"  -> {p1} ({p1.name})\n"
                    u"    -> {o2} ({o2.name})\n"
                    u"    -> {o3} ({o3.name})\n"
                    u"    -> {p2} ({p2.name})\n"
                    u"      -> {o4} ({o4.name})\n"
                    u"  -> {o5} ({o5.name})\n"
                    u"  -> {oTest}\n"
                ).format(
                    root=root,
                    o1=o1, o2=o2, o3=o3, o4=o4, o5=o5,
                    p1=p1, p2=p2,
                    oTest=oTest
                )
            )
        oTest = testObserver

        p2 = LogPublisher(o4)
        p1 = LogPublisher(o2, o3, p2)

        p2.name = "root/p1/p2/"
        p1.name = "root/p1/"

        root = LogPublisher(o1, p1, o5, oTest)
        root.name = "root/"
        root(event)
