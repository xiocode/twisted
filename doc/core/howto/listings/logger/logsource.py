from twisted.python.logger import Logger

class MyObject(object):
    log = Logger()

    def __init__(self, value):
        self.value = value

    def doSomething(self, something):
        self.log.critical(
            "object with value {log_source.value} doing {something}",
            something=something
        )

MyObject(7).doSomething("a task")
