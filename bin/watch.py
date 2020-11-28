import signal
import sys
import time

if len(sys.argv) <= 1:
    exit(1)

signal.signal(signal.SIGINT, lambda sig, frame: exit(0))

while True:
    try:
        with open(sys.argv[1], "r") as fp:
            print(fp.read())
    except:
        pass
    time.sleep(0.5)
