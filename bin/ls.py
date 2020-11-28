import os
import shutil
import sys

argc = len(sys.argv)
columns, lines = shutil.get_terminal_size((80, 20))

def creation_date(path_to_file):
    import platform
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime

def date_string(path):
    import datetime
    ctime = creation_date(path)
    return datetime.datetime.utcfromtimestamp(ctime).strftime("%B %d %Y")

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
    if os.path.isdir(content):
        print(GREEN, content, RESET, end='', sep='')
    else:
        print(content, end='')

def horizontal(contents, cwd):
    widest = max(len(content) for content in contents) + 1
    eachrow = columns // widest
    while len(contents) % eachrow != 0:
        contents.append('')

    for i, content in enumerate(contents):
        show(content, cwd)
        print(' ' * (widest - len(content)), end='')
        if i % eachrow == eachrow - 1:
            print()

##
# _m modes
# _d dates
# _s sizes
#
def vertical(contents, cwd, _m=True, _d=True, _s=True):
    import stat

    # stats
    stats = []
    for content in contents:
        stats.append(os.stat(content))

    # modes
    modes = []
    for s in stats:
        modes.append(stat.filemode(s.st_mode))

    # sizes
    sizes = []
    gb = 2 ** 30
    mb = 2 ** 20
    kb = 2 ** 10
    for stat in stats:
        size = stat.st_size
        if size >= gb:
            size /= gb
            sizes.append("%.1lfGiB" % size)
        elif size >= mb:
            size /= mb
            sizes.append("%.1lfMiB" % size)
        elif size >= kb:
            size /= kb
            sizes.append("%.1lfKiB" % size)
        else:
            sizes.append("%d" % size)
    sizes_widest = max(len(size) for size in sizes)

    # dates
    dates = []
    for content in contents:
        dates.append(date_string(content))
    date_widest = max(len(date) for date in dates)

    # display
    for mode, date, size, content in zip(modes, dates, sizes, contents):
        if _m:
            print(mode, end=' ', sep='')
        if _d:
            print(' ' * (date_widest - len(date)), date, end=' ', sep='')
        if _s:
            print(' ' * (sizes_widest - len(size)), size, end=' ', sep='')
        show(content, cwd)
        print()

def getcontent(directory):
    try:
        contents = os.listdir(directory)
    except Exception as e:
        print(e, file=sys.stderr)
        exit(1)

    dirs = [x for x in contents if os.path.isdir(x)]
    files = [x for x in contents if not os.path.isdir(x)]
    dirs = list(sorted(dirs))
    files = list(sorted(files))

    contents = dirs + files
    return contents

directory = os.getcwd()
if argc == 1:
    os.chdir(directory)
    contents = getcontent(directory)
    contents = [x for x in contents if not x.startswith('.')]
    horizontal(contents, directory)
    exit(0)

aflag = False # all
lflag = False # do list
dflag = True # date list
sflag = True # size list
mflag = True # mode list
oflag = False # 0 list, only show content no details
for arg in sys.argv[1:]:
    if not arg.startswith("-"):
        directory = arg
        continue

    for ch in arg:
        if ch == 'a':
            aflag = True
        elif ch == 'l':
            lflag = True
        elif ch == 'd':
            dflag = False
        elif ch == 's':
            sflag = False
        elif ch == 'm':
            mflag = False
        elif ch == '0':
            dflag = False
            sflag = False
            mflag = False

os.chdir(directory)
contents = getcontent(directory)
if not aflag:
    contents = [x for x in contents if not x.startswith('.')]

if lflag:
    vertical(contents, directory, mflag, dflag, sflag)
else:
    horizontal(contents, directory)

exit(0)
