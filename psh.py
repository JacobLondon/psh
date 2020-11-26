import json
import os
import getpass
import readchar
import socket
import subprocess
import shlex
import sys

thisdir = os.path.dirname(os.path.realpath(__file__))
rcfile = f"{thisdir}/etc/pshrc.json"

def file_read(filename: str):
    try:
        return open(filename, "r")
    except:
        return None

def json_read(fp):
    try:
        return json.load(fp)
    except:
        return None

def json_read_file(filename):
    if (fp := file_read(filename)):
        if (d := json_read(fp)):
            fp.close()
            return d

def autocomplete(text: str, lookup: list):
    """
    Returns the first thing in the list which matches
    """
    for completion in lookup:
        if completion.startswith(text):
            yield completion
    yield None

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

BLACK = "\u001b[30m"
RED = "\u001b[31m"
GREEN = "\u001b[32m"
YELLOW = "\u001b[33m"
BLUE = "\u001b[34m"
MAGENTA = "\u001b[35m"
CYAN = "\u001b[36m"
WHITE = "\u001b[37m"
RESET = "\u001b[0m"

class Psh:
    def __init__(self):
        self.workdir = os.getcwd()

        self.path = [
            f"{thisdir}/bin",
        ]

        self.aliases = {}
        self.settings = {}

        if (settings := json_read_file(rcfile)):
            self.settings = settings

        if (path := self.settings.get("path")):
            self.path.extend(path)

        if (aliases := self.settings.get("aliases")):
            self.aliases = aliases 

        if (executors := self.settings.get("executors")):
            self.executors = executors
        else:
            self.executors = {}

        self.bin_index = {}
        self.bin_builtins = {
            "cd": self.builtin_cd,
            "clear": self.builtin_clear,
            "ref": self.refresh_bin_index,
            "exit": self.builtin_exit,
            "help": self.builtin_help,
        }
        self.refresh_bin_index(None, None)

        self.argc = 0
        self.argv = []
        self.returncode = 0
        self.command_and: bool = False
        self.command_or:  bool = False

        self.username = getpass.getuser()
        self.hostname = socket.gethostname()
        self.ps1 = self.get_ps1()
        self.history = []
        self.history_idx = 0

    def get_ps1(self):
        if supports_color():
            return f"{GREEN}{self.username}@{self.hostname}{RESET}:{BLUE}{os.sep}{self.workdir}{RESET}$ "
        else:
            return f"{self.username}@{self.hostname}:{os.sep}{self.workdir}$ "

    def show_ps1(self):
        print(self.ps1, end='', flush=True)

    def exec(self, command):
        if type(command) is str:
            cmd = shlex.split(command, posix=False)
        else:
            cmd = command
        proc = subprocess.Popen(cmd)
        try:
            proc.communicate()
        except KeyboardInterrupt:
            proc.kill()

        self.returncode = proc.returncode
        return proc.returncode

    def stop(self):
        print("Exit...")
        exit(0)

    def lookup_executor(self, ext: str):
        for extension, executor in self.executors.items():
            if ext == extension:
                return f"{executor} "
        return ""

    def lookup_command(self, argc, argv):
        if argc <= 0:
            return None
        return self.bin_index.get(argv[0])
    
    def lookup_builtin(self, argc, argv):
        if argc <= 0:
            return None
        return self.bin_builtins.get(argv[0])

    def lookup_aliases(self, argc, argv):
        if argc <= 0:
            return None
        return self.aliases.get(argv[0])

    # get the args after the program name
    def argv_args(self, argc, argv):
        if argc <= 1:
            return ""
        else:
            return shlex.join(argv[1:])

    def refresh_bin_index(self, argc, argv):
        self.bin_index = {}
        for path in self.path:
            binaries = os.listdir(path)
            for binary in binaries:
                basename = os.path.basename(binary)
                name, ext = os.path.splitext(basename)

                executor = self.lookup_executor(ext)
                self.bin_index[name] = f"{executor}{path}/{binary}"

    def reset_command_chain(self):
        self.command_and = False
        self.command_or = False

    def split_line(self, line: str):
        args = shlex.split(line, posix=False)
        builder = []
        for arg in args:
            if arg == ';':
                yield builder
                builder = []
            elif arg == '&&':
                self.command_and = True
                yield builder
                builder = []
            elif arg == '||':
                self.command_or = True
                yield builder
                builder = []
            else:
                builder.append(arg)
        yield builder

    def command(self, line: str):
        for argv in self.split_line(line):
            self.argv = argv
            self.argc = len(self.argv)
            if self.argc == 0:
                self.reset_command_chain()
                break

            if (alias := self.lookup_aliases(self.argc, self.argv)):
                if not any(alias.startswith(builtin) for builtin in self.bin_builtins.keys()):
                    self.exec(alias)
                else:
                    self.argv = shlex.split(alias)
                    self.argc = len(self.argv)

            if (program := self.lookup_command(self.argc, self.argv)):
                args = self.argv_args(self.argc, self.argv)
                cmd = f"{program} {args}"
                try:
                    self.exec(cmd)
                except Exception as e:
                    print(f"{self.argv}", e, file=sys.stderr)

            elif (method := self.lookup_builtin(self.argc, self.argv)):
                method(self.argc, self.argv)

            else:
                try:
                    self.exec(self.argv)
                except Exception as e:
                    print(f"{self.argv}", e, file=sys.stderr)

            if self.command_and and self.returncode != 0:
                self.reset_command_chain()
                break
            elif self.command_or and self.returncode == 0:
                self.reset_command_chain()
                break

    def read_line(self):
        buf = []
        cursor = 0
        end = 0

        upndown = False
        write = lambda string: print(string, end='', file=sys.stdout, flush=True)
        completion = None

        while True:
            ch = readchar.readchar()
            #print(ch)
            #print(self.history_idx)

            if ch not in (b'\x10', b'\x0e'):
                upndown = False

            if ch == b'\t':
                complete = None
                command = str(b"".join(buf), encoding='utf-8')
                if completion is None:
                    # check cwd, then each item in each dir on path
                    lookup = os.listdir(os.getcwd())
                    for curpath in self.path:
                        lookup.extend(os.listdir(curpath))
                    completion = autocomplete(command, lookup)
                complete = next(completion)
                if complete:
                    for _ in range(end):
                        write("\x08\x20\x08")
                    write(complete)
                    buf = [bytes(str(ch), encoding='utf-8') for ch in complete]
                    cursor = len(buf)
                    end = cursor
                else:
                    completion = None

            elif ch in (b'\r', b'\n'):
                print("", file=sys.stdout, flush=True)
                command = str(b"".join(buf), encoding='utf-8')
                if not self.history or command != self.history[-1]:
                    self.history.append(command)
                yield command
                self.history_idx = len(self.history) - 1
                buf = []
                cursor = 0
                end = 0

            elif ch == b'\x06': # C-f
                if cursor < end:
                    write(str(buf[cursor], encoding='utf-8'))
                    cursor += 1

            elif ch == b'\x02': # C-b
                if cursor > 0:
                    cursor -= 1
                    write("\x08")

            elif ch == b'\x10': # C-p
                if self.history and self.history_idx > 0:
                    for _ in range(end):
                        write("\x08\x20\x08")

                    if upndown and self.history_idx - 1 >= 0:
                        self.history_idx -= 1

                    buf = [bytes(str(ch), encoding='utf-8') for ch in self.history[self.history_idx]]
                    write(self.history[self.history_idx])

                    upndown = True
                    cursor = len(buf)
                    end = cursor

            elif ch == b'\x0e': # C-n
                if self.history_idx + 1 < len(self.history):
                    for _ in range(end):
                        write("\x08\x20\x08")

                    self.history_idx += 1
                    buf = [bytes(str(ch), encoding='utf-8') for ch in self.history[self.history_idx]]
                    write(self.history[self.history_idx])

                    upndown = True
                    cursor = len(buf)
                    end = cursor

            elif ch == b'\x01': # C-a
                if cursor - 1 >= 0:
                    for _ in range(cursor):
                        write("\x08")
                    cursor = 0

            elif ch == b'\x05': # C-e
                write(str(b"".join(buf[cursor:]), encoding='utf-8'))
                cursor = end

            elif ch == b'\x03': # C-c
                raise KeyboardInterrupt

            elif ch == b'\x04': # C-d
                if cursor == end:
                    raise EOFError
                elif buf and cursor < len(buf):
                    for _ in range(end - cursor):
                        write("\x20")
                    for _ in buf:
                        write("\x08\x20\x08")

                    del buf[cursor]
                    write(str(b"".join(buf), encoding='utf-8'))
                    end -= 1

                    # move cursor back to where it was
                    for _ in range(end - cursor):
                        write("\x08")

            elif ch == b'\x08': # backspace
                if buf and cursor > 0:
                    if cursor != end:
                        for _ in range(end - cursor):
                            write("\x20")
                        
                        for _ in range(end - cursor + 1):
                            write("\x08")

                    cursor -= 1
                    end -= 1
                    del buf[cursor]

                    if cursor != end:
                        write(str(b"".join(buf[cursor:]), encoding='utf-8'))
                        for _ in range(end - cursor):
                            write("\x08")
                    else:
                        write("\x08\x20\x08")

            elif ch == b'\x0c': # C-l
                yield "clear"
                write(str(b"".join(buf), encoding='utf-8'))

            elif ch == b'\x15': # C-u
                for _ in range(end - cursor):
                    write("\x20")
                for _ in range(end):
                    write("\x08\x20\x08")

                buf = buf[cursor:]
                write(str(b"".join(buf), encoding='utf-8'))
                if cursor != end:
                    for _ in buf:
                        write("\x08")
                end -= cursor
                cursor = 0

            else:
                if cursor == len(buf) or not buf:
                    buf.append(ch)
                    write(str(ch, encoding='utf-8'))
                else:
                    buf.insert(cursor, ch)
                    write(str(b"".join(buf[cursor:]), encoding='utf-8'))
                    for _ in range(end - cursor):
                        write("\x08")
                cursor += 1
                end += 1
            #print(buf)

    def run(self):
        while True:
            self.show_ps1()
            for line in self.read_line():
                self.command(line)

                sys.stdin.flush()
                if self.returncode != 0:
                    break
                self.show_ps1()

    def builtin_cd(self, argc, argv):
        if argc <= 1:
            self.returncode = 1
            return

        try:
            directory = argv[1]
            # remove the extra set of quotes!!
            if (directory.startswith('"') and directory.endswith('"')) or \
                    (directory.startswith("'") and directory.endswith("'")):
                directory = directory[1:-1]

            os.chdir(directory)
            self.workdir = os.getcwd()
            self.ps1 = self.get_ps1()
            self.returncode = 0
        except Exception as e:
            print('cd:', e)

    def builtin_clear(self, argc, argv):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.returncode = 0

    def builtin_exit(self, argc, argv):
        self.returncode = 0
        self.stop()

    def builtin_help(self, argc, argv):
        commands = list(self.bin_index.keys()) + list(self.bin_builtins.keys())
        commands = sorted(commands)
        for key in commands:
            print(key, end="    ")
        print()
        self.returncode = 0

if __name__ == '__main__':
    psh = Psh()
    psh.run()
