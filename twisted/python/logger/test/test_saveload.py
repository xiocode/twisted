# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for L{twisted.python.logger._saveload}.
"""

from twisted.python.compat import unicode

from twisted.trial.unittest import TestCase
from twisted.python.logger import formatEvent
from twisted.python.logger._saveload import saveEventJSON, loadEventJSON

def savedJSONInvariants(testCase, savedJSON):
    """
    Assert a few things about the result of L{saveEventJSON}, then return it.

    @param testCase: The L{TestCase} with which to perform the assertions.
    @type testCase: L{TestCase}

    @param savedJSON: The result of L{saveEventJSON}.
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

    def test_simpleSaveLoad(self):
        """
        Saving and loading an empty dictionary results in an empty dictionary.
        """
        self.assertEquals(loadEventJSON(saveEventJSON({})), {})


    def test_saveLoad(self):
        """
        Saving and loading a dictionary with some simple values in it results
        in those same simple values in the output; according to JSON's rules,
        though, all dictionary keys must be L{unicode} and any non-L{unicode}
        keys will be converted.
        """
        self.assertEquals(loadEventJSON(saveEventJSON({1: 2, u'3': u'4'})),
                          {u'1': 2, u'3': u'4'})


    def test_saveUnPersistable(self):
        """
        Saving and loading an object which cannot be represented in JSON will
        result in a placeholder.
        """
        self.assertEquals(
            loadEventJSON(saveEventJSON({u"1": 2, u"3": object()})),
            {u'1': 2, u'3': {u'unpersistable': True}}
        )


    def test_saveNonASCII(self):
        """
        Non-ASCII keys and values can be saved and loaded.
        """
        self.assertEquals(
            loadEventJSON(saveEventJSON(
                {u"\u1234": u"\u4321", u"3": object()}
            )),
            {u'\u1234': u'\u4321', u'3': {u'unpersistable': True}}
        )


    def test_saveBytes(self):
        """
        Any L{bytes} objects will be saved as if they are latin-1 so they can
        be faithfully re-loaded.
        """
        def asbytes(x):
            if bytes is str:
                return b''.join(map(chr, x))
            else:
                return bytes(x)

        inputEvent = {"hello": asbytes(range(255))}
        if bytes is not str:
            # On Python 3, bytes keys will be skipped by the JSON encoder. Not
            # much we can do about that.  Let's make sure that we don't get an
            # error, though.
            inputEvent.update({b'skipped': 'okay'})
        self.assertEquals(
            loadEventJSON(saveEventJSON(inputEvent)),
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
        outputEvent = loadEventJSON(saveEventJSON(inputEvent))
        self.assertEquals(formatEvent(outputEvent), "reprable 7")
