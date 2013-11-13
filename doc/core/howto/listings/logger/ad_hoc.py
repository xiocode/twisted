from twisted.python.logger import Logger
import io

class AdHoc(object):
    log = Logger(namespace="ad_hoc")

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def logMessage(self):
        self.log.info("message from {log_source} "
                      "where a is {log_source.a} and b is {log_source.b}")

if __name__ == '__main__':
    from twisted.python.logger import jsonFileLogObserver
    AdHoc.log.observer.addObserver(
        jsonFileLogObserver(io.open("log.json", "a"))
    )
    AdHoc(3, 4).logMessage()
