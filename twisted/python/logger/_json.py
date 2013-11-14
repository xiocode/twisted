# -*- test-case-name: twisted.python.logger.test.test_json -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tools for saving and loading log events in a structured format.
"""

import types
from json import dumps, loads
from uuid import UUID

from twisted.python.logger._format import flattenEvent
from twisted.python.logger._file import FileLogObserver
from twisted.python.logger._levels import LogLevel
from twisted.python.constants import NamedConstant

from twisted.python.compat import unicode
from twisted.python.failure import Failure

def saveFailure(obj):
    return dict(obj.__getstate__(),
                type=dict(__module__=obj.type.__module__,
                          __name__=obj.type.__name__))



def loadFailure(failureDict):
    if hasattr(Failure, "__new__"):
        f = Failure.__new__()
    else:
        def nativify(x):
            if isinstance(x, list):
                return map(nativify, x)
            elif isinstance(x, dict):
                return dict((nativify(k), nativify(v)) for k, v in x.items())
            elif isinstance(x, unicode):
                return x.encode("utf-8")
            else:
                return x
        failureDict = nativify(failureDict)
        f = types.InstanceType(Failure)
    typeInfo = failureDict['type']
    failureDict['type'] = type(typeInfo['__name__'], (), typeInfo)
    f.__dict__ = failureDict
    return f



classInfo = [
    (lambda level: (isinstance(level, NamedConstant) and
                    getattr(LogLevel, level.name, None) is level),
     UUID("02E59486-F24D-46AD-8224-3ACDF2A5732A"),
     lambda level: dict(name=level.name),
     lambda level: getattr(LogLevel, level['name'], None)),

    (lambda o: isinstance(o, Failure),
     UUID("E76887E2-20ED-49BF-A8F8-BA25CC586F2D"), saveFailure, loadFailure),
]



uuidToLoader = dict([(uuid, loader) for (predicate, uuid, saver, loader)
                     in classInfo])



def objectLoadHook(aDict):
    if '__class_uuid__' in aDict:
        return uuidToLoader[UUID(aDict['__class_uuid__'])](aDict)
    return aDict



def objectSaveHook(pythonObject):
    for (predicate, uuid, saver, loader) in classInfo:
        if predicate(pythonObject):
            result = saver(pythonObject)
            result['__class_uuid__'] = str(uuid)
            return result
    return {"unpersistable": True}



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
    if bytes is str:
        kw = dict(default=objectSaveHook, encoding="charmap", skipkeys=True)
    else:
        def default(unencodable):
            if isinstance(unencodable, bytes):
                return unencodable.decode("charmap")
            return objectSaveHook(unencodable)
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
    loaded = loads(eventText, object_hook=objectLoadHook)
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
