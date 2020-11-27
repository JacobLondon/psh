import os
import sys

if len(sys.argv) <= 1:
    exit(1)

def filestuff(path):
    # https://www.garykessler.net/library/file_sigs.html
    lookup = {
        b'\x4d\x5a': "Windows/DOS executable file",
        b'\x00\x00\x01\x00': "Windows icon file",
        b'\x1F\x8B\x08': "GZIP archive file",
        b'\x21\x3C\x61\x72\x63\x68\x3E\x0A': "Unix archiver (ar) files and Microsoft Program Library Common Object File Format (COFF)",
        b'\x42\x5A\x68': "bzip2 compressed archive",
        b'\x47\x49\x46\x38\x37\x61': "Graphics interchange format file",
        b'\x47\x49\x46\x38\x39\x61': "Graphics interchange format file",
        b'\x49\x20\x49': "Tagged Image File Format file",
        b'\x49\x44\x33': "MPEG-1 Audio Layer 3 (MP3) audio file",
        b'\x4C\x00\x00\x00\x01\x14\x02\x00': "Windows shell link (shortcut) file",
        b'\x50\x4B\x03\x04\x0A\x00\x02\x00': "Open Publication Structure eBook file",
        b'\x50\x4B\x03\x04\x14\x00\x08\x00\x08\x00': "Java archive",
        b'\x7F\x45\x4C\x46': "Executable and Linking Format executable file (Linux/Unix)",
        b'\x80': "Relocatable object code",
        b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A': "Portable Network Graphics file"
    }
    with open(path, 'br') as fp:
        start = fp.read(32)
        print(f'{path} is a', end=' ', sep='')
        for key, value in lookup.items():
            if start.startswith(key):
                print(value)
                return
        print("file")

path = sys.argv[1]
if os.path.islink(path):
    print(f"'{path}' is a link")
elif os.path.isfile(path):
    filestuff(path)
elif os.path.isdir(path):
    print(f"'{path}' is a directory")
exit(0)
