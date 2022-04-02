import rpyc
import time
import random
import _thread
import datetime
from rpyc.utils.server import ThreadedServer


class CriticalSection:
    def __init__(self):
        self.t_low = 10
        self.t_up = 10

    def possess(self):
        """" simulate resource possession"""
        time.sleep(self.gen_hold_time)  # simulate possession

    @property
    def gen_hold_time(self):
        """generate random value within [t_up, t_low] range"""
        return random.random() * (self.t_up - self.t_low) + self.t_low


class Message:
    def __init__(self, resource_name: str, process_id: int, logical_time: int):
        self.resource_name = resource_name
        self.process_id = process_id
        self.logical_time = logical_time

    def __repr__(self):
        return f"Message(resource_name={self.resource_name}, process_id={self.process_id}, logical_time={self.logical_time})"


system_start = datetime.datetime.now()
processes = {}  # list to store all the processes
cs = CriticalSection()  # one critical section to compete for
clock = 0  # global monotonic clock (counter)


class Process:
    def __init__(self, id_: int):
        self.id = id_

        # default variables
        self.logical_time = clock  # global variable
        self.t_low = 5
        self.t_up = 5
        self.status = "DO-NOT-WANT"

        # variables to be set later
        self.tick = None  # to track time passed for time-out
        self.responses = {}  # dictionary of responses for other processes

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, val):
        assert val in ("DO-NOT-WANT", "WANTED", "HELD")
        self._status = val

    @property
    def gen_time_out(self):
        """generate random value within [t_up, t_low] range"""
        return random.random() * (self.t_up - self.t_low) + self.t_low

    def reset_tick(self):
        self.tick = time.perf_counter()

    def broadcast(self):
        """send the messages to all the other processes, return True if all responds OK"""
        # increment monotonic clock and assign time to current process
        global clock
        clock += 1
        self.logical_time = clock

        # broadcast message to other processes are save responses
        msg = Message("CS", self.id, self.logical_time)
        for p in processes.values():
            if p.id != self.id:
                resp = p.request(msg)
                self.responses[p.id] = resp

    def request(self, msg):
        """generate response to a request"""
        if self.status == "DO-NOT-WANT" or (self.status == "WANTED" and msg.logical_time < self.logical_time):
            return "OK"  # reply message

    def run(self):
        self.reset_tick()  # benchmark to track real time passed
        while True:
            diff = time.perf_counter() - self.tick  # time passed
            if diff > self.gen_time_out:
                # switch status and send messages
                self.status = "WANTED"
                self.broadcast()

                # wait until all the reply messages to be "OK"
                responses = self.responses.values()
                while not all(map(lambda r: r == "OK", responses)):
                    responses = self.responses.values()

                # possession
                self.status = "HELD"
                cs.possess()
                self.status = "DO-NOT-WANT"

                # send reply messages to deferred requests
                for p in processes.values():
                    if self.id != p.id:
                        p.responses[self.id] = "OK"

                self.reset_tick()

    # starts a thread that runs the process
    def start(self):
        _thread.start_new_thread(self.run, ())


class MonitorService(rpyc.Service):
    def on_connect(self, conn):
        print("\nconnected on {}".format(system_start))

    def on_disconnect(self, conn):
        print("disconnected on {}\n".format(system_start))

    def exposed_setup(self, N: int):
        """create and start N processes"""
        for i in range(N):
            p = Process(i)
            processes[i] = p

        # start threads of all processes
        for p in processes.values():
            p.start()

    def exposed_list(self):
        for p in processes.values():
            print(f'{datetime.datetime.now()} - Process {p.id} status: {p.status}')
        print()

    def exposed_clock(self):
        for p in processes.values():
            print(f'Process {p.id} time {p.logical_time}')

    def exposed_time_cs(self, t: float):
        cs.t_up = t

    def exposed_time_p(self, t: float):
        for p in processes.values():
            p.t_up = t


if __name__ == '__main__':
    t = ThreadedServer(MonitorService, port=18812)
    t.start()
