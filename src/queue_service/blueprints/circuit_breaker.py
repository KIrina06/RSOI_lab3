import time
import random

CIRCUIT_BREAKER_BAN_TIME = 60 * 60
CIRCUIT_BREAKER_CONNECT_CHANCE = 25
CIRCUIT_BREAKER_CONNECT_TRIES = 10


class CircuitBreaker:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(CircuitBreaker, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.urls_data = {}

    def try_connect(self, url):
        if url not in self.urls_data.keys():
            self.urls_data[url] = [0, time.time()]
            return True
        else:
            if self.urls_data[url][0] == -1:
                if self.urls_data[url][1] < time.time():
                    return False
                else:
                    if random.randint(0, 100) >= CIRCUIT_BREAKER_CONNECT_CHANCE:
                        return False
        return True

    def connection_error(self, url):
        if self.urls_data[url][0] == -1:
            self.urls_data[url][1] = time.time() + CIRCUIT_BREAKER_BAN_TIME
            return

        self.urls_data[url][0] += 1
        if self.urls_data[url][0] >= CIRCUIT_BREAKER_CONNECT_TRIES:
            self.urls_data[url][0] = -1
            self.urls_data[url][1] = time.time() + CIRCUIT_BREAKER_BAN_TIME

    def connection_successful(self, url):
        self.urls_data[url][0] = 0

