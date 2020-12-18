# fuzzy find

import os
import sys
import re

if len(sys.argv) < 2:
    exit(1)

def recurse(curdir: str):
    filenames = os.listdir(curdir)
    for filename in filenames:
        if os.path.isdir(filename):
            nextdir = '%s%s%s' % (curdir, os.sep, filename)
            thisdir = curdir
            os.chdir(nextdir)
            yield from recurse(nextdir)
            os.chdir(thisdir)
        else:
            yield '%s%s%s' % (curdir, os.sep, filename)

expr = '.*' + ''.join(['%s.*' % letter for letter in sys.argv[1]])
program = re.compile(expr)
filenames = iter(recurse(os.getcwd()))

for filename in filenames:
    if program.match(filename):
        print(filename)

exit(0)
