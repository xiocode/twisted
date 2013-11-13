import sys
import io
from twisted.python.logger import (
    eventsFromStructuredLogFile, textFileLogObserver
)

output = textFileLogObserver(sys.stdout)

for event in eventsFromStructuredLogFile(io.open("log.json")):
    output(event)
