from .Worker import Worker
from utils.Utils import *

class WorkerQueue(object):
    def __init__(self):
        self.queue = {}
        return

    def ready(self, worker):
        self.queue.pop(worker.address, None)
        self.queue[worker.address] = worker
        return

    def purge(self):
        """Look for & kill expired workers."""
        # t = time.time()
        t = current_milli_time()
        # print("Killing expired workers at time: %s" % t)
        expired = []
        for address, worker in self.queue.items():
            # print(address, worker.last_alive)
            if t > worker.last_alive:  # Worker expired
                expired.append(address)

        for address in expired:
            print("W: Idle worker expired: %s" % address)
            self.queue.pop(address, None)

        return

    def next(self):
        address, worker = self.queue.popitem()
        return address
