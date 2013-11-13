from twisted.python.logger import (
    eventsFromStructuredLogFile
)
import io
from analyze import analyze
for event in eventsFromStructuredLogFile(io.open("log.json")):
    analyze(event)
