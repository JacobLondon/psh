import os
import shutil
import sys

argc = len(sys.argv)
columns, lines = shutil.get_terminal_size((80, 20))

def supports_color():
    """
    Returns True if the running system's terminal supports color, and False
    otherwise.
    """
    plat = sys.platform
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or 'ANSICON' in os.environ)
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    return supported_platform and is_a_tty

if supports_color():
    GREEN = "\u001b[32m"
    RESET = "\u001b[0m"
else:
    GREEN = ""
    RESET = ""

def show(content, directory):
    if os.path.isdir(f"{directory}/{content}"):
        print(f"{GREEN}{content}{RESET}", end='')
    else:
        print(content, end='')

def horizontal(contents, cwd):
    widest = max(len(content) for content in contents) + 1
    eachrow = columns // widest

    count = 0
    for i, content in enumerate(contents):
        show(content, cwd)
        print(' ' * (widest - len(content)), end='')
        if i % eachrow == eachrow - 1:
            print()
        count = i
    if count % (eachrow - 1) != 0:
        print()

def vertical(contents, cwd):
    for content in contents:
        show(content, cwd)
        print()

if argc == 1:
    contents = os.listdir(os.getcwd())
    contents = filter(lambda x: not x.startswith('.'), contents)
    contents = sorted(contents)
    horizontal(contents, os.getcwd())
    exit(0)

aflag = False
lflag = False
directory = os.getcwd()

for i, arg in enumerate(sys.argv[1:]):
    if not arg.startswith("-"):
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
    vertical(contents, directory)
else:
    horizontal(contents, directory)

exit(0)
