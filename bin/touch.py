import os
import sys

if len(sys.argv) <= 1:
    exit(1)

if os.path.exists(sys.argv[1]):
    print("touch: File already exists", file=sys.stderr)
    exit(1)

try:
    with open(sys.argv[1], "w+") as fp:
        fp.truncate(0)
except Exception as e:
    print(e, file=sys.stderr)
    exit(1)
exit(0)
