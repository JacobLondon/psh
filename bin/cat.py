import os
import sys

if len(sys.argv) <= 1:
    exit(1)

nflag = False
filename = None

for i, arg in enumerate(sys.argv):
    if not arg.startswith("-"):
        if i > 0:
            filename = arg
        continue

    for ch in arg:
        if ch == 'n':
            nflag = True

if filename is None:
    print("cat: No file specified", file=sys.stderr)
    exit(1)

try:
    with open(filename, "r") as fp:
        if nflag:
            for i, line in enumerate(fp.readlines()):
                print(i, '\t', line, end='', flush=True)
        else:
            for line in fp.readlines():
                print(line, end='', flush=True)

except Exception as e:
    print(e, file=sys.stderr)
    exit(1)
exit(0)
