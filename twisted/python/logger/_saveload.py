# -*- test-case-name: twisted.python.logger.test.test_saveload -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tools for saving and loading log events in a structured format.
"""

from twisted.python.logger._format import flattenEvent
from twisted.python.logger._file import FileLogObserver
from json import dumps, loads
from twisted.python.compat import unicode


def saveEventJSON(event):
    """
    Save an event as JSON, flattening it if necessary to preserve as much
    structure as possible.

    Not all structure from the log event will be preserved when it is
    serialized

    @param event: A log event dictionary.
    @type event: L{dict} with arbitrary keys and values

    @return: A string of the serialized JSON; note that this will contain no
        newline characters, and may thus safely be stored in a line-delimited
        file.
    @rtype: L{unicode}
    """
    if bytes is str:
        kw = dict(default=lambda x: {"unpersistable": True},
                  encoding="charmap", skipkeys=True)
    else:
        def default(unencodable):
            if isinstance(unencodable, bytes):
                return unencodable.decode("charmap")
            else:
                return {"unpersistable": True}
        kw = dict(default=default, skipkeys=True)
    flattenEvent(event)
    result = dumps(event, **kw)
    if not isinstance(result, unicode):
        return unicode(result, 'utf-8', 'replace')
    return result



def loadEventJSON(eventText):
    """
    Load a log event from JSON.

    @param eventText: The output of a previous call to L{saveEventJSON}
    @type eventText: L{unicode}

    @return: A reconstructed version of the log event.
    @rtype: L{dict}
    """
    return loads(eventText)
