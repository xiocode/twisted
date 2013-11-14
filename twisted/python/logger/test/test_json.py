# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for L{twisted.python.logger._json}.
"""

from twisted.python.compat import unicode

from twisted.trial.unittest import TestCase
from twisted.python.logger import formatEvent, LogLevel
from twisted.python.logger._format import extractField
from twisted.python.logger._json import eventAsJSON, eventFromJSON



def savedJSONInvariants(testCase, savedJSON):
    """
    Assert a few things about the result of L{eventAsJSON}, then return it.

    @param testCase: The L{TestCase} with which to perform the assertions.
    @type testCase: L{TestCase}

    @param savedJSON: The result of L{eventAsJSON}.
    @type savedJSON: L{unicode} (we hope)

    @return: C{savedJSON}
    @rtype: L{unicode}

    @raise AssertionError: If any of the preconditions fail.
    """
    testCase.assertIsInstance(savedJSON, unicode)
    testCase.assertEquals(savedJSON.count("\n"), 0)
    return savedJSON



class SaveLoadTests(TestCase):
    """
    Tests for loading and saving log events.
    """

    def savedEventJSON(self, event):
        return savedJSONInvariants(self, eventAsJSON(event))


    def test_simpleSaveLoad(self):
        """
        Saving and loading an empty dictionary results in an empty dictionary.
        """
        self.assertEquals(eventFromJSON(self.savedEventJSON({})), {})


    def test_saveLoad(self):
        """
        Saving and loading a dictionary with some simple values in it results
        in those same simple values in the output; according to JSON's rules,
        though, all dictionary keys must be L{unicode} and any non-L{unicode}
        keys will be converted.
        """
        self.assertEquals(
            eventFromJSON(self.savedEventJSON({1: 2, u"3": u"4"})),
            {u"1": 2, u"3": u"4"}
        )


    def test_saveUnPersistable(self):
        """
        Saving and loading an object which cannot be represented in JSON will
        result in a placeholder.
        """
        self.assertEquals(
            eventFromJSON(self.savedEventJSON({u"1": 2, u"3": object()})),
            {u"1": 2, u"3": {u"unpersistable": True}}
        )


    def test_saveNonASCII(self):
        """
        Non-ASCII keys and values can be saved and loaded.
        """
        self.assertEquals(
            eventFromJSON(self.savedEventJSON(
                {u"\u1234": u"\u4321", u"3": object()}
            )),
            {u"\u1234": u"\u4321", u"3": {u"unpersistable": True}}
        )


    def test_saveBytes(self):
        """
        Any L{bytes} objects will be saved as if they are latin-1 so they can
        be faithfully re-loaded.
        """
        def asbytes(x):
            if bytes is str:
                return b"".join(map(chr, x))
            else:
                return bytes(x)

        inputEvent = {"hello": asbytes(range(255))}
        if bytes is not str:
            # On Python 3, bytes keys will be skipped by the JSON encoder. Not
            # much we can do about that.  Let's make sure that we don't get an
            # error, though.
            inputEvent.update({b"skipped": "okay"})
        self.assertEquals(
            eventFromJSON(self.savedEventJSON(inputEvent)),
            {u"hello": asbytes(range(255)).decode("charmap")}
        )


    def test_saveUnPersistableThenFormat(self):
        """
        Saving and loading an object which cannot be represented in JSON, but
        has a string representation which I{can} be saved as JSON, will result
        in the same string formatting; any extractable fields will retain their
        data types.
        """
        class reprable(object):
            def __init__(self, value):
                self.value = value

            def __repr__(self):
                return("reprable")

        inputEvent = {
            "log_format": "{object} {object.value}",
            "object": reprable(7)
        }
        outputEvent = eventFromJSON(self.savedEventJSON(inputEvent))
        self.assertEquals(formatEvent(outputEvent), "reprable 7")


    def test_extractingFieldsPostLoad(self):
        """
        L{extractField} can extract fields from an object that's been saved and
        loaded from JSON.
        """
        class obj(object):
            def __init__(self):
                self.value = 345

        inputEvent = dict(log_format="{object.value}", object=obj())
        loadedEvent = eventFromJSON(self.savedEventJSON(inputEvent))
        self.assertEquals(extractField("object.value", loadedEvent), 345)

        # The behavior of extractField is consistent between pre-persistence
        # and post-persistence events, although looking up the key directly
        # won't be:
        self.assertRaises(KeyError, extractField, "object", loadedEvent)
        self.assertRaises(KeyError, extractField, "object", inputEvent)


    def test_saveLoadLevel(self):
        """
        It's important that the C{log_level} key remain a
        L{twisted.python.constants.NamedConstant} object.
        """
        inputEvent = dict(log_level=LogLevel.warn)
        loadedEvent = eventFromJSON(self.savedEventJSON(inputEvent))
        self.assertIdentical(loadedEvent["log_level"], LogLevel.warn)


    def test_saveLoadUnknownLevel(self):
        """
        If a saved bit of JSON (let's say, from a future version of Twisted)
        were to persist a different log_level, it will resolve as None.
        """
        loadedEvent = eventFromJSON(
            '{"log_level": {"name": "other", '
            '"__class_uuid__": "02E59486-F24D-46AD-8224-3ACDF2A5732A"}}'
        )
        self.assertEquals(loadedEvent, dict(log_level=None))
