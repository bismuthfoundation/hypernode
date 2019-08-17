"""
A Simple cache decorator with TTL.

Usage :

@asyncttlcache
def myfunc(a):
    print "in func"
    return (a, datetime.now())

@asyncttlcache(ttl=1))
def cacheable_test(a):
    print "in cacheable test: "
    return (a, datetime.now())
"""

from time import time, sleep

__version__ = '0.0.1'


class TtlCache(object):
    """Not thread safe"""

    def __init__(self, *args, **kwargs):
        self.cached_function_responses = {}

    def __call__(self, ttl=0):
        def outer(func):
            def inner(*args, **kwargs):
                # Is some lock needed here to be thread safe?
                key = (func, str(args))
                if not ttl or key not in self.cached_function_responses or (
                        time() - self.cached_function_responses[key]['cached_time'] > ttl):
                    res = func(*args, **kwargs)
                    self.cached_function_responses[key] = {'data': res, 'cached_time': time()}
                    print("!! New cache !!", str(args))
                else:
                    print("!! Cache Hit !!", str(args))
                return self.cached_function_responses[key]['data']
            return inner

        return outer

    def purge(self):
        self.cached_function_responses = {}


class AsyncTtlCache(object):
    def __init__(self, *args, **kwargs):
        self.cached_function_responses = {}

    def __call__(self, ttl=0):
        def outer(func):
            async def inner(*args, **kwargs):
                # Is some lock needed here to be thread safe?
                key = (func, str(args))
                if not ttl or key not in self.cached_function_responses or (
                        time() - self.cached_function_responses[key]['cached_time'] > ttl):
                    res = await func(*args, **kwargs)
                    self.cached_function_responses[key] = {'data': res, 'cached_time': time()}
                    print("!! New cache !!", str(args))
                else:
                    print("!! Cache Hit !!", str(args))
                return self.cached_function_responses[key]['data']
            return inner

        return outer

    def purge(self):
        print("!! Cache purge !!")
        self.cached_function_responses = {}


ttlcache = TtlCache()
asyncttlcache = AsyncTtlCache()


# test

if __name__ == "__main__":
    @ttlcache(ttl=5)
    def t5(prefix):
        return "{}{}".format(prefix, time())

    @ttlcache(ttl=1)
    def t1(prefix):
        return "{}{}".format(prefix, time())


    for x in range(5):
        print("t5", t5(0), "t1", t1(0), "t1bis", t1(1))
        sleep(0.5)
    ttlcache.purge()
    for x in range(15):
        print("t5", t5(0), "t1", t1(0), "t1bis", t1(1))
        sleep(0.5)
