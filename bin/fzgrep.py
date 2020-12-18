# fuzzy grep

import sys
import os

if len(sys.argv) < 3:
    print("Invalid args", file=sys.stderr)
    exit(1)

term = sys.argv[1]
filename = sys.argv[2]

search = ''
for letter in term:
    search += '%s.*' % (letter)

thisdir = os.path.dirname(os.path.realpath(__file__))
command = '%s/grep.exe -n %s %s' % (thisdir, search, filename)
exit(os.system(command))
