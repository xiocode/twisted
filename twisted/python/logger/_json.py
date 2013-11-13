# -*- test-case-name: twisted.python.logger.test.test_json -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tools for saving and loading log events in a structured format.
"""

from twisted.python.logger._format import flattenEvent
from twisted.python.logger._file import FileLogObserver
from twisted.python.logger._levels import LogLevel
from twisted.python.constants import NamedConstant

from json import dumps, loads
from twisted.python.logger._levels import InvalidLogLevelError
from twisted.python.compat import unicode


def eventAsJSON(event):
    """
    Encode an event as JSON, flattening it if necessary to preserve as much
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
    def unpersistable(unencodable):
        if isinstance(unencodable, NamedConstant):
            return unicode(unencodable.name, "utf-8")
        else:
            return {"unpersistable": True}
    if bytes is str:
        kw = dict(default=unpersistable,
                  encoding="charmap", skipkeys=True)
    else:
        def default(unencodable):
            if isinstance(unencodable, bytes):
                return unencodable.decode("charmap")
            return unpersistable(unencodable)
        kw = dict(default=default, skipkeys=True)
    flattenEvent(event)
    result = dumps(event, **kw)
    if not isinstance(result, unicode):
        return unicode(result, "utf-8", "replace")
    return result



def eventFromJSON(eventText):
    """
    Decode a log event from JSON.

    @param eventText: The output of a previous call to L{eventAsJSON}
    @type eventText: L{unicode}

    @return: A reconstructed version of the log event.
    @rtype: L{dict}
    """
    loaded = loads(eventText)
    if "log_level" in loaded:
        try:
            loaded["log_level"] = LogLevel.levelWithName(loaded["log_level"])
        except InvalidLogLevelError:
            loaded["log_level_name"] = loaded.pop("log_level")
    return loaded



def jsonFileLogObserver(outFile):
    """
    Create a L{FileLogObserver} that emits JSON lines to a specified (writable)
    file-like object.

    @param outFile: A file-like object.  Ideally one should be passed which
        accepts L{unicode} data.  Otherwise, UTF-8 L{bytes} will be used.
    @type outFile: L{io.IOBase}

    @return: A file log observer.
    @rtype: L{FileLogObserver}
    """
    # FIXME: test coverage
    return FileLogObserver(outFile, lambda event: eventAsJSON(event) + u"\n")



def eventsFromJSONLogFile(inFile):
    """
    Load events from a file previously saved with jsonFileLogObserver.

    @param inFile: A (readable) file-like object.  Data read from L{inFile}
        should be L{unicode} or UTF-8 L{bytes}.
    @type inFile: iterable of lines

    @return: an iterable of log events
    @rtype: iterable of L{dict}
    """
    for line in inFile:
        yield eventFromJSON(line)
