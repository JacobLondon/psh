import signal
import shutil
import sys

if len(sys.argv) <= 1:
    exit(1)

signal.signal(signal.SIGINT, lambda sig, frame: exit(0))

try:
    columns, lines = shutil.get_terminal_size((80, 20))
    lines -= 3
    with open(sys.argv[1], 'r') as fp:
        iterator = zip(range(lines), iter(fp.readlines()))
        it = 0
        for _, line in iterator:
            print(line, end='')
            it += 1

        # we finished going thru the whole file
        if it < lines:
            exit(0)

        # go thru rest of file 1 at a time
        fp.seek(0, 0)
        iterator = iter(fp.readlines())
        for _ in range(lines):
            next(iterator)

        for line in iterator:
            print(line, end='')
            input()
            # go up 1 row, beginning of row
            print("\033[A\033[F")

except Exception as e:
    print(e, file=sys.stderr)
    exit(1)
exit(0)
