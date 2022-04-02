import rpyc
import sys
import datetime
import _thread
import time
from operator import itemgetter
import argparse


def main(N, conn):
    conn.root.exposed_setup(N)

    print("Commands: list, clock, time_cs <t>, time_p <t>, exit")
    running = True
    while running:
        print ("Input the command:", end=' ')
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
            conn.root.list()

        # handle time_cs
        elif command == "time_cs":
            conn.root.time_cs(int(cmd[1]))

        # handle time_p
        elif command == "time_p":
            conn.root.time_p(int(cmd[1]))

        # handle clock
        elif command == "clock":
            conn.root.clock()

        # handle list
        elif command == "show_time_p":
            conn.root.show_time_p()

        # handle unsupported command
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
