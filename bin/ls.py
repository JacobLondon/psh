#
# TODO
# Add '/' after directory names
# Sort items into organized columns for horizontal
#

import os
import sys

argc = len(sys.argv)

def horizontal(contents):
    for content in contents:
        print(content, end="    ")
    print()

def vertical(contents):
    for content in contents:
        print("   ", content)

if argc == 1:
    contents = os.listdir(os.getcwd())
    contents = filter(lambda x: not x.startswith('.'), contents)
    contents = sorted(contents)
    horizontal(contents)

else:
    aflag = False
    lflag = False
    directory = os.getcwd()

    for i, arg in enumerate(sys.argv):
        if not arg.startswith("-"):
            if i > 0:
                directory = arg
            continue

        for ch in arg:
            if ch == 'a':
                aflag = True
            elif ch == 'l':
                lflag = True

    try:
        contents = os.listdir(directory)
    except Exception as e:
        print(e)
        exit(1)

    if not aflag:
        contents = filter(lambda x: not x.startswith('.'), contents)
    contents = sorted(contents)

    if lflag:
        vertical(contents)
    else:
        horizontal(contents)

exit(0)
