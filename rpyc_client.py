import rpyc
import argparse


def main(N, conn):
    conn.root.exposed_setup(N)

    print("Commands: exit, list, clock, time-cs <sec>, time-p <sec>")
    running = True
    while running:
        inp = input().lower()
        cmd = inp.split(" ")

        command = cmd[0]

        if len(cmd) > 2:
            print("Too many arguments")
        elif command == "exit":
            running = False
        elif command == "list":
            conn.root.list()
        elif command == "clock":
            conn.root.clock()
        elif command == "time-cs":
            conn.root.time_cs(float(cmd[1]))
        elif command == "time-p":
            conn.root.time_p(float(cmd[1]))
        else:
            print("Unsupported command:", inp)

    print("Program exited")


parser = argparse.ArgumentParser()
parser.add_argument('-N', type=int, required=True, help='number of processes to create')
parser.add_argument('--server', type=str, default='localhost', help='host')
args = parser.parse_args()
assert args.N > 0, "N must be at least 1"

conn = rpyc.connect(args.server, 18812)
main(args.N, conn)
