import os
import shutil
import sys

if len(sys.argv) <= 1:
    exit(1)

try:
    if os.path.isfile(sys.argv[1]):
        os.remove(sys.argv[1])
    elif os.path.isdir(sys.argv[1]):
        shutil.rmtree(sys.argv[1])
except Exception as e:
    print(e)
    exit(1)
exit(0)
