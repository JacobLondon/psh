import os
import sys

# windows only for now
def execute(directory):
    try:
        os.system(f"cmd.exe /C start explorer.exe {directory}")
    except Exception as e:
        print(e)
        exit(1)

execute(os.getcwd())
exit(0)
