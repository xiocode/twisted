from twisted.python.logger import eventsFromStructuredLogFile
import io
for event in eventsFromStructuredLogFile(io.open("log.json")):
    print(sum(event['values']))
