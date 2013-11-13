import io
from twisted.python.logger import eventsFromStructuredLogFile

for event in eventsFromStructuredLogFile(io.open("log.json")):
    print(sum(event["values"]))
