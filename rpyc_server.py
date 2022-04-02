import rpyc
import sys
import datetime
import _thread
import time
from operator import itemgetter
from rpyc.utils.server import ThreadedServer
import datetime
import random


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
        print(f'Received command from client: list')

        for p in processes:
            print(p.id, p.status)

    def exposed_clock(self):
        print(f'Received command from client: clock')
        for p in processes:
            print(p.id, p.time)

    def exposed_time_cs(self, t):
        '''
        sets the time to the critical section
        assigns a time-out for possessing the critical section
        the time-out is selected randomly from the interval (10, t)
        By default: each process can have the critical section for 10 second
        E.g.: $ time-cs 20, sets the interval for time-out as [10, 20] – in seconds.
        '''
        print(f'Received command from client: time_cs {t}')
        pass

    def exposed_time_p(self, t):
        '''
        sets the time-out interval for all processes [5, t],
        meaning that each process takes its timeout randomly from the interval.
        This time is used by each process to move between states.
        E.g.: a process changes from DO-NOT-WANT to WANTED after a time-out,
        e.g., after 5 seconds.
        Notice here that the process cannot go back to DO-NOT-WANT, and can only proceed to HELD once is authorized by
all the nodes to do so. After the process has going through the steps of accessing and releasing the CS,
then it goes back to the DO-NOT-WANT, where the time-out can be once again trigger to request access
to the CS.

        '''
        print(f'Received command from client: time_p {t}')
        for p in processes:
            time_p = random.randint(5, t)
            p.time_out = time_p


    def exposed_show_time_p(self):
        print(f'Received command from client: show_time_p')
        for p in processes:
            print(f'P{p.id} time_out: {p.time_out}')


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
