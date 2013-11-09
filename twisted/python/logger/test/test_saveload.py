# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for L{twisted.python.logger._saveload}.
"""

from twisted.python.compat import unicode

from twisted.trial.unittest import TestCase
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
        Any L{bytes} objects will be saved as latin-1 so they can be faithfully
        re-loaded.
        """


