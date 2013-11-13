from twisted.python.logger import (
    eventsFromStructuredLogFile, textFileLogObserver)
import sys, io
output = textFileLogObserver(sys.stdout)
for event in eventsFromStructuredLogFile(io.open("log.json")):
    output(event)
