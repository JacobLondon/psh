import json
import os
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

        self.bookmarks = {}
        self.settings = {}

        if (settings := json_read_file(rcfile)):
            self.settings = settings

        if (path := self.settings.get("path")):
            self.path.extend(path)

        if (bookmarks := self.settings.get("bookmarks")):
            self.bookmarks = bookmarks

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

    def show_ps1(self):
        print(f"{self.workdir}$ ", end='', flush=True)

    def exec(self, command):
        if type(command) is str:
            cmd = shlex.split(command, posix=False)
        else:
            cmd = command
        print(cmd)
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

    def lookup_bookmarks(self, argc, argv):
        if argc <= 0:
            return None
        return self.bookmarks.get(argv[0])

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

            if (bookmark := self.lookup_bookmarks(self.argc, self.argv)):
                cmd = ["cd", bookmark]
                self.builtin_cd(len(cmd), cmd)

            elif (program := self.lookup_command(self.argc, self.argv)):
                args = self.argv_args(self.argc, self.argv)
                cmd = f"{program} {args}"
                try:
                    self.exec(cmd)
                except Exception as e:
                    print(e, file=sys.stderr)

            elif (method := self.lookup_builtin(self.argc, self.argv)):
                method(self.argc, self.argv)

            else:
                try:
                    self.exec(argv)
                except Exception as e:
                    print(e, file=sys.stderr)
            
            if self.command_and and self.returncode != 0:
                self.reset_command_chain()
                break
            elif self.command_or and self.returncode == 0:
                self.reset_command_chain()
                break

    def run(self):
        while True:
            self.show_ps1()
            for line in sys.stdin:
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
            os.chdir(argv[1])
            self.workdir = os.getcwd()
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
