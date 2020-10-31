import os
import sys

if len(sys.argv) <= 1:
    exit(1)

if os.path.exists(sys.argv[1]):
    print("mkdir: Path already exists", file=sys.stderr)
    exit(1)

try:
    os.mkdir(sys.argv[1])
except Exception as e:
    print(e, file=sys.stderr)
    exit(1)
exit(0)
