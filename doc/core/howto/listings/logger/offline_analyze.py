from twisted.python.logger import (
    eventsFromJSONLogFile
)
import io
from analyze import analyze

for event in eventsFromJSONLogFile(io.open("log.json")):
    analyze(event)
