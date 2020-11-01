import json
import os
import readchar
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
            "c": self.builtin_clear,
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

        self.ps1 = f"{self.workdir}$ "
        self.history = []
        self.history_idx = 0

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

        while True:
            ch = readchar.readchar()
            #print(ch)
            #print(self.history_idx)
            if ch == b'\t':
                print('tab', file=sys.stdout, flush=True)
            elif ch in (b'\r', b'\n'):
                print("", file=sys.stdout, flush=True)
                command = str(b"".join(buf), encoding='utf-8')
                if not self.history or command != self.history[-1]:
                    self.history.append(command)
                    self.history_idx = len(self.history) - 1
                yield command
                buf = []
                cursor = 0
                end = 0

            # TODO: This is not quite right
            elif ch == b'\x10': # C-p
                if self.history:# and self.history_idx - 1 >= 0:
                    for _ in range(end):
                        print("\x08\x20\x08", end='', file=sys.stdout, flush=True)
                    buf = [bytes(str(ch), encoding='utf-8') for ch in self.history[self.history_idx]]
                    print(self.history[self.history_idx], end='', file=sys.stdout, flush=True)
                    if self.history_idx - 1 >= 0:
                        self.history_idx -= 1
                    cursor = len(buf)
                    end = cursor
            # TODO: This is not quite right
            elif ch == b'\x0e': # C-n
                if self.history_idx + 1 < len(self.history):
                    for _ in range(end):
                        print("\x08\x20\x08", end='', file=sys.stdout, flush=True)
                    self.history_idx += 1
                    buf = [bytes(str(ch), encoding='utf-8') for ch in self.history[self.history_idx]]
                    print(self.history[self.history_idx], end='', file=sys.stdout, flush=True)
                    cursor = len(buf)
                    end = cursor

            elif ch == b'\x01': # C-a
                if cursor - 1 >= 0:
                    for _ in range(cursor):
                        print("\x08", end='', file=sys.stdout, flush=True)
                    cursor = 0
            elif ch == b'\x05': # C-e
                print(str(b"".join(buf[cursor:]), encoding='utf-8'), end='', file=sys.stdout, flush=True)
                cursor = end
            elif ch == b'\x03': # C-c
                raise KeyboardInterrupt
            elif ch == b'\x04': # C-d
                raise EOFError
            elif ch == b'\x08': # backspace
                if buf and cursor > 0:
                    buf.pop()
                    cursor -= 1
                    end -= 1
                    print("\x08\x20\x08", end='', file=sys.stdout, flush=True)
            elif ch == b'\x0c': # C-l
                # TODO: This erases current text, but text remains in buf
                yield "clear"
            elif ch == b'\x15': # C-u
                for _ in range(end - cursor):
                    print("\x20", end='', file=sys.stdout, flush=True)
                for _ in range(end):
                    print("\x08\x20\x08", end='', file=sys.stdout, flush=True)

                end -= cursor
                buf = buf[cursor:]
                print(str(b"".join(buf), encoding='utf-8'), end='', file=sys.stdout, flush=True)
                cursor = 0
            else:
                if cursor == len(buf) or not buf:
                    buf.append(ch)
                    print(str(ch, encoding='utf-8'), end='', file=sys.stdout, flush=True)
                else:
                    buf.insert(cursor, ch)
                    print(str(b"".join(buf[cursor:]), encoding='utf-8'), end='', file=sys.stdout, flush=True)
                    for _ in range(end - cursor):
                        print("\x08", end='', file=sys.stdout, flush=True)
                cursor += 1
                end += 1
            #print(buf)

    def run(self):
        while True:
            self.show_ps1()
            #for line in sys.stdin:
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
            if (directory.startswith('"') and directory.endswith('"')) or \
                    (directory.startswith("'") and directory.endswith("'")):
                directory = directory[1:-1]

            os.chdir(directory)
            self.workdir = os.getcwd()
            self.ps1 = f"{self.workdir}$ "
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
