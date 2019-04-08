"""
Autonomous sentinel running in background to restart missing Bismuth Hypernode
"""


import time
import os
from subprocess import getoutput
from datetime import datetime


__version__ = "0.0.1"

# If your python invocation is not standard, edit it there.
PYTHON_EXECUTABLE='python3'


############################################################################################


def list_screens():
    """List all the existing screens and build a Screen instance for each
    """
    list_cmd = "screen -ls"
    return [".".join(l.split(".")[1:]).split("\t")[0]
            for l in getoutput(list_cmd).split('\n')
            if "\t" in l and ".".join(l.split(".")[1:]).split("\t")[0]]


def say(what):
    the_time = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    print("{}: {}".format(the_time, what))


def check1():
    """
    Run every minute, restart HN screen if needed
    """
    if 'hypernode' not in list_screens():
        say("Restarting stopped Hypernode...")
        getoutput('screen -d -S hypernode -m bash -c "cd ../main;{} hn_instance.py -v" -X quit'.format(PYTHON_EXECUTABLE))
        say("started")


def check5():
    """
    Run every 5 minutes, restart HN screen if needed
    """
    if os.path.getmtime("../main/logs/pos_app.log") < time.time() -120:
        say("Hypernode is frozen, stopping...")
        getoutput("screen -S hypernode -X at '#' stuff $'\003'")
    if os.path.getmtime("../main/logs/pos_app.log") < time.time() -300:
        print("Hypernode is frozen, killing...")
        data = subprocess.getoutput("screen -list")
        i2 = data.find('.hypernode')
        i1 = data.find(chr(9),i2-10)
        if (i1>0) and (i2>i1):
            data = data[i1+1:i2]
            str = "kill -15 {}".format(data)
            subprocess.getoutput(str)

if __name__ == "__main__":
    say("Bismuth Sentinel v{} starting".format(__version__))

    while True:
        for i in range(4):
            check1()
            time.sleep(60)
        check1()
        check5()
        time.sleep(60)
