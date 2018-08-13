

class FakeLog:

    def warning(self, msg):
        print("Warning: {}".format(msg))

    def error(self, msg):
        print("Error: {}".format(msg))

    def info(self, msg):
        print("Info: {}".format(msg))

    def debug(self, msg):
        print("Debug: {}".format(msg))
