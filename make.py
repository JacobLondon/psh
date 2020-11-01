import os

CC = "tcc"
TARGET = "psh.exe"
FILES = "main.c"
CFLAGS = "-Wall -Wextra"

BIN_FILES = ["src/fgrep.c", "src/grep.c"]

thisdir = os.path.dirname(os.path.realpath(__file__))

with open("dir.h", "w") as fp:
    fp.truncate(0)
    fp.write(f"""\
/**
 * This file is auto-generated
 */
#ifndef PSH_DIR_H
#define PSH_DIR_H

#define THISDIR "{thisdir}"
#define THISPY "psh.py"

#endif /* PSH_DIR_H */
""".replace("\\", "\\\\"))

if not os.path.exists("etc"):
    os.mkdir("etc")

config = "etc/pshrc.json"
if not os.path.exists(config):
    with open(config, "w") as fp:
        fp.truncate(0)
        fp.write("""\
{
    "path": [],
    "executors":
    {
        ".py": "python"
    },
    "aliases":
    {

    }
}
""")

rv = 0
rv |= os.system(f"{CC} {FILES} -o {TARGET} {CFLAGS}")
for filename in BIN_FILES:
    name = f"bin/{os.path.basename(filename).replace('.c', '.exe')}"
    rv |= os.system(f"{CC} {filename} -o {name}")

exit(rv)
