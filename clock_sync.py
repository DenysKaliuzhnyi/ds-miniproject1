import sys
import datetime
import _thread
import time
from operator import itemgetter

# global variables
processes = []
system_start = datetime.datetime.now()


class Process:
    def __init__(self, id, name, time):
        self.id = id
        self.name = name
        self.time = time
        self.elections = 0
        self.label = None
        self.time_start = time
        self.set_time = time
        self.alive = True

    # starts a thread that runs the process
    def start(self):
        _thread.start_new_thread(self.run, ())

    def kill(self):
        self.alive = False

    def run(self):
        # with 5 second interval, update clock
        while self.alive:
            time.sleep(5)
            self.update_clock()

    def update_clock(self, seconds=5):
        # delta = datetime.timedelta(seconds=seconds)
        # self.time = self.add_delta_to_time(delta, self.time)
        bully(processes)

        for p in processes:
            if p.label == "C":
                self.time = p.time
                break

    @staticmethod
    def add_delta_to_time(delta, time):
        return (datetime.datetime.combine(datetime.date(1,1,1), time) + delta).time()

    def __repr__(self):
        return ("Slave" if self.label == "S" else "Coordinator") + " with id " + str(self.id)

    def reset_time(self):
        self.time = self.time_start


def tick(running, processes):
    # program ticks evey second
    # to update the coordinator time
    # other processes update clock by Berkeley algorithm
    while running:
        time.sleep(1)
        for p in processes:
            #if p.coordinator and p.coordinator.id == p.id:
            if p.label=="C":
                system_time = datetime.datetime.now()
                # how much time passed since program started
                time_diff = system_time - system_start

                ct = p.set_time
                today = datetime.date.today()
                t = datetime.datetime(today.year, today.month,
                                      today.day, ct.hour, ct.minute, ct.second)
                nt = t + time_diff
                # update time based on difference
                p.time = datetime.time(nt.hour, nt.minute, nt.second)


def list(processes):
    # utility method to list proceeses
    for p in processes:
        print("%d, %s_%d" % (p.id, p.name, p.elections), end='')
        if p.label == 'C':
            print(' (Coordinator)')
        elif p.label == 'S':
            print()
        else:
            raise ValueError(f'p.label = {p.label}, but should be "C" or "S"')


def clock(processes):
    for p in processes:
        print("%s_%d," %
              (p.name, p.elections), p.time.strftime("%H:%M:%S"))


def kill(processes, id):
    for i, p in enumerate(processes):
        if p.id == id:
            label = p.label
            p.kill()
            processes.pop(i)

            if label == "C":
                for p in processes:
                    p.reset_time()
                bully(processes)
            break
    else:
        raise ValueError('Unknown process id')


def parse_lines(lines):
    # utility method to arse input
    result = []
    for l in lines:
        p = l.split(",")
        id = int(p[0].strip())
        name = p[1].strip().split("_")[0]
        time = p[2].strip(" apm").split(":")
        h = int(time[0])
        m = int(time[1])
        s = 0
        t = datetime.time(h, m, s)
        result.append([id, name, t])
    return result


def bully(processes):
    """"assign coordinator"""
    max_id = float("-inf")
    for p in processes:
        if p.id > max_id:
            max_id = p.id

    for p in processes:
        if p.id == max_id:
            p.label = "C"
        else:
            p.label = "S"


def main(fname):
    # main program function
    if fname:
        try:
            with open(fname) as f:
                lines = [line.rstrip('\n') for line in f.readlines()]
                lines = [line for line in lines if len(
                    line) > 0 and line[0].isdigit()]
                parsed = parse_lines(lines)
                ids = []
                for p in parsed:
                    if p[0] not in ids:
                        processes.append(Process(p[0], p[1], p[2]))
                        ids.append(p[0])
                    else:
                        print("[WARNING] Duplicate procees id %d discarded" % p[0])
        except:
            print("[ERROR] Failed to parse the input file.")
            print("Loading default test values.")
    else:
        print("[WARNING] No input file provided.")
        print("Loading default test values.")

    bully(processes)

    print("Commands: exit, list, clock, kill <id>")
    # start threads of all processes
    for p in processes:
        p.start()

    # start the main loop
    running = True

    # start a separate thread for system tick
    _thread.start_new_thread(tick, (running, processes))

    while running:
        inp = input().lower()
        cmd = inp.split(" ")

        command = cmd[0]

        if len(cmd) > 3:
            print("Too many arguments")

        # handle exit
        elif command == "exit":
            running = False

        # handle list
        elif command == "list":
            list(processes)

        # handle clock
        elif command == "clock":
            clock(processes)

        # handle kill
        elif command == "kill":
            kill(processes, id=int(cmd[1]))

        # handle unsupported command        
        else:
            print("Unsupported command:", inp)

    print("Program exited")


if __name__ == "__main__":
    main(sys.argv[1])


