import os


def run_system_cmd1(cmd):
    os.system(cmd)


def run_system_cmd2(cmd):
    print(cmd)
    os.system("whoami")
