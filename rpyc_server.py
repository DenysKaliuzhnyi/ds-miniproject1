import rpyc
import sys
import datetime
import _thread
import time
from operator import itemgetter
from rpyc.utils.server import ThreadedServer
import datetime


class CriticalSection:
    def __init__(self, hold_time=5):
        self.hold_time = hold_time
        self._status = "FREE"

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, val):
        assert val in ("OCCUPIED", "FREE"), "CS status must be either OCCUPIED or FREE"
        self._status = val

    def request(self, process):
        process.status = "WANTED"
        if self.status == "FREE":
            self.status = "OCCUPIED"
            process.status = "HELD"

            time.sleep(self.hold_time)

            self.status = "FREE"
            process.status = "DO-NOT-WANT"
            process.reset_tick()


processes = []
system_start = datetime.datetime.now()
cs = CriticalSection()


class MonitorService(rpyc.Service):
    def on_connect(self, conn):
        print("\nconnected on {}".format(system_start))

    def on_disconnect(self, conn):
        print("disconnected on {}\n".format(system_start))

    def exposed_setup(self, N: int):
        """create and start N processes"""
        for i in range(N):
            time_ = (0,) * N  # setup initial Lamport time to zeros
            p = Process(i, time_, time_out=5)
            processes.append(p)

        # start threads of all processes
        for p in processes:
            p.start()

    def exposed_list(self):
        for p in processes:
            print(p.id, p.status)

    def exposed_clock(self):
        for p in processes:
            print(p.id, p.time)


class Process:
    def __init__(self, id_: int, time_: tuple, time_out: int, status: str = "DO-NOT-WANT"):
        self.id = id_
        self.time = time_
        self.time_out = time_out
        self._status = status
        self.tick = None

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, val):
        assert val in ("DO-NOT-WANT", "WANTED", "HELD")
        self._status = val

    def reset_tick(self):
        self.tick = time.perf_counter()

    def run(self):
        self.reset_tick()  # benchmark to track real time passed
        while True:
            time.sleep(0.1)  # add small delay
            diff = time.perf_counter() - self.tick  # time passed
            if diff > self.time_out:
                cs.request(self)

    # starts a thread that runs the process
    def start(self):
        _thread.start_new_thread(self.run, ())


if __name__ == '__main__':
    t = ThreadedServer(MonitorService, port=18812)
    t.start()
