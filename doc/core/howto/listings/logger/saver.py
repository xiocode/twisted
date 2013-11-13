from twisted.python.logger import structuredFileLogObserver, Logger
import io
log = Logger(observer=structuredFileLogObserver(io.open("log.json", "a")),
             namespace="saver")
def loggit(values):
    log.info("Some values: {values!r}", values=values)
loggit([1234, 5678])
loggit([9876, 5432])
