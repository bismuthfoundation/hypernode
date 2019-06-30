# From https://stackoverflow.com/questions/38856410/monitoring-the-asyncio-event-loop

import logging
import asyncio


class EventLoopDelayMonitor:

    def __init__(self, loop=None, start=True, interval=1, logger=None):
        self._stopped = True
        self._interval = interval
        self._log = logger or logging.getLogger(__name__)
        self._loop = loop or asyncio.get_event_loop()
        if start:
            self.start()

    def run(self):
        self._loop.call_later(self._interval, self._handler, self._loop.time())

    def _handler(self, start_time):
        latency = (self._loop.time() - start_time) - self._interval
        self._log.info('EventLoop delay %.4f', latency)
        if not self.is_stopped():
            self.run()

    def is_stopped(self):
        return self._stopped

    def start(self):
        self._stopped = False
        self.run()

    def stop(self):
        self._stopped = True
